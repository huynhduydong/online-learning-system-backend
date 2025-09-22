"""
Progress Service
Business logic for lesson and course progress tracking
"""

from app.dao.progress_dao import ProgressDAO, CourseProgressDAO
from app.dao.course_dao import CourseDAO
from app.dao.enrollment_dao import EnrollmentDAO
from app.models.course import Course, Module, Lesson
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.exceptions.base import ValidationException
from app import db

class ProgressService:
    
    @staticmethod
    def validate_course_access(user, course_slug):
        """Validate that user has access to the course"""
        # Get course by slug
        course = CourseDAO.get_course_by_slug(course_slug)
        if not course:
            raise ValidationException({"course": ["Không tìm thấy khóa học"]})
        
        # Check if user is enrolled
        enrollment = Enrollment.query.filter_by(
            user_id=user.id,
            course_id=course.id
        ).first()
        
        if not enrollment:
            raise ValidationException({"enrollment": ["Bạn chưa đăng ký khóa học này"]})
        
        # Check if enrollment is active
        if not enrollment.access_granted:
            raise ValidationException({"access": ["Bạn chưa có quyền truy cập khóa học này"]})
        
        return course, enrollment
    
    @staticmethod
    def validate_lesson_access(course, lesson_id):
        """Validate that lesson belongs to the course"""
        lesson = Lesson.query.join(
            Module, Lesson.module_id == Module.id
        ).filter(
            Lesson.id == lesson_id,
            Module.course_id == course.id
        ).first()
        
        if not lesson:
            raise ValidationException({"lesson": ["Không tìm thấy bài học trong khóa học này"]})
        
        return lesson
    
    @staticmethod
    def track_lesson_progress(user, course_slug, lesson_id, watch_time=None, completion_percentage=None):
        """
        Track user progress for a specific lesson
        
        Args:
            user: Current user
            course_slug: Course slug
            lesson_id: Lesson ID
            watch_time: Watch time in seconds
            completion_percentage: Completion percentage (0-100)
        
        Returns:
            dict: Updated lesson progress
        """
        try:
            # Validate access
            course, enrollment = ProgressService.validate_course_access(user, course_slug)
            lesson = ProgressService.validate_lesson_access(course, lesson_id)
            
            # Validate input parameters
            if watch_time is not None:
                if not isinstance(watch_time, (int, float)) or watch_time < 0:
                    raise ValidationException({"watch_time": ["Thời gian xem phải là số dương"]})
            
            if completion_percentage is not None:
                if not isinstance(completion_percentage, (int, float)) or not (0 <= completion_percentage <= 100):
                    raise ValidationException({"completion_percentage": ["Phần trăm hoàn thành phải từ 0 đến 100"]})
            
            # Update lesson progress
            lesson_progress = ProgressDAO.update_lesson_progress(
                user_id=user.id,
                lesson_id=lesson_id,
                course_id=course.id,
                watch_time=watch_time,
                completion_percentage=completion_percentage
            )
            
            # Update course progress
            CourseProgressDAO.update_course_progress(user.id, course.id)
            
            return {
                'success': True,
                'data': lesson_progress.to_dict()
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException({"error": [f"Lỗi khi cập nhật tiến trình: {str(e)}"]})
    
    @staticmethod
    def mark_lesson_complete(user, course_slug, lesson_id):
        """
        Mark a lesson as completed
        
        Args:
            user: Current user
            course_slug: Course slug
            lesson_id: Lesson ID
        
        Returns:
            dict: Updated lesson progress
        """
        try:
            # Validate access
            course, enrollment = ProgressService.validate_course_access(user, course_slug)
            lesson = ProgressService.validate_lesson_access(course, lesson_id)
            
            # Mark lesson as complete
            lesson_progress = ProgressDAO.mark_lesson_complete(
                user_id=user.id,
                lesson_id=lesson_id,
                course_id=course.id
            )
            
            # Update course progress
            CourseProgressDAO.update_course_progress(user.id, course.id)
            
            return {
                'success': True,
                'data': lesson_progress.to_dict()
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException({"error": [f"Lỗi khi đánh dấu hoàn thành: {str(e)}"]})
    
    @staticmethod
    def get_lesson_progress(user, course_slug, lesson_id):
        """
        Get progress for a specific lesson
        
        Args:
            user: Current user
            course_slug: Course slug
            lesson_id: Lesson ID
        
        Returns:
            dict: Lesson progress data
        """
        try:
            # Validate access
            course, enrollment = ProgressService.validate_course_access(user, course_slug)
            lesson = ProgressService.validate_lesson_access(course, lesson_id)
            
            # Get lesson progress
            lesson_progress = ProgressDAO.get_lesson_progress(user.id, lesson_id)
            
            if lesson_progress:
                progress_data = lesson_progress.to_dict()
            else:
                # Return default progress if none exists
                progress_data = {
                    'user_id': user.id,
                    'lesson_id': lesson_id,
                    'course_id': course.id,
                    'status': 'not_started',
                    'watch_time_seconds': 0,
                    'completion_percentage': 0.0,
                    'is_completed': False,
                    'started_at': None,
                    'completed_at': None,
                    'last_accessed_at': None
                }
            
            # Include lesson details
            progress_data['lesson'] = {
                'id': lesson.id,
                'title': lesson.title,
                'description': lesson.description,
                'content_type': lesson.content_type.value,
                'duration_minutes': lesson.duration_minutes,
                'sort_order': lesson.sort_order,
                'is_preview': lesson.is_preview
            }
            
            return {
                'success': True,
                'data': progress_data
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException({"error": [f"Lỗi khi lấy tiến trình bài học: {str(e)}"]})
    
    @staticmethod
    def get_course_progress(user, course_slug):
        """
        Get overall progress for a course
        
        Args:
            user: Current user
            course_slug: Course slug
        
        Returns:
            dict: Course progress data with lesson breakdown
        """
        try:
            # Validate access
            course, enrollment = ProgressService.validate_course_access(user, course_slug)
            
            # Get detailed course progress
            progress_data = CourseProgressDAO.get_course_progress_with_details(user.id, course.id)
            
            if not progress_data:
                # Initialize course progress if none exists
                CourseProgressDAO.update_course_progress(user.id, course.id)
                progress_data = CourseProgressDAO.get_course_progress_with_details(user.id, course.id)
            
            # Add course information
            progress_data['course'] = {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'description': course.description,
                'thumbnail_url': course.thumbnail_url,
                'instructor': {
                    'id': course.instructor_id,
                    'name': course.instructor_name
                }
            }
            
            return {
                'success': True,
                'data': progress_data
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException({"error": [f"Lỗi khi lấy tiến trình khóa học: {str(e)}"]})
    
    @staticmethod
    def get_course_lessons_with_progress(user, course_slug):
        """
        Get all lessons in a course with user progress
        
        Args:
            user: Current user
            course_slug: Course slug
        
        Returns:
            dict: Course with modules and lessons including progress
        """
        try:
            # Validate access
            course, enrollment = ProgressService.validate_course_access(user, course_slug)
            
            # Get course progress details
            progress_data = CourseProgressDAO.get_course_progress_with_details(user.id, course.id)
            
            if not progress_data:
                # Initialize if no progress exists
                CourseProgressDAO.update_course_progress(user.id, course.id)
                progress_data = CourseProgressDAO.get_course_progress_with_details(user.id, course.id)
            
            # Format response
            return {
                'success': True,
                'data': {
                    'course': {
                        'id': course.id,
                        'title': course.title,
                        'slug': course.slug,
                        'description': course.description,
                        'thumbnail_url': course.thumbnail_url,
                        'total_lessons': course.total_lessons,
                        'duration_hours': course.duration_hours,
                        'instructor': {
                            'id': course.instructor_id,
                            'name': course.instructor_name
                        }
                    },
                    'progress': progress_data['course_progress'],
                    'modules': progress_data['modules']
                }
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException({"error": [f"Lỗi khi lấy danh sách bài học: {str(e)}"]})
    
    @staticmethod
    def get_lesson_details_with_progress(user, course_slug, lesson_id):
        """
        Get detailed lesson information with user progress
        
        Args:
            user: Current user
            course_slug: Course slug
            lesson_id: Lesson ID
        
        Returns:
            dict: Detailed lesson data with progress and content
        """
        try:
            # Validate access
            course, enrollment = ProgressService.validate_course_access(user, course_slug)
            lesson = ProgressService.validate_lesson_access(course, lesson_id)
            
            # Get lesson progress
            lesson_progress = ProgressDAO.get_lesson_progress(user.id, lesson_id)
            
            # Get lesson content
            contents = []
            for content in lesson.contents:
                contents.append({
                    'id': content.id,
                    'title': content.title,
                    'content_data': content.content_data,
                    'file_url': content.file_url,
                    'sort_order': content.sort_order
                })
            
            # Format lesson data
            lesson_data = {
                'id': lesson.id,
                'title': lesson.title,
                'description': lesson.description,
                'content_type': lesson.content_type.value,
                'duration_minutes': lesson.duration_minutes,
                'sort_order': lesson.sort_order,
                'is_preview': lesson.is_preview,
                'contents': contents,
                'module': {
                    'id': lesson.module.id,
                    'title': lesson.module.title,
                    'sort_order': lesson.module.sort_order
                },
                'course': {
                    'id': course.id,
                    'title': course.title,
                    'slug': course.slug
                }
            }
            
            # Add progress data
            if lesson_progress:
                lesson_data['progress'] = lesson_progress.to_dict()
            else:
                lesson_data['progress'] = {
                    'status': 'not_started',
                    'watch_time_seconds': 0,
                    'completion_percentage': 0.0,
                    'is_completed': False,
                    'started_at': None,
                    'completed_at': None,
                    'last_accessed_at': None
                }
            
            return {
                'success': True,
                'data': lesson_data
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException({"error": [f"Lỗi khi lấy chi tiết bài học: {str(e)}"]})
