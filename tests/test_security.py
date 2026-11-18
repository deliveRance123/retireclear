import pytest
import io
from app.services.document_service import DocumentService

def test_unauthenticated_access_redirects_to_login(client):
    client.get('/auth/logout')
    response = client.get('/admin/dashboard')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']

def test_role_enforcement_prevents_unauthorized_access(client):
    # Log in as civil servant
    client.post('/auth/login', data={'username_or_email': 'test_civil_servant', 'password': 'RetireeTest@123'}, follow_redirects=True)
    
    # Try accessing admin settings
    response = client.get('/admin/settings', follow_redirects=True)
    assert b"Access Denied" in response.data

    # Try accessing auditor dashboard
    response = client.get('/auditor/dashboard', follow_redirects=True)
    assert b"Access Denied" in response.data

def test_file_upload_extension_security(app):
    with app.app_context():
        # Disallowed file type (e.g. .exe or .sh)
        fake_exe = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00")
        fake_exe.filename = 'malicious.exe'
        doc, err = DocumentService.save_document(fake_exe, 1, 'appointment_letter')
        assert doc is None
        assert "not permitted" in err

        # Deceptive extension: file named .pdf but containing executable content
        fake_deceptive = io.BytesIO(b"MZ\x90\x00not-a-pdf-header")
        fake_deceptive.filename = 'deceptive.pdf'
        doc, err = DocumentService.save_document(fake_deceptive, 1, 'appointment_letter')
        assert doc is None
        assert "signature does not match" in err
