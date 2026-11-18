import re
import requests

def test_photo():
    s = requests.Session()
    r = s.get('http://127.0.0.1:5000/auth/avatar/passports/adebayo_olumide_passport.jpg')
    print('Avatar URL test:', r.status_code, 'Bytes:', len(r.content), 'Content-Type:', r.headers.get('Content-Type'))
    assert r.status_code == 200
    assert len(r.content) > 500000

    # Log in as Adebayo Olumide
    r_login = s.get('http://127.0.0.1:5000/auth/login')
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r_login.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', r_login.text)
    csrf_token = match.group(1)
    
    r_post = s.post('http://127.0.0.1:5000/auth/login', data={
        'username_or_email': 'adebayo.olumide',
        'password': 'RetireePass@2026',
        'csrf_token': csrf_token
    }, allow_redirects=True)
    
    # 1. Check Retiree Dashboard
    r_dash = s.get('http://127.0.0.1:5000/employee/dashboard')
    print('Retiree Dashboard:', r_dash.status_code, 'Final URL:', r_dash.url)
    for line in r_dash.text.splitlines():
        if 'passport' in line or 'avatar' in line or 'img' in line:
            print('  Line:', line.strip())
    assert 'adebayo_olumide_passport.jpg' in r_dash.text
    print(' -> PASSED: Passport photo displayed on Retiree Dashboard!')

    # 2. Check Retiree Profile
    r_prof = s.get('http://127.0.0.1:5000/employee/profile')
    print('Retiree Profile:', r_prof.status_code)
    assert 'adebayo_olumide_passport.jpg' in r_prof.text
    print(' -> PASSED: Passport photo displayed on Retiree Profile!')

    # 3. Check Certificate View
    r_cert = s.get('http://127.0.0.1:5000/certificates/view/1')
    print('Certificate View:', r_cert.status_code)
    assert 'adebayo_olumide_passport.jpg' in r_cert.text
    print(' -> PASSED: Passport photo displayed on Official Certificate!')

    # 4. Check HR Employee View
    s_hr = requests.Session()
    r_hr_login = s_hr.get('http://127.0.0.1:5000/auth/login')
    match_hr = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r_hr_login.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', r_hr_login.text)
    csrf_hr = match_hr.group(1)
    s_hr.post('http://127.0.0.1:5000/auth/login', data={
        'username_or_email': 'hr_officer',
        'password': 'HrPass@2026',
        'csrf_token': csrf_hr
    }, allow_redirects=True)
    r_hr_emp = s_hr.get('http://127.0.0.1:5000/hr/employees/1')
    print('HR Employee Detail:', r_hr_emp.status_code)
    assert 'adebayo_olumide_passport.jpg' in r_hr_emp.text
    print(' -> PASSED: Passport photo displayed on HR Officer Employee File!')

    # 5. Check Verification Detail
    r_ver = s_hr.get('http://127.0.0.1:5000/verification/detail/1')
    print('Verification Detail:', r_ver.status_code)
    assert 'adebayo_olumide_passport.jpg' in r_ver.text
    print(' -> PASSED: Passport photo displayed on AI Verification Detail!')

    print('\n[ALL RETIREE PHOTO TESTS PASSED PERFECTLY!]')

if __name__ == '__main__':
    test_photo()
