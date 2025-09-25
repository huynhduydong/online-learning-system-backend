"""
Vote Router
API endpoints for Q&A voting system management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError

from app.services.vote_service import VoteService
from app.utils.response import success_response, error_response, validation_error_response, created_response
from app.utils.auth import get_current_user
from app.exceptions.base import ValidationException, AuthenticationException, BusinessLogicException

vote_router = Blueprint('votes', __name__)

# Initialize service
vote_service = VoteService()


# Validation schemas
class VoteSchema(Schema):
    vote_type = fields.Str(required=True, validate=validate.OneOf(['upvote', 'downvote']))


@vote_router.route('/<item_type>/<int:item_id>', methods=['POST'])
@jwt_required()
def cast_vote(item_type, item_id):
    """
    POST /api/votes/{itemType}/{itemId}
    Bỏ phiếu cho một item (question hoặc answer)
    """
    try:
        # Validate item type
        if item_type not in ['question', 'answer']:
            return validation_error_response('Invalid item type', {'item_type': ['Must be question or answer']})
        
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
        
        # Cast vote
        result = vote_service.cast_vote(
            item_type=item_type,
            item_id=item_id,
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
        return error_response("Lỗi khi bỏ phiếu", 500)


@vote_router.route('/<item_type>/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_vote(item_type, item_id):
    """
    DELETE /api/votes/{itemType}/{itemId}
    Hủy bỏ phiếu cho một item
    """
    try:
        # Validate item type
        if item_type not in ['question', 'answer']:
            return validation_error_response('Invalid item type', {'item_type': ['Must be question or answer']})
        
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Remove vote
        result = vote_service.remove_vote(
            item_type=item_type,
            item_id=item_id,
            user_id=int(user_id)
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
        return error_response("Lỗi khi hủy bỏ phiếu", 500)


@vote_router.route('/<item_type>/<int:item_id>/user', methods=['GET'])
@jwt_required()
def get_user_vote(item_type, item_id):
    """
    GET /api/votes/{itemType}/{itemId}/user
    Lấy thông tin phiếu bầu của user hiện tại cho một item
    """
    try:
        # Validate item type
        if item_type not in ['question', 'answer']:
            return validation_error_response('Invalid item type', {'item_type': ['Must be question or answer']})
        
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get user vote
        result = vote_service.get_user_vote(
            item_type=item_type,
            item_id=item_id,
            user_id=int(user_id)
        )
        
        return success_response(
            data=result['data'],
            message="Thông tin phiếu bầu được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy thông tin phiếu bầu", 500)


@vote_router.route('/<item_type>/<int:item_id>/score', methods=['GET'])
def get_vote_score(item_type, item_id):
    """
    GET /api/votes/{itemType}/{itemId}/score
    Lấy điểm số vote của một item
    """
    try:
        # Validate item type
        if item_type not in ['question', 'answer']:
            return validation_error_response('Invalid item type', {'item_type': ['Must be question or answer']})
        
        # Get vote score
        result = vote_service.get_vote_score(item_type, item_id)
        
        return success_response(
            data=result['data'],
            message="Điểm số vote được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy điểm số vote", 500)


@vote_router.route('/<item_type>/<int:item_id>/statistics', methods=['GET'])
def get_vote_statistics(item_type, item_id):
    """
    GET /api/votes/{itemType}/{itemId}/statistics
    Lấy thống kê chi tiết về vote của một item
    """
    try:
        # Validate item type
        if item_type not in ['question', 'answer']:
            return validation_error_response('Invalid item type', {'item_type': ['Must be question or answer']})
        
        # Get vote statistics
        result = vote_service.get_vote_statistics(item_type, item_id)
        
        return success_response(
            data=result['data'],
            message="Thống kê vote được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy thống kê vote", 500)


@vote_router.route('/user/<int:user_id>', methods=['GET'])
def get_user_votes(user_id):
    """
    GET /api/votes/user/{userId}
    Lấy danh sách vote của một user
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        item_type = request.args.get('item_type')  # question, answer, hoặc None cho tất cả
        vote_type = request.args.get('vote_type')  # upvote, downvote, hoặc None cho tất cả
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Get current user for permission check
        current_user = get_current_user()
        current_user_id = current_user.id if current_user else None
        
        # Get user votes
        result = vote_service.get_user_votes(
            user_id=user_id,
            page=page,
            per_page=per_page,
            item_type=item_type,
            vote_type=vote_type,
            sort_by=sort_by,
            sort_order=sort_order,
            current_user_id=current_user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách vote của user được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách vote của user", 500)


@vote_router.route('/summary', methods=['GET'])
def get_vote_summary():
    """
    GET /api/votes/summary
    Lấy tổng quan về hệ thống vote
    """
    try:
        # Get query parameters
        item_type = request.args.get('item_type')  # question, answer, hoặc None cho tất cả
        course_id = request.args.get('course_id', type=int)
        time_range = request.args.get('time_range', 'all')  # today, week, month, year, all
        
        # Build filters
        filters = {}
        if item_type:
            filters['item_type'] = item_type
        if course_id:
            filters['course_id'] = course_id
        if time_range:
            filters['time_range'] = time_range
        
        # Get vote summary
        result = vote_service.get_vote_summary(filters)
        
        return success_response(
            data=result['data'],
            message="Tổng quan vote được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy tổng quan vote", 500)


@vote_router.route('/top-voted', methods=['GET'])
def get_top_voted_items():
    """
    GET /api/votes/top-voted
    Lấy danh sách item có điểm vote cao nhất
    """
    try:
        # Get query parameters
        item_type = request.args.get('item_type', 'question')  # question hoặc answer
        limit = request.args.get('limit', 10, type=int)
        time_range = request.args.get('time_range', 'all')  # today, week, month, year, all
        course_id = request.args.get('course_id', type=int)
        
        # Validate item type
        if item_type not in ['question', 'answer']:
            return validation_error_response('Invalid item type', {'item_type': ['Must be question or answer']})
        
        # Build filters
        filters = {}
        if time_range:
            filters['time_range'] = time_range
        if course_id:
            filters['course_id'] = course_id
        
        # Get current user for personalization
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # Get top voted items
        result = vote_service.get_top_voted_items(
            item_type=item_type,
            limit=limit,
            filters=filters,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách item có điểm vote cao nhất được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách item có điểm vote cao nhất", 500)


@vote_router.route('/bulk-update', methods=['POST'])
@jwt_required()
def bulk_update_vote_scores():
    """
    POST /api/votes/bulk-update
    Cập nhật điểm vote hàng loạt (chỉ admin)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Check admin permission (implement based on your user role system)
        current_user = get_current_user()
        if not current_user or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return error_response('Admin permission required', 403)
        
        # Get request data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        item_type = data.get('item_type')
        item_ids = data.get('item_ids', [])
        
        if not item_type or item_type not in ['question', 'answer']:
            return validation_error_response('Invalid item type', {'item_type': ['Must be question or answer']})
        
        if not item_ids or not isinstance(item_ids, list):
            return validation_error_response('Invalid item IDs', {'item_ids': ['Must be a list of item IDs']})
        
        # Bulk update vote scores
        result = vote_service.bulk_update_vote_scores(item_type, item_ids)
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi cập nhật điểm vote hàng loạt", 500)


@vote_router.route('/trends', methods=['GET'])
def get_vote_trends():
    """
    GET /api/votes/trends
    Lấy xu hướng vote theo thời gian
    """
    try:
        # Get query parameters
        item_type = request.args.get('item_type')  # question, answer, hoặc None cho tất cả
        time_range = request.args.get('time_range', 'week')  # day, week, month, year
        course_id = request.args.get('course_id', type=int)
        granularity = request.args.get('granularity', 'day')  # hour, day, week, month
        
        # Build filters
        filters = {}
        if item_type:
            filters['item_type'] = item_type
        if course_id:
            filters['course_id'] = course_id
        
        # Get vote trends
        result = vote_service.get_vote_trends(
            time_range=time_range,
            granularity=granularity,
            filters=filters
        )
        
        return success_response(
            data=result['data'],
            message="Xu hướng vote được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy xu hướng vote", 500)


# Error handlers
@vote_router.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors"""
    return error_response("Không tìm thấy vote", 404)


@vote_router.errorhandler(403)
def handle_forbidden(error):
    """Handle 403 errors"""
    return error_response("Bạn không có quyền thực hiện thao tác này", 403)


@vote_router.errorhandler(401)
def handle_unauthorized(error):
    """Handle 401 errors"""
    return error_response("Yêu cầu đăng nhập để thực hiện thao tác này", 401)