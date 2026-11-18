from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def role_required(*allowed_roles):
    """
    Ensure the current user possesses one of the designated system roles.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not current_user.role or current_user.role.name not in allowed_roles:
                flash("Access Denied: You do not have the required administrative clearance to access this module.", "danger")
                # Redirect to appropriate home dashboard
                return redirect(get_role_dashboard_url(current_user.role.name if current_user.role else None))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_role_dashboard_url(role_name):
    """Return the designated landing dashboard for a given user role."""
    mapping = {
        'admin': 'admin.dashboard',
        'hr_officer': 'hr.dashboard',
        'pension_officer': 'pension.dashboard',
        'auditor': 'auditor.dashboard',
        'civil_servant': 'employee.dashboard'
    }
    endpoint = mapping.get(role_name, 'auth.login')
    return url_for(endpoint)
