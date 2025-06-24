from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TimeField, IntegerField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, NumberRange
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('student', 'Student'), ('teacher', 'Teacher')], validators=[DataRequired()])
    
    # Optional personal information fields
    date_of_birth = DateField('Date of Birth', validators=[Optional()], format='%Y-%m-%d')
    gender = SelectField('Gender', choices=[('', 'Not Set'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[Optional()])
    program = SelectField('Program', choices=[('', 'Not Set'), ('3 months', '3 months'), ('6 months', '6 months'), ('1 year', '1 year')], validators=[Optional()])
    plan = SelectField('Plan', choices=[('', 'Not Set'), ('1/week', '1/week'), ('2/week', '2/week')], validators=[Optional()])
    effective_from = DateField('Effective From', validators=[Optional()], format='%Y-%m-%d')
    effective_to = DateField('Effective To', validators=[Optional()], format='%Y-%m-%d')
    classes = SelectField('Classes', choices=[('', 'Not Set'), ('48', '48'), ('96', '96')], validators=[Optional()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class AddStudentForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    
    # Optional personal information fields
    date_of_birth = DateField('Date of Birth', validators=[Optional()], format='%Y-%m-%d')
    gender = SelectField('Gender', choices=[('', 'Not Set'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[Optional()])
    program = SelectField('Program', choices=[('', 'Not Set'), ('3 months', '3 months'), ('6 months', '6 months'), ('1 year', '1 year')], validators=[Optional()])
    plan = SelectField('Plan', choices=[('', 'Not Set'), ('1/week', '1/week'), ('2/week', '2/week')], validators=[Optional()])
    effective_from = DateField('Effective From', validators=[Optional()], format='%Y-%m-%d')
    effective_to = DateField('Effective To', validators=[Optional()], format='%Y-%m-%d')
    classes = SelectField('Classes', choices=[('', 'Not Set'), ('48', '48'), ('96', '96')], validators=[Optional()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    
    submit = SubmitField('Add Student')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ClassForm(FlaskForm):
    name = StringField('Class Name', validators=[DataRequired(), Length(max=100)])
    day_of_week = SelectField('Day of Week', choices=[
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), 
        (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ], coerce=int, validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()], format='%H:%M')
    end_time = TimeField('End Time', validators=[DataRequired()], format='%H:%M')
    min_belt_level = SelectField('Minimum Belt Level', choices=[
        ('', 'All levels'), ('No Belt', 'No Belt'), ('White', 'White'), ('Yellow', 'Yellow'), 
        ('Green', 'Green'), ('Purple', 'Purple'), ('Purple-Blue', 'Purple-Blue'), ('Blue', 'Blue'), 
        ('Blue-Brown', 'Blue-Brown'), ('Brown', 'Brown'), ('Brown-Red', 'Brown-Red'), 
        ('Red', 'Red'), ('Red-Black', 'Red-Black'), ('Black', 'Black')
    ], validators=[Optional()])
    max_belt_level = SelectField('Maximum Belt Level', choices=[
        ('', 'All levels'), ('No Belt', 'No Belt'), ('White', 'White'), ('Yellow', 'Yellow'), 
        ('Green', 'Green'), ('Purple', 'Purple'), ('Purple-Blue', 'Purple-Blue'), ('Blue', 'Blue'), 
        ('Blue-Brown', 'Blue-Brown'), ('Brown', 'Brown'), ('Brown-Red', 'Brown-Red'), 
        ('Red', 'Red'), ('Red-Black', 'Red-Black'), ('Black', 'Black')
    ], validators=[Optional()])
    max_capacity = IntegerField('Maximum Capacity', validators=[Optional(), NumberRange(min=1)], description='Leave empty for unlimited')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Class')

    def validate_end_time(self, end_time):
        if self.start_time.data and end_time.data:
            if end_time.data <= self.start_time.data:
                raise ValidationError('End time must be after start time.')

class ClassEnrollmentForm(FlaskForm):
    class_id = SelectField('Class', coerce=int, validators=[DataRequired()])
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    enrolled_from = DateField('Enrolled From', validators=[DataRequired()], format='%Y-%m-%d')
    enrolled_until = DateField('Enrolled Until', validators=[Optional()], format='%Y-%m-%d', description='Leave empty for ongoing enrollment')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Enrollment')

class ClassHolidayForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    description = StringField('Description', validators=[Optional(), Length(max=200)])
    is_recurring = BooleanField('Recurring Holiday', default=False, description='Check if this holiday repeats annually')
    submit = SubmitField('Save Holiday') 