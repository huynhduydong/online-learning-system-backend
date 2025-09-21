"""
Course models for Online Learning System
Implements course catalog browsing functionality
"""

from enum import Enum
from datetime import datetime
from sqlalchemy import Numeric
from app import db

class DifficultyLevel(Enum):
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'

class ContentType(Enum):
    VIDEO = 'video'
    TEXT = 'text'
    DOCUMENT = 'document'
    QUIZ = 'quiz'
    ASSIGNMENT = 'assignment'

class CourseStatus(Enum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'

class Course(db.Model):
    __tablename__ = 'courses'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic information
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    short_description = db.Column(db.String(500))
    
    # Instructor information
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    instructor_name = db.Column(db.String(255))  # Denormalized for performance
    
    # Category and difficulty
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    difficulty_level = db.Column(db.Enum(DifficultyLevel), nullable=False, default=DifficultyLevel.BEGINNER)
    
    # Pricing
    price = db.Column(Numeric(10, 2), nullable=False, default=0.00)
    original_price = db.Column(Numeric(10, 2))  # For discount display
    is_free = db.Column(db.Boolean, default=False)
    
    # Rating and popularity
    average_rating = db.Column(db.Float, default=0.0)
    total_ratings = db.Column(db.Integer, default=0)
    total_enrollments = db.Column(db.Integer, default=0)
    
    # Course metadata
    duration_hours = db.Column(db.Integer)  # Total course duration in hours
    total_lessons = db.Column(db.Integer, default=0)
    language = db.Column(db.String(50), default='vi')
    
    # Publishing and status
    status = db.Column(db.Enum(CourseStatus), nullable=False, default=CourseStatus.DRAFT)
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    
    # Media
    thumbnail_url = db.Column(db.String(500))
    preview_video_url = db.Column(db.String(500))
    
    # SEO and tags
    tags = db.Column(db.Text)  # JSON string of tags
    slug = db.Column(db.String(255), unique=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = db.relationship('Category', backref='courses')
    instructor = db.relationship('User', backref='taught_courses')
    
    def __init__(self, title, instructor_id, category_id, price=0.00, **kwargs):
        self.title = title
        self.instructor_id = instructor_id
        self.category_id = category_id
        self.price = price
        self.is_free = (price == 0.00)
        
        # Set optional fields from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<Course {self.id}: {self.title}>'
    
    @property
    def display_price(self):
        """Return formatted price for display"""
        if self.is_free:
            return "Miễn phí"
        return f"{int(self.price):,}đ"
    
    @property
    def has_enough_ratings(self):
        """Check if course has enough ratings to display rating"""
        return self.total_ratings >= 5
    
    @property
    def display_rating(self):
        """Return rating for display (only if enough ratings)"""
        if self.has_enough_ratings:
            return round(self.average_rating, 1)
        return None
    
    def update_rating(self, new_rating):
        """Update course rating with new rating"""
        if self.total_ratings == 0:
            self.average_rating = new_rating
        else:
            total_score = self.average_rating * self.total_ratings
            total_score += new_rating
            self.total_ratings += 1
            self.average_rating = total_score / self.total_ratings
        
class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    slug = db.Column(db.String(100), unique=True)
    icon = db.Column(db.String(100))  # Icon class or URL
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, **kwargs):
        self.name = name
        self.slug = name.lower().replace(' ', '-')
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<Category {self.id}: {self.name}>'

class Module(db.Model):
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='modules')
    
    def __init__(self, course_id, title, **kwargs):
        self.course_id = course_id
        self.title = title
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<Module {self.id}: {self.title}>'

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    content_type = db.Column(db.Enum(ContentType), nullable=False)
    duration_minutes = db.Column(db.Integer)
    sort_order = db.Column(db.Integer, default=0)
    is_preview = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    module = db.relationship('Module', backref='lessons')
    
    def __init__(self, module_id, title, content_type, **kwargs):
        self.module_id = module_id
        self.title = title
        self.content_type = content_type
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<Lesson {self.id}: {self.title}>'

class Content(db.Model):
    __tablename__ = 'content'
    
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content_data = db.Column(db.Text)  # JSON or text content
    file_url = db.Column(db.String(500))  # For video, document files
    sort_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lesson = db.relationship('Lesson', backref='contents')
    
    def __init__(self, lesson_id, title, **kwargs):
        self.lesson_id = lesson_id
        self.title = title
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<Content {self.id}: {self.title}>'