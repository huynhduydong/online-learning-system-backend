"""
Coupon models for Online Learning System
Implements discount and promotional functionality
"""

from enum import Enum
from datetime import datetime
from sqlalchemy import Numeric, CheckConstraint
from app import db


class CouponType(Enum):
    """Coupon type enumeration"""
    PERCENTAGE = 'percentage'
    FIXED_AMOUNT = 'fixed_amount'


class CouponStatus(Enum):
    """Coupon status enumeration"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    EXPIRED = 'expired'


class Coupon(db.Model):
    """
    Coupon model for discount functionality
    
    Business Rules:
    - Coupon codes must be unique
    - Percentage discounts cannot exceed 100%
    - Fixed amount discounts cannot exceed minimum order amount
    - Coupons have usage limits and expiration dates
    - Can be restricted to specific courses or categories
    """
    __tablename__ = 'coupons'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Coupon identification
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Discount configuration
    type = db.Column(db.Enum(CouponType), nullable=False)
    value = db.Column(Numeric(10, 2), nullable=False)  # Percentage or fixed amount
    
    # Usage constraints
    minimum_order_amount = db.Column(Numeric(10, 2), default=0.00)
    maximum_discount_amount = db.Column(Numeric(10, 2), nullable=True)  # For percentage coupons
    usage_limit = db.Column(db.Integer, nullable=True)  # Total usage limit
    usage_limit_per_user = db.Column(db.Integer, default=1)  # Per user limit
    
    # Validity period
    valid_from = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime, nullable=False)
    
    # Status and metadata
    status = db.Column(db.Enum(CouponStatus), nullable=False, default=CouponStatus.ACTIVE)
    is_public = db.Column(db.Boolean, default=True)  # Public vs private coupons
    
    # Usage tracking
    total_used = db.Column(db.Integer, default=0)
    total_discount_given = db.Column(Numeric(10, 2), default=0.00)
    
    # Restrictions (JSON fields for flexibility)
    applicable_courses = db.Column(db.Text, nullable=True)  # JSON array of course IDs
    applicable_categories = db.Column(db.Text, nullable=True)  # JSON array of category IDs
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', backref='created_coupons')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('value > 0', name='positive_value'),
        CheckConstraint('minimum_order_amount >= 0', name='non_negative_minimum'),
        CheckConstraint('usage_limit IS NULL OR usage_limit > 0', name='positive_usage_limit'),
        CheckConstraint('usage_limit_per_user > 0', name='positive_per_user_limit'),
        CheckConstraint('valid_until > valid_from', name='valid_date_range'),
    )
    
    def __init__(self, code, name, type, value, valid_until, **kwargs):
        """
        Initialize coupon
        
        Args:
            code: Unique coupon code
            name: Coupon name
            type: CouponType (percentage or fixed_amount)
            value: Discount value
            valid_until: Expiration date
        """
        self.code = code.upper().strip()  # Normalize code
        self.name = name
        self.type = type
        self.value = value
        self.valid_until = valid_until
        
        # Set optional fields
        self.description = kwargs.get('description')
        self.minimum_order_amount = kwargs.get('minimum_order_amount', 0.00)
        self.maximum_discount_amount = kwargs.get('maximum_discount_amount')
        self.usage_limit = kwargs.get('usage_limit')
        self.usage_limit_per_user = kwargs.get('usage_limit_per_user', 1)
        self.valid_from = kwargs.get('valid_from', datetime.utcnow())
        self.status = kwargs.get('status', CouponStatus.ACTIVE)
        self.is_public = kwargs.get('is_public', True)
        self.applicable_courses = kwargs.get('applicable_courses')
        self.applicable_categories = kwargs.get('applicable_categories')
        self.created_by = kwargs.get('created_by')
        
        # Validate percentage coupons
        if self.type == CouponType.PERCENTAGE and self.value > 100:
            raise ValueError("Percentage discount cannot exceed 100%")
    
    def __repr__(self):
        return f'<Coupon {self.code}: {self.type.value} {self.value}>'
    
    @property
    def is_valid(self):
        """Check if coupon is currently valid"""
        now = datetime.utcnow()
        return (
            self.status == CouponStatus.ACTIVE and
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit is None or self.total_used < self.usage_limit)
        )
    
    @property
    def is_expired(self):
        """Check if coupon is expired"""
        return datetime.utcnow() > self.valid_until
    
    @property
    def usage_remaining(self):
        """Get remaining usage count"""
        if self.usage_limit is None:
            return None
        return max(0, self.usage_limit - self.total_used)
    
    def calculate_discount(self, order_amount):
        """
        Calculate discount amount for given order
        
        Args:
            order_amount: Total order amount
            
        Returns:
            float: Discount amount
        """
        if not self.is_valid:
            return 0.00
        
        if order_amount < self.minimum_order_amount:
            return 0.00
        
        if self.type == CouponType.PERCENTAGE:
            discount = (float(self.value) / 100) * float(order_amount)
            if self.maximum_discount_amount:
                discount = min(discount, float(self.maximum_discount_amount))
        else:  # FIXED_AMOUNT
            discount = min(float(self.value), float(order_amount))
        
        return round(discount, 2)
    
    def can_be_used_by_user(self, user_id, current_usage=0):
        """
        Check if coupon can be used by specific user
        
        Args:
            user_id: User ID
            current_usage: Current usage count for this user
            
        Returns:
            bool: True if can be used
        """
        if not self.is_valid:
            return False
        
        return current_usage < self.usage_limit_per_user
    
    def increment_usage(self, discount_amount):
        """
        Increment usage counters
        
        Args:
            discount_amount: Amount of discount given
        """
        self.total_used += 1
        self.total_discount_given += discount_amount
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_sensitive=False):
        """
        Convert coupon to dictionary
        
        Args:
            include_sensitive: Include sensitive information like usage stats
        """
        data = {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'type': self.type.value,
            'value': float(self.value),
            'minimum_order_amount': float(self.minimum_order_amount),
            'maximum_discount_amount': float(self.maximum_discount_amount) if self.maximum_discount_amount else None,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'status': self.status.value,
            'is_public': self.is_public,
            'is_valid': self.is_valid,
            'is_expired': self.is_expired,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_sensitive:
            data.update({
                'usage_limit': self.usage_limit,
                'usage_limit_per_user': self.usage_limit_per_user,
                'total_used': self.total_used,
                'usage_remaining': self.usage_remaining,
                'total_discount_given': float(self.total_discount_given),
                'applicable_courses': self.applicable_courses,
                'applicable_categories': self.applicable_categories,
                'created_by': self.created_by
            })
        
        return data


class CouponUsage(db.Model):
    """
    Track coupon usage by users
    """
    __tablename__ = 'coupon_usage'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for guest usage
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=True)
    
    # Usage details
    order_amount = db.Column(Numeric(10, 2), nullable=False)
    discount_amount = db.Column(Numeric(10, 2), nullable=False)
    session_id = db.Column(db.String(255), nullable=True)  # For guest tracking
    
    # Timestamp
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    coupon = db.relationship('Coupon', backref='usage_records')
    user = db.relationship('User', backref='coupon_usage')
    cart = db.relationship('Cart', backref='coupon_usage')
    
    def __init__(self, coupon_id, order_amount, discount_amount, user_id=None, cart_id=None, session_id=None):
        """Initialize coupon usage record"""
        self.coupon_id = coupon_id
        self.user_id = user_id
        self.cart_id = cart_id
        self.order_amount = order_amount
        self.discount_amount = discount_amount
        self.session_id = session_id
    
    def __repr__(self):
        return f'<CouponUsage {self.id}: Coupon {self.coupon_id}, User {self.user_id}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'coupon_id': self.coupon_id,
            'user_id': self.user_id,
            'cart_id': self.cart_id,
            'order_amount': float(self.order_amount),
            'discount_amount': float(self.discount_amount),
            'session_id': self.session_id,
            'used_at': self.used_at.isoformat() if self.used_at else None
        }