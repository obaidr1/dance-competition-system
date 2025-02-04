from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models.database import db
from models.jack_and_jill import *
import random

bp = Blueprint('jack_and_jill', __name__)

def head_judge_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        competition_id = kwargs.get('competition_id')
        if not competition_id:
            flash('Competition not found.', 'error')
            return redirect(url_for('jack_and_jill.list_competitions'))
        
        judge = JackAndJillJudge.query.filter_by(
            competition_id=competition_id,
            user_id=current_user.id,
            is_head_judge=True
        ).first()
        
        if not judge:
            flash('Head judge access required.', 'error')
            return redirect(url_for('jack_and_jill.list_competitions'))
            
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/jack-and-jill')
@login_required
def list_competitions():
    competitions = JackAndJillCompetition.query.all()
    return render_template('jack_and_jill/list.html', competitions=competitions)

@bp.route('/jack-and-jill/create', methods=['GET', 'POST'])
@login_required
def create_competition():
    if request.method == 'POST':
        competition = JackAndJillCompetition(
            name=request.form['name'],
            max_participants=request.form.get('max_participants', type=int),
            num_rounds=request.form.get('num_rounds', type=int),
            head_judge_id=current_user.id
        )
        
        # Create default criteria
        criteria = [
            JackAndJillCriteria(name='Musicality'),
            JackAndJillCriteria(name='Connection'),
            JackAndJillCriteria(name='Styling'),
            JackAndJillCriteria(name='Footwork'),
            JackAndJillCriteria(name='Impression')
        ]
        
        db.session.add(competition)
        for c in criteria:
            c.competition = competition
            db.session.add(c)
            
        db.session.commit()
        
        return redirect(url_for('jack_and_jill.manage_competition', competition_id=competition.id))
        
    return render_template('jack_and_jill/create.html')

@bp.route('/jack-and-jill/<int:competition_id>')
@login_required
def manage_competition(competition_id):
    competition = JackAndJillCompetition.query.get_or_404(competition_id)
    return render_template('jack_and_jill/manage.html', competition=competition)

@bp.route('/jack-and-jill/<int:competition_id>/register', methods=['POST'])
@login_required
def register_participant(competition_id):
    competition = JackAndJillCompetition.query.get_or_404(competition_id)
    role = request.form.get('role')
    
    if role not in ['leader', 'follower']:
        flash('Invalid role specified.', 'error')
        return redirect(url_for('jack_and_jill.manage_competition', competition_id=competition_id))
        
    # Check if already registered
    existing = JackAndJillParticipant.query.filter_by(
        competition_id=competition_id,
        user_id=current_user.id
    ).first()
    
    if existing:
        flash('Already registered for this competition.', 'error')
        return redirect(url_for('jack_and_jill.manage_competition', competition_id=competition_id))
        
    # Get next available dancer number
    last_number = db.session.query(db.func.max(JackAndJillParticipant.dancer_number))\
        .filter_by(competition_id=competition_id).scalar() or 0
        
    participant = JackAndJillParticipant(
        competition_id=competition_id,
        user_id=current_user.id,
        dancer_number=last_number + 1,
        role=role
    )
    
    db.session.add(participant)
    db.session.commit()
    
    flash(f'Successfully registered as {role.title()} #{participant.dancer_number}', 'success')
    return redirect(url_for('jack_and_jill.manage_competition', competition_id=competition_id))

@bp.route('/jack-and-jill/<int:competition_id>/start-round', methods=['POST'])
@login_required
@head_judge_required
def start_round(competition_id):
    competition = JackAndJillCompetition.query.get_or_404(competition_id)
    
    if competition.current_round > competition.num_rounds:
        flash('All rounds completed.', 'error')
        return redirect(url_for('jack_and_jill.manage_competition', competition_id=competition_id))
        
    # Create new round
    round = JackAndJillRound(
        competition_id=competition_id,
        round_number=competition.current_round,
        couples_per_heat=request.form.get('couples_per_heat', type=int, default=4),
        rotation_size=request.form.get('rotation_size', type=int, default=2)
    )
    
    db.session.add(round)
    db.session.commit()
    
    # Generate initial pairings
    leaders = JackAndJillParticipant.query.filter_by(
        competition_id=competition_id,
        role='leader',
        is_active=True
    ).all()
    
    followers = JackAndJillParticipant.query.filter_by(
        competition_id=competition_id,
        role='follower',
        is_active=True
    ).all()
    
    # Balance leaders and followers
    if len(leaders) != len(followers):
        flash('Unequal number of leaders and followers. Please add substitutes.', 'error')
        return redirect(url_for('jack_and_jill.manage_competition', competition_id=competition_id))
        
    # Randomize order
    random.shuffle(leaders)
    random.shuffle(followers)
    
    # Create pairings for first rotation
    heat_number = 1
    for i in range(0, len(leaders), round.couples_per_heat):
        heat_leaders = leaders[i:i + round.couples_per_heat]
        heat_followers = followers[i:i + round.couples_per_heat]
        
        for leader, follower in zip(heat_leaders, heat_followers):
            pairing = JackAndJillPairing(
                round=round,
                leader_id=leader.id,
                follower_id=follower.id,
                heat_number=heat_number,
                rotation_number=1
            )
            db.session.add(pairing)
            
        heat_number += 1
        
    db.session.commit()
    return redirect(url_for('jack_and_jill.judge_round', competition_id=competition_id, round_id=round.id))

@bp.route('/jack-and-jill/<int:competition_id>/round/<int:round_id>/rotate', methods=['POST'])
@login_required
@head_judge_required
def rotate_dancers(competition_id, round_id):
    round = JackAndJillRound.query.get_or_404(round_id)
    
    # Get current rotation's pairings
    current_pairings = JackAndJillPairing.query.filter_by(
        round_id=round_id
    ).order_by(JackAndJillPairing.heat_number, JackAndJillPairing.id).all()
    
    # Group followers by heat
    followers_by_heat = {}
    for pairing in current_pairings:
        if pairing.heat_number not in followers_by_heat:
            followers_by_heat[pairing.heat_number] = []
        followers_by_heat[pairing.heat_number].append(pairing.follower_id)
        
    # Rotate followers forward
    new_rotation = current_pairings[0].rotation_number + 1
    for heat_number, heat_followers in followers_by_heat.items():
        # Rotate followers by rotation_size positions
        rotated = heat_followers[round.rotation_size:] + heat_followers[:round.rotation_size]
        followers_by_heat[heat_number] = rotated
        
    # Create new pairings with rotated followers
    for pairing in current_pairings:
        heat_followers = followers_by_heat[pairing.heat_number]
        follower_index = current_pairings.index(pairing) % len(heat_followers)
        
        new_pairing = JackAndJillPairing(
            round_id=round_id,
            leader_id=pairing.leader_id,
            follower_id=heat_followers[follower_index],
            heat_number=pairing.heat_number,
            rotation_number=new_rotation
        )
        db.session.add(new_pairing)
        
    db.session.commit()
    return redirect(url_for('jack_and_jill.judge_round', competition_id=competition_id, round_id=round_id))

@bp.route('/jack-and-jill/<int:competition_id>/round/<int:round_id>/judge')
@login_required
def judge_round(competition_id, round_id):
    competition = JackAndJillCompetition.query.get_or_404(competition_id)
    round = JackAndJillRound.query.get_or_404(round_id)
    
    # Check if user is a judge
    judge = JackAndJillJudge.query.filter_by(
        competition_id=competition_id,
        user_id=current_user.id
    ).first()
    
    if not judge:
        flash('Judge access required.', 'error')
        return redirect(url_for('jack_and_jill.manage_competition', competition_id=competition_id))
        
    # Get enabled criteria
    criteria = JackAndJillCriteria.query.filter_by(
        competition_id=competition_id,
        enabled=True
    ).all()
    
    # Get current pairings
    pairings = JackAndJillPairing.query.filter_by(
        round_id=round_id
    ).order_by(JackAndJillPairing.heat_number, JackAndJillPairing.id).all()
    
    return render_template('jack_and_jill/judge.html',
                         competition=competition,
                         round=round,
                         criteria=criteria,
                         pairings=pairings,
                         is_head_judge=judge.is_head_judge)

@bp.route('/jack-and-jill/<int:competition_id>/round/<int:round_id>/score', methods=['POST'])
@login_required
def submit_scores(competition_id, round_id):
    judge = JackAndJillJudge.query.filter_by(
        competition_id=competition_id,
        user_id=current_user.id
    ).first()
    
    if not judge:
        return jsonify({'error': 'Judge access required'}), 403
        
    pairing_id = request.form.get('pairing_id', type=int)
    
    score = JackAndJillScore(
        pairing_id=pairing_id,
        judge_id=judge.id,
        musicality=request.form.get('musicality', type=int),
        connection=request.form.get('connection', type=int),
        styling=request.form.get('styling', type=int),
        footwork=request.form.get('footwork', type=int),
        impression=request.form.get('impression', type=int),
        notes=request.form.get('notes')
    )
    
    db.session.add(score)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/jack-and-jill/<int:competition_id>/round/<int:round_id>/complete', methods=['POST'])
@login_required
@head_judge_required
def complete_round(competition_id, round_id):
    competition = JackAndJillCompetition.query.get_or_404(competition_id)
    round = JackAndJillRound.query.get_or_404(round_id)
    
    # Calculate scores and determine who advances
    if competition.current_round < competition.num_rounds:
        # Get all scores for this round
        scores = db.session.query(
            JackAndJillPairing.leader_id,
            JackAndJillPairing.follower_id,
            db.func.avg(
                (JackAndJillScore.musicality +
                 JackAndJillScore.connection +
                 JackAndJillScore.styling +
                 JackAndJillScore.footwork +
                 JackAndJillScore.impression) / 5.0
            ).label('avg_score')
        ).join(JackAndJillScore)\
         .filter(JackAndJillPairing.round_id == round_id)\
         .group_by(JackAndJillPairing.leader_id, JackAndJillPairing.follower_id)\
         .order_by(db.text('avg_score DESC')).all()
        
        # Mark bottom 50% as eliminated
        cutoff = len(scores) // 2
        eliminated_leaders = [s.leader_id for s in scores[cutoff:]]
        eliminated_followers = [s.follower_id for s in scores[cutoff:]]
        
        JackAndJillParticipant.query.filter(
            JackAndJillParticipant.id.in_(eliminated_leaders + eliminated_followers)
        ).update({
            'is_active': False,
            'eliminated_in_round': competition.current_round
        }, synchronize_session=False)
        
    # Update competition status
    round.status = 'completed'
    competition.current_round += 1
    
    if competition.current_round > competition.num_rounds:
        competition.status = 'completed'
        
    db.session.commit()
    
    return redirect(url_for('jack_and_jill.manage_competition', competition_id=competition_id))

@bp.route('/jack-and-jill/<int:competition_id>/leaderboard')
def view_leaderboard(competition_id):
    competition = JackAndJillCompetition.query.get_or_404(competition_id)
    
    if competition.status != 'completed':
        flash('Competition is still in progress.', 'error')
        return redirect(url_for('jack_and_jill.manage_competition', competition_id=competition_id))
        
    # Calculate final scores
    final_round = JackAndJillRound.query.filter_by(
        competition_id=competition_id,
        round_number=competition.num_rounds
    ).first()
    
    scores = db.session.query(
        JackAndJillParticipant,
        db.func.avg(
            (JackAndJillScore.musicality +
             JackAndJillScore.connection +
             JackAndJillScore.styling +
             JackAndJillScore.footwork +
             JackAndJillScore.impression) / 5.0
        ).label('avg_score')
    ).join(JackAndJillPairing, db.or_(
        JackAndJillParticipant.id == JackAndJillPairing.leader_id,
        JackAndJillParticipant.id == JackAndJillPairing.follower_id
    )).join(JackAndJillScore)\
     .filter(JackAndJillPairing.round_id == final_round.id)\
     .group_by(JackAndJillParticipant.id)\
     .order_by(db.text('avg_score DESC')).all()
    
    return render_template('jack_and_jill/leaderboard.html',
                         competition=competition,
                         scores=scores)
