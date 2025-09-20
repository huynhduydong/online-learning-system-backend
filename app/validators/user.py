"""
User validators
"""

from marshmallow import Schema, fields, ValidationError, validates
from app.utils.security import sanitize_input


class UserProfileUpdateSchema(Schema):
    """Schema validation cho user profile update"""
    
    first_name = fields.Str(allow_none=True)
    last_name = fields.Str(allow_none=True)
    
    @validates('first_name')
    def validate_first_name(self, value):
        """Validate first name"""
        if value is not None:
            sanitized = sanitize_input(value)
            if len(sanitized.strip()) < 2:
                raise ValidationError('First name must be at least 2 characters long')
    
    @validates('last_name')
    def validate_last_name(self, value):
        """Validate last name"""
        if value is not None:
            sanitized = sanitize_input(value)
            if len(sanitized.strip()) < 2:
                raise ValidationError('Last name must be at least 2 characters long')


class AvatarUploadSchema(Schema):
    """Schema validation cho avatar upload"""
    
    # File validation sẽ được handle trong service layer
    pass


class UserSearchSchema(Schema):
    """Schema validation cho user search"""
    
    query = fields.Str(required=True, validate=lambda x: len(x.strip()) >= 2)
    page = fields.Int(missing=1, validate=lambda x: x >= 1)
    per_page = fields.Int(missing=10, validate=lambda x: 1 <= x <= 100)
    
    @validates('query')
    def validate_query(self, value):
        """Validate search query"""
        sanitized = sanitize_input(value)
        if len(sanitized.strip()) < 2:
            raise ValidationError('Search query must be at least 2 characters long')