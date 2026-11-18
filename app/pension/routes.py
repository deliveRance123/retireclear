from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.application import RetirementApplication, ApplicationStatus, ApplicationStage, ApplicationStatusHistory
from app.models.clearance import Clearance, RetirementCertificate
from app.models.verification import AIVerification
from app.models.notification import Notification
from app.auth.decorators import role_required
from app.services.certificate_service import CertificateService
from app.services.audit_service import AuditService

pension_bp = Blueprint('pension', __name__)

@pension_bp.route('/dashboard')
@login_required
@role_required('pension_officer', 'admin')
def dashboard():
    awaiting_pension = RetirementApplication.query.filter_by(
        current_status=ApplicationStatus.PENDING_PENSION
    ).count()
    
    total_approved = RetirementApplication.query.filter_by(
        current_status=ApplicationStatus.APPROVED
    ).count()
    
    total_rejected = RetirementApplication.query.filter_by(
        current_status=ApplicationStatus.REJECTED
    ).count()
    
    further_verification = RetirementApplication.query.filter_by(
        current_status=ApplicationStatus.FURTHER_VERIFICATION
    ).count()
    
    recent_applications = RetirementApplication.query.filter(
        RetirementApplication.current_status.in_([
            ApplicationStatus.PENDING_PENSION,
            ApplicationStatus.FURTHER_VERIFICATION
        ])
    ).order_by(RetirementApplication.updated_at.desc()).limit(8).all()
    
    recent_clearances = Clearance.query.order_by(Clearance.created_at.desc()).limit(6).all()
    
    return render_template(
        'pension/dashboard.html',
        awaiting_pension=awaiting_pension,
        total_approved=total_approved,
        total_rejected=total_rejected,
        further_verification=further_verification,
        recent_applications=recent_applications,
        recent_clearances=recent_clearances
    )

@pension_bp.route('/applications')
@login_required
@role_required('pension_officer', 'admin')
def applications():
    query = RetirementApplication.query
    status = request.args.get('status')
    search = request.args.get('search', '').strip()
    
    if status:
        query = query.filter(RetirementApplication.current_status == status)
    if search:
        query = query.join(RetirementApplication.employee).filter(
            (RetirementApplication.application_reference.ilike(f'%{search}%')) |
            (RetirementApplication.employee.has(staff_number=search))
        )
        
    apps = query.order_by(RetirementApplication.updated_at.desc()).all()
    return render_template('pension/applications.html', applications=apps, current_status=status, search=search)

@pension_bp.route('/review/<int:application_id>', methods=['GET', 'POST'])
@login_required
@role_required('pension_officer', 'admin')
def application_review(application_id):
    app_obj = RetirementApplication.query.get_or_404(application_id)
    emp = app_obj.employee
    ai_ver = app_obj.latest_ai_verification
    
    if request.method == 'POST':
        decision = request.form.get('decision')
        remarks = request.form.get('remarks', '').strip()
        
        if decision == 'approve':
            app_obj.current_status = ApplicationStatus.APPROVED
            app_obj.current_stage = ApplicationStage.COMPLETED
            app_obj.pension_reviewed_at = datetime.utcnow()
            app_obj.pension_officer_id = current_user.id
            app_obj.pension_notes = remarks
            
            # Create Clearance record
            clearance = Clearance(
                application_id=app_obj.id,
                approving_officer_id=current_user.id,
                decision='Approved',
                decision_date=datetime.utcnow(),
                remarks=remarks,
                pension_entitlement_status='Cleared for Full Statutory Benefits',
                gratuity_applicable=True,
                monthly_pension_applicable=True
            )
            db.session.add(clearance)
            db.session.flush()
            
            # Automatically generate official retirement clearance certificate
            cert = CertificateService.generate_certificate(clearance, is_sample=True)
            app_obj.current_status = ApplicationStatus.CERTIFICATE_GENERATED
            
            # Add to Status History
            history = ApplicationStatusHistory(
                application_id=app_obj.id,
                changed_by_user_id=current_user.id,
                previous_status=ApplicationStatus.PENDING_PENSION,
                new_status=ApplicationStatus.CERTIFICATE_GENERATED,
                comments=f"Retirement Clearance Approved by Pension Officer {current_user.full_name}. Certificate {cert.certificate_number} issued. Remarks: {remarks}"
            )
            db.session.add(history)
            
            # Notify the employee if user account exists
            if emp.user:
                notif = Notification(
                    user_id=emp.user.id,
                    title="Congratulations: Retirement Clearance Approved!",
                    message=f"Your retirement clearance application ({app_obj.application_reference}) has been officially approved. Certificate {cert.certificate_number} is available for download.",
                    link=url_for('certificates.view', certificate_id=cert.id),
                    category='success'
                )
                db.session.add(notif)
                
            db.session.commit()
            AuditService.log('PENSION_APPROVE_CLEARANCE', 'RetirementApplication', app_obj.id, {
                'certificate_number': cert.certificate_number,
                'decision': 'Approved'
            })
            flash(f"Application {app_obj.application_reference} approved! Retirement Certificate {cert.certificate_number} generated.", "success")
            return redirect(url_for('pension.dashboard'))
            
        elif decision == 'reject':
            rejection_reason = request.form.get('rejection_reason', 'Failed statutory verification criteria.').strip()
            app_obj.current_status = ApplicationStatus.REJECTED
            app_obj.current_stage = ApplicationStage.COMPLETED
            app_obj.rejection_reason = rejection_reason
            app_obj.pension_reviewed_at = datetime.utcnow()
            app_obj.pension_officer_id = current_user.id
            
            history = ApplicationStatusHistory(
                application_id=app_obj.id,
                changed_by_user_id=current_user.id,
                previous_status=ApplicationStatus.PENDING_PENSION,
                new_status=ApplicationStatus.REJECTED,
                comments=f"Application Rejected by Pension Officer {current_user.full_name}. Reason: {rejection_reason}"
            )
            db.session.add(history)
            
            if emp.user:
                notif = Notification(
                    user_id=emp.user.id,
                    title="Retirement Clearance Application Status Update",
                    message=f"Your application ({app_obj.application_reference}) could not be approved. Reason: {rejection_reason}",
                    link=url_for('employee.tracking', application_id=app_obj.id),
                    category='danger'
                )
                db.session.add(notif)
                
            db.session.commit()
            AuditService.log('PENSION_REJECT_APPLICATION', 'RetirementApplication', app_obj.id, {'reason': rejection_reason})
            flash(f"Application {app_obj.application_reference} has been marked as Rejected.", "warning")
            return redirect(url_for('pension.dashboard'))
            
        elif decision == 'request_verification':
            req_reason = request.form.get('request_notes', 'Additional clarification requested on service records.').strip()
            app_obj.current_status = ApplicationStatus.FURTHER_VERIFICATION
            app_obj.current_stage = ApplicationStage.HR
            
            history = ApplicationStatusHistory(
                application_id=app_obj.id,
                changed_by_user_id=current_user.id,
                previous_status=ApplicationStatus.PENDING_PENSION,
                new_status=ApplicationStatus.FURTHER_VERIFICATION,
                comments=f"Further verification requested by Pension Officer {current_user.full_name}. Notes: {req_reason}"
            )
            db.session.add(history)
            
            if emp.user:
                notif = Notification(
                    user_id=emp.user.id,
                    title="Additional Verification Required",
                    message=f"Pension Officers requested further verification for application {app_obj.application_reference}: {req_reason}",
                    link=url_for('employee.documents', application_id=app_obj.id),
                    category='warning'
                )
                db.session.add(notif)
                
            db.session.commit()
            AuditService.log('PENSION_REQUEST_VERIFICATION', 'RetirementApplication', app_obj.id, {'notes': req_reason})
            flash(f"Application {app_obj.application_reference} returned for further verification.", "info")
            return redirect(url_for('pension.dashboard'))

    return render_template('pension/application_review.html', application=app_obj, employee=emp, ai_ver=ai_ver)

@pension_bp.route('/clearances')
@login_required
@role_required('pension_officer', 'admin')
def clearances():
    clearance_list = Clearance.query.order_by(Clearance.decision_date.desc()).all()
    return render_template('pension/clearances.html', clearances=clearance_list)
