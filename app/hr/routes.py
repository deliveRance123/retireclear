import os
import uuid
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.employee import Employee
from app.models.records import EmploymentRecord, PromotionRecord, PensionRecord
from app.models.application import RetirementApplication, ApplicationStatus, ApplicationStage, ApplicationStatusHistory
from app.models.notification import Notification
from app.models.user import User, Role
from app.auth.decorators import role_required
from app.hr.forms import EmployeeRegistrationForm, PromotionRecordForm, PensionRecordForm
from app.services.audit_service import AuditService

hr_bp = Blueprint('hr', __name__)

@hr_bp.route('/dashboard')
@login_required
@role_required('hr_officer', 'admin')
def dashboard():
    today = date.today()
    in_six_months = today + timedelta(days=180)
    
    total_employees = Employee.query.count()
    upcoming_retirements = Employee.query.filter(
        Employee.statutory_retirement_date.between(today, in_six_months)
    ).count()
    
    pending_hr_apps = RetirementApplication.query.filter_by(
        current_status=ApplicationStatus.PENDING_HR
    ).count()
    
    verified_records = RetirementApplication.query.filter(
        RetirementApplication.hr_verified_at != None
    ).count()
    
    recent_employees = Employee.query.order_by(Employee.created_at.desc()).limit(6).all()
    pending_applications = RetirementApplication.query.filter(
        RetirementApplication.current_status.in_([
            ApplicationStatus.PENDING_HR,
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.DOCUMENTS_INCOMPLETE
        ])
    ).order_by(RetirementApplication.created_at.desc()).limit(6).all()
    
    return render_template(
        'hr/dashboard.html',
        total_employees=total_employees,
        upcoming_retirements=upcoming_retirements,
        pending_hr_apps=pending_hr_apps,
        verified_records=verified_records,
        recent_employees=recent_employees,
        pending_applications=pending_applications
    )

@hr_bp.route('/employees')
@login_required
@role_required('hr_officer', 'admin', 'pension_officer', 'auditor')
def employees():
    query = Employee.query
    search = request.args.get('search', '').strip()
    ministry = request.args.get('ministry', '').strip()
    grade = request.args.get('grade', '').strip()
    
    if search:
        query = query.filter(
            (Employee.staff_number.ilike(f'%{search}%')) |
            (Employee.first_name.ilike(f'%{search}%')) |
            (Employee.last_name.ilike(f'%{search}%')) |
            (Employee.email.ilike(f'%{search}%'))
        )
    if ministry:
        query = query.filter(Employee.ministry_or_agency == ministry)
    if grade:
        query = query.filter(Employee.current_grade_level == grade)
        
    employee_list = query.order_by(Employee.created_at.desc()).all()
    return render_template('hr/employees.html', employees=employee_list, search=search, ministry=ministry, grade=grade)

@hr_bp.route('/employees/register', methods=['GET', 'POST'])
@login_required
@role_required('hr_officer', 'admin')
def register_employee():
    form = EmployeeRegistrationForm()
    if form.validate_on_submit():
        # Check duplicate staff number
        existing = Employee.query.filter_by(staff_number=form.staff_number.data.strip().upper()).first()
        if existing:
            flash(f"Error: Staff Number '{form.staff_number.data}' is already registered in the system.", "danger")
            return render_template('hr/employee_form.html', form=form, title="Register New Civil Servant")
        
        # Check duplicate email
        existing_email = Employee.query.filter_by(email=form.email.data.strip().lower()).first()
        if existing_email:
            flash(f"Error: Email address '{form.email.data}' is already associated with another employee record.", "danger")
            return render_template('hr/employee_form.html', form=form, title="Register New Civil Servant")

        # Handle passport upload
        passport_path = None
        if form.passport_photo.data:
            f = form.passport_photo.data
            ext = secure_filename(f.filename).rsplit('.', 1)[-1].lower()
            photo_name = f"passport_{uuid.uuid4().hex[:10]}.{ext}"
            folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'passports')
            os.makedirs(folder, exist_ok=True)
            f.save(os.path.join(folder, photo_name))
            passport_path = f"passports/{photo_name}"
            
        emp = Employee(
            staff_number=form.staff_number.data.strip().upper(),
            first_name=form.first_name.data.strip(),
            middle_name=form.middle_name.data.strip() if form.middle_name.data else None,
            last_name=form.last_name.data.strip(),
            gender=form.gender.data,
            date_of_birth=form.date_of_birth.data,
            state_of_origin=form.state_of_origin.data,
            lga=form.lga.data.strip() if form.lga.data else None,
            residential_address=form.residential_address.data.strip(),
            city=form.city.data.strip(),
            state_of_residence=form.state_of_residence.data,
            phone_number=form.phone_number.data.strip(),
            email=form.email.data.strip().lower(),
            nin=form.nin.data.strip() if form.nin.data else None,
            bvn=form.bvn.data.strip() if form.bvn.data else None,
            ministry_or_agency=form.ministry_or_agency.data,
            department=form.department.data.strip(),
            current_cadre=form.current_cadre.data.strip(),
            current_grade_level=form.current_grade_level.data,
            current_step=form.current_step.data,
            appointment_date=form.appointment_date.data,
            confirmation_date=form.confirmation_date.data,
            statutory_retirement_date=form.statutory_retirement_date.data,
            passport_photo_path=passport_path
        )
        
        # Also create initial employment record
        emp_rec = EmploymentRecord(
            ministry_or_agency=form.ministry_or_agency.data,
            department=form.department.data.strip(),
            cadre_and_rank=form.current_cadre.data.strip(),
            grade_level=form.current_grade_level.data,
            start_date=form.appointment_date.data,
            is_current=True,
            record_verified=True,
            verified_by_user_id=current_user.id
        )
        emp.employment_records.append(emp_rec)
        
        db.session.add(emp)
        db.session.commit()
        
        AuditService.log('REGISTER_EMPLOYEE', 'Employee', emp.id, {
            'staff_number': emp.staff_number,
            'full_name': emp.full_name,
            'ministry': emp.ministry_or_agency
        })
        
        flash(f"Public servant record for {emp.full_name} ({emp.staff_number}) successfully registered.", "success")
        return redirect(url_for('hr.employee_detail', employee_id=emp.id))
        
    return render_template('hr/employee_form.html', form=form, title="Register New Civil Servant")

@hr_bp.route('/employees/<int:employee_id>')
@login_required
@role_required('hr_officer', 'admin', 'pension_officer', 'auditor')
def employee_detail(employee_id):
    emp = Employee.query.get_or_404(employee_id)
    promotion_form = PromotionRecordForm()
    pension_form = PensionRecordForm()
    return render_template('hr/employee_detail.html', employee=emp, promotion_form=promotion_form, pension_form=pension_form)

@hr_bp.route('/employees/<int:employee_id>/add-promotion', methods=['POST'])
@login_required
@role_required('hr_officer', 'admin')
def add_promotion(employee_id):
    emp = Employee.query.get_or_404(employee_id)
    form = PromotionRecordForm()
    if form.validate_on_submit():
        prom = PromotionRecord(
            employee_id=emp.id,
            from_grade_level=form.from_grade_level.data,
            to_grade_level=form.to_grade_level.data,
            effective_date=form.effective_date.data,
            gazette_or_ref_number=form.gazette_or_ref_number.data.strip() if form.gazette_or_ref_number.data else None,
            is_verified=True,
            verified_by_user_id=current_user.id
        )
        emp.current_grade_level = form.to_grade_level.data
        db.session.add(prom)
        db.session.commit()
        AuditService.log('ADD_PROMOTION_RECORD', 'Employee', emp.id, {
            'from_grade': prom.from_grade_level,
            'to_grade': prom.to_grade_level
        })
        flash("Promotion record successfully registered and grade level updated.", "success")
    return redirect(url_for('hr.employee_detail', employee_id=emp.id))

@hr_bp.route('/employees/<int:employee_id>/add-pension', methods=['POST'])
@login_required
@role_required('hr_officer', 'admin')
def add_pension(employee_id):
    emp = Employee.query.get_or_404(employee_id)
    form = PensionRecordForm()
    if form.validate_on_submit():
        contrib = 0.00
        if form.total_contributions_estimate.data:
            try:
                contrib = float(form.total_contributions_estimate.data.replace(',', '').replace('₦', '').strip())
            except ValueError:
                contrib = 0.00
                
        pension = PensionRecord(
            employee_id=emp.id,
            pfa_name=form.pfa_name.data,
            rsa_pin=form.rsa_pin.data.strip().upper(),
            total_contributions_estimate=contrib,
            is_verified=True
        )
        db.session.add(pension)
        db.session.commit()
        AuditService.log('ADD_PENSION_RECORD', 'Employee', emp.id, {'pfa': pension.pfa_name, 'rsa_pin': pension.rsa_pin})
        flash("Pension Administration record linked successfully.", "success")
    return redirect(url_for('hr.employee_detail', employee_id=emp.id))

@hr_bp.route('/verify-records/<int:application_id>', methods=['GET', 'POST'])
@login_required
@role_required('hr_officer', 'admin')
def verify_records(application_id):
    app_obj = RetirementApplication.query.get_or_404(application_id)
    emp = app_obj.employee
    
    if request.method == 'POST':
        action = request.form.get('action')
        notes = request.form.get('notes', '').strip()
        
        if action == 'confirm':
            app_obj.hr_verified_at = datetime.utcnow()
            app_obj.hr_officer_id = current_user.id
            app_obj.hr_notes = notes
            app_obj.current_status = ApplicationStatus.PENDING_PENSION
            app_obj.current_stage = ApplicationStage.PENSION
            
            # Record status change
            history = ApplicationStatusHistory(
                application_id=app_obj.id,
                changed_by_user_id=current_user.id,
                previous_status=ApplicationStatus.PENDING_HR,
                new_status=ApplicationStatus.PENDING_PENSION,
                comments=f"HR Service Records verified by {current_user.full_name}. Forwarded to Pension Clearance Board. Notes: {notes}"
            )
            db.session.add(history)
            
            # Notify pension officers
            pension_role = Role.query.filter_by(name='pension_officer').first()
            if pension_role:
                for po in pension_role.users:
                    notif = Notification(
                        user_id=po.id,
                        title=f"New Clearance Awaiting Pension Review: {app_obj.application_reference}",
                        message=f"HR Service Records for {emp.full_name} ({emp.staff_number}) verified. Ready for pension assessment.",
                        link=url_for('pension.application_review', application_id=app_obj.id),
                        category='info'
                    )
                    db.session.add(notif)
                    
            db.session.commit()
            AuditService.log('HR_VERIFY_APPLICATION', 'RetirementApplication', app_obj.id, {'status': 'Forwarded to Pension'})
            flash(f"Application {app_obj.application_reference} verified and forwarded to Pension Clearance Officers.", "success")
            return redirect(url_for('hr.dashboard'))
            
        elif action == 'flag':
            reason = request.form.get('flag_reason', 'Discrepancy identified in service records.')
            app_obj.is_flagged = True
            app_obj.flag_reason = reason
            app_obj.current_status = ApplicationStatus.FLAGGED
            app_obj.current_stage = ApplicationStage.AUDITOR
            
            history = ApplicationStatusHistory(
                application_id=app_obj.id,
                changed_by_user_id=current_user.id,
                previous_status=app_obj.current_status,
                new_status=ApplicationStatus.FLAGGED,
                comments=f"Flagged for Auditor Review by HR Officer {current_user.full_name}. Reason: {reason}"
            )
            db.session.add(history)
            db.session.commit()
            AuditService.log('HR_FLAG_APPLICATION', 'RetirementApplication', app_obj.id, {'reason': reason})
            flash(f"Application {app_obj.application_reference} has been flagged for investigation.", "warning")
            return redirect(url_for('hr.dashboard'))

    return render_template('hr/verify_records.html', application=app_obj, employee=emp)
