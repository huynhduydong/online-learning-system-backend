"""
Cart Router
API endpoints for cart operations
"""

from flask import Blueprint, request, session
from app.services.cart_service import CartService
from app.utils.response import success_response, error_response
from app.utils.auth import get_current_user_optional, get_session_id
from app.exceptions.validation_exception import ValidationException

cart_router = Blueprint('cart', __name__)


@cart_router.route('/', methods=['GET'])
def get_cart():
    """
    Get current cart information
    
    Returns: Cart with items, totals, and metadata
    Authentication: Optional (supports guest carts)
    Session: Uses session ID for guest users
    """
    try:
        cart_service = CartService()
        current_user = get_current_user_optional()
        session_id = get_session_id()
        user_id = current_user.id if current_user else None
        
        cart_data = cart_service.get_cart(user_id=user_id, session_id=session_id)
        
        return success_response(
            data=cart_data,
            message="Cart retrieved successfully"
        )
        
    except ValidationException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Internal server error", 500)


@cart_router.route('/items', methods=['POST'])
def add_item_to_cart():
    """
    Add item to cart
    
    course_id: ID of the course to add
    Returns: Updated cart information
    Idempotent: Returns current state if course already in cart
    Conflict: Returns 409 if duplicate detected
    """
    try:
        data = request.get_json()
        if not data or 'course_id' not in data:
            return error_response("course_id is required", 400)
        
        course_id = data.get('course_id')
        if not isinstance(course_id, int) or course_id <= 0:
            return error_response("Invalid course_id", 400)
        
        cart_service = CartService()
        current_user = get_current_user_optional()
        session_id = get_session_id()
        user_id = current_user.id if current_user else None
        
        cart_data = cart_service.add_item_to_cart(
            course_id=course_id,
            user_id=user_id,
            session_id=session_id
        )
        
        return success_response(
            data=cart_data,
            message="Item added to cart successfully"
        )
        
    except ValidationException as e:
        status_code = getattr(e, 'status_code', 400)
        return error_response(str(e), status_code)
    except Exception as e:
        return error_response("Internal server error", 500)


@cart_router.route('/items/<int:item_id>', methods=['DELETE'])
def remove_item_from_cart(item_id):
    """
    Remove item from cart
    
    item_id: ID of the cart item to remove
    Returns: Updated cart information
    Authentication: Optional (supports guest carts)
    """
    try:
        if item_id <= 0:
            return error_response("Invalid item ID", 400)
        
        cart_service = CartService()
        current_user = get_current_user_optional()
        session_id = get_session_id()
        user_id = current_user.id if current_user else None
        
        cart_data = cart_service.remove_item_from_cart(
            item_id=item_id,
            user_id=user_id,
            session_id=session_id
        )
        
        return success_response(
            data=cart_data,
            message="Item removed from cart successfully"
        )
        
    except ValidationException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Internal server error", 500)


@cart_router.route('/apply-coupon', methods=['POST'])
def apply_coupon():
    """
    Apply coupon to cart
    
    coupon_code: Coupon code to apply
    Returns: Cart with coupon applied and calculation breakdown
    Calculations: Includes initial total, tax/fee (stub), and final amount
    """
    try:
        data = request.get_json()
        if not data or 'coupon_code' not in data:
            return error_response("coupon_code is required", 400)
        
        coupon_code = data.get('coupon_code', '').strip()
        if not coupon_code:
            return error_response("coupon_code cannot be empty", 400)
        
        cart_service = CartService()
        current_user = get_current_user_optional()
        session_id = get_session_id()
        user_id = current_user.id if current_user else None
        
        cart_data = cart_service.apply_coupon(
            coupon_code=coupon_code,
            user_id=user_id,
            session_id=session_id
        )
        
        return success_response(
            data=cart_data,
            message="Coupon applied successfully"
        )
        
    except ValidationException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Internal server error", 500)


@cart_router.route('/coupon', methods=['DELETE'])
def remove_coupon():
    """
    Remove coupon from cart
    
    Returns: Updated cart information without coupon
    Authentication: Optional (supports guest carts)
    """
    try:
        cart_service = CartService()
        current_user = get_current_user_optional()
        session_id = get_session_id()
        user_id = current_user.id if current_user else None
        
        cart_data = cart_service.remove_coupon(
            user_id=user_id,
            session_id=session_id
        )
        
        return success_response(
            data=cart_data,
            message="Coupon removed successfully"
        )
        
    except ValidationException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Internal server error", 500)


@cart_router.route('/merge', methods=['POST'])
def merge_guest_cart():
    """
    Merge guest cart on login
    
    Returns: Merged cart information
    Authentication: Required (user must be logged in)
    Usage: Called automatically during login process
    """
    try:
        current_user = get_current_user_optional()
        if not current_user:
            return error_response("Authentication required", 401)
        
        session_id = get_session_id()
        if not session_id:
            return error_response("Session ID required", 400)
        
        cart_service = CartService()
        
        cart_data = cart_service.merge_guest_cart_on_login(
            user_id=current_user.id,
            session_id=session_id
        )
        
        return success_response(
            data=cart_data,
            message="Guest cart merged successfully"
        )
        
    except ValidationException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Internal server error", 500)


@cart_router.route('/clear', methods=['DELETE'])
def clear_cart():
    """
    Clear all items from cart
    
    Returns: Empty cart information
    Authentication: Optional (supports guest carts)
    """
    try:
        cart_service = CartService()
        current_user = get_current_user_optional()
        session_id = get_session_id()
        user_id = current_user.id if current_user else None
        
        cart_data = cart_service.clear_cart(
            user_id=user_id,
            session_id=session_id
        )
        
        return success_response(
            data=cart_data,
            message="Cart cleared successfully"
        )
        
    except ValidationException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Internal server error", 500)


@cart_router.route('/coupons', methods=['GET'])
def get_available_coupons():
    """
    Get available public coupons
    
    limit: Maximum number of coupons to return (default: 10)
    Returns: List of available coupons with details
    Authentication: Not required
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        if limit <= 0 or limit > 50:
            return error_response("Limit must be between 1 and 50", 400)
        
        cart_service = CartService()
        coupons = cart_service.get_available_coupons(limit=limit)
        
        return success_response(
            data={"coupons": coupons},
            message="Available coupons retrieved successfully"
        )
        
    except ValidationException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Internal server error", 500)


@cart_router.route('/health', methods=['GET'])
def cart_health_check():
    """
    Cart service health check
    
    Returns: Service status
    Authentication: Not required
    """
    try:
        return success_response(
            data={"status": "healthy", "service": "cart"},
            message="Cart service is healthy"
        )
    except Exception as e:
        return error_response("Cart service unhealthy", 500)