import os
from flask import Flask, redirect, url_for, render_template, jsonify
from flask_login import current_user
from app.extensions import db, login_manager, migrate, csrf
from config import config

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize Flask Extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Ensure Storage Directories
    with app.app_context():
        upload_base = app.config.get('UPLOAD_FOLDER', os.path.join(app.root_path, '..', 'uploads'))
        os.makedirs(os.path.join(upload_base, 'documents'), exist_ok=True)
        os.makedirs(os.path.join(upload_base, 'passports'), exist_ok=True)
        os.makedirs(os.path.join(upload_base, 'certificates'), exist_ok=True)

    # Register Blueprints
    from app.auth import auth_bp
    from app.admin import admin_bp
    from app.hr import hr_bp
    from app.pension import pension_bp
    from app.auditor import auditor_bp
    from app.employee import employee_bp
    from app.verification import verification_bp
    from app.certificates import certificates_bp
    from app.reports import reports_bp
    from app.notifications import notifications_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(hr_bp, url_prefix='/hr')
    app.register_blueprint(pension_bp, url_prefix='/pension')
    app.register_blueprint(auditor_bp, url_prefix='/auditor')
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app.register_blueprint(verification_bp, url_prefix='/verification')
    app.register_blueprint(certificates_bp, url_prefix='/certificates')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    # Root route - Public Landing Page
    @app.route('/')
    def index():
        from app.auth.decorators import get_role_dashboard_url
        dashboard_url = None
        if current_user.is_authenticated and current_user.role:
            dashboard_url = get_role_dashboard_url(current_user.role.name)
        return render_template('index.html', dashboard_url=dashboard_url)

    # Dedicated About Page
    @app.route('/about')
    def about():
        from app.auth.decorators import get_role_dashboard_url
        dashboard_url = None
        if current_user.is_authenticated and current_user.role:
            dashboard_url = get_role_dashboard_url(current_user.role.name)
        return render_template('about.html', dashboard_url=dashboard_url)

    # Dedicated Retirement Due Date & Pension Milestone Calculator Page
    @app.route('/calculator')
    def calculator_page():
        from app.auth.decorators import get_role_dashboard_url
        dashboard_url = None
        if current_user.is_authenticated and current_user.role:
            dashboard_url = get_role_dashboard_url(current_user.role.name)
        return render_template('calculator.html', dashboard_url=dashboard_url)

    # Dedicated Public Certificate Verification Portal Page
    @app.route('/verify')
    def verify_page():
        from app.auth.decorators import get_role_dashboard_url
        dashboard_url = None
        if current_user.is_authenticated and current_user.role:
            dashboard_url = get_role_dashboard_url(current_user.role.name)
        return render_template('verify.html', dashboard_url=dashboard_url)

    # Health check endpoint for Railway & production deployment
    @app.route('/health')
    def health_check():
        db_status = "connected"
        try:
            db.session.execute(db.text('SELECT 1'))
        except Exception as e:
            db_status = f"error: {str(e)}"
        return jsonify({
            'status': 'ok' if db_status == "connected" else "degraded",
            'application': app.config.get('APP_NAME'),
            'database': db_status,
            'country': app.config.get('COUNTRY')
        })

    # Context processors for navigation badges & alerts
    @app.context_processor
    def inject_global_data():
        unread_count = 0
        header_notifications = []
        if current_user.is_authenticated:
            from app.models.notification import Notification
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            header_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
        return {
            'app_name': app.config.get('APP_NAME'),
            'app_subtitle': app.config.get('APP_SUBTITLE'),
            'currency': app.config.get('CURRENCY'),
            'unread_notifications_count': unread_count,
            'header_notifications': header_notifications
        }

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
