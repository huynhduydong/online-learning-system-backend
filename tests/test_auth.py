"""
Tests for Authentication endpoints
Tests User Stories: OLS-US-001, OLS-US-002, OLS-US-003
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


class TestUserRegistration:
    """Test User Story OLS-US-001: User Registration"""
    
    def test_successful_registration(self, client):
        """Test successful user registration"""
        data = {
            'email': 'newuser@example.com',
            'password': 'StrongPassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'user' in response_data
        assert response_data['user']['email'] == 'newuser@example.com'
    
    def test_duplicate_email_registration(self, client, sample_user):
        """Test registration with existing email"""
        data = {
            'email': 'test@example.com',  # Same as sample_user
            'password': 'StrongPassword123',
            'first_name': 'Another',
            'last_name': 'User'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Email đã được sử dụng' in str(response_data['details'])
    
    def test_weak_password_registration(self, client):
        """Test registration with weak password"""
        data = {
            'email': 'newuser@example.com',
            'password': 'weak',  # Too short, no uppercase, no numbers
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False


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


class TestUserProfile:
    """Test User Story OLS-US-003: User Profile Management"""
    
    def get_auth_headers(self, client, user_email='test@example.com', password='TestPassword123'):
        """Helper method to get authentication headers"""
        login_data = {
            'email': user_email,
            'password': password
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        response_data = json.loads(response.data)
        token = response_data['access_token']
        
        return {'Authorization': f'Bearer {token}'}
    
    def test_get_profile(self, client, sample_user):
        """Test getting user profile"""
        headers = self.get_auth_headers(client)
        
        response = client.get('/api/users/profile', headers=headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'profile' in response_data
        assert response_data['profile']['email'] == 'test@example.com'
    
    def test_update_profile(self, client, sample_user):
        """Test updating user profile"""
        headers = self.get_auth_headers(client)
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = client.put('/api/users/profile',
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['profile']['first_name'] == 'Updated'
        assert response_data['profile']['last_name'] == 'Name'
    
    def test_get_dashboard(self, client, sample_user):
        """Test getting user dashboard"""
        headers = self.get_auth_headers(client)
        
        response = client.get('/api/users/dashboard', headers=headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'dashboard' in response_data
        assert 'user' in response_data['dashboard']
        assert 'statistics' in response_data['dashboard']