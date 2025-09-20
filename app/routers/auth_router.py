"""
Authentication Blueprint
Implements User Stories: OLS-US-001 (User Registration), OLS-US-002 (User Login)

Business Requirements:
- User registration với email validation và password strength
- User login với JWT token generation
- Account security với failed login tracking
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import create_refresh_token, jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app import limiter
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.validators.auth import UserRegistrationSchema, UserLoginSchema
from app.utils.response import (
    success_response, 
    error_response, 
    validation_error_response,
    created_response
)
from app.exceptions.base import (
    ValidationException,
    AuthenticationException,
    BusinessLogicException,
    ExternalServiceException
)

auth_router = Blueprint('auth', __name__)





@auth_router.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """
    User Registration Endpoint
    
    Implements: OLS-US-001 (User Registration)
    
    Business Requirements:
    - Validate email format và uniqueness
    - Validate password strength (minimum 8 characters)
    - Validate required fields (first_name, last_name)
    - Send confirmation email
    - Return success response với user info
    
    Rate Limiting: 20 requests per minute per IP
    """
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input using schema
        schema = UserRegistrationSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Register user using service
        user = AuthService.register_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data.get('role', 'student')
        )
        
        # Return success response
        return created_response(
            message='Registration successful! Please check your email to confirm your account.',
            data={
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role.value
                }
            }
        )
        
    except ValidationException as e:
        return validation_error_response(e.message, e.errors)
    except BusinessLogicException as e:
        return error_response(e.message, 400)
    except ExternalServiceException as e:
        current_app.logger.error(f"External service error during registration: {e}")
        # Still return success since user was created, just email failed
        return created_response(
            message='Registration successful! However, confirmation email could not be sent. Please contact support.',
            data={
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role.value
                }
            }
        )
    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        return error_response('Registration failed. Please try again.', 500)


@auth_router.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    User Login Endpoint
    
    Implements: OLS-US-002 (User Login)
    
    Business Requirements:
    - Validate email và password
    - Check account status (active, confirmed, not locked)
    - Generate JWT tokens (access + refresh)
    - Track failed login attempts
    - Update last login timestamp
    
    Rate Limiting: 10 requests per minute per IP
    """
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input using schema
        schema = UserLoginSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Login user using service
        login_result = AuthService.login_user(
            email=validated_data['email'],
            password=validated_data['password'],
            remember_me=validated_data.get('remember_me', False)
        )
        
        # Return success response
        return success_response(
            message='Login successful',
            data=login_result
        )
        
    except AuthenticationException as e:
        return error_response(e.message, 401)
    except BusinessLogicException as e:
        # Handle account locked, email not confirmed, etc.
        status_code = 423 if 'locked' in e.message.lower() else 403
        return error_response(e.message, status_code)
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return error_response('Login failed. Please try again.', 500)


@auth_router.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Token Refresh Endpoint
    
    Implements: OLS-US-003 (Token Refresh)
    
    Business Requirements:
    - Validate refresh token
    - Generate new access token
    - Maintain user session
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return error_response('User not found or inactive', 404)
        
        # Create new access token
        new_access_token = create_access_token(identity=str(user.id))
        
        return success_response(
            message='Token refreshed successfully',
            data={
                'access_token': new_access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role.value,
                    'avatar_url': user.get_avatar_url()
                }
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {e}")
        return error_response('Token refresh failed. Please try again.', 500)


@auth_router.route('/logout', methods=['POST'])
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


@auth_router.route('/confirm-email/<token>', methods=['GET'])
def confirm_email(token):
    """
    Email Confirmation Endpoint
    
    Implements: OLS-US-004 (Email Confirmation)
    
    Business Requirements:
    - Validate confirmation token
    - Activate user account
    - Update email confirmation status
    """
    try:
        # Confirm email using service
        result = AuthService.confirm_email(token)
        
        return success_response(
            message='Email confirmed successfully',
            data=result
        )
        
    except ValidationException as e:
        return validation_error_response(e.message, {'token': [e.message]})
    except BusinessLogicException as e:
        # Handle already confirmed case
        if 'already confirmed' in e.message.lower():
            return success_response(
                message='Email already confirmed',
                data={'status': 'already_confirmed'}
            )
        return error_response(e.message, 400)
    except Exception as e:
        current_app.logger.error(f"Email confirmation error: {e}")
        return error_response('Email confirmation failed. Please try again.', 500)


@auth_router.route('/resend-confirmation', methods=['POST'])
@limiter.limit("3 per minute")
def resend_confirmation():
    """
    Resend Email Confirmation Endpoint
    
    Implements: OLS-US-005 (Resend Confirmation)
    
    Business Requirements:
    - Validate email exists
    - Check if already confirmed
    - Send new confirmation email
    - Rate limit to prevent spam
    
    Rate Limiting: 3 requests per minute per IP
    """
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return validation_error_response('Email is required', {'email': ['Email is required']})
        
        email = data['email'].lower().strip()
        
        # Resend confirmation using service
        result = AuthService.resend_confirmation_email(email)
        
        return success_response(
            message='If the email exists, a confirmation link has been sent',
            data=result
        )
        
    except BusinessLogicException as e:
        return error_response(e.message, 400)
    except Exception as e:
        current_app.logger.error(f"Resend confirmation error: {e}")
        return error_response('Failed to resend confirmation. Please try again.', 500)


@auth_router.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user information
    
    Returns the current authenticated user's profile
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
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