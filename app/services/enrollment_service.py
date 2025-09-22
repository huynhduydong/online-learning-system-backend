"""
Enrollment Service
Business logic for course enrollment and registration workflow
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.dao.enrollment_dao import EnrollmentDAO
from app.dao.payment_dao import PaymentDAO, TransactionDAO
from app.dao.user_dao import UserDAO
from app.models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus as PaymentStatusEnum
from app.models.course import Course
from app.models.user import User
from app.models.coupon import Coupon
from app.exceptions.validation_exception import ValidationException

logger = logging.getLogger(__name__)


class EnrollmentService:
    """
    Service class for enrollment business logic
    """
    
    def __init__(self):
        self.enrollment_dao = EnrollmentDAO()
        self.payment_dao = PaymentDAO()
        self.transaction_dao = TransactionDAO()
        self.user_dao = UserDAO()
    
    def register_for_course(self, user_id: int, course_id: str, full_name: str,
                          email: str, discount_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize course registration process
        
        Args:
            user_id: User ID
            course_id: Course ID
            full_name: Student's full name
            email: Email for certificate delivery
            discount_code: Optional discount code
            
        Returns:
            Dict[str, Any]: Registration response
            
        Raises:
            ValidationException: Validation errors
        """
        try:
            # Validate inputs
            self._validate_registration_inputs(user_id, course_id, full_name, email)
            
            # Get course and user
            course = Course.query.get(int(course_id))
            if not course:
                raise ValidationException({"course_id": ["Course not found or not available for enrollment"]})
            
            user = self.user_dao.get_by_id(user_id)
            if not user:
                raise ValidationException({"user_id": ["User not found"]})
            
            # Check if already enrolled
            existing_enrollment = self.enrollment_dao.get_by_user_and_course(user_id, int(course_id))
            if existing_enrollment:
                raise ValidationException({"email": ["This email is already enrolled in this course"]})
            
            # Calculate payment details
            payment_amount = float(course.price or 0)
            discount_applied = 0.00
            discount_code_used = None
            
            # Validate and apply discount code if provided
            if discount_code:
                is_valid, coupon, message = self.enrollment_dao.validate_discount_code(
                    discount_code, user_id, payment_amount
                )
                if not is_valid:
                    raise ValidationException({"discount_code": [message]})
                
                if coupon:
                    discount_applied = self.enrollment_dao.apply_discount(
                        coupon, user_id, payment_amount
                    )
                    discount_code_used = discount_code
            
            # Create enrollment
            enrollment = self.enrollment_dao.create_enrollment(
                user_id=user_id,
                course_id=int(course_id),
                full_name=full_name,
                email=email,
                payment_amount=payment_amount,
                discount_code=discount_code_used,
                discount_applied=discount_applied
            )
            
            # Prepare response
            response_data = {
                "enrollment": enrollment.to_dict(),
                "payment_required": enrollment.payment_required,
                "payment_url": None,
                "access_immediate": not enrollment.payment_required
            }
            
            # Generate payment URL if payment is required
            if enrollment.payment_required:
                response_data["payment_url"] = self._generate_payment_url(enrollment)
            
            logger.info(f"Course registration initiated for user {user_id}, course {course_id}")
            return response_data
            
        except ValidationException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error during registration: {str(e)}")
            raise ValidationException({"error": ["Registration failed due to database error"]})
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            raise ValidationException({"error": ["An unexpected error occurred during registration"]})
    
    def process_payment(self, enrollment_id: str, payment_method: str,
                       payment_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process payment for enrollment
        
        Args:
            enrollment_id: Enrollment ID
            payment_method: Payment method
            payment_details: Payment details
            
        Returns:
            Dict[str, Any]: Payment response
            
        Raises:
            ValidationException: Validation errors
        """
        try:
            # Validate enrollment
            enrollment = self.enrollment_dao.get_by_id(enrollment_id)
            if not enrollment:
                raise ValidationException({"enrollment_id": ["Enrollment not found"]})
            
            if enrollment.status != EnrollmentStatus.PAYMENT_PENDING:
                raise ValidationException({"enrollment_id": ["Enrollment is not pending payment"]})
            
            # Validate payment method
            try:
                payment_method_enum = PaymentMethod(payment_method)
            except ValueError:
                raise ValidationException({"payment_method": ["Invalid payment method"]})
            
            # Create payment record
            payment = self.payment_dao.create_payment(
                enrollment_id=enrollment_id,
                user_id=enrollment.user_id,
                payment_method=payment_method_enum,
                amount=enrollment.final_amount
            )
            
            # Process payment based on method
            payment_success = False
            transaction_id = None
            error_details = None
            
            if payment_method_enum == PaymentMethod.CREDIT_CARD:
                payment_success, transaction_id, error_details = self._process_credit_card_payment(
                    payment, payment_details
                )
            elif payment_method_enum == PaymentMethod.PAYPAL:
                payment_success, transaction_id, error_details = self._process_paypal_payment(
                    payment, payment_details
                )
            elif payment_method_enum == PaymentMethod.BANK_TRANSFER:
                payment_success, transaction_id, error_details = self._process_bank_transfer_payment(
                    payment, payment_details
                )
            
            # Update payment and enrollment status
            if payment_success:
                self.payment_dao.update_payment_status(
                    payment.id, PaymentStatusEnum.COMPLETED, transaction_id
                )
                self.enrollment_dao.update_enrollment_status(
                    enrollment_id, EnrollmentStatus.ENROLLED, PaymentStatus.COMPLETED
                )
                
                # Set payment details
                self.payment_dao.set_payment_details(payment.id, payment_details)
                
                logger.info(f"Payment completed for enrollment {enrollment_id}")
                
                # Get updated enrollment
                updated_enrollment = self.enrollment_dao.get_by_id(enrollment_id)
                return updated_enrollment.to_dict()
            else:
                self.payment_dao.update_payment_status(
                    payment.id, PaymentStatusEnum.FAILED, 
                    error_code=error_details.get('error_code') if error_details else 'PAYMENT_FAILED',
                    error_message=error_details.get('message') if error_details else 'Payment processing failed'
                )
                self.enrollment_dao.update_enrollment_status(
                    enrollment_id, EnrollmentStatus.PAYMENT_PENDING, PaymentStatus.FAILED
                )
                
                logger.warning(f"Payment failed for enrollment {enrollment_id}: {error_details}")
                
                raise ValidationException({
                    "payment_error": [error_details.get('message', 'Payment processing failed')],
                    "error_code": [error_details.get('error_code', 'PAYMENT_FAILED')],
                    "gateway_response": [error_details.get('gateway_response', 'Transaction declined')]
                })
                
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            raise ValidationException({"error": ["Payment processing failed"]})
    
    def activate_course_access(self, enrollment_id: str) -> Dict[str, Any]:
        """
        Activate course access for enrollment
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            Dict[str, Any]: Activation response
        """
        try:
            enrollment = self.enrollment_dao.get_by_id(enrollment_id)
            if not enrollment:
                raise ValidationException({"enrollment_id": ["Enrollment not found"]})
            
            # Check if enrollment is eligible for activation
            if enrollment.status not in [EnrollmentStatus.ENROLLED, EnrollmentStatus.ACTIVATING]:
                raise ValidationException({"enrollment_id": ["Enrollment is not eligible for activation"]})
            
            if enrollment.payment_status != PaymentStatus.COMPLETED:
                raise ValidationException({"enrollment_id": ["Payment must be completed before activation"]})
            
            # Simulate activation process (could involve external systems)
            activation_success = self._perform_activation(enrollment)
            
            if activation_success:
                # Update enrollment to active
                self.enrollment_dao.update_enrollment_status(
                    enrollment_id, EnrollmentStatus.ACTIVE
                )
                
                # Get first lesson URL
                first_lesson_url = self._get_first_lesson_url(enrollment.course_id)
                
                logger.info(f"Course access activated for enrollment {enrollment_id}")
                
                return {
                    "success": True,
                    "access_granted": True,
                    "first_lesson_url": first_lesson_url,
                    "retry_available": False,
                    "activation_time": datetime.utcnow().isoformat()
                }
            else:
                # Update to activating status and increment attempt
                self.enrollment_dao.update_enrollment_status(
                    enrollment_id, EnrollmentStatus.ACTIVATING
                )
                self.enrollment_dao.increment_activation_attempt(enrollment_id)
                
                # Get updated enrollment for retry info
                updated_enrollment = self.enrollment_dao.get_by_id(enrollment_id)
                
                return {
                    "success": False,
                    "access_granted": False,
                    "first_lesson_url": None,
                    "retry_available": updated_enrollment.can_retry_activation,
                    "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
                }
                
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error activating course access: {str(e)}")
            raise ValidationException({"error": ["Activation failed"]})
    
    def retry_activation(self, enrollment_id: str) -> Dict[str, Any]:
        """
        Retry course activation
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            Dict[str, Any]: Retry response
        """
        try:
            enrollment = self.enrollment_dao.get_by_id(enrollment_id)
            if not enrollment:
                raise ValidationException({"enrollment_id": ["Enrollment not found"]})
            
            if not enrollment.can_retry_activation:
                raise ValidationException({"enrollment_id": ["No retries available for this enrollment"]})
            
            # Attempt activation again
            return self.activate_course_access(enrollment_id)
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error retrying activation: {str(e)}")
            raise ValidationException({"error": ["Retry failed"]})
    
    def get_enrollment_status(self, enrollment_id: str) -> Dict[str, Any]:
        """
        Get enrollment status
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            Dict[str, Any]: Enrollment status data
        """
        try:
            enrollment = self.enrollment_dao.get_enrollment_with_relations(enrollment_id)
            if not enrollment:
                raise ValidationException({"enrollment_id": ["Enrollment not found"]})
            
            response_data = enrollment.to_dict(include_course_info=True, include_progress=True)
            
            # Add additional course information
            if enrollment.course:
                response_data["course_title"] = enrollment.course.title
                response_data["course_slug"] = enrollment.course.slug
            
            # Add certificate information (placeholder)
            response_data["certificate"] = {
                "issued": False,
                "issue_date": None,
                "certificate_url": None
            }
            
            return response_data
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error getting enrollment status: {str(e)}")
            raise ValidationException({"error": ["Failed to retrieve enrollment status"]})
    
    def get_user_enrollments(self, user_id: int, status_filter: Optional[str] = None,
                           page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """
        Get user's course enrollments
        
        Args:
            user_id: User ID
            status_filter: Optional status filter
            page: Page number
            limit: Items per page
            
        Returns:
            Dict[str, Any]: User enrollments with pagination
        """
        try:
            # Validate user_id
            if not isinstance(user_id, int) or user_id <= 0:
                logger.error(f"Invalid user_id: {user_id}")
                raise ValidationException({"user_id": ["Invalid user ID"]})
            
            # Validate pagination parameters
            if page < 1:
                page = 1
            if limit < 1:
                limit = 10
            elif limit > 50:
                limit = 50
            
            logger.info(f"Getting enrollments for user {user_id}, status: {status_filter}, page: {page}, limit: {limit}")
            
            # Get enrollments from DAO with error handling
            try:
                enrollments, total_count = self.enrollment_dao.get_user_enrollments(
                    user_id, status_filter, page, limit
                )
            except SQLAlchemyError as e:
                logger.error(f"Database error getting user enrollments for user {user_id}: {str(e)}")
                raise ValidationException({"error": ["Database error retrieving enrollments"]})
            except Exception as e:
                logger.error(f"Unexpected DAO error for user {user_id}: {str(e)}")
                raise ValidationException({"error": ["Failed to retrieve enrollments from database"]})
            
            # Ensure we have valid data
            if enrollments is None:
                enrollments = []
            if total_count is None:
                total_count = 0
            
            # Convert to response format with error handling
            enrollment_data = []
            for enrollment in enrollments:
                try:
                    if enrollment is not None:
                        data = enrollment.to_dict(include_course_info=True, include_progress=True)
                        enrollment_data.append(data)
                except Exception as e:
                    logger.warning(f"Error converting enrollment {getattr(enrollment, 'id', 'unknown')} to dict: {str(e)}")
                    # Skip this enrollment but continue with others
                    continue
            
            # Calculate pagination info safely
            try:
                total_pages = max(1, (total_count + limit - 1) // limit) if total_count > 0 else 1
            except (ZeroDivisionError, TypeError):
                total_pages = 1
            
            result = {
                "data": enrollment_data,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_count,
                    "per_page": limit,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
            logger.info(f"Successfully retrieved {len(enrollment_data)} enrollments for user {user_id}")
            return result
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting user enrollments for user {user_id}: {str(e)}", exc_info=True)
            raise ValidationException({"error": ["Failed to retrieve enrollments"]})
    
    def check_course_access(self, user_id: int, course_id: str) -> Dict[str, Any]:
        """
        Check if user has access to a course
        
        Args:
            user_id: User ID
            course_id: Course ID
            
        Returns:
            Dict[str, Any]: Access check response
        """
        try:
            enrollment = self.enrollment_dao.check_user_access(user_id, int(course_id))
            
            if enrollment:
                # User has access
                next_lesson_url = self._get_next_lesson_url(enrollment.course_id, user_id)
                
                return {
                    "hasAccess": True,
                    "enrollmentStatus": enrollment.to_dict(),
                    "nextLessonUrl": next_lesson_url,
                    "canDownloadCertificate": False  # Placeholder
                }
            else:
                # Check if user has any enrollment for this course
                any_enrollment = self.enrollment_dao.get_by_user_and_course(user_id, int(course_id))
                
                if any_enrollment:
                    if any_enrollment.payment_status == PaymentStatus.PENDING:
                        reason_code = "PAYMENT_PENDING"
                        message = "Payment is required to access this course"
                    else:
                        reason_code = "ENROLLMENT_EXPIRED"
                        message = "Your enrollment has expired or been cancelled"
                else:
                    reason_code = "NOT_ENROLLED"
                    message = "You need to enroll in this course to access the content"
                
                return {
                    "hasAccess": False,
                    "enrollmentStatus": None,
                    "reasonCode": reason_code,
                    "message": message
                }
                
        except Exception as e:
            logger.error(f"Error checking course access: {str(e)}")
            raise ValidationException({"error": ["Failed to check course access"]})
    
    # Private helper methods
    def _validate_registration_inputs(self, user_id: int, course_id: str, 
                                    full_name: str, email: str) -> None:
        """Validate registration inputs"""
        errors = {}
        
        # Validate course_id
        try:
            int(course_id)
        except (ValueError, TypeError):
            errors["course_id"] = ["Course ID must be a valid integer"]
        
        # Validate full_name
        if not full_name or len(full_name.strip()) < 2:
            errors["full_name"] = ["Full name must be at least 2 characters long"]
        elif len(full_name.strip()) > 100:
            errors["full_name"] = ["Full name must be less than 100 characters"]
        elif not full_name.replace(' ', '').replace('-', '').replace("'", '').isalpha():
            errors["full_name"] = ["Full name contains invalid characters"]
        
        # Validate email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not email or not re.match(email_pattern, email):
            errors["email"] = ["Invalid email format"]
        elif len(email) > 255:
            errors["email"] = ["Email must be less than 255 characters"]
        
        if errors:
            raise ValidationException(errors)
    
    def _generate_payment_url(self, enrollment: Enrollment) -> Optional[str]:
        """Generate payment URL for enrollment"""
        # This would integrate with actual payment gateway
        # For now, return a placeholder URL
        return f"/payment/process/{enrollment.id}"
    
    def _process_credit_card_payment(self, payment: Payment, 
                                   payment_details: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Process credit card payment"""
        # This would integrate with actual payment gateway (Stripe, etc.)
        # For demonstration, simulate success/failure
        
        # Validate required fields
        required_fields = ['card_number', 'card_expiry', 'card_cvv', 'card_holder_name']
        for field in required_fields:
            if field not in payment_details:
                return False, None, {
                    'error_code': 'MISSING_PAYMENT_DATA',
                    'message': f'Missing required field: {field}'
                }
        
        # Simulate payment processing
        # In real implementation, this would call payment gateway API
        import random
        success = random.choice([True, True, True, False])  # 75% success rate
        
        if success:
            transaction_id = f"txn_{payment.id}_{int(datetime.utcnow().timestamp())}"
            return True, transaction_id, None
        else:
            return False, None, {
                'error_code': 'CARD_DECLINED',
                'message': 'Credit card declined',
                'gateway_response': 'Insufficient funds'
            }
    
    def _process_paypal_payment(self, payment: Payment, 
                              payment_details: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Process PayPal payment"""
        # PayPal integration would go here
        # For demonstration, simulate success
        transaction_id = f"pp_{payment.id}_{int(datetime.utcnow().timestamp())}"
        return True, transaction_id, None
    
    def _process_bank_transfer_payment(self, payment: Payment, 
                                     payment_details: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Process bank transfer payment"""
        # Bank transfer integration would go here
        # For demonstration, simulate success
        transaction_id = f"bt_{payment.id}_{int(datetime.utcnow().timestamp())}"
        return True, transaction_id, None
    
    def _perform_activation(self, enrollment: Enrollment) -> bool:
        """Perform actual course activation"""
        # This would involve setting up user access in LMS, 
        # sending welcome emails, etc.
        # For demonstration, simulate mostly successful activation
        import random
        return random.choice([True, True, True, True, False])  # 80% success rate
    
    def _get_first_lesson_url(self, course_id: int) -> Optional[str]:
        """Get URL of first lesson in course"""
        # This would query the course structure to find the first lesson
        # For demonstration, return a placeholder URL
        return f"/courses/{course_id}/lessons/1"
    
    def _get_next_lesson_url(self, course_id: int, user_id: int) -> Optional[str]:
        """Get URL of next lesson for user"""
        # This would check user progress and return next lesson
        # For demonstration, return a placeholder URL
        return f"/courses/{course_id}/lessons/6"