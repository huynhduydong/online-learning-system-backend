"""
Enrollment Router - Course Registration Workflow
Implements all enrollment and payment related endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.enrollment_service import EnrollmentService
from app.validators.enrollment import EnrollmentValidator
from app.exceptions.validation_exception import ValidationException
from app.utils.response import success_response, error_response

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
enrollment_router = Blueprint('enrollments', __name__)

# Initialize service
enrollment_service = EnrollmentService()


@enrollment_router.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'Enrollment service is running', 'version': '1.0.0'}




@enrollment_router.route('/register', methods=['POST'])
@jwt_required()
def register_for_course():
    """
    POST /api/enrollments/register
    Initialize the course registration process
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get request data
        data = request.get_json()
        if not data:
            return error_response('Request body is required', 400)
        
        # Validate request data
        validated_data = EnrollmentValidator.validate_registration_request(data)
        
        # Process registration
        result = enrollment_service.register_for_course(
            user_id=int(user_id),
            course_id=validated_data['course_id'],
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            discount_code=validated_data.get('discount_code')
        )
        
        logger.info(f"Course registration successful for user {user_id}")
        return success_response('Registration started successfully', result)
        
    except ValidationException as e:
        details = getattr(e, "errors", {"error": [str(e)]})
        logger.warning(f"Validation error in registration: {details}")
        return error_response('Validation failed', 422, details=details)
    except Exception as e:
        logger.error(f"Unexpected error in registration: {str(e)}")
        return error_response('Internal server error', 500)


@enrollment_router.route('/payment', methods=['POST'])
@jwt_required()
def process_payment():
    """
    POST /api/enrollments/payment
    Process payment for course enrollment
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get request data
        data = request.get_json()
        if not data:
            return error_response('Request body is required', 400)
        
        # Validate request data
        validated_data = EnrollmentValidator.validate_payment_request(data)
        
        # Process payment
        result = enrollment_service.process_payment(
            enrollment_id=validated_data['enrollment_id'],
            payment_method=validated_data['payment_method'],
            payment_details=validated_data['payment_details']
        )
        
        logger.info(f"Payment processed successfully for user {user_id}")
        return success_response('Payment processed successfully', result)
        
    except ValidationException as e:
        details = getattr(e, "errors", {"error": [str(e)]})
        logger.warning(f"Validation error in payment: {details}")
        return error_response('Payment failed', 422, details=details)
    except Exception as e:
        logger.error(f"Unexpected error in payment: {str(e)}")
        return error_response('Internal server error', 500)


@enrollment_router.route('/<enrollment_id>/activate', methods=['POST'])
@jwt_required()
def activate_course_access(enrollment_id):
    """
    POST /api/enrollments/{enrollmentId}/activate
    Activate course access after successful enrollment/payment
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Validate enrollment ID
        validated_enrollment_id = EnrollmentValidator.validate_enrollment_id(enrollment_id)
        
        # Activate course access
        result = enrollment_service.activate_course_access(validated_enrollment_id)
        
        if result['success']:
            logger.info(f"Course access activated for enrollment {enrollment_id}")
            return success_response('Course access activated', result)
        else:
            logger.info(f"Course activation in progress for enrollment {enrollment_id}")
            return success_response('Activation in progress', result)
        
    except ValidationException as e:
        details = getattr(e, "errors", {"error": [str(e)]})
        logger.warning(f"Validation error in activation: {details}")
        return error_response('Activation failed', 422, details=details)
    except Exception as e:
        logger.error(f"Unexpected error in activation: {str(e)}")
        return error_response('Internal server error', 500)


@enrollment_router.route('/<enrollment_id>', methods=['GET'])
@jwt_required()
def get_enrollment_status(enrollment_id):
    """
    GET /api/enrollments/{enrollmentId}
    Retrieve enrollment status by ID
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Validate enrollment ID
        validated_enrollment_id = EnrollmentValidator.validate_enrollment_id(enrollment_id)
        
        # Get enrollment status
        result = enrollment_service.get_enrollment_status(validated_enrollment_id)
        
        logger.info(f"Enrollment status retrieved for {enrollment_id}")
        return success_response('Enrollment status retrieved', result)
        
    except ValidationException as e:
        details = getattr(e, "errors", {"error": [str(e)]})
        logger.warning(f"Validation error getting enrollment status: {details}")
        return error_response('Not found', 404, details=details)
    except Exception as e:
        logger.error(f"Unexpected error getting enrollment status: {str(e)}")
        return error_response('Internal server error', 500)


@enrollment_router.route('/my-courses', methods=['GET'])
@jwt_required()
def get_my_courses():
    """
    GET /api/enrollments/my-courses
    Retrieve all course enrollments for the authenticated user
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Validate and convert user_id
        try:
            user_id = int(user_id)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid user_id from JWT: {user_id}, error: {str(e)}")
            return error_response('Invalid authentication token', 401)
        
        # Get query parameters
        status_filter = request.args.get('status')
        page = request.args.get('page', '1')
        limit = request.args.get('limit', '10')
        
        # Validate parameters
        try:
            if status_filter:
                status_filter = EnrollmentValidator.validate_status_filter(status_filter)
            page, limit = EnrollmentValidator.validate_pagination_params(page, limit)
        except ValidationException as ve:
            logger.warning(f"Parameter validation failed: {ve.errors}")
            return error_response('Invalid parameters', 400, details=ve.errors)
        
        # Get user enrollments
        try:
            result = enrollment_service.get_user_enrollments(
                user_id=user_id,
                status_filter=status_filter,
                page=page,
                limit=limit
            )
        except ValidationException as ve:
            logger.warning(f"Service validation error: {ve.errors}")
            return error_response('Failed to retrieve enrollments', 422, details=ve.errors)
        except Exception as e:
            logger.error(f"Service error getting user enrollments: {str(e)}", exc_info=True)
            return error_response('Failed to retrieve enrollments', 500)
        
        # Return response with proper format
        response_data = {
            'enrollments': result['data'],
            'pagination': result.get('pagination')
        }
        
        logger.info(f"User enrollments retrieved successfully for user {user_id}")
        return success_response(response_data, 'User enrollments retrieved')
        
    except ValidationException as e:
        details = getattr(e, "errors", {"error": [str(e)]})
        logger.warning(f"Validation error getting user enrollments: {details}")
        return error_response('Validation failed', 422, details=details)
    except Exception as e:
        logger.error(f"Unexpected error getting user enrollments: {str(e)}", exc_info=True)
        return error_response('Internal server error', 500)


@enrollment_router.route('/check-access/<course_id>', methods=['GET'])
@jwt_required()
def check_course_access(course_id):
    """
    GET /api/enrollments/check-access/{courseId}
    Check if the authenticated user has access to a specific course
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Validate course ID
        validated_course_id = EnrollmentValidator.validate_course_id(course_id)
        
        # Check course access
        result = enrollment_service.check_course_access(
            user_id=int(user_id),
            course_id=validated_course_id
        )
        
        if result['hasAccess']:
            logger.info(f"Course access confirmed for user {user_id}, course {course_id}")
            return success_response('Course access checked', result)
        else:
            logger.info(f"Course access denied for user {user_id}, course {course_id}")
            return success_response('No access to course', result)
        
    except ValidationException as e:
        details = getattr(e, "errors", {"error": [str(e)]})
        logger.warning(f"Validation error checking course access: {details}")
        return error_response('Validation failed', 422, details=details)
    except Exception as e:
        logger.error(f"Unexpected error checking course access: {str(e)}")
        return error_response('Internal server error', 500)


@enrollment_router.route('/<enrollment_id>/retry-activation', methods=['POST'])
@jwt_required()
def retry_activation(enrollment_id):
    """
    POST /api/enrollments/{enrollmentId}/retry-activation
    Retry course activation when the initial process failed
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Validate enrollment ID
        validated_enrollment_id = EnrollmentValidator.validate_enrollment_id(enrollment_id)
        
        # Retry activation
        result = enrollment_service.retry_activation(validated_enrollment_id)
        
        if result['success']:
            logger.info(f"Retry activation completed for enrollment {enrollment_id}")
            return success_response('Retry activation completed', result)
        else:
            logger.info(f"Retry activation failed for enrollment {enrollment_id}")
            return success_response('Retry activation failed', result)
        
    except ValidationException as e:
        details = getattr(e, "errors", {"error": [str(e)]})
        logger.warning(f"Validation error in retry activation: {details}")
        return error_response('Retry failed', 422, details=details)
    except Exception as e:
        logger.error(f"Unexpected error in retry activation: {str(e)}")
        return error_response('Internal server error', 500)


# Error handlers
@enrollment_router.errorhandler(ValidationException)
def handle_validation_error(error):
    """Handle validation exceptions"""
    details = getattr(error, "errors", {"error": [str(error)]})
    return error_response('Validation failed', 422, details=details)


@enrollment_router.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors"""
    return error_response('Enrollment not found', 404, error_code='ENROLLMENT_NOT_FOUND')


@enrollment_router.errorhandler(403)
def handle_forbidden(error):
    """Handle 403 errors"""
    return error_response("You don't have permission to access this resource", 403, 
                         error_code='INSUFFICIENT_PERMISSIONS')


@enrollment_router.errorhandler(401)
def handle_unauthorized(error):
    """Handle 401 errors"""
    return error_response('Access token is missing or invalid', 401, 
                         error_code='AUTH_REQUIRED')
