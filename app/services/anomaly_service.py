from datetime import date, timedelta
from app.models.employee import Employee
from app.models.application import RetirementApplication
from app.models.document import UploadedDocument, DocumentType

class AnomalyDetectionService:
    @staticmethod
    def detect_anomalies(employee, application):
        """
        Execute multi-layer anomaly detection over civil service records,
        identifying duplicate records, date discrepancies, and fraud risks.
        """
        anomalies = []
        fraud_risk_score = 0  # 0 to 10 scale
        
        # 1. Duplicate Records Detection across database
        duplicates_found = []
        
        # Check duplicate Staff Number
        other_staff = Employee.query.filter(
            Employee.staff_number == employee.staff_number,
            Employee.id != employee.id
        ).all()
        if other_staff:
            duplicates_found.append(f"Staff Number '{employee.staff_number}' is registered to {len(other_staff)} other employee record(s).")
            fraud_risk_score += 4
            anomalies.append({
                'type': 'DUPLICATE_STAFF_NUMBER',
                'severity': 'Critical',
                'description': f"Critical duplicate conflict: Staff number {employee.staff_number} is already attached to another employee."
            })
            
        # Check duplicate NIN (if present)
        if employee.nin:
            other_nin = Employee.query.filter(
                Employee.nin == employee.nin,
                Employee.id != employee.id
            ).all()
            if other_nin:
                duplicates_found.append(f"National Identity Number (NIN) '{employee.nin}' matches {len(other_nin)} existing record(s).")
                fraud_risk_score += 4
                anomalies.append({
                    'type': 'DUPLICATE_NIN',
                    'severity': 'Critical',
                    'description': f"National Identity Number (NIN) {employee.nin} is already in use by another public servant."
                })

        # Check duplicate BVN (if present)
        if employee.bvn:
            other_bvn = Employee.query.filter(
                Employee.bvn == employee.bvn,
                Employee.id != employee.id
            ).all()
            if other_bvn:
                duplicates_found.append(f"Bank Verification Number (BVN) matches existing record(s).")
                fraud_risk_score += 3
                anomalies.append({
                    'type': 'DUPLICATE_BVN',
                    'severity': 'High',
                    'description': "BVN duplicate detected across civil service database."
                })
                
        # Check multiple concurrent active retirement applications
        other_active_apps = RetirementApplication.query.filter(
            RetirementApplication.employee_id == employee.id,
            RetirementApplication.id != application.id,
            RetirementApplication.current_status.notin_(['Rejected', 'Approved'])
        ).all()
        if other_active_apps:
            fraud_risk_score += 3
            anomalies.append({
                'type': 'CONCURRENT_APPLICATION',
                'severity': 'High',
                'description': f"Employee already has {len(other_active_apps)} active pending retirement application(s)."
            })

        # 2. Date & Service Chronology Anomalies
        if employee.date_of_birth and employee.appointment_date:
            age_at_appointment = (employee.appointment_date - employee.date_of_birth).days / 365.25
            if age_at_appointment < 18.0:
                fraud_risk_score += 3
                anomalies.append({
                    'type': 'UNDERAGE_APPOINTMENT',
                    'severity': 'High',
                    'description': f"Appointment date indicates employment began at age {age_at_appointment:.1f} (under statutory minimum age of 18 years)."
                })
            
            if employee.appointment_date > date.today():
                fraud_risk_score += 3
                anomalies.append({
                    'type': 'FUTURE_APPOINTMENT_DATE',
                    'severity': 'High',
                    'description': f"First appointment date ({employee.appointment_date.strftime('%d/%m/%Y')}) is in the future."
                })
                
            if application.proposed_retirement_date and application.proposed_retirement_date < employee.appointment_date:
                fraud_risk_score += 5
                anomalies.append({
                    'type': 'INVALID_RETIREMENT_DATE',
                    'severity': 'Critical',
                    'description': f"Proposed retirement date predates first appointment date."
                })

        # Check Promotion Timeline Consistency
        for prom in employee.promotion_records:
            if prom.effective_date < employee.appointment_date:
                fraud_risk_score += 2
                anomalies.append({
                    'type': 'PRE_APPOINTMENT_PROMOTION',
                    'severity': 'Medium',
                    'description': f"Promotion to {prom.to_grade_level} on {prom.effective_date.strftime('%d/%m/%Y')} is dated prior to initial appointment date."
                })

        # 3. Document Extraction Discrepancies
        ocr_name_status = 'Consistent'
        ocr_staff_status = 'Consistent'
        ocr_date_status = 'Consistent'
        
        for doc in application.documents:
            if doc.extracted_metadata and 'comparison' in doc.extracted_metadata:
                comp = doc.extracted_metadata['comparison']
                if 'Discrepancy' in comp.get('staff_no_match', ''):
                    ocr_staff_status = 'Inconsistent'
                    fraud_risk_score += 3
                    anomalies.append({
                        'type': 'OCR_STAFF_MISMATCH',
                        'severity': 'High',
                        'description': f"Discrepancy in {doc.display_type}: Extracted staff identifier differs from employee master record."
                    })
                if comp.get('name_match') == 'Name Not Detected in Text' and doc.document_type in (DocumentType.APPOINTMENT_LETTER, DocumentType.BIRTH_CERTIFICATE):
                    ocr_name_status = 'Name Mismatch / Undetected'
                    fraud_risk_score += 1
                    anomalies.append({
                        'type': 'OCR_NAME_UNDETECTED',
                        'severity': 'Low',
                        'description': f"Employee full name could not be reliably matched in {doc.display_type} text scan."
                    })

        # Determine Fraud Risk Level based on cumulative severity
        if fraud_risk_score >= 7:
            fraud_risk_level = 'Critical'
            risk_rationale = "Critical irregularities detected: High probability of record conflict, duplicate credentials, or forged chronological service tenure."
        elif fraud_risk_score >= 4:
            fraud_risk_level = 'High'
            risk_rationale = "High-risk anomalies flagged: Discrepancies found in document extraction or significant chronology inconsistencies."
        elif fraud_risk_score >= 2:
            fraud_risk_level = 'Moderate'
            risk_rationale = "Moderate attention items flagged: Document OCR requires human officer confirmation or partial service details missing."
        else:
            fraud_risk_level = 'Low'
            risk_rationale = "No significant integrity violations or record conflicts identified. Routine verification passed."

        # Numerical Fraud Score (0.0 - 100.0 scale, per PDF Section 3.8.5 & 4.2.7)
        fraud_score = float(min(100.0, round(fraud_risk_score * 10.0, 1)))

        # AI Confidence Level % (0.0 - 100.0%, per PDF Section 4.2.7)
        conf = 98.0 - (fraud_risk_score * 5.0) - (len(anomalies) * 2.5)
        confidence_score = float(max(35.0, min(99.0, round(conf, 1))))

        return {
            'fraud_risk_score': fraud_risk_score,
            'fraud_score': fraud_score,
            'confidence_score': confidence_score,
            'fraud_risk_level': fraud_risk_level,
            'fraud_risk_rationale': risk_rationale,
            'anomalies': anomalies,
            'duplicates_found': duplicates_found,
            'ocr_name_match_status': ocr_name_status,
            'ocr_staff_no_match_status': ocr_staff_status,
            'ocr_date_match_status': ocr_date_status,
            'requires_manual_review': fraud_risk_score >= 2 or len(anomalies) > 0,
            'model_status': 'Rule-based verification & anomaly detection engine'
        }
