from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date, time, timedelta
from flask_migrate import Migrate
from forms import RegistrationForm
from models import User, Competition, CompetitionJudge, CompetitionParticipant
from extensions import db, login_manager
import os
import secrets
import json
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/djobi_devstation/CascadeProjects/dance-competition-system/dance_competition.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)

# Initialize migrations
migrate = Migrate(app, db)

@app.context_processor
def inject_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return dict(csrf_token=session['csrf_token'])

@app.template_filter('contains')
def contains_filter(seq, item):
    if seq is None:
        return False
    return item in seq

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not (current_user.is_admin or current_user.is_organizer):
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.dance_role = form.dance_role.data
        user.level = form.level.data
        user.city = form.city.data
        
        # Set role flags using protected attributes
        user._dancer = form.user_role.data == 'dancer'
        user._organizer = form.user_role.data == 'organizer'
        user._judge = form.user_role.data == 'judge'
        
        # Make sure dancer flag is False for non-dancer roles
        if user._organizer or user._judge:
            user._dancer = False
            
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_organizer:
        return redirect(url_for('organizer_dashboard'))
    elif current_user.is_judge:
        return redirect(url_for('judge_dashboard'))
    else:
        return redirect(url_for('dancer_dashboard'))

@app.route('/organizer/dashboard')
@login_required
def organizer_dashboard():
    if not current_user.is_organizer:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    # Get competitions organized by the current user
    competitions = Competition.query.filter_by(organizer_id=current_user.id).all()
    return render_template('organizer/dashboard.html', competitions=competitions, organizer=current_user)

@app.route('/judge/dashboard')
@login_required
def judge_dashboard():
    if not current_user.is_judge:
        flash('Access denied. You must be a judge to view this page.', 'danger')
        return redirect(url_for('index'))
    
    competitions = current_user.get_assigned_competitions()
    return render_template('judge/dashboard.html', competitions=competitions)

@app.route('/dancer/dashboard')
@login_required
def dancer_dashboard():
    from pprint import pprint
    print("Aktueller User:", current_user)
    print("User-Klasse:", type(current_user))
    print("Ist authentifiziert:", current_user.is_authenticated)
    pprint(dir(current_user))
    
    if not current_user.is_dancer:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    competitions = current_user.get_assigned_competitions()
    return render_template('dancer/dashboard.html', competitions=competitions)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            flash('You do not have admin privileges.', 'error')
            return redirect(url_for('index'))
            
    if request.method == 'POST':
        if 'csrf_token' not in request.form:
            flash('CSRF token missing', 'error')
            return redirect(url_for('admin_login'))

        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.check_password(request.form['password']):
            if user.is_admin:
                login_user(user)
                return redirect(url_for('admin_dashboard'))
            else:
                flash('You do not have admin privileges.', 'error')
        else:
            flash('Invalid email or password.', 'error')
            
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

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileForm(obj=user)
    
    if form.validate_on_submit():
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.city = form.city.data
        user.dance_role = form.dance_role.data
        user.level = form.level.data
        user.role = form.role.data
        
        if form.new_password.data:
            user.set_password(form.new_password.data)
            
        db.session.commit()
        flash('User information updated successfully.', 'success')
        return redirect(url_for('admin_users'))
        
    return render_template('admin/edit_user.html', user=user, form=form)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting user: ' + str(e), 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    
    # Generate a random temporary password
    temp_password = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(12))
    
    # Update user's password
    user.set_password(temp_password)
    db.session.commit()
    
    flash(f'Password has been reset. Temporary password: {temp_password}', 'success')
    return redirect(url_for('admin_edit_user', user_id=user.id))

@app.route('/admin/competitions')
@login_required
@admin_required
def admin_competitions():
    competitions = Competition.query.order_by(Competition.date.desc()).all()
    return render_template('admin/competitions.html', 
                         competitions=competitions,
                         current_time=datetime.now())

@app.route('/admin/statistics')
@login_required
@admin_required
def admin_statistics():
    # Calculate user statistics
    total_users = User.query.count()
    total_leaders = User.query.filter_by(dance_role='leader').count()
    total_followers = User.query.filter_by(dance_role='follower').count()
    total_admins = User.query.filter_by(is_admin=True).count()

    # Calculate competition statistics
    total_competitions = Competition.query.count()
    active_competitions = Competition.query.filter_by(registration_open=True).count()
    completed_competitions = Competition.query.filter(
        Competition.date < datetime.now().date()
    ).count()

    # Calculate total registrations using CompetitionParticipant
    total_registrations = CompetitionParticipant.query.count()

    # Get competition type distribution
    competition_types = {}
    for comp in Competition.query.all():
        if comp.competition_type:
            competition_types[comp.competition_type] = competition_types.get(comp.competition_type, 0) + 1

    # Calculate recent activity
    one_week_ago = datetime.now() - timedelta(days=7)
    new_users_week = User.query.filter(
        User.created_at >= one_week_ago
    ).count()

    # Count new registrations in the last week using CompetitionParticipant
    new_registrations_week = CompetitionParticipant.query.filter(
        CompetitionParticipant.registered_at >= one_week_ago
    ).count()

    upcoming_competitions = Competition.query.filter(
        Competition.date >= datetime.now().date()
    ).count()

    stats = {
        'total_users': total_users,
        'total_leaders': total_leaders,
        'total_followers': total_followers,
        'total_admins': total_admins,
        'total_competitions': total_competitions,
        'active_competitions': active_competitions,
        'completed_competitions': completed_competitions,
        'total_registrations': total_registrations,
        'competition_types': competition_types,
        'new_users_week': new_users_week,
        'new_registrations_week': new_registrations_week,
        'upcoming_competitions': upcoming_competitions
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
    # Load settings from database or use defaults
    settings = {
        'site_name': 'Dance Competition System',
        'contact_email': 'admin@example.com',
        'timezone': 'UTC',
        'max_competitors': 100,
        'registration_buffer_days': 7,
        'enable_waitlist': True,
        'email_notifications': True,
        'registration_notifications': True,
        'score_notifications': True,
        'currency': 'USD',
        'enable_refunds': True,
        'refund_window_days': 30
    }
    return render_template('admin/settings.html', settings=settings)

@app.route('/admin/settings/update', methods=['POST'])
@login_required
@admin_required
def admin_settings_update():
    section = request.form.get('section')
    
    if section == 'general':
        # Update general settings
        site_name = request.form.get('site_name')
        contact_email = request.form.get('contact_email')
        timezone = request.form.get('timezone')
        # Save to database
        flash('General settings updated successfully', 'success')
    
    elif section == 'competition':
        # Update competition settings
        max_competitors = request.form.get('max_competitors')
        registration_buffer_days = request.form.get('registration_buffer_days')
        enable_waitlist = 'enable_waitlist' in request.form
        # Save to database
        flash('Competition settings updated successfully', 'success')
    
    elif section == 'notifications':
        # Update notification settings
        email_notifications = 'email_notifications' in request.form
        registration_notifications = 'registration_notifications' in request.form
        score_notifications = 'score_notifications' in request.form
        # Save to database
        flash('Notification settings updated successfully', 'success')
    
    elif section == 'payment':
        # Update payment settings
        currency = request.form.get('currency')
        enable_refunds = 'enable_refunds' in request.form
        refund_window_days = request.form.get('refund_window_days')
        # Save to database
        flash('Payment settings updated successfully', 'success')
    
    return redirect(url_for('admin_settings'))

@app.route('/admin/create-competition', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_competition():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            date_str = request.form['date']
            city = request.form['city']
            dance_style = request.form['dance_style']
            price = float(request.form['price'])
            description = request.form.get('description', '')
            max_participants = request.form.get('max_participants')
            max_rounds = int(request.form['max_rounds'])
            rotation_size = int(request.form['rotation_size'])
            pairs_per_final = int(request.form['pairs_per_final'])
            scoring_dimensions = request.form.getlist('scoring_dimensions')

            # Convert date string to date object
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Validate future date
            if date <= datetime.now().date():
                flash('Competition date must be in the future', 'danger')
                return redirect(url_for('admin_create_competition'))
            
            # Create new competition
            competition = Competition(
                name=name,
                date=date,
                city=city,
                dance_style=dance_style,
                price=price,
                description=description,
                status='upcoming',
                competition_type='jack_and_jill',
                registration_open=True,
                max_participants=int(max_participants) if max_participants else None,
                max_rounds=max_rounds,
                rotation_size=rotation_size,
                pairs_per_final=pairs_per_final,
                organizer_id=current_user.id  # Add the current user as the organizer
            )
            competition.set_scoring_dimensions(scoring_dimensions)
            
            # Handle banner upload
            if 'banner' in request.files:
                banner = request.files['banner']
                if banner and banner.filename and allowed_file(banner.filename):
                    filename = secure_filename(banner.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    banner.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    competition.banner = filename
            
            db.session.add(competition)
            db.session.commit()

            flash('Competition created successfully! Please set up the head judge in the competition settings.', 'success')
            return redirect(url_for('admin_competitions'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating competition: {str(e)}', 'danger')
            return redirect(url_for('admin_create_competition'))

    # GET request - show form
    return render_template('admin/create_competition.html')

@app.route('/admin/competitions/<int:competition_id>/manage-dancers')
@login_required
@admin_required
def manage_dancers(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    # Get leaders and followers separately
    leaders = CompetitionParticipant.query.join(User).filter(
        CompetitionParticipant.competition_id == competition_id,
        User.dance_role == 'leader'
    ).order_by(CompetitionParticipant.dancer_number).all()
    
    followers = CompetitionParticipant.query.join(User).filter(
        CompetitionParticipant.competition_id == competition_id,
        User.dance_role == 'follower'
    ).order_by(CompetitionParticipant.dancer_number).all()
    
    # Get available dancers (not in competition)
    available_dancers = User.query.filter(
        ~User.id.in_(
            db.session.query(CompetitionParticipant.user_id)
            .filter(CompetitionParticipant.competition_id == competition_id)
        )
    ).all()

    # Create forms
    add_dancer_form = AddDancerForm()
    add_dancer_form.dancer_id.choices = [(d.id, f"{d.first_name} {d.last_name} ({d.dance_role})") for d in available_dancers]
    
    add_audience_form = AddAudienceMemberForm()
    
    return render_template('admin/manage_dancers.html',
                         competition=competition,
                         leaders=leaders,
                         followers=followers,
                         available_dancers=available_dancers,
                         form=add_dancer_form,
                         audience_form=add_audience_form)

@app.route('/admin/competitions/<int:competition_id>/add-dancer', methods=['POST'])
@login_required
@admin_required
def add_dancer_to_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    if competition.participant_list_locked:
        flash('Participant list is locked', 'danger')
        return redirect(url_for('manage_dancers', competition_id=competition_id))
    
    form = AddDancerForm()
    if not form.csrf_token.validate(form):
        flash('CSRF token is missing or invalid', 'danger')
        return redirect(url_for('manage_dancers', competition_id=competition_id))
    
    # Get available dancers for form validation
    available_dancers = User.query.filter(
        ~User.id.in_(
            db.session.query(CompetitionParticipant.user_id)
            .filter(CompetitionParticipant.competition_id == competition_id)
        )
    ).all()
    form.dancer_id.choices = [(d.id, f"{d.first_name} {d.last_name} ({d.dance_role})") for d in available_dancers]
    
    if form.validate_on_submit():
        dancer = User.query.get_or_404(form.dancer_id.data)
        
        # Check if dancer is already in competition
        existing = CompetitionParticipant.query.filter_by(
            competition_id=competition_id,
            user_id=dancer.id
        ).first()
        
        if existing:
            flash('Dancer is already in the competition', 'danger')
            return redirect(url_for('manage_dancers', competition_id=competition_id))
        
        # Get the next available number for this role
        last_number = db.session.query(db.func.max(CompetitionParticipant.dancer_number))\
            .join(User)\
            .filter(
                CompetitionParticipant.competition_id == competition_id,
                User.dance_role == dancer.dance_role
            ).scalar() or 0
        
        # Create new participant
        participant = CompetitionParticipant(
            competition_id=competition_id,
            user_id=dancer.id,
            dancer_number=last_number + 1,
            is_active=True
        )
        
        db.session.add(participant)
        db.session.commit()
        
        # Update competition counts
        competition.update_tiers()
        db.session.commit()
        
        flash('Dancer added successfully', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('manage_dancers', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/add-audience', methods=['POST'])
@login_required
@admin_required
def add_audience_member(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    if competition.participant_list_locked:
        flash('Participant list is locked', 'danger')
        return redirect(url_for('manage_dancers', competition_id=competition_id))
    
    form = AddAudienceMemberForm()
    if form.validate_on_submit():
        # Create temporary user for audience member
        user = User(
            email=f"audience_{int(time.time())}@temp.com",
            first_name=form.name.data,
            last_name="(Audience)",
            dance_role=form.dance_role.data,
            level=competition.level,
            city=competition.city,
            is_temporary=True
        )
        user.set_password('temp123')  # Set a temporary password
        db.session.add(user)
        db.session.flush()  # Get user.id without committing
        
        # Get the next available number for this role
        last_number = db.session.query(db.func.max(CompetitionParticipant.dancer_number))\
            .join(User)\
            .filter(
                CompetitionParticipant.competition_id == competition_id,
                User.dance_role == form.dance_role.data
            ).scalar() or 0
        
        # Create participant
        participant = CompetitionParticipant(
            competition_id=competition_id,
            user_id=user.id,
            dancer_number=last_number + 1,
            is_active=True,
            is_audience_fill=True
        )
        
        db.session.add(participant)
        db.session.commit()
        
        # Update competition counts
        competition.update_tiers()
        db.session.commit()
        
        flash('Audience member added successfully', 'success')
    else:
        flash('Invalid form submission', 'danger')
    
    return redirect(url_for('manage_dancers', competition_id=competition_id))

@app.route('/api/participant/<int:participant_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_participant_status(participant_id):
    participant = CompetitionParticipant.query.get_or_404(participant_id)
    
    try:
        participant.is_active = not participant.is_active
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/participant/<int:participant_id>/remove', methods=['POST'])
@login_required
@admin_required
def remove_participant(participant_id):
    participant = CompetitionParticipant.query.get_or_404(participant_id)
    competition_id = participant.competition_id
    
    try:
        db.session.delete(participant)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/competition/<int:competition_id>/lock-participants', methods=['POST'])
@login_required
@admin_required
def lock_participant_list(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    try:
        competition.participant_list_locked = True
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/competition/<int:competition_id>/unlock-participants', methods=['POST'])
@login_required
@admin_required
def unlock_participant_list(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    try:
        competition.participant_list_locked = False
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/competitions/<int:competition_id>/judges')
@login_required
@admin_required
def manage_competition_judges(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    all_users = User.query.filter_by(role='judge').all()
    return render_template('admin/manage_judges.html', 
                         competition=competition, 
                         all_users=all_users)

@app.route('/admin/competitions/<int:competition_id>/judges/add-existing', methods=['POST'])
@login_required
@admin_required
def add_existing_judge(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    judge_id = request.form.get('judge_id')
    
    if not judge_id:
        flash('Please select a judge', 'danger')
        return redirect(url_for('admin_competition_settings', competition_id=competition_id))
    
    judge = User.query.get(judge_id)
    if not judge:
        flash('Selected judge not found', 'danger')
        return redirect(url_for('admin_competition_settings', competition_id=competition_id))
    
    if judge in competition.judges:
        flash('Judge is already assigned to this competition', 'warning')
        return redirect(url_for('admin_competition_settings', competition_id=competition_id))
    
    try:
        competition.judges.append(judge)
        db.session.commit()
        flash('Judge added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding judge: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/judges/remove/<int:judge_id>', methods=['POST'])
@login_required
@admin_required
def remove_judge(competition_id, judge_id):
    competition = Competition.query.get_or_404(competition_id)
    judge = User.query.get_or_404(judge_id)
    
    if judge not in competition.judges:
        flash('Judge is not assigned to this competition', 'warning')
        return redirect(url_for('admin_competition_settings', competition_id=competition_id))
    
    try:
        competition.judges.remove(judge)
        db.session.commit()
        flash('Judge removed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing judge: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/judges/add-new', methods=['POST'])
@login_required
@admin_required
def add_new_judge(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    try:
        # Create new judge user
        judge = User(
            email=request.form['email'],
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            is_judge=True,
            dance_role='judge',  # Setting a default dance_role for judges
            password=generate_password_hash('temppass123')  # Temporary password
        )
        
        db.session.add(judge)
        competition.judges.append(judge)
        db.session.commit()
        
        flash('New judge added successfully. They will receive an email with login credentials.', 'success')
        # TODO: Send email with credentials
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding new judge: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

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
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    banner.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    competition.banner = filename
            
            # Update competition details
            competition.name = request.form['name']
            date_str = request.form['date']
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Validate future date
            if date <= datetime.now().date():
                flash('Competition date must be in the future', 'danger')
                return redirect(url_for('admin_edit_competition', competition_id=competition_id))
            
            competition.date = date
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

@app.route('/admin/competitions/<int:competition_id>/details', methods=['GET', 'POST'])
@login_required
@admin_required
def complete_competition_details(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    if request.method == 'POST':
        try:
            # Handle banner upload
            if 'banner' in request.files:
                file = request.files['banner']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    competition.banner = filename

            # Update other details
            competition.description = request.form.get('description')
            competition.price = float(request.form.get('price'))
            competition.dance_style = request.form.get('dance_style')
            
            db.session.commit()
            flash('Competition details updated successfully!', 'success')
            return redirect(url_for('admin_competitions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating competition details: {str(e)}', 'error')
    
    return render_template('admin/competition_details.html', competition=competition)

@app.route('/admin/competitions/<int:competition_id>/rounds')
@login_required
@admin_required
def manage_competition_rounds(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    return render_template('admin/competition_rounds.html', competition=competition)

@app.route('/admin/competitions/<int:competition_id>/rounds/add', methods=['POST'])
@login_required
@admin_required
def add_competition_round(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    round_number = len(competition.rounds) + 1
    new_round = Round(
        competition_id=competition_id,
        round_number=round_number,
        status='pending'
    )
    db.session.add(new_round)
    db.session.commit()
    flash(f'Added Round {round_number} to {competition.name}', 'success')
    return redirect(url_for('manage_competition_rounds', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/rounds/<int:round_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_competition_round(competition_id, round_id):
    competition = Competition.query.get_or_404(competition_id)
    round = Round.query.get_or_404(round_id)
    if round.competition_id == competition_id:
        db.session.delete(round)
        db.session.commit()
        flash(f'Deleted Round {round.round_number} from {competition.name}', 'success')
    return redirect(url_for('manage_competition_rounds', competition_id=competition_id))

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

@app.route('/admin/competitions/<int:competition_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    try:
        # Delete all participants first
        CompetitionParticipant.query.filter_by(competition_id=competition_id).delete()
        # Then delete the competition
        db.session.delete(competition)
        db.session.commit()
        flash('Competition deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting competition: {str(e)}', 'danger')
    return redirect(url_for('admin_competitions'))

@app.route('/admin/competitions/<int:competition_id>/settings')
@login_required
@admin_required
def admin_competition_settings(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    # Get all users who are judges but not already assigned to this competition
    assigned_judge_ids = [ja.judge_id for ja in competition.judge_assignments]
    available_judges = User.query.filter(
        User.is_judge == True,
        ~User.id.in_(assigned_judge_ids)
    ).all()
    return render_template('admin/competition_settings.html', 
                         competition=competition,
                         available_judges=available_judges,
                         current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/admin/competitions/<int:competition_id>/settings/update', methods=['POST'])
@login_required
@admin_required
def update_competition_settings(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    try:
        competition.name = request.form['name']
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Validate future date
        if date <= datetime.now().date():
            flash('Competition date must be in the future', 'danger')
            return redirect(url_for('admin_competition_settings', competition_id=competition_id))
            
        competition.date = date
        competition.city = request.form['city']
        competition.price = float(request.form['price'])
        competition.description = request.form.get('description', '')
        competition.max_participants = request.form.get('max_participants', type=int)
        competition.registration_open = bool(request.form.get('registration_open'))
        competition.status = request.form.get('status', 'upcoming')
        
        # Handle scoring dimensions - getlist returns empty list if no values selected
        scoring_dimensions = request.form.getlist('scoring_dimensions')
        competition.set_scoring_dimensions(scoring_dimensions)
        
        if 'banner' in request.files:
            banner = request.files['banner']
            if banner and banner.filename and allowed_file(banner.filename):
                filename = secure_filename(banner.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                banner.save(file_path)
                competition.banner = file_path
        
        db.session.commit()
        flash('Competition settings updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating competition settings: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/structure/update', methods=['POST'])
@login_required
@admin_required
def admin_update_competition_structure(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    try:
        competition.max_rounds = int(request.form['max_rounds'])
        competition.rotation_size = int(request.form['rotation_size'])
        competition.pairs_per_final = int(request.form['pairs_per_final'])
        
        db.session.commit()
        flash('Competition structure updated successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating competition structure: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/head-judge/update', methods=['POST'])
@login_required
@admin_required
def admin_update_head_judge(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    try:
        judge_id = request.form.get('judge_id')
        
        if judge_id:
            head_judge = User.query.get(judge_id)
            if head_judge and head_judge in competition.judges:
                competition.head_judge_id = head_judge.id
                db.session.commit()
                flash('Head judge updated successfully!', 'success')
            else:
                flash('Invalid head judge selection', 'danger')
        else:
            flash('Please select a head judge', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating head judge: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/registration/update', methods=['POST'])
@login_required
@admin_required
def admin_update_registration_settings(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    try:
        competition.registration_open = 'registration_open' in request.form
        competition.max_participants = int(request.form.get('max_participants', 0))
        db.session.commit()
        flash('Registration settings updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating registration settings: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/judges/add-existing', methods=['POST'])
@login_required
@admin_required
def admin_add_existing_judge_to_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    judge_id = request.form.get('judge_id')
    
    if not judge_id:
        flash('Please select a judge', 'danger')
        return redirect(url_for('admin_competition_settings', competition_id=competition_id))
    
    judge = User.query.get(judge_id)
    if not judge:
        flash('Selected judge not found', 'danger')
        return redirect(url_for('admin_competition_settings', competition_id=competition_id))
    
    if judge in competition.judges:
        flash('Judge is already assigned to this competition', 'warning')
        return redirect(url_for('admin_competition_settings', competition_id=competition_id))
    
    try:
        competition.judges.append(judge)
        db.session.commit()
        flash('Judge added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding judge: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/judges/remove/<int:judge_id>', methods=['POST'])
@login_required
@admin_required
def admin_remove_judge_from_competition(competition_id, judge_id):
    competition = Competition.query.get_or_404(competition_id)
    judge = User.query.get_or_404(judge_id)
    
    if judge not in competition.judges:
        flash('Judge is not assigned to this competition', 'warning')
        return redirect(url_for('admin_competition_settings', competition_id=competition_id))
    
    try:
        competition.judges.remove(judge)
        db.session.commit()
        flash('Judge removed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing judge: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/judges/add-new', methods=['POST'])
@login_required
@admin_required
def admin_add_new_judge_to_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    try:
        # Generate a random temporary password
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        # Create new judge user
        judge = User(
            email=request.form['email'],
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            is_judge=True,
            dance_role='judge'  # Setting a default dance_role for judges
        )
        judge.set_password(temp_password)
        
        db.session.add(judge)
        competition.judges.append(judge)
        db.session.commit()
        
        # Send email with credentials
        send_judge_credentials_email(judge.email, temp_password, competition)
        
        flash('New judge created and added successfully. Credentials have been sent by email.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating judge: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/judges/invite', methods=['POST'])
@login_required
@admin_required
def admin_invite_judge_to_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    email = request.form.get('email')
    
    if not email:
        flash('Please provide an email address', 'danger')
        return redirect(url_for('admin_competition_settings', competition_id=competition_id))
    
    try:
        # Generate invitation token
        token = generate_invitation_token(email, competition.id)
        
        # Send invitation email
        send_judge_invitation_email(email, token, competition)
        
        flash('Invitation sent successfully', 'success')
    except Exception as e:
        flash(f'Error sending invitation: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/judges/<int:judge_id>/remove', methods=['POST'])
@login_required
@admin_required
def admin_remove_judge_from_competition_by_id(competition_id, judge_id):
    competition = Competition.query.get_or_404(competition_id)
    judge = User.query.get_or_404(judge_id)
    
    try:
        if competition.head_judge_id == judge.id:
            competition.head_judge_id = None
        
        competition.judges.remove(judge)
        db.session.commit()
        flash('Judge removed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing judge: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/admin/competitions/<int:competition_id>/scoring/update', methods=['POST'])
@login_required
@admin_required
def admin_update_scoring_settings(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    try:
        scoring_dimensions = request.form.getlist('scoring_dimensions')
        competition.set_scoring_dimensions(scoring_dimensions)
        db.session.commit()
        flash('Scoring settings updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating scoring settings: {str(e)}', 'danger')
    
    return redirect(url_for('admin_competition_settings', competition_id=competition_id))

@app.route('/competitions')
def competitions():
    upcoming_competitions = Competition.query.filter_by(status='upcoming').all()
    in_progress_competitions = Competition.query.filter_by(status='in_progress').all()
    completed_competitions = Competition.query.filter_by(status='completed').all()
    return render_template('competitions.html', 
                         upcoming_competitions=upcoming_competitions, 
                         in_progress_competitions=in_progress_competitions, 
                         completed_competitions=completed_competitions)

@app.route('/competitions/<int:competition_id>')
def competition_detail(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    user_registered = False
    if current_user.is_authenticated:
        participant = CompetitionParticipant.query.filter_by(
            competition_id=competition_id,
            user_id=current_user.id
        ).first()
        user_registered = participant is not None
        
    return render_template('competition_detail.html', 
                         competition=competition,
                         user_registered=user_registered)

@app.route('/competitions/<int:competition_id>/register', methods=['POST'])
@login_required
def register_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    
    if not competition.registration_open:
        flash('Registration is closed for this competition.', 'error')
        return redirect(url_for('competition_detail', competition_id=competition_id))
        
    if not current_user.can_compete_in(competition.level):
        flash(f'You are not eligible to compete in {competition.level} level.', 'error')
        return redirect(url_for('competition_detail', competition_id=competition_id))
        
    # Check if already registered
    existing = CompetitionParticipant.query.filter_by(
        competition_id=competition_id,
        user_id=current_user.id
    ).first()
    
    if existing:
        flash('You are already registered for this competition.', 'info')
        return redirect(url_for('competition_detail', competition_id=competition_id))
        
    # Register user
    participant = CompetitionParticipant(
        competition_id=competition_id,
        user_id=current_user.id,
        is_active=True
    )
    db.session.add(participant)
    
    # Update competition counts
    if current_user.dance_role == 'leader':
        competition.leader_count += 1
    else:
        competition.follower_count += 1
    competition.update_tiers()
    
    db.session.commit()
    flash('Successfully registered for the competition!', 'success')
    return redirect(url_for('competition_detail', competition_id=competition_id))

@app.route('/competitions/<int:competition_id>/manage', methods=['GET'])
@login_required
@admin_required
def manage_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    judge_form = JudgeAssignmentForm()
    start_round_form = StartRoundForm()
    
    # Populate judge choices
    judge_form.judges.choices = [(u.id, u.username) for u in User.query.filter_by(is_judge=True).all()]
    
    # Populate round number choices based on current round
    if competition.current_round:
        next_round = competition.current_round + 1
        start_round_form.round_number.choices = [(next_round, f'Round {next_round}')]
    else:
        start_round_form.round_number.choices = [(1, 'Round 1')]
    
    return render_template('manage_competition.html', 
                         competition=competition,
                         judge_form=judge_form,
                         start_round_form=start_round_form)

@app.route('/competitions/<int:competition_id>/assign-judge', methods=['POST'])
@login_required
@admin_required
def assign_judge(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    form = JudgeAssignmentForm()
    
    if form.validate_on_submit():
        judge = User.query.get(form.judges.data)
        if judge:
            if form.is_head_judge.data:
                competition.head_judge_id = judge.id
            competition.judges.append(judge)
            db.session.commit()
            flash('Judge assigned successfully!', 'success')
        else:
            flash('Invalid judge selection.', 'error')
    
    return redirect(url_for('manage_competition', competition_id=competition_id))

@app.route('/competitions/<int:competition_id>/start-round', methods=['POST'])
@login_required
@admin_required
def start_round(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    form = StartRoundForm()
    
    if form.validate_on_submit():
        if not competition.can_start_competition():
            flash('Cannot start competition. Check minimum requirements.', 'error')
            return redirect(url_for('manage_competition', competition_id=competition_id))
            
        round_number = int(form.round_number.data)
        
        # Create new round
        new_round = Round(
            competition_id=competition_id,
            round_number=round_number,
            status='in_progress'
        )
        db.session.add(new_round)
        
        # Update competition status
        competition.status = 'in_progress'
        competition.current_round = round_number
        
        db.session.commit()
        flash(f'Successfully started round {round_number}!', 'success')
        
    return redirect(url_for('manage_competition', competition_id=competition_id))

@app.route('/competitions/<int:competition_id>/round/<int:round_id>/create-heats', methods=['POST'])
@login_required
@admin_required
def create_heats(competition_id, round_id):
    competition = Competition.query.get_or_404(competition_id)
    round = Round.query.get_or_404(round_id)
    
    if round.status != 'in_progress':
        flash('Can only create heats for in-progress rounds.', 'error')
        return redirect(url_for('manage_competition', competition_id=competition_id))
        
    # Get all active participants
    leaders = CompetitionParticipant.query.join(User).filter(
        CompetitionParticipant.competition_id == competition_id,
        CompetitionParticipant.is_active == True,
        User.dance_role == 'leader'
    ).all()
    
    followers = CompetitionParticipant.query.join(User).filter(
        CompetitionParticipant.competition_id == competition_id,
        CompetitionParticipant.is_active == True,
        User.dance_role == 'follower'
    ).all()
    
    # Randomize participants
    random.shuffle(leaders)
    random.shuffle(followers)
    
    # Create heats (5 couples per heat)
    couples_per_heat = 5
    total_couples = min(len(leaders), len(followers))
    total_heats = (total_couples + couples_per_heat - 1) // couples_per_heat
    
    for heat_number in range(1, total_heats + 1):
        heat = Heat(
            round_id=round_id,
            heat_number=heat_number,
            status='pending'
        )
        db.session.add(heat)
        db.session.flush()  # Get heat ID
        
        # Assign couples to this heat
        start_idx = (heat_number - 1) * couples_per_heat
        end_idx = min(start_idx + couples_per_heat, total_couples)
        
        for i in range(start_idx, end_idx):
            leader_participant = HeatParticipant(
                heat_id=heat.id,
                participant_id=leaders[i].id,
                partner_id=followers[i].id
            )
            follower_participant = HeatParticipant(
                heat_id=heat.id,
                participant_id=followers[i].id,
                partner_id=leaders[i].id
            )
            db.session.add(leader_participant)
            db.session.add(follower_participant)
    
    db.session.commit()
    flash(f'Successfully created {total_heats} heats!', 'success')
    return redirect(url_for('manage_competition', competition_id=competition_id))

@app.route('/join_competition/<int:competition_id>', methods=['POST'])
@login_required
def join_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    participant = CompetitionParticipant(
        competition_id=competition.id,
        user_id=current_user.id,
        is_active=True
    )
    db.session.add(participant)
    db.session.commit()
    flash('You have successfully joined the competition!', 'success')
    return redirect(url_for('competition_detail', competition_id=competition.id))

@app.route('/organizer/create-competition', methods=['GET', 'POST'])
@login_required
def organizer_create_competition():
    if not current_user.is_organizer and not current_user.is_admin:
        flash('You do not have permission to create competitions.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            # Debug: Print all form data
            print("Form data received:", request.form)
            print("Files received:", request.files)
            
            name = request.form.get('name')
            date_str = request.form.get('date')
            city = request.form.get('city')
            max_participants = request.form.get('max_participants')
            price = request.form.get('price')
            description = request.form.get('description')
            dance_style = request.form.get('dance_style')
            level = request.form.get('level')  # Get level from form
            max_rounds = int(request.form.get('max_rounds', 3))
            rotation_size = int(request.form.get('rotation_size', 2))
            pairs_per_final = int(request.form.get('pairs_per_final', 5))
            
            # Debug: Print processed data
            print("Processed data:", {
                'name': name,
                'date': date_str,
                'city': city,
                'price': price,
                'description': description,
                'max_participants': max_participants,
                'max_rounds': max_rounds,
                'rotation_size': rotation_size,
                'pairs_per_final': pairs_per_final,
                'dance_style': dance_style,
                'level': level  # Add level to debug output
            })
            
            # Convert date string to datetime object
            competition_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Validate required fields
            if not dance_style:
                flash('Dance style is required', 'danger')
                return redirect(url_for('organizer_create_competition'))
                
            competition = Competition(
                name=name,
                date=competition_date,
                city=city,
                max_participants=int(max_participants) if max_participants else None,
                price=float(price),
                description=description,
                dance_style=dance_style,
                level=level,  # Add level to competition
                competition_type='jack_and_jill',
                max_rounds=max_rounds,
                rotation_size=rotation_size,
                pairs_per_final=pairs_per_final,
                organizer_id=current_user.id,
                status='upcoming',
                registration_open=True,
                scoring_dimensions=''
            )
            
            # Handle banner upload
            if 'banner' in request.files:
                banner = request.files['banner']
                if banner and banner.filename and allowed_file(banner.filename):
                    filename = secure_filename(banner.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    banner.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    competition.banner = filename

            db.session.add(competition)
            db.session.commit()
            
            flash('Competition created successfully!', 'success')
            return redirect(url_for('organizer_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating competition: {str(e)}', 'danger')
            print("Error details:", str(e))  # Debug: Print error details
            return redirect(url_for('organizer_create_competition'))
        
    return render_template('organizer/create_competition.html')

def send_judge_credentials_email(email, password, competition):
    # TODO: Implement email sending
    print(f"Would send credentials to {email} for competition {competition.name}")
    pass

def send_judge_invitation_email(email, token, competition):
    # TODO: Implement email sending
    print(f"Would send invitation to {email} for competition {competition.name}")
    pass

def generate_invitation_token(email, competition_id):
    # TODO: Implement secure token generation
    return f"{email}_{competition_id}_{random.randint(1000, 9999)}"

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/create-jack-and-jill', methods=['GET', 'POST'])
@login_required
@admin_required
def create_jack_and_jill():
    if request.method == 'POST':
        try:
            # Debug: Print all form data
            print("Form data received:", request.form)
            print("Files received:", request.files)
            
            name = request.form['name']
            date_str = request.form['date']
            city = request.form['city']
            price = float(request.form['price'])
            description = request.form.get('description', '')
            max_participants = request.form.get('max_participants')
            max_rounds = int(request.form['max_rounds'])
            rotation_size = int(request.form['rotation_size'])
            pairs_per_final = int(request.form['pairs_per_final'])
            scoring_dimensions = request.form.getlist('scoring_dimensions')
            dance_style = request.form['dance_style']
            
            # Debug: Print processed data
            print("Processed data:", {
                'name': name,
                'date': date_str,
                'city': city,
                'price': price,
                'description': description,
                'max_participants': max_participants,
                'max_rounds': max_rounds,
                'rotation_size': rotation_size,
                'pairs_per_final': pairs_per_final,
                'scoring_dimensions': scoring_dimensions,
                'dance_style': dance_style
            })
            
            # Convert date string to date object
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Validate future date
            if date <= datetime.now().date():
                flash('Competition date must be in the future', 'danger')
                return redirect(url_for('create_jack_and_jill'))
            
            # Create new competition
            competition = Competition(
                name=name,
                date=date,
                city=city,
                price=price,
                description=description,
                status='upcoming',
                dance_style=dance_style,
                competition_type='jack_and_jill',
                registration_open=True,
                max_participants=int(max_participants) if max_participants else None,
                max_rounds=max_rounds,
                rotation_size=rotation_size,
                pairs_per_final=pairs_per_final,
                organizer_id=current_user.id  # Add the current user as the organizer
            )
            competition.set_scoring_dimensions(scoring_dimensions)
            
            if 'banner' in request.files:
                banner = request.files['banner']
                if banner and banner.filename and allowed_file(banner.filename):
                    filename = secure_filename(banner.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    banner.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    competition.banner = filename

            db.session.add(competition)
            db.session.commit()
            flash('Competition created successfully!', 'success')
            return redirect(url_for('admin_competitions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating competition: {str(e)}', 'danger')
            print("Error details:", str(e))  # Debug: Print error details
            return redirect(url_for('create_jack_and_jill'))
    
    return render_template('admin/create_jack_and_jill.html')

@app.context_processor
def utility_processor():
    def format_date(d):
        if not d:
            return ''
        if isinstance(d, str):
            try:
                d = datetime.strptime(d, '%Y-%m-%d')
            except ValueError:
                return d
        return d.strftime('%Y-%m-%d')

    def format_datetime(dt):
        if not dt:
            return ''
        if isinstance(dt, str):
            try:
                dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return dt
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    return {
        'datetime': datetime,
        'len': len,
        'str': str,
        'enumerate': enumerate,
        'format_date': format_date,
        'format_datetime': format_datetime
    }

if __name__ == '__main__':
    with app.app_context():
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()

        try:
            # Create test admin account
            admin = User()
            admin.email = "admin@example.com"
            admin.first_name = "Admin"
            admin.last_name = "User"
            admin.dance_role = "leader"
            admin.level = "advanced"
            admin._admin = True
            admin._organizer = True
            admin.set_password("admin123")
            db.session.add(admin)

            # Create test organizer
            organizer = User()
            organizer.email = "organizer@example.com"
            organizer.first_name = "Test"
            organizer.last_name = "Organizer"
            organizer.dance_role = "leader"
            organizer.level = "advanced"
            organizer._organizer = True
            organizer._dancer = False
            organizer.set_password("organizer123")
            db.session.add(organizer)

            # Create test judge
            judge = User()
            judge.email = "judge@example.com"
            judge.first_name = "Test"
            judge.last_name = "Judge"
            judge.dance_role = "leader"
            judge.level = "advanced"
            judge._judge = True
            judge._dancer = False
            judge.set_password("judge123")
            db.session.add(judge)

            # Create test dancer
            dancer = User()
            dancer.email = "dancer@example.com"
            dancer.first_name = "Test"
            dancer.last_name = "Dancer"
            dancer.dance_role = "follower"
            dancer.level = "intermediate"
            dancer._dancer = True
            dancer.set_password("dancer123")
            db.session.add(dancer)

            db.session.commit()
            print("Test accounts created successfully")

        except Exception as e:
            db.session.rollback()
            print(f"Error creating test accounts: {str(e)}")
            raise

    app.run(debug=True, port=5019)
