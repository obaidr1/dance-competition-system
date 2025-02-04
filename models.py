from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db

# Association tables for many-to-many relationships
user_competitions = db.Table('user_competitions',
    db.Column('competition_id', db.Integer, db.ForeignKey('competitions.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """User model for authentication and role management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    city = db.Column(db.String(100))
    dance_role = db.Column(db.String(20))
    level = db.Column(db.String(20))
    _admin = db.Column('is_admin', db.Boolean, default=False, nullable=False)
    _organizer = db.Column('is_organizer', db.Boolean, default=False, nullable=False)
    _judge = db.Column('is_judge', db.Boolean, default=False, nullable=False)
    _dancer = db.Column('is_dancer', db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Beziehungen
    participations = db.relationship('CompetitionParticipant', back_populates='participant')
    judging = db.relationship('CompetitionJudge', back_populates='judge')
    organized_competitions = db.relationship('Competition', backref='organizer')

    @property
    def is_admin(self):
        return self._admin

    @is_admin.setter
    def is_admin(self, value):
        self._admin = value

    @property
    def is_organizer(self):
        return self._organizer

    @is_organizer.setter
    def is_organizer(self, value):
        self._organizer = value

    @property
    def is_judge(self):
        return self._judge

    @is_judge.setter
    def is_judge(self, value):
        self._judge = value

    @property
    def is_dancer(self):
        return self._dancer

    @is_dancer.setter
    def is_dancer(self, value):
        self._dancer = value

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_assigned_competitions(self):
        """Get competitions based on user role"""
        if self.is_organizer:
            # For organizers, return competitions they created
            return Competition.query.filter_by(organizer_id=self.id).all()
        elif self.is_judge:
            # For judges, return competitions they are assigned to judge
            judge_assignments = CompetitionJudge.query.filter_by(user_id=self.id).all()
            return [assignment.competition for assignment in judge_assignments]
        elif self.is_dancer:
            # For dancers, return competitions they are participating in
            participations = CompetitionParticipant.query.filter_by(user_id=self.id).all()
            return [participation.competition for participation in participations]
        else:
            return []

    def __repr__(self):
        return f'<User {self.email}>'

class Competition(db.Model):
    __tablename__ = 'competitions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    registration_open = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    organizer = db.relationship('User', foreign_keys=[organizer_id], backref='organized_competitions')
    judges = db.relationship('CompetitionJudge', 
                           back_populates='competition',
                           cascade='all, delete-orphan',
                           overlaps="judge_assignments")
    judge_assignments = db.relationship('CompetitionJudge',
                                      overlaps="judges",
                                      viewonly=True)
    participants = db.relationship('CompetitionParticipant', 
                                 back_populates='competition',
                                 cascade='all, delete-orphan')
    rounds = db.relationship('Round', 
                           back_populates='competition',
                           cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Competition {self.name}>'

class CompetitionJudge(db.Model):
    __tablename__ = 'competition_judges'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_head_judge = db.Column(db.Boolean, default=False)
    
    # Relationships
    competition = db.relationship('Competition', 
                                back_populates='judges',
                                overlaps="judge_assignments")
    judge = db.relationship('User', back_populates='judging')
    scores = db.relationship('Score', 
                           back_populates='judge',
                           cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CompetitionJudge competition_id={self.competition_id} user_id={self.user_id}>'

class CompetitionParticipant(db.Model):
    __tablename__ = 'competition_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dancer_number = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    
    # Relationships
    competition = db.relationship('Competition', back_populates='participants')
    participant = db.relationship('User', back_populates='participations')
    heat_participants = db.relationship('HeatParticipant', back_populates='participant', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CompetitionParticipant {self.user.first_name} {self.user.last_name}>'

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    competition = db.relationship('Competition', foreign_keys=[competition_id], back_populates='rounds', lazy=True)
    scores = db.relationship('Score', back_populates='round', lazy=True)
    heats = db.relationship('Heat', back_populates='round', lazy=True)

    def __repr__(self):
        return f'<Round {self.round_number} of Competition {self.competition_id}>'

class Heat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    heat_number = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    round = db.relationship('Round', foreign_keys=[round_id], back_populates='heats', lazy=True)
    participants = db.relationship('HeatParticipant', back_populates='heat', lazy=True)

    def __repr__(self):
        return f'<Heat {self.heat_number} of Round {self.round_id}>'

class HeatParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    heat_id = db.Column(db.Integer, db.ForeignKey('heat.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('competition_participant.id'), nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('competition_participant.id'), nullable=True)
    
    # Relationships
    heat = db.relationship('Heat', foreign_keys=[heat_id], back_populates='participants', lazy=True)
    participant = db.relationship('CompetitionParticipant', foreign_keys=[participant_id], back_populates='heat_participants', lazy=True)
    partner = db.relationship('CompetitionParticipant', foreign_keys=[partner_id], back_populates='partner_participations', lazy=True)

    def __repr__(self):
        return f'<HeatParticipant {self.participant_id} in Heat {self.heat_id}>'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    judge_id = db.Column(db.Integer, db.ForeignKey('competition_judges.id'), nullable=False)
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
    round = db.relationship('Round', foreign_keys=[round_id], back_populates='scores', lazy=True)
    judge = db.relationship('CompetitionJudge', foreign_keys=[judge_id], back_populates='scores', lazy=True)
    participant = db.relationship('CompetitionParticipant', foreign_keys=[participant_id], back_populates='scores', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('round_id', 'judge_id', 'participant_id', name='unique_score_per_judge'),
    )

    def __repr__(self):
        return f'<Score {self.musicality} for {self.participant_id} by {self.judge_id}>'
