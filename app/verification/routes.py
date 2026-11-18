from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.application import RetirementApplication
from app.models.verification import AIVerification
from app.auth.decorators import role_required
from app.services.audit_service import AuditService
from app.services.ai_verification_service import AIVerificationService

verification_bp = Blueprint('verification', __name__)

@verification_bp.route('/')
@login_required
@role_required('admin', 'hr_officer', 'pension_officer', 'auditor')
def index():
    """
    Central AI Verification & Decision Support Screening Dashboard.
    Displays all retirement clearance applications with their AI statutory assessment,
    OCR document alignments, fraud risk level, and human review states.
    """
    query = RetirementApplication.query
    recommendation_filter = request.args.get('recommendation')
    risk_filter = request.args.get('risk')
    search = request.args.get('search', '').strip()

    if search:
        query = query.join(RetirementApplication.employee).filter(
            (RetirementApplication.application_reference.ilike(f'%{search}%')) |
            (RetirementApplication.employee.has(staff_number=search))
        )

    apps = query.order_by(RetirementApplication.updated_at.desc()).all()

    # Filter in Python if AI-specific attributes requested
    if recommendation_filter:
        apps = [a for a in apps if a.latest_ai_verification and a.latest_ai_verification.overall_eligibility_recommendation == recommendation_filter]
    if risk_filter:
        apps = [a for a in apps if a.latest_ai_verification and a.latest_ai_verification.fraud_risk_level == risk_filter]

    # Metrics
    total_screened = AIVerification.query.count()
    eligible_count = AIVerification.query.filter_by(overall_eligibility_recommendation='Eligible').count()
    flagged_risk_count = AIVerification.query.filter(AIVerification.fraud_risk_level.in_(['High', 'Critical'])).count()
    manual_review_needed = AIVerification.query.filter_by(requires_manual_review=True).count()

    return render_template(
        'verification/index.html',
        applications=apps,
        total_screened=total_screened,
        eligible_count=eligible_count,
        flagged_risk_count=flagged_risk_count,
        manual_review_needed=manual_review_needed,
        search=search,
        current_recommendation=recommendation_filter,
        current_risk=risk_filter
    )


@verification_bp.route('/run/<int:application_id>', methods=['POST'])
@login_required
@role_required('admin', 'hr_officer', 'pension_officer', 'auditor')
def run_verification(application_id):
    """
    On-demand execution of the full AI Verification Pipeline:
    OCR Entity Extraction, Rule-Based Statutory Assessment, and Anomaly Detection.
    """
    app_obj = RetirementApplication.query.get_or_404(application_id)
    emp = app_obj.employee

    ai_ver = AIVerificationService.run_pipeline(app_obj, emp)

    AuditService.log('RUN_AI_VERIFICATION', 'RetirementApplication', app_obj.id, {
        'recommendation': ai_ver.overall_eligibility_recommendation,
        'fraud_risk_level': ai_ver.fraud_risk_level,
        'triggered_by': current_user.username
    })

    flash(
        f"AI Screening successfully executed: Recommendation is '{ai_ver.overall_eligibility_recommendation}' with {ai_ver.fraud_risk_level} Fraud Risk.",
        "success"
    )
    
    next_url = request.form.get('next') or request.args.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(url_for('verification.detail', application_id=app_obj.id))


@verification_bp.route('/detail/<int:application_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'hr_officer', 'pension_officer', 'auditor')
def detail(application_id):
    app_obj = RetirementApplication.query.get_or_404(application_id)
    emp = app_obj.employee
    ai_ver = app_obj.latest_ai_verification
    
    # Auto-run if not yet analyzed
    if not ai_ver and app_obj.documents:
        ai_ver = AIVerificationService.run_pipeline(app_obj, emp)
    
    if request.method == 'POST':
        comments = request.form.get('officer_comments', '').strip()
        manual_override = request.form.get('manual_override') == 'yes'
        
        if ai_ver:
            ai_ver.reviewed_by_officer_id = current_user.id
            ai_ver.officer_comments = comments
            ai_ver.reviewed_at = datetime.utcnow()
            if manual_override:
                ai_ver.requires_manual_review = False
            db.session.commit()
            
            AuditService.log('OFFICER_REVIEW_AI_ASSESSMENT', 'AIVerification', ai_ver.id, {
                'application_ref': app_obj.application_reference,
                'manual_override': manual_override
            })
            flash("Officer review comments and assessment sign-off recorded successfully.", "success")
            return redirect(url_for('verification.detail', application_id=app_obj.id))

    return render_template('verification/detail.html', application=app_obj, employee=emp, ai_ver=ai_ver)
