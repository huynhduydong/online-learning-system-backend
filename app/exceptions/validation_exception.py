"""
Custom validation exception for business logic errors.
"""

class ValidationException(Exception):
    """
    Exception raised for validation errors in business logic.
    
    This exception is used when business rules are violated
    or when input validation fails at the service layer.
    """
    
    def __init__(self, message, field_errors=None):
        """
        Initialize ValidationException.
        
        Args:
            message (str): Error message
            field_errors (dict): Optional field-specific errors
        """
        super().__init__(message)
        self.message = message
        self.field_errors = field_errors or {}
    
    def __str__(self):
        return self.message