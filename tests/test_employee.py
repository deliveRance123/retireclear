import pytest
from datetime import date
from app.models.employee import Employee

def test_register_employee_valid(client, app):
    # Log in as HR officer
    client.post('/auth/login', data={
        'username_or_email': 'test_hr',
        'password': 'HrTest@123'
    }, follow_redirects=True)

    data = {
        'staff_number': 'FGN/TEST/2026/00999',
        'first_name': 'Oluwaseun',
        'middle_name': 'Babatunde',
        'last_name': 'Adeleke',
        'gender': 'Male',
        'date_of_birth': '1966-06-12',
        'state_of_origin': 'Ogun',
        'lga': 'Abeokuta South',
        'residential_address': 'Plot 5, Ibara Estate, Abeokuta',
        'city': 'Abeokuta',
        'state_of_residence': 'Ogun',
        'phone_number': '+2348034567890',
        'email': 'oluwaseun.adeleke@education.gov.ng',
        'nin': '12345678901',
        'ministry_or_agency': 'Federal Ministry of Education',
        'department': 'Basic Education Department',
        'current_cadre': 'Principal Education Officer',
        'current_grade_level': 'GL 12',
        'current_step': 5,
        'appointment_date': '1991-07-01',
        'statutory_retirement_date': '2026-06-12'
    }

    response = client.post('/hr/employees/register', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"successfully registered" in response.data

    with app.app_context():
        emp = Employee.query.filter_by(staff_number='FGN/TEST/2026/00999').first()
        assert emp is not None
        assert emp.full_name == 'Oluwaseun Babatunde Adeleke'
        assert emp.age == 60
        assert emp.years_of_service >= 34.0

def test_duplicate_staff_number_rejected(client):
    client.post('/auth/login', data={
        'username_or_email': 'test_hr',
        'password': 'HrTest@123'
    }, follow_redirects=True)

    data = {
        'staff_number': 'FGN/TEST/2026/00999',  # Already created above
        'first_name': 'Duplicated',
        'last_name': 'Officer',
        'gender': 'Female',
        'date_of_birth': '1970-01-01',
        'state_of_origin': 'Lagos',
        'residential_address': 'Victoria Island, Lagos',
        'city': 'Lagos',
        'state_of_residence': 'Lagos',
        'phone_number': '+2348099887766',
        'email': 'different.email@gov.ng',
        'ministry_or_agency': 'Federal Ministry of Works',
        'department': 'Civil Works',
        'current_cadre': 'Engineer',
        'current_grade_level': 'GL 10',
        'current_step': 1,
        'appointment_date': '2000-01-01',
        'statutory_retirement_date': '2030-01-01'
    }

    response = client.post('/hr/employees/register', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"already registered in the system" in response.data

def test_invalid_phone_number_rejected(client):
    client.post('/auth/login', data={
        'username_or_email': 'test_hr',
        'password': 'HrTest@123'
    }, follow_redirects=True)

    data = {
        'staff_number': 'FGN/INVALID/2026/00001',
        'first_name': 'Test',
        'last_name': 'InvalidPhone',
        'gender': 'Male',
        'date_of_birth': '1975-01-01',
        'state_of_origin': 'Kano',
        'residential_address': 'Kano City',
        'city': 'Kano',
        'state_of_residence': 'Kano',
        'phone_number': '12345-not-nigerian',  # Invalid phone format
        'email': 'invalid.phone@gov.ng',
        'ministry_or_agency': 'Federal Ministry of Finance',
        'department': 'Accounts',
        'current_cadre': 'Accountant',
        'current_grade_level': 'GL 08',
        'current_step': 1,
        'appointment_date': '2005-01-01',
        'statutory_retirement_date': '2035-01-01'
    }

    response = client.post('/hr/employees/register', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"valid Nigerian mobile phone number" in response.data
