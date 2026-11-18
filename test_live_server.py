import requests
import re

BASE_URL = "http://127.0.0.1:5000"

def run_live_verification():
    print("=================================================================")
    print("LIVE SERVER HTTP INTEGRATION VERIFICATION")
    print("=================================================================")

    # 1. Health check
    r = requests.get(f"{BASE_URL}/health")
    print(f"[*] GET /health -> Status: {r.status_code}")
    assert r.status_code == 200
    print(f"    Payload: {r.json()}")

    # 1b. Landing page check
    r_landing = requests.get(f"{BASE_URL}/")
    print(f"[*] GET / (Landing Page) -> Status: {r_landing.status_code}")
    assert r_landing.status_code == 200
    assert "RetireClear" in r_landing.text
    assert "Civil Service Portal" not in r_landing.text
    assert "Retirement Due Date Calculator" in r_landing.text
    assert "Public Certificate Verification" in r_landing.text
    assert "fixed-nav" in r_landing.text
    assert "hero-retiree-nigeria.jpg" in r_landing.text
    assert "verification-collaborative-nigeria.jpg" in r_landing.text
    print("    [+] Public landing page verified: 'Civil Service Portal' removed from header, Nigerian photos embedded!")

    # 1d. Nigerian Images verification
    r_img1 = requests.get(f"{BASE_URL}/static/images/hero-retiree-nigeria.jpg")
    print(f"[*] GET hero-retiree-nigeria.jpg -> Status: {r_img1.status_code}, Length: {len(r_img1.content)} bytes")
    assert r_img1.status_code == 200
    assert len(r_img1.content) > 1000

    r_img2 = requests.get(f"{BASE_URL}/static/images/verification-collaborative-nigeria.jpg")
    print(f"[*] GET verification-collaborative-nigeria.jpg -> Status: {r_img2.status_code}, Length: {len(r_img2.content)} bytes")
    assert r_img2.status_code == 200
    assert len(r_img2.content) > 1000
    print("    [+] Both Nigerian-related photos successfully delivered via static assets!")

    # 1e. Mobile Hamburger navbar & icon-less small navigation links
    assert 'navbar-toggler' in r_landing.text
    assert 'landingNavbar' in r_landing.text
    # Ensure no icons beside Verify Certificate and Due Date Calculator in landingNavbar
    assert '<i class="bi bi-search me-1"></i> Verify' not in r_landing.text
    assert '<i class="bi bi-calculator me-1"></i> Due' not in r_landing.text
    print("    [+] Header navigation links verified without icons and with clean compact sizing!")

    # 2. Login Page check (Standalone, top home link, autofill pills)
    s = requests.Session()
    r = s.get(f"{BASE_URL}/auth/login")
    print(f"[*] GET /auth/login -> Status: {r.status_code}")
    assert r.status_code == 200
    assert "RetireClear" in r.text
    assert "Sign In" in r.text
    assert "Sign Up" in r.text
    assert "Back to Home" in r.text
    assert "autoFill" in r.text
    assert "favicon.svg" in r.text
    print("    [+] Login page verified with standalone modern card, top home link & auto-fill pills!")

    # 2b. Registration Page check & Live Registration
    r_reg = s.get(f"{BASE_URL}/auth/register")
    print(f"[*] GET /auth/register -> Status: {r_reg.status_code}")
    assert r_reg.status_code == 200
    assert "Create Account" in r_reg.text
    assert "Back to Home" in r_reg.text
    assert "Staff ID" in r_reg.text
    
    # 2c. Forgot Password Page check (Standalone form only)
    r_fp = s.get(f"{BASE_URL}/auth/forgot-password")
    print(f"[*] GET /auth/forgot-password -> Status: {r_fp.status_code}")
    assert r_fp.status_code == 200
    assert "Reset Password" in r_fp.text
    assert "Back to Home" in r_fp.text
    assert "Send Reset Link" in r_fp.text
    print("    [+] Standalone forgot password page verified with pure form & top home link!")
    
    # Test registering a new civil servant
    reg_csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r_reg.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', r_reg.text)
    reg_csrf = reg_csrf_match.group(1) if reg_csrf_match else ""
    
    import random
    test_id = random.randint(1000, 9999)
    test_staff = f"FGN/TEST/2026/{test_id}"
    test_email = f"officer.{test_id}@service.gov.ng"
    
    r_reg_post = s.post(f"{BASE_URL}/auth/register", data={
        'csrf_token': reg_csrf,
        'staff_number': test_staff,
        'first_name': 'Chukwudi',
        'last_name': 'Eze',
        'email': test_email,
        'phone_number': '+2348039876543',
        'ministry_or_agency': 'Federal Ministry of Works',
        'password': 'TestPassword@2026',
        'confirm_password': 'TestPassword@2026'
    }, allow_redirects=True)
    print(f"[*] POST /auth/register -> Status: {r_reg_post.status_code}")
    assert "Registration completed successfully" in r_reg_post.text or "already exists" in r_reg_post.text
    print(f"    [+] Self-service registration tested successfully for {test_staff}!")

    # Extract CSRF token
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', r.text)
    csrf_token = match.group(1) if match else ""

    # 3. Authenticate as Admin
    r_login = s.post(f"{BASE_URL}/auth/login", data={
        'csrf_token': csrf_token,
        'username_or_email': 'admin',
        'password': 'AdminPass@2026'
    }, allow_redirects=True)
    print(f"[*] POST /auth/login (admin) -> Status: {r_login.status_code}, Final URL: {r_login.url}")
    assert r_login.status_code == 200
    assert "Executive Administration" in r_login.text
    assert "Registered Staff" in r_login.text
    print("    [+] Administrator successfully authenticated & executive governance dashboard rendered!")

    # 3b. Verify header notification dropdown and clean sidebar
    assert 'id="notifDropdown"' in r_login.text
    assert 'Public Landing Page' not in r_login.text
    assert 'Alerts & Notices' not in r_login.text
    print("    [+] Header notification dropdown verified; notification & public links cleanly removed from sidebar!")

    # 3c. Verify Profile editing & photo uploading page
    r_prof = s.get(f"{BASE_URL}/auth/profile")
    print(f"[*] GET /auth/profile -> Status: {r_prof.status_code}")
    assert r_prof.status_code == 200
    assert "My Profile" in r_prof.text
    assert "Profile Picture" in r_prof.text
    
    prof_csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r_prof.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', r_prof.text)
    prof_csrf = prof_csrf_match.group(1) if prof_csrf_match else ""
    r_prof_post = s.post(f"{BASE_URL}/auth/profile", data={
        'csrf_token': prof_csrf,
        'first_name': 'System',
        'last_name': 'Administrator',
        'phone': '+2348011112222'
    }, allow_redirects=True)
    assert r_prof_post.status_code == 200
    assert "Your profile and avatar have been updated successfully" in r_prof_post.text
    print("    [+] User profile editing verified successfully!")

    # 3d. Verify Avatar Serving Route
    r_avatar = s.get(f"{BASE_URL}/auth/avatar/default-avatar.svg")
    print(f"[*] GET /auth/avatar/default-avatar.svg -> Status: {r_avatar.status_code}")
    assert r_avatar.status_code == 200
    print("    [+] Avatar asset route verified successfully!")

    # 4. View Employees directory
    r_emp = s.get(f"{BASE_URL}/hr/employees")
    print(f"[*] GET /hr/employees -> Status: {r_emp.status_code}")
    assert r_emp.status_code == 200
    assert "Registered Civil Servants" in r_emp.text
    assert "FGN/EDU/2018/00125" in r_emp.text
    print("    [+] Staff directory rendered with seeded employees!")

    # 5. View Settings
    r_settings = s.get(f"{BASE_URL}/admin/settings")
    print(f"[*] GET /admin/settings -> Status: {r_settings.status_code}")
    assert r_settings.status_code == 200
    assert "Configurable Statutory Eligibility Rules" in r_settings.text
    print("    [+] Configurable rules settings page accessible!")

    # 6. Logout Admin
    r_logout = s.get(f"{BASE_URL}/auth/logout", allow_redirects=True)
    print(f"[*] GET /auth/logout -> Status: {r_logout.status_code}")
    assert "Sign In" in r_logout.text

    # 7. Authenticate as Retiring Civil Servant
    s_retiree = requests.Session()
    r_ret_page = s_retiree.get(f"{BASE_URL}/auth/login")
    ret_csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r_ret_page.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', r_ret_page.text)
    ret_csrf = ret_csrf_match.group(1) if ret_csrf_match else ""
    r_ret_login = s_retiree.post(f"{BASE_URL}/auth/login", data={
        'csrf_token': ret_csrf,
        'username_or_email': 'adebayo.olumide',
        'password': 'RetireePass@2026'
    }, allow_redirects=True)
    print(f"[*] POST /auth/login (adebayo.olumide) -> Status: {r_ret_login.status_code}, URL: {r_ret_login.url}")
    assert r_ret_login.status_code == 200
    assert "Welcome, Adebayo Sunday Olumide" in r_ret_login.text
    assert "RET-2026-00125" in r_ret_login.text
    assert "Certificate Ready" in r_ret_login.text
    print("    [+] Retiring Civil Servant authenticated & self-service dashboard loaded!")

    # 8. View Certificate
    r_cert = s_retiree.get(f"{BASE_URL}/certificates/view/1")
    print(f"[*] GET /certificates/view/1 -> Status: {r_cert.status_code}")
    assert r_cert.status_code == 200
    assert "NATIONAL RETIREMENT CLEARANCE CERTIFICATE" in r_cert.text
    assert "FGN-RET-CERT-2026-00001" in r_cert.text or "FGN-RET-CERT-" in r_cert.text
    print("    [+] Official Retirement Clearance Certificate preview rendered!")

    # 9. Verify Public Certificate Verification Endpoint (No login required)
    # Find token from certificate page
    token_match = re.search(r'/certificates/verify/([a-f0-9]+)', r_cert.text)
    if token_match:
        token = token_match.group(1)
        public_client = requests.Session()
        r_pub = public_client.get(f"{BASE_URL}/certificates/verify/{token}")
        print(f"[*] GET /certificates/verify/{token} -> Status: {r_pub.status_code}")
        assert r_pub.status_code == 200
        assert "Document Authenticity Confirmed" in r_pub.text
        assert "Adebayo Olumide" in r_pub.text
        # Ensure private phone and address are not leaked
        assert "+2348012345678" not in r_pub.text
        assert "Plot 14, Alausa Crescent" not in r_pub.text
        print("    [+] Public verification portal validated (privacy safeguards working)!")

    # 10. Distinct Dashboard checks (No Twin Content)
    def login_role(username, password):
        sess = requests.Session()
        lp = sess.get(f"{BASE_URL}/auth/login")
        c_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', lp.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', lp.text)
        token = c_match.group(1) if c_match else ""
        resp = sess.post(f"{BASE_URL}/auth/login", data={
            'csrf_token': token,
            'username_or_email': username,
            'password': password
        }, allow_redirects=True)
        return sess, resp

    # Check HR Officer Dashboard
    s_hr, r_hr_login = login_role('hr_officer', 'HrPass@2026')
    assert r_hr_login.status_code == 200
    assert "Human Resources Directorate" in r_hr_login.text
    assert "Applications Requiring HR Service Verification" in r_hr_login.text
    print("    [+] HR Officer dashboard verified with dedicated service verification queue!")

    # Check Pension Officer Dashboard
    s_pension, r_pen_login = login_role('pension_officer', 'PensionPass@2026')
    assert r_pen_login.status_code == 200
    assert "Pension Clearance & Entitlements Board" in r_pen_login.text
    assert "Clearance Applications Awaiting Pension Adjudication" in r_pen_login.text
    print("    [+] Pension Officer dashboard verified with dedicated adjudication queue!")

    # Check Auditor Dashboard
    s_auditor, r_aud_login = login_role('auditor', 'AuditorPass@2026')
    assert r_aud_login.status_code == 200
    assert "Independent Audit & Irregularities Desk" in r_aud_login.text
    assert "Applications Flagged for Irregularities" in r_aud_login.text
    print("    [+] Auditor dashboard verified with dedicated audit & irregularities queue!")

    # 11. AI Verification & Decision Support Engine checks
    s_admin, _ = login_role('admin', 'AdminPass@2026')
    
    # 11a. View AI Screening Desk
    r_ai_index = s_admin.get(f"{BASE_URL}/verification/")
    print(f"[*] GET /verification/ -> Status: {r_ai_index.status_code}")
    assert r_ai_index.status_code == 200
    assert "AI-Assisted Verification & Anomaly Screening" in r_ai_index.text
    assert "Retirement Dossiers & AI Assessment Ledger" in r_ai_index.text
    print("    [+] Central AI Screening Desk verified!")

    # 11b. View AI Detailed Dossier
    r_ai_detail = s_admin.get(f"{BASE_URL}/verification/detail/1")
    print(f"[*] GET /verification/detail/1 -> Status: {r_ai_detail.status_code}")
    assert r_ai_detail.status_code == 200
    assert "Evaluated Civil Service Eligibility Rules" in r_ai_detail.text
    assert "Automated Document Content Analysis" in r_ai_detail.text
    print("    [+] AI detailed dossier and rule breakdown verified!")

    # 11c. Execute On-Demand AI Pipeline Run
    detail_csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r_ai_detail.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', r_ai_detail.text)
    detail_csrf = detail_csrf_match.group(1) if detail_csrf_match else ""
    r_ai_run = s_admin.post(f"{BASE_URL}/verification/run/1", data={
        'csrf_token': detail_csrf
    }, allow_redirects=True)
    print(f"[*] POST /verification/run/1 -> Status: {r_ai_run.status_code}")
    assert r_ai_run.status_code == 200
    assert "AI Screening successfully executed" in r_ai_run.text
    print("    [+] On-demand AI pipeline successfully executed with statutory rules and anomaly detection!")

    print("\n[SUCCESS] ALL LIVE HTTP INTEGRATION TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    run_live_verification()
