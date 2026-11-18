from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User, Role
from app.models.employee import Employee
from app.models.application import RetirementApplication, ApplicationStatus
from app.models.clearance import Clearance, InvestigationRecord
from app.models.audit import AuditLog
from app.models.settings import SystemSetting
from app.models.verification import AIVerification
from app.auth.decorators import role_required
from app.services.audit_service import AuditService
from app.services.report_service import ReportService

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    total_employees = Employee.query.count()
    total_apps = RetirementApplication.query.count()
    pending_apps = RetirementApplication.query.filter(
        RetirementApplication.current_status.in_([
            ApplicationStatus.PENDING_HR,
            ApplicationStatus.PENDING_PENSION,
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.AI_VERIFICATION
        ])
    ).count()
    approved_apps = RetirementApplication.query.filter_by(current_status=ApplicationStatus.APPROVED).count()
    rejected_apps = RetirementApplication.query.filter_by(current_status=ApplicationStatus.REJECTED).count()
    flagged_apps = RetirementApplication.query.filter_by(is_flagged=True).count()
    
    recent_applications = RetirementApplication.query.order_by(RetirementApplication.created_at.desc()).limit(6).all()
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
    
    # Status distribution for Chart.js
    statuses = [
        ApplicationStatus.APPROVED,
        ApplicationStatus.PENDING_PENSION,
        ApplicationStatus.PENDING_HR,
        ApplicationStatus.FLAGGED,
        ApplicationStatus.REJECTED
    ]
    status_counts = [RetirementApplication.query.filter_by(current_status=s).count() for s in statuses]
    
    return render_template(
        'admin/dashboard.html',
        total_employees=total_employees,
        total_apps=total_apps,
        pending_apps=pending_apps,
        approved_apps=approved_apps,
        rejected_apps=rejected_apps,
        flagged_apps=flagged_apps,
        recent_applications=recent_applications,
        recent_logs=recent_logs,
        chart_labels=statuses,
        chart_data=status_counts
    )

@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    user_list = User.query.order_by(User.created_at.desc()).all()
    roles = Role.query.all()
    return render_template('admin/users.html', users=user_list, roles=roles)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_user():
    roles = Role.query.all()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role_id = request.form.get('role_id')
        phone = request.form.get('phone', '').strip()
        
        # Validation
        if not username or not email or not password or not role_id:
            flash("Please fill in all mandatory fields.", "danger")
            return render_template('admin/user_form.html', roles=roles, title="Create System User")
            
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Error: Username or email is already registered in the system.", "danger")
            return render_template('admin/user_form.html', roles=roles, title="Create System User")
            
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role_id=int(role_id),
            phone=phone,
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        AuditService.log('ADMIN_CREATE_USER', 'User', new_user.id, {'username': new_user.username, 'role_id': role_id})
        flash(f"System user account '{username}' successfully created.", "success")
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', roles=roles, title="Create System User")

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user_status(user_id):
    if user_id == current_user.id:
        flash("You cannot deactivate your own administrative account.", "warning")
        return redirect(url_for('admin.users'))
        
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    action = "Activated" if user.is_active else "Deactivated"
    AuditService.log(f'USER_{action.upper()}', 'User', user.id, {'is_active': user.is_active})
    flash(f"User '{user.username}' has been {action}.", "info")
    return redirect(url_for('admin.users'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def settings():
    if request.method == 'POST':
        # Configurable Eligibility Rules
        ret_age = request.form.get('statutory_retirement_age', '60')
        ret_service = request.form.get('statutory_years_of_service', '35')
        logic_op = request.form.get('eligibility_logic_operator', 'OR')
        vol_service = request.form.get('min_voluntary_service_years', '10')
        session_timeout = request.form.get('session_timeout_minutes', '60')
        
        SystemSetting.set_value('statutory_retirement_age', ret_age, 'Mandatory civil service retirement age threshold', 'integer')
        SystemSetting.set_value('statutory_years_of_service', ret_service, 'Mandatory civil service maximum years of service', 'integer')
        SystemSetting.set_value('eligibility_logic_operator', logic_op, 'Boolean combination operator for age and service rules (OR/AND)', 'string')
        SystemSetting.set_value('min_voluntary_service_years', vol_service, 'Minimum service years for voluntary pensionable retirement', 'integer')
        SystemSetting.set_value('session_timeout_minutes', session_timeout, 'Session inactivity timeout in minutes', 'integer')
        
        AuditService.log('UPDATE_SYSTEM_SETTINGS', 'SystemSetting', None, {
            'retirement_age': ret_age,
            'service_years': ret_service,
            'logic_operator': logic_op
        })
        flash("Civil service retirement eligibility rules and system configuration successfully updated.", "success")
        return redirect(url_for('admin.settings'))

    curr_age = SystemSetting.get_value('statutory_retirement_age', 60)
    curr_service = SystemSetting.get_value('statutory_years_of_service', 35)
    curr_op = SystemSetting.get_value('eligibility_logic_operator', 'OR')
    curr_vol = SystemSetting.get_value('min_voluntary_service_years', 10)
    curr_timeout = SystemSetting.get_value('session_timeout_minutes', 60)

    return render_template(
        'admin/settings.html',
        statutory_retirement_age=curr_age,
        statutory_years_of_service=curr_service,
        eligibility_logic_operator=curr_op,
        min_voluntary_service_years=curr_vol,
        session_timeout_minutes=curr_timeout
    )

@admin_bp.route('/audit-logs')
@login_required
@role_required('admin')
def audit_logs():
    query = AuditLog.query
    user_id = request.args.get('user_id')
    action = request.args.get('action')
    
    if user_id:
        query = query.filter_by(user_id=int(user_id))
    if action:
        query = query.filter_by(action=action)
        
    logs = query.order_by(AuditLog.created_at.desc()).limit(150).all()
    all_users = User.query.all()
    return render_template('admin/audit_logs.html', logs=logs, users=all_users, current_user_id=user_id, current_action=action)
