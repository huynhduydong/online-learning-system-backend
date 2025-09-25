"""
Answer Router
API endpoints for Q&A answers management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError

from app.services.answer_service import AnswerService
from app.utils.response import success_response, error_response, validation_error_response, created_response
from app.utils.auth import get_current_user
from app.exceptions.base import ValidationException, AuthenticationException, BusinessLogicException

answer_router = Blueprint('answers', __name__)

# Initialize service
answer_service = AnswerService()


# Validation schemas
class AnswerCreateSchema(Schema):
    content = fields.Str(required=True, validate=validate.Length(min=20, max=5000))


class AnswerUpdateSchema(Schema):
    content = fields.Str(required=True, validate=validate.Length(min=20, max=5000))


class VoteSchema(Schema):
    vote_type = fields.Str(required=True, validate=validate.OneOf(['upvote', 'downvote']))


@answer_router.route('/question/<int:question_id>', methods=['GET'])
def get_question_answers(question_id):
    """
    GET /api/answers/question/{questionId}
    Lấy danh sách câu trả lời của câu hỏi
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort_by', 'votes')  # votes, created_at, accepted
        sort_order = request.args.get('sort_order', 'desc')
        
        # Get current user for personalization
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # Get question answers
        result = answer_service.get_question_answers(
            question_id=question_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách câu trả lời được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách câu trả lời", 500)


@answer_router.route('/<int:answer_id>', methods=['GET'])
def get_answer_by_id(answer_id):
    """
    GET /api/answers/{id}
    Lấy chi tiết câu trả lời theo ID
    """
    try:
        # Get current user for personalization
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # Get answer details
        result = answer_service.get_answer_by_id(answer_id, user_id)
        
        return success_response(
            data=result['data'],
            message="Chi tiết câu trả lời được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy chi tiết câu trả lời", 500)


@answer_router.route('/question/<int:question_id>', methods=['POST'])
@jwt_required()
def create_answer(question_id):
    """
    POST /api/answers/question/{questionId}
    Tạo câu trả lời mới cho câu hỏi
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
        schema = AnswerCreateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Create answer
        result = answer_service.create_answer(
            question_id=question_id,
            user_id=int(user_id),
            content=validated_data['content']
        )
        
        return created_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi tạo câu trả lời", 500)


@answer_router.route('/<int:answer_id>', methods=['PUT'])
@jwt_required()
def update_answer(answer_id):
    """
    PUT /api/answers/{id}
    Cập nhật câu trả lời
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
        schema = AnswerUpdateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Update answer
        result = answer_service.update_answer(
            answer_id=answer_id,
            user_id=int(user_id),
            content=validated_data['content']
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
        return error_response("Lỗi khi cập nhật câu trả lời", 500)


@answer_router.route('/<int:answer_id>', methods=['DELETE'])
@jwt_required()
def delete_answer(answer_id):
    """
    DELETE /api/answers/{id}
    Xóa câu trả lời
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Delete answer
        result = answer_service.delete_answer(answer_id, int(user_id))
        
        return success_response(
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi xóa câu trả lời", 500)


@answer_router.route('/<int:answer_id>/accept', methods=['POST'])
@jwt_required()
def accept_answer(answer_id):
    """
    POST /api/answers/{id}/accept
    Chấp nhận câu trả lời (chỉ tác giả câu hỏi mới được phép)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Accept answer
        result = answer_service.accept_answer(answer_id, int(user_id))
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi chấp nhận câu trả lời", 500)


@answer_router.route('/<int:answer_id>/unaccept', methods=['POST'])
@jwt_required()
def unaccept_answer(answer_id):
    """
    POST /api/answers/{id}/unaccept
    Bỏ chấp nhận câu trả lời (chỉ tác giả câu hỏi mới được phép)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Unaccept answer
        result = answer_service.unaccept_answer(answer_id, int(user_id))
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi bỏ chấp nhận câu trả lời", 500)


@answer_router.route('/<int:answer_id>/vote', methods=['POST'])
@jwt_required()
def vote_answer(answer_id):
    """
    POST /api/answers/{id}/vote
    Vote cho câu trả lời (upvote/downvote)
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
        
        # Vote answer
        result = answer_service.vote_answer(
            answer_id=answer_id,
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
        return error_response("Lỗi khi vote câu trả lời", 500)


@answer_router.route('/user/<int:user_id>', methods=['GET'])
def get_user_answers(user_id):
    """
    GET /api/answers/user/{userId}
    Lấy danh sách câu trả lời của user
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Get current user for permission check
        current_user = get_current_user()
        current_user_id = current_user.id if current_user else None
        
        # Get user answers
        result = answer_service.get_user_answers(
            user_id=user_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            current_user_id=current_user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách câu trả lời của user được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách câu trả lời của user", 500)


@answer_router.route('/top', methods=['GET'])
def get_top_answers():
    """
    GET /api/answers/top
    Lấy danh sách câu trả lời được vote cao nhất
    """
    try:
        # Get query parameters
        time_frame = request.args.get('time_frame', 'week')  # day, week, month, all
        limit = request.args.get('limit', 10, type=int)
        course_id = request.args.get('course_id', type=int)
        
        # Get current user for personalization
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # Get top answers
        result = answer_service.get_top_answers(
            time_frame=time_frame,
            limit=limit,
            course_id=course_id,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách câu trả lời top được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách câu trả lời top", 500)


@answer_router.route('/search', methods=['GET'])
def search_answers():
    """
    GET /api/answers/search
    Tìm kiếm câu trả lời
    """
    try:
        # Get query parameters
        search_term = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort_by', 'relevance')
        course_id = request.args.get('course_id', type=int)
        accepted_only = request.args.get('accepted_only', 'false').lower() == 'true'
        
        if not search_term:
            return validation_error_response('Search term is required', {'q': ['Search term is required']})
        
        # Build filters
        filters = {}
        if course_id:
            filters['course_id'] = course_id
        if accepted_only:
            filters['accepted_only'] = True
        
        # Get current user for personalization
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # Search answers
        result = answer_service.search_answers(
            search_term=search_term,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            filters=filters,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Kết quả tìm kiếm câu trả lời được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi tìm kiếm câu trả lời", 500)


@answer_router.route('/recent', methods=['GET'])
def get_recent_answers():
    """
    GET /api/answers/recent
    Lấy danh sách câu trả lời gần đây
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        course_id = request.args.get('course_id', type=int)
        
        # Get current user for personalization
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # Get recent answers
        result = answer_service.get_recent_answers(
            limit=limit,
            course_id=course_id,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách câu trả lời gần đây được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách câu trả lời gần đây", 500)


# Error handlers
@answer_router.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors"""
    return error_response("Không tìm thấy câu trả lời", 404)


@answer_router.errorhandler(403)
def handle_forbidden(error):
    """Handle 403 errors"""
    return error_response("Bạn không có quyền thực hiện thao tác này", 403)


@answer_router.errorhandler(401)
def handle_unauthorized(error):
    """Handle 401 errors"""
    return error_response("Yêu cầu đăng nhập để thực hiện thao tác này", 401)