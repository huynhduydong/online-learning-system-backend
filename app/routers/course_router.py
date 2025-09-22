"""
Course Router
API endpoints for course catalog browsing and management
"""

from flask import Blueprint, request
from app.services.course_service import CourseService
from app.utils.response import success_response, error_response
from app.exceptions.validation_exception import ValidationException

course_router = Blueprint('courses', __name__)

@course_router.route('/catalog', methods=['GET'])
def get_course_catalog():
    """
    Get paginated course catalog with filtering and sorting
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 12, max: 50)
    - category: Filter by category
    - min_price: Minimum price filter
    - max_price: Maximum price filter
    - difficulty: Filter by difficulty level
    - rating: Minimum rating filter
    - sort_by: Sort field (popularity, price, rating, newest)
    - sort_order: Sort order (asc, desc)
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 12)), 50)
        
        filters = {
            'category': request.args.get('category'),
            'min_price': request.args.get('min_price'),
            'max_price': request.args.get('max_price'),
            'difficulty': request.args.get('difficulty'),
            'rating': request.args.get('rating')
        }
        
        sort_by = request.args.get('sort_by', 'popularity')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Get courses from service
        result = CourseService.get_course_catalog(
            page=page,
            per_page=per_page,
            filters=filters,
            sort_by=sort_by
        )
        
        return success_response(result, "Course catalog retrieved successfully")
        
    except ValidationException as e:
        return error_response(str(e))
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/catalog/filters', methods=['GET'])
def get_catalog_filters():
    """Get available filter options for course catalog"""
    try:
        filters = CourseService.get_catalog_filters()
        return success_response(filters, "Catalog filters retrieved successfully")
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/popular', methods=['GET'])
def get_popular_courses():
    """Get popular courses"""
    try:
        limit = min(int(request.args.get('limit', 10)), 20)
        courses = CourseService.get_popular_courses(limit)
        return success_response(courses, "Popular courses retrieved successfully")
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/top-rated', methods=['GET'])
def get_top_rated_courses():
    """Get top-rated courses"""
    try:
        limit = min(int(request.args.get('limit', 10)), 20)
        courses = CourseService.get_top_rated_courses(limit)
        return success_response(courses, "Top-rated courses retrieved successfully")
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/free', methods=['GET'])
def get_free_courses():
    """Get free courses"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 12)), 50)
        
        result = CourseService.get_free_courses(per_page)
        return success_response(result, "Free courses retrieved successfully")
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/search', methods=['GET'])
def search_courses():
    """Search courses by keyword"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return error_response("Search query is required")
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 12)), 50)
        
        result = CourseService.search_courses(query, page, per_page)
        return success_response(result, "Search results retrieved successfully")
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/categories', methods=['GET'])
def get_categories():
    """Get all course categories"""
    try:
        categories_response = CourseService.get_categories()
        categories = categories_response['data']  # Extract actual categories list
        
        # Format response to match requirements
        formatted_categories = []
        for category in categories:
            formatted_categories.append({
                'id': category['id'],
                'name': category['name'],
                'slug': category['slug'],
                'description': category.get('description', '')
            })
        
        return success_response(formatted_categories, "Categories retrieved successfully")
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/categories/with-count', methods=['GET'])
def get_categories_with_count():
    """Get categories with course count"""
    try:
        categories_response = CourseService.get_categories_with_course_count()
        categories = categories_response['data']  # Extract actual categories list
        return success_response(categories, "Categories with count retrieved successfully")
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/categories/<slug>/courses', methods=['GET'])
def get_courses_by_category_slug(slug):
    """
    Get courses by category slug with pagination
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 12, max: 50)
    - sort_by: Sort field (newest, oldest, popularity, price_low, price_high, rating, title)
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 12)), 50)
        sort_by = request.args.get('sort_by', 'newest')
        
        # Get courses from service
        result = CourseService.get_courses_by_category_slug(
            slug=slug,
            page=page,
            per_page=per_page,
            sort_by=sort_by
        )
        
        return success_response(result, "Courses retrieved successfully")
        
    except ValidationException as e:
        return error_response(str(e), 404 if "Không tìm thấy danh mục" in str(e) else 400)
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/<slug>', methods=['GET'])
def get_course_by_slug(slug):
    """Get course details by slug"""
    try:
        course = CourseService.get_course_by_slug(slug)
        if not course:
            return error_response("Course not found")
        
        return success_response(course, "Course details retrieved successfully")
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/<int:course_id>/reviews', methods=['GET'])
def get_course_reviews(course_id):
    """Get reviews for a specific course"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 20)
        
        result = CourseService.get_course_reviews(course_id, page, per_page)
        return success_response(result, "Course reviews retrieved successfully")
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/<int:course_id>/similar', methods=['GET'])
def get_similar_courses(course_id):
    """Get similar courses"""
    try:
        limit = min(int(request.args.get('limit', 6)), 12)
        courses = CourseService.get_similar_courses(course_id, limit)
        return success_response(courses, "Similar courses retrieved successfully")
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/languages', methods=['GET'])
def get_languages():
    """Get supported languages"""
    try:
        # Return hardcoded language list as per requirements
        languages = [
            {"code": "vi", "name": "Vietnamese"},
            {"code": "en", "name": "English"},
            {"code": "zh", "name": "Chinese"}
        ]
        
        return success_response(languages, "Languages retrieved successfully")
    except Exception as e:
        return error_response("Internal server error")

@course_router.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return success_response({"status": "healthy"}, "Course service is running")