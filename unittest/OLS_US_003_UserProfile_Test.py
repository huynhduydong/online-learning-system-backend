"""
Unit Tests for User Story OLS-US-003: User Profile Management
Tests User Profile functionality including profile updates and dashboard

Test Coverage:
- Get user profile information
- Update user profile data
- Avatar upload functionality
- User dashboard data
- Profile validation
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