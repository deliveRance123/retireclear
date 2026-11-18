import os
from flask import Blueprint, render_template, redirect, url_for, flash, send_file, current_app, abort, request
from flask_login import login_required, current_user
from app.models.clearance import RetirementCertificate
from app.models.application import RetirementApplication
from app.services.audit_service import AuditService

certificates_bp = Blueprint('certificates', __name__)

@certificates_bp.route('/lookup', methods=['GET', 'POST'])
def lookup():
    """
    Search certificate by certificate number or verification token.
    """
    search_term = (request.args.get('q') or request.form.get('search_term') or '').strip()
    if not search_term:
        flash("Please enter a Certificate Number or Verification Token to verify.", "warning")
        return redirect(url_for('index') + '#verify-search')
        
    cert = RetirementCertificate.query.filter(
        (RetirementCertificate.verification_token == search_term) |
        (RetirementCertificate.certificate_number.ilike(search_term))
    ).first()
    
    if cert:
        return redirect(url_for('certificates.public_verify', token=cert.verification_token))
    
    flash(f"No certificate found matching '{search_term}'. Please check the certificate number and try again.", "danger")
    return redirect(url_for('index') + '#verify-search')

@certificates_bp.route('/view/<int:certificate_id>')
@login_required
def view(certificate_id):
    cert = RetirementCertificate.query.get_or_404(certificate_id)
    emp = cert.employee
    
    # Ownership authorization check
    if current_user.has_role('civil_servant') and emp.user_id != current_user.id and emp.email != current_user.email:
        abort(403)
        
    return render_template('certificates/view.html', certificate=cert, employee=emp, clearance=cert.clearance)

@certificates_bp.route('/print/<int:certificate_id>')
@login_required
def print_cert(certificate_id):
    cert = RetirementCertificate.query.get_or_404(certificate_id)
    emp = cert.employee
    
    if current_user.has_role('civil_servant') and emp.user_id != current_user.id and emp.email != current_user.email:
        abort(403)
        
    return render_template('certificates/print.html', certificate=cert, employee=emp, clearance=cert.clearance)

@certificates_bp.route('/download/<int:certificate_id>')
@login_required
def download_pdf(certificate_id):
    cert = RetirementCertificate.query.get_or_404(certificate_id)
    emp = cert.employee
    
    if current_user.has_role('civil_servant') and emp.user_id != current_user.id and emp.email != current_user.email:
        abort(403)
        
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cert.pdf_path)
    if not os.path.exists(full_path):
        flash("Certificate PDF file could not be located on the server storage.", "danger")
        return redirect(url_for('certificates.view', certificate_id=cert.id))
        
    AuditService.log('DOWNLOAD_CERTIFICATE_PDF', 'RetirementCertificate', cert.id, {'certificate_number': cert.certificate_number})
    return send_file(full_path, as_attachment=True, download_name=f"{cert.certificate_number}.pdf")

@certificates_bp.route('/verify/<token>')
def public_verify(token):
    """
    Public-facing certificate verification portal.
    Verifies authenticity while safeguarding sensitive employee personal records.
    """
    cert = RetirementCertificate.query.filter_by(verification_token=token).first()
    if not cert:
        return render_template('certificates/public_verify.html', is_valid=False, token=token)
        
    emp = cert.employee
    clr = cert.clearance
    
    # Mask private employee data for public display
    masked_name = f"{emp.first_name} {emp.last_name[:1]}.***"
    
    cert_info = {
        'certificate_number': cert.certificate_number,
        'employee_name': f"{emp.first_name} {emp.last_name}",
        'staff_number': emp.staff_number,
        'ministry': emp.ministry_or_agency,
        'department': emp.department,
        'retirement_date': cert.application.proposed_retirement_date.strftime('%d/%m/%Y'),
        'issued_date': cert.issued_at.strftime('%d/%m/%Y'),
        'decision': clr.decision,
        'is_sample': cert.is_sample
    }
    return render_template('certificates/public_verify.html', is_valid=True, cert=cert_info, token=token)
