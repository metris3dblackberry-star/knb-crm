"""
Main Routes Blueprint
Contains home page, login, public functionality routes
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session, g
from datetime import date
import logging
from app.services.customer_service import CustomerService
from app.services.job_service import JobService
from app.services.billing_service import BillingService
from app.utils.decorators import handle_database_errors, log_function_call
from app.utils.validators import validate_customer_data, sanitize_input
from app.utils.security import require_auth, InputSanitizer, SQLInjectionProtection
from app.utils.error_handler import ValidationError, BusinessLogicError
from app.extensions import db as main_db
from app.models.job import Job as MainJob

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

customer_service = CustomerService()
job_service = JobService()
billing_service = BillingService()


@main_bp.route('/')
@handle_database_errors
@log_function_call
def index():
    try:
        job_stats = job_service.get_job_statistics()
        billing_stats = billing_service.get_billing_statistics()
        recent_jobs, _, _ = job_service.get_current_jobs(page=1, per_page=5)
        overdue_bills = billing_service.get_overdue_bills()[:5]
        return render_template('index.html', job_stats=job_stats, billing_stats=billing_stats,
                             recent_jobs=recent_jobs, overdue_bills=overdue_bills, current_date=date.today())
    except Exception as e:
        logger.error(f"Home page loading failed: {e}")
        flash('System temporarily unavailable, please try again later', 'error')
        return render_template('index.html', job_stats={}, billing_stats={},
                             recent_jobs=[], overdue_bills=[], current_date=date.today())


@main_bp.route('/login')
def login():
    return redirect(url_for('auth.login'))


@main_bp.route('/logout')
def logout():
    from flask import current_app
    import requests as http_requests
    neon_auth_url = (current_app.config.get('NEON_AUTH_URL') or '').rstrip('/')
    if neon_auth_url:
        try:
            http_requests.post(f"{neon_auth_url}/sign-out", timeout=5)
        except Exception:
            pass
    session.clear()
    flash('You have successfully logged out', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/dashboard')
@require_auth()
@log_function_call
def dashboard():
    if not session.get('logged_in'):
        flash('Please login first', 'warning')
        return redirect(url_for('auth.login'))
    try:
        from sqlalchemy import and_
        import datetime as dt
        Job = MainJob
        db = main_db

        user_type = session.get('current_role', 'technician')
        tenant_id = session.get('current_tenant_id')
        if not tenant_id:
            # Nincs tenant session - átirányítás a szervezet regisztrációhoz
            return redirect(url_for('auth.register_organization'))
        today = dt.date.today()

        job_stats = job_service.get_job_statistics()
        billing_stats = billing_service.get_billing_statistics()
        recent_jobs, _, _ = job_service.get_current_jobs(page=1, per_page=5)

        # ── TENANT-AWARE lekérdezések ──────────────────────────────
        from sqlalchemy import func

        # Összes bevétel (lezárt munkák, tenant_id alapján)
        total_revenue = db.session.execute(
            db.select(func.coalesce(func.sum(Job.total_cost), 0))
            .where(and_(Job.tenant_id == tenant_id, Job.completed == True))
        ).scalar() or 0

        paid_revenue = db.session.execute(
            db.select(func.coalesce(func.sum(Job.total_cost), 0))
            .where(and_(Job.tenant_id == tenant_id, Job.completed == True, Job.paid == True))
        ).scalar() or 0

        unpaid_revenue = float(total_revenue) - float(paid_revenue)

        # Felülírjuk a service által visszaadott értékeket
        billing_stats['total_amount'] = float(total_revenue)
        billing_stats['paid_amount'] = float(paid_revenue)
        billing_stats['unpaid_amount'] = unpaid_revenue

        # Aktív ügyfelek (tenant_id alapján)
        try:
            from app.models.customer import Customer
            total_customers = db.session.execute(
                db.select(func.count()).select_from(Customer)
                .where(Customer.tenant_id == tenant_id)
            ).scalar() or 0
            customers_with_unpaid = db.session.execute(
                db.select(func.count(func.distinct(Job.customer_id)))
                .where(and_(Job.tenant_id == tenant_id, Job.completed == True, Job.paid == False))
            ).scalar() or 0
        except Exception:
            total_customers = len(customer_service.get_all_customers())
            customers_with_unpaid = 0

        # ORM overdue_bills (befejezett, kifizetetlen)
        overdue_q = db.select(Job).where(
            and_(Job.completed == True, Job.paid == False, Job.tenant_id == tenant_id)
        ).order_by(Job.job_id.desc()).limit(5)
        overdue_bills = list(db.session.execute(overdue_q).scalars())

        # Monthly revenue for chart
        monthly_revenue = [0.0] * 12
        monthly_q = db.select(
            db.func.extract('month', Job.job_date).label('month'),
            db.func.coalesce(db.func.sum(Job.total_cost), 0).label('revenue')
        ).where(
            and_(
                db.func.extract('year', Job.job_date) == today.year,
                Job.tenant_id == tenant_id,
                Job.total_cost > 0
            )
        ).group_by(db.func.extract('month', Job.job_date))
        for row in db.session.execute(monthly_q):
            monthly_revenue[int(row.month) - 1] = float(row.revenue)
        billing_stats['monthly_revenue'] = monthly_revenue

        # Technician dashboard extras
        week_start = today - dt.timedelta(days=today.weekday())
        active_jobs = db.session.execute(
            db.select(db.func.count()).select_from(Job).where(
                and_(Job.completed == False, Job.tenant_id == tenant_id)
            )
        ).scalar() or 0
        todays_jobs = db.session.execute(
            db.select(db.func.count()).select_from(Job).where(
                and_(Job.job_date == today, Job.tenant_id == tenant_id)
            )
        ).scalar() or 0
        completed_this_week = db.session.execute(
            db.select(db.func.count()).select_from(Job).where(
                and_(Job.completed == True, Job.job_date >= week_start, Job.tenant_id == tenant_id)
            )
        ).scalar() or 0
        todays_schedule = list(db.session.execute(
            db.select(Job).where(and_(Job.job_date == today, Job.tenant_id == tenant_id))
        ).scalars())

        template = 'administrator/dashboard.html' if user_type in ('owner', 'admin') else 'technician/dashboard.html'

        return render_template(template,
                             user_type=user_type,
                             job_stats=job_stats,
                             billing_stats=billing_stats,
                             recent_jobs=recent_jobs,
                             overdue_bills=overdue_bills,
                             total_customers=total_customers,
                             customers_with_unpaid=customers_with_unpaid,
                             customers_with_overdue=0,
                             active_jobs=active_jobs,
                             todays_jobs=todays_jobs,
                             completed_this_week=completed_this_week,
                             todays_schedule=todays_schedule,
                             current_date=today)
    except Exception as e:
        logger.error(f"Dashboard loading failed: {e}", exc_info=True)
        flash(f'Hiba: {str(e)}', 'error')
        return render_template('technician/dashboard.html', user_type='technician',
                             job_stats={}, billing_stats={}, recent_jobs=[], overdue_bills=[],
                             active_jobs=0, todays_jobs=0, completed_this_week=0,
                             todays_schedule=[], current_date=dt.date.today())


@main_bp.route('/api/search/customers')
@require_auth()
@handle_database_errors
def api_search_customers():
    query = InputSanitizer.sanitize_string(request.args.get('q', ''))
    search_type = InputSanitizer.sanitize_string(request.args.get('type', 'both'))
    if SQLInjectionProtection.scan_sql_injection(query):
        raise ValidationError("Search criteria contains illegal characters")
    if not query:
        return jsonify([])
    try:
        customers = customer_service.search_customers(query, search_type)
        return jsonify([{'customer_id': c.customer_id, 'full_name': c.full_name,
                        'email': c.email, 'phone': c.phone} for c in customers])
    except Exception as e:
        logger.error(f"Customer search failed: {e}")
        return jsonify({'error': 'Search failed'}), 500


@main_bp.route('/api/customers/<int:customer_id>')
@handle_database_errors
def api_get_customer(customer_id):
    try:
        customer = customer_service.get_customer_by_id(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        stats = customer_service.get_customer_statistics(customer_id)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Get customer details failed: {e}")
        return jsonify({'error': 'Failed to get customer information'}), 500


@main_bp.route('/customers')
@handle_database_errors
@log_function_call
def customers():
    try:
        search_query = sanitize_input(request.args.get('search', ''))
        search_type = sanitize_input(request.args.get('search_type', 'both'))
        if search_query:
            customers = customer_service.search_customers(search_query, search_type)
        else:
            customers = customer_service.get_all_customers()
        return render_template('customers/list.html', customers=customers,
                             search_query=search_query, search_type=search_type)
    except Exception as e:
        logger.error(f"Customer list loading failed: {e}")
        flash('Failed to load customer list', 'error')
        return render_template('customers/list.html', customers=[], search_query='', search_type='both')


@main_bp.route('/customers/new')
def new_customer():
    return render_template('customers/form.html', customer=None, action='create')


@main_bp.route('/customers', methods=['POST'])
@handle_database_errors
def create_customer():
    tenant_id = session.get('current_tenant_id') or getattr(g, 'current_tenant_id', None) or 1
    customer_data = {
        'first_name': sanitize_input(request.form.get('first_name', '')),
        'family_name': sanitize_input(request.form.get('family_name', '')),
        'email': sanitize_input(request.form.get('email', '')),
        'phone': sanitize_input(request.form.get('phone', '')),
        'tenant_id': tenant_id,
        'tax_number': sanitize_input(request.form.get('tax_number', ''))
    }
    try:
        validation_result = validate_customer_data(customer_data)
        if not validation_result.is_valid:
            for error in validation_result.get_errors():
                flash(error, 'error')
            return render_template('customers/form.html', customer=customer_data, action='create')
        success, errors, customer = customer_service.create_customer(customer_data)
        if success:
            flash(f'Ügyfél sikeresen létrehozva: {customer.full_name}!', 'success')
            return redirect(url_for('main.customers'))
        else:
            for error in errors:
                flash(error, 'error')
            return render_template('customers/form.html', customer=customer_data, action='create')
    except Exception as e:
        logger.error(f"Failed to create customer: {e}", exc_info=True)
        flash(f'Hiba: {str(e)}', 'error')
        return render_template('customers/form.html', customer=customer_data, action='create')


@main_bp.route('/customers/<int:customer_id>')
@handle_database_errors
@log_function_call
def customer_detail(customer_id):
    try:
        customer = customer_service.get_customer_by_id(customer_id)
        if not customer:
            flash('Customer not found', 'error')
            return redirect(url_for('main.customers'))
        stats = customer_service.get_customer_statistics(customer_id)
        return render_template('customers/detail.html', customer=customer, stats=stats)
    except Exception as e:
        logger.error(f"Customer detail loading failed: {e}")
        flash('Failed to load customer details', 'error')
        return redirect(url_for('main.customers'))


@main_bp.route('/customers/<int:customer_id>/edit')
@handle_database_errors
def edit_customer(customer_id):
    try:
        customer = customer_service.get_customer_by_id(customer_id)
        if not customer:
            flash('Customer not found', 'error')
            return redirect(url_for('main.customers'))
        return render_template('customers/form.html', customer=customer, action='edit')
    except Exception as e:
        logger.error(f"Failed to load customer edit page: {e}")
        flash('Failed to load edit page', 'error')
        return redirect(url_for('main.customers'))


@main_bp.route('/customers/<int:customer_id>', methods=['POST'])
@handle_database_errors
def update_customer(customer_id):
    customer_data = {
        'first_name': sanitize_input(request.form.get('first_name', '')),
        'family_name': sanitize_input(request.form.get('family_name', '')),
        'email': sanitize_input(request.form.get('email', '')),
        'phone': sanitize_input(request.form.get('phone', '')),
        'tax_number': sanitize_input(request.form.get('tax_number', ''))
    }
    try:
        validation_result = validate_customer_data(customer_data)
        if not validation_result.is_valid:
            for error in validation_result.get_errors():
                flash(error, 'error')
            customer = customer_service.get_customer_by_id(customer_id)
            return render_template('customers/form.html', customer=customer, action='edit')
        success, errors, customer = customer_service.update_customer(customer_id, customer_data)
        if success:
            flash(f'Customer {customer.full_name} updated successfully!', 'success')
            return redirect(url_for('main.customer_detail', customer_id=customer_id))
        else:
            for error in errors:
                flash(error, 'error')
            customer = customer_service.get_customer_by_id(customer_id)
            return render_template('customers/form.html', customer=customer, action='edit')
    except Exception as e:
        logger.error(f"Failed to update customer: {e}")
        flash('Failed to update customer, please try again later', 'error')
        customer = customer_service.get_customer_by_id(customer_id)
        return render_template('customers/form.html', customer=customer, action='edit')


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/help')
def help_page():
    return render_template('help.html')


@main_bp.route('/fix-tenant-data2-xk9p2')
def fix_tenant_data2():
    import sqlalchemy as sa
    from app.extensions import db as _ext_db
    try:
        r1 = db.session.execute(sa.text("DELETE FROM customer WHERE tenant_id IS NULL AND email IN (SELECT email FROM customer WHERE tenant_id=1)"))
        r2 = db.session.execute(sa.text("UPDATE customer SET tenant_id=1 WHERE tenant_id IS NULL"))
        r3 = db.session.execute(sa.text("UPDATE job SET tenant_id=1 WHERE tenant_id IS NULL"))
        r4 = db.session.execute(sa.text("UPDATE service SET tenant_id=1 WHERE tenant_id IS NULL"))
        r5 = db.session.execute(sa.text("UPDATE part SET tenant_id=1 WHERE tenant_id IS NULL"))
        db.session.commit()
        return f'OK! deleted={r1.rowcount} customers={r2.rowcount} jobs={r3.rowcount} services={r4.rowcount} parts={r5.rowcount}'
    except Exception as e:
        db.session.rollback()
        return f'Error: {str(e)}'


@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@main_bp.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500


@main_bp.route('/fix-tenant-data3-xk9p2')
def fix_tenant_data3():
    import sqlalchemy as sa
    from app.extensions import db as _ext_db
    try:
        # Delete ALL null tenant customers (they're duplicates)
        r1 = db.session.execute(sa.text("DELETE FROM job WHERE tenant_id IS NULL"))
        r2 = db.session.execute(sa.text("DELETE FROM customer WHERE tenant_id IS NULL"))
        r3 = db.session.execute(sa.text("UPDATE service SET tenant_id=1 WHERE tenant_id IS NULL"))
        r4 = db.session.execute(sa.text("UPDATE part SET tenant_id=1 WHERE tenant_id IS NULL"))
        db.session.commit()
        return f'OK! deleted_jobs={r1.rowcount} deleted_customers={r2.rowcount} services={r3.rowcount} parts={r4.rowcount}'
    except Exception as e:
        db.session.rollback()
        return f'Error: {str(e)}'


@main_bp.route('/debug-jobs-xk9p2')
def debug_jobs():
    import sqlalchemy as sa
    from app.extensions import db as _ext_db
    from flask import session
    jobs = db.session.execute(sa.text('SELECT job_id, tenant_id, completed, customer FROM job')).fetchall()
    return f'Session tenant: {session.get("current_tenant_id")} | Jobs: {list(jobs)}'


@main_bp.route('/debug-customers-xk9p2')
def debug_customers():
    import sqlalchemy as sa
    from app.extensions import db as _ext_db
    customers = db.session.execute(sa.text('SELECT customer_id, tenant_id, first_name, family_name FROM customer')).fetchall()
    return f'Customers: {list(customers)}'


@main_bp.route('/fix-tenant-name-xk9p2')
def fix_tenant_name():
    import sqlalchemy as sa
    from app.extensions import db as _ext_db
    try:
        db.session.execute(sa.text("UPDATE tenant SET name='SOLVIOR CRM/ERP' WHERE tenant_id=1"))
        db.session.commit()
        result = db.session.execute(sa.text("SELECT name FROM tenant WHERE tenant_id=1")).fetchone()
        return f'OK! Tenant name: {result[0]}'
    except Exception as e:
        db.session.rollback()
        return f'Error: {str(e)}'


@main_bp.route('/migrate-tax-number-xk9p2')
def migrate_tax_number():
    import sqlalchemy as sa
    from app.extensions import db as _ext_db
    try:
        db.session.execute(sa.text("ALTER TABLE customer ADD COLUMN IF NOT EXISTS tax_number VARCHAR(20)"))
        db.session.commit()
        return 'OK! tax_number oszlop hozzáadva'
    except Exception as e:
        db.session.rollback()
        return f'Error: {str(e)}'


@main_bp.route('/fix-tenant-reset-xk9p2')
def fix_tenant_reset():
    import sqlalchemy as sa
    from app.extensions import db as _ext_db
    try:
        result = db.session.execute(sa.text("SELECT tenant_id, name, slug FROM tenant")).fetchall()
        if not result:
            db.session.execute(sa.text("""
                INSERT INTO tenant (tenant_id, name, slug, business_type, status, settings)
                VALUES (1, 'SOLVIOR CRM/ERP', 'solvior-crm', 'Vállalatirányítás', 'active', '{}')
                ON CONFLICT (tenant_id) DO UPDATE SET name='SOLVIOR CRM/ERP', settings='{}'
            """))
            db.session.commit()
            return 'Tenant létrehozva!'
        else:
            # Reset settings to empty to fix potential JSON issue
            db.session.execute(sa.text("UPDATE tenant SET settings='{}', logo_url=NULL WHERE tenant_id=1"))
            db.session.commit()
            return f'Tenant reset: {list(result)}'
    except Exception as e:
        db.session.rollback()
        return f'Error: {str(e)}'


@main_bp.route('/migrate-logo-column-xk9p2')
def migrate_logo_column():
    import sqlalchemy as sa
    from app.extensions import db as _ext_db
    try:
        db.session.execute(sa.text("ALTER TABLE tenant ALTER COLUMN logo_url TYPE TEXT"))
        db.session.commit()
        return 'OK! logo_url mező TEXT-re növelve'
    except Exception as e:
        db.session.rollback()
        return f'Error: {str(e)}'


@main_bp.route('/debug-tenant-xk9p2')
def debug_tenant():
    import sqlalchemy as sa
    from app.extensions import db as _ext_db
    result = db.session.execute(sa.text("SELECT tenant_id, name, settings, logo_url FROM tenant WHERE tenant_id=1")).fetchone()
    return f'Tenant: id={result[0]} name={result[1]} settings={result[2]} logo={str(result[3])[:50] if result[3] else None}'


@main_bp.route('/migrate-notes-xk9p2')
def migrate_notes():
    import sqlalchemy as sa
    from app.extensions import db as _ext_db
    try:
        db.session.execute(sa.text('ALTER TABLE job ADD COLUMN IF NOT EXISTS notes TEXT'))
        db.session.commit()
        return 'OK! notes oszlop hozzáadva.'
    except Exception as e:
        db.session.rollback()
        return f'Hiba: {e}'


@main_bp.route('/migrate-numeric-xk9p2')
def migrate_numeric():
    import sqlalchemy as sa
    from app.extensions import db as _ext_db
    try:
        db.session.execute(sa.text('ALTER TABLE job ALTER COLUMN total_cost TYPE NUMERIC(12,2)'))
        db.session.commit()
        return 'OK! total_cost mező kibővítve.'
    except Exception as e:
        db.session.rollback()
        return f'Hiba: {e}'


@main_bp.route('/check-fonts-xk9p2')
def check_fonts():
    import os, subprocess
    result = subprocess.run(['find', '/usr/share/fonts', '-name', '*.ttf'], 
                          capture_output=True, text=True)
    return f'<pre>{result.stdout}</pre>'


@main_bp.route('/customers/<int:customer_id>/delete', methods=['POST'])
@handle_database_errors
def delete_customer(customer_id):
    """Delete a customer"""
    from app.extensions import db as _ext_db
    from app.models.customer import Customer
    try:
        customer = db.session.get(Customer, customer_id)
        if not customer:
            flash('Ügyfél nem található', 'error')
            return redirect(url_for('main.customers'))
        name = customer.full_name
        db.session.delete(customer)
        db.session.commit()
        flash(f'Ügyfél törölve: {name}', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete customer failed: {e}")
        flash(f'Törlési hiba: {str(e)}', 'error')
    return redirect(url_for('main.customers'))



