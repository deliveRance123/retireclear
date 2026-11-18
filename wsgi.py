import os
from app import create_app
from app.extensions import db

app = create_app(os.environ.get('FLASK_CONFIG', 'production'))

# Auto-create tables and baseline roles on first startup
with app.app_context():
    try:
        db.create_all()
        from app.models.user import Role
        if Role.query.count() == 0:
            roles_data = [
                ('admin', 'System Administrator', 'Full portal governance and configuration privileges'),
                ('hr_officer', 'Human Resource Officer', 'Employee records management and service verification'),
                ('pension_officer', 'Pension Officer', 'Pension eligibility clearance and certificate generation'),
                ('auditor', 'Independent Auditor', 'Audit investigation, fraud detection, and integrity oversight'),
                ('civil_servant', 'Retiring Civil Servant', 'Self-service application filing and document tracking')
            ]
            for code, disp, desc in roles_data:
                if not Role.query.filter_by(name=code).first():
                    db.session.add(Role(name=code, display_name=disp, description=desc))
            db.session.commit()
            print("[Auto-Seed] Initialized essential roles successfully.")
    except Exception as e:
        print(f"[Startup Database Notice] {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
