import pytest
from app.models.user import User

def test_valid_login(client):
    client.get('/auth/logout')
    response = client.post('/auth/login', data={
        'username_or_email': 'test_admin',
        'password': 'AdminTest@123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back, Test" in response.data
    assert b"Executive Administration Dashboard" in response.data

def test_invalid_login(client):
    client.get('/auth/logout')
    response = client.post('/auth/login', data={
        'username_or_email': 'test_admin',
        'password': 'WrongPassword999'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid login credentials" in response.data or b"Attempt" in response.data

def test_empty_credentials(client):
    client.get('/auth/logout')
    response = client.post('/auth/login', data={
        'username_or_email': '',
        'password': ''
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Please enter your username" in response.data

def test_role_based_redirection(client):
    # Test HR Officer Login redirects to HR Dashboard
    client.get('/auth/logout')
    response = client.post('/auth/login', data={
        'username_or_email': 'test_hr',
        'password': 'HrTest@123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Human Resources Directorate" in response.data

    # Test Pension Officer Login redirects to Pension Dashboard
    client.get('/auth/logout')
    response = client.post('/auth/login', data={
        'username_or_email': 'test_pension',
        'password': 'PensionTest@123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Pension Clearance" in response.data

def test_logout(client):
    client.post('/auth/login', data={
        'username_or_email': 'test_admin',
        'password': 'AdminTest@123'
    }, follow_redirects=True)
    
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"signed out" in response.data
    assert b"Sign In" in response.data or b"RetireClear" in response.data
