import pytest
from datetime import date, datetime
from app.models.employee import Employee
from app.models.application import RetirementApplication
from app.models.records import PromotionRecord, PensionRecord
from app.models.document import UploadedDocument, DocumentType
from app.models.settings import SystemSetting
from app.services.eligibility_service import EligibilityService
from app.services.anomaly_service import AnomalyDetectionService
from app.services.biometric_service import BiometricService

def test_eligibility_age_60_condition(app):
    with app.app_context():
        # Employee age 60, service 20 years
        emp = Employee(
            staff_number='FGN/AGE/60/TEST',
            first_name='AgeEligible',
            last_name='Officer',
            gender='Female',
            date_of_birth=date(1966, 1, 1), # 60 years
            appointment_date=date(2006, 1, 1), # 20 years
            statutory_retirement_date=date(2026, 1, 1),
            state_of_origin='Lagos',
            residential_address='Lagos',
            city='Lagos',
            state_of_residence='Lagos',
            phone_number='+2348011112222',
            email='age60@example.com',
            ministry_or_agency='Federal Ministry of Education',
            department='Secondary Education',
            current_cadre='Education Officer',
            current_grade_level='GL 12'
        )
        emp.pension_records.append(PensionRecord(
            pfa_name='Stanbic IBTC Pension',
            rsa_pin='PEN_AGE_TEST_01',
            total_contributions_estimate=10000000.00
        ))
        emp.promotion_records.append(PromotionRecord(
            from_grade_level='GL 10',
            to_grade_level='GL 12',
            effective_date=date(2022, 1, 1)
        ))
        
        app_obj = RetirementApplication(
            application_reference='RET-AGE-60-TEST',
            employee=emp,
            reason_for_retirement='Statutory Age (60 Years)',
            proposed_retirement_date=date(2026, 1, 1)
        )
        # Add required documents
        for dtype in [DocumentType.APPOINTMENT_LETTER, DocumentType.BIRTH_CERTIFICATE, DocumentType.STAFF_ID_CARD, DocumentType.PENSION_RECORD]:
            app_obj.documents.append(UploadedDocument(
                document_type=dtype,
                original_filename=f"{dtype}.pdf",
                stored_filename=f"{dtype}.pdf",
                file_path=f"/fake/{dtype}.pdf",
                file_size_bytes=1000,
                mime_type='application/pdf',
                sha256_hash='fakehash'
            ))

        result = EligibilityService.evaluate_retirement_eligibility(emp, app_obj)
        assert result['age_eligible'] == 'Eligible'
        assert result['service_eligible'] == 'Not Eligible'
        assert result['overall_recommendation'] == 'Eligible'

def test_eligibility_service_35_condition(app):
    with app.app_context():
        # Employee age 55, service 35 years
        emp = Employee(
            staff_number='FGN/SRV/35/TEST',
            first_name='ServiceEligible',
            last_name='Officer',
            gender='Male',
            date_of_birth=date(1971, 1, 1), # 55 years
            appointment_date=date(1991, 1, 1), # 35 years service
            statutory_retirement_date=date(2026, 1, 1),
            state_of_origin='Kano',
            residential_address='Kano',
            city='Kano',
            state_of_residence='Kano',
            phone_number='+2348022223333',
            email='srv35@example.com',
            ministry_or_agency='Federal Ministry of Works',
            department='Civil Engineering',
            current_cadre='Senior Engineer',
            current_grade_level='GL 12'
        )
        emp.pension_records.append(PensionRecord(
            pfa_name='ARM Pension',
            rsa_pin='PEN_SRV_TEST_01'
        ))
        emp.promotion_records.append(PromotionRecord(
            from_grade_level='GL 10',
            to_grade_level='GL 12',
            effective_date=date(2021, 1, 1)
        ))

        app_obj = RetirementApplication(
            application_reference='RET-SRV-35-TEST',
            employee=emp,
            reason_for_retirement='Statutory Years of Service (35 Years)',
            proposed_retirement_date=date(2026, 1, 1)
        )
        for dtype in [DocumentType.APPOINTMENT_LETTER, DocumentType.BIRTH_CERTIFICATE, DocumentType.STAFF_ID_CARD, DocumentType.PENSION_RECORD]:
            app_obj.documents.append(UploadedDocument(
                document_type=dtype,
                original_filename=f"{dtype}.pdf",
                stored_filename=f"{dtype}.pdf",
                file_path=f"/fake/{dtype}.pdf",
                file_size_bytes=1000,
                mime_type='application/pdf',
                sha256_hash='fakehash'
            ))

        result = EligibilityService.evaluate_retirement_eligibility(emp, app_obj)
        assert result['age_eligible'] == 'Not Eligible'
        assert result['service_eligible'] == 'Eligible'
        assert result['overall_recommendation'] == 'Eligible'

def test_missing_mandatory_documents_detection(app):
    with app.app_context():
        emp = Employee(
            staff_number='FGN/MISSING/DOCS',
            first_name='Incomplete',
            last_name='Applicant',
            gender='Male',
            date_of_birth=date(1964, 1, 1),
            appointment_date=date(1990, 1, 1),
            statutory_retirement_date=date(2024, 1, 1),
            state_of_origin='Oyo',
            residential_address='Ibadan',
            city='Ibadan',
            state_of_residence='Oyo',
            phone_number='+2348033334444',
            email='incomplete@example.com',
            ministry_or_agency='Ministry of Finance',
            department='Finance',
            current_cadre='Officer',
            current_grade_level='GL 08'
        )
        app_obj = RetirementApplication(
            application_reference='RET-MISSING-DOCS',
            employee=emp,
            reason_for_retirement='Statutory Age',
            proposed_retirement_date=date(2024, 1, 1)
        )
        # No documents uploaded
        result = EligibilityService.evaluate_retirement_eligibility(emp, app_obj)
        assert result['overall_recommendation'] == 'Further Verification Required'
        assert len(result['missing_docs']) > 0

def test_biometric_honest_status_boundary(app):
    with app.app_context():
        emp = Employee(
            staff_number='FGN/BIO/TEST',
            first_name='Bio',
            last_name='Test',
            gender='Female',
            date_of_birth=date(1975, 1, 1),
            appointment_date=date(2005, 1, 1),
            statutory_retirement_date=date(2035, 1, 1),
            state_of_origin='Delta',
            residential_address='Asaba',
            city='Asaba',
            state_of_residence='Delta',
            phone_number='+2348044445555',
            email='bio@example.com',
            ministry_or_agency='Health',
            department='Nursing',
            current_cadre='Nurse',
            current_grade_level='GL 09',
            biometric_enrolled=False
        )
        status = BiometricService.get_biometric_status(emp)
        assert status['hardware_connected'] is False
        assert status['status_label'] == 'Not Configured (Hardware Required)'
        assert status['requires_manual_waiver'] is True
