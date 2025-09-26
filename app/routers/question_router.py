"""
Question Router
API endpoints for Q&A questions management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
import logging
import traceback

from app.services.question_service import QuestionService
from app.utils.response import success_response, error_response, validation_error_response, created_response
from app.utils.auth import get_current_user_optional, get_current_user
from app.exceptions.base import ValidationException, AuthenticationException, BusinessLogicException

question_router = Blueprint('questions', __name__)

# Initialize service
question_service = QuestionService()


# Validation schemas
class QuestionCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=10, max=200))
    content = fields.Str(required=True, validate=validate.Length(min=20, max=5000))
    category = fields.Str(allow_none=True, validate=validate.OneOf(['general', 'technical', 'course', 'assignment']))
    scope = fields.Str(allow_none=True, validate=validate.OneOf(['course', 'chapter', 'lesson', 'quiz', 'assignment']))
    scope_id = fields.Int(allow_none=True)
    tags = fields.List(fields.Str(validate=validate.Length(min=1, max=50)), missing=[])
    course_id = fields.Int(allow_none=True)


class QuestionUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=10, max=200))
    content = fields.Str(validate=validate.Length(min=20, max=5000))
    tags = fields.List(fields.Str(validate=validate.Length(min=1, max=50)))


class VoteSchema(Schema):
    vote_type = fields.Str(required=True, validate=validate.OneOf(['upvote', 'downvote']))


@question_router.route('/', methods=['GET'], strict_slashes=False)
def get_questions():
    """
    GET /api/questions
    Lấy danh sách câu hỏi với phân trang và filter
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        course_id = request.args.get('course_id', type=int)
        tag = request.args.get('tag')
        status = request.args.get('status')
        scope = request.args.get('scope')
        scope_id = request.args.get('scope_id', type=int)
        category = request.args.get('category')
        
        # Build filters
        filters = {}
        if course_id:
            filters['course_id'] = course_id
        if tag:
            filters['tag'] = tag
        if status:
            filters['status'] = status
        if scope:
            filters['scope'] = scope
        if scope_id:
            filters['scope_id'] = scope_id
        if category:
            filters['category'] = category
        
        # Get current user for personalization (optional)
        current_user = get_current_user_optional()
        user_id = current_user.id if current_user else None
        
        # Get questions
        result = question_service.get_questions(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách câu hỏi được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        logging.error(f"Error in get_questions: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return error_response("Lỗi khi lấy danh sách câu hỏi", 500)


@question_router.route('/<int:question_id>', methods=['GET'])
def get_question_by_id(question_id):
    """
    GET /api/questions/{id}
    Lấy chi tiết câu hỏi theo ID
    """
    try:
        # Get current user for personalization
        current_user = get_current_user_optional()
        user_id = current_user.id if current_user else None
        
        # Get question details
        result = question_service.get_question_by_id(question_id, user_id)
        
        return success_response(
            data=result['data'],
            message="Chi tiết câu hỏi được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy chi tiết câu hỏi", 500)


@question_router.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
def create_question():
    """
    POST /api/questions
    Tạo câu hỏi mới
    """
    logging.info("🚀 API CREATE_QUESTION: Starting request")
    try:
        # Get current user
        user_id = get_jwt_identity()
        logging.info(f"🔐 API CREATE_QUESTION: Got user_id from JWT: {user_id}")
        if not user_id:
            logging.error("❌ API CREATE_QUESTION: No user_id in JWT token")
            return error_response('Authentication required', 401)
        
        # Get request data
        data = request.get_json()
        logging.info(f"📥 API CREATE_QUESTION: Raw request data: {data}")
        if not data:
            logging.error("❌ API CREATE_QUESTION: No data provided in request")
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input
        schema = QuestionCreateSchema()
        try:
            validated_data = schema.load(data)
            logging.info(f"✅ API CREATE_QUESTION: Data validation successful: {validated_data}")
        except ValidationError as err:
            logging.error(f"❌ API CREATE_QUESTION: Validation failed: {err.messages}")
            return validation_error_response('Validation failed', err.messages)
        
        # Create question
        logging.info(f"🔄 API CREATE_QUESTION: Calling service with user_id={int(user_id)}, data={validated_data}")
        result = question_service.create_question(
            user_id=int(user_id),
            data=validated_data
        )
        logging.info(f"✅ API CREATE_QUESTION: Service call successful: {result}")
        
        return created_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        logging.error(f"❌ API CREATE_QUESTION: ValidationException: {str(e)}")
        logging.error(f"❌ API CREATE_QUESTION: Full traceback: {traceback.format_exc()}")
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        logging.error(f"❌ API CREATE_QUESTION: BusinessLogicException: {str(e)}")
        logging.error(f"❌ API CREATE_QUESTION: Full traceback: {traceback.format_exc()}")
        return error_response(str(e), 400)
    except Exception as e:
        logging.error(f"❌ API CREATE_QUESTION: Unexpected error: {str(e)}")
        logging.error(f"❌ API CREATE_QUESTION: Full traceback: {traceback.format_exc()}")
        return error_response("Lỗi khi tạo câu hỏi", 500)


@question_router.route('/<int:question_id>', methods=['PUT'])
@jwt_required()
def update_question(question_id):
    """
    PUT /api/questions/{id}
    Cập nhật câu hỏi
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get request data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input
        schema = QuestionUpdateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Update question
        result = question_service.update_question(
            question_id=question_id,
            user_id=int(user_id),
            **validated_data
        )
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi cập nhật câu hỏi", 500)


@question_router.route('/<int:question_id>', methods=['DELETE'])
@jwt_required()
def delete_question(question_id):
    """
    DELETE /api/questions/{id}
    Xóa câu hỏi
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Delete question
        result = question_service.delete_question(question_id, int(user_id))
        
        return success_response(
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi xóa câu hỏi", 500)


@question_router.route('/<int:question_id>/vote', methods=['POST'])
@jwt_required()
def vote_question(question_id):
    """
    POST /api/questions/{id}/vote
    Vote cho câu hỏi (upvote/downvote)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get request data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input
        schema = VoteSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Vote question
        result = question_service.vote_question(
            question_id=question_id,
            user_id=int(user_id),
            vote_type=validated_data['vote_type']
        )
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi vote câu hỏi", 500)


@question_router.route('/search', methods=['GET'], strict_slashes=False)
def search_questions():
    """
    GET /api/questions/search
    Tìm kiếm câu hỏi
    """
    try:
        # Get query parameters
        search_term = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort_by', 'relevance')
        course_id = request.args.get('course_id', type=int)
        tag = request.args.get('tag')
        
        if not search_term:
            return validation_error_response('Search term is required', {'q': ['Search term is required']})
        
        # Build filters
        filters = {}
        if course_id:
            filters['course_id'] = course_id
        if tag:
            filters['tag'] = tag
        
        # Get current user for personalization
        current_user = get_current_user_optional()
        user_id = current_user.id if current_user else None
        
        # Search questions
        result = question_service.search_questions(
            search_term=search_term,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            filters=filters,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Kết quả tìm kiếm được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi tìm kiếm câu hỏi", 500)


@question_router.route('/user/<int:user_id>', methods=['GET'])
def get_user_questions(user_id):
    """
    GET /api/questions/user/{userId}
    Lấy danh sách câu hỏi của user
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Get current user for permission check
        current_user = get_current_user_optional()
        current_user_id = current_user.id if current_user else None
        
        # Get user questions
        result = question_service.get_user_questions(
            user_id=user_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            current_user_id=current_user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách câu hỏi của user được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách câu hỏi của user", 500)


@question_router.route('/trending', methods=['GET'], strict_slashes=False)
def get_trending_questions():
    """
    GET /api/questions/trending
    Lấy danh sách câu hỏi trending
    """
    try:
        # Get query parameters
        time_frame = request.args.get('time_frame', 'week')  # day, week, month
        limit = request.args.get('limit', 10, type=int)
        course_id = request.args.get('course_id', type=int)
        
        # Get current user for personalization
        current_user = get_current_user_optional()
        user_id = current_user.id if current_user else None
        
        # Get trending questions
        result = question_service.get_trending_questions(
            time_frame=time_frame,
            limit=limit,
            course_id=course_id,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách câu hỏi trending được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách câu hỏi trending", 500)


@question_router.route('/<int:question_id>/related', methods=['GET'])
def get_related_questions(question_id):
    """
    GET /api/questions/{id}/related
    Lấy danh sách câu hỏi liên quan
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 5, type=int)
        
        # Get current user for personalization
        current_user = get_current_user_optional()
        user_id = current_user.id if current_user else None
        
        # Get related questions
        result = question_service.get_related_questions(
            question_id=question_id,
            limit=limit,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách câu hỏi liên quan được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách câu hỏi liên quan", 500)


# Error handlers
@question_router.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors"""
    return error_response("Không tìm thấy câu hỏi", 404)


@question_router.errorhandler(403)
def handle_forbidden(error):
    """Handle 403 errors"""
    return error_response("Bạn không có quyền thực hiện thao tác này", 403)


@question_router.errorhandler(401)
def handle_unauthorized(error):
    """Handle 401 errors"""
    return error_response("Yêu cầu đăng nhập để thực hiện thao tác này", 401)