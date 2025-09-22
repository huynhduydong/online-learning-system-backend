"""
Enrollment DAO (Data Access Object)
Provides data access methods for enrollment operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, desc
from app.dao.base_dao import BaseDAO
from app.models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus
from app.models.course import Course
from app.models.user import User
from app.models.coupon import Coupon, CouponUsage
from app import db


class EnrollmentDAO(BaseDAO):
    """
    DAO class for enrollment operations
    Extends BaseDAO with enrollment-specific methods
    """
    
    def __init__(self):
        super().__init__(Enrollment)
    
    def get_by_id(self, enrollment_id: str) -> Optional[Enrollment]:
        """
        Get enrollment by UUID string ID
        
        Args:
            enrollment_id: UUID string of enrollment
            
        Returns:
            Optional[Enrollment]: Enrollment instance or None
        """
        try:
            return self.session.query(Enrollment).filter(
                Enrollment.id == enrollment_id
            ).first()
        except SQLAlchemyError as e:
            raise e
    
    def get_by_user_and_course(self, user_id: int, course_id: int) -> Optional[Enrollment]:
        """
        Get enrollment by user and course ID
        
        Args:
            user_id: User ID
            course_id: Course ID
            
        Returns:
            Optional[Enrollment]: Enrollment instance or None
        """
        try:
            return self.session.query(Enrollment).filter(
                and_(
                    Enrollment.user_id == user_id,
                    Enrollment.course_id == course_id
                )
            ).first()
        except SQLAlchemyError as e:
            raise e
    
    def get_user_enrollments(self, user_id: int, status_filter: Optional[str] = None,
                           page: int = 1, limit: int = 10) -> tuple[List[Enrollment], int]:
        """
        Get user's enrollments with pagination and optional status filter
        
        Args:
            user_id: User ID
            status_filter: Optional enrollment status filter
            page: Page number (1-based)
            limit: Number of items per page
            
        Returns:
            tuple[List[Enrollment], int]: (enrollments list, total count)
        """
        try:
            # Validate inputs
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError(f"Invalid user_id: {user_id}")
            
            if page < 1:
                page = 1
            if limit < 1 or limit > 100:
                limit = 10
            
            # Build base query with safer relationship loading
            query = self.session.query(Enrollment).filter(
                Enrollment.user_id == user_id
            )
            
            # Use selectinload instead of joinedload for better performance and error handling
            try:
                from sqlalchemy.orm import selectinload
                query = query.options(
                    selectinload(Enrollment.course),
                    selectinload(Enrollment.user)
                )
            except ImportError:
                # Fallback to joinedload if selectinload is not available
                query = query.options(
                    joinedload(Enrollment.course),
                    joinedload(Enrollment.user)
                )
            
            # Apply status filter if provided
            if status_filter:
                try:
                    status_enum = EnrollmentStatus(status_filter)
                    query = query.filter(Enrollment.status == status_enum)
                except ValueError:
                    # Invalid status, return empty result
                    return [], 0
            
            # Get total count before pagination with error handling
            try:
                total_count = query.count()
            except SQLAlchemyError as e:
                # If count fails, try simpler query
                simple_query = self.session.query(Enrollment).filter(
                    Enrollment.user_id == user_id
                )
                if status_filter:
                    try:
                        status_enum = EnrollmentStatus(status_filter)
                        simple_query = simple_query.filter(Enrollment.status == status_enum)
                    except ValueError:
                        return [], 0
                total_count = simple_query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            
            try:
                enrollments = query.order_by(desc(Enrollment.enrollment_date)).offset(offset).limit(limit).all()
            except SQLAlchemyError as e:
                # If complex query fails, try simpler one without relationships
                simple_query = self.session.query(Enrollment).filter(
                    Enrollment.user_id == user_id
                )
                if status_filter:
                    try:
                        status_enum = EnrollmentStatus(status_filter)
                        simple_query = simple_query.filter(Enrollment.status == status_enum)
                    except ValueError:
                        return [], 0
                
                enrollments = simple_query.order_by(desc(Enrollment.enrollment_date)).offset(offset).limit(limit).all()
            
            return enrollments or [], total_count or 0
            
        except SQLAlchemyError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Database error in get_user_enrollments for user {user_id}: {str(e)}")
            raise e
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in get_user_enrollments for user {user_id}: {str(e)}")
            raise SQLAlchemyError(f"Error retrieving user enrollments: {str(e)}")
    
    def check_user_access(self, user_id: int, course_id: int) -> Optional[Enrollment]:
        """
        Check if user has access to a specific course
        
        Args:
            user_id: User ID
            course_id: Course ID
            
        Returns:
            Optional[Enrollment]: Active enrollment or None
        """
        try:
            return self.session.query(Enrollment).filter(
                and_(
                    Enrollment.user_id == user_id,
                    Enrollment.course_id == course_id,
                    Enrollment.access_granted == True,
                    Enrollment.status.in_([
                        EnrollmentStatus.ENROLLED,
                        EnrollmentStatus.ACTIVE
                    ])
                )
            ).first()
        except SQLAlchemyError as e:
            raise e
    
    def get_enrollments_by_status(self, status: EnrollmentStatus,
                                limit: Optional[int] = None) -> List[Enrollment]:
        """
        Get enrollments by status
        
        Args:
            status: Enrollment status
            limit: Optional limit for results
            
        Returns:
            List[Enrollment]: List of enrollments
        """
        try:
            query = self.session.query(Enrollment).filter(
                Enrollment.status == status
            ).options(
                joinedload(Enrollment.course),
                joinedload(Enrollment.user)
            )
            
            if limit:
                query = query.limit(limit)
                
            return query.all()
        except SQLAlchemyError as e:
            raise e
    
    def get_pending_activations(self, limit: Optional[int] = None) -> List[Enrollment]:
        """
        Get enrollments pending activation
        
        Args:
            limit: Optional limit for results
            
        Returns:
            List[Enrollment]: List of enrollments pending activation
        """
        try:
            query = self.session.query(Enrollment).filter(
                and_(
                    Enrollment.status == EnrollmentStatus.ACTIVATING,
                    or_(
                        Enrollment.next_retry_at.is_(None),
                        Enrollment.next_retry_at <= db.func.now()
                    )
                )
            ).options(
                joinedload(Enrollment.course),
                joinedload(Enrollment.user)
            )
            
            if limit:
                query = query.limit(limit)
                
            return query.all()
        except SQLAlchemyError as e:
            raise e
    
    def create_enrollment(self, user_id: int, course_id: int, full_name: str,
                         email: str, payment_amount: float = 0.00,
                         discount_code: Optional[str] = None,
                         discount_applied: float = 0.00) -> Enrollment:
        """
        Create new enrollment with validation
        
        Args:
            user_id: User ID
            course_id: Course ID
            full_name: Student's full name
            email: Email for certificate
            payment_amount: Payment amount required
            discount_code: Optional discount code
            discount_applied: Discount amount applied
            
        Returns:
            Enrollment: Created enrollment instance
            
        Raises:
            SQLAlchemyError: Database error
            ValueError: Validation error
        """
        try:
            # Check if enrollment already exists
            existing = self.get_by_user_and_course(user_id, course_id)
            if existing:
                raise ValueError("User is already enrolled in this course")
            
            # Create enrollment
            enrollment = Enrollment(
                user_id=user_id,
                course_id=course_id,
                full_name=full_name,
                email=email,
                payment_amount=payment_amount,
                discount_code=discount_code,
                discount_applied=discount_applied
            )
            
            self.session.add(enrollment)
            self.session.commit()
            return enrollment
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def update_enrollment_status(self, enrollment_id: str, new_status: EnrollmentStatus,
                               payment_status: Optional[PaymentStatus] = None) -> Optional[Enrollment]:
        """
        Update enrollment status
        
        Args:
            enrollment_id: Enrollment ID
            new_status: New enrollment status
            payment_status: Optional new payment status
            
        Returns:
            Optional[Enrollment]: Updated enrollment or None
        """
        try:
            enrollment = self.get_by_id(enrollment_id)
            if not enrollment:
                return None
            
            enrollment.update_status(new_status, payment_status)
            self.session.commit()
            return enrollment
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def increment_activation_attempt(self, enrollment_id: str) -> Optional[Enrollment]:
        """
        Increment activation attempt for enrollment
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            Optional[Enrollment]: Updated enrollment or None
        """
        try:
            enrollment = self.get_by_id(enrollment_id)
            if not enrollment:
                return None
            
            enrollment.increment_activation_attempt()
            self.session.commit()
            return enrollment
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def validate_discount_code(self, code: str, user_id: int, order_amount: float) -> tuple[bool, Optional[Coupon], str]:
        """
        Validate discount code and calculate discount
        
        Args:
            code: Discount code
            user_id: User ID
            order_amount: Order amount
            
        Returns:
            tuple[bool, Optional[Coupon], str]: (is_valid, coupon, message)
        """
        try:
            # Get coupon by code
            coupon = self.session.query(Coupon).filter(
                Coupon.code == code.upper().strip()
            ).first()
            
            if not coupon:
                return False, None, "Invalid discount code"
            
            if not coupon.is_valid:
                return False, coupon, "Discount code has expired or is not active"
            
            if order_amount < coupon.minimum_order_amount:
                return False, coupon, f"Minimum order amount is {coupon.minimum_order_amount}"
            
            # Check user usage limit
            usage_count = self.session.query(CouponUsage).filter(
                and_(
                    CouponUsage.coupon_id == coupon.id,
                    CouponUsage.user_id == user_id
                )
            ).count()
            
            if not coupon.can_be_used_by_user(user_id, usage_count):
                return False, coupon, "You have reached the usage limit for this coupon"
            
            return True, coupon, "Valid discount code"
            
        except SQLAlchemyError as e:
            raise e
    
    def apply_discount(self, coupon: Coupon, user_id: int, order_amount: float,
                      cart_id: Optional[int] = None, session_id: Optional[str] = None) -> float:
        """
        Apply discount and record usage
        
        Args:
            coupon: Coupon instance
            user_id: User ID
            order_amount: Order amount
            cart_id: Optional cart ID
            session_id: Optional session ID
            
        Returns:
            float: Discount amount applied
        """
        try:
            discount_amount = coupon.calculate_discount(order_amount)
            
            if discount_amount > 0:
                # Record coupon usage
                usage = CouponUsage(
                    coupon_id=coupon.id,
                    user_id=user_id,
                    cart_id=cart_id,
                    order_amount=order_amount,
                    discount_amount=discount_amount,
                    session_id=session_id
                )
                self.session.add(usage)
                
                # Update coupon usage counters
                coupon.increment_usage(discount_amount)
                
                self.session.commit()
            
            return discount_amount
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def get_enrollment_with_relations(self, enrollment_id: str) -> Optional[Enrollment]:
        """
        Get enrollment with course and user relations loaded
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            Optional[Enrollment]: Enrollment with relations or None
        """
        try:
            return self.session.query(Enrollment).options(
                joinedload(Enrollment.course),
                joinedload(Enrollment.user)
            ).filter(Enrollment.id == enrollment_id).first()
        except SQLAlchemyError as e:
            raise e
    
    def search_enrollments(self, user_id: Optional[int] = None,
                          course_id: Optional[int] = None,
                          status: Optional[str] = None,
                          email: Optional[str] = None,
                          page: int = 1, limit: int = 10) -> tuple[List[Enrollment], int]:
        """
        Search enrollments with multiple filters
        
        Args:
            user_id: Optional user ID filter
            course_id: Optional course ID filter
            status: Optional status filter
            email: Optional email filter
            page: Page number
            limit: Items per page
            
        Returns:
            tuple[List[Enrollment], int]: (enrollments, total_count)
        """
        try:
            query = self.session.query(Enrollment).options(
                joinedload(Enrollment.course),
                joinedload(Enrollment.user)
            )
            
            # Apply filters
            if user_id:
                query = query.filter(Enrollment.user_id == user_id)
            if course_id:
                query = query.filter(Enrollment.course_id == course_id)
            if status:
                try:
                    status_enum = EnrollmentStatus(status)
                    query = query.filter(Enrollment.status == status_enum)
                except ValueError:
                    return [], 0
            if email:
                query = query.filter(Enrollment.email.ilike(f"%{email}%"))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            enrollments = query.order_by(desc(Enrollment.created_at)).offset(offset).limit(limit).all()
            
            return enrollments, total_count
            
        except SQLAlchemyError as e:
            raise e
