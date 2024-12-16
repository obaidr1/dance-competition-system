import pytest
from models import User, db
from werkzeug.security import generate_password_hash

def test_login_page(client):
    """Test that the login page loads"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_successful_login(client, app):
    """Test successful login"""
    with app.app_context():
        # Create a test user
        hashed_password = generate_password_hash('password123')
        user = User(username='testuser', email='test@example.com', password=hashed_password, role='dancer')
        db.session.add(user)
        db.session.commit()
        
        # Try to login
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Competitions' in response.data  # We should see the competitions page

def test_failed_login(client):
    """Test login with incorrect credentials"""
    response = client.post('/login', data={
        'email': 'wrong@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data

def test_logout(auth_client):
    """Test logout functionality"""
    response = auth_client.logout()
    assert response.status_code == 200
    assert b'Login' in response.data
