"""
Enrollment validators
Validates enrollment and payment request data
"""

import re
from typing import Dict, Any, Optional, List
from app.exceptions.validation_exception import ValidationException


class EnrollmentValidator:
    """Validator for enrollment-related operations"""
    
    @staticmethod
    def validate_registration_request(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate course registration request
        
        Args:
            data: Request data dictionary
            
        Returns:
            Dict[str, Any]: Validated and cleaned data
            
        Raises:
            ValidationException: If validation fails
        """
        errors = {}
        validated_data = {}
        
        # Validate course_id
        course_id = data.get('course_id')
        if not course_id:
            errors['course_id'] = ['Course ID is required']
        else:
            try:
                # Ensure course_id is string but can be converted to int
                validated_data['course_id'] = str(course_id).strip()
                int(validated_data['course_id'])  # Test if it's a valid integer
            except (ValueError, TypeError):
                errors['course_id'] = ['Course ID must be a valid number']
        
        # Validate full_name
        full_name = data.get('full_name')
        if not full_name:
            errors['full_name'] = ['Full name is required']
        else:
            full_name = str(full_name).strip()
            if len(full_name) < 2:
                errors['full_name'] = ['Full name must be at least 2 characters long']
            elif len(full_name) > 100:
                errors['full_name'] = ['Full name must be less than 100 characters']
            elif not re.match(r"^[a-zA-ZÀ-ỹ\s\-']+$", full_name):
                errors['full_name'] = ['Full name contains invalid characters']
            else:
                validated_data['full_name'] = full_name
        
        # Validate email
        email = data.get('email')
        if not email:
            errors['email'] = ['Email is required']
        else:
            email = str(email).strip().lower()
            if len(email) > 255:
                errors['email'] = ['Email must be less than 255 characters']
            elif not EnrollmentValidator._is_valid_email(email):
                errors['email'] = ['Invalid email format']
            else:
                validated_data['email'] = email
        
        # Validate discount_code (optional)
        discount_code = data.get('discount_code')
        if discount_code:
            discount_code = str(discount_code).strip().upper()
            if len(discount_code) > 50:
                errors['discount_code'] = ['Discount code must be less than 50 characters']
            elif not re.match(r"^[A-Z0-9_-]+$", discount_code):
                errors['discount_code'] = ['Discount code contains invalid characters']
            else:
                validated_data['discount_code'] = discount_code
        
        if errors:
            raise ValidationException(errors)
        
        return validated_data
    
    @staticmethod
    def validate_payment_request(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate payment processing request
        
        Args:
            data: Request data dictionary
            
        Returns:
            Dict[str, Any]: Validated and cleaned data
            
        Raises:
            ValidationException: If validation fails
        """
        errors = {}
        validated_data = {}
        
        # Validate enrollment_id
        enrollment_id = data.get('enrollment_id')
        if not enrollment_id:
            errors['enrollment_id'] = ['Enrollment ID is required']
        else:
            enrollment_id = str(enrollment_id).strip()
            if len(enrollment_id) != 36:  # UUID length
                errors['enrollment_id'] = ['Invalid enrollment ID format']
            else:
                validated_data['enrollment_id'] = enrollment_id
        
        # Validate payment_method
        payment_method = data.get('payment_method')
        valid_methods = ['credit_card', 'paypal', 'bank_transfer']
        if not payment_method:
            errors['payment_method'] = ['Payment method is required']
        elif payment_method not in valid_methods:
            errors['payment_method'] = [f'Payment method must be one of: {", ".join(valid_methods)}']
        else:
            validated_data['payment_method'] = payment_method
        
        # Validate payment_details
        payment_details = data.get('payment_details', {})
        if not isinstance(payment_details, dict):
            errors['payment_details'] = ['Payment details must be an object']
        else:
            validated_details = EnrollmentValidator._validate_payment_details(payment_method, payment_details)
            if validated_details.get('errors'):
                errors.update(validated_details['errors'])
            else:
                validated_data['payment_details'] = validated_details['data']
        
        if errors:
            raise ValidationException(errors)
        
        return validated_data
    
    @staticmethod
    def validate_enrollment_id(enrollment_id: Any) -> str:
        """
        Validate enrollment ID
        
        Args:
            enrollment_id: Enrollment ID to validate
            
        Returns:
            str: Validated enrollment ID
            
        Raises:
            ValidationException: If validation fails
        """
        if not enrollment_id:
            raise ValidationException({'enrollment_id': ['Enrollment ID is required']})
        
        enrollment_id = str(enrollment_id).strip()
        if len(enrollment_id) != 36:  # UUID length
            raise ValidationException({'enrollment_id': ['Invalid enrollment ID format']})
        
        return enrollment_id
    
    @staticmethod
    def validate_course_id(course_id: Any) -> str:
        """
        Validate course ID
        
        Args:
            course_id: Course ID to validate
            
        Returns:
            str: Validated course ID
            
        Raises:
            ValidationException: If validation fails
        """
        if not course_id:
            raise ValidationException({'course_id': ['Course ID is required']})
        
        try:
            course_id = str(course_id).strip()
            int(course_id)  # Test if it's a valid integer
            return course_id
        except (ValueError, TypeError):
            raise ValidationException({'course_id': ['Course ID must be a valid number']})
    
    @staticmethod
    def validate_pagination_params(page: Any, limit: Any) -> tuple[int, int]:
        """
        Validate pagination parameters
        
        Args:
            page: Page number
            limit: Items per page
            
        Returns:
            tuple[int, int]: (validated_page, validated_limit)
            
        Raises:
            ValidationException: If validation fails
        """
        errors = {}
        
        # Validate page
        try:
            page = int(page) if page is not None else 1
            if page < 1:
                errors['page'] = ['Page number must be at least 1']
        except (ValueError, TypeError):
            errors['page'] = ['Page number must be a valid integer']
            page = 1
        
        # Validate limit
        try:
            limit = int(limit) if limit is not None else 10
            if limit < 1:
                errors['limit'] = ['Limit must be at least 1']
            elif limit > 50:
                errors['limit'] = ['Limit cannot exceed 50']
        except (ValueError, TypeError):
            errors['limit'] = ['Limit must be a valid integer']
            limit = 10
        
        if errors:
            raise ValidationException(errors)
        
        return page, limit
    
    @staticmethod
    def validate_status_filter(status: Optional[str]) -> Optional[str]:
        """
        Validate enrollment status filter
        
        Args:
            status: Status to validate
            
        Returns:
            Optional[str]: Validated status or None
            
        Raises:
            ValidationException: If validation fails
        """
        if not status:
            return None
        
        valid_statuses = ['pending', 'payment_pending', 'enrolled', 'activating', 'active', 'cancelled']
        if status not in valid_statuses:
            raise ValidationException({
                'status': [f'Status must be one of: {", ".join(valid_statuses)}']
            })
        
        return status
    
    @staticmethod
    def _validate_payment_details(payment_method: str, payment_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate payment method specific details
        
        Args:
            payment_method: Payment method
            payment_details: Payment details to validate
            
        Returns:
            Dict[str, Any]: Validation result with 'data' or 'errors'
        """
        if payment_method == 'credit_card':
            return EnrollmentValidator._validate_credit_card_details(payment_details)
        elif payment_method == 'paypal':
            return EnrollmentValidator._validate_paypal_details(payment_details)
        elif payment_method == 'bank_transfer':
            return EnrollmentValidator._validate_bank_transfer_details(payment_details)
        else:
            return {'errors': {'payment_method': ['Unknown payment method']}}
    
    @staticmethod
    def _validate_credit_card_details(details: Dict[str, Any]) -> Dict[str, Any]:
        """Validate credit card payment details"""
        errors = {}
        validated_data = {}
        
        # Validate card_number
        card_number = details.get('card_number')
        if not card_number:
            errors['card_number'] = ['Card number is required']
        else:
            # Remove spaces and validate format
            card_number = re.sub(r'\s+', '', str(card_number))
            if not re.match(r'^\d{13,19}$', card_number):
                errors['card_number'] = ['Invalid card number format']
            else:
                # Mask all but last 4 digits for security
                validated_data['last_four_digits'] = card_number[-4:]
                validated_data['card_number'] = '*' * (len(card_number) - 4) + card_number[-4:]
        
        # Validate card_expiry
        card_expiry = details.get('card_expiry')
        if not card_expiry:
            errors['card_expiry'] = ['Card expiry is required']
        else:
            if not re.match(r'^\d{2}/\d{2}$', str(card_expiry)):
                errors['card_expiry'] = ['Card expiry must be in MM/YY format']
            else:
                validated_data['card_expiry'] = str(card_expiry)
        
        # Validate card_cvv
        card_cvv = details.get('card_cvv')
        if not card_cvv:
            errors['card_cvv'] = ['CVV is required']
        else:
            if not re.match(r'^\d{3,4}$', str(card_cvv)):
                errors['card_cvv'] = ['CVV must be 3 or 4 digits']
            else:
                # Don't store CVV in validated data for security
                pass
        
        # Validate card_holder_name
        card_holder_name = details.get('card_holder_name')
        if not card_holder_name:
            errors['card_holder_name'] = ['Cardholder name is required']
        else:
            card_holder_name = str(card_holder_name).strip()
            if len(card_holder_name) < 2:
                errors['card_holder_name'] = ['Cardholder name must be at least 2 characters']
            elif len(card_holder_name) > 255:
                errors['card_holder_name'] = ['Cardholder name must be less than 255 characters']
            elif not re.match(r"^[a-zA-Z\s\-'\.]+$", card_holder_name):
                errors['card_holder_name'] = ['Cardholder name contains invalid characters']
            else:
                validated_data['card_holder_name'] = card_holder_name
        
        if errors:
            return {'errors': errors}
        else:
            return {'data': validated_data}
    
    @staticmethod
    def _validate_paypal_details(details: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PayPal payment details"""
        errors = {}
        validated_data = {}
        
        # Validate paypal_email
        paypal_email = details.get('paypal_email')
        if not paypal_email:
            errors['paypal_email'] = ['PayPal email is required']
        else:
            paypal_email = str(paypal_email).strip().lower()
            if not EnrollmentValidator._is_valid_email(paypal_email):
                errors['paypal_email'] = ['Invalid PayPal email format']
            else:
                validated_data['paypal_email'] = paypal_email
        
        if errors:
            return {'errors': errors}
        else:
            return {'data': validated_data}
    
    @staticmethod
    def _validate_bank_transfer_details(details: Dict[str, Any]) -> Dict[str, Any]:
        """Validate bank transfer payment details"""
        errors = {}
        validated_data = {}
        
        # Validate bank_account
        bank_account = details.get('bank_account')
        if not bank_account:
            errors['bank_account'] = ['Bank account number is required']
        else:
            bank_account = str(bank_account).strip()
            if not re.match(r'^\d{8,20}$', bank_account):
                errors['bank_account'] = ['Bank account number must be 8-20 digits']
            else:
                # Store only last 4 digits for security
                validated_data['bank_account_last_four'] = bank_account[-4:]
        
        # Validate bank_code
        bank_code = details.get('bank_code')
        if not bank_code:
            errors['bank_code'] = ['Bank code is required']
        else:
            bank_code = str(bank_code).strip().upper()
            if not re.match(r'^[A-Z0-9]{3,10}$', bank_code):
                errors['bank_code'] = ['Bank code must be 3-10 alphanumeric characters']
            else:
                validated_data['bank_code'] = bank_code
        
        if errors:
            return {'errors': errors}
        else:
            return {'data': validated_data}
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Check if email format is valid"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
