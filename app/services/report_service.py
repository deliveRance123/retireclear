import io
import csv
from datetime import datetime
from sqlalchemy import func
from app.models.employee import Employee
from app.models.application import RetirementApplication, ApplicationStatus
from app.models.clearance import Clearance, InvestigationRecord
from app.models.verification import AIVerification

class ReportService:
    @staticmethod
    def get_clearance_report_data(start_date=None, end_date=None, department=None, status=None):
        query = RetirementApplication.query.join(Employee)
        
        if department:
            query = query.filter(Employee.department == department)
        if status:
            query = query.filter(RetirementApplication.current_status == status)
        if start_date:
            query = query.filter(RetirementApplication.submission_date >= start_date)
        if end_date:
            query = query.filter(RetirementApplication.submission_date <= end_date)
            
        applications = query.order_by(RetirementApplication.created_at.desc()).all()
        
        records = []
        for app in applications:
            emp = app.employee
            ai = app.latest_ai_verification
            clr = app.clearance
            
            records.append({
                'application_ref': app.application_reference,
                'staff_number': emp.staff_number,
                'full_name': emp.full_name,
                'department': emp.department,
                'ministry': emp.ministry_or_agency,
                'grade_level': emp.current_grade_level,
                'years_of_service': emp.years_of_service,
                'age': emp.age,
                'status': app.current_status,
                'ai_recommendation': ai.overall_eligibility_recommendation if ai else 'Pending AI Run',
                'ai_risk_level': ai.fraud_risk_level if ai else 'Not Evaluated',
                'clearance_decision': clr.decision if clr else 'Pending',
                'decision_date': clr.decision_date.strftime('%d/%m/%Y') if clr else 'N/A',
                'approving_officer': clr.approving_officer.full_name if clr else 'N/A'
            })
        return records

    @staticmethod
    def get_fraud_report_data():
        flagged_apps = RetirementApplication.query.filter(
            (RetirementApplication.is_flagged == True) | 
            (RetirementApplication.current_status == ApplicationStatus.FLAGGED)
        ).all()
        
        investigations = InvestigationRecord.query.order_by(InvestigationRecord.created_at.desc()).all()
        
        flagged_records = []
        for app in flagged_apps:
            ai = app.latest_ai_verification
            flagged_records.append({
                'application_ref': app.application_reference,
                'staff_number': app.employee.staff_number,
                'employee_name': app.employee.full_name,
                'department': app.employee.department,
                'flag_reason': app.flag_reason or (ai.fraud_risk_rationale if ai else 'Flagged for review'),
                'risk_level': ai.fraud_risk_level if ai else 'High',
                'fraud_score': getattr(ai, 'fraud_score', 0.0) if ai else 60.0,
                'confidence_score': getattr(ai, 'confidence_score', 85.0) if ai else 75.0,
                'duplicate_records': (ai.duplicate_records_found if (ai and ai.duplicate_records_found) else []),
                'missing_documents': (ai.missing_documents if (ai and ai.missing_documents) else []),
                'suspicious_activities': ([a.get('description', str(a)) for a in (ai.inconsistencies_detected or [])] if (ai and ai.inconsistencies_detected) else [app.flag_reason or 'Irregular service records']),
                'identity_mismatch': (ai.ocr_name_match_status if ai else 'Verification Pending'),
                'anomalies_count': len(ai.inconsistencies_detected or []) if ai else 1,
                'status': app.current_status
            })
            
        return {
            'flagged_cases': flagged_records,
            'investigations': investigations
        }

    @staticmethod
    def get_administrative_metrics():
        total_employees = Employee.query.count()
        total_applications = RetirementApplication.query.count()
        pending_applications = RetirementApplication.query.filter(
            RetirementApplication.current_status.in_([
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.PENDING_HR,
                ApplicationStatus.PENDING_PENSION,
                ApplicationStatus.AI_VERIFICATION
            ])
        ).count()
        approved_applications = RetirementApplication.query.filter_by(current_status=ApplicationStatus.APPROVED).count()
        rejected_applications = RetirementApplication.query.filter_by(current_status=ApplicationStatus.REJECTED).count()
        flagged_applications = RetirementApplication.query.filter_by(is_flagged=True).count()
        
        # Breakdown by department
        dept_breakdown = (
            Employee.query.with_entities(Employee.department, func.count(Employee.id))
            .group_by(Employee.department)
            .all()
        )
        
        # Monthly application volume
        monthly_query = (
            RetirementApplication.query.with_entities(
                func.substr(RetirementApplication.submission_date, 1, 7),
                func.count(RetirementApplication.id)
            )
            .group_by(func.substr(RetirementApplication.submission_date, 1, 7))
            .order_by(func.substr(RetirementApplication.submission_date, 1, 7).desc())
            .limit(6)
            .all()
        )

        # Predictive Analytics per PDF Section 3.8.1 & 2.1:
        # Forecast retirements within 12 months & 24 months based on age (≥59 / ≥58) and service (≥34 / ≥33)
        all_emps = Employee.query.all()
        retire_12m = sum(1 for e in all_emps if e.age >= 59 or e.years_of_service >= 34)
        retire_24m = sum(1 for e in all_emps if (e.age >= 58 or e.years_of_service >= 33) and not (e.age >= 59 or e.years_of_service >= 34))
        
        # Estimated liability (approx ₦5,200,000 avg gratuity per retiree)
        projected_liability_12m = retire_12m * 5200000
        
        predictive_analytics = {
            'projected_retirements_12m': retire_12m,
            'projected_retirements_24m': retire_24m,
            'projected_pension_liability_12m': f"₦{projected_liability_12m:,.2f}",
            'workforce_succession_need': f"{max(5, round((retire_12m / max(1, total_employees)) * 100, 1))}%"
        }
        
        return {
            'total_employees': total_employees,
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'approved_applications': approved_applications,
            'rejected_applications': rejected_applications,
            'flagged_applications': flagged_applications,
            'dept_breakdown': dept_breakdown,
            'monthly_stats': list(reversed(monthly_query)),
            'predictive_analytics': predictive_analytics
        }

    @staticmethod
    def export_clearance_csv(records):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Application Ref', 'Staff Number', 'Full Name', 'Ministry', 'Department',
            'Grade Level', 'Years of Service', 'Age', 'Status', 'AI Recommendation',
            'Fraud Risk', 'Clearance Decision', 'Decision Date', 'Approving Officer'
        ])
        for r in records:
            writer.writerow([
                r['application_ref'], r['staff_number'], r['full_name'], r['ministry'],
                r['department'], r['grade_level'], r['years_of_service'], r['age'],
                r['status'], r['ai_recommendation'], r['ai_risk_level'],
                r['clearance_decision'], r['decision_date'], r['approving_officer']
            ])
        return output.getvalue()
