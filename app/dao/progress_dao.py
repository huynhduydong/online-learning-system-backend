"""
Progress Data Access Object
Handles database operations for progress tracking
"""

from sqlalchemy import and_, desc, func
from app.dao.base_dao import BaseDAO
from app.models.progress import LessonProgress, CourseProgress, ProgressStatus
from app.models.course import Course, Module, Lesson
from app.models.enrollment import Enrollment
from app import db

class ProgressDAO(BaseDAO):
    model = LessonProgress
    
    @classmethod
    def get_lesson_progress(cls, user_id, lesson_id):
        """Get lesson progress for a specific user and lesson"""
        return cls.model.query.filter_by(
            user_id=user_id,
            lesson_id=lesson_id
        ).first()
    
    @classmethod
    def get_or_create_lesson_progress(cls, user_id, lesson_id, course_id):
        """Get existing lesson progress or create new one"""
        progress = cls.get_lesson_progress(user_id, lesson_id)
        
        if not progress:
            progress = cls.model(
                user_id=user_id,
                lesson_id=lesson_id,
                course_id=course_id
            )
            db.session.add(progress)
            db.session.flush()  # Get the ID without committing
        
        return progress
    
    @classmethod
    def update_lesson_progress(cls, user_id, lesson_id, course_id, watch_time=None, completion_percentage=None):
        """Update lesson progress with watch time or completion"""
        progress = cls.get_or_create_lesson_progress(user_id, lesson_id, course_id)
        progress.update_progress(watch_time=watch_time, completion_percentage=completion_percentage)
        
        db.session.commit()
        return progress
    
    @classmethod
    def mark_lesson_complete(cls, user_id, lesson_id, course_id):
        """Mark a lesson as completed"""
        progress = cls.get_or_create_lesson_progress(user_id, lesson_id, course_id)
        progress.mark_completed()
        
        db.session.commit()
        return progress
    
    @classmethod
    def get_course_lesson_progress(cls, user_id, course_id):
        """Get all lesson progress for a user in a specific course"""
        return cls.model.query.filter_by(
            user_id=user_id,
            course_id=course_id
        ).all()
    
    @classmethod
    def get_course_progress_summary(cls, user_id, course_id):
        """Get progress summary for a course"""
        # Get lesson progress stats
        progress_stats = db.session.query(
            func.count(cls.model.id).label('total_started'),
            func.count(cls.model.id).filter(cls.model.is_completed == True).label('total_completed'),
            func.sum(cls.model.watch_time_seconds).label('total_watch_time')
        ).filter_by(
            user_id=user_id,
            course_id=course_id
        ).first()
        
        # Get total lessons in course
        total_lessons = db.session.query(func.count(Lesson.id)).join(
            Module, Lesson.module_id == Module.id
        ).filter(Module.course_id == course_id).scalar() or 0
        
        return {
            'total_lessons': total_lessons,
            'lessons_started': progress_stats.total_started or 0,
            'lessons_completed': progress_stats.total_completed or 0,
            'total_watch_time_seconds': progress_stats.total_watch_time or 0,
            'completion_percentage': (progress_stats.total_completed / total_lessons * 100) if total_lessons > 0 else 0
        }

class CourseProgressDAO(BaseDAO):
    model = CourseProgress
    
    @classmethod
    def get_course_progress(cls, user_id, course_id):
        """Get course progress for a specific user and course"""
        return cls.model.query.filter_by(
            user_id=user_id,
            course_id=course_id
        ).first()
    
    @classmethod
    def get_or_create_course_progress(cls, user_id, course_id, enrollment_id):
        """Get existing course progress or create new one"""
        progress = cls.get_course_progress(user_id, course_id)
        
        if not progress:
            # Get total lessons for this course
            total_lessons = db.session.query(func.count(Lesson.id)).join(
                Module, Lesson.module_id == Module.id
            ).filter(Module.course_id == course_id).scalar() or 0
            
            progress = cls.model(
                user_id=user_id,
                course_id=course_id,
                enrollment_id=enrollment_id,
                total_lessons=total_lessons
            )
            db.session.add(progress)
            db.session.flush()
        
        return progress
    
    @classmethod
    def update_course_progress(cls, user_id, course_id):
        """Update course progress based on lesson progress"""
        # Get enrollment
        enrollment = Enrollment.query.filter_by(
            user_id=user_id,
            course_id=course_id
        ).first()
        
        if not enrollment:
            return None
        
        progress = cls.get_or_create_course_progress(user_id, course_id, enrollment.id)
        progress.update_progress()
        
        db.session.commit()
        return progress
    
    @classmethod
    def get_user_course_progress_list(cls, user_id):
        """Get all course progress for a user"""
        return cls.model.query.filter_by(user_id=user_id).all()
    
    @classmethod
    def get_course_progress_with_details(cls, user_id, course_id):
        """Get detailed course progress including lesson breakdown"""
        course_progress = cls.get_course_progress(user_id, course_id)
        
        if not course_progress:
            return None
        
        # Get lesson progress breakdown by module
        lesson_progress_query = db.session.query(
            Module.id.label('module_id'),
            Module.title.label('module_title'),
            Module.sort_order.label('module_order'),
            Lesson.id.label('lesson_id'),
            Lesson.title.label('lesson_title'),
            Lesson.sort_order.label('lesson_order'),
            Lesson.duration_minutes.label('lesson_duration'),
            Lesson.is_preview.label('is_preview'),
            LessonProgress.status.label('progress_status'),
            LessonProgress.completion_percentage.label('completion_percentage'),
            LessonProgress.watch_time_seconds.label('watch_time_seconds'),
            LessonProgress.is_completed.label('is_completed'),
            LessonProgress.last_accessed_at.label('last_accessed_at')
        ).select_from(Module).join(
            Lesson, Module.id == Lesson.module_id
        ).outerjoin(
            LessonProgress, and_(
                Lesson.id == LessonProgress.lesson_id,
                LessonProgress.user_id == user_id
            )
        ).filter(
            Module.course_id == course_id
        ).order_by(
            Module.sort_order,
            Lesson.sort_order
        ).all()
        
        # Group by modules
        modules = {}
        for row in lesson_progress_query:
            if row.module_id not in modules:
                modules[row.module_id] = {
                    'id': row.module_id,
                    'title': row.module_title,
                    'sort_order': row.module_order,
                    'lessons': []
                }
            
            modules[row.module_id]['lessons'].append({
                'id': row.lesson_id,
                'title': row.lesson_title,
                'sort_order': row.lesson_order,
                'duration_minutes': row.lesson_duration,
                'is_preview': row.is_preview,
                'progress': {
                    'status': row.progress_status.value if row.progress_status else 'not_started',
                    'completion_percentage': row.completion_percentage or 0.0,
                    'watch_time_seconds': row.watch_time_seconds or 0,
                    'is_completed': row.is_completed or False,
                    'last_accessed_at': row.last_accessed_at.isoformat() if row.last_accessed_at else None
                }
            })
        
        # Convert to list and sort
        modules_list = list(modules.values())
        modules_list.sort(key=lambda x: x['sort_order'])
        
        return {
            'course_progress': course_progress.to_dict(),
            'modules': modules_list
        }
