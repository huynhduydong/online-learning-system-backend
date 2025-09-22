"""
Custom validation exception for business logic errors.
"""

class ValidationException(Exception):
    """
    Exception raised for validation errors in business logic.
    
    This exception is used when business rules are violated
    or when input validation fails at the service layer.
    """
    
    def __init__(self, errors):
        """
        Initialize ValidationException.
        
        Args:
            errors (dict): Error details, e.g. {"email": ["This field is required"]}
        """
        # errors là dict, ví dụ {"email": ["..."]}
        self.errors = errors
        # để str(e) đọc được thay vì "<exception str() failed>"
        try:
            import json
            msg = json.dumps(errors, ensure_ascii=False)
        except Exception:
            msg = str(errors)
        super().__init__(msg)