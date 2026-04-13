"""
Üzleti Központ Blueprint
ERP kiegészítő modul: kiadások, munkás kifizetések, leadek, feladatok, teljesítési igazolások
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from datetime import date
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
    """Get all active workers for the current tenant"""
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
    """Üzleti Központ főoldal"""
    r = require_login()
    if r: return r
    tenant_id = get_tenant_id()
    today = date.today()

    try:
        from app.models.expense import Expense
        from app.models.lead import Lead
        from app.models.task import Task
        from app.models.worker_payment import WorkerPayment
        from sqlalchemy import and_, func

        # Összesítők
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

        # Bevétel becslés (munkák összege adott hónapban)
        from app.models.job import Job
        monthly_revenue = db.session.execute(
            db.select(func.coalesce(func.sum(Job.total_cost), 0))
            .where(and_(Job.tenant_id == tenant_id, Job.completed == True,
                        func.extract('month', Job.job_date) == today.month,
                        func.extract('year', Job.job_date) == today.year))
        ).scalar() or 0

        profit_estimate = float(monthly_revenue) - float(total_expenses) - float(total_payouts)

        return render_template('business/hub.html',
            total_expenses=float(total_expenses),
            total_payouts=float(total_payouts),
            open_leads=open_leads,
            open_tasks=open_tasks,
            monthly_revenue=float(monthly_revenue),
            profit_estimate=profit_estimate,
            current_month=today.strftime('%Y. %B'),
        )
    except Exception as e:
        logger.error(f"Business hub error: {e}", exc_info=True)
        flash(f'Hiba: {e}', 'error')
        return render_template('business/hub.html',
            total_expenses=0, total_payouts=0, open_leads=0,
            open_tasks=0, monthly_revenue=0, profit_estimate=0,
            current_month=today.strftime('%Y. %B'))


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
    return redirect(url_for('business.expenses'))


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

    # Összesítés workerenként
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
            currency=request.form.get('currency', 'HUF'),
            payment_source=sanitize_input(request.form.get('payment_source', '')),
            notes=sanitize_input(request.form.get('notes', '')),
            payment_date=date.fromisoformat(request.form.get('payment_date', str(date.today()))),
        )
        db.session.add(p)
        db.session.commit()
        flash('Kifizetés rögzítve!', 'success')
    except Exception as ex:
        db.session.rollback()
        flash(f'Hiba: {ex}', 'error')
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
    return redirect(url_for('business.leads'))


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
    return redirect(url_for('business.tasks'))


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
