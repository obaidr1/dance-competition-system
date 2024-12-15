import pytest
from app import app as flask_app
from models import db
import os

@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    
    # Create tables
    with flask_app.app_context():
        db.create_all()
    
    yield flask_app
    
    # Clean up
    with flask_app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client):
    """A test client with authentication helpers"""
    class AuthClient:
        def __init__(self, client):
            self._client = client
            
        def login(self, email="test@example.com", password="password"):
            return self._client.post('/login', data={
                'email': email,
                'password': password
            }, follow_redirects=True)
            
        def logout(self):
            return self._client.get('/logout', follow_redirects=True)
            
    return AuthClient(client)
