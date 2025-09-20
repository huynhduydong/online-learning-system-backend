"""
Course Service
Business logic for course catalog browsing and management
"""

from decimal import Decimal
from app.dao.course_dao import CourseDAO, CategoryDAO
from app.models.course import DifficultyLevel, CourseStatus
from app.exceptions.base import ValidationException
from app import db

class CourseService:
    
    @staticmethod
    def get_course_catalog(page=1, per_page=12, filters=None, sort_by='newest'):
        """
        Get course catalog with filtering, sorting, and pagination
        
        Args:
            page (int): Page number (1-based)
            per_page (int): Number of courses per page (max 50)
            filters (dict): Filter criteria
            sort_by (str): Sort criteria
        
        Returns:
            dict: Course catalog data with pagination info
        """
        try:
            # Validate pagination parameters
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Validate and process filters
            processed_filters = CourseService._process_filters(filters or {})
            
            # Validate sort parameter
            valid_sorts = ['newest', 'oldest', 'popularity', 'price_low', 'price_high', 'rating', 'title']
            if sort_by not in valid_sorts:
                sort_by = 'newest'
            
            # Get courses from DAO
            result = CourseDAO.get_published_courses(
                page=page,
                per_page=per_page,
                filters=processed_filters,
                sort_by=sort_by
            )
            
            # Format course data for response
            formatted_courses = []
            for course in result['courses']:
                formatted_courses.append(CourseService._format_course_for_catalog(course))
            
            return {
                'success': True,
                'data': {
                    'courses': formatted_courses,
                    'pagination': {
                        'total': result['total'],
                        'pages': result['pages'],
                        'current_page': result['current_page'],
                        'per_page': result['per_page'],
                        'has_next': result['has_next'],
                        'has_prev': result['has_prev'],
                        'next_page': result['next_page'],
                        'prev_page': result['prev_page']
                    },
                    'filters_applied': processed_filters,
                    'sort_by': sort_by
                }
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy danh mục khóa học: {str(e)}")
    
    @staticmethod
    def _process_filters(filters):
        """Process and validate filter parameters"""
        processed = {}
        
        # Category filter
        if filters.get('category_id'):
            try:
                processed['category_id'] = int(filters['category_id'])
            except (ValueError, TypeError):
                raise ValidationException("ID danh mục không hợp lệ")
        
        # Price range filters
        if filters.get('min_price') is not None:
            try:
                min_price = Decimal(str(filters['min_price']))
                if min_price < 0:
                    raise ValidationException("Giá tối thiểu không thể âm")
                processed['min_price'] = min_price
            except (ValueError, TypeError):
                raise ValidationException("Giá tối thiểu không hợp lệ")
        
        if filters.get('max_price') is not None:
            try:
                max_price = Decimal(str(filters['max_price']))
                if max_price < 0:
                    raise ValidationException("Giá tối đa không thể âm")
                processed['max_price'] = max_price
            except (ValueError, TypeError):
                raise ValidationException("Giá tối đa không hợp lệ")
        
        # Validate price range
        if processed.get('min_price') and processed.get('max_price'):
            if processed['min_price'] > processed['max_price']:
                raise ValidationException("Giá tối thiểu không thể lớn hơn giá tối đa")
        
        # Free courses filter
        if filters.get('is_free'):
            processed['is_free'] = bool(filters['is_free'])
        
        # Difficulty level filter
        if filters.get('difficulty_level'):
            difficulty = filters['difficulty_level']
            if isinstance(difficulty, list):
                valid_levels = []
                for level in difficulty:
                    if level in [e.value for e in DifficultyLevel]:
                        valid_levels.append(DifficultyLevel(level))
                if valid_levels:
                    processed['difficulty_level'] = valid_levels
            else:
                if difficulty in [e.value for e in DifficultyLevel]:
                    processed['difficulty_level'] = DifficultyLevel(difficulty)
        
        # Rating filter
        if filters.get('min_rating'):
            try:
                min_rating = float(filters['min_rating'])
                if 1 <= min_rating <= 5:
                    processed['min_rating'] = min_rating
                else:
                    raise ValidationException("Đánh giá tối thiểu phải từ 1 đến 5")
            except (ValueError, TypeError):
                raise ValidationException("Đánh giá tối thiểu không hợp lệ")
        
        # Instructor filter
        if filters.get('instructor_id'):
            try:
                processed['instructor_id'] = int(filters['instructor_id'])
            except (ValueError, TypeError):
                raise ValidationException("ID giảng viên không hợp lệ")
        
        # Search filter
        if filters.get('search'):
            search_term = str(filters['search']).strip()
            if len(search_term) >= 2:  # Minimum search length
                processed['search'] = search_term
        
        # Language filter
        if filters.get('language'):
            processed['language'] = str(filters['language']).strip()
        
        return processed
    
    @staticmethod
    def _format_course_for_catalog(course):
        """Format course data for catalog display"""
        return {
            'id': course.id,
            'title': course.title,
            'short_description': course.short_description,
            'slug': course.slug,
            'instructor': {
                'id': course.instructor_id,
                'name': course.instructor_name or (course.instructor.full_name if course.instructor else 'Unknown')
            },
            'category': {
                'id': course.category_id,
                'name': course.category.name if course.category else 'Uncategorized'
            },
            'price': {
                'amount': float(course.price),
                'display': course.display_price,
                'is_free': course.is_free,
                'original_price': float(course.original_price) if course.original_price else None
            },
            'rating': {
                'average': course.display_rating,
                'total_ratings': course.total_ratings,
                'has_enough_ratings': course.has_enough_ratings
            },
            'stats': {
                'total_enrollments': course.total_enrollments,
                'duration_hours': course.duration_hours,
                'total_lessons': course.total_lessons
            },
            'difficulty_level': course.difficulty_level.value if course.difficulty_level else 'beginner',
            'thumbnail_url': course.thumbnail_url,
            'language': course.language,
            'published_at': course.published_at.isoformat() if course.published_at else None
        }
    
    @staticmethod
    def get_course_by_slug(slug):
        """Get detailed course information by slug"""
        try:
            course = CourseDAO.get_course_by_slug(slug)
            if not course:
                raise ValidationException("Không tìm thấy khóa học")
            
            return {
                'success': True,
                'data': CourseService._format_course_details(course)
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy thông tin khóa học: {str(e)}")
    
    @staticmethod
    def _format_course_details(course):
        """Format detailed course information"""
        return {
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'short_description': course.short_description,
            'slug': course.slug,
            'instructor': {
                'id': course.instructor_id,
                'name': course.instructor_name or (course.instructor.full_name if course.instructor else 'Unknown'),
                'email': course.instructor.email if course.instructor else None
            },
            'category': {
                'id': course.category_id,
                'name': course.category.name if course.category else 'Uncategorized',
                'slug': course.category.slug if course.category else None
            },
            'price': {
                'amount': float(course.price),
                'display': course.display_price,
                'is_free': course.is_free,
                'original_price': float(course.original_price) if course.original_price else None
            },
            'rating': {
                'average': course.display_rating,
                'total_ratings': course.total_ratings,
                'has_enough_ratings': course.has_enough_ratings
            },
            'stats': {
                'total_enrollments': course.total_enrollments,
                'duration_hours': course.duration_hours,
                'total_lessons': course.total_lessons
            },
            'difficulty_level': course.difficulty_level.value if course.difficulty_level else 'beginner',
            'thumbnail_url': course.thumbnail_url,
            'preview_video_url': course.preview_video_url,
            'language': course.language,
            'tags': course.tags,
            'published_at': course.published_at.isoformat() if course.published_at else None,
            'created_at': course.created_at.isoformat(),
            'updated_at': course.updated_at.isoformat()
        }
    
    @staticmethod
    def get_categories():
        """Get all active categories"""
        try:
            categories = CategoryDAO.get_active_categories()
            
            formatted_categories = []
            for category in categories:
                formatted_categories.append({
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'icon': category.icon
                })
            
            return {
                'success': True,
                'data': formatted_categories
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy danh sách danh mục: {str(e)}")
    
    @staticmethod
    def get_categories_with_course_count():
        """Get categories with course count"""
        try:
            categories_with_count = CategoryDAO.get_categories_with_course_count()
            
            formatted_categories = []
            for category, course_count in categories_with_count:
                formatted_categories.append({
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'icon': category.icon,
                    'course_count': course_count
                })
            
            return {
                'success': True,
                'data': formatted_categories
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy danh mục với số lượng khóa học: {str(e)}")
    
    @staticmethod
    def get_popular_courses(limit=10):
        """Get popular courses"""
        try:
            courses = CourseDAO.get_popular_courses(limit)
            
            formatted_courses = []
            for course in courses:
                formatted_courses.append(CourseService._format_course_for_catalog(course))
            
            return {
                'success': True,
                'data': formatted_courses
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy khóa học phổ biến: {str(e)}")
    
    @staticmethod
    def get_top_rated_courses(limit=10):
        """Get top rated courses"""
        try:
            courses = CourseDAO.get_top_rated_courses(limit)
            
            formatted_courses = []
            for course in courses:
                formatted_courses.append(CourseService._format_course_for_catalog(course))
            
            return {
                'success': True,
                'data': formatted_courses
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy khóa học đánh giá cao: {str(e)}")
    
    @staticmethod
    def get_free_courses(limit=10):
        """Get free courses"""
        try:
            courses = CourseDAO.get_free_courses(limit)
            
            formatted_courses = []
            for course in courses:
                formatted_courses.append(CourseService._format_course_for_catalog(course))
            
            return {
                'success': True,
                'data': formatted_courses
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy khóa học miễn phí: {str(e)}")
    
    @staticmethod
    def search_courses(search_term, page=1, per_page=12):
        """Search courses"""
        try:
            if not search_term or len(search_term.strip()) < 2:
                raise ValidationException("Từ khóa tìm kiếm phải có ít nhất 2 ký tự")
            
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            result = CourseDAO.search_courses(search_term.strip(), page, per_page)
            
            formatted_courses = []
            for course in result['courses']:
                formatted_courses.append(CourseService._format_course_for_catalog(course))
            
            return {
                'success': True,
                'data': {
                    'courses': formatted_courses,
                    'pagination': {
                        'total': result['total'],
                        'pages': result['pages'],
                        'current_page': result['current_page'],
                        'per_page': result['per_page'],
                        'has_next': result['has_next'],
                        'has_prev': result['has_prev']
                    },
                    'search_term': result['search_term']
                }
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi tìm kiếm khóa học: {str(e)}")
    
    @staticmethod
    def get_course_statistics():
        """Get course catalog statistics"""
        try:
            stats = CourseDAO.get_course_statistics()
            
            return {
                'success': True,
                'data': stats
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy thống kê khóa học: {str(e)}")
    
    @staticmethod
    def get_filter_options():
        """Get available filter options for the catalog"""
        try:
            # Get categories
            categories = CategoryDAO.get_active_categories()
            
            # Get difficulty levels
            difficulty_levels = [
                {'value': level.value, 'label': level.value.title()}
                for level in DifficultyLevel
            ]
            
            # Get price ranges (predefined)
            price_ranges = [
                {'label': 'Miễn phí', 'min': 0, 'max': 0, 'is_free': True},
                {'label': 'Dưới 500k', 'min': 0, 'max': 500000},
                {'label': '500k - 1tr', 'min': 500000, 'max': 1000000},
                {'label': '1tr - 2tr', 'min': 1000000, 'max': 2000000},
                {'label': 'Trên 2tr', 'min': 2000000, 'max': None}
            ]
            
            # Get rating options
            rating_options = [
                {'label': '4+ sao', 'value': 4},
                {'label': '3+ sao', 'value': 3},
                {'label': '2+ sao', 'value': 2},
                {'label': '1+ sao', 'value': 1}
            ]
            
            # Get sort options
            sort_options = [
                {'value': 'newest', 'label': 'Mới nhất'},
                {'value': 'popularity', 'label': 'Phổ biến nhất'},
                {'value': 'rating', 'label': 'Đánh giá cao nhất'},
                {'value': 'price_low', 'label': 'Giá thấp đến cao'},
                {'value': 'price_high', 'label': 'Giá cao đến thấp'},
                {'value': 'title', 'label': 'Tên A-Z'}
            ]
            
            return {
                'success': True,
                'data': {
                    'categories': [{'id': cat.id, 'name': cat.name, 'slug': cat.slug} for cat in categories],
                    'difficulty_levels': difficulty_levels,
                    'price_ranges': price_ranges,
                    'rating_options': rating_options,
                    'sort_options': sort_options
                }
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy tùy chọn bộ lọc: {str(e)}")