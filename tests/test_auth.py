import pytest
from models import User, db
from werkzeug.security import generate_password_hash

def test_login_page(client):
    """Test that the login page loads"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_successful_login(client, app):
    """Test successful login with correct credentials"""
    # Create a test user
    with app.app_context():
        user = User(
            email='test@example.com',
            password_hash=generate_password_hash('password'),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
    
    # Try to login
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Welcome' in response.data or b'Dashboard' in response.data

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
