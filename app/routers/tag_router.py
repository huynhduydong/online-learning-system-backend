"""
Tag Router
API endpoints for Q&A tags management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError

from app.services.tag_service import TagService
from app.utils.response import success_response, error_response, validation_error_response, created_response
from app.utils.auth import get_current_user
from app.exceptions.base import ValidationException, AuthenticationException, BusinessLogicException

tag_router = Blueprint('tags', __name__)

# Initialize service
tag_service = TagService()


# Validation schemas
class TagCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    description = fields.Str(allow_none=True, validate=validate.Length(max=500))
    category = fields.Str(allow_none=True, validate=validate.Length(max=50))
    color = fields.Str(allow_none=True, validate=validate.Length(max=7))  # Hex color code


class TagUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=2, max=50))
    description = fields.Str(allow_none=True, validate=validate.Length(max=500))
    category = fields.Str(allow_none=True, validate=validate.Length(max=50))
    color = fields.Str(allow_none=True, validate=validate.Length(max=7))


class QuestionTagsUpdateSchema(Schema):
    tag_names = fields.List(fields.Str(validate=validate.Length(min=2, max=50)), required=True, validate=validate.Length(min=1, max=5))


@tag_router.route('/', methods=['GET'])
def get_tags():
    """
    GET /api/tags
    Lấy danh sách tất cả tags
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        sort_by = request.args.get('sort_by', 'name')
        sort_order = request.args.get('sort_order', 'asc')
        category = request.args.get('category')
        search = request.args.get('search', '').strip()
        
        # Build filters
        filters = {}
        if category:
            filters['category'] = category
        if search:
            filters['search'] = search
        
        # Get tags
        result = tag_service.get_tags(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách tags được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách tags", 500)


@tag_router.route('/<int:tag_id>', methods=['GET'])
def get_tag_by_id(tag_id):
    """
    GET /api/tags/{id}
    Lấy chi tiết tag theo ID
    """
    try:
        # Get tag details
        result = tag_service.get_tag_by_id(tag_id)
        
        return success_response(
            data=result['data'],
            message="Chi tiết tag được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy chi tiết tag", 500)


@tag_router.route('/name/<tag_name>', methods=['GET'])
def get_tag_by_name(tag_name):
    """
    GET /api/tags/name/{tagName}
    Lấy chi tiết tag theo tên
    """
    try:
        # Get tag details
        result = tag_service.get_tag_by_name(tag_name)
        
        return success_response(
            data=result['data'],
            message="Chi tiết tag được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy chi tiết tag", 500)


@tag_router.route('/', methods=['POST'])
@jwt_required()
def create_tag():
    """
    POST /api/tags
    Tạo tag mới (chỉ admin hoặc instructor)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Check permission (implement based on your user role system)
        current_user = get_current_user()
        if not current_user or not (hasattr(current_user, 'is_admin') and current_user.is_admin) and not (hasattr(current_user, 'role') and current_user.role in ['admin', 'instructor']):
            return error_response('Admin or instructor permission required', 403)
        
        # Get request data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input
        schema = TagCreateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Create tag
        result = tag_service.create_tag(
            name=validated_data['name'],
            description=validated_data.get('description'),
            category=validated_data.get('category'),
            color=validated_data.get('color'),
            created_by=int(user_id)
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
        return error_response("Lỗi khi tạo tag", 500)


@tag_router.route('/<int:tag_id>', methods=['PUT'])
@jwt_required()
def update_tag(tag_id):
    """
    PUT /api/tags/{id}
    Cập nhật tag (chỉ admin hoặc instructor)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Check permission (implement based on your user role system)
        current_user = get_current_user()
        if not current_user or not (hasattr(current_user, 'is_admin') and current_user.is_admin) and not (hasattr(current_user, 'role') and current_user.role in ['admin', 'instructor']):
            return error_response('Admin or instructor permission required', 403)
        
        # Get request data
        data = request.get_json()
        if not data:
            return validation_error_response('No data provided', {'general': ['Request body is required']})
        
        # Validate input
        schema = TagUpdateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Update tag
        result = tag_service.update_tag(tag_id, validated_data)
        
        return success_response(
            data=result['data'],
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi cập nhật tag", 500)


@tag_router.route('/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def delete_tag(tag_id):
    """
    DELETE /api/tags/{id}
    Xóa tag (chỉ admin)
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
        
        # Delete tag
        result = tag_service.delete_tag(tag_id)
        
        return success_response(
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi xóa tag", 500)


@tag_router.route('/search', methods=['GET'])
def search_tags():
    """
    GET /api/tags/search
    Tìm kiếm tags
    """
    try:
        # Get query parameters
        search_term = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)
        category = request.args.get('category')
        
        if not search_term:
            return validation_error_response('Search term is required', {'q': ['Search term is required']})
        
        # Build filters
        filters = {}
        if category:
            filters['category'] = category
        
        # Search tags
        result = tag_service.search_tags(
            search_term=search_term,
            limit=limit,
            filters=filters
        )
        
        return success_response(
            data=result['data'],
            message="Kết quả tìm kiếm tags được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi tìm kiếm tags", 500)


@tag_router.route('/popular', methods=['GET'])
def get_popular_tags():
    """
    GET /api/tags/popular
    Lấy danh sách tags phổ biến
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        time_range = request.args.get('time_range', 'month')  # week, month, year, all
        category = request.args.get('category')
        course_id = request.args.get('course_id', type=int)
        
        # Build filters
        filters = {}
        if category:
            filters['category'] = category
        if course_id:
            filters['course_id'] = course_id
        
        # Get popular tags
        result = tag_service.get_popular_tags(
            limit=limit,
            time_range=time_range,
            filters=filters
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách tags phổ biến được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách tags phổ biến", 500)


@tag_router.route('/question/<int:question_id>', methods=['GET'])
def get_question_tags(question_id):
    """
    GET /api/tags/question/{questionId}
    Lấy danh sách tags của một question
    """
    try:
        # Get question tags
        result = tag_service.get_question_tags(question_id)
        
        return success_response(
            data=result['data'],
            message="Danh sách tags của question được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách tags của question", 500)


@tag_router.route('/question/<int:question_id>', methods=['POST'])
@jwt_required()
def add_question_tags(question_id):
    """
    POST /api/tags/question/{questionId}
    Thêm tags cho question (chỉ tác giả question)
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
        
        tag_names = data.get('tag_names', [])
        if not tag_names or not isinstance(tag_names, list):
            return validation_error_response('Tag names are required', {'tag_names': ['Tag names are required']})
        
        # Add question tags
        result = tag_service.add_question_tags(
            question_id=question_id,
            tag_names=tag_names,
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
        return error_response("Lỗi khi thêm tags cho question", 500)


@tag_router.route('/question/<int:question_id>/tag/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def remove_question_tag(question_id, tag_id):
    """
    DELETE /api/tags/question/{questionId}/tag/{tagId}
    Xóa tag khỏi question (chỉ tác giả question)
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        if not user_id:
            return error_response('Authentication required', 401)
        
        # Remove question tag
        result = tag_service.remove_question_tag(
            question_id=question_id,
            tag_id=tag_id,
            user_id=int(user_id)
        )
        
        return success_response(
            message=result['message']
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except BusinessLogicException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Lỗi khi xóa tag khỏi question", 500)


@tag_router.route('/question/<int:question_id>', methods=['PUT'])
@jwt_required()
def update_question_tags(question_id):
    """
    PUT /api/tags/question/{questionId}
    Cập nhật tất cả tags của question (chỉ tác giả question)
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
        schema = QuestionTagsUpdateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return validation_error_response('Validation failed', err.messages)
        
        # Update question tags
        result = tag_service.update_question_tags(
            question_id=question_id,
            tag_names=validated_data['tag_names'],
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
        return error_response("Lỗi khi cập nhật tags của question", 500)


@tag_router.route('/statistics', methods=['GET'])
def get_tag_statistics():
    """
    GET /api/tags/statistics
    Lấy thống kê về tags
    """
    try:
        # Get query parameters
        category = request.args.get('category')
        time_range = request.args.get('time_range', 'all')  # week, month, year, all
        course_id = request.args.get('course_id', type=int)
        
        # Build filters
        filters = {}
        if category:
            filters['category'] = category
        if time_range:
            filters['time_range'] = time_range
        if course_id:
            filters['course_id'] = course_id
        
        # Get tag statistics
        result = tag_service.get_tag_statistics(filters)
        
        return success_response(
            data=result['data'],
            message="Thống kê tags được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy thống kê tags", 500)


@tag_router.route('/<int:tag_id>/related', methods=['GET'])
def get_related_tags(tag_id):
    """
    GET /api/tags/{tagId}/related
    Lấy danh sách tags liên quan
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        
        # Get related tags
        result = tag_service.get_related_tags(tag_id, limit)
        
        return success_response(
            data=result['data'],
            message="Danh sách tags liên quan được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách tags liên quan", 500)


@tag_router.route('/categories', methods=['GET'])
def get_tag_categories():
    """
    GET /api/tags/categories
    Lấy danh sách categories của tags
    """
    try:
        # Get tag categories
        result = tag_service.get_tag_categories()
        
        return success_response(
            data=result['data'],
            message="Danh sách categories được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách categories", 500)


@tag_router.route('/category/<category_name>', methods=['GET'])
def get_tags_by_category(category_name):
    """
    GET /api/tags/category/{categoryName}
    Lấy danh sách tags theo category
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        sort_by = request.args.get('sort_by', 'name')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Get tags by category
        result = tag_service.get_tags_by_category(
            category=category_name,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return success_response(
            data=result['data'],
            message="Danh sách tags theo category được lấy thành công"
        )
        
    except ValidationException as e:
        return validation_error_response(str(e), {'general': [str(e)]})
    except Exception as e:
        return error_response("Lỗi khi lấy danh sách tags theo category", 500)


# Error handlers
@tag_router.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors"""
    return error_response("Không tìm thấy tag", 404)


@tag_router.errorhandler(403)
def handle_forbidden(error):
    """Handle 403 errors"""
    return error_response("Bạn không có quyền thực hiện thao tác này", 403)


@tag_router.errorhandler(401)
def handle_unauthorized(error):
    """Handle 401 errors"""
    return error_response("Yêu cầu đăng nhập để thực hiện thao tác này", 401)