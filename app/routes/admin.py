from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.competition import Competition, CompetitionStatus
from app.services.competition_service import CompetitionService
from app.decorators import admin_required
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/competitions')
@login_required
@admin_required
def list_competitions():
    competitions = Competition.query.all()
    return render_template('admin/competitions.html', competitions=competitions)

@admin_bp.route('/admin/competitions/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_competition():
    if request.method == 'POST':
        name = request.form.get('name')
        date_str = request.form.get('date')
        dance_level = request.form.get('dance_level')
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            competition = CompetitionService.create_competition(
                name=name,
                date=date,
                dance_level=dance_level,
                organizer_id=current_user.id
            )
            flash('Competition created successfully!', 'success')
            return redirect(url_for('admin.manage_competition', competition_id=competition.id))
        except Exception as e:
            flash(f'Error creating competition: {str(e)}', 'error')
    
    return render_template('admin/create_competition.html')

@admin_bp.route('/admin/competitions/<int:competition_id>')
@login_required
@admin_required
def manage_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    return render_template('admin/manage_competition.html', competition=competition)

@admin_bp.route('/admin/competitions/<int:competition_id>/registration/<string:action>')
@login_required
@admin_required
def manage_registration(competition_id, action):
    if action == 'open':
        CompetitionService.open_registration(competition_id)
        flash('Registration opened!', 'success')
    elif action == 'close':
        CompetitionService.close_registration(competition_id)
        flash('Registration closed!', 'success')
    
    return redirect(url_for('admin.manage_competition', competition_id=competition_id))

@admin_bp.route('/admin/competitions/<int:competition_id>/start', methods=['POST'])
@login_required
@admin_required
def start_competition(competition_id):
    success, message = CompetitionService.start_competition(competition_id)
    if success:
        flash('Competition started successfully!', 'success')
    else:
        flash(f'Error starting competition: {message}', 'error')
    
    return redirect(url_for('admin.manage_competition', competition_id=competition_id))

@admin_bp.route('/admin/competitions/<int:competition_id>/advance-round', methods=['POST'])
@login_required
@admin_required
def advance_round(competition_id):
    # Get selected couples from form
    advancing_couples = request.form.getlist('advancing_couples')
    
    if CompetitionService.advance_round(competition_id, advancing_couples):
        flash('Advanced to next round successfully!', 'success')
    else:
        flash('Error advancing round', 'error')
    
    return redirect(url_for('admin.manage_competition', competition_id=competition_id))
