"""
Authentication validators
"""

from marshmallow import Schema, fields, ValidationError, validates, validates_schema
from app.models.user import User


class UserRegistrationSchema(Schema):
    """Schema validation cho user registration"""
    
    email = fields.Email(required=True, error_messages={'required': 'Email is required'})
    password = fields.Str(required=True, validate=lambda x: len(x) >= 8, 
                         error_messages={'required': 'Password is required'})
    first_name = fields.Str(required=True, validate=lambda x: len(x.strip()) >= 2,
                           error_messages={'required': 'First name is required'})
    last_name = fields.Str(required=True, validate=lambda x: len(x.strip()) >= 2,
                          error_messages={'required': 'Last name is required'})
    role = fields.Str(missing='student', validate=lambda x: x in ['student', 'instructor'])
    
    @validates('email')
    def validate_email_format(self, value):
        """Validate email format và domain"""
        if not value or '@' not in value:
            raise ValidationError('Invalid email format')
    
    @validates('password')
    def validate_password_strength(self, value):
        """Validate password strength"""
        if len(value) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        # Add more password strength checks if needed
    
    @validates_schema
    def validate_email_unique(self, data, **kwargs):
        """Validate email uniqueness"""
        if 'email' in data:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                raise ValidationError('Email already registered', field_name='email')


class UserLoginSchema(Schema):
    """Schema validation cho user login"""
    
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember_me = fields.Bool(missing=False)


class EmailConfirmationSchema(Schema):
    """Schema validation cho email confirmation"""
    
    email = fields.Email(required=True)


class PasswordResetRequestSchema(Schema):
    """Schema validation cho password reset request"""
    
    email = fields.Email(required=True)


class PasswordResetSchema(Schema):
    """Schema validation cho password reset"""
    
    token = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=lambda x: len(x) >= 8)
    
    @validates('new_password')
    def validate_password_strength(self, value):
        """Validate new password strength"""
        if len(value) < 8:
            raise ValidationError('Password must be at least 8 characters long')