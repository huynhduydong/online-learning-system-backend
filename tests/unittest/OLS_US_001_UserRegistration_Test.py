"""
Unit Tests for User Story OLS-US-001: User Registration
Tests User Registration functionality including email confirmation

Test Coverage:
- Successful registration with email confirmation
- Duplicate email validation
- Password strength validation
- Email format validation
- Required fields validation
- Role assignment (Student/Instructor)
- Email confirmation flow
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
    """
    Test User Story OLS-US-001: User Registration
    
    Acceptance Criteria:
    1. Given visitor chưa có tài khoản When điền form hợp lệ Then tài khoản được tạo và nhận email xác nhận
    2. Given nhập email đã tồn tại When submit form Then hiển thị lỗi "Email đã được sử dụng"
    3. Given nhập mật khẩu yếu When submit form Then yêu cầu mật khẩu mạnh hơn
    """
    
    def test_successful_registration_with_email_confirmation(self, client):
        """
        Test Acceptance Criteria 1: Successful registration with email confirmation
        Given: visitor chưa có tài khoản
        When: điền form đăng ký với thông tin hợp lệ
        Then: tài khoản được tạo và nhận email xác nhận
        """
        data = {
            'email': 'newuser@example.com',
            'password': 'StrongPassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        # Verify response
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'user' in response_data
        assert response_data['user']['email'] == 'newuser@example.com'
        assert response_data['user']['role'] == 'student'  # Default role
        assert response_data['user']['is_verified'] is False  # Not verified yet
        assert 'email xác nhận' in response_data['message'].lower()
        
        # Verify user was created in database
        with client.application.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.first_name == 'New'
            assert user.last_name == 'User'
            assert user.role == UserRole.STUDENT
            assert user.confirmation_token is not None  # Token generated
            assert user.confirmed_at is None  # Not confirmed yet
    
    def test_duplicate_email_registration(self, client, sample_user):
        """
        Test Acceptance Criteria 2: Duplicate email validation
        Given: nhập email đã tồn tại
        When: submit form đăng ký
        Then: hệ thống hiển thị lỗi "Email đã được sử dụng"
        """
        data = {
            'email': 'test@example.com',  # Same as sample_user
            'password': 'StrongPassword123',
            'first_name': 'Another',
            'last_name': 'User'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        # Verify error response
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Email đã được sử dụng' in str(response_data['details'])
    
    def test_weak_password_registration(self, client):
        """
        Test Acceptance Criteria 3: Password strength validation
        Given: nhập mật khẩu yếu (< 8 ký tự)
        When: submit form
        Then: hệ thống yêu cầu mật khẩu mạnh hơn
        """
        # Test 1: Too short password
        data = {
            'email': 'weakpass1@example.com',
            'password': 'weak',  # Too short
            'first_name': 'Weak',
            'last_name': 'Password'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'password' in str(response_data['details']).lower()
        
        # Test 2: No uppercase letter
        data['email'] = 'weakpass2@example.com'
        data['password'] = 'nouppercase123'
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        
        # Test 3: No lowercase letter
        data['email'] = 'weakpass3@example.com'
        data['password'] = 'NOLOWERCASE123'
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        
        # Test 4: No numbers
        data['email'] = 'weakpass4@example.com'
        data['password'] = 'NoNumbersHere'
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
    
    def test_invalid_email_format(self, client):
        """Test registration with invalid email format"""
        data = {
            'email': 'invalid-email',  # Invalid format
            'password': 'StrongPassword123',
            'first_name': 'Invalid',
            'last_name': 'Email'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'email' in str(response_data['details']).lower()
    
    def test_missing_required_fields(self, client):
        """Test registration with missing required fields"""
        # Missing email
        data = {
            'password': 'StrongPassword123',
            'first_name': 'Missing',
            'last_name': 'Email'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        
        # Missing password
        data = {
            'email': 'missing@example.com',
            'first_name': 'Missing',
            'last_name': 'Password'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
    
    def test_instructor_role_registration(self, client):
        """Test registration with instructor role"""
        data = {
            'email': 'instructor@example.com',
            'password': 'StrongPassword123',
            'first_name': 'New',
            'last_name': 'Instructor',
            'role': 'instructor'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['user']['role'] == 'instructor'
        
        # Verify in database
        with client.application.app_context():
            user = User.query.filter_by(email='instructor@example.com').first()
            assert user.role == UserRole.INSTRUCTOR
    
    def test_default_student_role(self, client):
        """Test that default role is student when not specified"""
        data = {
            'email': 'defaultrole@example.com',
            'password': 'StrongPassword123',
            'first_name': 'Default',
            'last_name': 'Role'
            # No role specified
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['user']['role'] == 'student'  # Default role
        
        # Verify in database
        with client.application.app_context():
            user = User.query.filter_by(email='defaultrole@example.com').first()
            assert user.role == UserRole.STUDENT


class TestEmailConfirmation:
    """Test email confirmation functionality for User Registration"""
    
    def test_email_confirmation_success(self, client, app):
        """Test successful email confirmation"""
        # First register a user
        data = {
            'email': 'confirm@example.com',
            'password': 'StrongPassword123',
            'first_name': 'Confirm',
            'last_name': 'User'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        
        # Get confirmation token from database
        with app.app_context():
            user = User.query.filter_by(email='confirm@example.com').first()
            token = user.confirmation_token
            assert token is not None
            assert user.confirmed_at is None
        
        # Confirm email
        response = client.get(f'/api/auth/confirm-email/{token}')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'xác nhận thành công' in response_data['message']
        
        # Verify user is confirmed
        with app.app_context():
            user = User.query.filter_by(email='confirm@example.com').first()
            assert user.confirmed_at is not None
            assert user.is_verified is True
            assert user.confirmation_token is None  # Token cleared
    
    def test_invalid_confirmation_token(self, client):
        """Test confirmation with invalid token"""
        response = client.get('/api/auth/confirm-email/invalid-token')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Invalid or expired' in response_data['error']
    
    def test_already_confirmed_email(self, client, app):
        """Test confirmation of already confirmed email"""
        # Register and confirm user
        data = {
            'email': 'already@example.com',
            'password': 'StrongPassword123',
            'first_name': 'Already',
            'last_name': 'Confirmed'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(data),
                   content_type='application/json')
        
        # Get token and confirm
        with app.app_context():
            user = User.query.filter_by(email='already@example.com').first()
            token = user.confirmation_token
        
        client.get(f'/api/auth/confirm-email/{token}')
        
        # Try to confirm again
        response = client.get(f'/api/auth/confirm-email/{token}')
        
        assert response.status_code == 200  # Should still return success
        response_data = json.loads(response.data)
        assert 'đã được xác nhận trước đó' in response_data['message']
    
    def test_resend_confirmation_email(self, client, app):
        """Test resending confirmation email"""
        # Register user
        data = {
            'email': 'resend@example.com',
            'password': 'StrongPassword123',
            'first_name': 'Resend',
            'last_name': 'User'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(data),
                   content_type='application/json')
        
        # Resend confirmation
        resend_data = {'email': 'resend@example.com'}
        response = client.post('/api/auth/resend-confirmation',
                             data=json.dumps(resend_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'gửi lại' in response_data['message']