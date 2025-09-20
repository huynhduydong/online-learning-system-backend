"""
Course models - Placeholder
Will be implemented in Sprint 2: Course Discovery
"""

from enum import Enum
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

# Placeholder models - will be implemented in Sprint 2
class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Module(db.Model):
    __tablename__ = 'modules'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)

class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)

class Content(db.Model):
    __tablename__ = 'content'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)