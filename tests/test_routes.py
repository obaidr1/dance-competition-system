import pytest
from models import User, Competition, db
from datetime import datetime
from werkzeug.security import generate_password_hash

def test_index_route(client):
    """Test the index route"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome' in response.data

def test_competitions_route_unauthorized(client):
    """Test that unauthorized users are redirected from competitions route"""
    response = client.get('/competitions', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

def test_competitions_route_authorized(client, app):
    """Test that authorized users can access competitions route"""
    with app.app_context():
        # Create a regular user
        user = User(
            username='testuser',
            email='test@example.com',
            password=generate_password_hash('password'),
            role='dancer',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        
        # Login as user
        client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password'
        })
        
        response = client.get('/competitions')
        assert response.status_code == 200
        assert b'Competitions' in response.data

def test_admin_route_unauthorized(client):
    """Test that unauthorized users cannot access admin routes"""
    response = client.get('/admin', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

def test_admin_route_authorized(client, app):
    """Test that admin users can access admin routes"""
    with app.app_context():
        # Create an admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('password'),
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        
        # Login as admin
        client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'password'
        })
        
        response = client.get('/admin')
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data
