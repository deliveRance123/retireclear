from datetime import date, datetime
from app.models.settings import SystemSetting
from app.models.document import DocumentType

class EligibilityService:
    @staticmethod
    def evaluate_retirement_eligibility(employee, application):
        """
        Evaluate civil service retirement eligibility using configurable rules.
        Default Nigerian Civil Service Rule: Age >= 60 OR Years of Service >= 35 (whichever comes first).
        """
        # Read configurable rules from SystemSettings
        statutory_age = SystemSetting.get_value('statutory_retirement_age', 60)
        statutory_service = SystemSetting.get_value('statutory_years_of_service', 35)
        logic_operator = SystemSetting.get_value('eligibility_logic_operator', 'OR').upper()
        min_voluntary_service = SystemSetting.get_value('min_voluntary_service_years', 10)
        
        calculated_age = employee.age
        calculated_service = employee.years_of_service
        
        rule_evaluations = []
        
        # Rule 1: Age Threshold
        age_eligible = calculated_age >= statutory_age
        rule_evaluations.append({
            'rule_code': 'RULE_AGE_60',
            'rule_name': f'Statutory Retirement Age Requirement (≥ {statutory_age} years)',
            'criterion': f'Age >= {statutory_age}',
            'actual_value': f'{calculated_age} years (DOB: {employee.date_of_birth.strftime("%d/%m/%Y")})',
            'passed': age_eligible,
            'explanation': (
                f'Civil servant is {calculated_age} years old, meeting the statutory threshold of {statutory_age} years.'
                if age_eligible else
                f'Civil servant is {calculated_age} years old, which is below the statutory retirement age of {statutory_age} years.'
            )
        })
        
        # Rule 2: Years of Service Threshold
        service_eligible = calculated_service >= statutory_service
        rule_evaluations.append({
            'rule_code': 'RULE_SERVICE_35',
            'rule_name': f'Statutory Years of Service Requirement (≥ {statutory_service} years)',
            'criterion': f'Service >= {statutory_service}',
            'actual_value': f'{calculated_service} years (Appointed: {employee.appointment_date.strftime("%d/%m/%Y")})',
            'passed': service_eligible,
            'explanation': (
                f'Civil servant has accumulated {calculated_service} years of pensionable service, meeting the {statutory_service} years cap.'
                if service_eligible else
                f'Civil servant has accumulated {calculated_service} years of service, below the {statutory_service} years limit.'
            )
        })
        
        # Rule 3: Voluntary Retirement Assessment
        is_voluntary = 'voluntary' in application.reason_for_retirement.lower()
        if is_voluntary:
            voluntary_passed = calculated_service >= min_voluntary_service
            rule_evaluations.append({
                'rule_code': 'RULE_VOLUNTARY_PENSIONABLE',
                'rule_name': f'Voluntary Retirement Minimum Service Requirement (≥ {min_voluntary_service} years)',
                'criterion': f'Service >= {min_voluntary_service}',
                'actual_value': f'{calculated_service} years',
                'passed': voluntary_passed,
                'explanation': (
                    f'Civil servant has attained {calculated_service} years of service, qualifying for voluntary retirement with pension.'
                    if voluntary_passed else
                    f'Civil servant with {calculated_service} years of service has not reached the {min_voluntary_service} years required for pensionable voluntary retirement.'
                )
            })

        # Rule 4: Mandatory Document Completeness
        required_doc_types = {
            DocumentType.APPOINTMENT_LETTER,
            DocumentType.BIRTH_CERTIFICATE,
            DocumentType.STAFF_ID_CARD,
            DocumentType.PENSION_RECORD
        }
        uploaded_types = {doc.document_type for doc in application.documents}
        missing_docs = [DocumentType.LABELS.get(t, t) for t in (required_doc_types - uploaded_types)]
        docs_complete = len(missing_docs) == 0
        rule_evaluations.append({
            'rule_code': 'RULE_MANDATORY_DOCS',
            'rule_name': 'Mandatory Document Completeness',
            'criterion': 'First Appointment, Birth Certificate, Staff ID, and Pension Record must be uploaded',
            'actual_value': f'{len(uploaded_types)} document types submitted',
            'passed': docs_complete,
            'explanation': (
                'All essential statutory service documents have been uploaded.'
                if docs_complete else
                f'Missing mandatory documents: {", ".join(missing_docs)}.'
            )
        })
        
        # Rule 5: Promotion Record Verification
        has_promotions = len(employee.promotion_records) > 0 or employee.current_grade_level in ('GL 01', 'GL 02', 'GL 03')
        rule_evaluations.append({
            'rule_code': 'RULE_PROMOTION_RECORD',
            'rule_name': 'Promotion & Gazetting History Check',
            'criterion': 'Employees at GL 04 and above must have recorded promotion/gazette track',
            'actual_value': f'{len(employee.promotion_records)} promotion records on file (Current: {employee.current_grade_level})',
            'passed': has_promotions,
            'explanation': (
                'Promotion history matches current grade level progression.'
                if has_promotions else
                f'No promotion record found on file for Grade Level {employee.current_grade_level}. Further verification is recommended.'
            )
        })
        
        # Rule 6: Pension Fund Administrator (PFA) Record
        has_pfa = len(employee.pension_records) > 0
        rule_evaluations.append({
            'rule_code': 'RULE_PFA_REGISTRATION',
            'rule_name': 'PenCom RSA & PFA Registration Verification',
            'criterion': 'Valid RSA PIN and licensed PFA on record',
            'actual_value': (
                f'{employee.pension_records[0].pfa_name} ({employee.pension_records[0].rsa_pin})'
                if has_pfa else 'No RSA registered'
            ),
            'passed': has_pfa,
            'explanation': (
                'Active Retirement Savings Account (RSA) with registered PFA confirmed.'
                if has_pfa else
                'No RSA PIN or Pension Fund Administrator registered for this employee.'
            )
        })

        # Combine logic according to configurable operator
        if logic_operator == 'AND':
            statutory_eligible = age_eligible and service_eligible
            logic_summary = f"Evaluated with conjunction (Age ≥ {statutory_age} AND Service ≥ {statutory_service})"
        else:
            # Default 'OR'
            statutory_eligible = age_eligible or service_eligible
            logic_summary = f"Evaluated with disjunction (Age ≥ {statutory_age} OR Service ≥ {statutory_service}, whichever is reached first)"
            
        if is_voluntary and calculated_service >= min_voluntary_service:
            statutory_eligible = True
            logic_summary = f"Voluntary retirement qualifying under {min_voluntary_service}+ years pensionable threshold"

        # Overall Recommendation Determination
        if not docs_complete:
            overall_recommendation = 'Further Verification Required'
            primary_reason = f"Application pending mandatory documents: {', '.join(missing_docs)}"
        elif not has_promotions:
            overall_recommendation = 'Further Verification Required'
            primary_reason = f"Missing promotion or gazette history on file for Grade Level {employee.current_grade_level}. Further administrative verification required."
        elif not has_pfa:
            overall_recommendation = 'Further Verification Required'
            primary_reason = "PFA / RSA pension record not yet registered or verified"
        elif statutory_eligible:
            overall_recommendation = 'Eligible'
            primary_reason = f"Applicant meets civil service statutory retirement requirements ({logic_summary})."
        else:
            overall_recommendation = 'Not Eligible'
            primary_reason = f"Applicant has not attained statutory retirement age ({calculated_age}/{statutory_age}) nor service threshold ({calculated_service}/{statutory_service} yrs)."
        
        return {
            'calculated_age': calculated_age,
            'calculated_years_of_service': calculated_service,
            'age_eligible': 'Eligible' if age_eligible else 'Not Eligible',
            'service_eligible': 'Eligible' if service_eligible else 'Not Eligible',
            'overall_recommendation': overall_recommendation,
            'primary_reason': primary_reason,
            'missing_docs': missing_docs,
            'rule_evaluations': rule_evaluations,
            'evaluated_at': datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S UTC'),
            'logic_operator_applied': logic_operator
        }
