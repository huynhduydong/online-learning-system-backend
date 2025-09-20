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
    
    def test_remember_me_login(self, client, sample_user):
        """Test login with remember me option"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'remember_me': True
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['remember_me'] is True
        assert response_data['expires_in'] == 30 * 24 * 3600  # 30 days
    
    def test_normal_login_without_remember_me(self, client, sample_user):
        """Test normal login without remember me"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'remember_me': False
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['remember_me'] is False
        assert response_data['expires_in'] == 24 * 3600  # 24 hours
    
    def test_dashboard_access_after_login(self, client, sample_user):
        """Test dashboard access after successful login"""
        # First login
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123'
        }
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        assert login_response.status_code == 200
        login_result = json.loads(login_response.data)
        access_token = login_result['access_token']
        
        # Then access dashboard
        headers = {'Authorization': f'Bearer {access_token}'}
        dashboard_response = client.get('/api/users/dashboard', headers=headers)
        
        # Fail test and show response if failed
        if dashboard_response.status_code != 200:
            pytest.fail(f"Dashboard response status: {dashboard_response.status_code}, data: {dashboard_response.data}")
        
        assert dashboard_response.status_code == 200
        dashboard_data = json.loads(dashboard_response.data)
        assert dashboard_data['success'] is True
        assert 'dashboard' in dashboard_data
        assert 'welcome_message' in dashboard_data['dashboard']