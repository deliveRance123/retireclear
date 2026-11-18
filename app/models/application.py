from datetime import datetime
from app.extensions import db

class ApplicationStatus:
    DRAFT = 'Draft'
    SUBMITTED = 'Submitted'
    PENDING_HR = 'Pending HR Verification'
    DOCUMENTS_INCOMPLETE = 'Documents Incomplete'
    AI_VERIFICATION = 'AI Verification in Progress'
    FLAGGED = 'Flagged for Investigation'
    PENDING_PENSION = 'Pending Pension Review'
    FURTHER_VERIFICATION = 'Further Verification Required'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
    CERTIFICATE_GENERATED = 'Certificate Generated'

class ApplicationStage:
    HR = 'HR Verification'
    AI = 'AI/OCR Screening'
    AUDITOR = 'Audit Investigation'
    PENSION = 'Pension Review'
    COMPLETED = 'Completed'

class RetirementApplication(db.Model):
    __tablename__ = 'retirement_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    application_reference = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., RET-2026-00104
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    
    reason_for_retirement = db.Column(db.String(100), nullable=False)  # Statutory Age (60 Years), Years of Service (35 Years), Voluntary, Medical
    proposed_retirement_date = db.Column(db.Date, nullable=False)
    
    current_status = db.Column(db.String(60), default=ApplicationStatus.PENDING_HR, nullable=False, index=True)
    current_stage = db.Column(db.String(50), default=ApplicationStage.HR, nullable=False)
    
    is_flagged = db.Column(db.Boolean, default=False, index=True)
    flag_reason = db.Column(db.Text, nullable=True)
    
    eligibility_summary = db.Column(db.String(100), nullable=True)  # e.g. "Eligible by Statutory Age (60+)"
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # HR verification details
    hr_verified_at = db.Column(db.DateTime, nullable=True)
    hr_officer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    hr_notes = db.Column(db.Text, nullable=True)
    
    # Pension officer review details
    pension_reviewed_at = db.Column(db.DateTime, nullable=True)
    pension_officer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    pension_notes = db.Column(db.Text, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employee = db.relationship('Employee', back_populates='applications')
    hr_officer = db.relationship('User', foreign_keys=[hr_officer_id])
    pension_officer = db.relationship('User', foreign_keys=[pension_officer_id])
    
    documents = db.relationship('UploadedDocument', back_populates='application', cascade='all, delete-orphan')
    ai_verifications = db.relationship('AIVerification', back_populates='application', cascade='all, delete-orphan', order_by='AIVerification.created_at.desc()')
    clearance = db.relationship('Clearance', back_populates='application', uselist=False, cascade='all, delete-orphan')
    status_history = db.relationship('ApplicationStatusHistory', back_populates='application', cascade='all, delete-orphan', order_by='ApplicationStatusHistory.created_at.desc()')
    investigations = db.relationship('InvestigationRecord', back_populates='application', cascade='all, delete-orphan')
    certificate = db.relationship('RetirementCertificate', back_populates='application', uselist=False)

    @property
    def latest_ai_verification(self):
        return self.ai_verifications[0] if self.ai_verifications else None

    def __repr__(self):
        return f'<RetirementApplication {self.application_reference} ({self.current_status})>'


class ApplicationStatusHistory(db.Model):
    __tablename__ = 'application_status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('retirement_applications.id', ondelete='CASCADE'), nullable=False, index=True)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    previous_status = db.Column(db.String(60), nullable=True)
    new_status = db.Column(db.String(60), nullable=False)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    application = db.relationship('RetirementApplication', back_populates='status_history')
    changed_by = db.relationship('User', foreign_keys=[changed_by_user_id])
