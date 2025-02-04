from flask_login import UserMixin
from models.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    city = db.Column(db.String(100))
    dance_role = db.Column(db.String(20))  # leader or follower
    level = db.Column(db.String(20))  # novice, intermediate, advanced
    role = db.Column(db.String(20), default='dancer')  # dancer, judge, organizer, admin
    instagram = db.Column(db.String(100))
    profile_picture = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def can_compete_in(self, level):
        # Add your level validation logic here
        return True
        
    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"
        
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_judge(self):
        return self.role == 'judge'
        
    @property
    def is_organizer(self):
        return self.role == 'organizer'
        
    @property
    def is_dancer(self):
        return self.role == 'dancer'
