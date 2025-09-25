"""
Notification Router
API endpoints for notification system management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError

from app.services.notification_service import NotificationService
from app.utils.response import success_response, error_response, validation_error_response, created_response
from app.utils.auth import get_current_user
from app.exceptions.base import ValidationException, AuthenticationException, BusinessLogicException

notification_router = Blueprint('notifications', __name__)

# Initialize service
notification_service = NotificationService()


# Validation schemas
class NotificationCreateSchema(Schema):
    user_id = fields.Int(required=True)
    type = fields.Str(required=True, validate=validate.OneOf([
        'question_answered', 'answer_accepted', 'comment_replied', 
        'vote_received', 'mentioned', 'system', 'course_update'
    ]))
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    message = fields.Str(required=True, validate=validate.Length(min=1, max=1000))
    data = fields.Dict(allow_none=True)


class BulkNotificationCreateSchema(Schema):
    user_ids = fields.List(fields.Int(), required=True, validate=validate.Length(min=1))
    type = fields.Str(required=True, validate=validate.OneOf([
        'question_answered', 'answer_accepted', 'comment_replied', 
        'vote_received', 'mentioned', 'system', 'course_update'
    ]))
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    message = fields.Str(required=True, validate=validate.Length(min=1, max=1000))
    data = fields.Dict(allow_none=True)


class SystemNotificationSchema(Schema):
    template_name = fields.Str(required=True)
    template_data = fields.Dict(allow_none=True)
    user_ids = fields.List(fields.Int(), allow_none=True)  # None means all users


@notification_router.route('/', methods=['GET'])
@jwt_required()
def get_user_notifications():
    """
    GET /api/notifications
    Lấy danh sách notification của user hiện tại
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get query parameters - support both 'limit' and 'per_page' for compatibility
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', request.args.get('limit', 20, type=int), type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Get user notifications
        result = notification_service.get_user_notifications(
            user_id=int(user_id),
            page=page,
            per_page=per_page,
            unread_only=unread_only
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách notification được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách notification", 500)


@notification_router.route('/<int:notification_id>', methods=['GET'])
@jwt_required()
def get_notification_by_id(notification_id):
    """
    GET /api/notifications/{id}
    Lấy chi tiết notification theo ID
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get notification details
        result = notification_service.get_notification_by_id(notification_id, int(user_id))
        
        return success_response(
            data=result['data'],
            message="Chi tiết notification được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy chi tiết notification", 500)


@notification_router.route('/', methods=['POST'])
@jwt_required()
def create_notification():
    """
    POST /api/notifications
    Tạo notification mới (chỉ admin hoặc system)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Check admin permission
        current_user = get_current_user()
        if not current_user or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return error_response('Admin permission required', 403)
        
        # Get request data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input
        schema = NotificationCreateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Create notification
        result = notification_service.create_notification(
            user_id=validated_data['user_id'],
            notification_type=validated_data['type'],
            title=validated_data['title'],
            message=validated_data['message'],
            data=validated_data.get('data')
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
        return error_response("Lỗi khi tạo notification", 500)


@notification_router.route('/bulk', methods=['POST'])
@jwt_required()
def create_bulk_notifications():
    """
    POST /api/notifications/bulk
    Tạo notification hàng loạt (chỉ admin)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Check admin permission
        current_user = get_current_user()
        if not current_user or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return error_response('Admin permission required', 403)
        
        # Get request data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input
        schema = BulkNotificationCreateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Create bulk notifications
        result = notification_service.create_bulk_notifications(
            user_ids=validated_data['user_ids'],
            notification_type=validated_data['type'],
            title=validated_data['title'],
            message=validated_data['message'],
            data=validated_data.get('data')
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
        return error_response("Lỗi khi tạo notification hàng loạt", 500)


@notification_router.route('/system', methods=['POST'])
@jwt_required()
def create_system_notification():
    """
    POST /api/notifications/system
    Tạo system notification từ template (chỉ admin)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Check admin permission
        current_user = get_current_user()
        if not current_user or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return error_response('Admin permission required', 403)
        
        # Get request data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input
        schema = SystemNotificationSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Create system notification
        result = notification_service.create_system_notification(
            template_name=validated_data['template_name'],
            template_data=validated_data.get('template_data', {}),
            user_ids=validated_data.get('user_ids')
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
        return error_response("Lỗi khi tạo system notification", 500)


@notification_router.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_as_read(notification_id):
    """
    POST /api/notifications/{id}/read
    Đánh dấu notification đã đọc
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Mark notification as read
        result = notification_service.mark_notification_as_read(notification_id, int(user_id))
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi đánh dấu notification đã đọc", 500)


@notification_router.route('/read-all', methods=['POST'])
@jwt_required()
def mark_all_notifications_as_read():
    """
    POST /api/notifications/read-all
    Đánh dấu tất cả notification đã đọc
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Mark all notifications as read
        result = notification_service.mark_all_notifications_as_read(int(user_id))
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi đánh dấu tất cả notification đã đọc", 500)


@notification_router.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """
    DELETE /api/notifications/{id}
    Xóa notification
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Delete notification
        result = notification_service.delete_notification(notification_id, int(user_id))
        
        return success_response(
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi xóa notification", 500)


@notification_router.route('/cleanup', methods=['DELETE'])
@jwt_required()
def delete_old_notifications():
    """
    DELETE /api/notifications/cleanup
    Xóa notification cũ (chỉ admin)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Check admin permission
        current_user = get_current_user()
        if not current_user or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return error_response('Admin permission required', 403)
        
        # Get query parameters
        days_old = request.args.get('days_old', 30, type=int)
        
        # Delete old notifications
        result = notification_service.delete_old_notifications(days_old)
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi xóa notification cũ", 500)


@notification_router.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """
    GET /api/notifications/unread-count
    Lấy số lượng notification chưa đọc
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get unread count
        result = notification_service.get_unread_count(int(user_id))
        
        return success_response(
            data=result['data'],
            message="Số lượng notification chưa đọc được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy số lượng notification chưa đọc", 500)


@notification_router.route('/by-type/<notification_type>', methods=['GET'])
@jwt_required()
def get_notifications_by_type(notification_type):
    """
    GET /api/notifications/by-type/{type}
    Lấy danh sách notification theo loại
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Get notifications by type
        result = notification_service.get_notifications_by_type(
            user_id=int(user_id),
            notification_type=notification_type,
            page=page,
            per_page=per_page,
            unread_only=unread_only
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách notification theo loại được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách notification theo loại", 500)


@notification_router.route('/statistics', methods=['GET'])
@jwt_required()
def get_notification_statistics():
    """
    GET /api/notifications/statistics
    Lấy thống kê notification (chỉ admin)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Check admin permission
        current_user = get_current_user()
        if not current_user or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return error_response('Admin permission required', 403)
        
        # Get query parameters
        time_range = request.args.get('time_range', 'week')  # day, week, month, year
        notification_type = request.args.get('type')
        
        # Build filters
        filters = {}
        if time_range:
            filters['time_range'] = time_range
        if notification_type:
            filters['type'] = notification_type
        
        # Get notification statistics
        result = notification_service.get_notification_statistics(filters)
        
        return success_response(
            data=result['data'],
            message="Thống kê notification được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy thống kê notification", 500)


@notification_router.route('/search', methods=['GET'])
@jwt_required()
def search_notifications():
    """
    GET /api/notifications/search
    Tìm kiếm notification
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get query parameters
        search_term = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        notification_type = request.args.get('type')
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        if not search_term:
            return validation_error_response('Search term is required', {'q': ['Search term is required']})
        
        # Build filters
        filters = {}
        if notification_type:
            filters['type'] = notification_type
        if unread_only:
            filters['unread_only'] = unread_only
        
        # Search notifications
        result = notification_service.search_notifications(
            user_id=int(user_id),
            search_term=search_term,
            page=page,
            per_page=per_page,
            filters=filters
        )
        
        return success_response(
            data=result['data'],
            message="Kết quả tìm kiếm notification được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi tìm kiếm notification", 500)


@notification_router.route('/recent', methods=['GET'])
@jwt_required()
def get_recent_notifications():
    """
    GET /api/notifications/recent
    Lấy danh sách notification gần đây
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        notification_type = request.args.get('type')
        
        # Get recent notifications
        result = notification_service.get_recent_notifications(
            user_id=int(user_id),
            limit=limit,
            notification_type=notification_type
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách notification gần đây được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách notification gần đây", 500)


# Specific notification endpoints
@notification_router.route('/question-answered', methods=['POST'])
@jwt_required()
def notify_question_answered():
    """
    POST /api/notifications/question-answered
    Gửi notification khi question được trả lời
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get request data
        data = request.get_json()
        if not data or 'question_id' not in data or 'answer_id' not in data:
            return validation_error_response('Question ID and Answer ID are required', 
                                           {'question_id': ['Question ID is required'], 'answer_id': ['Answer ID is required']})
        
        question_id = data['question_id']
        answer_id = data['answer_id']
        
        # Send notification
        result = notification_service.notify_question_answered(question_id, answer_id, int(user_id))
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi gửi notification question answered", 500)


@notification_router.route('/answer-accepted', methods=['POST'])
@jwt_required()
def notify_answer_accepted():
    """
    POST /api/notifications/answer-accepted
    Gửi notification khi answer được chấp nhận
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get request data
        data = request.get_json()
        if not data or 'answer_id' not in data:
            return validation_error_response('Answer ID is required', {'answer_id': ['Answer ID is required']})
        
        answer_id = data['answer_id']
        
        # Send notification
        result = notification_service.notify_answer_accepted(answer_id, int(user_id))
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi gửi notification answer accepted", 500)


@notification_router.route('/comment-replied', methods=['POST'])
@jwt_required()
def notify_comment_replied():
    """
    POST /api/notifications/comment-replied
    Gửi notification khi comment được reply
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get request data
        data = request.get_json()
        if not data or 'comment_id' not in data or 'reply_id' not in data:
            return validation_error_response('Comment ID and Reply ID are required', 
                                           {'comment_id': ['Comment ID is required'], 'reply_id': ['Reply ID is required']})
        
        comment_id = data['comment_id']
        reply_id = data['reply_id']
        
        # Send notification
        result = notification_service.notify_comment_replied(comment_id, reply_id, int(user_id))
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi gửi notification comment replied", 500)


@notification_router.route('/vote-received', methods=['POST'])
@jwt_required()
def notify_vote_received():
    """
    POST /api/notifications/vote-received
    Gửi notification khi nhận được vote
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get request data
        data = request.get_json()
        if not data or 'item_type' not in data or 'item_id' not in data or 'vote_type' not in data:
            return validation_error_response('Item type, item ID and vote type are required', 
                                           {'item_type': ['Item type is required'], 'item_id': ['Item ID is required'], 'vote_type': ['Vote type is required']})
        
        item_type = data['item_type']
        item_id = data['item_id']
        vote_type = data['vote_type']
        
        # Send notification
        result = notification_service.notify_vote_received(item_type, item_id, vote_type, int(user_id))
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi gửi notification vote received", 500)


@notification_router.route('/mentioned', methods=['POST'])
@jwt_required()
def notify_mentioned():
    """
    POST /api/notifications/mentioned
    Gửi notification khi được mention
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Get request data
        data = request.get_json()
        if not data or 'mentioned_user_id' not in data or 'item_type' not in data or 'item_id' not in data:
            return validation_error_response('Mentioned user ID, item type and item ID are required', 
                                           {'mentioned_user_id': ['Mentioned user ID is required'], 
                                            'item_type': ['Item type is required'], 
                                            'item_id': ['Item ID is required']})
        
        mentioned_user_id = data['mentioned_user_id']
        item_type = data['item_type']
        item_id = data['item_id']
        
        # Send notification
        result = notification_service.notify_mentioned(mentioned_user_id, item_type, item_id, int(user_id))
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi gửi notification mentioned", 500)


# Error handlers
@notification_router.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors"""
    return error_response("Không tìm thấy notification", 404)


@notification_router.errorhandler(403)
def handle_forbidden(error):
    """Handle 403 errors"""
    return error_response("Bạn không có quyền thực hiện thao tác này", 403)


@notification_router.errorhandler(401)
def handle_unauthorized(error):
    """Handle 401 errors"""
    return error_response("Yêu cầu đăng nhập để thực hiện thao tác này", 401)