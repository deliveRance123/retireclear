from datetime import datetime, date
from app.extensions import db

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), unique=True, nullable=True, index=True)
    staff_number = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g. FGN/EDU/2018/00125
    first_name = db.Column(db.String(80), nullable=False)
    middle_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=False)
    gender = db.Column(db.String(15), nullable=False)  # Male, Female
    date_of_birth = db.Column(db.Date, nullable=False)
    state_of_origin = db.Column(db.String(50), nullable=False)
    lga = db.Column(db.String(80), nullable=True)
    residential_address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(80), nullable=False)
    state_of_residence = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    nin = db.Column(db.String(25), nullable=True)  # National Identity Number
    bvn = db.Column(db.String(25), nullable=True)  # Bank Verification Number
    
    ministry_or_agency = db.Column(db.String(150), nullable=False, index=True)
    department = db.Column(db.String(120), nullable=False, index=True)
    current_cadre = db.Column(db.String(100), nullable=False)
    current_grade_level = db.Column(db.String(15), nullable=False)  # e.g. GL 14
    current_step = db.Column(db.Integer, default=1)
    
    appointment_date = db.Column(db.Date, nullable=False)
    confirmation_date = db.Column(db.Date, nullable=True)
    statutory_retirement_date = db.Column(db.Date, nullable=False)
    
    passport_photo_path = db.Column(db.String(255), nullable=True)
    biometric_enrolled = db.Column(db.Boolean, default=False)
    biometric_reference_hash = db.Column(db.String(128), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='employee_profile')
    employment_records = db.relationship('EmploymentRecord', back_populates='employee', cascade='all, delete-orphan', order_by='EmploymentRecord.start_date.desc()')
    promotion_records = db.relationship('PromotionRecord', back_populates='employee', cascade='all, delete-orphan', order_by='PromotionRecord.effective_date.desc()')
    pension_records = db.relationship('PensionRecord', back_populates='employee', cascade='all, delete-orphan')
    applications = db.relationship('RetirementApplication', back_populates='employee', cascade='all, delete-orphan', order_by='RetirementApplication.created_at.desc()')
    certificates = db.relationship('RetirementCertificate', back_populates='employee')

    @property
    def passport_url(self):
        from flask import url_for
        if self.passport_photo_path:
            return url_for('auth.serve_avatar', filename=self.passport_photo_path)
        if self.user and self.user.avatar_path:
            return url_for('auth.serve_avatar', filename=self.user.avatar_path)
        return url_for('auth.serve_avatar', filename='passports/default_retiree_passport.jpg')

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join([p for p in parts if p])

    @property
    def age(self):
        if not self.date_of_birth:
            return 0
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def years_of_service(self):
        if not self.appointment_date:
            return 0.0
        today = date.today()
        delta_days = (today - self.appointment_date).days
        return round(max(0.0, delta_days / 365.25), 1)

    def __repr__(self):
        return f'<Employee {self.staff_number} - {self.full_name}>'
