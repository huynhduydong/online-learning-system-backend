"""
Base exceptions cho Online Learning System
"""

class APIException(Exception):
    """Base exception cho API errors"""
    
    def __init__(self, message, status_code=400, error_code=None, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self):
        """Convert exception to dictionary for JSON response"""
        return {
            'success': False,
            'error': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class ValidationException(APIException):
    """Exception cho validation errors"""
    
    def __init__(self, message, field_errors=None):
        super().__init__(message, status_code=400, error_code='VALIDATION_ERROR')
        self.field_errors = field_errors or {}
        self.details['field_errors'] = self.field_errors


class AuthenticationException(APIException):
    """Exception cho authentication errors"""
    
    def __init__(self, message="Authentication required"):
        super().__init__(message, status_code=401, error_code='AUTH_ERROR')


class AuthorizationException(APIException):
    """Exception cho authorization errors"""
    
    def __init__(self, message="Access denied"):
        super().__init__(message, status_code=403, error_code='ACCESS_DENIED')


class ResourceNotFoundException(APIException):
    """Exception cho resource not found errors"""
    
    def __init__(self, message="Resource not found", resource_type=None):
        super().__init__(message, status_code=404, error_code='NOT_FOUND')
        if resource_type:
            self.details['resource_type'] = resource_type


class BusinessLogicException(APIException):
    """Exception cho business logic errors"""
    
    def __init__(self, message, error_code='BUSINESS_ERROR'):
        super().__init__(message, status_code=422, error_code=error_code)


class ExternalServiceException(APIException):
    """Exception cho external service errors"""
    
    def __init__(self, message, service_name=None):
        super().__init__(message, status_code=503, error_code='SERVICE_ERROR')
        if service_name:
            self.details['service'] = service_name