from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Dancer, Competition, Round, Pairing, Score
from datetime import datetime, timedelta
import secrets
from functools import wraps
import logging
from authlib.integrations.flask_client import OAuth
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Configure database
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
elif not database_url:
    database_url = 'sqlite:///dance.db'
    app.logger.warning('No DATABASE_URL found, using SQLite database')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)

# Create tables if they don't exist
with app.app_context():
    try:
        db.create_all()
        app.logger.info('Database tables created successfully')
    except Exception as e:
        app.logger.error(f'Error creating database tables: {str(e)}')

# Email configuration (optional)
mail = None
Message = None  # Define Message as None by default
if os.getenv('MAIL_SERVER'):
    try:
        from flask_mail import Mail, Message
        app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
        app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
        app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
        app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
        app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
        mail = Mail(app)
        app.logger.info('Email configuration loaded successfully')
    except ImportError:
        app.logger.warning('Flask-Mail not installed. Email features will be disabled.')
    except Exception as e:
        app.logger.error(f'Error loading email configuration: {str(e)}')
        app.logger.warning('Email features will be disabled.')
else:
    app.logger.warning('Email configuration not found. Email features will be disabled.')

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Set up logging
if os.getenv('FLASK_ENV') == 'production':
    app.logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)

# OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You must be an admin to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class TestInvitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    used = db.Column(db.Boolean, default=False)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        app.logger.info(f"Admin login attempt for email: {email}")
        
        user = User.query.filter_by(email=email).first()
        app.logger.info(f"Found user: {user}")
        
        if user and user.role == 'admin' and check_password_hash(user.password, password):
            login_user(user)
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')
            if user:
                app.logger.info(f"Login failed - Role: {user.role}")
            else:
                app.logger.info("Login failed - User not found")
    
    return render_template('admin/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/dancers')
@login_required
@admin_required
def list_dancers():
    dancers = Dancer.query.all()
    return render_template('admin/list_dancers.html', dancers=dancers)

@app.route('/admin/dancers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_dancer():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone')
            date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            level = request.form.get('level')
            
            app.logger.info(f"Adding dancer with email: {email}")
            app.logger.info(f"Form data - First Name: {first_name}, Last Name: {last_name}, Level: {level}")
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('add_dancer'))
            
            # Create user first
            user = User(
                username=email.split('@')[0],
                email=email,
                password=generate_password_hash(password),
                role='dancer',
                is_active=True
            )
            db.session.add(user)
            db.session.flush()  # Get user.id
            
            # Create dancer profile
            dancer = Dancer(
                user_id=user.id,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                date_of_birth=date_of_birth,
                level=level
            )
            db.session.add(dancer)
            db.session.commit()
            
            app.logger.info(f"Successfully added dancer: {first_name} {last_name}")
            flash('Dancer added successfully!', 'success')
            return redirect(url_for('list_dancers'))
            
        except ValueError as e:
            db.session.rollback()
            error_msg = "Invalid date format. Please use YYYY-MM-DD."
            app.logger.error(f"Date parsing error: {str(e)}")
            flash(error_msg, 'danger')
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error adding dancer: {str(e)}"
            app.logger.error(error_msg)
            flash('Error adding dancer. Please try again.', 'danger')
    
    return render_template('admin/add_dancer.html')

@app.route('/admin/dancers/edit/<int:dancer_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_dancer(dancer_id):
    dancer = Dancer.query.get_or_404(dancer_id)
    
    if request.method == 'POST':
        dancer.first_name = request.form.get('first_name')
        dancer.last_name = request.form.get('last_name')
        dancer.phone = request.form.get('phone')
        dancer.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
        dancer.user.email = request.form.get('email')

        try:
            db.session.commit()
            flash('Dancer updated successfully', 'success')
            return redirect(url_for('list_dancers'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating dancer', 'danger')
            app.logger.error(f'Error updating dancer: {str(e)}')
    
    return render_template('admin/edit_dancer.html', dancer=dancer)

@app.route('/admin/dancers/delete/<int:dancer_id>', methods=['POST'])
@login_required
@admin_required
def delete_dancer(dancer_id):
    dancer = Dancer.query.get_or_404(dancer_id)
    user = dancer.user

    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('list_dancers'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash('Dancer has been successfully deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting dancer: {str(e)}')
        flash('An error occurred while deleting the dancer.', 'danger')
    
    return redirect(url_for('list_dancers'))

@app.route('/admin/dancers/promote/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def promote_to_judge(user_id):
    user = User.query.get_or_404(user_id)
    dancer = Dancer.query.filter_by(user_id=user_id).first()
    
    if not dancer:
        flash('Dancer not found.', 'danger')
        return redirect(url_for('list_dancers'))
    
    try:
        # Change user role to judge
        user.role = 'judge'
        db.session.commit()
        flash(f'Successfully promoted {user.email} to judge!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error promoting dancer to judge. Please try again.', 'danger')
        app.logger.error(f'Error promoting to judge: {str(e)}')
    
    return redirect(url_for('list_dancers'))

@app.route('/admin/competitions')
@login_required
@admin_required
def list_competitions():
    competitions = Competition.query.all()
    return render_template('admin/list_competitions.html', competitions=competitions)

@app.route('/admin/competitions/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_competition():
    if request.method == 'POST':
        name = request.form.get('name')
        date_str = request.form.get('date')
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            competition = Competition(name=name, date=date)
            db.session.add(competition)
            db.session.commit()
            flash('Competition added successfully', 'success')
            return redirect(url_for('list_competitions'))
        except ValueError:
            flash('Invalid date format', 'danger')
    
    return render_template('admin/add_competition.html')

@app.route('/admin/competitions/<int:competition_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    if request.method == 'POST':
        try:
            competition.name = request.form.get('name')
            competition.date = datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M')
            competition.status = request.form.get('status')
            competition.registration_open = 'registration_open' in request.form
            
            db.session.commit()
            flash('Competition updated successfully!', 'success')
            return redirect(url_for('list_competitions'))
            
        except ValueError as e:
            flash('Invalid date format. Please use the date picker.', 'danger')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error updating competition: {str(e)}')
            flash('Error updating competition. Please try again.', 'danger')
    
    return render_template('admin/edit_competition.html', competition=competition)

@app.route('/admin/competitions/<int:competition_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    try:
        db.session.delete(competition)
        db.session.commit()
        flash('Competition deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting competition', 'danger')
        app.logger.error(f'Error deleting competition: {str(e)}')
    
    return redirect(url_for('list_competitions'))

@app.route('/admin/competitions/<int:competition_id>/registration', methods=['POST'])
@login_required
@admin_required
def toggle_registration(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    competition.registration_open = not competition.registration_open
    db.session.commit()
    flash(f'Registration {"opened" if competition.registration_open else "closed"} successfully', 'success')
    return redirect(url_for('list_competitions'))

@app.route('/admin/competitions/<int:competition_id>/dancers', methods=['GET'])
@login_required
@admin_required
def manage_competition_dancers(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    # Get all dancers not in this competition
    available_dancers = Dancer.query.filter(~Dancer.competitions.contains(competition)).all()
    return render_template('admin/competition_dancers.html', 
                         competition=competition,
                         available_dancers=available_dancers)

@app.route('/admin/competitions/<int:competition_id>/judges', methods=['GET'])
@login_required
@admin_required
def manage_competition_judges(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    judges = User.query.filter_by(role='judge').all()
    return render_template('admin/competition_judges.html', 
                         competition=competition,
                         judges=judges)

@app.route('/admin/competitions/<int:competition_id>/dancers/<int:dancer_id>', methods=['POST'])
@login_required
@admin_required
def assign_dancer(competition_id, dancer_id):
    competition = Competition.query.get_or_404(competition_id)
    dancer = Dancer.query.get_or_404(dancer_id)
    
    if dancer in competition.dancers:
        competition.dancers.remove(dancer)
        flash(f'Dancer {dancer.first_name} {dancer.last_name} removed from competition', 'success')
    else:
        competition.dancers.append(dancer)
        flash(f'Dancer {dancer.first_name} {dancer.last_name} added to competition', 'success')
    
    db.session.commit()
    return redirect(url_for('manage_competition_dancers', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/judges/<int:judge_id>', methods=['POST'])
@login_required
@admin_required
def assign_judge(competition_id, judge_id):
    competition = Competition.query.get_or_404(competition_id)
    judge = User.query.get_or_404(judge_id)
    
    if judge in competition.judges:
        competition.judges.remove(judge)
        flash(f'Judge removed from competition', 'success')
    else:
        competition.judges.append(judge)
        flash(f'Judge added to competition', 'success')
    
    db.session.commit()
    return redirect(url_for('manage_competition_judges', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/dancers/<int:dancer_id>/remove', methods=['POST'])
@login_required
@admin_required
def remove_dancer_from_competition(competition_id, dancer_id):
    competition = Competition.query.get_or_404(competition_id)
    dancer = Dancer.query.get_or_404(dancer_id)
    
    if dancer in competition.dancers:
        try:
            competition.dancers.remove(dancer)
            db.session.commit()
            flash(f'Successfully removed {dancer.first_name} {dancer.last_name} from {competition.name}', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error removing dancer from competition: {str(e)}')
            flash('Error removing dancer from competition. Please try again.', 'danger')
    else:
        flash('Dancer is not registered for this competition.', 'warning')
    
    return redirect(url_for('manage_competition_dancers', competition_id=competition_id))

@app.route('/admin/judges')
@login_required
@admin_required
def manage_judges():
    judges = User.query.filter_by(role='judge').all()
    return render_template('admin/manage_judges.html', judges=judges)

@app.route('/admin/users')
@login_required
@admin_required
def list_users():
    users = User.query.all()
    return render_template('admin/list_users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('add_user'))
        
        user = User(
            username=email.split('@')[0],
            email=email,
            password=generate_password_hash(password),
            role=role,
            is_active=True
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('User added successfully!', 'success')
            return redirect(url_for('list_users'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding user. Please try again.', 'danger')
            app.logger.error(f'Error adding user: {str(e)}')
    
    return render_template('admin/add_user.html')

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        
        # Check if email is taken by another user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user_id:
            flash('Email already taken by another user', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))
        
        user.email = email
        user.username = email.split('@')[0]
        user.role = role
        if password:  # Only update password if provided
            user.password = generate_password_hash(password)
        
        try:
            db.session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('list_users'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating user. Please try again.', 'danger')
            app.logger.error(f'Error updating user: {str(e)}')
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('list_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting user. Please try again.', 'danger')
        app.logger.error(f'Error deleting user: {str(e)}')
    
    return redirect(url_for('list_users'))

@app.route('/admin/users/reset-password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    
    # Generate a random temporary password
    temp_password = secrets.token_urlsafe(8)  # 8 characters long
    user.password = generate_password_hash(temp_password)
    
    try:
        db.session.commit()
        flash(f'Password reset successfully! Temporary password: {temp_password}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error resetting password. Please try again.', 'danger')
        app.logger.error(f'Error resetting password: {str(e)}')
    
    return redirect(url_for('edit_user', user_id=user_id))

@app.route('/competitions')
@login_required
def view_competitions():
    competitions = Competition.query.all()
    return render_template('competitions.html', competitions=competitions)

@app.route('/results')
@login_required
def view_results_list():
    competitions = Competition.query.filter_by(status='completed').all()
    return render_template('results_list.html', competitions=competitions)

@app.route('/register', methods=['GET'])
def register():
    token = request.args.get('token')
    if token:
        invitation = TestInvitation.query.filter_by(token=token, used=False).first()
        if invitation and invitation.expires_at > datetime.utcnow():
            return render_template('register.html', email=invitation.email, token=token)
    return render_template('register.html')

@app.route('/login/google')
def google_login():
    app.logger.info('Starting Google OAuth login process')
    try:
        redirect_uri = url_for('google_authorize', _external=True)
        app.logger.info(f'Redirect URI: {redirect_uri}')
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        app.logger.error(f'Error in google_login: {str(e)}')
        flash('Error connecting to Google. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/login/google/authorize')
def google_authorize():
    app.logger.info('Received Google OAuth callback')
    try:
        token = google.authorize_access_token()
        app.logger.info('Successfully obtained access token')
        resp = google.get('userinfo')
        user_info = resp.json()
        app.logger.info(f'Got user info: {user_info.get("email")}')
        
        # Check if user exists
        user = User.query.filter_by(email=user_info['email']).first()
        
        if not user:
            app.logger.info(f'Creating new user for {user_info.get("email")}')
            # Create new user
            user = User(
                email=user_info['email'],
                username=user_info.get('name', '').split('@')[0],
                password='',  # No password for Google users
                role='user'
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        app.logger.info(f'Successfully logged in user {user.email}')
        flash('Successfully logged in with Google!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f'Error in google_authorize: {str(e)}')
        flash('Error during Google login. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/admin/competitions/<int:competition_id>/rounds')
@login_required
@admin_required
def manage_competition_rounds(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    return render_template('admin/competition_rounds.html', competition=competition)

@app.route('/admin/competitions/<int:competition_id>/rounds/add', methods=['POST'])
@login_required
@admin_required
def add_round(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    try:
        round_type = request.form.get('round_type')
        status = request.form.get('status')
        
        new_round = Round(
            competition_id=competition.id,
            round_type=round_type,
            status=status
        )
        db.session.add(new_round)
        db.session.commit()
        
        flash('Round added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error adding round: {str(e)}')
        flash('Error adding round. Please try again.', 'danger')
    
    return redirect(url_for('manage_competition_rounds', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/rounds/<int:round_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_round(competition_id, round_id):
    round = Round.query.get_or_404(round_id)
    
    try:
        round.round_type = request.form.get('round_type')
        round.status = request.form.get('status')
        db.session.commit()
        flash('Round updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error updating round: {str(e)}')
        flash('Error updating round. Please try again.', 'danger')
    
    return redirect(url_for('manage_competition_rounds', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/rounds/<int:round_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_round(competition_id, round_id):
    round = Round.query.get_or_404(round_id)
    
    try:
        db.session.delete(round)
        db.session.commit()
        flash('Round deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting round: {str(e)}')
        flash('Error deleting round. Please try again.', 'danger')
    
    return redirect(url_for('manage_competition_rounds', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/rounds/<int:round_id>/pairings')
@login_required
@admin_required
def manage_round_pairings(competition_id, round_id):
    competition = Competition.query.get_or_404(competition_id)
    round = Round.query.get_or_404(round_id)
    return render_template('admin/round_pairings.html', competition=competition, round=round)

@app.route('/admin/invite-tester', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_tester():
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            # Generate unique token
            token = secrets.token_urlsafe(32)
            
            # Create invitation
            invitation = TestInvitation(
                email=email,
                token=token,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(invitation)
            
            # Send invitation email if mail is configured
            if mail and Message:
                try:
                    invite_url = url_for('register', token=token, _external=True)
                    msg = Message(
                        'Dance Competition System - Test Invitation',
                        sender=app.config['MAIL_USERNAME'],
                        recipients=[email]
                    )
                    msg.body = f'''You have been invited to test the Dance Competition System!
                    
    Please click the following link to register:
    {invite_url}

    This invitation will expire in 7 days.'''
                    
                    mail.send(msg)
                    app.logger.info(f'Invitation email sent to {email}')
                except Exception as e:
                    app.logger.error(f'Failed to send invitation email: {str(e)}')
                    flash('Failed to send invitation email, but invitation was created', 'warning')
            else:
                app.logger.warning('Email not configured. Skipping invitation email.')
                flash('Invitation created, but email could not be sent (email not configured)', 'warning')
            
            db.session.commit()
            flash(f'Invitation created for {email}', 'success')
            return redirect(url_for('admin_dashboard'))
            
    return render_template('admin/invite_tester.html')

if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)
    app.run(debug=True)
