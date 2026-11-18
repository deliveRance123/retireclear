import os
import pytest
from app import create_app
from app.extensions import db
from app.models.user import Role, User
from app.models.employee import Employee
from app.models.settings import SystemSetting

@pytest.fixture(scope='session')
def app():
    # Use testing configuration with in-memory database
    test_app = create_app('testing')
    with test_app.app_context():
        db.create_all()
        _seed_test_roles_and_users()
        yield test_app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    with app.app_context():
        yield db.session
        db.session.rollback()

def _seed_test_roles_and_users():
    roles_data = [
        ('admin', 'System Administrator'),
        ('hr_officer', 'HR Officer'),
        ('pension_officer', 'Pension Officer'),
        ('auditor', 'Auditor'),
        ('civil_servant', 'Retiring Civil Servant')
    ]
    roles = {}
    for code, disp in roles_data:
        r = Role.query.filter_by(name=code).first()
        if not r:
            r = Role(name=code, display_name=disp)
            db.session.add(r)
        roles[code] = r
    db.session.commit()

    users_data = [
        ('test_admin', 'admin@test.gov.ng', 'AdminTest@123', 'admin'),
        ('test_hr', 'hr@test.gov.ng', 'HrTest@123', 'hr_officer'),
        ('test_pension', 'pension@test.gov.ng', 'PensionTest@123', 'pension_officer'),
        ('test_auditor', 'auditor@test.gov.ng', 'AuditorTest@123', 'auditor'),
        ('test_civil_servant', 'retiree@test.gov.ng', 'RetireeTest@123', 'civil_servant')
    ]
    for uname, email, pwd, rcode in users_data:
        u = User.query.filter_by(username=uname).first()
        if not u:
            u = User(
                username=uname,
                email=email,
                first_name='Test',
                last_name=uname.replace('_', ' ').title(),
                role_id=roles[rcode].id,
                is_active=True
            )
            u.set_password(pwd)
            db.session.add(u)
    db.session.commit()

    # Seed Default Eligibility settings
    SystemSetting.set_value('statutory_retirement_age', 60, 'Age', 'integer')
    SystemSetting.set_value('statutory_years_of_service', 35, 'Service', 'integer')
    SystemSetting.set_value('eligibility_logic_operator', 'OR', 'Logic', 'string')
