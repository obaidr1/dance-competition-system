from datetime import datetime
from models.database import db

class Competition(db.Model):
    __tablename__ = 'competitions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    dance_style = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)  
    description = db.Column(db.Text)  
    competition_type = db.Column(db.String(50), default='jack_and_jill')  
    max_rounds = db.Column(db.Integer)  
    rotation_size = db.Column(db.Integer)  
    pairs_per_final = db.Column(db.Integer)  
    max_participants = db.Column(db.Integer)
    registration_open = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='upcoming')  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'))  
    scoring_dimensions = db.Column(db.Text)  
    banner = db.Column(db.String(255))  
    participant_list_locked = db.Column(db.Boolean, default=False)  
    
    # Relationships
    participants = db.relationship('CompetitionParticipant', backref='competition')
    judges = db.relationship('CompetitionJudge', backref='competition')
    rounds = db.relationship('CompetitionRound', backref='competition')
    organizer = db.relationship('User', backref='organized_competitions')
    judge_assignments = db.relationship('CompetitionJudge', backref='judge_competition')  

    def set_scoring_dimensions(self, dimensions):
        self.scoring_dimensions = ','.join(dimensions) if dimensions else ''

    def get_scoring_dimensions(self):
        return self.scoring_dimensions.split(',') if self.scoring_dimensions else []

    def check_ratio(self):
        leader_count = self.get_leader_count()
        follower_count = self.get_follower_count()
        return leader_count >= follower_count

    def get_leader_count(self):
        return sum(1 for participant in self.participants if participant.user.dance_role == 'leader')

    def get_follower_count(self):
        return sum(1 for participant in self.participants if participant.user.dance_role == 'follower')

    def update_tiers(self):
        leaders = [p for p in self.participants if p.user.dance_role == 'leader']
        followers = [p for p in self.participants if p.user.dance_role == 'follower']
        
        if len(leaders) > len(followers):
            pass  
        elif len(followers) > len(leaders):
            pass  
        else:
            pass  

class CompetitionParticipant(db.Model):
    __tablename__ = 'competition_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    eliminated_in_round = db.Column(db.Integer)
    dancer_number = db.Column(db.Integer)

    user = db.relationship('User', backref='competition_participants')

class CompetitionJudge(db.Model):
    __tablename__ = 'competition_judges'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_head_judge = db.Column(db.Boolean, default=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

class CompetitionRound(db.Model):
    __tablename__ = 'competition_rounds'
    
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'))
    round_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
