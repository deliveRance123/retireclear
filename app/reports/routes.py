from datetime import datetime
from flask import Blueprint, render_template, request, Response, flash, redirect, url_for
from flask_login import login_required, current_user
from app.auth.decorators import role_required
from app.services.report_service import ReportService
from app.services.audit_service import AuditService

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
@role_required('admin', 'hr_officer', 'pension_officer', 'auditor')
def index():
    admin_metrics = ReportService.get_administrative_metrics()
    return render_template('reports/index.html', metrics=admin_metrics)

@reports_bp.route('/clearance')
@login_required
@role_required('admin', 'hr_officer', 'pension_officer', 'auditor')
def clearance_report():
    department = request.args.get('department')
    status = request.args.get('status')
    export_csv = request.args.get('export') == 'csv'
    
    records = ReportService.get_clearance_report_data(department=department, status=status)
    
    if export_csv:
        csv_data = ReportService.export_clearance_csv(records)
        AuditService.log('EXPORT_CLEARANCE_REPORT_CSV', 'Report', None, {'records_count': len(records)})
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=Retirement_Clearance_Report_{datetime.utcnow().strftime("%Y%m%d")}.csv'}
        )
        
    return render_template('reports/clearance_report.html', records=records, department=department, status=status)

@reports_bp.route('/fraud-detection')
@login_required
@role_required('admin', 'auditor')
def fraud_report():
    fraud_data = ReportService.get_fraud_report_data()
    return render_template('reports/fraud_report.html', data=fraud_data)

@reports_bp.route('/administrative')
@login_required
@role_required('admin')
def admin_report():
    metrics = ReportService.get_administrative_metrics()
    return render_template('reports/admin_report.html', metrics=metrics)
