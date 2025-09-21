"""
Course Data Access Object
Handles database operations for course catalog browsing
"""

from sqlalchemy import and_, or_, desc, asc, func
from app.dao.base_dao import BaseDAO
from app.models.course import Course, Category, DifficultyLevel, CourseStatus
from app import db

class CourseDAO(BaseDAO):
    model = Course
    
    @classmethod
    def get_published_courses(cls, page=1, per_page=12, filters=None, sort_by='newest'):
        """
        Get published courses with filtering, sorting, and pagination
        
        Args:
            page (int): Page number (1-based)
            per_page (int): Number of courses per page
            filters (dict): Filter criteria
            sort_by (str): Sort criteria ('newest', 'popularity', 'price_low', 'price_high', 'rating')
        
        Returns:
            dict: Paginated course results with metadata
        """
        query = cls.model.query.filter(
            cls.model.is_published == True,
            cls.model.status == CourseStatus.PUBLISHED
        )
        
        # Apply filters
        if filters:
            query = cls._apply_filters(query, filters)
        
        # Apply sorting
        query = cls._apply_sorting(query, sort_by)
        
        # Execute pagination
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'courses': pagination.items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'next_page': pagination.next_num if pagination.has_next else None,
            'prev_page': pagination.prev_num if pagination.has_prev else None
        }
    
    @classmethod
    def _apply_filters(cls, query, filters):
        """Apply various filters to the course query"""
        
        # Category filter
        if filters.get('category_id'):
            query = query.filter(cls.model.category_id == filters['category_id'])
        
        # Price range filter
        if filters.get('min_price') is not None:
            query = query.filter(cls.model.price >= filters['min_price'])
        
        if filters.get('max_price') is not None:
            query = query.filter(cls.model.price <= filters['max_price'])
        
        # Free courses filter
        if filters.get('is_free'):
            query = query.filter(cls.model.is_free == True)
        
        # Difficulty level filter
        if filters.get('difficulty_level'):
            if isinstance(filters['difficulty_level'], list):
                query = query.filter(cls.model.difficulty_level.in_(filters['difficulty_level']))
            else:
                query = query.filter(cls.model.difficulty_level == filters['difficulty_level'])
        
        # Rating filter (minimum rating)
        if filters.get('min_rating'):
            query = query.filter(
                and_(
                    cls.model.total_ratings >= 5,  # Only courses with enough ratings
                    cls.model.average_rating >= filters['min_rating']
                )
            )
        
        # Instructor filter
        if filters.get('instructor_id'):
            query = query.filter(cls.model.instructor_id == filters['instructor_id'])
        
        # Search by title or description
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    cls.model.title.ilike(search_term),
                    cls.model.description.ilike(search_term),
                    cls.model.short_description.ilike(search_term)
                )
            )
        
        # Language filter
        if filters.get('language'):
            query = query.filter(cls.model.language == filters['language'])
        
        return query
    
    @classmethod
    def _apply_sorting(cls, query, sort_by):
        """Apply sorting to the course query"""
        
        if sort_by == 'newest':
            return query.order_by(desc(cls.model.published_at))
        
        elif sort_by == 'oldest':
            return query.order_by(asc(cls.model.published_at))
        
        elif sort_by == 'popularity':
            return query.order_by(desc(cls.model.total_enrollments))
        
        elif sort_by == 'price_low':
            return query.order_by(asc(cls.model.price))
        
        elif sort_by == 'price_high':
            return query.order_by(desc(cls.model.price))
        
        elif sort_by == 'rating':
            # Sort by rating (only courses with enough ratings first)
            return query.order_by(
                desc(cls.model.total_ratings >= 5),
                desc(cls.model.average_rating)
            )
        
        elif sort_by == 'title':
            return query.order_by(asc(cls.model.title))
        
        else:
            # Default to newest
            return query.order_by(desc(cls.model.published_at))
    
    @classmethod
    def get_course_by_slug(cls, slug):
        """Get course by slug"""
        return cls.model.query.filter_by(slug=slug, is_published=True).first()
    
    @classmethod
    def get_courses_by_category(cls, category_id, limit=6):
        """Get courses by category (for related courses)"""
        return cls.model.query.filter(
            cls.model.category_id == category_id,
            cls.model.is_published == True,
            cls.model.status == CourseStatus.PUBLISHED
        ).order_by(desc(cls.model.total_enrollments)).limit(limit).all()
    
    @classmethod
    def get_popular_courses(cls, limit=10):
        """Get most popular courses"""
        return cls.model.query.filter(
            cls.model.is_published == True,
            cls.model.status == CourseStatus.PUBLISHED
        ).order_by(desc(cls.model.total_enrollments)).limit(limit).all()
    
    @classmethod
    def get_top_rated_courses(cls, limit=10):
        """Get top rated courses (with enough ratings)"""
        return cls.model.query.filter(
            cls.model.is_published == True,
            cls.model.status == CourseStatus.PUBLISHED,
            cls.model.total_ratings >= 5
        ).order_by(desc(cls.model.average_rating)).limit(limit).all()
    
    @classmethod
    def get_free_courses(cls, limit=10):
        """Get free courses"""
        return cls.model.query.filter(
            cls.model.is_published == True,
            cls.model.status == CourseStatus.PUBLISHED,
            cls.model.is_free == True
        ).order_by(desc(cls.model.total_enrollments)).limit(limit).all()
    
    @classmethod
    def get_courses_by_instructor(cls, instructor_id, page=1, per_page=12):
        """Get courses by instructor with pagination"""
        pagination = cls.model.query.filter(
            cls.model.instructor_id == instructor_id,
            cls.model.is_published == True,
            cls.model.status == CourseStatus.PUBLISHED
        ).order_by(desc(cls.model.published_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'courses': pagination.items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    
    @classmethod
    def search_courses(cls, search_term, page=1, per_page=12):
        """Search courses by title, description"""
        search_pattern = f"%{search_term}%"
        
        pagination = cls.model.query.filter(
            cls.model.is_published == True,
            cls.model.status == CourseStatus.PUBLISHED,
            or_(
                cls.model.title.ilike(search_pattern),
                cls.model.description.ilike(search_pattern),
                cls.model.short_description.ilike(search_pattern),
                cls.model.instructor_name.ilike(search_pattern)
            )
        ).order_by(desc(cls.model.total_enrollments)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'courses': pagination.items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'search_term': search_term
        }
    
    @classmethod
    def get_course_statistics(cls):
        """Get course catalog statistics"""
        total_courses = cls.model.query.filter(
            cls.model.is_published == True,
            cls.model.status == CourseStatus.PUBLISHED
        ).count()
        
        free_courses = cls.model.query.filter(
            cls.model.is_published == True,
            cls.model.status == CourseStatus.PUBLISHED,
            cls.model.is_free == True
        ).count()
        
        paid_courses = total_courses - free_courses
        
        # Average price of paid courses
        avg_price = db.session.query(func.avg(cls.model.price)).filter(
            cls.model.is_published == True,
            cls.model.status == CourseStatus.PUBLISHED,
            cls.model.is_free == False
        ).scalar() or 0
        
        return {
            'total_courses': total_courses,
            'free_courses': free_courses,
            'paid_courses': paid_courses,
            'average_price': float(avg_price)
        }
    
    @classmethod
    def get_course_with_details(cls, course_id):
        """Get course with all related information"""
        return cls.model.query.options(
            db.joinedload(cls.model.category),
            db.joinedload(cls.model.instructor),
            db.joinedload(cls.model.modules).joinedload('lessons')
        ).filter_by(id=course_id, is_published=True).first()

class CategoryDAO(BaseDAO):
    model = Category
    
    @classmethod
    def get_active_categories(cls):
        """Get all active categories ordered by sort_order"""
        return cls.model.query.filter_by(is_active=True).order_by(
            cls.model.sort_order,
            cls.model.name
        ).all()
    
    @classmethod
    def get_category_by_slug(cls, slug):
        """Get category by slug"""
        return cls.model.query.filter_by(slug=slug, is_active=True).first()
    
    @classmethod
    def get_categories_with_course_count(cls):
        """Get categories with course count"""
        return db.session.query(
            cls.model,
            func.count(Course.id).label('course_count')
        ).outerjoin(Course, and_(
            Course.category_id == cls.model.id,
            Course.is_published == True,
            Course.status == CourseStatus.PUBLISHED
        )).filter(cls.model.is_active == True).group_by(
            cls.model.id
        ).order_by(cls.model.sort_order, cls.model.name).all()