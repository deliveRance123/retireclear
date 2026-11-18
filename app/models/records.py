from datetime import datetime
from app.extensions import db

class EmploymentRecord(db.Model):
    __tablename__ = 'employment_records'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    ministry_or_agency = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(120), nullable=False)
    cadre_and_rank = db.Column(db.String(100), nullable=False)
    grade_level = db.Column(db.String(15), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_current = db.Column(db.Boolean, default=True)
    record_verified = db.Column(db.Boolean, default=False)
    verified_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='employment_records')
    verifier = db.relationship('User', foreign_keys=[verified_by_user_id])


class PromotionRecord(db.Model):
    __tablename__ = 'promotion_records'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    from_grade_level = db.Column(db.String(15), nullable=False)
    to_grade_level = db.Column(db.String(15), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    gazette_or_ref_number = db.Column(db.String(120), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    verified_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='promotion_records')
    verifier = db.relationship('User', foreign_keys=[verified_by_user_id])


class PensionRecord(db.Model):
    __tablename__ = 'pension_records'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    pfa_name = db.Column(db.String(150), nullable=False)  # e.g., Stanbic IBTC Pension Managers
    rsa_pin = db.Column(db.String(50), nullable=False, unique=True, index=True)  # e.g., PEN10029384756
    last_contributed_date = db.Column(db.Date, nullable=True)
    total_contributions_estimate = db.Column(db.Numeric(14, 2), default=0.00)
    status = db.Column(db.String(30), default='Active')  # Active, Suspended, Transferred
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='pension_records')
