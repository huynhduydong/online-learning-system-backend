"""
Instructor Service
Business logic for instructor course management
"""

import re
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import desc, asc
from app import db
from app.models.user import User, UserRole
from app.models.course import Course, Category, CourseStatus, DifficultyLevel
from app.dao.course_dao import CourseDAO, CategoryDAO
from app.exceptions.base import ValidationException, BusinessLogicException


class InstructorService:
    """Service for instructor course management functionality"""
    
    @staticmethod
    def get_instructor_courses(instructor_id: int, page: int = 1, per_page: int = 10, 
                             status: str = 'all', sort_by: str = 'updated_at', 
                             sort_order: str = 'desc') -> Dict:
        """
        Get courses for a specific instructor with pagination and filtering
        """
        try:
            # Validate instructor exists and has permission
            instructor = User.query.get(instructor_id)
            if not instructor or not instructor.can_create_courses():
                raise BusinessLogicException("Instructor not found or not authorized")
            
            # Build query
            query = Course.query.filter_by(instructor_id=instructor_id)
            
            # Apply status filter
            if status != 'all':
                if status == 'draft':
                    query = query.filter_by(status=CourseStatus.DRAFT)
                elif status == 'published':
                    query = query.filter_by(status=CourseStatus.PUBLISHED)
            
            # Apply sorting
            sort_column = getattr(Course, sort_by, Course.updated_at)
            if sort_order == 'asc':
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
            
            # Paginate
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            # Format courses
            courses = []
            for course in pagination.items:
                courses.append(InstructorService._format_instructor_course(course))
            
            return {
                'courses': courses,
                'pagination': {
                    'current_page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'total_pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
            
        except BusinessLogicException:
            raise
        except Exception as e:
            raise BusinessLogicException(f"Failed to retrieve courses: {str(e)}")
    
    @staticmethod
    def create_course(instructor_id: int, title: str, short_description: str, **kwargs) -> Dict:
        """
        Create a new course for instructor
        """
        try:
            # Validate instructor
            instructor = User.query.get(instructor_id)
            if not instructor or not instructor.can_create_courses():
                raise BusinessLogicException("Instructor not found or not authorized to create courses")
            
            # Generate slug from title
            slug = InstructorService._generate_slug(title)
            
            # Check if slug is unique
            if Course.query.filter_by(slug=slug).first():
                # Add suffix to make it unique
                counter = 1
                base_slug = slug
                while Course.query.filter_by(slug=slug).first():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
            
            # Set default values
            difficulty_level = kwargs.get('difficulty_level', 'beginner')
            if difficulty_level == 'beginner':
                difficulty_enum = DifficultyLevel.BEGINNER
            elif difficulty_level == 'intermediate':
                difficulty_enum = DifficultyLevel.INTERMEDIATE
            else:
                difficulty_enum = DifficultyLevel.ADVANCED
            
            # Create course
            course = Course(
                title=title,
                short_description=short_description,
                slug=slug,
                instructor_id=instructor_id,
                instructor_name=instructor.full_name,
                language=kwargs.get('language', 'vi'),
                difficulty_level=difficulty_enum,
                category_id=kwargs.get('category_id'),
                price=kwargs.get('price', 0),
                is_free=kwargs.get('is_free', True),
                status=CourseStatus.DRAFT
            )
            
            db.session.add(course)
            db.session.commit()
            
            return InstructorService._format_instructor_course_details(course)
            
        except BusinessLogicException:
            raise
        except Exception as e:
            db.session.rollback()
            raise BusinessLogicException(f"Failed to create course: {str(e)}")
    
    @staticmethod
    def get_instructor_course_details(instructor_id: int, course_id: int) -> Dict:
        """
        Get detailed course information for instructor
        """
        try:
            course = Course.query.filter_by(id=course_id, instructor_id=instructor_id).first()
            if not course:
                raise ValidationException("Course not found")
            
            return InstructorService._format_instructor_course_details(course)
            
        except ValidationException:
            raise
        except Exception as e:
            raise BusinessLogicException(f"Failed to retrieve course: {str(e)}")
    
    @staticmethod
    def update_course(instructor_id: int, course_id: int, **kwargs) -> Dict:
        """
        Update course for instructor
        """
        try:
            course = Course.query.filter_by(id=course_id, instructor_id=instructor_id).first()
            if not course:
                raise ValidationException("Course not found")
            
            # Update fields
            for field, value in kwargs.items():
                if field == 'difficulty_level' and value:
                    if value == 'beginner':
                        course.difficulty_level = DifficultyLevel.BEGINNER
                    elif value == 'intermediate':
                        course.difficulty_level = DifficultyLevel.INTERMEDIATE
                    elif value == 'advanced':
                        course.difficulty_level = DifficultyLevel.ADVANCED
                elif field == 'title' and value:
                    course.title = value
                    # Regenerate slug if title changed
                    course.slug = InstructorService._generate_slug(value)
                elif hasattr(course, field) and value is not None:
                    setattr(course, field, value)
            
            course.updated_at = datetime.utcnow()
            db.session.commit()
            
            return InstructorService._format_instructor_course_details(course)
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise BusinessLogicException(f"Failed to update course: {str(e)}")
    
    @staticmethod
    def publish_course(instructor_id: int, course_id: int) -> Dict:
        """
        Publish a course
        """
        try:
            course = Course.query.filter_by(id=course_id, instructor_id=instructor_id).first()
            if not course:
                raise ValidationException("Course not found")
            
            if course.status == CourseStatus.PUBLISHED:
                raise BusinessLogicException("Course is already published")
            
            # Validate course can be published (has minimum required content)
            if not course.title or not course.short_description:
                raise BusinessLogicException("Course must have title and description before publishing")
            
            course.status = CourseStatus.PUBLISHED
            course.is_published = True
            course.published_at = datetime.utcnow()
            course.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'id': course.id,
                'status': course.status.value,
                'published_at': course.published_at.isoformat() + 'Z',
                'public_url': f"/courses/{course.slug}"  # This should be configurable
            }
            
        except (ValidationException, BusinessLogicException):
            raise
        except Exception as e:
            db.session.rollback()
            raise BusinessLogicException(f"Failed to publish course: {str(e)}")
    
    @staticmethod
    def unpublish_course(instructor_id: int, course_id: int) -> Dict:
        """
        Unpublish a course
        """
        try:
            course = Course.query.filter_by(id=course_id, instructor_id=instructor_id).first()
            if not course:
                raise ValidationException("Course not found")
            
            if course.status != CourseStatus.PUBLISHED:
                raise BusinessLogicException("Course is not published")
            
            course.status = CourseStatus.DRAFT
            course.is_published = False
            course.published_at = None
            course.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'id': course.id,
                'status': course.status.value,
                'published_at': None
            }
            
        except (ValidationException, BusinessLogicException):
            raise
        except Exception as e:
            db.session.rollback()
            raise BusinessLogicException(f"Failed to unpublish course: {str(e)}")
    
    @staticmethod
    def delete_course(instructor_id: int, course_id: int) -> None:
        """
        Delete a course (soft delete)
        """
        try:
            course = Course.query.filter_by(id=course_id, instructor_id=instructor_id).first()
            if not course:
                raise ValidationException("Course not found")
            
            # Check if course has enrollments
            if course.total_enrollments > 0:
                raise BusinessLogicException("Cannot delete course with existing enrollments")
            
            db.session.delete(course)
            db.session.commit()
            
        except (ValidationException, BusinessLogicException):
            raise
        except Exception as e:
            db.session.rollback()
            raise BusinessLogicException(f"Failed to delete course: {str(e)}")
    
    @staticmethod
    def _format_instructor_course(course: Course) -> Dict:
        """Format course for instructor course list"""
        return {
            'id': course.id,
            'title': course.title,
            'short_description': course.short_description,
            'slug': course.slug,
            'status': course.status.value,
            'language': course.language,
            'difficulty_level': course.difficulty_level.value,
            'category': {
                'id': course.category_id,
                'name': course.category.name if course.category else None,
                'slug': course.category.slug if course.category else None
            } if course.category_id else None,
            'price': {
                'amount': float(course.price),
                'is_free': course.is_free,
                'currency': 'VND'
            },
            'thumbnail_url': course.thumbnail_url,
            'stats': {
                'total_enrollments': course.total_enrollments,
                'total_lessons': course.total_lessons,
                'duration_hours': course.duration_hours or 0
            },
            'created_at': course.created_at.isoformat() + 'Z' if course.created_at else None,
            'updated_at': course.updated_at.isoformat() + 'Z' if course.updated_at else None,
            'published_at': course.published_at.isoformat() + 'Z' if course.published_at else None
        }
    
    @staticmethod
    def _format_instructor_course_details(course: Course) -> Dict:
        """Format detailed course information for instructor"""
        formatted = InstructorService._format_instructor_course(course)
        
        # Add additional fields for detailed view
        formatted.update({
            'description': course.description,
            'preview_video_url': course.preview_video_url,
            'requirements': [],  # TODO: Parse from JSON field or related table
            'what_you_will_learn': [],  # TODO: Parse from JSON field or related table
            'tags': []  # TODO: Parse from tags field
        })
        
        return formatted
    
    @staticmethod
    def _generate_slug(title: str) -> str:
        """Generate URL-friendly slug from title"""
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        # Ensure maximum length
        if len(slug) > 50:
            slug = slug[:50].rstrip('-')
        
        return slug
