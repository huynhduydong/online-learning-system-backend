"""
Cart models for Online Learning System
Implements shopping cart functionality with guest and user cart support
"""

from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import Numeric, UniqueConstraint
from app import db


class CartStatus(Enum):
    """Cart status enumeration"""
    ACTIVE = 'active'
    ABANDONED = 'abandoned'
    CONVERTED = 'converted'


class Cart(db.Model):
    """
    Cart model for managing shopping carts
    
    Business Rules:
    - Each user can have only one active cart
    - Guest carts are identified by session_id
    - Carts expire after 30 days of inactivity
    - Cart merging happens when guest logs in
    """
    __tablename__ = 'carts'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # User association (nullable for guest carts)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(255), nullable=True)  # For guest carts
    
    # Cart metadata
    status = db.Column(db.Enum(CartStatus), nullable=False, default=CartStatus.ACTIVE)
    total_amount = db.Column(Numeric(10, 2), nullable=False, default=0.00)
    item_count = db.Column(db.Integer, nullable=False, default=0)
    
    # Coupon information
    coupon_code = db.Column(db.String(50), nullable=True)
    discount_amount = db.Column(Numeric(10, 2), nullable=False, default=0.00)
    final_amount = db.Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))
    
    # Relationships
    user = db.relationship('User', backref='carts')
    items = db.relationship('CartItem', backref='cart', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'status', name='unique_active_user_cart'),
    )
    
    def __init__(self, user_id=None, session_id=None, **kwargs):
        """
        Initialize cart
        
        Args:
            user_id: User ID for authenticated users
            session_id: Session ID for guest users
        """
        if not user_id and not session_id:
            raise ValueError("Either user_id or session_id must be provided")
        
        self.user_id = user_id
        self.session_id = session_id
        self.status = kwargs.get('status', CartStatus.ACTIVE)
        self.total_amount = kwargs.get('total_amount', 0.00)
        self.item_count = kwargs.get('item_count', 0)
        self.discount_amount = kwargs.get('discount_amount', 0.00)
        self.final_amount = kwargs.get('final_amount', 0.00)
        
        # Set expiration
        if 'expires_at' in kwargs:
            self.expires_at = kwargs['expires_at']
        else:
            self.expires_at = datetime.utcnow() + timedelta(days=30)
    
    def __repr__(self):
        return f'<Cart {self.id}: User {self.user_id}, Items {self.item_count}>'
    
    @property
    def is_expired(self):
        """Check if cart is expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_guest_cart(self):
        """Check if this is a guest cart"""
        return self.user_id is None and self.session_id is not None
    
    def extend_expiration(self, days=30):
        """Extend cart expiration"""
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.updated_at = datetime.utcnow()
    
    def calculate_totals(self):
        """Calculate cart totals based on items"""
        self.item_count = len(self.items)
        self.total_amount = sum(item.price for item in self.items)
        self.final_amount = self.total_amount - self.discount_amount
        self.updated_at = datetime.utcnow()
    
    def apply_coupon(self, coupon_code, discount_amount):
        """Apply coupon to cart"""
        self.coupon_code = coupon_code
        self.discount_amount = discount_amount
        self.final_amount = self.total_amount - discount_amount
        self.updated_at = datetime.utcnow()
    
    def remove_coupon(self):
        """Remove coupon from cart"""
        self.coupon_code = None
        self.discount_amount = 0.00
        self.final_amount = self.total_amount
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert cart to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'status': self.status.value,
            'total_amount': float(self.total_amount),
            'item_count': self.item_count,
            'coupon_code': self.coupon_code,
            'discount_amount': float(self.discount_amount),
            'final_amount': float(self.final_amount),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired,
            'is_guest_cart': self.is_guest_cart,
            'items': [item.to_dict() for item in self.items]
        }


class CartItem(db.Model):
    """
    Cart item model for individual course items in cart
    
    Business Rules:
    - Each course can only appear once per cart
    - Price is captured at time of adding to cart
    - Items maintain reference to original course
    """
    __tablename__ = 'cart_items'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Item details (captured at time of adding)
    course_title = db.Column(db.String(255), nullable=False)
    course_instructor = db.Column(db.String(255), nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)
    original_price = db.Column(Numeric(10, 2), nullable=True)
    
    # Metadata
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='cart_items')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('cart_id', 'course_id', name='unique_cart_course'),
    )
    
    def __init__(self, cart_id, course_id, course_title, course_instructor, price, original_price=None, **kwargs):
        """
        Initialize cart item
        
        Args:
            cart_id: Cart ID
            course_id: Course ID
            course_title: Course title (captured)
            course_instructor: Course instructor (captured)
            price: Current price
            original_price: Original price (for discount display)
        """
        self.cart_id = cart_id
        self.course_id = course_id
        self.course_title = course_title
        self.course_instructor = course_instructor
        self.price = price
        self.original_price = original_price or price
    
    def __repr__(self):
        return f'<CartItem {self.id}: Cart {self.cart_id}, Course {self.course_id}>'
    
    @property
    def has_discount(self):
        """Check if item has discount"""
        return self.original_price and self.original_price > self.price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if not self.has_discount:
            return 0
        return int(((self.original_price - self.price) / self.original_price) * 100)
    
    def to_dict(self):
        """Convert cart item to dictionary"""
        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'course_id': self.course_id,
            'course_title': self.course_title,
            'course_instructor': self.course_instructor,
            'price': float(self.price),
            'original_price': float(self.original_price) if self.original_price else None,
            'has_discount': self.has_discount,
            'discount_percentage': self.discount_percentage,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }