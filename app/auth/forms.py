from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class LoginForm(FlaskForm):
    username_or_email = StringField(
        'Staff Number, Username or Official Email',
        validators=[DataRequired(message="Please enter your username, staff number, or email."), Length(min=3, max=120)]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message="Please provide your account password.")]
    )
    remember_me = BooleanField('Remember this secure session')
    submit = SubmitField('Sign In to Portal')

class PasswordResetRequestForm(FlaskForm):
    email = StringField(
        'Registered Official Email',
        validators=[DataRequired(), Email(message="Please enter a valid official email address.")]
    )
    submit = SubmitField('Send Password Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        'New Password',
        validators=[DataRequired(), Length(min=8, message="Password must be at least 8 characters.")]
    )
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('password', message="Passwords must match exactly.")]
    )
    submit = SubmitField('Update Password')

class RegistrationForm(FlaskForm):
    staff_number = StringField(
        'Staff Identification Number',
        validators=[DataRequired(message="Staff ID is required (e.g. FGN/2026/001)."), Length(min=4, max=50)]
    )
    first_name = StringField(
        'First Name',
        validators=[DataRequired(), Length(min=2, max=60)]
    )
    last_name = StringField(
        'Last / Surname',
        validators=[DataRequired(), Length(min=2, max=60)]
    )
    email = StringField(
        'Official or Personal Email',
        validators=[DataRequired(), Email(message="Please provide a valid email address."), Length(max=120)]
    )
    phone_number = StringField(
        'Mobile Phone Number (+234)',
        validators=[DataRequired(), Length(min=10, max=20)]
    )
    ministry_or_agency = StringField(
        'Ministry, Department or Agency (MDA)',
        validators=[DataRequired(), Length(min=3, max=150)]
    )
    password = PasswordField(
        'Create Password',
        validators=[DataRequired(), Length(min=8, message="Password must contain at least 8 characters.")]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message="Passwords do not match.")]
    )
    submit = SubmitField('Complete Registration & Create Account')


class ProfileEditForm(FlaskForm):
    first_name = StringField(
        'First Name',
        validators=[DataRequired(), Length(min=2, max=80)]
    )
    last_name = StringField(
        'Last / Surname',
        validators=[DataRequired(), Length(min=2, max=80)]
    )
    phone = StringField(
        'Phone Number',
        validators=[Optional(), Length(max=25)]
    )
    avatar = FileField(
        'Profile Picture',
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Only image files (JPG, PNG, WEBP) are supported.')]
    )
    submit = SubmitField('Save Profile Changes')
