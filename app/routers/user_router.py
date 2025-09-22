"""
Users Blueprint
Implements User Story: OLS-US-003 (User Profile Management)

Business Requirements:
- User xem và cập nhật thông tin profile
- Upload ảnh đại diện với validation
- User dashboard với enrolled courses
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from marshmallow import ValidationError
from werkzeug.utils import secure_filename
from PIL import Image
import os
from datetime import datetime

from app import db, limiter
from app.models.user import User
from app.services.user_service import UserService
from app.services.progress_service import ProgressService
from app.validators.user import UserProfileUpdateSchema, AvatarUploadSchema, UserSearchSchema
from app.utils.response import success_response, error_response, validation_error_response
from app.utils.security import sanitize_input, allowed_file, validate_image_file
from app.utils.auth import get_current_user
from app.exceptions.base import ValidationException, BusinessLogicException, APIException

user_router = Blueprint('users', __name__)

# Khởi tạo UserService instance
user_service = UserService()

















@user_router.route('/profile', methods=['GET'])
@limiter.limit("30 per minute")
@jwt_required()
def get_profile():
    """
    Get User Profile Endpoint
    
    Implements: OLS-US-003 (User Profile Management)
    
    Business Requirements:
    - Return complete user profile information
    - Include avatar URL if available
    - Validate user authentication
    - Rate limit to prevent abuse
    
    Rate Limiting: 30 requests per minute per user
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get user profile using service
        profile_data = user_service.get_user_profile(current_user_id)
        
        return success_response(
            message='Profile retrieved successfully',
            data={'user': profile_data}
        )
        
    except BusinessLogicException as e:
        return error_response(e.message, 404 if 'not found' in e.message.lower() else 403)
    except Exception as e:
        current_app.logger.error(f"Get profile error: {e}")
        return error_response('Failed to retrieve profile. Please try again.', 500)


@user_router.route('/profile', methods=['PUT'])
@limiter.limit("10 per minute")
@jwt_required()
def update_profile():
    """
    Update User Profile Endpoint
    
    Implements: OLS-US-003 (User Profile Management)
    
    Business Requirements:
    - Allow users to update their profile information
    - Validate input data
    - Sanitize user input for security
    - Update database with new information
    
    Rate Limiting: 10 requests per minute per user
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input using schema
        schema = UserProfileUpdateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Update profile using service
        result = user_service.update_user_profile(current_user_id, validated_data)
        
        return success_response(
            message='Profile updated successfully',
            data=result
        )
        
    except ValidationException as e:
        return validation_error_response(e.message, {'validation': [e.message]})
    except BusinessLogicException as e:
        return error_response(e.message, 404 if 'not found' in e.message.lower() else 403)
    except Exception as e:
        current_app.logger.error(f"Update profile error: {e}")
        return error_response('Failed to update profile. Please try again.', 500)


@user_router.route('/upload-avatar', methods=['POST'])
@limiter.limit("5 per minute")
@jwt_required()
def upload_avatar():
    """
    Upload User Avatar Endpoint
    
    Implements: OLS-US-003 (User Profile Management)
    
    Business Requirements:
    - Allow users to upload profile pictures
    - Validate file type and size
    - Process and resize images
    - Store securely with proper naming
    
    Rate Limiting: 5 requests per minute per user
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Check if file is present in request
        if 'avatar' not in request.files:
            return validation_error_response('No file provided', {'file': ['Avatar file is required']})
        
        file = request.files['avatar']
        
        # Check if file was actually selected
        if file.filename == '':
            return validation_error_response('No file selected', {'file': ['Please select a file']})
        
        # Validate file using schema
        schema = AvatarUploadSchema()
        try:
            validated_data = schema.load({'avatar': file})
        except ValidationError as err:
            return validation_error_response('File validation failed', err.messages)
        
        # Upload avatar using service
        result = user_service.upload_avatar(current_user_id, file)
        
        return success_response(
            message='Avatar uploaded successfully',
            data=result
        )
        
    except ValidationException as e:
        return validation_error_response(e.message, {'validation': [e.message]})
    except BusinessLogicException as e:
        return error_response(e.message, 404 if 'not found' in e.message.lower() else 403)
    except Exception as e:
        current_app.logger.error(f"Avatar upload error: {e}")
        return error_response('Failed to upload avatar. Please try again.', 500)


@user_router.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """
    Get User Dashboard
    
    Implements: OLS-US-002 (Dashboard redirect after login)
    Implements: OLS-US-003 (User dashboard with course overview)
    
    Returns dashboard data including enrolled courses and progress
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get dashboard data using service
        dashboard_data = user_service.get_user_dashboard_data(current_user_id)
        
        return success_response(
            message='Dashboard data retrieved successfully',
            data=dashboard_data
        )
        
    except BusinessLogicException as e:
        return error_response(e.message, 404 if 'not found' in e.message.lower() else 403)
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {e}")
        return error_response('Failed to load dashboard. Please try again.', 500)


@user_router.route('/remove-avatar', methods=['DELETE'])
@limiter.limit("10 per minute")
@jwt_required()
def remove_avatar():
    """
    Remove User Avatar
    
    Implements User Story OLS-US-003: Avatar Management
    
    Allows users to remove their current avatar image
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Remove avatar using service
        result = user_service.delete_avatar(current_user_id)
        
        return success_response(
            message='Avatar removed successfully',
            data=result
        )
        
    except BusinessLogicException as e:
        return error_response(e.message, 404 if 'not found' in e.message.lower() else 403)
    except Exception as e:
        current_app.logger.error(f"Remove avatar error: {e}")
        return error_response('Failed to remove avatar. Please try again.', 500)


@user_router.route('/debug-profile', methods=['GET'])
@jwt_required()
def debug_profile():
    """
    Debug endpoint to check profile_image in database
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get debug info using service
        debug_info = user_service.get_user_profile(current_user_id)
        
        return success_response(
            message='Debug info retrieved successfully',
            data={'debug_info': debug_info}
        )
        
    except BusinessLogicException as e:
        return error_response(e.message, 404 if 'not found' in e.message.lower() else 403)
    except Exception as e:
        current_app.logger.error(f"Debug profile error: {e}")
        return error_response('Failed to get debug info. Please try again.', 500)


@user_router.route('/avatar-info', methods=['GET'])
@jwt_required()
def get_avatar_info():
    """
    Get Avatar Information
    
    Returns information about the user's current avatar
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get avatar info using service
        profile_data = user_service.get_user_profile(current_user_id)
        avatar_info = {
            'has_avatar': bool(profile_data.get('avatar_url')),
            'avatar_url': profile_data.get('avatar_url')
        }
        
        return success_response(
            message='Avatar info retrieved successfully',
            data={'avatar_info': avatar_info}
        )
        
    except BusinessLogicException as e:
        return error_response(e.message, 404 if 'not found' in e.message.lower() else 403)
    except Exception as e:
        current_app.logger.error(f"Get avatar info error: {e}")
        return error_response('Failed to get avatar info. Please try again.', 500)


@user_router.route('/me/courses/<course_slug>/progress', methods=['GET'])
@limiter.limit("60 per minute")
@jwt_required()
def get_user_course_progress(course_slug):
    """
    Get User Course Progress
    
    Returns detailed progress information for a specific course
    including lesson completion, watch time, and overall progress
    
    Args:
        course_slug: Course slug identifier
        
    Returns:
        Detailed course progress with lesson breakdown
    """
    try:
        user = get_current_user()
        result = ProgressService.get_course_progress(user, course_slug)
        
        return success_response(
            message="Course progress retrieved successfully",
            data=result['data']
        )
        
    except ValidationException as e:
        return error_response(str(e), 404 if "Không tìm thấy" in str(e) else 400)
    except Exception as e:
        current_app.logger.error(f"Get course progress error: {e}")
        return error_response('Failed to get course progress. Please try again.', 500)