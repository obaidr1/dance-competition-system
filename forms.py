from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, FloatField, DateField, FileField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional, Length
from models import User
from datetime import date

class EditProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone')
    city = StringField('City')
    dance_role = SelectField('Dance Role', choices=[('leader', 'Leader'), ('follower', 'Follower')])
    level = SelectField('Level', choices=[('novice', 'Novice'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')])
    role = SelectField('User Role', choices=[('dancer', 'Dancer'), ('judge', 'Judge'), ('admin', 'Admin')])
    instagram = StringField('Instagram')
    profile_picture = FileField('Profile Picture')
    new_password = PasswordField('New Password')
    submit = SubmitField('Save Changes')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    dance_role = SelectField('Dance Role', 
                           choices=[('leader', 'Leader'), ('follower', 'Follower')],
                           validators=[DataRequired()])
    level = SelectField('Dance Level',
                       choices=[('novice', 'Novice'),
                               ('intermediate', 'Intermediate'),
                               ('advanced', 'Advanced')],
                       validators=[DataRequired()])
    city = StringField('City')
    user_role = SelectField('Account Type',
                          choices=[('dancer', 'Dancer'),
                                  ('organizer', 'Competition Organizer'),
                                  ('judge', 'Judge')],
                          validators=[DataRequired()])
    
    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if user is not None:
            raise ValidationError('Email already registered.')

class CreateCompetitionForm(FlaskForm):
    name = StringField('Competition Name', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    level = SelectField('Level', choices=[
        ('Novice', 'Novice'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced')
    ], validators=[DataRequired()])
    price = FloatField('Entry Price', validators=[DataRequired()])
    description = TextAreaField('Description')
    banner = FileField('Banner Image')
    music_genre = SelectField('Music Genre', choices=[
        ('modern', 'Modern Bachata'),
        ('traditional', 'Traditional Bachata'),
        ('both', 'Both')
    ], validators=[DataRequired()])
    max_participants = StringField('Max Participants (optional)', validators=[Optional()])
    submit = SubmitField('Create Competition')

class JudgeAssignmentForm(FlaskForm):
    judges = SelectField('Select Judge', validators=[DataRequired()])
    is_head_judge = BooleanField('Assign as Head Judge')
    submit = SubmitField('Add Judge')

class StartRoundForm(FlaskForm):
    round_number = SelectField('Round', choices=[
        (1, 'Preliminaries'),
        (2, 'Quarter-Finals'),
        (3, 'Semi-Finals'),
        (4, 'Finals')
    ], validators=[DataRequired()])
    submit = SubmitField('Start Round')

class AddDancerForm(FlaskForm):
    dancer_id = SelectField('Select Dancer', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Add Dancer')

class AddAudienceMemberForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    dance_role = SelectField('Role Needed', choices=[
        ('leader', 'Leader'),
        ('follower', 'Follower')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Member')

class CompetitionForm(FlaskForm):
    name = StringField('Competition Name', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    level = SelectField('Level',
                       choices=[('novice', 'Novice'),
                               ('intermediate', 'Intermediate'),
                               ('advanced', 'Advanced'),
                               ('allstar', 'All Star')],
                       validators=[DataRequired()])
    max_participants = IntegerField('Max Participants', validators=[Optional()])
    
    def validate_date(self, field):
        if field.data < date.today():
            raise ValidationError('You cannot create a competition in the past.')
