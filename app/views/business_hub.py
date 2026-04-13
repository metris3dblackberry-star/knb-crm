"""
Üzleti Központ Blueprint
ERP kiegészítő modul: kiadások, munkás kifizetések, leadek, feladatok, teljesítési igazolások
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from datetime import date, datetime, timedelta
import logging
from app.extensions import db
from app.utils.decorators import handle_database_errors, log_function_call
from app.utils.validators import sanitize_input

business_bp = Blueprint('business', __name__)
logger = logging.getLogger(__name__)


def require_login():
    if not session.get('logged_in'):
        flash('Kérjük jelentkezzen be!', 'warning')
        return redirect(url_for('auth.login'))
    return None


def get_tenant_id():
    return session.get('current_tenant_id') or 1


def get_workers():
    from app.models.user import User
    from app.models.tenant_membership import TenantMembership
    from sqlalchemy import and_
    tenant_id = get_tenant_id()
    try:
        memberships = db.session.execute(
            db.select(TenantMembership).where(
                and_(TenantMembership.tenant_id == tenant_id, TenantMembership.status == 'active')
            )
        ).scalars().all()
        user_ids = [m.user_id for m in memberships]
        if not user_ids:
            return []
        return db.session.execute(
            db.select(User).where(User.user_id.in_(user_ids))
        ).scalars().all()
    except Exception as e:
        logger.error(f"get_workers error: {e}")
        return []


# ─────────────────────────────────────────────────────────────────
# MAIN HUB
# ─────────────────────────────────────────────────────────────────

@business_bp.route('/business-hub')
@handle_database_errors
def hub():
    r = require_login()
    if r: return r

    tenant_id = get_tenant_id()
    today = date.today()

    try:
        from app.models.expense import Expense
        from app.models.lead import Lead
        from app.models.task import Task
        from app.models.worker_payment import WorkerPayment, PerformanceConfirmation
        from app.models.job import Job
        from app.models.user import User
        from sqlalchemy import and_, func, case

        # ── HAVI ÖSSZESÍTŐK ────────────────────────────────────────
        total_expenses = db.session.execute(
            db.select(func.coalesce(func.sum(Expense.amount), 0))
            .where(and_(Expense.tenant_id == tenant_id,
                        func.extract('month', Expense.expense_date) == today.month,
                        func.extract('year', Expense.expense_date) == today.year))
        ).scalar() or 0

        total_payouts = db.session.execute(
            db.select(func.coalesce(func.sum(WorkerPayment.amount), 0))
            .where(and_(WorkerPayment.tenant_id == tenant_id,
                        func.extract('month', WorkerPayment.payment_date) == today.month,
                        func.extract('year', WorkerPayment.payment_date) == today.year))
        ).scalar() or 0

        open_leads = db.session.execute(
            db.select(func.count()).select_from(Lead)
            .where(and_(Lead.tenant_id == tenant_id, Lead.stage.notin_(['Megnyert', 'Elveszett'])))
        ).scalar() or 0

        open_tasks = db.session.execute(
            db.select(func.count()).select_from(Task)
            .where(and_(Task.tenant_id == tenant_id, Task.done == False))
        ).scalar() or 0

        monthly_revenue = db.session.execute(
            db.select(func.coalesce(func.sum(Job.total_cost), 0))
            .where(and_(Job.tenant_id == tenant_id, Job.completed == True,
                        func.extract('month', Job.job_date) == today.month,
                        func.extract('year', Job.job_date) == today.year))
        ).scalar() or 0

        # ── PROFIT RÉSZLETEZÉS ─────────────────────────────────────
        # Anyagköltség (alkatrészek)
        try:
            from app.models.job import JobPart
            material_cost = db.session.execute(
                db.select(func.coalesce(
                    func.sum(JobPart.quantity * JobPart.unit_price), 0))
                .join(Job, JobPart.job_id == Job.job_id)
                .where(and_(Job.tenant_id == tenant_id, Job.completed == True,
                            func.extract('month', Job.job_date) == today.month,
                            func.extract('year', Job.job_date) == today.year))
            ).scalar() or 0
        except Exception:
            material_cost = 0

        labor_cost = float(total_payouts)
        net_profit = float(monthly_revenue) - float(total_expenses) - labor_cost
        profit_pct = round((net_profit / float(monthly_revenue) * 100), 1) if float(monthly_revenue) > 0 else 0

        # ── MAI TEENDŐK ────────────────────────────────────────────
        today_jobs = db.session.execute(
            db.select(func.count()).select_from(Job)
            .where(and_(Job.tenant_id == tenant_id,
                        Job.job_date == today,
                        Job.completed == False))
        ).scalar() or 0

        overdue_tasks = db.session.execute(
            db.select(Task)
            .where(and_(Task.tenant_id == tenant_id,
                        Task.done == False,
                        Task.deadline != None,
                        Task.deadline <= today))
            .order_by(Task.deadline)
            .limit(5)
        ).scalars().all()

        today_tasks = db.session.execute(
            db.select(Task)
            .where(and_(Task.tenant_id == tenant_id,
                        Task.done == False,
                        Task.deadline == today))
        ).scalars().all()

        # Lejárt/fizetetlen számlák (jobs where completed but not invoiced / old)
        try:
            unpaid_jobs = db.session.execute(
                db.select(Job)
                .where(and_(Job.tenant_id == tenant_id,
                            Job.completed == True,
                            Job.job_date <= today - timedelta(days=30)))
                .order_by(Job.job_date.asc())
                .limit(5)
            ).scalars().all()
        except Exception:
            unpaid_jobs = []

        # Kifizetendő munkások (van-e PerformanceConfirmation 'Beadva' státuszban)
        try:
            pending_confirmations = db.session.execute(
                db.select(func.count()).select_from(PerformanceConfirmation)
                .where(and_(PerformanceConfirmation.tenant_id == tenant_id,
                            PerformanceConfirmation.status == 'Beadva'))
            ).scalar() or 0
        except Exception:
            pending_confirmations = 0

        # ── CASHFLOW ADATOK (30 nap) ───────────────────────────────
        cashflow_days = []
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            rev = db.session.execute(
                db.select(func.coalesce(func.sum(Job.total_cost), 0))
                .where(and_(Job.tenant_id == tenant_id, Job.completed == True,
                            Job.job_date == d))
            ).scalar() or 0
            exp = db.session.execute(
                db.select(func.coalesce(func.sum(Expense.amount), 0))
                .where(and_(Expense.tenant_id == tenant_id,
                            Expense.expense_date == d))
            ).scalar() or 0
            cashflow_days.append({
                'date': d.strftime('%m.%d'),
                'revenue': float(rev),
                'expense': float(exp),
                'profit': float(rev) - float(exp)
            })

        # ── TOP MUNKÁSOK ───────────────────────────────────────────
        workers = get_workers()
        top_workers = []
        avg_jobs = 0
        try:
            worker_stats = []
            for w in workers:
                job_count = db.session.execute(
                    db.select(func.count()).select_from(Job)
                    .where(and_(Job.tenant_id == tenant_id,
                                Job.completed == True,
                                func.extract('month', Job.job_date) == today.month,
                                func.extract('year', Job.job_date) == today.year))
                ).scalar() or 0
                revenue = db.session.execute(
                    db.select(func.coalesce(func.sum(Job.total_cost), 0))
                    .where(and_(Job.tenant_id == tenant_id,
                                Job.completed == True,
                                func.extract('month', Job.job_date) == today.month,
                                func.extract('year', Job.job_date) == today.year))
                ).scalar() or 0
                worker_stats.append({
                    'name': getattr(w, 'username', 'Ismeretlen'),
                    'job_count': job_count,
                    'revenue': float(revenue),
                })
            worker_stats.sort(key=lambda x: x['job_count'], reverse=True)
            top_workers = worker_stats[:3]
            if worker_stats:
                avg_jobs = sum(s['job_count'] for s in worker_stats) / len(worker_stats)
        except Exception as e:
            logger.warning(f"top_workers error: {e}")

        # ── FIGYELMEZTETÉSEK ───────────────────────────────────────
        warnings = []

        # Hiányzó teljesítési igazolások
        if pending_confirmations > 0:
            warnings.append({
                'type': 'danger',
                'icon': 'ti-file-alert',
                'text': f'{pending_confirmations} teljesítési igazolás jóváhagyásra vár',
                'url': url_for('business.confirmations')
            })

        # Lejárt feladatok
        overdue_count = len(overdue_tasks)
        if overdue_count > 0:
            warnings.append({
                'type': 'warning',
                'icon': 'ti-clock-exclamation',
                'text': f'{overdue_count} lejárt feladat',
                'url': url_for('business.tasks')
            })

        # Negatív profit
        if net_profit < 0:
            warnings.append({
                'type': 'danger',
                'icon': 'ti-trending-down',
                'text': f'Negatív havi profit: {int(net_profit):,} Ft'.replace(',', ' '),
                'url': url_for('business.expenses')
            })

        # Sok lead veszteség
        lost_leads = db.session.execute(
            db.select(func.count()).select_from(Lead)
            .where(and_(Lead.tenant_id == tenant_id, Lead.stage == 'Elveszett',
                        func.extract('month', Lead.created_date) == today.month))
        ).scalar() or 0
        if lost_leads >= 3:
            warnings.append({
                'type': 'warning',
                'icon': 'ti-user-x',
                'text': f'{lost_leads} elveszett lead ebben a hónapban',
                'url': url_for('business.leads')
            })

        # ── LEGUTÓBBI AKTIVITÁSOK ──────────────────────────────────
        recent_activities = []

        # Utolsó 5 kiadás
        recent_expenses = db.session.execute(
            db.select(Expense).where(Expense.tenant_id == tenant_id)
            .order_by(Expense.expense_date.desc()).limit(3)
        ).scalars().all()
        for e in recent_expenses:
            recent_activities.append({
                'icon': 'ti-receipt',
                'color': 'danger',
                'text': f'Kiadás rögzítve: {int(e.amount):,} Ft ({e.category or "egyéb"})'.replace(',', ' '),
                'date': e.expense_date.strftime('%m.%d') if e.expense_date else '',
                'sort_date': e.expense_date or date.min
            })

        # Utolsó 3 befejezett munka
        recent_jobs = db.session.execute(
            db.select(Job).where(and_(Job.tenant_id == tenant_id, Job.completed == True))
            .order_by(Job.job_date.desc()).limit(3)
        ).scalars().all()
        for j in recent_jobs:
            recent_activities.append({
                'icon': 'ti-check',
                'color': 'success',
                'text': f'Munka lezárva: {int(j.total_cost or 0):,} Ft'.replace(',', ' '),
                'date': j.job_date.strftime('%m.%d') if j.job_date else '',
                'sort_date': j.job_date or date.min
            })

        # Utolsó 2 lead
        recent_leads_list = db.session.execute(
            db.select(Lead).where(Lead.tenant_id == tenant_id)
            .order_by(Lead.created_date.desc()).limit(2)
        ).scalars().all()
        for l in recent_leads_list:
            recent_activities.append({
                'icon': 'ti-user-plus',
                'color': 'primary',
                'text': f'Új lead: {l.name} ({l.stage})',
                'date': l.created_date.strftime('%m.%d') if l.created_date else '',
                'sort_date': l.created_date or date.min
            })

        recent_activities.sort(key=lambda x: x['sort_date'], reverse=True)
        recent_activities = recent_activities[:8]

        return render_template('business/hub.html',
            # Havi összesítők
            total_expenses=float(total_expenses),
            total_payouts=float(total_payouts),
            open_leads=open_leads,
            open_tasks=open_tasks,
            monthly_revenue=float(monthly_revenue),
            profit_estimate=net_profit,
            current_month=today.strftime('%Y. %B'),
            # Profit részletezés
            material_cost=float(material_cost),
            labor_cost=labor_cost,
            net_profit=net_profit,
            profit_pct=profit_pct,
            # Mai teendők
            today_jobs=today_jobs,
            overdue_tasks=overdue_tasks,
            today_tasks=today_tasks,
            unpaid_jobs=unpaid_jobs,
            pending_confirmations=pending_confirmations,
            # Cashflow
            cashflow_days=cashflow_days,
            # Top munkások
            top_workers=top_workers,
            avg_jobs=avg_jobs,
            # Figyelmeztetések
            warnings=warnings,
            # Aktivitások
            recent_activities=recent_activities,
            # Workers (modal-hoz)
            workers=workers,
            today=today,
        )

    except Exception as e:
        logger.error(f"Business hub error: {e}", exc_info=True)
        flash(f'Dashboard hiba: {e}', 'error')
        return render_template('business/hub.html',
            total_expenses=0, total_payouts=0, open_leads=0, open_tasks=0,
            monthly_revenue=0, profit_estimate=0, current_month=today.strftime('%Y. %B'),
            material_cost=0, labor_cost=0, net_profit=0, profit_pct=0,
            today_jobs=0, overdue_tasks=[], today_tasks=[], unpaid_jobs=[],
            pending_confirmations=0, cashflow_days=[], top_workers=[], avg_jobs=0,
            warnings=[], recent_activities=[], workers=[], today=today)


# ─────────────────────────────────────────────────────────────────
# NAPI ZÁRÁS API
# ─────────────────────────────────────────────────────────────────

@business_bp.route('/business-hub/daily-close', methods=['POST'])
@handle_database_errors
def daily_close():
    r = require_login()
    if r: return jsonify({'error': 'Nincs bejelentkezve'}), 401

    tenant_id = get_tenant_id()
    today = date.today()
    issues = []
    ok = []

    try:
        from app.models.task import Task
        from app.models.expense import Expense
        from app.models.job import Job
        from sqlalchemy import and_, func

        # Nyitott feladatok ma
        open_tasks_count = db.session.execute(
            db.select(func.count()).select_from(Task)
            .where(and_(Task.tenant_id == tenant_id, Task.done == False,
                        Task.deadline != None, Task.deadline <= today))
        ).scalar() or 0

        if open_tasks_count > 0:
            issues.append(f'⚠️ {open_tasks_count} lejárt feladat maradt nyitva')
        else:
            ok.append('✅ Minden lejárt feladat elvégezve')

        # Mai befejezetlen munkák
        open_jobs = db.session.execute(
            db.select(func.count()).select_from(Job)
            .where(and_(Job.tenant_id == tenant_id, Job.completed == False,
                        Job.job_date == today))
        ).scalar() or 0

        if open_jobs > 0:
            issues.append(f'⚠️ {open_jobs} mai munka nincs lezárva')
        else:
            ok.append('✅ Minden mai munka lezárva')

        # Rögzítetlen kiadások ellenőrzése (ha nincs egyetlen mai kiadás sem, és van munka)
        today_expenses = db.session.execute(
            db.select(func.count()).select_from(Expense)
            .where(and_(Expense.tenant_id == tenant_id, Expense.expense_date == today))
        ).scalar() or 0

        today_completed = db.session.execute(
            db.select(func.count()).select_from(Job)
            .where(and_(Job.tenant_id == tenant_id, Job.completed == True, Job.job_date == today))
        ).scalar() or 0

        if today_completed > 0 and today_expenses == 0:
            issues.append('💡 Tipp: Volt munka ma, de nem lett kiadás rögzítve')
        elif today_expenses > 0:
            ok.append(f'✅ {today_expenses} kiadás rögzítve ma')

        status = 'ok' if len(issues) == 0 else 'warning'
        return jsonify({
            'status': status,
            'issues': issues,
            'ok': ok,
            'date': today.strftime('%Y. %m. %d.')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'issues': [str(e)], 'ok': []}), 500


# ─────────────────────────────────────────────────────────────────
# KIADÁSOK
# ─────────────────────────────────────────────────────────────────

@business_bp.route('/business-hub/expenses')
@handle_database_errors
def expenses():
    r = require_login()
    if r: return r
    from app.models.expense import Expense
    from sqlalchemy import and_
    tenant_id = get_tenant_id()
    items = db.session.execute(
        db.select(Expense).where(Expense.tenant_id == tenant_id).order_by(Expense.expense_date.desc())
    ).scalars().all()
    workers = get_workers()
    return render_template('business/expenses.html', expenses=items, workers=workers)


@business_bp.route('/business-hub/expenses/add', methods=['POST'])
@handle_database_errors
def add_expense():
    r = require_login()
    if r: return r
    from app.models.expense import Expense
    try:
        e = Expense(
            tenant_id=get_tenant_id(),
            worker_id=request.form.get('worker_id', type=int) or None,
            amount=float(request.form.get('amount', 0)),
            currency=request.form.get('currency', 'HUF'),
            payment_source=sanitize_input(request.form.get('payment_source', '')),
            category=sanitize_input(request.form.get('category', '')),
            notes=sanitize_input(request.form.get('notes', '')),
            expense_date=date.fromisoformat(request.form.get('expense_date', str(date.today()))),
        )
        db.session.add(e)
        db.session.commit()
        flash('Kiadás rögzítve!', 'success')
    except Exception as ex:
        db.session.rollback()
        flash(f'Hiba: {ex}', 'error')
    next_url = request.form.get('next', url_for('business.expenses'))
    return redirect(next_url)


@business_bp.route('/business-hub/expenses/<int:expense_id>/delete', methods=['POST'])
@handle_database_errors
def delete_expense(expense_id):
    r = require_login()
    if r: return r
    from app.models.expense import Expense
    e = db.session.get(Expense, expense_id)
    if e:
        db.session.delete(e)
        db.session.commit()
        flash('Kiadás törölve!', 'success')
    return redirect(url_for('business.expenses'))


# ─────────────────────────────────────────────────────────────────
# MUNKÁS KIFIZETÉSEK
# ─────────────────────────────────────────────────────────────────

@business_bp.route('/business-hub/worker-payments')
@handle_database_errors
def worker_payments():
    r = require_login()
    if r: return r
    from app.models.worker_payment import WorkerPayment
    from sqlalchemy import and_, func
    tenant_id = get_tenant_id()
    workers = get_workers()

    payment_totals = {}
    for w in workers:
        total = db.session.execute(
            db.select(func.coalesce(func.sum(WorkerPayment.amount), 0))
            .where(and_(WorkerPayment.tenant_id == tenant_id, WorkerPayment.worker_id == w.user_id))
        ).scalar() or 0
        payment_totals[w.user_id] = float(total)

    payments = db.session.execute(
        db.select(WorkerPayment).where(WorkerPayment.tenant_id == tenant_id)
        .order_by(WorkerPayment.payment_date.desc())
    ).scalars().all()

    return render_template('business/worker_payments.html',
        workers=workers, payments=payments, payment_totals=payment_totals)


@business_bp.route('/business-hub/worker-payments/add', methods=['POST'])
@handle_database_errors
def add_worker_payment():
    r = require_login()
    if r: return r
    from app.models.worker_payment import WorkerPayment
    try:
        p = WorkerPayment(
            tenant_id=get_tenant_id(),
            worker_id=request.form.get('worker_id', type=int),
            amount=float(request.form.get('amount', 0)),
            payment_date=date.fromisoformat(request.form.get('payment_date', str(date.today()))),
            notes=sanitize_input(request.form.get('notes', '')),
        )
        db.session.add(p)
        db.session.commit()
        flash('Kifizetés rögzítve!', 'success')
    except Exception as ex:
        db.session.rollback()
        flash(f'Hiba: {ex}', 'error')
    next_url = request.form.get('next', url_for('business.worker_payments'))
    return redirect(next_url)


@business_bp.route('/business-hub/worker-payments/<int:payment_id>/delete', methods=['POST'])
@handle_database_errors
def delete_worker_payment(payment_id):
    r = require_login()
    if r: return r
    from app.models.worker_payment import WorkerPayment
    p = db.session.get(WorkerPayment, payment_id)
    if p:
        db.session.delete(p)
        db.session.commit()
        flash('Kifizetés törölve!', 'success')
    return redirect(url_for('business.worker_payments'))


# ─────────────────────────────────────────────────────────────────
# LEADEK
# ─────────────────────────────────────────────────────────────────

@business_bp.route('/business-hub/leads')
@handle_database_errors
def leads():
    r = require_login()
    if r: return r
    from app.models.lead import Lead, LEAD_STAGES
    from sqlalchemy import and_
    tenant_id = get_tenant_id()
    all_leads = db.session.execute(
        db.select(Lead).where(Lead.tenant_id == tenant_id).order_by(Lead.created_date.desc())
    ).scalars().all()
    workers = get_workers()
    return render_template('business/leads.html', leads=all_leads, stages=LEAD_STAGES, workers=workers)


@business_bp.route('/business-hub/leads/add', methods=['POST'])
@handle_database_errors
def add_lead():
    r = require_login()
    if r: return r
    from app.models.lead import Lead
    try:
        lead = Lead(
            tenant_id=get_tenant_id(),
            name=sanitize_input(request.form.get('name', '')),
            phone=sanitize_input(request.form.get('phone', '')),
            email=sanitize_input(request.form.get('email', '')),
            source=sanitize_input(request.form.get('source', '')),
            stage=request.form.get('stage', 'Új lead'),
            notes=sanitize_input(request.form.get('notes', '')),
            assigned_worker_id=request.form.get('assigned_worker_id', type=int) or None,
            created_date=date.today(),
        )
        db.session.add(lead)
        db.session.commit()
        flash('Lead hozzáadva!', 'success')
    except Exception as ex:
        db.session.rollback()
        flash(f'Hiba: {ex}', 'error')
    next_url = request.form.get('next', url_for('business.leads'))
    return redirect(next_url)


@business_bp.route('/business-hub/leads/<int:lead_id>/stage', methods=['POST'])
@handle_database_errors
def update_lead_stage(lead_id):
    r = require_login()
    if r: return r
    from app.models.lead import Lead
    lead = db.session.get(Lead, lead_id)
    if lead:
        lead.stage = request.form.get('stage', lead.stage)
        db.session.commit()
        flash('Lead státusz frissítve!', 'success')
    return redirect(url_for('business.leads'))


@business_bp.route('/business-hub/leads/<int:lead_id>/delete', methods=['POST'])
@handle_database_errors
def delete_lead(lead_id):
    r = require_login()
    if r: return r
    from app.models.lead import Lead
    lead = db.session.get(Lead, lead_id)
    if lead:
        db.session.delete(lead)
        db.session.commit()
        flash('Lead törölve!', 'success')
    return redirect(url_for('business.leads'))


# ─────────────────────────────────────────────────────────────────
# FELADATOK
# ─────────────────────────────────────────────────────────────────

@business_bp.route('/business-hub/tasks')
@handle_database_errors
def tasks():
    r = require_login()
    if r: return r
    from app.models.task import Task
    from sqlalchemy import and_
    tenant_id = get_tenant_id()
    all_tasks = db.session.execute(
        db.select(Task).where(Task.tenant_id == tenant_id).order_by(Task.done, Task.deadline)
    ).scalars().all()
    workers = get_workers()

    from app.models.job import Job
    jobs = db.session.execute(
        db.select(Job).where(Job.tenant_id == tenant_id).order_by(Job.job_id.desc()).limit(50)
    ).scalars().all()

    return render_template('business/tasks.html', tasks=all_tasks, workers=workers, jobs=jobs)


@business_bp.route('/business-hub/tasks/add', methods=['POST'])
@handle_database_errors
def add_task():
    r = require_login()
    if r: return r
    from app.models.task import Task
    try:
        deadline_str = request.form.get('deadline', '')
        t = Task(
            tenant_id=get_tenant_id(),
            title=sanitize_input(request.form.get('title', '')),
            description=sanitize_input(request.form.get('description', '')),
            assigned_worker_id=request.form.get('assigned_worker_id', type=int) or None,
            deadline=date.fromisoformat(deadline_str) if deadline_str else None,
            job_id=request.form.get('job_id', type=int) or None,
            done=False,
            created_date=date.today(),
        )
        db.session.add(t)
        db.session.commit()
        flash('Feladat hozzáadva!', 'success')
    except Exception as ex:
        db.session.rollback()
        flash(f'Hiba: {ex}', 'error')
    next_url = request.form.get('next', url_for('business.tasks'))
    return redirect(next_url)


@business_bp.route('/business-hub/tasks/<int:task_id>/toggle', methods=['POST'])
@handle_database_errors
def toggle_task(task_id):
    r = require_login()
    if r: return r
    from app.models.task import Task
    t = db.session.get(Task, task_id)
    if t:
        t.done = not t.done
        db.session.commit()
    return redirect(url_for('business.tasks'))


@business_bp.route('/business-hub/tasks/<int:task_id>/delete', methods=['POST'])
@handle_database_errors
def delete_task(task_id):
    r = require_login()
    if r: return r
    from app.models.task import Task
    t = db.session.get(Task, task_id)
    if t:
        db.session.delete(t)
        db.session.commit()
        flash('Feladat törölve!', 'success')
    return redirect(url_for('business.tasks'))


# ─────────────────────────────────────────────────────────────────
# TELJESÍTÉSI IGAZOLÁSOK
# ─────────────────────────────────────────────────────────────────

@business_bp.route('/business-hub/confirmations')
@handle_database_errors
def confirmations():
    r = require_login()
    if r: return r
    from app.models.worker_payment import PerformanceConfirmation
    tenant_id = get_tenant_id()
    items = db.session.execute(
        db.select(PerformanceConfirmation).where(PerformanceConfirmation.tenant_id == tenant_id)
        .order_by(PerformanceConfirmation.month.desc())
    ).scalars().all()
    workers = get_workers()
    return render_template('business/confirmations.html', confirmations=items, workers=workers)


@business_bp.route('/business-hub/confirmations/add', methods=['POST'])
@handle_database_errors
def add_confirmation():
    r = require_login()
    if r: return r
    from app.models.worker_payment import PerformanceConfirmation
    import os
    from werkzeug.utils import secure_filename
    try:
        file = request.files.get('file')
        file_path = None
        if file and file.filename:
            upload_dir = os.path.join('app', 'static', 'uploads', 'confirmations')
            os.makedirs(upload_dir, exist_ok=True)
            filename = secure_filename(file.filename)
            full_path = os.path.join(upload_dir, filename)
            file.save(full_path)
            file_path = f'/static/uploads/confirmations/{filename}'
        c = PerformanceConfirmation(
            tenant_id=get_tenant_id(),
            worker_id=request.form.get('worker_id', type=int),
            month=request.form.get('month', date.today().strftime('%Y-%m')),
            file_path=file_path,
            status='Beadva',
            notes=sanitize_input(request.form.get('notes', '')),
            job_id=request.form.get('job_id', type=int) or None,
        )
        db.session.add(c)
        db.session.commit()
        flash('Teljesítési igazolás beadva!', 'success')
    except Exception as ex:
        db.session.rollback()
        flash(f'Hiba: {ex}', 'error')
    return redirect(url_for('business.confirmations'))


@business_bp.route('/business-hub/confirmations/<int:conf_id>/approve', methods=['POST'])
@handle_database_errors
def approve_confirmation(conf_id):
    r = require_login()
    if r: return r
    from app.models.worker_payment import PerformanceConfirmation
    c = db.session.get(PerformanceConfirmation, conf_id)
    if c:
        c.status = 'Jóváhagyva'
        db.session.commit()
        flash('Teljesítési igazolás jóváhagyva!', 'success')
    return redirect(url_for('business.confirmations'))


# ─────────────────────────────────────────────────────────────────
# ÚJ MUNKÁS HOZZÁADÁSA
# ─────────────────────────────────────────────────────────────────

@business_bp.route('/business-hub/workers/add', methods=['POST'])
@handle_database_errors
def add_worker():
    r = require_login()
    if r: return r
    from app.models.user import User
    from app.models.tenant_membership import TenantMembership
    from werkzeug.security import generate_password_hash
    try:
        email = sanitize_input(request.form.get('email', ''))
        # Email egyediség ellenőrzés
        existing = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()
        if existing:
            flash(f'Ez az email cím már foglalt: {email}', 'error')
            next_url = request.form.get('next', url_for('business.hub'))
            return redirect(next_url)

        password_raw = request.form.get('password', '')
        first_name = sanitize_input(request.form.get('first_name', ''))
        last_name = sanitize_input(request.form.get('last_name', ''))
        full_name = f"{first_name} {last_name}".strip() or email.split('@')[0]

        # Username egyediség biztosítása
        base_username = full_name
        username = base_username
        counter = 1
        while db.session.execute(db.select(User).where(User.username == username)).scalar_one_or_none():
            username = f"{base_username} {counter}"
            counter += 1

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password_raw),
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()  # user.user_id generálás

        membership = TenantMembership(
            tenant_id=get_tenant_id(),
            user_id=user.user_id,
            role=request.form.get('role', 'technician'),
            status='active',
        )
        db.session.add(membership)
        db.session.commit()
        flash(f'Munkás hozzáadva: {full_name}', 'success')
    except Exception as ex:
        db.session.rollback()
        flash(f'Hiba: {ex}', 'error')
    next_url = request.form.get('next', url_for('business.hub'))
    return redirect(next_url)
