"""
Cart DAO (Data Access Object)
Handles database operations for cart and cart items
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_

from app import db
from app.dao.base_dao import BaseDAO
from app.models.cart import Cart, CartItem, CartStatus
from app.models.coupon import Coupon, CouponUsage, CouponStatus
from app.models.course import Course


class CartDAO(BaseDAO):
    """DAO for Cart operations"""
    
    def __init__(self):
        super().__init__(Cart)
    
    def get_active_cart_by_user(self, user_id: int) -> Optional[Cart]:
        """
        Get active cart for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Cart or None
        """
        try:
            return self.session.query(Cart).filter(
                and_(
                    Cart.user_id == user_id,
                    Cart.status == CartStatus.ACTIVE
                )
            ).options(joinedload(Cart.items)).first()
        except SQLAlchemyError as e:
            raise e
    
    def get_active_cart_by_session(self, session_id: str) -> Optional[Cart]:
        """
        Get active cart for a guest session
        
        Args:
            session_id: Session ID
            
        Returns:
            Cart or None
        """
        try:
            return self.session.query(Cart).filter(
                and_(
                    Cart.session_id == session_id,
                    Cart.status == CartStatus.ACTIVE,
                    Cart.user_id.is_(None)
                )
            ).options(joinedload(Cart.items)).first()
        except SQLAlchemyError as e:
            raise e
    
    def create_cart(self, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Cart:
        """
        Create a new cart
        
        Args:
            user_id: User ID for authenticated users
            session_id: Session ID for guest users
            
        Returns:
            Created cart
        """
        try:
            cart = Cart(user_id=user_id, session_id=session_id)
            self.session.add(cart)
            self.session.commit()
            return cart
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def add_item_to_cart(self, cart_id: int, course_id: int) -> CartItem:
        """
        Add item to cart
        
        Args:
            cart_id: Cart ID
            course_id: Course ID
            
        Returns:
            Created cart item
            
        Raises:
            IntegrityError: If course already in cart
        """
        try:
            # Get course details
            course = self.session.query(Course).get(course_id)
            if not course:
                raise ValueError(f"Course {course_id} not found")
            
            # Create cart item
            cart_item = CartItem(
                cart_id=cart_id,
                course_id=course_id,
                course_title=course.title,
                course_instructor=course.instructor_name or "Unknown",
                price=course.price,
                original_price=course.original_price or course.price
            )
            
            self.session.add(cart_item)
            self.session.commit()
            return cart_item
            
        except IntegrityError as e:
            self.session.rollback()
            if "unique_cart_course" in str(e):
                raise ValueError("Course already in cart")
            raise e
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def remove_item_from_cart(self, cart_id: int, item_id: int) -> bool:
        """
        Remove item from cart
        
        Args:
            cart_id: Cart ID
            item_id: Cart item ID
            
        Returns:
            True if removed, False if not found
        """
        try:
            item = self.session.query(CartItem).filter(
                and_(
                    CartItem.id == item_id,
                    CartItem.cart_id == cart_id
                )
            ).first()
            
            if not item:
                return False
            
            self.session.delete(item)
            self.session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def update_cart_totals(self, cart_id: int) -> Cart:
        """
        Update cart totals based on items
        
        Args:
            cart_id: Cart ID
            
        Returns:
            Updated cart
        """
        try:
            cart = self.session.query(Cart).options(joinedload(Cart.items)).get(cart_id)
            if not cart:
                raise ValueError(f"Cart {cart_id} not found")
            
            cart.calculate_totals()
            self.session.commit()
            return cart
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def clear_cart(self, cart_id: int) -> bool:
        """
        Clear all items from cart
        
        Args:
            cart_id: Cart ID
            
        Returns:
            True if cleared
        """
        try:
            # Delete all items
            self.session.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
            
            # Update cart totals
            cart = self.session.query(Cart).get(cart_id)
            if cart:
                cart.item_count = 0
                cart.total_amount = 0.00
                cart.discount_amount = 0.00
                cart.final_amount = 0.00
                cart.coupon_code = None
                cart.updated_at = datetime.utcnow()
            
            self.session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def merge_carts(self, guest_cart_id: int, user_cart_id: int) -> Cart:
        """
        Merge guest cart into user cart
        
        Args:
            guest_cart_id: Guest cart ID
            user_cart_id: User cart ID
            
        Returns:
            Updated user cart
        """
        try:
            guest_cart = self.session.query(Cart).options(joinedload(Cart.items)).get(guest_cart_id)
            user_cart = self.session.query(Cart).options(joinedload(Cart.items)).get(user_cart_id)
            
            if not guest_cart or not user_cart:
                raise ValueError("Cart not found")
            
            # Get existing course IDs in user cart
            existing_course_ids = {item.course_id for item in user_cart.items}
            
            # Move items from guest cart to user cart (avoid duplicates)
            for item in guest_cart.items:
                if item.course_id not in existing_course_ids:
                    item.cart_id = user_cart_id
                    existing_course_ids.add(item.course_id)
            
            # Mark guest cart as converted
            guest_cart.status = CartStatus.CONVERTED
            guest_cart.updated_at = datetime.utcnow()
            
            # Update user cart totals
            user_cart.calculate_totals()
            
            self.session.commit()
            return user_cart
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def convert_guest_cart_to_user(self, cart_id: int, user_id: int) -> Cart:
        """
        Convert guest cart to user cart
        
        Args:
            cart_id: Cart ID
            user_id: User ID
            
        Returns:
            Updated cart
        """
        try:
            cart = self.session.query(Cart).get(cart_id)
            if not cart:
                raise ValueError(f"Cart {cart_id} not found")
            
            cart.user_id = user_id
            cart.session_id = None
            cart.updated_at = datetime.utcnow()
            
            self.session.commit()
            return cart
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def cleanup_expired_carts(self, days_old: int = 30) -> int:
        """
        Clean up expired carts
        
        Args:
            days_old: Days old to consider expired
            
        Returns:
            Number of carts cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Delete expired carts and their items (cascade will handle items)
            result = self.session.query(Cart).filter(
                or_(
                    Cart.expires_at < datetime.utcnow(),
                    and_(
                        Cart.updated_at < cutoff_date,
                        Cart.status == CartStatus.ABANDONED
                    )
                )
            ).delete(synchronize_session=False)
            
            self.session.commit()
            return result
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def get_cart_item_by_course(self, cart_id: int, course_id: int) -> Optional[CartItem]:
        """
        Get cart item by course ID
        
        Args:
            cart_id: Cart ID
            course_id: Course ID
            
        Returns:
            CartItem or None
        """
        try:
            return self.session.query(CartItem).filter(
                and_(
                    CartItem.cart_id == cart_id,
                    CartItem.course_id == course_id
                )
            ).first()
        except SQLAlchemyError as e:
            raise e


class CouponDAO(BaseDAO):
    """DAO for Coupon operations"""
    
    def __init__(self):
        super().__init__(Coupon)
    
    def get_coupon_by_code(self, code: str) -> Optional[Coupon]:
        """
        Get coupon by code
        
        Args:
            code: Coupon code
            
        Returns:
            Coupon or None
        """
        try:
            return self.session.query(Coupon).filter(
                Coupon.code == code.upper().strip()
            ).first()
        except SQLAlchemyError as e:
            raise e
    
    def get_valid_coupon_by_code(self, code: str) -> Optional[Coupon]:
        """
        Get valid coupon by code
        
        Args:
            code: Coupon code
            
        Returns:
            Valid coupon or None
        """
        try:
            now = datetime.utcnow()
            return self.session.query(Coupon).filter(
                and_(
                    Coupon.code == code.upper().strip(),
                    Coupon.status == CouponStatus.ACTIVE,
                    Coupon.valid_from <= now,
                    Coupon.valid_until >= now,
                    or_(
                        Coupon.usage_limit.is_(None),
                        Coupon.total_used < Coupon.usage_limit
                    )
                )
            ).first()
        except SQLAlchemyError as e:
            raise e
    
    def get_user_coupon_usage_count(self, coupon_id: int, user_id: int) -> int:
        """
        Get coupon usage count for a user
        
        Args:
            coupon_id: Coupon ID
            user_id: User ID
            
        Returns:
            Usage count
        """
        try:
            return self.session.query(CouponUsage).filter(
                and_(
                    CouponUsage.coupon_id == coupon_id,
                    CouponUsage.user_id == user_id
                )
            ).count()
        except SQLAlchemyError as e:
            raise e
    
    def record_coupon_usage(self, coupon_id: int, order_amount: float, 
                           discount_amount: float, user_id: Optional[int] = None,
                           cart_id: Optional[int] = None, session_id: Optional[str] = None) -> CouponUsage:
        """
        Record coupon usage
        
        Args:
            coupon_id: Coupon ID
            order_amount: Order amount
            discount_amount: Discount amount
            user_id: User ID (optional)
            cart_id: Cart ID (optional)
            session_id: Session ID (optional)
            
        Returns:
            Created usage record
        """
        try:
            usage = CouponUsage(
                coupon_id=coupon_id,
                order_amount=order_amount,
                discount_amount=discount_amount,
                user_id=user_id,
                cart_id=cart_id,
                session_id=session_id
            )
            
            self.session.add(usage)
            
            # Update coupon usage counters
            coupon = self.session.query(Coupon).get(coupon_id)
            if coupon:
                coupon.increment_usage(discount_amount)
            
            self.session.commit()
            return usage
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def get_active_coupons(self, limit: Optional[int] = None) -> List[Coupon]:
        """
        Get active public coupons
        
        Args:
            limit: Optional limit
            
        Returns:
            List of active coupons
        """
        try:
            now = datetime.utcnow()
            query = self.session.query(Coupon).filter(
                and_(
                    Coupon.status == CouponStatus.ACTIVE,
                    Coupon.is_public == True,
                    Coupon.valid_from <= now,
                    Coupon.valid_until >= now
                )
            ).order_by(Coupon.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            raise e