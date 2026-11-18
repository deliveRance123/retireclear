from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, DateField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp

NIGERIAN_STATES = [
    ('Abia', 'Abia'), ('Adamawa', 'Adamawa'), ('Akwa Ibom', 'Akwa Ibom'), ('Anambra', 'Anambra'),
    ('Bauchi', 'Bauchi'), ('Bayelsa', 'Bayelsa'), ('Benue', 'Benue'), ('Borno', 'Borno'),
    ('Cross River', 'Cross River'), ('Delta', 'Delta'), ('Ebonyi', 'Ebonyi'), ('Edo', 'Edo'),
    ('Ekiti', 'Ekiti'), ('Enugu', 'Enugu'), ('FCT', 'Federal Capital Territory (Abuja)'),
    ('Gombe', 'Gombe'), ('Imo', 'Imo'), ('Jigawa', 'Jigawa'), ('Kaduna', 'Kaduna'),
    ('Kano', 'Kano'), ('Katsina', 'Katsina'), ('Kebbi', 'Kebbi'), ('Kogi', 'Kogi'),
    ('Kwara', 'Kwara'), ('Lagos', 'Lagos'), ('Nasarawa', 'Nasarawa'), ('Niger', 'Niger'),
    ('Ogun', 'Ogun'), ('Ondo', 'Ondo'), ('Osun', 'Osun'), ('Oyo', 'Oyo'),
    ('Plateau', 'Plateau'), ('Rivers', 'Rivers'), ('Sokoto', 'Sokoto'), ('Taraba', 'Taraba'),
    ('Yobe', 'Yobe'), ('Zamfara', 'Zamfara')
]

MINISTRIES = [
    ('Federal Ministry of Education', 'Federal Ministry of Education'),
    ('Federal Ministry of Health and Social Welfare', 'Federal Ministry of Health and Social Welfare'),
    ('Federal Ministry of Finance', 'Federal Ministry of Finance'),
    ('Federal Ministry of Works', 'Federal Ministry of Works'),
    ('Federal Ministry of Agriculture and Food Security', 'Federal Ministry of Agriculture and Food Security'),
    ('Federal Ministry of Justice', 'Federal Ministry of Justice'),
    ('Office of the Head of the Civil Service of the Federation', 'Office of the Head of the Civil Service of the Federation'),
    ('Federal Civil Service Commission', 'Federal Civil Service Commission'),
    ('National Pension Commission (PenCom)', 'National Pension Commission (PenCom)'),
    ('Federal Ministry of Industry, Trade and Investment', 'Federal Ministry of Industry, Trade and Investment')
]

GRADE_LEVELS = [(f'GL {i:02d}', f'Grade Level {i:02d}') for i in range(1, 18)]

class EmployeeRegistrationForm(FlaskForm):
    staff_number = StringField(
        'Staff Number (e.g. FGN/EDU/2018/00125)',
        validators=[DataRequired(), Length(min=5, max=50)]
    )
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=80)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(max=80)])
    last_name = StringField('Surname / Last Name', validators=[DataRequired(), Length(max=80)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    
    state_of_origin = SelectField('State of Origin', choices=NIGERIAN_STATES, validators=[DataRequired()])
    lga = StringField('Local Government Area (LGA)', validators=[Optional(), Length(max=80)])
    residential_address = TextAreaField('Residential Address', validators=[DataRequired()])
    city = StringField('City / Town (e.g. Abuja, Lagos, Ibadan, Kaduna)', validators=[DataRequired(), Length(max=80)])
    state_of_residence = SelectField('State of Residence', choices=NIGERIAN_STATES, validators=[DataRequired()])
    
    phone_number = StringField(
        'Phone Number (e.g. +2348012345678 or 08012345678)',
        validators=[
            DataRequired(),
            Regexp(r'^(?:\+234|0)[789][01]\d{8}$', message="Please enter a valid Nigerian mobile phone number (e.g. +2348012345678 or 08012345678).")
        ]
    )
    email = StringField('Official Email Address', validators=[DataRequired(), Email()])
    nin = StringField('National Identity Number (NIN)', validators=[Optional(), Length(min=11, max=11, message="NIN must be an 11-digit number.")])
    bvn = StringField('Bank Verification Number (BVN)', validators=[Optional(), Length(min=11, max=11, message="BVN must be an 11-digit number.")])
    
    ministry_or_agency = SelectField('Ministry / Agency', choices=MINISTRIES, validators=[DataRequired()])
    department = StringField('Department / Directorate', validators=[DataRequired(), Length(max=120)])
    current_cadre = StringField('Cadre / Rank (e.g. Administrative Officer, Chief Accountant)', validators=[DataRequired(), Length(max=100)])
    current_grade_level = SelectField('Current Grade Level', choices=GRADE_LEVELS, validators=[DataRequired()])
    current_step = IntegerField('Current Step (1 - 15)', default=1, validators=[DataRequired()])
    
    appointment_date = DateField('Date of First Appointment', format='%Y-%m-%d', validators=[DataRequired()])
    confirmation_date = DateField('Date of Confirmation of Appointment', format='%Y-%m-%d', validators=[Optional()])
    statutory_retirement_date = DateField('Statutory Retirement Date', format='%Y-%m-%d', validators=[DataRequired()])
    
    passport_photo = FileField('Passport Photograph (JPEG, PNG)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG and PNG image files are allowed.')
    ])
    
    submit = SubmitField('Register Public Servant')

class PromotionRecordForm(FlaskForm):
    from_grade_level = SelectField('From Grade Level', choices=GRADE_LEVELS, validators=[DataRequired()])
    to_grade_level = SelectField('To Grade Level', choices=GRADE_LEVELS, validators=[DataRequired()])
    effective_date = DateField('Effective Promotion Date', format='%Y-%m-%d', validators=[DataRequired()])
    gazette_or_ref_number = StringField('Gazette or Commission Reference Letter No.', validators=[Optional(), Length(max=120)])
    submit = SubmitField('Record Promotion')

class PensionRecordForm(FlaskForm):
    pfa_name = SelectField('Pension Fund Administrator (PFA)', choices=[
        ('Stanbic IBTC Pension Managers', 'Stanbic IBTC Pension Managers'),
        ('ARM Pension Managers', 'ARM Pension Managers'),
        ('Leadway Pensure PFA', 'Leadway Pensure PFA'),
        ('Premium Pension Limited', 'Premium Pension Limited'),
        ('Trustfund Pensions Plc', 'Trustfund Pensions Plc'),
        ('FCMB Pensions Limited', 'FCMB Pensions Limited'),
        ('Veritas Glanvills Pensions', 'Veritas Glanvills Pensions'),
        ('Nigeria Police Force Pensions', 'NPF Pensions Limited'),
        ('Other Licensed PFA', 'Other Licensed PFA')
    ], validators=[DataRequired()])
    rsa_pin = StringField('Retirement Savings Account (RSA) PIN (e.g. PEN10023458912)', validators=[DataRequired(), Length(min=10, max=50)])
    total_contributions_estimate = StringField('Estimated Total RSA Balance / Contributions (₦)', validators=[Optional()])
    submit = SubmitField('Save Pension Record')
