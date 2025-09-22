"""
Instructor Router
API endpoints for instructor course management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.instructor_service import InstructorService
from app.utils.response import success_response, error_response, validation_error_response, created_response
from app.utils.auth import instructor_required
from app.exceptions.base import ValidationException, AuthenticationException, BusinessLogicException
from app.validators.course import CourseCreateSchema, CourseUpdateSchema
from marshmallow import Schema, fields, validate, ValidationError

instructor_router = Blueprint('instructor', __name__)


# Inline validation schemas for modules and lessons
class ModuleCreateSchema(Schema):
    """Marshmallow schema for module creation"""
    
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(load_default=None, validate=validate.Length(max=1000))
    order = fields.Int(load_default=1, validate=validate.Range(min=1))


class ModuleUpdateSchema(Schema):
    """Marshmallow schema for module updates"""
    
    title = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(validate=validate.Length(max=1000))
    order = fields.Int(validate=validate.Range(min=1))


class LessonCreateSchema(Schema):
    """Marshmallow schema for lesson creation"""
    
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(load_default=None, validate=validate.Length(max=1000))
    content_type = fields.Str(required=True, validate=validate.OneOf(['video', 'text', 'document', 'quiz', 'assignment']))
    duration_minutes = fields.Int(load_default=0, validate=validate.Range(min=0, max=10080))  # Max 1 week
    order = fields.Int(load_default=1, validate=validate.Range(min=1))
    is_preview = fields.Bool(load_default=False)
    is_published = fields.Bool(load_default=False)
    
    # Content data - will be saved to Content table
    video_url = fields.Str(load_default=None, validate=validate.Length(max=500))
    content_data = fields.Str(load_default=None, validate=validate.Length(max=10000))


class LessonUpdateSchema(Schema):
    """Marshmallow schema for lesson updates"""
    
    title = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(validate=validate.Length(max=1000))
    content_type = fields.Str(validate=validate.OneOf(['video', 'text', 'document', 'quiz', 'assignment']))
    duration_minutes = fields.Int(validate=validate.Range(min=0, max=10080))
    order = fields.Int(validate=validate.Range(min=1))
    is_preview = fields.Bool()
    is_published = fields.Bool()
    
    # Content data - will be saved to Content table
    video_url = fields.Str(validate=validate.Length(max=500))
    content_data = fields.Str(validate=validate.Length(max=10000))


@instructor_router.route('/courses', methods=['GET'])
@jwt_required()
@instructor_required
def get_instructor_courses():
    """
    Get instructor's courses with pagination and filtering
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10)
    - status: "draft" | "published" | "all" (default: "all")
    - sort_by: "created_at" | "updated_at" | "title" (default: "updated_at")
    - sort_order: "asc" | "desc" (default: "desc")
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        status = request.args.get('status', 'all')
        sort_by = request.args.get('sort_by', 'updated_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Validate parameters
        if status not in ['draft', 'published', 'all']:
            status = 'all'
        if sort_by not in ['created_at', 'updated_at', 'title']:
            sort_by = 'updated_at'
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
            
        # Get courses from service
        result = InstructorService.get_instructor_courses(
            instructor_id=instructor_id,
            page=page,
            per_page=per_page,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return success_response(
            message='Courses retrieved successfully',
            data=result
        )
        
    except ValidationException as e:
        return error_response(e.message, 400)
    except Exception as e:
        return error_response('Failed to retrieve courses', 500)


@instructor_router.route('/courses', methods=['POST'])
@jwt_required()
@instructor_required
def create_course():
    """
    Create new course for instructor
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input using schema
        schema = CourseCreateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Create course using service
        course = InstructorService.create_course(
            instructor_id=instructor_id,
            **validated_data
        )
        
        return created_response(
            message='Course created successfully',
            data=course
        )
        
    except ValidationException as e:
        return validation_error_response('Validation failed', e.details if hasattr(e, 'details') else {'general': [e.message]})
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to create course', 500)


@instructor_router.route('/courses/<int:course_id>', methods=['GET'])
@jwt_required()
@instructor_required
def get_course_details(course_id):
    """
    Get single course details for instructor
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        course = InstructorService.get_instructor_course_details(
            instructor_id=instructor_id,
            course_id=course_id
        )
        
        return success_response(
            message='Course retrieved successfully',
            data=course
        )
        
    except ValidationException as e:
        return error_response(e.message, 404)
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to retrieve course', 500)


@instructor_router.route('/courses/<int:course_id>', methods=['PUT'])
@jwt_required()
@instructor_required
def update_course(course_id):
    """
    Update course for instructor
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input using schema
        schema = CourseUpdateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Update course using service
        course = InstructorService.update_course(
            instructor_id=instructor_id,
            course_id=course_id,
            **validated_data
        )
        
        return success_response(
            message='Course updated successfully',
            data=course
        )
        
    except ValidationException as e:
        return validation_error_response('Validation failed', e.details if hasattr(e, 'details') else {'general': [e.message]})
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to update course', 500)


@instructor_router.route('/courses/<int:course_id>/publish', methods=['POST'])
@jwt_required()
@instructor_required
def publish_course(course_id):
    """
    Publish course
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        result = InstructorService.publish_course(
            instructor_id=instructor_id,
            course_id=course_id
        )
        
        return success_response(
            message='Course published successfully',
            data=result
        )
        
    except ValidationException as e:
        return error_response(e.message, 404)
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to publish course', 500)


@instructor_router.route('/courses/<int:course_id>/unpublish', methods=['POST'])
@jwt_required()
@instructor_required
def unpublish_course(course_id):
    """
    Unpublish course
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        result = InstructorService.unpublish_course(
            instructor_id=instructor_id,
            course_id=course_id
        )
        
        return success_response(
            message='Course unpublished successfully',
            data=result
        )
        
    except ValidationException as e:
        return error_response(e.message, 404)
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to unpublish course', 500)


@instructor_router.route('/courses/<int:course_id>', methods=['DELETE'])
@jwt_required()
@instructor_required
def delete_course(course_id):
    """
    Delete course (optional endpoint)
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        InstructorService.delete_course(
            instructor_id=instructor_id,
            course_id=course_id
        )
        
        return success_response(
            message='Course deleted successfully'
        )
        
    except ValidationException as e:
        return error_response(e.message, 404)
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to delete course', 500)


# Module Management Endpoints

@instructor_router.route('/courses/<int:course_id>/modules', methods=['GET'])
@jwt_required()
@instructor_required
def get_course_modules(course_id):
    """
    Get all modules for a specific course
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        modules = InstructorService.get_course_modules(
            instructor_id=instructor_id,
            course_id=course_id
        )
        
        return success_response(
            message='Modules retrieved successfully',
            data=modules
        )
        
    except ValidationException as e:
        return error_response(e.message, 404)
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to retrieve modules', 500)


@instructor_router.route('/courses/<int:course_id>/modules', methods=['POST'])
@jwt_required()
@instructor_required
def create_module(course_id):
    """
    Create a new module for a course
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input using schema
        schema = ModuleCreateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Create module using service
        module = InstructorService.create_module(
            instructor_id=instructor_id,
            course_id=course_id,
            **validated_data
        )
        
        return created_response(
            message='Module created successfully',
            data=module
        )
        
    except ValidationException as e:
        return validation_error_response('Validation failed', e.details if hasattr(e, 'details') else {'general': [e.message]})
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to create module', 500)


@instructor_router.route('/courses/<int:course_id>/modules/<int:module_id>', methods=['PUT'])
@jwt_required()
@instructor_required
def update_module(course_id, module_id):
    """
    Update a module
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input using schema
        schema = ModuleUpdateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Update module using service
        module = InstructorService.update_module(
            instructor_id=instructor_id,
            course_id=course_id,
            module_id=module_id,
            **validated_data
        )
        
        return success_response(
            message='Module updated successfully',
            data=module
        )
        
    except ValidationException as e:
        return validation_error_response('Validation failed', e.details if hasattr(e, 'details') else {'general': [e.message]})
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to update module', 500)


@instructor_router.route('/courses/<int:course_id>/modules/<int:module_id>', methods=['DELETE'])
@jwt_required()
@instructor_required
def delete_module(course_id, module_id):
    """
    Delete a module
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        InstructorService.delete_module(
            instructor_id=instructor_id,
            course_id=course_id,
            module_id=module_id
        )
        
        return success_response(
            message='Module deleted successfully'
        )
        
    except ValidationException as e:
        return error_response(e.message, 404)
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to delete module', 500)


# Lesson Management Endpoints

@instructor_router.route('/courses/<int:course_id>/modules/<int:module_id>/lessons', methods=['GET'])
@jwt_required()
@instructor_required
def get_module_lessons(course_id, module_id):
    """
    Get all lessons for a specific module
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        lessons = InstructorService.get_module_lessons(
            instructor_id=instructor_id,
            course_id=course_id,
            module_id=module_id
        )
        
        return success_response(
            message='Lessons retrieved successfully',
            data=lessons
        )
        
    except ValidationException as e:
        return error_response(e.message, 404)
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to retrieve lessons', 500)


@instructor_router.route('/courses/<int:course_id>/modules/<int:module_id>/lessons', methods=['POST'])
@jwt_required()
@instructor_required
def create_lesson(course_id, module_id):
    """
    Create a new lesson for a module
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input using schema
        schema = LessonCreateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Create lesson using service
        lesson = InstructorService.create_lesson(
            instructor_id=instructor_id,
            course_id=course_id,
            module_id=module_id,
            **validated_data
        )
        
        return created_response(
            message='Lesson created successfully',
            data=lesson
        )
        
    except ValidationException as e:
        return validation_error_response('Validation failed', e.details if hasattr(e, 'details') else {'general': [e.message]})
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to create lesson', 500)


@instructor_router.route('/courses/<int:course_id>/modules/<int:module_id>/lessons/<int:lesson_id>', methods=['PUT'])
@jwt_required()
@instructor_required
def update_lesson(course_id, module_id, lesson_id):
    """
    Update a lesson
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input using schema
        schema = LessonUpdateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Update lesson using service
        lesson = InstructorService.update_lesson(
            instructor_id=instructor_id,
            course_id=course_id,
            module_id=module_id,
            lesson_id=lesson_id,
            **validated_data
        )
        
        return success_response(
            message='Lesson updated successfully',
            data=lesson
        )
        
    except ValidationException as e:
        return validation_error_response('Validation failed', e.details if hasattr(e, 'details') else {'general': [e.message]})
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to update lesson', 500)


@instructor_router.route('/courses/<int:course_id>/modules/<int:module_id>/lessons/<int:lesson_id>', methods=['DELETE'])
@jwt_required()
@instructor_required
def delete_lesson(course_id, module_id, lesson_id):
    """
    Delete a lesson
    """
    try:
        instructor_id = int(get_jwt_identity())
        
        InstructorService.delete_lesson(
            instructor_id=instructor_id,
            course_id=course_id,
            module_id=module_id,
            lesson_id=lesson_id
        )
        
        return success_response(
            message='Lesson deleted successfully'
        )
        
    except ValidationException as e:
        return error_response(e.message, 404)
    except BusinessLogicException as e:
        return error_response(e.message, 403)
    except Exception as e:
        return error_response('Failed to delete lesson', 500)
