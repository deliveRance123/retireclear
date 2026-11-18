from datetime import datetime
from app.extensions import db

class AIVerification(db.Model):
    __tablename__ = 'ai_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('retirement_applications.id', ondelete='CASCADE'), nullable=False, index=True)
    verification_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Calculated metrics
    calculated_age = db.Column(db.Integer, nullable=False)
    calculated_years_of_service = db.Column(db.Numeric(4, 1), nullable=False)
    
    # Eligibility outcomes
    age_eligibility_status = db.Column(db.String(30), nullable=False)  # Eligible, Not Eligible
    service_eligibility_status = db.Column(db.String(30), nullable=False)  # Eligible, Not Eligible
    overall_eligibility_recommendation = db.Column(db.String(50), nullable=False)  # Eligible, Ineligible, Further Verification Required, Manual Review Required
    rule_evaluation_details = db.Column(db.JSON, nullable=True)  # List/dict of rules and conditions evaluated
    
    # OCR alignment outcomes
    ocr_name_match_status = db.Column(db.String(50), default='Not Evaluated')  # Exact Match, Fuzzy Match, Inconsistent, Not Found
    ocr_staff_no_match_status = db.Column(db.String(50), default='Not Evaluated')
    ocr_date_match_status = db.Column(db.String(50), default='Not Evaluated')
    
    # Anomaly / Inconsistency detection
    inconsistencies_detected = db.Column(db.JSON, nullable=True)
    missing_documents = db.Column(db.JSON, nullable=True)
    duplicate_records_found = db.Column(db.JSON, nullable=True)
    
    # Risk assessment
    fraud_score = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 - 100.0 scale (from PDF Sec 3.8.5 & 4.2.7)
    confidence_score = db.Column(db.Float, default=95.0, nullable=False)  # AI Confidence Level % (PDF Sec 4.2.7)
    fraud_risk_level = db.Column(db.String(30), default='Low', nullable=False)  # Low, Moderate, High, Critical
    fraud_risk_rationale = db.Column(db.Text, nullable=True)
    model_status = db.Column(db.String(120), default='Rule-based verification & anomaly detection engine', nullable=False)
    
    # Biometrics
    biometric_status = db.Column(db.String(80), default='Not Configured (Hardware Required)', nullable=False)
    biometric_details = db.Column(db.JSON, nullable=True)
    
    # Human Officer Review State
    requires_manual_review = db.Column(db.Boolean, default=False)
    reviewed_by_officer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    officer_comments = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    application = db.relationship('RetirementApplication', back_populates='ai_verifications')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_officer_id])

    def __repr__(self):
        return f'<AIVerification for App #{self.application_id}: {self.overall_eligibility_recommendation} ({self.fraud_risk_level} Risk)>'
