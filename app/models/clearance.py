from datetime import datetime
from app.extensions import db

class Clearance(db.Model):
    __tablename__ = 'clearances'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('retirement_applications.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    approving_officer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    decision = db.Column(db.String(30), nullable=False)  # Approved, Rejected, Further Verification Required
    decision_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    
    pension_entitlement_status = db.Column(db.String(60), default='Cleared for Statutory Benefits')
    gratuity_applicable = db.Column(db.Boolean, default=True)
    monthly_pension_applicable = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    application = db.relationship('RetirementApplication', back_populates='clearance')
    approving_officer = db.relationship('User', foreign_keys=[approving_officer_id])
    certificate = db.relationship('RetirementCertificate', back_populates='clearance', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Clearance for App #{self.application_id}: {self.decision}>'


class RetirementCertificate(db.Model):
    __tablename__ = 'retirement_certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    certificate_number = db.Column(db.String(60), unique=True, nullable=False, index=True)  # e.g., FGN-RET-CERT-2026-00042
    clearance_id = db.Column(db.Integer, db.ForeignKey('clearances.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    application_id = db.Column(db.Integer, db.ForeignKey('retirement_applications.id', ondelete='CASCADE'), nullable=False, index=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    
    verification_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    qr_code_path = db.Column(db.String(255), nullable=True)
    pdf_path = db.Column(db.String(255), nullable=True)
    
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_sample = db.Column(db.Boolean, default=True)  # Clearly identified as demonstration/sample document
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    clearance = db.relationship('Clearance', back_populates='certificate')
    application = db.relationship('RetirementApplication', back_populates='certificate')
    employee = db.relationship('Employee', back_populates='certificates')

    def __repr__(self):
        return f'<RetirementCertificate {self.certificate_number}>'


class InvestigationRecord(db.Model):
    __tablename__ = 'investigation_records'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('retirement_applications.id', ondelete='CASCADE'), nullable=False, index=True)
    auditor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    investigation_type = db.Column(db.String(60), nullable=False)  # duplicate_record, identity_mismatch, service_duration_anomaly, missing_records, other
    findings = db.Column(db.Text, nullable=False)
    recommended_action = db.Column(db.String(80), nullable=False)  # Refer to Law Enforcement, Request Secondary Documents, Cleared after Verification, Cancel Application
    
    status = db.Column(db.String(30), default='Open', nullable=False)  # Open, Under Review, Resolved, Escalated
    resolution_date = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    application = db.relationship('RetirementApplication', back_populates='investigations')
    auditor = db.relationship('User', foreign_keys=[auditor_id])

    def __repr__(self):
        return f'<InvestigationRecord #{self.id} for App #{self.application_id} - {self.status}>'
