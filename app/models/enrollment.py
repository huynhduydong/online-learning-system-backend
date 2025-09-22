"""
Enrollment models for Course Registration Workflow
Implements course enrollment and registration functionality
"""

import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import Numeric
from app import db

class EnrollmentStatus(Enum):
    PENDING = 'pending'
    PAYMENT_PENDING = 'payment_pending'
    ENROLLED = 'enrolled'
    ACTIVATING = 'activating'
    ACTIVE = 'active'
    CANCELLED = 'cancelled'

class PaymentStatus(Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class Enrollment(db.Model):
    """
    Enrollment model for course registration workflow
    
    Business Rules:
    - Each user can only enroll once per course
    - Enrollment ID uses UUID for security
    - Payment is required for paid courses
    - Access is granted after successful payment/enrollment
    - Free courses get immediate access
    """
    __tablename__ = 'enrollments'
    
    # Primary key using UUID
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Enrollment details
    full_name = db.Column(db.String(200), nullable=False)  # For certificate
    email = db.Column(db.String(255), nullable=False)  # For certificate delivery
    
    # Status tracking
    status = db.Column(db.Enum(EnrollmentStatus), nullable=False, default=EnrollmentStatus.PENDING)
    payment_status = db.Column(db.Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Financial information
    payment_amount = db.Column(Numeric(10, 2), nullable=False, default=0.00)
    discount_applied = db.Column(Numeric(10, 2), default=0.00)
    discount_code = db.Column(db.String(50), nullable=True)
    
    # Access control
    access_granted = db.Column(db.Boolean, default=False)
    
    # Timestamps
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    activation_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Retry mechanism for activation
    activation_attempts = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    next_retry_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')
    
    # Unique constraint to prevent duplicate enrollments
    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='unique_user_course_enrollment'),
    )
    
    def __init__(self, user_id, course_id, full_name, email, payment_amount=0.00, discount_code=None, discount_applied=0.00):
        """Initialize enrollment with required fields"""
        self.user_id = user_id
        self.course_id = course_id
        self.full_name = full_name.strip()
        self.email = email.lower().strip()
        self.payment_amount = payment_amount
        self.discount_code = discount_code
        self.discount_applied = discount_applied or 0.00
        
        # Set initial status based on payment requirement
        if payment_amount > 0:
            self.status = EnrollmentStatus.PAYMENT_PENDING
            self.payment_status = PaymentStatus.PENDING
        else:
            self.status = EnrollmentStatus.ENROLLED
            self.payment_status = PaymentStatus.COMPLETED
            self.access_granted = True
            self.activation_date = datetime.utcnow()
    
    @property
    def payment_required(self):
        """Check if payment is required for this enrollment"""
        return self.payment_amount > 0
    
    @property
    def final_amount(self):
        """Calculate final amount after discount"""
        return max(0, self.payment_amount - self.discount_applied)
    
    @property
    def can_retry_activation(self):
        """Check if activation can be retried"""
        return (self.activation_attempts < self.max_retries and 
                self.status == EnrollmentStatus.ACTIVATING and
                (self.next_retry_at is None or datetime.utcnow() >= self.next_retry_at))
    
    def update_status(self, new_status, payment_status=None):
        """Update enrollment status with validation"""
        old_status = self.status
        self.status = new_status
        
        if payment_status:
            self.payment_status = payment_status
        
        # Handle status transitions
        if new_status == EnrollmentStatus.ENROLLED:
            self.access_granted = True
            if not self.activation_date:
                self.activation_date = datetime.utcnow()
        elif new_status == EnrollmentStatus.ACTIVE:
            self.access_granted = True
            if not self.activation_date:
                self.activation_date = datetime.utcnow()
        elif new_status == EnrollmentStatus.CANCELLED:
            self.access_granted = False
            
        self.updated_at = datetime.utcnow()
        return old_status
    
    def increment_activation_attempt(self):
        """Increment activation attempt counter"""
        self.activation_attempts += 1
        if self.activation_attempts < self.max_retries:
            # Set next retry time (exponential backoff)
            import datetime as dt
            retry_delay = min(300 * (2 ** (self.activation_attempts - 1)), 900)  # Max 15 minutes
            self.next_retry_at = datetime.utcnow() + dt.timedelta(seconds=retry_delay)
        
    def to_dict(self, include_course_info=False, include_progress=False):
        """Convert enrollment to dictionary for API responses"""
        try:
            # Base data with safe conversions
            data = {
                'id': self.id,
                'course_id': self.course_id,
                'user_id': self.user_id,
                'status': self.status.value if self.status else 'pending',
                'payment_status': self.payment_status.value if self.payment_status else 'pending',
                'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
                'activation_date': self.activation_date.isoformat() if self.activation_date else None,
                'payment_amount': float(self.payment_amount) if self.payment_amount is not None else 0.0,
                'discount_applied': float(self.discount_applied) if self.discount_applied is not None else 0.0,
                'access_granted': bool(self.access_granted) if self.access_granted is not None else False,
                'full_name': self.full_name or '',
                'email': self.email or ''
            }
            
            # Add course information safely
            if include_course_info:
                try:
                    if self.course:
                        data['course'] = {
                            'id': self.course.id,
                            'title': getattr(self.course, 'title', 'Unknown Course'),
                            'slug': getattr(self.course, 'slug', ''),
                            'thumbnail_url': getattr(self.course, 'thumbnail_url', None),
                            'difficulty_level': (
                                self.course.difficulty_level.value 
                                if hasattr(self.course, 'difficulty_level') and self.course.difficulty_level 
                                else None
                            ),
                            'instructor': {
                                'id': getattr(self.course, 'instructor_id', None),
                                'name': getattr(self.course, 'instructor_name', None)
                            } if hasattr(self.course, 'instructor_name') and self.course.instructor_name else None
                        }
                    else:
                        data['course'] = None
                except Exception:
                    # If there's an error accessing course data, set to None
                    data['course'] = None
            
            # Add progress information safely
            if include_progress:
                try:
                    total_lessons = 0
                    if self.course and hasattr(self.course, 'total_lessons'):
                        total_lessons = getattr(self.course, 'total_lessons', 0)
                    
                    data['progress'] = {
                        'completed_lessons': 0,
                        'total_lessons': total_lessons,
                        'percentage': 0,
                        'last_accessed': None,
                        'total_time_spent': 0
                    }
                except Exception:
                    # If there's an error accessing progress data, set defaults
                    data['progress'] = {
                        'completed_lessons': 0,
                        'total_lessons': 0,
                        'percentage': 0,
                        'last_accessed': None,
                        'total_time_spent': 0
                    }
            
            return data
            
        except Exception as e:
            # Fallback to basic data if there are any errors
            return {
                'id': getattr(self, 'id', None),
                'course_id': getattr(self, 'course_id', None),
                'user_id': getattr(self, 'user_id', None),
                'status': 'pending',
                'payment_status': 'pending',
                'enrollment_date': None,
                'activation_date': None,
                'payment_amount': 0.0,
                'discount_applied': 0.0,
                'access_granted': False,
                'full_name': '',
                'email': '',
                'error': 'Error converting enrollment data'
            }
    
    def __repr__(self):
        return f'<Enrollment {self.id}: User {self.user_id} -> Course {self.course_id}>'