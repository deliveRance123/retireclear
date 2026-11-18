from datetime import datetime
from app.extensions import db
from app.models.application import RetirementApplication, ApplicationStatus, ApplicationStage
from app.models.verification import AIVerification
from app.services.eligibility_service import EligibilityService
from app.services.anomaly_service import AnomalyDetectionService
from app.services.ocr_service import OCRService
from app.services.biometric_service import BiometricService

class AIVerificationService:
    """
    Centralized AI Verification and Decision-Support Engine.
    Coordinates:
      1. OCR Document Entity Extraction & Matching
      2. Configurable Statutory Retirement Eligibility Rules
      3. Statistical & Multi-layered Anomaly / Fraud Screening
      4. Biometric Terminal Integrity Verification
    """

    @staticmethod
    def run_pipeline(application, employee=None):
        """
        Execute full AI screening pipeline on a retirement clearance application.
        """
        if employee is None:
            employee = application.employee

        # 1. Ensure all uploaded documents have been OCR scanned
        for doc in application.documents:
            if doc.ocr_status != 'processed':
                try:
                    OCRService.process_document(doc.id, employee)
                except Exception as e:
                    print(f"[OCR Warning] Auto-processing doc #{doc.id}: {e}")

        # 2. Evaluate Statutory Eligibility Rules
        elig = EligibilityService.evaluate_retirement_eligibility(employee, application)

        # 3. Detect Anomalies & Calculate Fraud Risk
        anom = AnomalyDetectionService.detect_anomalies(employee, application)

        # 4. Check Biometric Status
        bio = BiometricService.get_biometric_status(employee)

        # 5. Record or Update AIVerification Entry
        ai_ver = AIVerification.query.filter_by(application_id=application.id).first()
        if not ai_ver:
            ai_ver = AIVerification(application_id=application.id)
            db.session.add(ai_ver)

        # Recommendation determination per PDF Table 4.9 & Section 4.2.7
        rec = elig['overall_recommendation']
        if anom.get('duplicates_found'):
            rec = 'Fraud Alert: Duplicate Records'
        elif bio.get('status_label') == 'Biometric Mismatch' or (anom.get('requires_manual_review') and rec == 'Eligible' and anom.get('fraud_risk_level') in ('High', 'Critical')):
            rec = 'Manual Review Required'

        ai_ver.calculated_age = elig['calculated_age']
        ai_ver.calculated_years_of_service = elig['calculated_years_of_service']
        ai_ver.age_eligibility_status = elig['age_eligible']
        ai_ver.service_eligibility_status = elig['service_eligible']
        ai_ver.overall_eligibility_recommendation = rec
        ai_ver.rule_evaluation_details = elig['rule_evaluations']

        ai_ver.ocr_name_match_status = anom['ocr_name_match_status']
        ai_ver.ocr_staff_no_match_status = anom['ocr_staff_no_match_status']
        ai_ver.ocr_date_match_status = anom['ocr_date_match_status']
        ai_ver.inconsistencies_detected = anom['anomalies']
        ai_ver.duplicate_records_found = anom['duplicates_found']
        ai_ver.missing_documents = elig['missing_docs']

        ai_ver.fraud_risk_level = anom['fraud_risk_level']
        ai_ver.fraud_score = anom.get('fraud_score', 0.0)
        ai_ver.confidence_score = anom.get('confidence_score', 95.0)
        ai_ver.fraud_risk_rationale = anom['fraud_risk_rationale']
        ai_ver.biometric_status = bio['status_label']
        ai_ver.biometric_details = bio
        ai_ver.requires_manual_review = anom['requires_manual_review'] or (rec == 'Manual Review Required')
        ai_ver.verification_timestamp = datetime.utcnow()

        # 6. Automatic risk escalation
        if anom['fraud_risk_level'] in ('High', 'Critical') and not application.is_flagged:
            application.is_flagged = True
            application.flag_reason = f"AI Automated Screen Flagged: {anom['fraud_risk_rationale']}"
            application.current_status = ApplicationStatus.FLAGGED
            application.current_stage = ApplicationStage.AUDITOR

        db.session.commit()
        return ai_ver
