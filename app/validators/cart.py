"""
Cart Validators
Pydantic models for cart request validation
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
import re


class AddItemRequest(BaseModel):
    """Request model for adding item to cart"""
    
    course_id: int = Field(..., gt=0, description="Course ID to add to cart")
    
    class Config:
        schema_extra = {
            "example": {
                "course_id": 123
            }
        }


class ApplyCouponRequest(BaseModel):
    """Request model for applying coupon"""
    
    coupon_code: str = Field(..., min_length=1, max_length=50, description="Coupon code to apply")
    
    @validator('coupon_code')
    def validate_coupon_code(cls, v):
        """Validate coupon code format"""
        if not v or not v.strip():
            raise ValueError('Coupon code cannot be empty')
        
        # Remove extra whitespace and convert to uppercase
        v = v.strip().upper()
        
        # Basic format validation (alphanumeric and common special chars)
        if not re.match(r'^[A-Z0-9\-_]+$', v):
            raise ValueError('Coupon code contains invalid characters')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "coupon_code": "SAVE20"
            }
        }


class CartResponse(BaseModel):
    """Response model for cart operations"""
    
    cart_id: int
    items: list
    item_count: int
    total_amount: float
    discount_amount: float
    final_amount: float
    coupon_code: Optional[str]
    status: str
    created_at: str
    updated_at: str
    expires_at: Optional[str]
    session_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "cart_id": 1,
                "items": [
                    {
                        "id": 1,
                        "course_id": 123,
                        "course_title": "Python Programming",
                        "course_instructor": "John Doe",
                        "price": 99.99,
                        "original_price": 129.99,
                        "added_at": "2025-01-21T10:00:00"
                    }
                ],
                "item_count": 1,
                "total_amount": 99.99,
                "discount_amount": 0.0,
                "final_amount": 99.99,
                "coupon_code": None,
                "status": "active",
                "created_at": "2025-01-21T10:00:00",
                "updated_at": "2025-01-21T10:00:00",
                "expires_at": "2025-01-28T10:00:00",
                "session_id": "guest-session-123"
            }
        }


class CartItemResponse(BaseModel):
    """Response model for cart item"""
    
    id: int
    course_id: int
    course_title: str
    course_instructor: str
    price: float
    original_price: float
    added_at: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "course_id": 123,
                "course_title": "Python Programming",
                "course_instructor": "John Doe",
                "price": 99.99,
                "original_price": 129.99,
                "added_at": "2025-01-21T10:00:00"
            }
        }


class CouponAppliedResponse(BaseModel):
    """Response model for coupon application"""
    
    cart_id: int
    items: list
    item_count: int
    total_amount: float
    discount_amount: float
    final_amount: float
    coupon_code: Optional[str]
    status: str
    created_at: str
    updated_at: str
    expires_at: Optional[str]
    session_id: Optional[str] = None
    calculation_breakdown: dict
    coupon_applied: dict
    
    class Config:
        schema_extra = {
            "example": {
                "cart_id": 1,
                "items": [
                    {
                        "id": 1,
                        "course_id": 123,
                        "course_title": "Python Programming",
                        "course_instructor": "John Doe",
                        "price": 99.99,
                        "original_price": 129.99,
                        "added_at": "2025-01-21T10:00:00"
                    }
                ],
                "item_count": 1,
                "total_amount": 99.99,
                "discount_amount": 20.0,
                "final_amount": 79.99,
                "coupon_code": "SAVE20",
                "status": "active",
                "created_at": "2025-01-21T10:00:00",
                "updated_at": "2025-01-21T10:00:00",
                "expires_at": "2025-01-28T10:00:00",
                "calculation_breakdown": {
                    "subtotal": 99.99,
                    "discount": 20.0,
                    "tax_rate": 0.085,
                    "tax_amount": 6.8,
                    "processing_fee": 2.5,
                    "final_total": 89.29
                },
                "coupon_applied": {
                    "code": "SAVE20",
                    "description": "Save $20 on your order",
                    "discount_amount": 20.0,
                    "type": "fixed"
                }
            }
        }


class AvailableCouponsResponse(BaseModel):
    """Response model for available coupons"""
    
    coupons: list
    
    class Config:
        schema_extra = {
            "example": {
                "coupons": [
                    {
                        "code": "SAVE20",
                        "description": "Save $20 on your order",
                        "type": "fixed",
                        "discount_value": 20.0,
                        "minimum_order_amount": 50.0,
                        "valid_until": "2025-12-31T23:59:59",
                        "usage_limit": 1000,
                        "total_used": 150
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors"""
    
    success: bool = False
    message: str
    data: Optional[dict] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Course already in cart",
                "data": None
            }
        }


class SuccessResponse(BaseModel):
    """Response model for success"""
    
    success: bool = True
    message: str
    data: dict
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Item added to cart successfully",
                "data": {
                    "cart_id": 1,
                    "items": [],
                    "item_count": 1,
                    "total_amount": 99.99
                }
            }
        }