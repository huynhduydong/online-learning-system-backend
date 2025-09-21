"""
Comprehensive test suite for Cart System
Tests cover: main flow, conflict handling, idempotency, guest cart merging
"""

import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from app import create_app, db
from app.models.user import User
from app.models.course import Course, CourseStatus
from app.models.cart import Cart, CartItem, CartStatus
from app.models.coupon import Coupon, CouponUsage, CouponType
from app.services.cart_service import CartService
from app.exceptions.validation_exception import ValidationException


class TestCartSystem:
    """Comprehensive test suite for cart system"""
    
    def setup_method(self, method):
        """Setup test environment before each test"""
        self.app = create_app('testing')
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        self._create_test_data()
            
        self.client = self.app.test_client()
    
    def teardown_method(self, method):
        """Cleanup after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_data(self):
        """Create test data for all tests"""
        # Create test user
        self.test_user = User(
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User"
        )
        db.session.add(self.test_user)
        db.session.flush()  # Get ID without committing
        
        # Create test courses
        self.course1 = Course(
            title="Python Basics",
            description="Learn Python programming",
            price=Decimal('99.99'),
            instructor_id=self.test_user.id,
            category_id=1,
            status=CourseStatus.PUBLISHED,
            is_published=True
        )
        self.course2 = Course(
            title="Advanced Python",
            description="Advanced Python concepts",
            price=Decimal('149.99'),
            instructor_id=self.test_user.id,
            category_id=1,
            status=CourseStatus.PUBLISHED,
            is_published=True
        )
        self.course3 = Course(
            title="Free Course",
            description="Free course for testing",
            price=Decimal('0.00'),
            instructor_id=self.test_user.id,
            category_id=1,
            status=CourseStatus.PUBLISHED,
            is_published=True,
            is_free=True
        )
        
        db.session.add_all([self.course1, self.course2, self.course3])
        db.session.flush()  # Get IDs without committing
        
        # Create test coupons
        self.percentage_coupon = Coupon(
            code="SAVE20",
            name="20% Off",
            description="Get 20% discount",
            type=CouponType.PERCENTAGE,
            value=Decimal('20.00'),
            minimum_amount=Decimal('50.00'),
            maximum_discount=Decimal('100.00'),
            usage_limit=100,
            is_active=True,
            valid_from=datetime.utcnow() - timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        
        self.fixed_coupon = Coupon(
            code="FIXED50",
            name="$50 Off",
            description="Get $50 discount",
            type=CouponType.FIXED_AMOUNT,
            value=Decimal('50.00'),
            minimum_amount=Decimal('100.00'),
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
        
        db.session.add_all([self.percentage_coupon, self.fixed_coupon, self.expired_coupon])
        db.session.commit()


class TestCartMainFlow(TestCartSystem):
    """Test main cart flow scenarios"""
    
    def test_create_cart_for_authenticated_user(self):
        """Test creating cart for authenticated user"""
        user_id = self.test_user.id
        
        cart_service = CartService()
        cart_data = cart_service.get_cart(user_id=user_id)
        
        assert cart_data is not None
        assert 'cart_id' in cart_data
        assert cart_data['cart_id'] is not None
        assert cart_data['status'] == CartStatus.ACTIVE.value
        assert cart_data['total_amount'] == 0.0
        assert cart_data['final_amount'] == 0.0
        assert cart_data['item_count'] == 0
        assert cart_data['items'] == []
    
    def test_create_cart_for_guest_user(self):
        """Test creating cart for guest user with session"""
        session_id = "guest_session_123"
        
        cart_service = CartService()
        cart_data = cart_service.get_cart(session_id=session_id)
        
        assert cart_data is not None
        assert 'cart_id' in cart_data
        assert cart_data['cart_id'] is not None
        assert cart_data['session_id'] == session_id
        assert cart_data['status'] == CartStatus.ACTIVE.value
        assert cart_data['total_amount'] == 0.0
        assert cart_data['final_amount'] == 0.0
        assert cart_data['item_count'] == 0
        assert cart_data['items'] == []
    
    def test_add_course_to_cart(self):
        """Test adding course to cart"""
        cart_service = CartService()
        user_id = self.test_user.id
        
        # Add course to cart
        result = cart_service.add_item_to_cart(self.course1.id, user_id=user_id)
        
        assert result is not None
        assert 'cart_id' in result
        assert result['item_count'] == 1
        assert len(result['items']) == 1
        assert result['items'][0]['course_id'] == self.course1.id
        assert result['items'][0]['price'] == float(self.course1.price)
        assert result['total_amount'] == float(self.course1.price)
        assert result['final_amount'] == float(self.course1.price)
    
    def test_add_multiple_courses_to_cart(self):
        """Test adding multiple courses to cart"""
        cart_service = CartService()
        
        # Add first course
        result1 = cart_service.add_item_to_cart(self.course1.id, user_id=self.test_user.id)
        assert result1['cart_id'] is not None
        assert result1['item_count'] == 1
        
        # Add second course
        result2 = cart_service.add_item_to_cart(self.course2.id, user_id=self.test_user.id)
        assert result2['cart_id'] == result1['cart_id']  # Same cart
        assert result2['item_count'] == 2
        assert len(result2['items']) == 2
        
        expected_total = float(self.course1.price + self.course2.price)
        assert result2['total_amount'] == expected_total
        assert result2['final_amount'] == expected_total
    
    def test_remove_course_from_cart(self):
        """Test removing course from cart"""
        cart_service = CartService()
        
        # Add courses to cart
        result1 = cart_service.add_item_to_cart(self.course1.id, user_id=self.test_user.id)
        result2 = cart_service.add_item_to_cart(self.course2.id, user_id=self.test_user.id)
        
        # Find item_id for course1
        course1_item_id = None
        for item in result2['items']:
            if item['course_id'] == self.course1.id:
                course1_item_id = item['id']
                break
        
        assert course1_item_id is not None
        
        # Remove course1 from cart
        result = cart_service.remove_item_from_cart(course1_item_id, user_id=self.test_user.id)
        
        assert result['item_count'] == 1
        assert len(result['items']) == 1
        assert result['items'][0]['course_id'] == self.course2.id
        assert result['total_amount'] == float(self.course2.price)
        assert result['final_amount'] == float(self.course2.price)
    
    def test_apply_percentage_coupon(self):
        """Test applying percentage coupon"""
        cart_service = CartService()
        
        # Add courses to cart
        cart_service.add_item_to_cart(self.course1.id, user_id=self.test_user.id)
        cart_service.add_item_to_cart(self.course2.id, user_id=self.test_user.id)
        
        # Apply coupon
        result = cart_service.apply_coupon(self.percentage_coupon.code, user_id=self.test_user.id)
        
        # Calculate expected discount: 20% of (99.99 + 149.99) = 20% of 249.98 = 49.996
        expected_discount = (self.course1.price + self.course2.price) * Decimal('0.20')
        expected_total = (self.course1.price + self.course2.price) - expected_discount
        
        assert result['coupon_applied'] is not None
        assert result['coupon_applied']['code'] == self.percentage_coupon.code
        assert abs(Decimal(str(result['coupon_applied']['discount_amount'])) - expected_discount) < Decimal('0.01')
        assert abs(Decimal(str(result['final_amount'])) - expected_total) < Decimal('0.01')
    
    def test_apply_fixed_amount_coupon(self):
        """Test applying fixed amount coupon"""
        cart_service = CartService()
        
        # Add courses to cart
        cart_service.add_item_to_cart(self.course1.id, user_id=self.test_user.id)
        cart_service.add_item_to_cart(self.course2.id, user_id=self.test_user.id)
        
        # Apply coupon
        result = cart_service.apply_coupon(self.fixed_coupon.code, user_id=self.test_user.id)
        
        # Calculate expected discount: Fixed $50.00
        expected_discount = Decimal('50.00')
        expected_total = (self.course1.price + self.course2.price) - expected_discount
        
        assert result['coupon_applied'] is not None
        assert result['coupon_applied']['code'] == self.fixed_coupon.code
        assert abs(Decimal(str(result['coupon_applied']['discount_amount'])) - expected_discount) < Decimal('0.01')
        assert abs(Decimal(str(result['final_amount'])) - expected_total) < Decimal('0.01')
    
    def test_clear_cart(self):
        """Test clearing cart"""
        cart_service = CartService()
        
        # Add courses to cart
        cart_service.add_item_to_cart(self.course1.id, user_id=self.test_user.id)
        cart_service.add_item_to_cart(self.course2.id, user_id=self.test_user.id)
        
        # Apply coupon
        cart_service.apply_coupon(self.percentage_coupon.code, user_id=self.test_user.id)
        
        # Clear cart
        result = cart_service.clear_cart(user_id=self.test_user.id)
        
        assert result['success'] is True
        assert result['message'] == "Cart cleared successfully"


class TestCartConflictHandling(TestCartSystem):
    """Test cart conflict handling scenarios"""
    
    def test_add_duplicate_course(self):
        """Test adding same course twice should not duplicate"""
        cart = CartService.get_cart(user_id=self.test_user.id)
        
        # Add course first time
        result1 = CartService.add_item_to_cart(cart.id, self.course1.id)
        assert result1['success'] is True
        
        # Try to add same course again
        result2 = CartService.add_item_to_cart(cart.id, self.course1.id)
        assert result2['success'] is False
        assert "already in cart" in result2['message'].lower()
        assert len(cart.items) == 1
    
    def test_add_nonexistent_course(self):
        """Test adding non-existent course"""
        cart = CartService.get_cart(user_id=self.test_user.id)
        
        with pytest.raises(ValidationException):
            CartService.add_item_to_cart(cart.id, 99999)
    
    def test_remove_nonexistent_course(self):
        """Test removing non-existent course from cart"""
        cart = CartService.get_cart(user_id=self.test_user.id)
        
        result = CartService.remove_item_from_cart(cart.id, self.course1.id)
        assert result['success'] is False
        assert "not found in cart" in result['message'].lower()
    
    def test_apply_invalid_coupon(self):
        """Test applying invalid coupon code"""
        cart = CartService.get_cart(user_id=self.test_user.id)
        CartService.add_item_to_cart(cart.id, self.course1.id)
        
        result = CartService.apply_coupon(cart.id, "INVALID_CODE")
        assert result['success'] is False
        assert "invalid coupon" in result['message'].lower()
    
    def test_apply_expired_coupon(self):
        """Test applying expired coupon"""
        cart = CartService.get_cart(user_id=self.test_user.id)
        CartService.add_item_to_cart(cart.id, self.course1.id)
        
        result = CartService.apply_coupon(cart.id, self.expired_coupon.code)
        assert result['success'] is False
        assert "expired" in result['message'].lower()
    
    def test_apply_coupon_minimum_amount_not_met(self):
        """Test applying coupon when minimum amount not met"""
        cart = CartService.get_cart(user_id=self.test_user.id)
        # Add only one course (99.99) but coupon requires minimum 100
        CartService.add_item_to_cart(cart.id, self.course1.id)
        
        result = CartService.apply_coupon(cart.id, self.fixed_coupon.code)
        assert result['success'] is False
        assert "minimum amount" in result['message'].lower()
    
    def test_apply_multiple_coupons(self):
        """Test applying multiple coupons (should replace previous)"""
        cart = CartService.get_cart(user_id=self.test_user.id)
        CartService.add_item_to_cart(cart.id, self.course1.id)
        CartService.add_item_to_cart(cart.id, self.course2.id)
        
        # Apply first coupon
        result1 = CartService.apply_coupon(cart.id, self.percentage_coupon.code)
        assert result1['success'] is True
        first_discount = cart.discount_amount
        
        # Apply second coupon (should replace first)
        result2 = CartService.apply_coupon(cart.id, self.fixed_coupon.code)
        assert result2['success'] is True
        assert cart.coupon_id == self.fixed_coupon.id
        assert cart.discount_amount == Decimal('50.00')
        assert cart.discount_amount != first_discount


class TestCartIdempotency(TestCartSystem):
    """Test cart idempotency scenarios"""
    
    def test_get_cart_idempotency(self):
        """Test that getting cart multiple times returns same cart"""
        cart1 = CartService.get_cart(user_id=self.test_user.id)
        cart2 = CartService.get_cart(user_id=self.test_user.id)
        cart3 = CartService.get_cart(user_id=self.test_user.id)
        
        assert cart1.id == cart2.id == cart3.id
        assert cart1 is cart2 is cart3  # Same object reference
    
    def test_add_item_idempotency_check(self):
        """Test that adding same item multiple times is handled gracefully"""
        cart = CartService.get_cart(user_id=self.test_user.id)
        
        # Add item multiple times
        for _ in range(3):
            result = CartService.add_item_to_cart(cart.id, self.course1.id)
            if result['success']:
                break
        
        # Should only have one item
        assert len(cart.items) == 1
        assert cart.subtotal == self.course1.price
    
    def test_remove_item_idempotency(self):
        """Test that removing non-existent item is handled gracefully"""
        cart = CartService.get_cart(user_id=self.test_user.id)
        
        # Try to remove item that was never added
        for _ in range(3):
            result = CartService.remove_item_from_cart(cart.id, self.course1.id)
            assert result['success'] is False
        
        assert len(cart.items) == 0
    
    def test_clear_empty_cart_idempotency(self):
        """Test that clearing empty cart multiple times works"""
        cart = CartService.get_cart(user_id=self.test_user.id)
        
        # Clear empty cart multiple times
        for _ in range(3):
            result = CartService.clear_cart(cart.id)
            assert result['success'] is True
        
        assert len(cart.items) == 0
        assert cart.total == Decimal('0.00')


class TestGuestCartMerging(TestCartSystem):
    """Test guest cart merging scenarios"""
    
    def test_merge_guest_cart_on_login(self):
        """Test merging guest cart when user logs in"""
        session_id = "guest_session_123"
        
        # Create guest cart and add items
        guest_cart = CartService.get_cart(session_id=session_id)
        CartService.add_item_to_cart(guest_cart.id, self.course1.id)
        CartService.add_item_to_cart(guest_cart.id, self.course2.id)
        
        # User logs in - merge guest cart
        result = CartService.merge_guest_cart(self.test_user.id, session_id)
        
        assert result['success'] is True
        
        # Check user cart has guest items
        user_cart = CartService.get_cart(user_id=self.test_user.id)
        assert len(user_cart.items) == 2
        
        # Check guest cart is marked as completed
        db.session.refresh(guest_cart)
        assert guest_cart.status == CartStatus.COMPLETED
    
    def test_merge_guest_cart_with_existing_user_cart(self):
        """Test merging guest cart when user already has items in cart"""
        session_id = "guest_session_123"
        
        # Create user cart with one item
        user_cart = CartService.get_cart(user_id=self.test_user.id)
        CartService.add_item_to_cart(user_cart.id, self.course1.id)
        
        # Create guest cart with different item
        guest_cart = CartService.get_cart(session_id=session_id)
        CartService.add_item_to_cart(guest_cart.id, self.course2.id)
        
        # Merge carts
        result = CartService.merge_guest_cart(self.test_user.id, session_id)
        
        assert result['success'] is True
        assert len(user_cart.items) == 2
        
        # Check both courses are in user cart
        course_ids = [item.course_id for item in user_cart.items]
        assert self.course1.id in course_ids
        assert self.course2.id in course_ids
    
    def test_merge_guest_cart_with_duplicate_items(self):
        """Test merging guest cart with duplicate items"""
        session_id = "guest_session_123"
        
        # Create user cart with course1
        user_cart = CartService.get_cart(user_id=self.test_user.id)
        CartService.add_item_to_cart(user_cart.id, self.course1.id)
        
        # Create guest cart with same course1 and course2
        guest_cart = CartService.get_cart(session_id=session_id)
        CartService.add_item_to_cart(guest_cart.id, self.course1.id)
        CartService.add_item_to_cart(guest_cart.id, self.course2.id)
        
        # Merge carts
        result = CartService.merge_guest_cart(self.test_user.id, session_id)
        
        assert result['success'] is True
        assert len(user_cart.items) == 2  # No duplicate course1
        
        # Check courses in cart
        course_ids = [item.course_id for item in user_cart.items]
        assert course_ids.count(self.course1.id) == 1  # Only one instance
        assert self.course2.id in course_ids
    
    def test_merge_guest_cart_with_coupons(self):
        """Test merging guest cart that has coupon applied"""
        session_id = "guest_session_123"
        
        # Create guest cart with items and coupon
        guest_cart = CartService.get_cart(session_id=session_id)
        CartService.add_item_to_cart(guest_cart.id, self.course1.id)
        CartService.add_item_to_cart(guest_cart.id, self.course2.id)
        CartService.apply_coupon(guest_cart.id, self.percentage_coupon.code)
        
        # Merge to user cart
        result = CartService.merge_guest_cart(self.test_user.id, session_id)
        
        assert result['success'] is True
        
        user_cart = CartService.get_cart(user_id=self.test_user.id)
        assert user_cart.coupon_id == self.percentage_coupon.id
        assert user_cart.discount_amount > Decimal('0.00')
    
    def test_merge_nonexistent_guest_cart(self):
        """Test merging non-existent guest cart"""
        result = CartService.merge_guest_cart(self.test_user.id, "nonexistent_session")
        
        assert result['success'] is True  # Should handle gracefully
        assert "no guest cart found" in result['message'].lower()


class TestCartAPIEndpoints(TestCartSystem):
    """Test cart API endpoints"""
    
    def _get_auth_headers(self):
        """Get authentication headers for API requests"""
        # Mock JWT token for testing
        return {'Authorization': 'Bearer mock_jwt_token'}
    
    @patch('app.utils.auth.get_current_user_optional')
    @patch('app.utils.auth.get_session_id')
    def test_get_cart_api_authenticated(self, mock_session, mock_user):
        """Test GET /api/cart for authenticated user"""
        mock_user.return_value = self.test_user
        mock_session.return_value = None
        
        response = self.client.get('/api/cart', headers=self._get_auth_headers())
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'cart' in data['data']
    
    @patch('app.utils.auth.get_current_user_optional')
    @patch('app.utils.auth.get_session_id')
    def test_get_cart_api_guest(self, mock_session, mock_user):
        """Test GET /api/cart for guest user"""
        mock_user.return_value = None
        mock_session.return_value = "guest_session_123"
        
        response = self.client.get('/api/cart')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'cart' in data['data']
    
    @patch('app.utils.auth.get_current_user_optional')
    @patch('app.utils.auth.get_session_id')
    def test_add_item_api(self, mock_session, mock_user):
        """Test POST /api/cart/items"""
        mock_user.return_value = self.test_user
        mock_session.return_value = None
        
        payload = {'course_id': self.course1.id}
        response = self.client.post(
            '/api/cart/items',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self._get_auth_headers()
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('app.utils.auth.get_current_user_optional')
    @patch('app.utils.auth.get_session_id')
    def test_remove_item_api(self, mock_session, mock_user):
        """Test DELETE /api/cart/items/{course_id}"""
        mock_user.return_value = self.test_user
        mock_session.return_value = None
        
        # First add item
        cart = CartService.get_cart(user_id=self.test_user.id)
        CartService.add_item_to_cart(cart.id, self.course1.id)
        
        response = self.client.delete(
            f'/api/cart/items/{self.course1.id}',
            headers=self._get_auth_headers()
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('app.utils.auth.get_current_user_optional')
    @patch('app.utils.auth.get_session_id')
    def test_apply_coupon_api(self, mock_session, mock_user):
        """Test POST /api/cart/coupon"""
        mock_user.return_value = self.test_user
        mock_session.return_value = None
        
        # Add items to cart first
        cart = CartService.get_cart(user_id=self.test_user.id)
        CartService.add_item_to_cart(cart.id, self.course1.id)
        CartService.add_item_to_cart(cart.id, self.course2.id)
        
        payload = {'coupon_code': self.percentage_coupon.code}
        response = self.client.post(
            '/api/cart/coupon',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self._get_auth_headers()
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('app.utils.auth.get_current_user_optional')
    @patch('app.utils.auth.get_session_id')
    def test_clear_cart_api(self, mock_session, mock_user):
        """Test DELETE /api/cart"""
        mock_user.return_value = self.test_user
        mock_session.return_value = None
        
        response = self.client.delete('/api/cart', headers=self._get_auth_headers())
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])