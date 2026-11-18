import os
import uuid
from datetime import datetime, timedelta, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.user import User, Role
from app.models.employee import Employee
from app.auth.forms import LoginForm, PasswordResetRequestForm, ResetPasswordForm, RegistrationForm, ProfileEditForm
from app.auth.decorators import get_role_dashboard_url
from app.services.audit_service import AuditService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(get_role_dashboard_url(current_user.role.name if current_user.role else 'civil_servant'))
    
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.username_or_email.data.strip()
        password = form.password.data
        
        # Check user by username, email, or linked employee staff number
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
        
        if not user:
            # Check if identifier is an employee staff number
            emp = Employee.query.filter_by(staff_number=identifier).first()
            if emp and emp.user:
                user = emp.user

        # Throttling & Account Locking Check
        if user and user.locked_until and user.locked_until > datetime.utcnow():
            remaining_mins = int((user.locked_until - datetime.utcnow()).total_seconds() // 60) + 1
            flash(f"Security Notice: Account is temporarily locked due to repeated failed logins. Please retry in {remaining_mins} minutes.", "danger")
            AuditService.log('LOGIN_BLOCKED_LOCKED', 'User', user.id, {'reason': 'Account currently locked'}, user_id=user.id)
            return render_template('auth/login.html', form=form)

        if user and user.is_active and user.check_password(password):
            # Success
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=form.remember_me.data)
            AuditService.log('LOGIN_SUCCESS', 'User', user.id, {'role': user.role.name if user.role else None})
            
            flash(f"Welcome back, {user.first_name}! Logged in as {user.role.display_name if user.role else 'User'}.", "success")
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(get_role_dashboard_url(user.role.name if user.role else 'civil_servant'))
        else:
            # Failed Attempt
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                    flash("Security Notice: 5 consecutive failed attempts detected. Account locked for 15 minutes.", "danger")
                else:
                    flash(f"Invalid credentials. Attempt {user.failed_login_attempts} of 5 before temporary lockout.", "danger")
                db.session.commit()
                AuditService.log('LOGIN_FAILED', 'User', user.id, {'attempt_count': user.failed_login_attempts})
            else:
                flash("Invalid login credentials provided. Please verify and try again.", "danger")
                AuditService.log('LOGIN_FAILED_UNKNOWN_USER', 'User', None, {'identifier': identifier})

    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    username = current_user.username
    logout_user()
    AuditService.log('LOGOUT', 'User', user_id, {'username': username}, user_id=user_id)
    flash("You have been securely signed out of the National Retirement Clearance Portal.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip()).first()
        if user:
            AuditService.log('PASSWORD_RESET_REQUESTED', 'User', user.id, {'email': user.email})
        flash("If an official civil service account is registered with this email, secure password reset instructions have been dispatched.", "info")
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(get_role_dashboard_url(current_user.role.name if current_user.role else 'civil_servant'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        staff_num = form.staff_number.data.strip().upper()
        email = form.email.data.strip().lower()
        
        # Check if username or email exists
        if User.query.filter((User.username == staff_num) | (User.email == email)).first():
            flash("An account with this Staff Number or Email already exists. Please sign in.", "warning")
            return redirect(url_for('auth.login'))
        
        # Check if staff number already linked to an existing employee
        emp = Employee.query.filter_by(staff_number=staff_num).first()
        
        # Find civil_servant role
        role = Role.query.filter_by(name='civil_servant').first()
        
        new_user = User(
            username=staff_num,
            email=email,
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            role_id=role.id if role else 5,
            is_active=True
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.flush()
        
        if emp:
            emp.user_id = new_user.id
            if not emp.email:
                emp.email = email
            if not emp.phone_number:
                emp.phone_number = form.phone_number.data.strip()
        else:
            dob = date(1966, 1, 1)
            doa = date(1991, 1, 1)
            ret_dob = date(dob.year + 60, dob.month, dob.day)
            ret_doa = date(doa.year + 35, doa.month, doa.day)
            statutory_ret = min(ret_dob, ret_doa)

            emp = Employee(
                user_id=new_user.id,
                staff_number=staff_num,
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip(),
                gender='Unspecified',
                date_of_birth=dob,
                state_of_origin='Federal Capital Territory',
                residential_address='Federal Civil Service Residential Quarter',
                city='Abuja',
                state_of_residence='FCT Abuja',
                phone_number=form.phone_number.data.strip(),
                email=email,
                ministry_or_agency=form.ministry_or_agency.data.strip(),
                department='Administration',
                current_cadre='Administrative Cadre',
                current_grade_level='GL 12',
                current_step=1,
                appointment_date=doa,
                statutory_retirement_date=statutory_ret
            )
            db.session.add(emp)
            
        db.session.commit()
        AuditService.log('USER_SELF_REGISTERED', 'User', new_user.id, {'staff_number': staff_num, 'email': email})
        
        flash("Registration completed successfully! You can now sign in with your Staff ID and password.", "success")
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', form=form)


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileEditForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data.strip()
        current_user.last_name = form.last_name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        
        # Sync with employee record if user has one
        if current_user.employee_profile:
            current_user.employee_profile.first_name = current_user.first_name
            current_user.employee_profile.last_name = current_user.last_name
            if current_user.phone:
                current_user.employee_profile.phone_number = current_user.phone

        # Handle avatar file upload
        if form.avatar.data and hasattr(form.avatar.data, 'filename') and form.avatar.data.filename:
            f = form.avatar.data
            orig_filename = secure_filename(f.filename)
            ext = orig_filename.rsplit('.', 1)[1].lower() if '.' in orig_filename else 'jpg'
            new_filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
            
            upload_dir = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, '..', 'uploads'))
            target_dir = os.path.join(upload_dir, 'passports')
            os.makedirs(target_dir, exist_ok=True)
            
            save_path = os.path.join(target_dir, new_filename)
            f.save(save_path)
            
            current_user.avatar_path = f"passports/{new_filename}"
            if current_user.employee_profile:
                current_user.employee_profile.passport_photo_path = f"passports/{new_filename}"
                
        db.session.commit()
        AuditService.log('PROFILE_UPDATED', 'User', current_user.id, {'full_name': current_user.full_name})
        flash("Your profile and avatar have been updated successfully.", "success")
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form)


@auth_bp.route('/avatar/<path:filename>')
def serve_avatar(filename):
    """Securely serve user avatar or employee passport photo with fallback."""
    upload_dir = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, '..', 'uploads'))
    
    # Try normalized paths
    candidates = [
        os.path.join(upload_dir, filename),
        os.path.join(upload_dir, 'passports', os.path.basename(filename)),
        os.path.join(upload_dir, os.path.basename(filename))
    ]
    
    for candidate in candidates:
        if os.path.isfile(candidate):
            return send_from_directory(os.path.dirname(candidate), os.path.basename(candidate))
            
    # Default fallback SVG avatar
    return send_from_directory(os.path.join(current_app.static_folder, 'images'), 'default-avatar.svg')

