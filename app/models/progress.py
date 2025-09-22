"""
Progress models for tracking user lesson completion and course progress
"""

from enum import Enum
from datetime import datetime
from sqlalchemy import Numeric
from app import db

class ProgressStatus(Enum):
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'

class LessonProgress(db.Model):
    """Track user progress for individual lessons"""
    __tablename__ = 'lesson_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Progress tracking
    status = db.Column(db.Enum(ProgressStatus), nullable=False, default=ProgressStatus.NOT_STARTED)
    watch_time_seconds = db.Column(db.Integer, default=0)
    completion_percentage = db.Column(db.Float, default=0.0)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Timestamps
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='lesson_progress')
    lesson = db.relationship('Lesson', backref='user_progress')
    course = db.relationship('Course', backref='lesson_progress')
    
    # Unique constraint per user per lesson
    __table_args__ = (
        db.UniqueConstraint('user_id', 'lesson_id', name='unique_user_lesson_progress'),
    )
    
    def __init__(self, user_id, lesson_id, course_id, **kwargs):
        self.user_id = user_id
        self.lesson_id = lesson_id
        self.course_id = course_id
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def mark_started(self):
        """Mark lesson as started"""
        if self.status == ProgressStatus.NOT_STARTED:
            self.status = ProgressStatus.IN_PROGRESS
            self.started_at = datetime.utcnow()
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self):
        """Mark lesson as completed"""
        self.status = ProgressStatus.COMPLETED
        self.is_completed = True
        self.completion_percentage = 100.0
        self.completed_at = datetime.utcnow()
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_progress(self, watch_time=None, completion_percentage=None):
        """Update lesson progress"""
        if watch_time is not None:
            self.watch_time_seconds = max(0, watch_time)
        
        if completion_percentage is not None:
            self.completion_percentage = max(0.0, min(100.0, completion_percentage))
            
            # Mark as completed if 100%
            if self.completion_percentage >= 100.0:
                self.mark_completed()
            elif self.status == ProgressStatus.NOT_STARTED:
                self.mark_started()
        
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lesson_id': self.lesson_id,
            'course_id': self.course_id,
            'status': self.status.value,
            'watch_time_seconds': self.watch_time_seconds,
            'completion_percentage': self.completion_percentage,
            'is_completed': self.is_completed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<LessonProgress {self.id}: User {self.user_id} -> Lesson {self.lesson_id}>'

class CourseProgress(db.Model):
    """Track overall user progress for courses"""
    __tablename__ = 'course_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrollment_id = db.Column(db.String(36), db.ForeignKey('enrollments.id'), nullable=False)
    
    # Progress tracking
    completed_lessons = db.Column(db.Integer, default=0)
    total_lessons = db.Column(db.Integer, default=0)
    completion_percentage = db.Column(db.Float, default=0.0)
    total_watch_time_seconds = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Timestamps
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='course_progress')
    course = db.relationship('Course', backref='user_progress')
    enrollment = db.relationship('Enrollment', backref='progress_record')
    
    # Unique constraint per user per course
    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='unique_user_course_progress'),
    )
    
    def __init__(self, user_id, course_id, enrollment_id, total_lessons=0, **kwargs):
        self.user_id = user_id
        self.course_id = course_id
        self.enrollment_id = enrollment_id
        self.total_lessons = total_lessons
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def update_progress(self):
        """Recalculate progress based on lesson progress"""
        from app.dao.course_dao import CourseDAO
        
        # Get total lessons for this course
        course = CourseDAO.get_by_id(self.course_id)
        if course:
            self.total_lessons = course.total_lessons
        
        # Count completed lessons
        completed_count = LessonProgress.query.filter_by(
            user_id=self.user_id,
            course_id=self.course_id,
            is_completed=True
        ).count()
        
        # Calculate total watch time
        total_time = db.session.query(
            db.func.sum(LessonProgress.watch_time_seconds)
        ).filter_by(
            user_id=self.user_id,
            course_id=self.course_id
        ).scalar() or 0
        
        # Update values
        self.completed_lessons = completed_count
        self.total_watch_time_seconds = total_time
        
        if self.total_lessons > 0:
            self.completion_percentage = (completed_count / self.total_lessons) * 100
        else:
            self.completion_percentage = 0.0
        
        # Mark as completed if all lessons done
        if self.total_lessons > 0 and completed_count >= self.total_lessons:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
        
        # Mark as started if any progress
        if completed_count > 0 and not self.started_at:
            self.started_at = datetime.utcnow()
        
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'enrollment_id': self.enrollment_id,
            'completed_lessons': self.completed_lessons,
            'total_lessons': self.total_lessons,
            'completion_percentage': self.completion_percentage,
            'total_watch_time_seconds': self.total_watch_time_seconds,
            'is_completed': self.is_completed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<CourseProgress {self.id}: User {self.user_id} -> Course {self.course_id}>'

# Legacy models for compatibility
class Progress(db.Model):
    __tablename__ = 'progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Achievement(db.Model):
    __tablename__ = 'achievements'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Certificate(db.Model):
    __tablename__ = 'certificates'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)