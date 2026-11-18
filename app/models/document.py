from datetime import datetime
from app.extensions import db

class DocumentType:
    APPOINTMENT_LETTER = 'appointment_letter'
    PROMOTION_LETTER = 'promotion_letter'
    BIRTH_CERTIFICATE = 'birth_certificate'
    STAFF_ID_CARD = 'staff_id_card'
    PENSION_RECORD = 'pension_record'
    PASSPORT_PHOTO = 'passport_photo'
    FACIAL_CAPTURE = 'facial_capture'
    FINGERPRINT = 'fingerprint'

    LABELS = {
        APPOINTMENT_LETTER: 'First Appointment Letter',
        PROMOTION_LETTER: 'Current / Last Promotion Letter',
        BIRTH_CERTIFICATE: 'Birth Certificate / Age Declaration',
        STAFF_ID_CARD: 'Official Staff Identity Card',
        PENSION_RECORD: 'PenCom / PFA RSA Statement',
        PASSPORT_PHOTO: 'Official Passport Photograph',
        FACIAL_CAPTURE: 'Facial Biometric Enrolment Image',
        FINGERPRINT: 'Fingerprint Biometric Data'
    }

class UploadedDocument(db.Model):
    __tablename__ = 'uploaded_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('retirement_applications.id', ondelete='CASCADE'), nullable=False, index=True)
    document_type = db.Column(db.String(60), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    sha256_hash = db.Column(db.String(64), nullable=False)
    
    # OCR & extraction results
    ocr_status = db.Column(db.String(30), default='pending')  # pending, processed, failed, manual_review
    extracted_text = db.Column(db.Text, nullable=True)
    extracted_metadata = db.Column(db.JSON, nullable=True)  # extracted name, dates, staff number, confidence
    
    is_verified = db.Column(db.Boolean, default=False)
    verified_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    verification_notes = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    application = db.relationship('RetirementApplication', back_populates='documents')
    verified_by = db.relationship('User', foreign_keys=[verified_by_user_id])

    @property
    def display_type(self):
        return DocumentType.LABELS.get(self.document_type, self.document_type.replace('_', ' ').title())

    def __repr__(self):
        return f'<UploadedDocument {self.document_type} for App #{self.application_id}>'
