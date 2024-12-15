import pytest
from models import User, Dancer, Competition, db
from datetime import datetime

def test_create_user(app):
    """Test user creation"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password='hashed_password',
            role='dancer',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        
        saved_user = User.query.filter_by(email='test@example.com').first()
        assert saved_user is not None
        assert saved_user.email == 'test@example.com'
        assert saved_user.role == 'dancer'

def test_create_dancer(app):
    """Test dancer creation"""
    with app.app_context():
        # First create a user for the dancer
        user = User(
            username='johndoe',
            email='john@example.com',
            password='password',
            role='dancer',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        dancer = Dancer(
            user_id=user.id,
            first_name='John',
            last_name='Doe',
            date_of_birth=datetime(2000, 1, 1).date(),
            level='Newcomer',
            phone='1234567890'
        )
        db.session.add(dancer)
        db.session.commit()
        
        saved_dancer = Dancer.query.filter_by(first_name='John').first()
        assert saved_dancer is not None
        assert saved_dancer.first_name == 'John'
        assert saved_dancer.last_name == 'Doe'
        assert saved_dancer.level == 'Newcomer'

def test_create_competition(app):
    """Test competition creation"""
    with app.app_context():
        competition = Competition(
            name='Test Competition',
            date=datetime(2024, 1, 1),
            status='pending',
            registration_open=True
        )
        db.session.add(competition)
        db.session.commit()
        
        saved_competition = Competition.query.filter_by(name='Test Competition').first()
        assert saved_competition is not None
        assert saved_competition.name == 'Test Competition'
        assert saved_competition.registration_open == True
        assert saved_competition.status == 'pending'
