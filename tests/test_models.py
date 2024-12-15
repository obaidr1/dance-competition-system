import pytest
from models import User, Dancer, Competition, db
from datetime import datetime

def test_create_user(app):
    """Test user creation"""
    with app.app_context():
        user = User(
            email='test@example.com',
            password_hash='hashed_password',
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        
        saved_user = User.query.filter_by(email='test@example.com').first()
        assert saved_user is not None
        assert saved_user.email == 'test@example.com'
        assert saved_user.is_admin == False

def test_create_dancer(app):
    """Test dancer creation"""
    with app.app_context():
        dancer = Dancer(
            name='John Doe',
            date_of_birth=datetime(2000, 1, 1),
            gender='M',
            contact_email='john@example.com'
        )
        db.session.add(dancer)
        db.session.commit()
        
        saved_dancer = Dancer.query.filter_by(name='John Doe').first()
        assert saved_dancer is not None
        assert saved_dancer.name == 'John Doe'
        assert saved_dancer.gender == 'M'

def test_create_competition(app):
    """Test competition creation"""
    with app.app_context():
        competition = Competition(
            name='Test Competition',
            date=datetime(2024, 1, 1),
            location='Test Location',
            registration_open=True
        )
        db.session.add(competition)
        db.session.commit()
        
        saved_competition = Competition.query.filter_by(name='Test Competition').first()
        assert saved_competition is not None
        assert saved_competition.name == 'Test Competition'
        assert saved_competition.registration_open == True
