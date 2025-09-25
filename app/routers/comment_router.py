"""
Comment Router
API endpoints for Q&A comments management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError

from app.services.comment_service import CommentService
from app.utils.response import success_response, error_response, validation_error_response, created_response
from app.utils.auth import get_current_user
from app.exceptions.base import ValidationException, AuthenticationException, BusinessLogicException

comment_router = Blueprint('comments', __name__)

# Initialize service
comment_service = CommentService()


# Validation schemas
class CommentCreateSchema(Schema):
    content = fields.Str(required=True, validate=validate.Length(min=5, max=1000))
    parent_id = fields.Int(allow_none=True)


class CommentUpdateSchema(Schema):
    content = fields.Str(required=True, validate=validate.Length(min=5, max=1000))


@comment_router.route('/<item_type>/<int:item_id>', methods=['GET'])
def get_item_comments(item_type, item_id):
    """
    GET /api/comments/{itemType}/{itemId}
    Lấy danh sách comment của một item (question hoặc answer)
    """
    try:
        # Validate item type
        if item_type not in ['question', 'answer']:
            return validation_error_response('Invalid item type', {'item_type': ['Must be question or answer']})
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Get current user for personalization
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # Get item comments
        result = comment_service.get_item_comments(
            item_type=item_type,
            item_id=item_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách comment được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách comment", 500)


@comment_router.route('/<int:comment_id>/replies', methods=['GET'])
def get_comment_replies(comment_id):
    """
    GET /api/comments/{commentId}/replies
    Lấy danh sách reply của một comment
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sort_order = request.args.get('sort_order', 'asc')
        
        # Get current user for personalization
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # Get comment replies
        result = comment_service.get_comment_replies(
            comment_id=comment_id,
            page=page,
            per_page=per_page,
            sort_order=sort_order,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách reply được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách reply", 500)


@comment_router.route('/<int:comment_id>', methods=['GET'])
def get_comment_by_id(comment_id):
    """
    GET /api/comments/{id}
    Lấy chi tiết comment theo ID
    """
    try:
        # Get current user for personalization
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # Get comment details
        result = comment_service.get_comment_by_id(comment_id, user_id)
        
        return success_response(
            data=result['data'],
            message="Chi tiết comment được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy chi tiết comment", 500)


@comment_router.route('/<item_type>/<int:item_id>', methods=['POST'])
@jwt_required()
def create_comment(item_type, item_id):
    """
    POST /api/comments/{itemType}/{itemId}
    Tạo comment mới cho một item (question hoặc answer)
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
        schema = CommentCreateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Create comment
        result = comment_service.create_comment(
            item_type=item_type,
            item_id=item_id,
            user_id=int(user_id),
            content=validated_data['content'],
            parent_id=validated_data.get('parent_id')
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
        return error_response("Lỗi khi tạo comment", 500)


@comment_router.route('/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """
    PUT /api/comments/{id}
    Cập nhật comment
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
        schema = CommentUpdateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Update comment
        result = comment_service.update_comment(
            comment_id=comment_id,
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
        return error_response("Lỗi khi cập nhật comment", 500)


@comment_router.route('/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """
    DELETE /api/comments/{id}
    Xóa comment
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Delete comment
        result = comment_service.delete_comment(comment_id, int(user_id))
        
        return success_response(
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi xóa comment", 500)


@comment_router.route('/user/<int:user_id>', methods=['GET'])
def get_user_comments(user_id):
    """
    GET /api/comments/user/{userId}
    Lấy danh sách comment của user
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        item_type = request.args.get('item_type')  # question, answer, hoặc None cho tất cả
        
        # Get current user for permission check
        current_user = get_current_user()
        current_user_id = current_user.id if current_user else None
        
        # Get user comments
        result = comment_service.get_user_comments(
            user_id=user_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            item_type=item_type,
            current_user_id=current_user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách comment của user được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách comment của user", 500)


@comment_router.route('/recent', methods=['GET'])
def get_recent_comments():
    """
    GET /api/comments/recent
    Lấy danh sách comment gần đây
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        item_type = request.args.get('item_type')  # question, answer, hoặc None cho tất cả
        course_id = request.args.get('course_id', type=int)
        
        # Get current user for personalization
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # Get recent comments
        result = comment_service.get_recent_comments(
            limit=limit,
            item_type=item_type,
            course_id=course_id,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách comment gần đây được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách comment gần đây", 500)


@comment_router.route('/search', methods=['GET'])
def search_comments():
    """
    GET /api/comments/search
    Tìm kiếm comment
    """
    try:
        # Get query parameters
        search_term = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort_by', 'relevance')
        item_type = request.args.get('item_type')  # question, answer, hoặc None cho tất cả
        course_id = request.args.get('course_id', type=int)
        
        if not search_term:
            return validation_error_response('Search term is required', {'q': ['Search term is required']})
        
        # Build filters
        filters = {}
        if item_type:
            filters['item_type'] = item_type
        if course_id:
            filters['course_id'] = course_id
        
        # Get current user for personalization
        current_user = get_current_user()
        user_id = current_user.id if current_user else None
        
        # Search comments
        result = comment_service.search_comments(
            search_term=search_term,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            filters=filters,
            user_id=user_id
        )
        
        return success_response(
            data=result['data'],
            message="Kết quả tìm kiếm comment được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi tìm kiếm comment", 500)


@comment_router.route('/<int:comment_id>/mentions', methods=['GET'])
def get_comment_mentions(comment_id):
    """
    GET /api/comments/{commentId}/mentions
    Lấy danh sách user được mention trong comment
    """
    try:
        # Get comment mentions
        result = comment_service.get_comment_mentions(comment_id)
        
        return success_response(
            data=result['data'],
            message="Danh sách mention được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách mention", 500)


@comment_router.route('/<int:comment_id>/mentions', methods=['POST'])
@jwt_required()
def add_comment_mention(comment_id):
    """
    POST /api/comments/{commentId}/mentions
    Thêm mention vào comment (chỉ tác giả comment mới được phép)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get request data
        data = request.get_json()
        if not data or 'mentioned_user_id' not in data:
            return validation_error_response('Mentioned user ID is required', 
                                           {'mentioned_user_id': ['Mentioned user ID is required']})
        
        mentioned_user_id = data['mentioned_user_id']
        
        # Add mention
        result = comment_service.add_comment_mention(
            comment_id=comment_id,
            user_id=int(user_id),
            mentioned_user_id=mentioned_user_id
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
        return error_response("Lỗi khi thêm mention", 500)


@comment_router.route('/<item_type>/<int:item_id>/count', methods=['GET'])
def get_comment_count(item_type, item_id):
    """
    GET /api/comments/{itemType}/{itemId}/count
    Lấy số lượng comment của một item
    """
    try:
        # Validate item type
        if item_type not in ['question', 'answer']:
            return validation_error_response('Invalid item type', {'item_type': ['Must be question or answer']})
        
        # Get comment count
        result = comment_service.get_comment_count(item_type, item_id)
        
        return success_response(
            data=result['data'],
            message="Số lượng comment được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy số lượng comment", 500)


# Error handlers
@comment_router.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors"""
    return error_response("Không tìm thấy comment", 404)


@comment_router.errorhandler(403)
def handle_forbidden(error):
    """Handle 403 errors"""
    return error_response("Bạn không có quyền thực hiện thao tác này", 403)


@comment_router.errorhandler(401)
def handle_unauthorized(error):
    """Handle 401 errors"""
    return error_response("Yêu cầu đăng nhập để thực hiện thao tác này", 401)