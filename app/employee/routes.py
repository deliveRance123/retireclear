import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.employee import Employee
from app.models.application import RetirementApplication, ApplicationStatus, ApplicationStage, ApplicationStatusHistory
from app.models.document import UploadedDocument, DocumentType
from app.models.verification import AIVerification
from app.models.clearance import RetirementCertificate
from app.models.notification import Notification
from app.models.user import Role
from app.auth.decorators import role_required
from app.employee.forms import RetirementApplicationForm, DocumentUploadForm
from app.services.document_service import DocumentService
from app.services.ocr_service import OCRService
from app.services.eligibility_service import EligibilityService
from app.services.anomaly_service import AnomalyDetectionService
from app.services.biometric_service import BiometricService
from app.services.audit_service import AuditService
from app.services.ai_verification_service import AIVerificationService

employee_bp = Blueprint('employee', __name__)

def get_current_employee():
    """Resolve current authenticated user to employee record."""
    if not current_user.is_authenticated:
        return None
    if current_user.employee_profile:
        return current_user.employee_profile
    # Check by email
    return Employee.query.filter_by(email=current_user.email).first()

@employee_bp.route('/my-documents')
@login_required
def my_documents():
    emp = get_current_employee()
    if not emp:
        return redirect(url_for('employee.dashboard'))
    app_obj = RetirementApplication.query.filter_by(employee_id=emp.id).order_by(RetirementApplication.created_at.desc()).first()
    if app_obj:
        return redirect(url_for('employee.documents', application_id=app_obj.id))
    flash("Please submit a retirement clearance notice first before uploading mandatory documents.", "info")
    return redirect(url_for('employee.apply'))

@employee_bp.route('/dashboard')
@login_required
@role_required('civil_servant', 'admin')
def dashboard():
    emp = get_current_employee()
    if not emp:
        flash("No civil service employment record is linked to your user account. Please contact your MDA HR department.", "warning")
        return render_template('employee/no_profile.html')
    
    application = RetirementApplication.query.filter_by(employee_id=emp.id).order_by(RetirementApplication.created_at.desc()).first()
    
    # Calculate document completeness
    required_types = [
        DocumentType.APPOINTMENT_LETTER,
        DocumentType.BIRTH_CERTIFICATE,
        DocumentType.STAFF_ID_CARD,
        DocumentType.PENSION_RECORD
    ]
    uploaded_types = [d.document_type for d in application.documents] if application else []
    missing_docs = [DocumentType.LABELS.get(t, t) for t in required_types if t not in uploaded_types]
    
    recent_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template(
        'employee/dashboard.html',
        employee=emp,
        application=application,
        missing_docs=missing_docs,
        notifications=recent_notifications
    )

@employee_bp.route('/apply', methods=['GET', 'POST'])
@login_required
@role_required('civil_servant', 'admin')
def apply():
    emp = get_current_employee()
    if not emp:
        flash("Employee profile required.", "danger")
        return redirect(url_for('employee.dashboard'))
        
    # Check for existing active application
    active_app = RetirementApplication.query.filter(
        RetirementApplication.employee_id == emp.id,
        RetirementApplication.current_status.notin_([ApplicationStatus.REJECTED])
    ).first()
    
    if active_app:
        flash(f"You already have an active retirement application: {active_app.application_reference}.", "info")
        return redirect(url_for('employee.tracking', application_id=active_app.id))
        
    form = RetirementApplicationForm()
    if form.validate_on_submit():
        ref_num = f"RET-{datetime.utcnow().year}-{emp.id:04d}-{uuid_snippet()}"
        
        new_app = RetirementApplication(
            application_reference=ref_num,
            employee_id=emp.id,
            reason_for_retirement=form.reason_for_retirement.data,
            proposed_retirement_date=form.proposed_retirement_date.data,
            current_status=ApplicationStatus.PENDING_HR,
            current_stage=ApplicationStage.HR,
            submission_date=datetime.utcnow()
        )
        db.session.add(new_app)
        db.session.flush()
        
        # Initial status log
        history = ApplicationStatusHistory(
            application_id=new_app.id,
            changed_by_user_id=current_user.id,
            previous_status=None,
            new_status=ApplicationStatus.PENDING_HR,
            comments=f"Application submitted by civil servant {emp.full_name}. Reason: {new_app.reason_for_retirement}."
        )
        db.session.add(history)
        
        # Notify HR officers
        hr_role = Role.query.filter_by(name='hr_officer').first()
        if hr_role:
            for hr in hr_role.users:
                notif = Notification(
                    user_id=hr.id,
                    title=f"New Retirement Application: {new_app.application_reference}",
                    message=f"{emp.full_name} ({emp.staff_number}) submitted retirement application for {emp.ministry_or_agency}.",
                    link=url_for('hr.verify_records', application_id=new_app.id),
                    category='info'
                )
                db.session.add(notif)
                
        db.session.commit()
        
        AuditService.log('SUBMIT_APPLICATION', 'RetirementApplication', new_app.id, {'reference': new_app.application_reference})
        flash(f"Retirement application successfully submitted! Your Reference: {new_app.application_reference}. Please proceed to upload required documents.", "success")
        return redirect(url_for('employee.documents', application_id=new_app.id))
        
    return render_template('employee/apply.html', employee=emp, form=form)

def uuid_snippet():
    import uuid
    return uuid.uuid4().hex[:4].upper()

@employee_bp.route('/documents/<int:application_id>', methods=['GET', 'POST'])
@login_required
@role_required('civil_servant', 'admin', 'hr_officer')
def documents(application_id):
    app_obj = RetirementApplication.query.get_or_404(application_id)
    emp = app_obj.employee
    
    # Ownership guard
    if current_user.has_role('civil_servant') and emp.user_id != current_user.id and emp.email != current_user.email:
        abort(403)
        
    form = DocumentUploadForm()
    if form.validate_on_submit():
        doc_type = form.document_type.data
        file_obj = form.file.data
        
        doc, err = DocumentService.save_document(file_obj, app_obj.id, doc_type, user_id=current_user.id)
        if err:
            flash(f"Upload Error: {err}", "danger")
        else:
            # Trigger OCR Extraction asynchronously / immediately
            ocr_doc, ocr_err = OCRService.process_document(doc.id, emp)
            
            # Run AI verification & anomaly screening
            run_ai_pipeline(app_obj, emp)
            
            AuditService.log('UPLOAD_DOCUMENT', 'UploadedDocument', doc.id, {
                'doc_type': doc_type,
                'application_ref': app_obj.application_reference
            })
            flash(f"{doc.display_type} uploaded and OCR analyzed successfully.", "success")
            return redirect(url_for('employee.documents', application_id=app_obj.id))
            
    return render_template('employee/documents.html', application=app_obj, employee=emp, form=form)

def run_ai_pipeline(app_obj, emp):
    """Execute AI eligibility engine and anomaly detection on application."""
    return AIVerificationService.run_pipeline(app_obj, emp)

@employee_bp.route('/tracking/<int:application_id>')
@login_required
def tracking(application_id):
    app_obj = RetirementApplication.query.get_or_404(application_id)
    emp = app_obj.employee
    
    if current_user.has_role('civil_servant') and emp.user_id != current_user.id and emp.email != current_user.email:
        abort(403)
        
    ai_ver = app_obj.latest_ai_verification
    return render_template('employee/tracking.html', application=app_obj, employee=emp, ai_ver=ai_ver)

@employee_bp.route('/profile')
@login_required
def profile():
    emp = get_current_employee()
    if not emp:
        flash("No linked civil servant profile.", "warning")
        return redirect(url_for('employee.dashboard'))
    return render_template('employee/profile.html', employee=emp)
