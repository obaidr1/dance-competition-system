import pytest
from models import User, Competition, db
from datetime import datetime
from werkzeug.security import generate_password_hash

def test_index_page(client):
    """Test that the index page loads"""
    response = client.get('/')
    assert response.status_code == 200

def test_competitions_page(client):
    """Test that the competitions page loads"""
    response = client.get('/competitions')
    assert response.status_code == 200
    assert b'Competitions' in response.data

def test_admin_required(client, app):
    """Test that admin routes are protected"""
    response = client.get('/admin/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data  # Should redirect to login

def test_admin_access(client, app):
    """Test that admin users can access admin routes"""
    # Create an admin user
    with app.app_context():
        admin = User(
            email='admin@example.com',
            password_hash=generate_password_hash('adminpass'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
    
    # Login as admin
    client.post('/login', data={
        'email': 'admin@example.com',
        'password': 'adminpass'
    })
    
    # Try to access admin dashboard
    response = client.get('/admin/dashboard')
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data
