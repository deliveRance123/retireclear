import os
import uuid
from datetime import date, datetime, timedelta
from app import create_app
from app.extensions import db
from app.models.user import Role, User
from app.models.employee import Employee
from app.models.records import EmploymentRecord, PromotionRecord, PensionRecord
from app.models.application import RetirementApplication, ApplicationStatus, ApplicationStage, ApplicationStatusHistory
from app.models.document import UploadedDocument, DocumentType
from app.models.verification import AIVerification
from app.models.clearance import Clearance, RetirementCertificate, InvestigationRecord
from app.models.settings import SystemSetting
from app.models.audit import AuditLog
from app.models.notification import Notification
from app.services.certificate_service import CertificateService

def seed_database(target_app=None):
    if target_app is None:
        target_app = create_app(os.environ.get('FLASK_CONFIG', 'default'))
    with target_app.app_context():
        print("[*] Creating database tables if not existing...")
        db.create_all()

        print("[*] Seeding System Roles...")
        roles_data = [
            ('admin', 'System Administrator', 'Full portal governance and configuration privileges'),
            ('hr_officer', 'Human Resource Officer', 'Employee records management and service verification'),
            ('pension_officer', 'Pension Officer', 'Pension eligibility clearance and certificate generation'),
            ('auditor', 'Independent Auditor', 'Audit investigation, fraud detection, and integrity oversight'),
            ('civil_servant', 'Retiring Civil Servant', 'Self-service application filing and document tracking')
        ]
        roles = {}
        for code, disp, desc in roles_data:
            r = Role.query.filter_by(name=code).first()
            if not r:
                r = Role(name=code, display_name=disp, description=desc)
                db.session.add(r)
            roles[code] = r
        db.session.commit()

        print("[*] Seeding Configurable System Eligibility Rules...")
        default_settings = [
            ('statutory_retirement_age', '60', 'integer', 'Mandatory civil service retirement age threshold'),
            ('statutory_years_of_service', '35', 'integer', 'Mandatory civil service maximum years of service'),
            ('eligibility_logic_operator', 'OR', 'string', 'Boolean combination operator for age and service rules (OR/AND)'),
            ('min_voluntary_service_years', '10', 'integer', 'Minimum service years for voluntary pensionable retirement'),
            ('session_timeout_minutes', '60', 'integer', 'Session inactivity timeout in minutes')
        ]
        for key, val, stype, desc in default_settings:
            SystemSetting.set_value(key, val, desc, stype)

        print("[*] Seeding Primary Administrative Users...")
        users_data = [
            ('admin', 'admin@clearance.gov.ng', 'AdminPass@2026', 'Ibrahim', 'Danjuma', '+2348031112233', 'admin'),
            ('hr_officer', 'hr@education.gov.ng', 'HrPass@2026', 'Folashade', 'Adeyemi', '+2348023334455', 'hr_officer'),
            ('pension_officer', 'pension@pencom.gov.ng', 'PensionPass@2026', 'Emeka', 'Okafor', '+2348055556677', 'pension_officer'),
            ('auditor', 'auditor@fcs.gov.ng', 'AuditorPass@2026', 'Amina', 'Mohammed', '+2348097778899', 'auditor'),
            ('adebayo.olumide', 'adebayo.olumide@example.com', 'RetireePass@2026', 'Adebayo', 'Olumide', '+2348012345678', 'civil_servant')
        ]
        user_objects = {}
        for username, email, password, fname, lname, phone, role_code in users_data:
            u = User.query.filter_by(username=username).first()
            if not u:
                u = User(
                    username=username,
                    email=email,
                    first_name=fname,
                    last_name=lname,
                    phone=phone,
                    role_id=roles[role_code].id,
                    is_active=True
                )
                u.set_password(password)
                db.session.add(u)
            user_objects[username] = u
        db.session.commit()

        print("[*] Seeding Fictional Nigerian Civil Servant Records...")
        # 1. Primary demo employee: Adebayo Olumide (Eligible 60 yrs, 35 yrs service)
        emp1 = Employee.query.filter_by(staff_number='FGN/EDU/2018/00125').first()
        if not emp1:
            emp1 = Employee(
                user_id=user_objects['adebayo.olumide'].id,
                staff_number='FGN/EDU/2018/00125',
                first_name='Adebayo',
                middle_name='Sunday',
                last_name='Olumide',
                gender='Male',
                date_of_birth=date(1966, 4, 15),
                state_of_origin='Lagos',
                lga='Ikeja',
                residential_address='Plot 14, Alausa Crescent, Ikeja',
                city='Ikeja',
                state_of_residence='Lagos',
                phone_number='+2348012345678',
                email='adebayo.olumide@example.com',
                nin='28491029384',
                bvn='22109847561',
                ministry_or_agency='Federal Ministry of Education',
                department='Secondary Education Directorate',
                current_cadre='Chief Education Officer',
                current_grade_level='GL 14',
                current_step=8,
                appointment_date=date(1991, 5, 2),
                confirmation_date=date(1993, 5, 2),
                statutory_retirement_date=date(2026, 4, 15),
                biometric_enrolled=False
            )
            db.session.add(emp1)
            db.session.flush()

            # Add Employment history
            emp1.employment_records.append(EmploymentRecord(
                ministry_or_agency='Federal Ministry of Education',
                department='Secondary Education Directorate',
                cadre_and_rank='Chief Education Officer',
                grade_level='GL 14',
                start_date=date(1991, 5, 2),
                is_current=True,
                record_verified=True,
                verified_by_user_id=user_objects['hr_officer'].id
            ))

            # Add Promotions
            emp1.promotion_records.append(PromotionRecord(
                from_grade_level='GL 12',
                to_grade_level='GL 14',
                effective_date=date(2020, 1, 1),
                gazette_or_ref_number='FCSC/EDU/PROM/2020/084',
                is_verified=True,
                verified_by_user_id=user_objects['hr_officer'].id
            ))

            # Add Pension Record
            emp1.pension_records.append(PensionRecord(
                pfa_name='Stanbic IBTC Pension Managers',
                rsa_pin='PEN10023458912',
                total_contributions_estimate=18450000.00,
                status='Active',
                is_verified=True
            ))

            # Create Retirement Application
            app1 = RetirementApplication(
                application_reference='RET-2026-00125',
                employee_id=emp1.id,
                reason_for_retirement='Statutory Age (Attainment of 60 Years)',
                proposed_retirement_date=date(2026, 4, 15),
                current_status=ApplicationStatus.CERTIFICATE_GENERATED,
                current_stage=ApplicationStage.COMPLETED,
                submission_date=datetime.utcnow() - timedelta(days=12),
                hr_verified_at=datetime.utcnow() - timedelta(days=9),
                hr_officer_id=user_objects['hr_officer'].id,
                pension_reviewed_at=datetime.utcnow() - timedelta(days=5),
                pension_officer_id=user_objects['pension_officer'].id
            )
            db.session.add(app1)
            db.session.flush()

            # Add Documents
            docs_info = [
                (DocumentType.APPOINTMENT_LETTER, 'appointment_letter_olumide.pdf'),
                (DocumentType.PROMOTION_LETTER, 'promotion_letter_gl14.pdf'),
                (DocumentType.BIRTH_CERTIFICATE, 'birth_declaration_olumide.pdf'),
                (DocumentType.STAFF_ID_CARD, 'staff_id_olumide.jpg'),
                (DocumentType.PENSION_RECORD, 'rsa_statement_stanbic.pdf')
            ]
            for dtype, fname in docs_info:
                doc = UploadedDocument(
                    application_id=app1.id,
                    document_type=dtype,
                    original_filename=fname,
                    stored_filename=f"seed_{fname}",
                    file_path=os.path.join(app.config['UPLOAD_FOLDER'], 'documents', f"seed_{fname}"),
                    file_size_bytes=1048576,
                    mime_type='application/pdf' if fname.endswith('.pdf') else 'image/jpeg',
                    sha256_hash=uuid.uuid4().hex,
                    ocr_status='processed',
                    extracted_text=f"FEDERAL REPUBLIC OF NIGERIA\nSTAFF: FGN/EDU/2018/00125\nNAME: ADEBAYO OLUMIDE\nMINISTRY OF EDUCATION",
                    extracted_metadata={'entities': {'staff_numbers': ['FGN/EDU/2018/00125']}, 'comparison': {'staff_no_match': 'Exact Match', 'name_match': 'Full Name Match'}}
                )
                db.session.add(doc)

            # AI Verification
            ai1 = AIVerification(
                application_id=app1.id,
                calculated_age=60,
                calculated_years_of_service=35.0,
                age_eligibility_status='Eligible',
                service_eligibility_status='Eligible',
                overall_eligibility_recommendation='Eligible',
                rule_evaluation_details=[
                    {
                        'rule_code': 'RULE_AGE_60',
                        'rule_name': 'Statutory Retirement Age Requirement (≥ 60 years)',
                        'criterion': 'Age >= 60',
                        'actual_value': '60 years (DOB: 15/04/1966)',
                        'passed': True,
                        'explanation': 'Civil servant has attained statutory retirement age of 60 years.'
                    },
                    {
                        'rule_code': 'RULE_SERVICE_35',
                        'rule_name': 'Statutory Years of Service Requirement (≥ 35 years)',
                        'criterion': 'Service >= 35',
                        'actual_value': '35.0 years (Appointed: 02/05/1991)',
                        'passed': True,
                        'explanation': 'Civil servant has accumulated 35 years of pensionable public service.'
                    }
                ],
                ocr_name_match_status='Full Name Match',
                ocr_staff_no_match_status='Exact Match',
                ocr_date_match_status='Consistent',
                fraud_risk_level='Low',
                fraud_risk_rationale='Routine statutory retirement verified. No record conflicts.',
                requires_manual_review=False
            )
            db.session.add(ai1)

            # Clearance & Certificate
            clr1 = Clearance(
                application_id=app1.id,
                approving_officer_id=user_objects['pension_officer'].id,
                decision='Approved',
                decision_date=datetime.utcnow() - timedelta(days=5),
                remarks='Full statutory clearance granted. Cleared for monthly pension and gratuity benefits.',
                pension_entitlement_status='Cleared for Statutory Benefits'
            )
            db.session.add(clr1)
            db.session.flush()

            CertificateService.generate_certificate(clr1, is_sample=True)

        # 2. Second Employee: Chinedu Eze (Ministry of Finance, GL 16, pending pension review)
        emp2 = Employee.query.filter_by(staff_number='FGN/FMF/2012/04491').first()
        if not emp2:
            emp2 = Employee(
                staff_number='FGN/FMF/2012/04491',
                first_name='Chinedu',
                middle_name='Emeka',
                last_name='Eze',
                gender='Male',
                date_of_birth=date(1968, 8, 22),
                state_of_origin='Enugu',
                lga='Nkanu West',
                residential_address='18 Independence Layout, Enugu',
                city='Enugu',
                state_of_residence='Enugu',
                phone_number='+2348039988776',
                email='chinedu.eze@example.com',
                nin='39481928471',
                bvn='22019485762',
                ministry_or_agency='Federal Ministry of Finance',
                department='Treasury & Consolidated Accounts',
                current_cadre='Director of Accounts',
                current_grade_level='GL 16',
                current_step=4,
                appointment_date=date(1991, 7, 10),
                confirmation_date=date(1993, 7, 10),
                statutory_retirement_date=date(2026, 7, 10)
            )
            db.session.add(emp2)
            db.session.flush()

            emp2.pension_records.append(PensionRecord(
                pfa_name='ARM Pension Managers',
                rsa_pin='PEN10088492019',
                total_contributions_estimate=24100000.00
            ))

            app2 = RetirementApplication(
                application_reference='RET-2026-04491',
                employee_id=emp2.id,
                reason_for_retirement='Statutory Years of Service (Attainment of 35 Years)',
                proposed_retirement_date=date(2026, 7, 10),
                current_status=ApplicationStatus.PENDING_PENSION,
                current_stage=ApplicationStage.PENSION,
                submission_date=datetime.utcnow() - timedelta(days=4),
                hr_verified_at=datetime.utcnow() - timedelta(days=2),
                hr_officer_id=user_objects['hr_officer'].id
            )
            db.session.add(app2)
            db.session.flush()

            ai2 = AIVerification(
                application_id=app2.id,
                calculated_age=58,
                calculated_years_of_service=35.0,
                age_eligibility_status='Not Eligible',
                service_eligibility_status='Eligible',
                overall_eligibility_recommendation='Eligible',
                rule_evaluation_details=[
                    {
                        'rule_code': 'RULE_SERVICE_35',
                        'rule_name': 'Statutory Years of Service Requirement (≥ 35 years)',
                        'criterion': 'Service >= 35',
                        'actual_value': '35.0 years',
                        'passed': True,
                        'explanation': 'Civil servant qualifies by attaining 35 maximum statutory years of service.'
                    }
                ],
                fraud_risk_level='Low',
                fraud_risk_rationale='Service duration verified via official civil service ledger.'
            )
            db.session.add(ai2)

        # 3. Third Employee: Yakubu Garba (Flagged duplicate / underage appointment anomaly)
        emp3 = Employee.query.filter_by(staff_number='FGN/MOW/2021/08812').first()
        if not emp3:
            emp3 = Employee(
                staff_number='FGN/MOW/2021/08812',
                first_name='Yakubu',
                middle_name='Kabir',
                last_name='Garba',
                gender='Male',
                date_of_birth=date(1974, 11, 5),
                state_of_origin='Kano',
                lga='Dala',
                residential_address='No 5 Bompai Road, Kano',
                city='Kano',
                state_of_residence='Kano',
                phone_number='+2348029911223',
                email='yakubu.garba@example.com',
                nin='18294019284',
                ministry_or_agency='Federal Ministry of Works',
                department='Highways & Bridges Planning',
                current_cadre='Senior Technical Officer',
                current_grade_level='GL 10',
                current_step=3,
                appointment_date=date(2003, 9, 15),
                statutory_retirement_date=date(2034, 11, 5)
            )
            db.session.add(emp3)
            db.session.flush()

            app3 = RetirementApplication(
                application_reference='RET-2026-08812',
                employee_id=emp3.id,
                reason_for_retirement='Voluntary Retirement',
                proposed_retirement_date=date(2026, 6, 30),
                current_status=ApplicationStatus.FLAGGED,
                current_stage=ApplicationStage.AUDITOR,
                is_flagged=True,
                flag_reason='Suspected duplicate appointment letter and incomplete promotion track.',
                submission_date=datetime.utcnow() - timedelta(days=7)
            )
            db.session.add(app3)
            db.session.flush()

            ai3 = AIVerification(
                application_id=app3.id,
                calculated_age=52,
                calculated_years_of_service=22.7,
                age_eligibility_status='Not Eligible',
                service_eligibility_status='Not Eligible',
                overall_eligibility_recommendation='Manual Review Required',
                rule_evaluation_details=[],
                inconsistencies_detected=[
                    {
                        'type': 'INCOMPLETE_RECORDS',
                        'severity': 'High',
                        'description': 'Appointment date and gazette record indicate unexplained 4-year service gap.'
                    }
                ],
                fraud_risk_level='High',
                fraud_risk_rationale='High risk of record conflict. Auditor investigation required before clearance.',
                requires_manual_review=True
            )
            db.session.add(ai3)

            inv3 = InvestigationRecord(
                application_id=app3.id,
                auditor_id=user_objects['auditor'].id,
                investigation_type='Service Duration Conflict',
                findings='Initial audit reveals contradictory promotion letters between Ministry of Works and State Service records.',
                recommended_action='Request Secondary Supporting Documents',
                status='Open'
            )
            db.session.add(inv3)

        # 4. Fourth Employee: Fatima Bello (Ministry of Health, Pending HR Verification)
        emp4 = Employee.query.filter_by(staff_number='FGN/MOH/2015/01928').first()
        if not emp4:
            emp4 = Employee(
                staff_number='FGN/MOH/2015/01928',
                first_name='Fatima',
                middle_name='Zahra',
                last_name='Bello',
                gender='Female',
                date_of_birth=date(1965, 3, 20),
                state_of_origin='Kaduna',
                lga='Kaduna North',
                residential_address='12 Isa Kaita Road, Kaduna',
                city='Kaduna',
                state_of_residence='Kaduna',
                phone_number='+2348076655443',
                email='fatima.bello@example.com',
                nin='48291049281',
                ministry_or_agency='Federal Ministry of Health and Social Welfare',
                department='Hospital Services Directorate',
                current_cadre='Chief Nursing Officer',
                current_grade_level='GL 13',
                current_step=6,
                appointment_date=date(1996, 2, 14),
                statutory_retirement_date=date(2025, 3, 20)
            )
            db.session.add(emp4)
            db.session.flush()

            emp4.pension_records.append(PensionRecord(
                pfa_name='Premium Pension Limited',
                rsa_pin='PEN10099482014',
                total_contributions_estimate=15200000.00
            ))

            app4 = RetirementApplication(
                application_reference='RET-2026-01928',
                employee_id=emp4.id,
                reason_for_retirement='Statutory Age (Attainment of 60 Years)',
                proposed_retirement_date=date(2026, 3, 20),
                current_status=ApplicationStatus.PENDING_HR,
                current_stage=ApplicationStage.HR,
                submission_date=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(app4)

        db.session.commit()
        print("[+] Database successfully seeded with authentic fictional Nigerian demo records!")

if __name__ == '__main__':
    seed_database()
