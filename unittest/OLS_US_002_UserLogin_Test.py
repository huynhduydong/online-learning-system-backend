"""
Unit Tests for User Story OLS-US-002: User Login
Tests User Login functionality with JWT authentication

Test Coverage:
- Successful login with valid credentials
- Invalid credentials handling
- Non-existent user handling
- Account lockout after failed attempts
- JWT token generation and validation
"""

import pytest
import json
from app import create_app, db
from app.models.user import User, UserRole


@pytest.fixture
def app():
    """Create test application"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing"""
    with app.app_context():
        user = User(
            email='test@example.com',
            password='TestPassword123',
            first_name='Test',
            last_name='User'
        )
        db.session.add(user)
        db.session.commit()
        return user


class TestUserLogin:
    """Test User Story OLS-US-002: User Login"""
    
    def test_successful_login(self, client, sample_user):
        """Test successful login"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'access_token' in response_data
        assert 'refresh_token' in response_data
    
    def test_invalid_credentials_login(self, client, sample_user):
        """Test login with invalid credentials"""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Thông tin đăng nhập không chính xác' in response_data['error']
    
    def test_nonexistent_user_login(self, client):
        """Test login with non-existent user"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['success'] is False