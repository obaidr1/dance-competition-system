from datetime import datetime
from models.database import db

class JackAndJillCompetition(db.Model):
    __tablename__ = 'jack_and_jill_competitions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    max_participants = db.Column(db.Integer)  # Null means unlimited
    num_rounds = db.Column(db.Integer, nullable=False)
    current_round = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='setup')  # setup, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    head_judge_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    participants = db.relationship('JackAndJillParticipant', backref='competition')
    rounds = db.relationship('JackAndJillRound', backref='competition')
    judges = db.relationship('JackAndJillJudge', backref='competition')

class JackAndJillParticipant(db.Model):
    __tablename__ = 'jack_and_jill_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('jack_and_jill_competitions.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    dancer_number = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'leader' or 'follower'
    is_active = db.Column(db.Boolean, default=True)
    is_substitute = db.Column(db.Boolean, default=False)
    eliminated_in_round = db.Column(db.Integer)

class JackAndJillRound(db.Model):
    __tablename__ = 'jack_and_jill_rounds'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('jack_and_jill_competitions.id'))
    round_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    couples_per_heat = db.Column(db.Integer, default=4)
    rotation_size = db.Column(db.Integer, default=2)  # How many spots followers rotate

class JackAndJillPairing(db.Model):
    __tablename__ = 'jack_and_jill_pairings'
    
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('jack_and_jill_rounds.id'))
    leader_id = db.Column(db.Integer, db.ForeignKey('jack_and_jill_participants.id'))
    follower_id = db.Column(db.Integer, db.ForeignKey('jack_and_jill_participants.id'))
    heat_number = db.Column(db.Integer, nullable=False)
    rotation_number = db.Column(db.Integer, nullable=False)

class JackAndJillJudge(db.Model):
    __tablename__ = 'jack_and_jill_judges'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('jack_and_jill_competitions.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_head_judge = db.Column(db.Boolean, default=False)

class JackAndJillScore(db.Model):
    __tablename__ = 'jack_and_jill_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    pairing_id = db.Column(db.Integer, db.ForeignKey('jack_and_jill_pairings.id'))
    judge_id = db.Column(db.Integer, db.ForeignKey('jack_and_jill_judges.id'))
    musicality = db.Column(db.Integer)
    connection = db.Column(db.Integer)
    styling = db.Column(db.Integer)
    footwork = db.Column(db.Integer)
    impression = db.Column(db.Integer)
    notes = db.Column(db.Text)

class JackAndJillCriteria(db.Model):
    __tablename__ = 'jack_and_jill_criteria'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('jack_and_jill_competitions.id'))
    name = db.Column(db.String(50), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    weight = db.Column(db.Float, default=1.0)
