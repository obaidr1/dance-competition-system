from datetime import datetime
from enum import Enum
from app import db

class CompetitionStatus(Enum):
    DRAFT = "draft"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class CompetitionTier(Enum):
    TIER_1 = 1  # 5-15 competitors
    TIER_2 = 2  # 16-30 competitors
    TIER_3 = 3  # 30+ competitors

class CompetitionRound(Enum):
    PRELIMINARY = "preliminary"
    QUARTER_FINAL = "quarter_final"
    SEMI_FINAL = "semi_final"
    FINAL = "final"

class Competition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(CompetitionStatus), default=CompetitionStatus.DRAFT)
    dance_level = db.Column(db.Enum('NOVICE', 'INTERMEDIATE', 'ADVANCED', 'INVITATIONAL'), nullable=False)
    current_round = db.Column(db.Enum(CompetitionRound), nullable=True)
    
    # Organizer
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organizer = db.relationship('User', backref='organized_competitions')
    
    # Judges
    judges = db.relationship('User', secondary='competition_judges')
    
    # Participants
    leaders = db.relationship('User', secondary='competition_leaders')
    followers = db.relationship('User', secondary='competition_followers')
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def leader_tier(self):
        count = len(self.leaders)
        if count < 5:
            return None
        elif count <= 15:
            return CompetitionTier.TIER_1
        elif count <= 30:
            return CompetitionTier.TIER_2
        else:
            return CompetitionTier.TIER_3
    
    @property
    def follower_tier(self):
        count = len(self.followers)
        if count < 5:
            return None
        elif count <= 15:
            return CompetitionTier.TIER_1
        elif count <= 30:
            return CompetitionTier.TIER_2
        else:
            return CompetitionTier.TIER_3

    def can_start(self):
        """Check if competition can start based on rules"""
        min_participants = 5
        return (len(self.leaders) >= min_participants and 
                len(self.followers) >= min_participants and
                len(self.judges) > 0 and
                self.status == CompetitionStatus.REGISTRATION_CLOSED)

# Association tables
competition_judges = db.Table('competition_judges',
    db.Column('competition_id', db.Integer, db.ForeignKey('competition.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

competition_leaders = db.Table('competition_leaders',
    db.Column('competition_id', db.Integer, db.ForeignKey('competition.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

competition_followers = db.Table('competition_followers',
    db.Column('competition_id', db.Integer, db.ForeignKey('competition.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)
