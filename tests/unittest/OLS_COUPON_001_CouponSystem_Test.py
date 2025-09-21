"""
Comprehensive test suite for Coupon System
Tests cover: validation, usage tracking, expiration, edge cases
"""

import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from app import create_app, db
from app.models.user import User
from app.models.course import Course
from app.models.cart import Cart, CartItem
from app.models.coupon import Coupon, CouponUsage, CouponType
from app.services.coupon_service import CouponService
from app.exceptions.validation_exception import ValidationException


class TestCouponSystem:
    """Base test class for coupon system"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup test environment before each test"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with self.app.app_context():
            db.create_all()
            self._create_test_data()
            
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def teardown_method(self):
        """Cleanup after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_data(self):
        """Create test data for all tests"""
        # Create test users
        self.test_user1 = User(
            email="user1@example.com",
            username="user1",
            first_name="User",
            last_name="One"
        )
        self.test_user1.set_password("password123")
        
        self.test_user2 = User(
            email="user2@example.com",
            username="user2",
            first_name="User",
            last_name="Two"
        )
        self.test_user2.set_password("password123")
        
        db.session.add_all([self.test_user1, self.test_user2])
        
        # Create test courses
        self.course1 = Course(
            title="Python Basics",
            description="Learn Python programming",
            price=Decimal('99.99'),
            instructor_id=1,
            category_id=1,
            status='published'
        )
        self.course2 = Course(
            title="Advanced Python",
            description="Advanced Python concepts",
            price=Decimal('149.99'),
            instructor_id=1,
            category_id=1,
            status='published'
        )
        
        db.session.add_all([self.course1, self.course2])
        
        # Create test coupons
        self.valid_percentage_coupon = Coupon(
            code="SAVE20",
            name="20% Off",
            description="Get 20% discount",
            type=CouponType.PERCENTAGE,
            value=Decimal('20.00'),
            minimum_amount=Decimal('50.00'),
            maximum_discount=Decimal('100.00'),
            usage_limit=10,
            is_active=True,
            valid_from=datetime.utcnow() - timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        
        self.valid_fixed_coupon = Coupon(
            code="FIXED50",
            name="$50 Off",
            description="Get $50 discount",
            type=CouponType.FIXED_AMOUNT,
            value=Decimal('50.00'),
            minimum_amount=Decimal('100.00'),
            usage_limit=5,
            is_active=True,
            valid_from=datetime.utcnow() - timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        
        self.expired_coupon = Coupon(
            code="EXPIRED",
            name="Expired Coupon",
            description="This coupon is expired",
            type=CouponType.PERCENTAGE,
            value=Decimal('10.00'),
            is_active=True,
            valid_from=datetime.utcnow() - timedelta(days=30),
            valid_until=datetime.utcnow() - timedelta(days=1)
        )
        
        self.inactive_coupon = Coupon(
            code="INACTIVE",
            name="Inactive Coupon",
            description="This coupon is inactive",
            type=CouponType.PERCENTAGE,
            value=Decimal('15.00'),
            is_active=False,
            valid_from=datetime.utcnow() - timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        
        self.limited_usage_coupon = Coupon(
            code="LIMITED",
            name="Limited Usage",
            description="Only 1 use allowed",
            type=CouponType.PERCENTAGE,
            value=Decimal('25.00'),
            usage_limit=1,
            is_active=True,
            valid_from=datetime.utcnow() - timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        
        self.no_minimum_coupon = Coupon(
            code="NOLIMIT",
            name="No Minimum",
            description="No minimum amount required",
            type=CouponType.FIXED_AMOUNT,
            value=Decimal('10.00'),
            minimum_amount=None,
            is_active=True,
            valid_from=datetime.utcnow() - timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        
        db.session.add_all([
            self.valid_percentage_coupon,
            self.valid_fixed_coupon,
            self.expired_coupon,
            self.inactive_coupon,
            self.limited_usage_coupon,
            self.no_minimum_coupon
        ])
        
        db.session.commit()


class TestCouponValidation(TestCouponSystem):
    """Test coupon validation scenarios"""
    
    def test_validate_valid_percentage_coupon(self):
        """Test validating valid percentage coupon"""
        result = CouponService.validate_coupon(
            self.valid_percentage_coupon.code,
            Decimal('100.00'),
            self.test_user1.id
        )
        
        assert result['valid'] is True
        assert result['coupon'].id == self.valid_percentage_coupon.id
        assert result['discount_amount'] == Decimal('20.00')  # 20% of 100
    
    def test_validate_valid_fixed_coupon(self):
        """Test validating valid fixed amount coupon"""
        result = CouponService.validate_coupon(
            self.valid_fixed_coupon.code,
            Decimal('150.00'),
            self.test_user1.id
        )
        
        assert result['valid'] is True
        assert result['coupon'].id == self.valid_fixed_coupon.id
        assert result['discount_amount'] == Decimal('50.00')
    
    def test_validate_nonexistent_coupon(self):
        """Test validating non-existent coupon"""
        result = CouponService.validate_coupon(
            "NONEXISTENT",
            Decimal('100.00'),
            self.test_user1.id
        )
        
        assert result['valid'] is False
        assert "not found" in result['message'].lower()
    
    def test_validate_expired_coupon(self):
        """Test validating expired coupon"""
        result = CouponService.validate_coupon(
            self.expired_coupon.code,
            Decimal('100.00'),
            self.test_user1.id
        )
        
        assert result['valid'] is False
        assert "expired" in result['message'].lower()
    
    def test_validate_inactive_coupon(self):
        """Test validating inactive coupon"""
        result = CouponService.validate_coupon(
            self.inactive_coupon.code,
            Decimal('100.00'),
            self.test_user1.id
        )
        
        assert result['valid'] is False
        assert "not active" in result['message'].lower()
    
    def test_validate_coupon_minimum_amount_not_met(self):
        """Test validating coupon when minimum amount not met"""
        result = CouponService.validate_coupon(
            self.valid_fixed_coupon.code,  # Requires minimum $100
            Decimal('50.00'),  # Only $50
            self.test_user1.id
        )
        
        assert result['valid'] is False
        assert "minimum amount" in result['message'].lower()
    
    def test_validate_coupon_no_minimum_requirement(self):
        """Test validating coupon with no minimum amount requirement"""
        result = CouponService.validate_coupon(
            self.no_minimum_coupon.code,
            Decimal('5.00'),  # Very small amount
            self.test_user1.id
        )
        
        assert result['valid'] is True
        assert result['discount_amount'] == Decimal('5.00')  # Discount limited by cart total
    
    def test_validate_percentage_coupon_with_maximum_discount(self):
        """Test percentage coupon with maximum discount limit"""
        # Cart total of $1000, 20% would be $200, but max discount is $100
        result = CouponService.validate_coupon(
            self.valid_percentage_coupon.code,
            Decimal('1000.00'),
            self.test_user1.id
        )
        
        assert result['valid'] is True
        assert result['discount_amount'] == Decimal('100.00')  # Capped at maximum


class TestCouponUsageTracking(TestCouponSystem):
    """Test coupon usage tracking scenarios"""
    
    def test_track_coupon_usage(self):
        """Test tracking coupon usage"""
        # Use coupon
        CouponService.use_coupon(
            self.valid_percentage_coupon.id,
            self.test_user1.id,
            Decimal('100.00'),
            Decimal('20.00')
        )
        
        # Check usage was recorded
        usage = CouponUsage.query.filter_by(
            coupon_id=self.valid_percentage_coupon.id,
            user_id=self.test_user1.id
        ).first()
        
        assert usage is not None
        assert usage.order_total == Decimal('100.00')
        assert usage.discount_amount == Decimal('20.00')
        assert usage.used_at is not None
    
    def test_coupon_usage_limit_reached(self):
        """Test coupon becomes invalid when usage limit reached"""
        # Use the limited coupon (limit = 1)
        CouponService.use_coupon(
            self.limited_usage_coupon.id,
            self.test_user1.id,
            Decimal('100.00'),
            Decimal('25.00')
        )
        
        # Try to validate same coupon again
        result = CouponService.validate_coupon(
            self.limited_usage_coupon.code,
            Decimal('100.00'),
            self.test_user2.id
        )
        
        assert result['valid'] is False
        assert "usage limit" in result['message'].lower()
    
    def test_user_specific_coupon_usage_limit(self):
        """Test user cannot use same coupon multiple times"""
        # First usage
        CouponService.use_coupon(
            self.valid_percentage_coupon.id,
            self.test_user1.id,
            Decimal('100.00'),
            Decimal('20.00')
        )
        
        # Try to use same coupon again by same user
        result = CouponService.validate_coupon(
            self.valid_percentage_coupon.code,
            Decimal('100.00'),
            self.test_user1.id
        )
        
        assert result['valid'] is False
        assert "already used" in result['message'].lower()
    
    def test_different_users_can_use_same_coupon(self):
        """Test different users can use the same coupon"""
        # User 1 uses coupon
        CouponService.use_coupon(
            self.valid_percentage_coupon.id,
            self.test_user1.id,
            Decimal('100.00'),
            Decimal('20.00')
        )
        
        # User 2 should still be able to use it
        result = CouponService.validate_coupon(
            self.valid_percentage_coupon.code,
            Decimal('100.00'),
            self.test_user2.id
        )
        
        assert result['valid'] is True
    
    def test_get_coupon_usage_stats(self):
        """Test getting coupon usage statistics"""
        # Create some usage records
        CouponService.use_coupon(
            self.valid_percentage_coupon.id,
            self.test_user1.id,
            Decimal('100.00'),
            Decimal('20.00')
        )
        CouponService.use_coupon(
            self.valid_percentage_coupon.id,
            self.test_user2.id,
            Decimal('150.00'),
            Decimal('30.00')
        )
        
        stats = CouponService.get_usage_stats(self.valid_percentage_coupon.id)
        
        assert stats['total_uses'] == 2
        assert stats['total_discount_given'] == Decimal('50.00')
        assert stats['average_order_value'] == Decimal('125.00')
        assert stats['remaining_uses'] == 8  # 10 - 2


class TestCouponEdgeCases(TestCouponSystem):
    """Test coupon edge cases and error scenarios"""
    
    def test_discount_cannot_exceed_cart_total(self):
        """Test discount cannot exceed cart total"""
        # Cart total is $50, but fixed coupon gives $50 discount
        result = CouponService.validate_coupon(
            self.valid_fixed_coupon.code,
            Decimal('150.00'),  # Meets minimum
            self.test_user1.id
        )
        
        assert result['valid'] is True
        assert result['discount_amount'] == Decimal('50.00')
        
        # But if we calculate for smaller amount after meeting minimum
        discount = CouponService.calculate_discount(
            self.valid_fixed_coupon,
            Decimal('30.00')  # Smaller than discount value
        )
        assert discount == Decimal('30.00')  # Should be limited to cart total
    
    def test_zero_value_coupon(self):
        """Test coupon with zero value"""
        zero_coupon = Coupon(
            code="ZERO",
            name="Zero Discount",
            description="No discount",
            type=CouponType.FIXED_AMOUNT,
            value=Decimal('0.00'),
            is_active=True,
            valid_from=datetime.utcnow() - timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(zero_coupon)
        db.session.commit()
        
        result = CouponService.validate_coupon(
            zero_coupon.code,
            Decimal('100.00'),
            self.test_user1.id
        )
        
        assert result['valid'] is True
        assert result['discount_amount'] == Decimal('0.00')
    
    def test_negative_cart_total(self):
        """Test validation with negative cart total"""
        with pytest.raises(ValidationException):
            CouponService.validate_coupon(
                self.valid_percentage_coupon.code,
                Decimal('-10.00'),
                self.test_user1.id
            )
    
    def test_coupon_valid_from_future(self):
        """Test coupon that becomes valid in the future"""
        future_coupon = Coupon(
            code="FUTURE",
            name="Future Coupon",
            description="Valid in the future",
            type=CouponType.PERCENTAGE,
            value=Decimal('10.00'),
            is_active=True,
            valid_from=datetime.utcnow() + timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(future_coupon)
        db.session.commit()
        
        result = CouponService.validate_coupon(
            future_coupon.code,
            Decimal('100.00'),
            self.test_user1.id
        )
        
        assert result['valid'] is False
        assert "not yet valid" in result['message'].lower()
    
    def test_percentage_coupon_over_100_percent(self):
        """Test percentage coupon with value over 100%"""
        over_100_coupon = Coupon(
            code="OVER100",
            name="Over 100%",
            description="More than 100% discount",
            type=CouponType.PERCENTAGE,
            value=Decimal('150.00'),  # 150%
            is_active=True,
            valid_from=datetime.utcnow() - timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(over_100_coupon)
        db.session.commit()
        
        result = CouponService.validate_coupon(
            over_100_coupon.code,
            Decimal('100.00'),
            self.test_user1.id
        )
        
        assert result['valid'] is True
        # Discount should be limited to cart total
        assert result['discount_amount'] == Decimal('100.00')


class TestCouponAPIEndpoints(TestCouponSystem):
    """Test coupon API endpoints"""
    
    def _get_auth_headers(self):
        """Get authentication headers for API requests"""
        return {'Authorization': 'Bearer mock_jwt_token'}
    
    @patch('app.utils.auth.get_current_user_optional')
    def test_validate_coupon_api(self, mock_user):
        """Test POST /api/coupons/validate"""
        mock_user.return_value = self.test_user1
        
        payload = {
            'coupon_code': self.valid_percentage_coupon.code,
            'cart_total': '100.00'
        }
        
        response = self.client.post(
            '/api/coupons/validate',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self._get_auth_headers()
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['valid'] is True
    
    @patch('app.utils.auth.get_current_user_optional')
    def test_get_coupon_details_api(self, mock_user):
        """Test GET /api/coupons/{code}"""
        mock_user.return_value = self.test_user1
        
        response = self.client.get(
            f'/api/coupons/{self.valid_percentage_coupon.code}',
            headers=self._get_auth_headers()
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['coupon']['code'] == self.valid_percentage_coupon.code
    
    def test_get_coupon_details_api_invalid_code(self):
        """Test GET /api/coupons/{code} with invalid code"""
        response = self.client.get('/api/coupons/INVALID')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    @patch('app.utils.auth.require_auth')
    def test_get_coupon_usage_stats_api(self, mock_auth):
        """Test GET /api/coupons/{code}/stats (admin only)"""
        mock_auth.return_value = self.test_user1  # Assume admin
        
        response = self.client.get(
            f'/api/coupons/{self.valid_percentage_coupon.code}/stats',
            headers=self._get_auth_headers()
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'stats' in data['data']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])