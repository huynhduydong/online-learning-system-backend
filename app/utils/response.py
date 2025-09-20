"""
Response utilities cho API responses chuẩn
"""

from flask import jsonify
from typing import Any, Dict, Optional


def success_response(data: Any = None, message: str = None, status_code: int = 200) -> tuple:
    """
    Tạo success response chuẩn
    
    Args:
        data: Dữ liệu trả về
        message: Thông báo thành công
        status_code: HTTP status code
    
    Returns:
        Tuple (response, status_code)
    """
    response = {
        'success': True
    }
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code


def error_response(
    message: str, 
    status_code: int = 400, 
    error_code: str = None, 
    details: Dict = None
) -> tuple:
    """
    Tạo error response chuẩn
    
    Args:
        message: Thông báo lỗi
        status_code: HTTP status code
        error_code: Mã lỗi cụ thể
        details: Chi tiết lỗi
    
    Returns:
        Tuple (response, status_code)
    """
    response = {
        'success': False,
        'error': message
    }
    
    if error_code:
        response['error_code'] = error_code
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code


def validation_error_response(message: str, field_errors: Dict = None) -> tuple:
    """
    Tạo validation error response
    
    Args:
        message: Thông báo lỗi chính
        field_errors: Lỗi cụ thể cho từng field
    
    Returns:
        Tuple (response, status_code)
    """
    details = {}
    if field_errors:
        details['field_errors'] = field_errors
    
    return error_response(
        message=message,
        status_code=400,
        error_code='VALIDATION_ERROR',
        details=details
    )


def paginated_response(
    data: list, 
    page: int, 
    per_page: int, 
    total: int, 
    message: str = None
) -> tuple:
    """
    Tạo paginated response chuẩn
    
    Args:
        data: Danh sách dữ liệu
        page: Trang hiện tại
        per_page: Số item per page
        total: Tổng số items
        message: Thông báo
    
    Returns:
        Tuple (response, status_code)
    """
    total_pages = (total + per_page - 1) // per_page
    
    pagination_info = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }
    
    response_data = {
        'items': data,
        'pagination': pagination_info
    }
    
    return success_response(data=response_data, message=message)


def created_response(data: Any = None, message: str = "Resource created successfully") -> tuple:
    """Tạo response cho resource được tạo thành công"""
    return success_response(data=data, message=message, status_code=201)


def no_content_response() -> tuple:
    """Tạo response cho thao tác thành công nhưng không có data trả về"""
    return '', 204