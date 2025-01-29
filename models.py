from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
from flask import url_for
from dateutil import parser

db = SQLAlchemy()

# Association tables for many-to-many relationships
user_competitions = db.Table('user_competitions',
    db.Column('competition_id', db.Integer, db.ForeignKey('competition.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

competition_judges = db.Table('competition_judges',
    db.Column('competition_id', db.Integer, db.ForeignKey('competition.id'), primary_key=True),
    db.Column('judge_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    dance_role = db.Column(db.String(20), nullable=False)  # leader/follower
    level = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100))
    profile_picture = db.Column(db.String(200))
    instagram = db.Column(db.String(50))
    
    # User roles
    is_admin = db.Column(db.Boolean, default=False)
    is_organizer = db.Column(db.Boolean, default=False)
    is_judge = db.Column(db.Boolean, default=False)
    is_dancer = db.Column(db.Boolean, default=True)  # Default role
    is_temporary = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Email preferences
    email_notifications = db.Column(db.Boolean, default=True)
    
    # Relationships
    competitions_organized = db.relationship('Competition', 
                                          foreign_keys='Competition.organizer_id',
                                          lazy=True)
    judge_assignments = db.relationship('JudgeAssignment',
                                     foreign_keys='JudgeAssignment.judge_id',
                                     lazy=True)
    participations = db.relationship('CompetitionParticipant',
                                  foreign_keys='CompetitionParticipant.user_id',
                                  lazy=True)
    scores_given = db.relationship('Score', 
                               foreign_keys='Score.judge_id',
                               lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_role(self):
        if self.is_admin:
            return 'admin'
        elif self.is_organizer:
            return 'organizer'
        elif self.is_judge:
            return 'judge'
        else:
            return 'dancer'
            
    def can_create_competition(self):
        return self.is_admin or self.is_organizer
    
    def can_manage_competition(self, competition):
        return (self.is_admin or 
                self.is_organizer and competition.organizer_id == self.id)
    
    def can_judge_competition(self, competition):
        return (self.is_judge and 
                JudgeAssignment.query.filter_by(
                    judge_id=self.id,
                    competition_id=competition.id,
                    is_active=True
                ).first() is not None)
    
    def get_assigned_competitions(self):
        if self.is_judge:
            return (Competition.query
                   .join(JudgeAssignment)
                   .filter(JudgeAssignment.judge_id == self.id,
                          JudgeAssignment.is_active == True)
                   .all())
        elif self.is_organizer:
            return Competition.query.filter_by(organizer_id=self.id).all()
        else:
            return (Competition.query
                   .join(CompetitionParticipant)
                   .filter(CompetitionParticipant.user_id == self.id,
                          CompetitionParticipant.is_active == True)
                   .all())

class JudgeAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'), nullable=False)
    judge_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_head_judge = db.Column(db.Boolean, default=False)
    
    # Relationships
    competition = db.relationship('Competition', 
                              foreign_keys=[competition_id],
                              lazy=True)
    judge = db.relationship('User', 
                              foreign_keys=[judge_id],
                              lazy=True)
    
    __table_args__ = (
        db.UniqueConstraint('competition_id', 'judge_id', name='unique_judge_assignment'),
    )

class Competition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    max_participants = db.Column(db.Integer)
    leader_count = db.Column(db.Integer, default=0)
    follower_count = db.Column(db.Integer, default=0)
    
    # Competition status
    registration_open = db.Column(db.Boolean, default=True)
    is_started = db.Column(db.Boolean, default=False)
    is_completed = db.Column(db.Boolean, default=False)
    current_round = db.Column(db.Integer, default=0)
    
    # Organizer
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organizer = db.relationship('User', foreign_keys=[organizer_id], lazy=True)
    participants = db.relationship('CompetitionParticipant', lazy=True)
    rounds = db.relationship('Round', lazy=True)
    judge_assignments = db.relationship('JudgeAssignment', lazy=True)

    def __repr__(self):
        return f'<Competition {self.name}>'
    
    def can_start(self):
        """Check if competition can be started"""
        return (not self.is_started and 
                not self.is_completed and 
                self.date == datetime.today().date() and
                len(self.judges) > 0)
    
    def start_competition(self):
        """Start the competition"""
        if not self.can_start():
            return False, "Competition cannot be started"
        
        self.is_started = True
        self.current_round = 1
        self.registration_open = False
        db.session.commit()
        return True, "Competition started successfully"
    
    def complete_competition(self):
        """Complete the competition"""
        if not self.is_started:
            return False, "Competition has not been started"
        
        self.is_completed = True
        self.is_started = False
        db.session.commit()
        return True, "Competition completed successfully"

class CompetitionParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dancer_number = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    competition = db.relationship('Competition', foreign_keys=[competition_id], lazy=True)
    user = db.relationship('User', foreign_keys=[user_id], lazy=True)
    scores = db.relationship('Score', lazy=True)
    heat_participations = db.relationship('HeatParticipant', 
                                        foreign_keys='HeatParticipant.participant_id',
                                        lazy=True)
    partner_participations = db.relationship('HeatParticipant',
                                           foreign_keys='HeatParticipant.partner_id',
                                           lazy=True)

    def __repr__(self):
        return f'<CompetitionParticipant {self.user.first_name} {self.user.last_name}>'

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    competition = db.relationship('Competition', foreign_keys=[competition_id], lazy=True)
    scores = db.relationship('Score', lazy=True)
    heats = db.relationship('Heat', lazy=True)

    def __repr__(self):
        return f'<Round {self.round_number} of Competition {self.competition_id}>'

class Heat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    heat_number = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    round = db.relationship('Round', foreign_keys=[round_id], lazy=True)
    participants = db.relationship('HeatParticipant', lazy=True)

    def __repr__(self):
        return f'<Heat {self.heat_number} of Round {self.round_id}>'

class HeatParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    heat_id = db.Column(db.Integer, db.ForeignKey('heat.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('competition_participant.id'), nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('competition_participant.id'), nullable=True)
    
    # Relationships
    heat = db.relationship('Heat', foreign_keys=[heat_id], lazy=True)
    participant = db.relationship('CompetitionParticipant', foreign_keys=[participant_id], lazy=True)
    partner = db.relationship('CompetitionParticipant', foreign_keys=[partner_id], lazy=True)

    def __repr__(self):
        return f'<HeatParticipant {self.participant_id} in Heat {self.heat_id}>'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    judge_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('competition_participant.id'), nullable=False)
    
    # Scores
    musicality = db.Column(db.Float, nullable=False)
    technique = db.Column(db.Float, nullable=False)
    connection = db.Column(db.Float, nullable=False)
    style = db.Column(db.Float, nullable=False)
    performance = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    round = db.relationship('Round', foreign_keys=[round_id], lazy=True)
    judge = db.relationship('User', foreign_keys=[judge_id], lazy=True)
    participant = db.relationship('CompetitionParticipant', foreign_keys=[participant_id], lazy=True)

    __table_args__ = (
        db.UniqueConstraint('round_id', 'judge_id', 'participant_id', name='unique_score_per_judge'),
    )

    def __repr__(self):
        return f'<Score {self.musicality} for {self.participant_id} by {self.judge_id}>'
