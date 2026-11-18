import pytest
from datetime import date
from app.extensions import db
from app.models.employee import Employee
from app.models.application import RetirementApplication, ApplicationStatus
from app.models.clearance import Clearance, RetirementCertificate
from app.models.user import User

def test_full_clearance_workflow_and_certificate(client, app):
    with app.app_context():
        # Setup an employee and application
        emp = Employee.query.filter_by(staff_number='FGN/WORKFLOW/TEST').first()
        if not emp:
            emp = Employee(
                staff_number='FGN/WORKFLOW/TEST',
                first_name='Abubakar',
                last_name='Shehu',
                gender='Male',
                date_of_birth=date(1966, 2, 10),
                appointment_date=date(1991, 3, 1),
                statutory_retirement_date=date(2026, 2, 10),
                state_of_origin='Sokoto',
                residential_address='Sokoto City',
                city='Sokoto',
                state_of_residence='Sokoto',
                phone_number='+2348055551122',
                email='abubakar.shehu@test.gov.ng',
                ministry_or_agency='Federal Ministry of Agriculture and Food Security',
                department='Agricultural Services',
                current_cadre='Chief Agric Officer',
                current_grade_level='GL 14'
            )
            db.session.add(emp)
            db.session.commit()

        app_obj = RetirementApplication.query.filter_by(application_reference='RET-WORKFLOW-01').first()
        if not app_obj:
            app_obj = RetirementApplication(
                application_reference='RET-WORKFLOW-01',
                employee_id=emp.id,
                reason_for_retirement='Statutory Age (60 Years)',
                proposed_retirement_date=date(2026, 2, 10),
                current_status=ApplicationStatus.PENDING_HR
            )
            db.session.add(app_obj)
            db.session.commit()
            
        app_id = app_obj.id

    # 1. HR Officer logs in and verifies records
    client.get('/auth/logout')
    client.post('/auth/login', data={'username_or_email': 'test_hr', 'password': 'HrTest@123'}, follow_redirects=True)
    resp_hr = client.post(f'/hr/verify-records/{app_id}', data={
        'action': 'confirm',
        'notes': 'All service records certified authentic from Ministry archives.'
    }, follow_redirects=True)
    assert resp_hr.status_code == 200

    with app.app_context():
        updated_app = RetirementApplication.query.get(app_id)
        assert updated_app.current_status == ApplicationStatus.PENDING_PENSION
        assert updated_app.hr_verified_at is not None

    # 2. Pension Officer logs in and approves clearance
    client.get('/auth/logout')
    client.post('/auth/login', data={'username_or_email': 'test_pension', 'password': 'PensionTest@123'}, follow_redirects=True)
    resp_pension = client.post(f'/pension/review/{app_id}', data={
        'decision': 'approve',
        'remarks': 'Full pension clearance approved. Entitled to standard gratuity and monthly pension.'
    }, follow_redirects=True)
    assert resp_pension.status_code == 200

    # 3. Verify Certificate was generated
    with app.app_context():
        approved_app = RetirementApplication.query.get(app_id)
        assert approved_app.current_status == ApplicationStatus.CERTIFICATE_GENERATED
        assert approved_app.clearance is not None
        assert approved_app.clearance.certificate is not None
        
        cert = approved_app.clearance.certificate
        assert cert.certificate_number.startswith('FGN-RET-CERT-')
        token = cert.verification_token

    # 4. Test Public Certificate Verification Page (Accessible without login, hides private data)
    client.get('/auth/logout')
    public_resp = client.get(f'/certificates/verify/{token}')
    assert public_resp.status_code == 200
    assert b"Document Authenticity Confirmed" in public_resp.data
    assert b"Abubakar Shehu" in public_resp.data
    assert b"FGN/WORKFLOW/TEST" in public_resp.data
    # Private phone number and address must NOT be present on public page
    assert b"+2348055551122" not in public_resp.data
    assert b"Sokoto City" not in public_resp.data
