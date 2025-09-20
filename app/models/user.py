"""
User model cho authentication và profile management
Implements User Stories: OLS-US-001, OLS-US-002, OLS-US-003
"""

from datetime import datetime, timedelta
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from app import db


class UserRole(Enum):
    """User roles trong hệ thống"""
    STUDENT = 'student'
    INSTRUCTOR = 'instructor'
    ADMIN = 'admin'


class User(db.Model):
    """
    User model cho authentication và profile management
    
    Business Rules:
    - Email phải unique trong hệ thống
    - Mật khẩu tối thiểu 8 ký tự, có chữ hoa, chữ thường, số
    - Tài khoản mới mặc định là "Student"
    - Email không thể thay đổi sau khi tạo tài khoản
    """
    __tablename__ = 'users'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    profile_image = db.Column(db.String(500), nullable=True)
    
    # Account settings
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_activity_at = db.Column(db.DateTime, nullable=True)
    
    # Security fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    confirmation_token = db.Column(db.String(255), nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships (commented out for now as related models may not exist)
    # courses = db.relationship('Course', backref='instructor', lazy='dynamic')
    # enrollments = db.relationship('Enrollment', backref='user', lazy='dynamic')
    # questions = db.relationship('Question', backref='user', lazy='dynamic')
    # answers = db.relationship('Answer', backref='user', lazy='dynamic')
    
    def __init__(self, email, password, first_name, last_name, role=UserRole.STUDENT):
        """Initialize user với required fields"""
        self.email = email.lower().strip()
        self.set_password(password)
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        self.role = role
    
    def set_password(self, password):
        """
        Set password với hashing
        Business Rule: Mật khẩu tối thiểu 8 ký tự
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_instructor(self):
        """Check if user is instructor"""
        return self.role == UserRole.INSTRUCTOR
    
    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    def can_create_courses(self):
        """Check if user can create courses"""
        return self.role in [UserRole.INSTRUCTOR, UserRole.ADMIN] and self.is_verified
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login_at = datetime.utcnow()
        self.last_activity_at = datetime.utcnow()
        db.session.commit()
    
    def update_activity(self):
        """Update last activity timestamp for session tracking"""
        self.last_activity_at = datetime.utcnow()
        db.session.commit()
    
    def is_session_expired(self):
        """
        Check if user session has expired based on activity
        Business Rule: Session timeout sau 24h nếu không có activity
        """
        if not self.last_activity_at:
            return True
        
        session_timeout = timedelta(hours=24)
        return datetime.utcnow() - self.last_activity_at > session_timeout
    
    def increment_failed_login(self):
        """
        Increment failed login attempts
        Business Rule: Sau 5 lần đăng nhập sai, tài khoản bị khóa 15 phút
        """
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()
    
    def reset_failed_login(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()
    
    @property
    def is_locked(self):
        """Check if account is locked"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def update_profile(self, first_name=None, last_name=None):
        """
        Update profile information with validation
        Returns dict of changes made
        """
        changes = {}
        
        if first_name is not None:
            is_valid, message = self.validate_name(first_name, "First name")
            if not is_valid:
                raise ValueError(message)
            
            if self.first_name != first_name:
                changes['first_name'] = {
                    'old': self.first_name,
                    'new': first_name
                }
                self.first_name = first_name
        
        if last_name is not None:
            is_valid, message = self.validate_name(last_name, "Last name")
            if not is_valid:
                raise ValueError(message)
            
            if self.last_name != last_name:
                changes['last_name'] = {
                    'old': self.last_name,
                    'new': last_name
                }
                self.last_name = last_name
        
        return changes
    
    def set_profile_image(self, image_path):
        """
        Set profile image path
        Business Rule: Ảnh đại diện được resize về 200x200px
        """
        self.profile_image = image_path
    
    @property
    def has_profile_image(self):
        """Check if user has a profile image"""
        return bool(self.profile_image)
    
    def get_enrollment_stats(self):
        """
        Get enrollment statistics for profile display
        Returns dict with enrollment counts
        """
        # Placeholder implementation - will be enhanced when enrollment models are available
        return {
            'total_enrollments': 0,
            'completed_courses': 0,
            'in_progress_courses': 0,
            'join_date': self.created_at.strftime('%B %Y') if self.created_at else 'Unknown'
        }
    
    def get_avatar_url(self):
        """
        Generate full avatar URL based on environment configuration
        Returns full URL or None if no avatar
        """
        if not self.profile_image:
            return None
        
        from flask import current_app, request
        
        # Get base URL from environment or request
        base_url = current_app.config.get('BASE_URL')
        if not base_url:
            # Fallback to request URL if BASE_URL not configured
            if request:
                base_url = f"{request.scheme}://{request.host}"
            else:
                base_url = "http://localhost:5000"  # Default fallback
        
        # Remove trailing slash
        base_url = base_url.rstrip('/')
        
        # Return full URL
        return f"{base_url}/{self.profile_image}"
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary for API responses"""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'profile_image': self.profile_image,
            'profile_image_url': self.get_avatar_url(),
            'role': self.role.value,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None
        }
        
        if include_sensitive:
            data.update({
                'failed_login_attempts': self.failed_login_attempts,
                'is_locked': self.is_locked,
                'has_confirmation_token': bool(self.confirmation_token)
            })
        
        return data
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password_strength(password):
        """
        Validate password strength
        Business Rule: Mật khẩu tối thiểu 8 ký tự, có chữ hoa, chữ thường, số
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        import re
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        return True, "Password is strong"
    
    @staticmethod
    def validate_name(name, field_name="Name"):
        """
        Validate name fields for profile updates
        Business Rule: Names must be at least 2 characters long
        """
        if not name or not isinstance(name, str):
            return False, f"{field_name} is required"
        
        name = name.strip()
        if len(name) < 2:
            return False, f"{field_name} must be at least 2 characters long"
        
        if len(name) > 100:
            return False, f"{field_name} must be less than 100 characters"
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        import re
        if not re.match(r"^[a-zA-ZÀ-ỹ\s\-']+$", name):
            return False, f"{field_name} contains invalid characters"
        
        return True, "Valid name"
    
    def __repr__(self):
        return f'<User {self.email}>'