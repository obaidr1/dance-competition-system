from datetime import datetime
from models.database import db

class Round(db.Model):
    __tablename__ = 'rounds'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'))
    round_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    heats = db.relationship('Heat', backref='round')

class Heat(db.Model):
    __tablename__ = 'heats'
    
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('rounds.id'))
    heat_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    participants = db.relationship('HeatParticipant', backref='heat')

class HeatParticipant(db.Model):
    __tablename__ = 'heat_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    heat_id = db.Column(db.Integer, db.ForeignKey('heats.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('competition_participants.id'))
    role = db.Column(db.String(10))  # leader or follower
    position = db.Column(db.Integer)  # position in the heat
    
    # Relationships
    scores = db.relationship('Score', backref='heat_participant')

class Score(db.Model):
    __tablename__ = 'scores'
    
    id = db.Column(db.Integer, primary_key=True)
    heat_participant_id = db.Column(db.Integer, db.ForeignKey('heat_participants.id'))
    judge_id = db.Column(db.Integer, db.ForeignKey('competition_judges.id'))
    score = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
