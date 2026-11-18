from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.application import RetirementApplication, ApplicationStatus, ApplicationStage, ApplicationStatusHistory
from app.models.clearance import InvestigationRecord
from app.models.verification import AIVerification
from app.models.audit import AuditLog
from app.auth.decorators import role_required
from app.services.audit_service import AuditService

auditor_bp = Blueprint('auditor', __name__)

@auditor_bp.route('/dashboard')
@login_required
@role_required('auditor', 'admin')
def dashboard():
    flagged_count = RetirementApplication.query.filter(
        (RetirementApplication.is_flagged == True) | 
        (RetirementApplication.current_status == ApplicationStatus.FLAGGED)
    ).count()
    
    open_investigations = InvestigationRecord.query.filter_by(status='Open').count()
    resolved_investigations = InvestigationRecord.query.filter_by(status='Resolved').count()
    total_logs = AuditLog.query.count()
    
    flagged_apps = RetirementApplication.query.filter(
        (RetirementApplication.is_flagged == True) | 
        (RetirementApplication.current_status == ApplicationStatus.FLAGGED)
    ).order_by(RetirementApplication.updated_at.desc()).limit(6).all()
    
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    
    return render_template(
        'auditor/dashboard.html',
        flagged_count=flagged_count,
        open_investigations=open_investigations,
        resolved_investigations=resolved_investigations,
        total_logs=total_logs,
        flagged_apps=flagged_apps,
        recent_logs=recent_logs
    )

@auditor_bp.route('/flagged')
@login_required
@role_required('auditor', 'admin')
def flagged():
    flagged_apps = RetirementApplication.query.filter(
        (RetirementApplication.is_flagged == True) | 
        (RetirementApplication.current_status == ApplicationStatus.FLAGGED)
    ).order_by(RetirementApplication.updated_at.desc()).all()
    
    return render_template('auditor/flagged.html', applications=flagged_apps)

@auditor_bp.route('/investigate/<int:application_id>', methods=['GET', 'POST'])
@login_required
@role_required('auditor', 'admin')
def investigate(application_id):
    app_obj = RetirementApplication.query.get_or_404(application_id)
    emp = app_obj.employee
    ai_ver = app_obj.latest_ai_verification
    
    if request.method == 'POST':
        inv_type = request.form.get('investigation_type', 'irregularity_review')
        findings = request.form.get('findings', '').strip()
        rec_action = request.form.get('recommended_action', 'Cleared after Verification')
        status = request.form.get('status', 'Resolved')
        clear_flag = request.form.get('clear_flag') == 'yes'
        
        inv = InvestigationRecord(
            application_id=app_obj.id,
            auditor_id=current_user.id,
            investigation_type=inv_type,
            findings=findings,
            recommended_action=rec_action,
            status=status,
            resolution_date=datetime.utcnow() if status == 'Resolved' else None
        )
        db.session.add(inv)
        
        if clear_flag:
            app_obj.is_flagged = False
            app_obj.current_status = ApplicationStatus.PENDING_PENSION
            app_obj.current_stage = ApplicationStage.PENSION
            
            history = ApplicationStatusHistory(
                application_id=app_obj.id,
                changed_by_user_id=current_user.id,
                previous_status=ApplicationStatus.FLAGGED,
                new_status=ApplicationStatus.PENDING_PENSION,
                comments=f"Investigation completed by Auditor {current_user.full_name}. Findings: {findings}. Flag cleared and routed to Pension Board."
            )
            db.session.add(history)
            
        db.session.commit()
        AuditService.log('AUDIT_INVESTIGATION_RECORDED', 'InvestigationRecord', inv.id, {
            'application_ref': app_obj.application_reference,
            'recommendation': rec_action
        })
        flash(f"Investigation report recorded for application {app_obj.application_reference}.", "success")
        return redirect(url_for('auditor.dashboard'))

    existing_investigations = InvestigationRecord.query.filter_by(application_id=app_obj.id).all()
    return render_template('auditor/investigate.html', application=app_obj, employee=emp, ai_ver=ai_ver, investigations=existing_investigations)

@auditor_bp.route('/logs')
@login_required
@role_required('auditor', 'admin')
def logs():
    query = AuditLog.query
    action = request.args.get('action')
    if action:
        query = query.filter_by(action=action)
    logs_list = query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return render_template('auditor/logs.html', logs=logs_list, current_action=action)
