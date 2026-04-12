"""
Technician Routes Blueprint
Contains work order management, service and parts addition functionality
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from datetime import date, datetime
import logging
from app.services.job_service import JobService
from app.services.customer_service import CustomerService
from app.models.service import Service
from app.models.part import Part
from app.utils.decorators import handle_database_errors, log_function_call, validate_pagination
from app.utils.validators import sanitize_input, validate_positive_integer, validate_date

# Create blueprint
technician_bp = Blueprint('technician', __name__)
logger = logging.getLogger(__name__)

# Initialize services
job_service = JobService()
customer_service = CustomerService()


def _load_unicode_font():
    """Load Unicode TTF font from project static/fonts folder."""
    import os
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reg_path = os.path.join(base_dir, 'static', 'fonts', 'DejaVuSans.ttf')
    bold_path = os.path.join(base_dir, 'static', 'fonts', 'DejaVuSans-Bold.ttf')

    try:
        if os.path.exists(reg_path):
            pdfmetrics.registerFont(TTFont('DejaVuSans', reg_path))
            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold_path))
                return 'DejaVuSans', 'DejaVuSans-Bold'
            return 'DejaVuSans', 'DejaVuSans'
    except Exception:
        pass
    return 'Helvetica', 'Helvetica-Bold'

def require_technician_login():
    """Check technician login status"""
    if not session.get('logged_in'):
        flash('Please log in first', 'warning')
        return redirect(url_for('auth.login'))
    return None


@technician_bp.route('/current-jobs', methods=['GET', 'POST'])
@validate_pagination
@handle_database_errors
@log_function_call
def current_jobs(page=1, per_page=10):
    """Current work order list"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        jobs, total, total_pages = job_service.get_current_jobs(page, per_page)

        return render_template('technician/current_jobs.html',
                             data=jobs,
                             jobs=jobs,
                             page=page,
                             per_page=per_page,
                             total=total,
                             total_pages=total_pages,
                             prev_page=max(1, page-1),
                             next_page=page+1)

    except Exception as e:
        logger.error(f"Failed to get current work orders: {e}")
        flash('Failed to load work orders', 'error')
        return render_template('technician/current_jobs.html',
                             data=[],
                             jobs=[],
                             page=1,
                             per_page=per_page,
                             total=0,
                             total_pages=0,
                             prev_page=1,
                             next_page=2)


@technician_bp.route('/jobs/<int:job_id>')
@handle_database_errors
@log_function_call
def job_detail(job_id):
    """Work order detail page"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        job_details = job_service.get_job_details(job_id)

        if not job_details:
            flash('Work order does not exist', 'error')
            return redirect(url_for('technician.current_jobs'))

        return render_template('technician/job_detail.html',
                             data=job_details.get('job_info', {}),
                             services=job_details.get('services', []),
                             parts=job_details.get('parts', []),
                             all_services=job_details.get('all_services', []),
                             all_parts=job_details.get('all_parts', []))

    except Exception as e:
        logger.error(f"Failed to get work order details (ID: {job_id}): {e}")
        flash('Failed to load work order details', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/jobs/<int:job_id>/notes', methods=['POST'])
@handle_database_errors
def save_notes(job_id):
    """Save notes for a job"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response
    try:
        from app.models.job import Job
        from app.extensions import db
        job = db.session.get(Job, job_id)
        if not job:
            flash('Munka nem található', 'error')
            return redirect(url_for('technician.current_jobs'))
        job.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Megjegyzés mentve!', 'success')
    except Exception as e:
        logger.error(f"Failed to save notes: {e}")
        db.session.rollback()
        flash('Hiba a mentés során', 'error')
    return redirect(url_for('technician.job_detail', job_id=job_id))


@technician_bp.route('/jobs/<int:job_id>/worksheet')
def generate_worksheet(job_id):
    """Generate PDF worksheet for a job"""
    from flask import make_response, session
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    from app.models.job import Job
    from app.models.tenant import Tenant
    from app.extensions import db
    import datetime, os

    job = db.session.get(Job, job_id)
    if not job:
        flash('Munka nem található', 'error')
        return redirect(url_for('technician.current_jobs'))

    tenant_id = session.get('current_tenant_id') or 1
    tenant = Tenant.find_by_id(tenant_id)
    settings = tenant.settings or {} if tenant else {}
    customer = job.customer_rel
    services = job.get_services()
    parts = job.get_parts()

    # Unicode font
    unicode_font, unicode_font_bold = _load_unicode_font()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = unicode_font
    story = []

    primary_color = colors.HexColor('#1e3a5f')
    accent_color = colors.HexColor('#e87e04')
    white = colors.white

    # Fejléc
    ws_num = f"ML-{datetime.date.today().year}-{job_id:04d}"
    header_data = [[
        Paragraph(f'<font color="white" size="22"><b>{tenant.name if tenant else "K&amp;B Autójavító"}</b></font>', styles['Normal']),
        Paragraph(f'<font color="white" size="10"><b>Munkalap</b><br/>{ws_num}<br/>{datetime.date.today().strftime("%Y. %m. %d.")}</font>', styles['Normal'])
    ]]
    header_table = Table(header_data, colWidths=[10*cm, 8*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary_color),
        ('TOPPADDING', (0,0), (-1,-1), 18),
        ('BOTTOMPADDING', (0,0), (-1,-1), 18),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))

    # Ügyfél + munka adatok
    info_style = ParagraphStyle('info', fontSize=9, leading=14, fontName=unicode_font)
    bold_style = ParagraphStyle('bold', fontSize=9, leading=14, fontName=unicode_font_bold)

    buyer_name = f"{customer.first_name} {customer.family_name}" if customer else "N/A"
    left_lines = ['<b>Ügyfél adatai</b>', buyer_name,
                  customer.phone if customer else '',
                  customer.email if customer else '']
    right_lines = ['<b>Munka adatai</b>',
                   f'Munkalap sz.: {ws_num}',
                   f'Dátum: {job.job_date.strftime("%Y. %m. %d.") if job.job_date else "N/A"}',
                   f'Státusz: {"Befejezett" if job.completed else "Folyamatban"}']

    info_data = [[
        Paragraph('<br/>'.join([l for l in left_lines if l]), info_style),
        Paragraph('<br/>'.join([l for l in right_lines if l]), info_style),
    ]]
    info_table = Table(info_data, colWidths=[9*cm, 9*cm])
    info_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('LINEAFTER', (0,0), (0,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

    # Szolgáltatások
    th_style = ParagraphStyle('th', fontSize=9, textColor=white, fontName=unicode_font_bold)
    cell_style = ParagraphStyle('cell', fontSize=9, fontName=unicode_font)

    if services:
        story.append(Paragraph('<b>Elvégzett munkák</b>', ParagraphStyle('h', fontSize=11, fontName=unicode_font_bold, spaceAfter=6)))
        svc_data = [[Paragraph('Megnevezés', th_style), Paragraph('Menny.', th_style), Paragraph('Megjegyzés', th_style)]]
        for s in services:
            svc_data.append([
                Paragraph(s['service_name'], cell_style),
                Paragraph(str(s['qty']), cell_style),
                Paragraph('', cell_style),
            ])
        svc_table = Table(svc_data, colWidths=[9*cm, 2.5*cm, 6.5*cm])
        svc_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, colors.HexColor('#f8fafc')]),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(svc_table)
        story.append(Spacer(1, 0.4*cm))

    # Alkatrészek
    if parts:
        story.append(Paragraph('<b>Felhasznált alkatrészek</b>', ParagraphStyle('h2', fontSize=11, fontName=unicode_font_bold, spaceAfter=6)))
        parts_data = [[Paragraph('Alkatrész', th_style), Paragraph('Menny.', th_style), Paragraph('Megjegyzés', th_style)]]
        for p in parts:
            parts_data.append([
                Paragraph(p['part_name'], cell_style),
                Paragraph(str(p['qty']), cell_style),
                Paragraph('', cell_style),
            ])
        parts_table = Table(parts_data, colWidths=[9*cm, 2.5*cm, 6.5*cm])
        parts_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, colors.HexColor('#f8fafc')]),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(parts_table)
        story.append(Spacer(1, 0.4*cm))

    # Aláírás sor — megjegyzés felette, több space-szel
    story.append(Spacer(1, 1.5*cm))

    if job.notes:
        story.append(Paragraph('<b>Megjegyzés</b>', ParagraphStyle('h3', fontSize=11, fontName=unicode_font_bold, spaceAfter=14)))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(job.notes, ParagraphStyle('notes', fontSize=9, fontName=unicode_font, leading=14,
                                                          borderPadding=10, backColor=colors.HexColor('#fffbeb'),
                                                          borderColor=colors.HexColor('#f59e0b'), borderWidth=0.5)))
        story.append(Spacer(1, 1.2*cm))

    sign_data = [[
        Paragraph('Szerel\u0151 al\u00e1\u00edr\u00e1sa: ________________________', cell_style),
        Paragraph('\u00dcgyf\u00e9l al\u00e1\u00edr\u00e1sa: ________________________', cell_style),
    ]]
    sign_table = Table(sign_data, colWidths=[9*cm, 9*cm])
    sign_table.setStyle(TableStyle([('PADDING', (0,0), (-1,-1), 4)]))
    story.append(sign_table)

    # Footer
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0')))
    footer_style = ParagraphStyle('footer', fontSize=8, textColor=colors.HexColor('#94a3b8'),
                                   alignment=TA_CENTER, fontName=unicode_font)
    story.append(Paragraph(f'Powered by RepairOS · {tenant.name if tenant else "K&B Autójavító"}', footer_style))

    doc.build(story)
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=munkalap-{ws_num}.pdf'
    return response



@technician_bp.route('/jobs/<int:job_id>/modify')
@handle_database_errors
@log_function_call
def modify_job(job_id):
    """Modify work order page"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        job_details = job_service.get_job_details(job_id)

        if not job_details:
            flash('Work order does not exist', 'error')
            return redirect(url_for('technician.current_jobs'))

        if job_details.get('job_completed'):
            flash('Cannot modify completed work order', 'warning')
            return redirect(url_for('technician.job_detail', job_id=job_id))

        return render_template('technician/modify_job.html',
                             job_details=job_details)

    except Exception as e:
        logger.error(f"Failed to load work order modification page (ID: {job_id}): {e}")
        flash('Failed to load modification page', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/jobs/<int:job_id>/add-service', methods=['POST'])
@handle_database_errors
def add_service_to_job(job_id):
    """Add service to work order"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        service_id = request.form.get('service_id', type=int)
        quantity = request.form.get('quantity', type=int) or 1

        if not service_id or service_id <= 0:
            flash('Válassz érvényes szolgáltatást!', 'error')
            return redirect(url_for('technician.job_detail', job_id=job_id))

        if not quantity or quantity <= 0:
            flash('Érvényes mennyiséget adj meg!', 'error')
            return redirect(url_for('technician.job_detail', job_id=job_id))

        success, errors = job_service.add_service_to_job(job_id, service_id, quantity)

        if success:
            flash('Szolgáltatás hozzáadva!', 'success')
        else:
            for error in errors:
                flash(error, 'error')

        return redirect(url_for('technician.job_detail', job_id=job_id))

    except Exception as e:
        logger.error(f"Failed to add service: {e}")
        flash('Hiba a szolgáltatás hozzáadásakor', 'error')
        return redirect(url_for('technician.job_detail', job_id=job_id))


@technician_bp.route('/jobs/<int:job_id>/add-part', methods=['POST'])
@handle_database_errors
def add_part_to_job(job_id):
    """Add part to work order"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        part_id = request.form.get('part_id', type=int)
        quantity = request.form.get('quantity', type=int) or 1

        if not part_id or part_id <= 0:
            flash('Válassz érvényes alkatrészt!', 'error')
            return redirect(url_for('technician.job_detail', job_id=job_id))

        if not quantity or quantity <= 0:
            flash('Érvényes mennyiséget adj meg!', 'error')
            return redirect(url_for('technician.job_detail', job_id=job_id))

        success, errors = job_service.add_part_to_job(job_id, part_id, quantity)

        if success:
            flash('Alkatrész hozzáadva!', 'success')
        else:
            for error in errors:
                flash(error, 'error')

        return redirect(url_for('technician.job_detail', job_id=job_id))

    except Exception as e:
        logger.error(f"Failed to add part: {e}")
        flash('Hiba az alkatrész hozzáadásakor', 'error')
        return redirect(url_for('technician.job_detail', job_id=job_id))


@technician_bp.route('/jobs/<int:job_id>/complete', methods=['POST'])
@handle_database_errors
def complete_job(job_id):
    """Mark work order as completed"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        success, errors = job_service.mark_job_as_completed(job_id)

        if success:
            flash('Work order marked as completed!', 'success')
            return redirect(url_for('technician.job_detail', job_id=job_id))
        else:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('technician.modify_job', job_id=job_id))

    except Exception as e:
        logger.error(f"Failed to mark work order as completed: {e}")
        flash('Failed to mark as completed, please try again later', 'error')
        return redirect(url_for('technician.modify_job', job_id=job_id))


@technician_bp.route('/jobs/new', methods=['GET', 'POST'])
@handle_database_errors
def new_job():
    """Create new work order page (GET) and form submit (POST)"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    if request.method == 'POST':
        try:
            customer_id = request.form.get('customer_id', type=int)
            job_date_str = sanitize_input(request.form.get('job_date', ''))

            if not customer_id or not validate_positive_integer(customer_id):
                flash('Kérjük válasszon érvényes ügyfelet', 'error')
                customers = customer_service.get_all_customers()
                return render_template('technician/new_job.html',
                                     customers=customers,
                                     min_date=date.today().isoformat())

            if not job_date_str or not validate_date(job_date_str):
                flash('Kérjük adjon meg érvényes dátumot', 'error')
                customers = customer_service.get_all_customers()
                return render_template('technician/new_job.html',
                                     customers=customers,
                                     min_date=date.today().isoformat())

            job_date = datetime.strptime(job_date_str, '%Y-%m-%d').date()
            success, errors, job = job_service.create_job(customer_id, job_date)

            if success:
                flash('Munkamegrendelés sikeresen létrehozva!', 'success')
                return redirect(url_for('technician.modify_job', job_id=job.job_id))
            else:
                for error in errors:
                    flash(error, 'error')
                customers = customer_service.get_all_customers()
                return render_template('technician/new_job.html',
                                     customers=customers,
                                     min_date=date.today().isoformat())

        except Exception as e:
            logger.error(f"Failed to create work order: {e}", exc_info=True)
            flash(f'Hiba a munkamegrendelés létrehozásakor: {str(e)}', 'error')
            customers = customer_service.get_all_customers()
            return render_template('technician/new_job.html',
                                 customers=customers,
                                 min_date=date.today().isoformat())

    try:
        customers = customer_service.get_all_customers()
        return render_template('technician/new_job.html',
                             customers=customers,
                             min_date=date.today().isoformat())

    except Exception as e:
        logger.error(f"Failed to load new work order page: {e}")
        flash('Failed to load page', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/jobs', methods=['POST'])
@handle_database_errors
def create_job():
    """Create new work order"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        customer_id = request.form.get('customer_id', type=int)
        job_date_str = sanitize_input(request.form.get('job_date', ''))

        if not customer_id or not validate_positive_integer(customer_id):
            flash('Please select a valid customer', 'error')
            customers = customer_service.get_all_customers()
            return render_template('technician/new_job.html',
                                 customers=customers,
                                 min_date=date.today().isoformat())

        if not job_date_str or not validate_date(job_date_str):
            flash('Please enter a valid work date', 'error')
            customers = customer_service.get_all_customers()
            return render_template('technician/new_job.html',
                                 customers=customers,
                                 min_date=date.today().isoformat())

        job_date = datetime.strptime(job_date_str, '%Y-%m-%d').date()

        success, errors, job = job_service.create_job(customer_id, job_date)

        if success:
            flash('Work order created successfully!', 'success')
            return redirect(url_for('technician.modify_job', job_id=job.job_id))
        else:
            for error in errors:
                flash(error, 'error')
            customers = customer_service.get_all_customers()
            return render_template('technician/new_job.html',
                                 customers=customers,
                                 min_date=date.today().isoformat())

    except Exception as e:
        logger.error(f"Failed to create work order: {e}")
        flash('Failed to create work order, please try again later', 'error')
        return redirect(url_for('technician.current_jobs'))


@technician_bp.route('/services')
@handle_database_errors
@log_function_call
def services():
    """Service list page"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        services = Service.get_all_sorted()
        return render_template('technician/services.html',
                             services=services)

    except Exception as e:
        logger.error(f"Failed to get service list: {e}")
        flash('Failed to load service list', 'error')
        return render_template('technician/services.html',
                             services=[])


@technician_bp.route('/parts')
@handle_database_errors
@log_function_call
def parts():
    """Parts list page"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        parts = Part.get_all_sorted()
        return render_template('technician/parts.html',
                             parts=parts)

    except Exception as e:
        logger.error(f"Failed to get parts list: {e}")
        flash('Failed to load parts list', 'error')
        return render_template('technician/parts.html',
                             parts=[])


@technician_bp.route('/dashboard')
@handle_database_errors
@log_function_call
def dashboard():
    """Technician dashboard"""
    redirect_response = require_technician_login()
    if redirect_response:
        return redirect_response

    try:
        job_stats = job_service.get_job_statistics()
        today = date.today()
        recent_jobs, _, _ = job_service.get_current_jobs(page=1, per_page=10)

        today_jobs = [job for job in recent_jobs
                     if getattr(job, 'job_date', None) == today]

        return render_template('technician/dashboard.html',
                             job_stats=job_stats,
                             recent_jobs=recent_jobs[:5],
                             today_jobs=today_jobs,
                             current_date=today)

    except Exception as e:
        logger.error(f"Technician dashboard loading failed: {e}")
        flash('Failed to load dashboard', 'error')
        return render_template('technician/dashboard.html',
                             job_stats={},
                             recent_jobs=[],
                             today_jobs=[],
                             current_date=date.today())


# API endpoints
@technician_bp.route('/api/services')
@handle_database_errors
def api_get_services():
    """API: Get all services"""
    try:
        services = Service.get_all_sorted()
        return jsonify([{
            'service_id': s.service_id,
            'service_name': s.service_name,
            'cost': float(s.cost) if s.cost else 0
        } for s in services])

    except Exception as e:
        logger.error(f"Failed to get services API: {e}")
        return jsonify({'error': 'Failed to get service list'}), 500


@technician_bp.route('/api/parts')
@handle_database_errors
def api_get_parts():
    """API: Get all parts"""
    try:
        parts = Part.get_all_sorted()
        return jsonify([{
            'part_id': p.part_id,
            'part_name': p.part_name,
            'cost': float(p.cost) if p.cost else 0
        } for p in parts])

    except Exception as e:
        logger.error(f"Failed to get parts API: {e}")
        return jsonify({'error': 'Failed to get parts list'}), 500


@technician_bp.route('/api/jobs/<int:job_id>/status')
@handle_database_errors
def api_get_job_status(job_id):
    """API: Get work order status"""
    try:
        job = job_service.get_job_by_id(job_id)
        if not job:
            return jsonify({'error': 'Work order not found'}), 404

        return jsonify({
            'job_id': job.job_id,
            'completed': bool(job.completed),
            'paid': bool(job.paid),
            'total_cost': float(job.total_cost) if job.total_cost else 0,
            'status_text': job.status_text
        })

    except Exception as e:
        logger.error(f"Failed to get work order status: {e}")
        return jsonify({'error': 'Failed to get status'}), 500


@technician_bp.route('/jobs/<int:job_id>/invoice')
def generate_invoice(job_id):
    """Generate PDF invoice for a job"""
    from flask import make_response, session
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    from app.models.job import Job
    from app.models.tenant import Tenant
    from app.extensions import db
    import datetime

    # Load job
    job = db.session.get(Job, job_id)
    if not job:
        flash('Munka nem található', 'error')
        return redirect(url_for('technician.current_jobs'))

    # Register Unicode font (DejaVu supports Hungarian chars: á, é, í, ó, ö, ő, ú, ü, ű)
    import os
    unicode_font, unicode_font_bold = _load_unicode_font()

    # Load tenant settings
    tenant_id = session.get('current_tenant_id') or 1
    tenant = Tenant.find_by_id(tenant_id)
    settings = tenant.settings or {} if tenant else {}

    # Customer info
    customer = job.customer_rel
    services = job.get_services()
    parts = job.get_parts()

    # Invoice number
    invoice_num = f"KNB-{datetime.date.today().year}-{job_id:04d}"

    # PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    # Override default font to Unicode-capable one
    for style in styles.byName.values():
        style.fontName = unicode_font
    story = []

    # Colors
    primary_color = colors.HexColor('#1e3a5f')
    accent_color = colors.HexColor('#e87e04')
    white = colors.white

    # Header background
    header_data = [[
        Paragraph(f'<font color="white" size="22"><b>{tenant.name if tenant else "K&amp;B Autójavító"}</b></font>', styles['Normal']),
        Paragraph(f'<font color="white" size="10"><b>Számla</b><br/>{invoice_num}<br/>{datetime.date.today().strftime("%Y. %m. %d.")}</font>', styles['Normal'])
    ]]
    header_table = Table(header_data, colWidths=[10*cm, 8*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), accent_color),
        ('TEXTCOLOR', (0,0), (-1,-1), white),
        ('TOPPADDING', (0,0), (-1,-1), 18),
        ('BOTTOMPADDING', (0,0), (-1,-1), 18),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
        ('ROUNDEDCORNERS', [8]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))

    # Seller / Buyer info
    seller_lines = [
        '<b>Eladó</b>',
        tenant.name if tenant else 'K&B Autojavito',
        settings.get('company_reg', ''),
        tenant.address if tenant else '',
        f'Adószám: {settings.get("tax_id", "")}' if settings.get('tax_id') else '',
        f'Bankszámlaszám: {settings.get("bank_account", "")}' if settings.get('bank_account') else '',
    ]
    seller_text = '<br/>'.join([l for l in seller_lines if l])

    buyer_name = f"{customer.first_name} {customer.family_name}" if customer else "N/A"
    buyer_lines = [
        '<b>Vev\u0151</b>',
        buyer_name,
        customer.phone if customer else '',
        customer.email if customer else '',
        f'Adószám: {customer.tax_number}' if customer and getattr(customer, 'tax_number', None) else '',
    ]
    buyer_text = '<br/>'.join([l for l in buyer_lines if l])

    info_style = ParagraphStyle('info', fontSize=9, leading=14, fontName=unicode_font)
    info_data = [[
        Paragraph(seller_text, info_style),
        Paragraph(buyer_text, info_style)
    ]]
    info_table = Table(info_data, colWidths=[9*cm, 9*cm])
    info_table.setStyle(TableStyle([
        ('BOX', (0,0), (0,0), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (1,0), (1,0), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

    # Items table header
    tax_rate = float(settings.get('tax_rate', 27))
    header_style = ParagraphStyle('th', fontSize=9, textColor=white, fontName=unicode_font_bold)
    items_data = [[
        Paragraph('Tétel', header_style),
        Paragraph('Menny.', header_style),
        Paragraph('Nettó', header_style),
        Paragraph(f'ÁFA {int(tax_rate)}%', header_style),
        Paragraph('Bruttó', header_style),
    ]]

    # Add services
    brutto_total = 0
    cell_style = ParagraphStyle('cell', fontSize=9, fontName=unicode_font)
    for svc in services:
        netto = float(svc['cost']) * int(svc['qty'])
        afa = netto * tax_rate / 100
        brutto = netto + afa
        brutto_total += brutto
        items_data.append([
            Paragraph(svc['service_name'], cell_style),
            Paragraph(f"{svc['qty']} db", cell_style),
            Paragraph(f"{int(netto):,} Ft".replace(',', ' '), cell_style),
            Paragraph(f"{int(afa):,} Ft".replace(',', ' '), cell_style),
            Paragraph(f"{int(brutto):,} Ft".replace(',', ' '), cell_style),
        ])

    # Add parts
    for part in parts:
        netto = float(part['cost']) * int(part['qty'])
        afa = netto * tax_rate / 100
        brutto = netto + afa
        brutto_total += brutto
        items_data.append([
            Paragraph(part['part_name'], cell_style),
            Paragraph(f"{part['qty']} db", cell_style),
            Paragraph(f"{int(netto):,} Ft".replace(',', ' '), cell_style),
            Paragraph(f"{int(afa):,} Ft".replace(',', ' '), cell_style),
            Paragraph(f"{int(brutto):,} Ft".replace(',', ' '), cell_style),
        ])

    items_table = Table(items_data, colWidths=[7*cm, 2*cm, 3*cm, 3*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.3*cm))

    # Total
    total_style = ParagraphStyle('total', fontSize=12, fontName=unicode_font_bold, alignment=TA_RIGHT)
    total_data = [[
        Paragraph(f'<b>Bruttó összesen: {int(brutto_total):,} Ft</b>'.replace(',', ' '), total_style)
    ]]
    total_table = Table(total_data, colWidths=[18*cm])
    total_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT'), ('PADDING', (0,0), (-1,-1), 8)]))
    story.append(total_table)

    # Footer
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
    footer_style = ParagraphStyle('footer', fontSize=8, textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER, fontName=unicode_font)
    story.append(Paragraph(f'Powered by SolvioRepair · {tenant.name if tenant else "K&B Autojavito"}', footer_style))

    doc.build(story)
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=szamla-{invoice_num}.pdf'
    return response
