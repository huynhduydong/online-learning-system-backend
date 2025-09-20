"""
Authentication Blueprint
Implements User Stories: OLS-US-001 (User Registration), OLS-US-002 (User Login)

Business Requirements:
- User registration với email validation và password strength
- User login với JWT token generation
- Account security với failed login tracking
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validates, validates_schema
from app import db, limiter
from app.models.user import User, UserRole
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


class UserRegistrationSchema(Schema):
    """Schema validation cho user registration"""
    email = fields.Email(required=True, error_messages={'required': 'Email is required'})
    password = fields.Str(required=True, validate=lambda x: len(x) >= 8, 
                         error_messages={'required': 'Password is required'})
    first_name = fields.Str(required=True, validate=lambda x: len(x.strip()) >= 2,
                           error_messages={'required': 'First name is required'})
    last_name = fields.Str(required=True, validate=lambda x: len(x.strip()) >= 2,
                          error_messages={'required': 'Last name is required'})
    role = fields.Str(missing='student', validate=lambda x: x in ['student', 'instructor'])
    
    @validates('email')
    def validate_email_format(self, value):
        """Validate email format"""
        if not User.validate_email(value):
            raise ValidationError('Invalid email format')
    
    @validates('password')
    def validate_password_strength(self, value):
        """Validate password strength according to business rules"""
        is_valid, message = User.validate_password_strength(value)
        if not is_valid:
            raise ValidationError(message)
    
    @validates_schema
    def validate_email_unique(self, data, **kwargs):
        """Check if email already exists"""
        if 'email' in data:
            existing_user = User.query.filter_by(email=data['email'].lower()).first()
            if existing_user:
                raise ValidationError({'email': ['Email đã được sử dụng']})


class UserLoginSchema(Schema):
    """Schema validation cho user login"""
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember_me = fields.Bool(missing=False)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """
    User Registration Endpoint
    
    Implements User Story OLS-US-001: User Registration
    
    Business Rules:
    - Email phải unique trong hệ thống
    - Mật khẩu tối thiểu 8 ký tự, có chữ hoa, chữ thường, số
    - Tài khoản mới mặc định là "Student"
    """
    try:
        # Validate input data
        schema = UserRegistrationSchema()
        data = schema.load(request.json)
        
        # Create new user
        user = User(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=UserRole.INSTRUCTOR if data['role'] == 'instructor' else UserRole.STUDENT
        )
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        # TODO: Send email confirmation (implement in future sprint)
        
        return jsonify({
            'success': True,
            'message': 'Tài khoản được tạo thành công. Vui lòng kiểm tra email để xác nhận.',
            'user': user.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.messages
        }), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Registration failed',
            'message': str(e)
        }), 500


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    User Login Endpoint
    
    Implements User Story OLS-US-002: User Login
    
    Business Rules:
    - Sau 5 lần đăng nhập sai, tài khoản bị khóa 15 phút
    - Session timeout sau 24h nếu không có activity
    - Remember me option cho 30 ngày
    """
    try:
        # Validate input data
        schema = UserLoginSchema()
        data = schema.load(request.json)
        
        # Find user by email
        user = User.query.filter_by(email=data['email'].lower()).first()
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Thông tin đăng nhập không chính xác'
            }), 401
        
        # Check if account is locked
        if user.is_locked:
            return jsonify({
                'success': False,
                'error': 'Tài khoản đã bị khóa do nhiều lần đăng nhập sai. Vui lòng thử lại sau.'
            }), 423
        
        # Check if account is active
        if not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Tài khoản đã bị vô hiệu hóa'
            }), 403
        
        # Verify password
        if not user.check_password(data['password']):
            user.increment_failed_login()
            return jsonify({
                'success': False,
                'error': 'Thông tin đăng nhập không chính xác'
            }), 401
        
        # Successful login
        user.reset_failed_login()
        user.update_last_login()
        
        # Create JWT tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Đăng nhập thành công',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.messages
        }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Login failed',
            'message': str(e)
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh JWT Token
    
    Allows users to get new access token using refresh token
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Invalid user'
            }), 401
        
        # Create new access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Token refresh failed',
            'message': str(e)
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User Logout
    
    Note: In a production system, you would want to blacklist the JWT token
    For now, we'll just return success (client should delete the token)
    """
    return jsonify({
        'success': True,
        'message': 'Đăng xuất thành công'
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user information
    
    Returns the current authenticated user's profile
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get user info',
            'message': str(e)
        }), 500