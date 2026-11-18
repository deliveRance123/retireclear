import os
from app import create_app
from app.extensions import db

app = create_app(os.environ.get('FLASK_CONFIG', 'production'))

with app.app_context():
    try:
        db.create_all()
        from app.models.user import Role
        if Role.query.count() == 0:
            from seed_db import seed_database
            seed_database()
            print("[Auto-Seed] Initialized database with roles and baseline configuration.")
    except Exception as e:
        print(f"[Startup Database Check Notice] {e}")

if __name__ == "__main__":
    app.run()
