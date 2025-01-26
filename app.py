from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Competition, Round, Pairing, Score
from datetime import datetime, timedelta, date
import os
from authlib.integrations.flask_client import OAuth
from functools import wraps
from urllib.parse import urlparse
import requests
import secrets
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dance_competition.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
db.init_app(app)

# Create upload directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class EditProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    level = SelectField('Dance Level', choices=[
        ('Newcomer', 'Newcomer'),
        ('Novice', 'Novice'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('AllStar', 'All Star')
    ], validators=[DataRequired()])

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dance_role = request.form.get('dance_role')
        instagram = request.form.get('instagram')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        # Handle profile picture upload
        profile_picture = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                profile_picture = filename

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            dance_role=dance_role,
            instagram=instagram,
            profile_picture=profile_picture
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('user_dashboard'))
    
    return render_template('register.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def user_dashboard():
    # Get all available competitions
    available_competitions = Competition.query.filter(
        Competition.date >= date.today(),
        Competition.registration_open == True,
        ~Competition.users.contains(current_user)
    ).all()
    
    # Get user's registered competitions
    registered_competitions = Competition.query.filter(
        Competition.date >= date.today(),
        Competition.users.contains(current_user)
    ).order_by(Competition.date).all()
    
    return render_template('user_dashboard.html', 
                         user=current_user,
                         available_competitions=available_competitions,
                         registered_competitions=registered_competitions)

@app.route('/competitions')
def view_competitions():
    competitions = Competition.query.filter(
        Competition.registration_open == True,
        Competition.date >= date.today()
    ).order_by(Competition.date).all()
    return render_template('competitions.html', competitions=competitions)

@app.route('/competitions/<int:competition_id>/info')
@login_required
def competition_info(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    # Count leaders and followers
    leaders_count = sum(1 for user in competition.users if user.dance_role == 'leader')
    followers_count = sum(1 for user in competition.users if user.dance_role == 'follower')
    
    return render_template('competition_info.html', 
                         competition=competition,
                         leaders_count=leaders_count,
                         followers_count=followers_count,
                         current_date=date.today())

@app.route('/competitions/<int:competition_id>/join', methods=['GET', 'POST'])
@login_required
def join_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    if competition.date < date.today():
        flash('This competition has already taken place.', 'error')
        return redirect(url_for('user_dashboard'))
    
    if current_user in competition.users:
        flash('You are already registered for this competition.', 'info')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST' or request.args.get('confirm') == 'true':
        competition.users.append(current_user)
        db.session.commit()
        flash('You have successfully joined the competition!', 'success')
        return redirect(url_for('user_dashboard'))
    
    # If GET request without confirmation, show confirmation page
    return render_template('confirm_join.html', competition=competition)

@app.route('/competitions/<int:competition_id>/results')
@login_required
def view_results(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    if competition.date >= date.today():
        flash('Results are not available yet.', 'info')
        return redirect(url_for('user_dashboard'))
    
    if current_user not in competition.users:
        flash('You did not participate in this competition.', 'error')
        return redirect(url_for('user_dashboard'))
    
    return render_template('competition_results.html', competition=competition)

@app.route('/results')
@login_required
def view_results_list():
    # Get past competitions where the user participated
    past_competitions = Competition.query.filter(
        Competition.date < date.today(),
        Competition.users.contains(current_user)
    ).order_by(Competition.date.desc()).all()
    
    return render_template('results_list.html', competitions=past_competitions)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Update user fields
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.phone = request.form.get('phone')
        current_user.city = request.form.get('city')
        current_user.country = request.form.get('country')
        current_user.level = request.form.get('level')
        current_user.dance_role = request.form.get('dance_role')
        
        # Handle password change
        new_password = request.form.get('new_password')
        if new_password:
            current_user.password = generate_password_hash(new_password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=current_user)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.is_admin:
            login_user(user)
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/competitions')
@login_required
@admin_required
def admin_competitions():
    competitions = Competition.query.all()
    return render_template('admin/competitions.html', competitions=competitions)

@app.route('/admin/statistics')
@login_required
@admin_required
def admin_statistics():
    stats = {
        'total_users': User.query.count(),
        'total_competitions': Competition.query.count(),
        'upcoming_competitions': Competition.query.filter(Competition.date >= date.today()).count(),
        'past_competitions': Competition.query.filter(Competition.date < date.today()).count()
    }
    return render_template('admin/statistics.html', stats=stats)

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    return render_template('admin/reports.html')

@app.route('/admin/settings')
@login_required
@admin_required
def admin_settings():
    return render_template('admin/settings.html')

@app.route('/admin/create-competition', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_competition():
    if request.method == 'POST':
        try:
            # Handle banner upload
            banner_path = None
            if 'banner' in request.files:
                banner = request.files['banner']
                if banner and banner.filename and allowed_file(banner.filename):
                    filename = secure_filename(banner.filename)
                    if not os.path.exists(app.config['UPLOAD_FOLDER']):
                        os.makedirs(app.config['UPLOAD_FOLDER'])
                    banner_path = os.path.join('uploads', filename)
                    banner.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Create competition
            competition = Competition(
                name=request.form['name'],
                date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
                city=request.form['city'],
                dance_style=request.form['dance_style'],
                price=float(request.form['price']),
                description=request.form.get('description', ''),
                banner=banner_path,
                registration_open=True
            )
            db.session.add(competition)
            db.session.commit()
            flash('Competition created successfully!', 'success')
            return redirect(url_for('view_competitions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating competition: {str(e)}', 'error')
            return redirect(url_for('admin_create_competition'))

    return render_template('admin/create_competition.html')

@app.route('/admin/competitions/<int:competition_id>/dancers')
@login_required
@admin_required
def manage_competition_dancers(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    all_users = User.query.filter_by(role='dancer').all()
    return render_template('admin/manage_dancers.html', 
                         competition=competition, 
                         all_users=all_users)

@app.route('/admin/competitions/<int:competition_id>/dancers/add', methods=['POST'])
@login_required
@admin_required
def add_competition_dancer(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    user_id = request.form.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user and user not in competition.users:
            competition.users.append(user)
            db.session.commit()
            flash(f'Added {user.first_name} {user.last_name} to {competition.name}', 'success')
    return redirect(url_for('manage_competition_dancers', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/dancers/remove/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def remove_competition_dancer(competition_id, user_id):
    competition = Competition.query.get_or_404(competition_id)
    user = User.query.get_or_404(user_id)
    if user in competition.users:
        competition.users.remove(user)
        db.session.commit()
        flash(f'Removed {user.first_name} {user.last_name} from {competition.name}', 'success')
    return redirect(url_for('manage_competition_dancers', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/judges')
@login_required
@admin_required
def manage_competition_judges(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    all_users = User.query.filter_by(role='judge').all()
    return render_template('admin/manage_judges.html', 
                         competition=competition, 
                         all_users=all_users)

@app.route('/admin/competitions/<int:competition_id>/judges/add', methods=['POST'])
@login_required
@admin_required
def add_competition_judge(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    user_id = request.form.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user and user not in competition.users:
            competition.users.append(user)
            db.session.commit()
            flash(f'Added judge {user.first_name} {user.last_name} to {competition.name}', 'success')
    return redirect(url_for('manage_competition_judges', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/judges/remove/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def remove_competition_judge(competition_id, user_id):
    competition = Competition.query.get_or_404(competition_id)
    user = User.query.get_or_404(user_id)
    if user in competition.users:
        competition.users.remove(user)
        db.session.commit()
        flash(f'Removed judge {user.first_name} {user.last_name} from {competition.name}', 'success')
    return redirect(url_for('manage_competition_judges', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/toggle', methods=['POST'])
@login_required
@admin_required
def admin_toggle_registration(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    competition.registration_open = not competition.registration_open
    db.session.commit()
    status = "opened" if competition.registration_open else "closed"
    flash(f'Registration for {competition.name} has been {status}', 'success')
    return redirect(url_for('admin_competitions'))

@app.route('/admin/competitions/<int:competition_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    if request.method == 'POST':
        try:
            # Handle banner upload
            if 'banner' in request.files:
                banner = request.files['banner']
                if banner and banner.filename and allowed_file(banner.filename):
                    filename = secure_filename(banner.filename)
                    if not os.path.exists(app.config['UPLOAD_FOLDER']):
                        os.makedirs(app.config['UPLOAD_FOLDER'])
                    banner_path = os.path.join('uploads', filename)
                    banner.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    competition.banner = banner_path

            # Update competition details
            competition.name = request.form['name']
            competition.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            competition.city = request.form['city']
            competition.dance_style = request.form['dance_style']
            competition.price = float(request.form['price'])
            competition.description = request.form.get('description', '')
            
            db.session.commit()
            flash('Competition updated successfully!', 'success')
            return redirect(url_for('admin_competitions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating competition: {str(e)}', 'error')
            return redirect(url_for('admin_edit_competition', competition_id=competition_id))

    return render_template('admin/edit_competition.html', competition=competition)

@app.route('/invite_tester', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_tester():
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            # Generate a unique token
            token = secrets.token_urlsafe(32)
            
            # Store the token in the database or cache
            # For now, we'll just print it
            invite_link = url_for('register', token=token, _external=True)
            print(f"Invite link for {email}: {invite_link}")
            
            flash(f'Invitation sent to {email}', 'success')
            return redirect(url_for('admin_dashboard'))
            
    return render_template('admin/invite_tester.html')

@app.context_processor
def utility_processor():
    return {
        'current_date': date.today()
    }

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(email='admin@dancecomp.com').first()
        if not admin:
            admin = User(
                email='admin@dancecomp.com',
                first_name='Admin',
                last_name='User',
                dance_role='leader',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Admin user created successfully!')
        
    app.run(debug=True)
