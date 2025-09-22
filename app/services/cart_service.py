"""
Cart Service
Handles business logic for cart operations, coupon application, and guest cart merging
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from app import db
from app.dao.cart_dao import CartDAO, CouponDAO
from app.models.cart import Cart, CartItem, CartStatus
from app.models.coupon import Coupon, CouponType, CouponStatus
from app.models.course import Course
from app.exceptions.validation_exception import ValidationException


class CartService:
    """Service for cart operations"""
    
    def __init__(self):
        self.cart_dao = CartDAO()
        self.coupon_dao = CouponDAO()
    
    def get_cart(self, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current cart information
        
        Args:
            user_id: User ID for authenticated users
            session_id: Session ID for guest users
            
        Returns:
            Cart information with items and totals
        """
        try:
            # Get or create cart
            if user_id:
                cart = self.cart_dao.get_active_cart_by_user(user_id)
                if not cart:
                    cart = self.cart_dao.create_cart(user_id=user_id)
            else:
                if not session_id:
                    session_id = str(uuid.uuid4())
                cart = self.cart_dao.get_active_cart_by_session(session_id)
                if not cart:
                    cart = self.cart_dao.create_cart(session_id=session_id)
            
            # Format response
            return self._format_cart_response(cart, session_id if not user_id else None)
            
        except Exception as e:
            raise ValidationException(f"Failed to get cart: {str(e)}")
    
    def add_item_to_cart(self, course_id: int, user_id: Optional[int] = None, 
                        session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Add item to cart (idempotent operation)
        
        Args:
            course_id: Course ID to add
            user_id: User ID for authenticated users
            session_id: Session ID for guest users
            
        Returns:
            Updated cart information
            
        Raises:
            ValidationException: If course already in cart or other validation errors
        """
        try:
            # Validate course exists and is available
            course = db.session.query(Course).get(course_id)
            if not course:
                raise ValidationException(f"Course {course_id} not found")
            
            if not course.is_published:
                raise ValidationException("Course is not available for purchase")
            
            # Get or create cart
            if user_id:
                cart = self.cart_dao.get_active_cart_by_user(user_id)
                if not cart:
                    cart = self.cart_dao.create_cart(user_id=user_id)
            else:
                if not session_id:
                    session_id = str(uuid.uuid4())
                cart = self.cart_dao.get_active_cart_by_session(session_id)
                if not cart:
                    cart = self.cart_dao.create_cart(session_id=session_id)
            
            # Check if course already in cart (idempotency)
            existing_item = self.cart_dao.get_cart_item_by_course(cart.id, course_id)
            if existing_item:
                # Return current cart state (idempotent behavior)
                return self._format_cart_response(cart, session_id if not user_id else None)
            
            # Add item to cart
            cart_item = self.cart_dao.add_item_to_cart(cart.id, course_id)
            
            # Update cart totals
            cart = self.cart_dao.update_cart_totals(cart.id)
            
            return self._format_cart_response(cart, session_id if not user_id else None)
            
        except ValueError as e:
            if "already in cart" in str(e):
                raise ValidationException("Course already in cart", status_code=409)
            raise ValidationException(str(e))
        except Exception as e:
            raise ValidationException(f"Failed to add item to cart: {str(e)}")
    
    def remove_item_from_cart(self, item_id: int, user_id: Optional[int] = None, 
                             session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove item from cart
        
        Args:
            item_id: Cart item ID to remove
            user_id: User ID for authenticated users
            session_id: Session ID for guest users
            
        Returns:
            Updated cart information
        """
        try:
            # Get cart
            if user_id:
                cart = self.cart_dao.get_active_cart_by_user(user_id)
            else:
                if not session_id:
                    raise ValidationException("Session ID required for guest users")
                cart = self.cart_dao.get_active_cart_by_session(session_id)
            
            if not cart:
                raise ValidationException("Cart not found")
            
            # Remove item
            removed = self.cart_dao.remove_item_from_cart(cart.id, item_id)
            if not removed:
                raise ValidationException("Item not found in cart")
            
            # Update cart totals
            cart = self.cart_dao.update_cart_totals(cart.id)
            
            return self._format_cart_response(cart, session_id if not user_id else None)
            
        except Exception as e:
            if isinstance(e, ValidationException):
                raise e
            raise ValidationException(f"Failed to remove item from cart: {str(e)}")
    
    def apply_coupon(self, coupon_code: str, user_id: Optional[int] = None, 
                    session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Apply coupon to cart
        
        Args:
            coupon_code: Coupon code to apply
            user_id: User ID for authenticated users
            session_id: Session ID for guest users
            
        Returns:
            Cart with coupon applied and calculation breakdown
        """
        try:
            # Get cart
            if user_id:
                cart = self.cart_dao.get_active_cart_by_user(user_id)
            else:
                if not session_id:
                    raise ValidationException("Session ID required for guest users")
                cart = self.cart_dao.get_active_cart_by_session(session_id)
            
            if not cart:
                raise ValidationException("Cart not found")
            
            if not cart.items:
                raise ValidationException("Cannot apply coupon to empty cart")
            
            # Get and validate coupon
            coupon = self.coupon_dao.get_valid_coupon_by_code(coupon_code)
            if not coupon:
                raise ValidationException("Invalid or expired coupon code")
            
            # Check user-specific usage limits
            if user_id and coupon.usage_limit_per_user:
                user_usage_count = self.coupon_dao.get_user_coupon_usage_count(coupon.id, user_id)
                if user_usage_count >= coupon.usage_limit_per_user:
                    raise ValidationException("Coupon usage limit exceeded for this user")
            
            # Check minimum order amount
            if coupon.minimum_order_amount and cart.total_amount < coupon.minimum_order_amount:
                raise ValidationException(f"Minimum order amount of ${coupon.minimum_order_amount:.2f} required")
            
            # Calculate discount amount based on coupon type
            if coupon.type == CouponType.PERCENTAGE:
                discount_amount = cart.total_amount * (coupon.value / 100)
            elif coupon.type == CouponType.FIXED_AMOUNT:
                discount_amount = min(coupon.value, cart.total_amount)
            else:
                raise ValidationException("Invalid coupon type")
            
            # Apply coupon to cart
            cart.apply_coupon(coupon.code, discount_amount)
            
            # Update cart in database
            db.session.commit()
            
            # Calculate breakdown
            breakdown = self._calculate_order_breakdown(cart)
            
            # Format response
            response = self._format_cart_response(cart, session_id if not user_id else None)
            response['calculation_breakdown'] = breakdown
            response['coupon_applied'] = {
                'code': coupon.code,
                'description': coupon.description,
                'discount_amount': float(discount_amount),
                'type': coupon.type.value
            }
            
            return response
            
        except Exception as e:
            db.session.rollback()
            if isinstance(e, ValidationException):
                raise e
            raise ValidationException(f"Failed to apply coupon: {str(e)}")
    
    def remove_coupon(self, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove coupon from cart
        
        Args:
            user_id: User ID for authenticated users
            session_id: Session ID for guest users
            
        Returns:
            Updated cart information
        """
        try:
            # Get cart
            if user_id:
                cart = self.cart_dao.get_active_cart_by_user(user_id)
            else:
                if not session_id:
                    raise ValidationException("Session ID required for guest users")
                cart = self.cart_dao.get_active_cart_by_session(session_id)
            
            if not cart:
                raise ValidationException("Cart not found")
            
            # Remove coupon
            cart.remove_coupon()
            db.session.commit()
            
            return self._format_cart_response(cart, session_id if not user_id else None)
            
        except Exception as e:
            db.session.rollback()
            if isinstance(e, ValidationException):
                raise e
            raise ValidationException(f"Failed to remove coupon: {str(e)}")
    
    def merge_guest_cart_on_login(self, user_id: int, session_id: str) -> Dict[str, Any]:
        """
        Merge guest cart into user cart when user logs in
        
        Args:
            user_id: User ID
            session_id: Guest session ID
            
        Returns:
            Merged cart information
        """
        try:
            # Get guest cart
            guest_cart = self.cart_dao.get_active_cart_by_session(session_id)
            if not guest_cart or not guest_cart.items:
                # No guest cart or empty cart, just return user's cart
                return self.get_cart(user_id=user_id)
            
            # Get or create user cart
            user_cart = self.cart_dao.get_active_cart_by_user(user_id)
            if not user_cart:
                # Convert guest cart to user cart
                user_cart = self.cart_dao.convert_guest_cart_to_user(guest_cart.id, user_id)
            else:
                # Merge guest cart into user cart
                user_cart = self.cart_dao.merge_carts(guest_cart.id, user_cart.id)
            
            return self._format_cart_response(user_cart)
            
        except Exception as e:
            raise ValidationException(f"Failed to merge carts: {str(e)}")
    
    def clear_cart(self, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear all items from cart
        
        Args:
            user_id: User ID for authenticated users
            session_id: Session ID for guest users
            
        Returns:
            Empty cart information
        """
        try:
            # Get cart
            if user_id:
                cart = self.cart_dao.get_active_cart_by_user(user_id)
            else:
                if not session_id:
                    raise ValidationException("Session ID required for guest users")
                cart = self.cart_dao.get_active_cart_by_session(session_id)
            
            if not cart:
                raise ValidationException("Cart not found")
            
            # Clear cart
            self.cart_dao.clear_cart(cart.id)
            
            return {
                'success': True,
                'message': 'Cart cleared successfully'
            }
            
        except Exception as e:
            if isinstance(e, ValidationException):
                raise e
            raise ValidationException(f"Failed to clear cart: {str(e)}")
    
    def get_available_coupons(self, limit: Optional[int] = 10) -> List[Dict[str, Any]]:
        """
        Get available public coupons
        
        Args:
            limit: Maximum number of coupons to return
            
        Returns:
            List of available coupons
        """
        try:
            coupons = self.coupon_dao.get_active_coupons(limit)
            
            return [
                {
                    'code': coupon.code,
                    'description': coupon.description,
                    'type': coupon.type.value,
                    'discount_value': float(coupon.value),
                    'minimum_order_amount': float(coupon.minimum_order_amount) if coupon.minimum_order_amount else None,
                    'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
                    'usage_limit': coupon.usage_limit,
                    'total_used': coupon.total_used
                }
                for coupon in coupons
            ]
            
        except Exception as e:
            raise ValidationException(f"Failed to get available coupons: {str(e)}")
    
    def _format_cart_response(self, cart: Cart, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Format cart response
        
        Args:
            cart: Cart object
            session_id: Session ID for guest users
            
        Returns:
            Formatted cart response
        """
        items = []
        for item in cart.items:
            items.append({
                'id': item.id,
                'course_id': item.course_id,
                'course_title': item.course_title,
                'course_instructor': item.course_instructor,
                'price': float(item.price),
                'original_price': float(item.original_price),
                'added_at': item.added_at.isoformat()
            })
        
        response = {
            'cart_id': cart.id,
            'items': items,
            'item_count': cart.item_count,
            'total_amount': float(cart.total_amount),
            'discount_amount': float(cart.discount_amount),
            'final_amount': float(cart.final_amount),
            'coupon_code': cart.coupon_code,
            'status': cart.status.value,
            'created_at': cart.created_at.isoformat(),
            'updated_at': cart.updated_at.isoformat(),
            'expires_at': cart.expires_at.isoformat() if cart.expires_at else None
        }
        
        if session_id:
            response['session_id'] = session_id
        
        return response
    
    def _calculate_order_breakdown(self, cart: Cart) -> Dict[str, Any]:
        """
        Calculate order breakdown with taxes and fees
        
        Args:
            cart: Cart object
            
        Returns:
            Order breakdown
        """
        subtotal = cart.total_amount
        discount = cart.discount_amount
        
        # Calculate tax (stub - 8.5% for demo)
        tax_rate = Decimal('0.085')
        tax_amount = (subtotal - discount) * tax_rate
        
        # Calculate processing fee (stub - $2.50 for demo)
        processing_fee = Decimal('2.50')
        
        # Final total
        final_total = subtotal - discount + tax_amount + processing_fee
        
        return {
            'subtotal': float(subtotal),
            'discount': float(discount),
            'tax_rate': float(tax_rate),
            'tax_amount': float(tax_amount),
            'processing_fee': float(processing_fee),
            'final_total': float(final_total)
        }
    
    @staticmethod
    def cleanup_expired_carts(days_old: int = 30) -> int:
        """
        Clean up expired carts (utility method for background tasks)
        
        Args:
            days_old: Days old to consider expired
            
        Returns:
            Number of carts cleaned up
        """
        try:
            cart_dao = CartDAO()
            return cart_dao.cleanup_expired_carts(days_old)
        except Exception as e:
            raise ValidationException(f"Failed to cleanup expired carts: {str(e)}")