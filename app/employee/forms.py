from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SelectField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from app.models.document import DocumentType

RETIREMENT_REASONS = [
    ('Statutory Age (Attainment of 60 Years)', 'Statutory Age (Attainment of 60 Years)'),
    ('Statutory Years of Service (Attainment of 35 Years)', 'Statutory Years of Service (Attainment of 35 Years)'),
    ('Voluntary Retirement', 'Voluntary Retirement'),
    ('Medical Grounds / Incapacitation', 'Medical Grounds / Incapacitation')
]

class RetirementApplicationForm(FlaskForm):
    reason_for_retirement = SelectField('Primary Reason for Retirement', choices=RETIREMENT_REASONS, validators=[DataRequired()])
    proposed_retirement_date = DateField('Proposed Effective Retirement Date', format='%Y-%m-%d', validators=[DataRequired()])
    additional_notes = TextAreaField('Additional Remarks / Forwarding Notes')
    submit = SubmitField('Submit Retirement Application')

class DocumentUploadForm(FlaskForm):
    document_type = SelectField('Select Document Type', choices=[
        (DocumentType.APPOINTMENT_LETTER, DocumentType.LABELS[DocumentType.APPOINTMENT_LETTER]),
        (DocumentType.PROMOTION_LETTER, DocumentType.LABELS[DocumentType.PROMOTION_LETTER]),
        (DocumentType.BIRTH_CERTIFICATE, DocumentType.LABELS[DocumentType.BIRTH_CERTIFICATE]),
        (DocumentType.STAFF_ID_CARD, DocumentType.LABELS[DocumentType.STAFF_ID_CARD]),
        (DocumentType.PENSION_RECORD, DocumentType.LABELS[DocumentType.PENSION_RECORD]),
        (DocumentType.PASSPORT_PHOTO, DocumentType.LABELS[DocumentType.PASSPORT_PHOTO])
    ], validators=[DataRequired()])
    
    file = FileField('Upload Document (PDF, JPEG, PNG)', validators=[
        FileRequired(message="Please choose a file to upload."),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], message="Only PDF, JPG, and PNG documents are supported.")
    ])
    submit = SubmitField('Upload and Process Document')
