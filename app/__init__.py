"""
Flask Application Factory
Hệ thống Học tập Trực tuyến - Online Learning System

Implements clean application factory pattern with:
- Modular configuration loading
- Extension initialization
- Blueprint registration
- Middleware setup
- Error handling
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[]
)


def load_config(app, config_name=None):
    """Load configuration based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_mapping = {
        'development': 'config.DevelopmentConfig',
        'production': 'config.ProductionConfig',
        'testing': 'config.TestingConfig'
    }
    
    config_class = config_mapping.get(config_name)
    if config_class:
        app.config.from_object(config_class)
    else:
        # Fallback to development config
        app.config.from_object('config.DevelopmentConfig')


def init_extensions(app):
    """Initialize Flask extensions with app context"""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)


def register_routers(app):
    """Register all application routers"""
    from app.routers.auth_router import auth_router
    from app.routers.user_router import user_router
    from app.routers.course_router import course_router
    from app.routers.instructor_router import instructor_router
    from app.routers.enrollment_router import enrollment_router
    from app.routers.payment_router import payment_router
    from app.routers.progress_router import progress_router
    from app.routers.qa_router import qa_router
    from app.routers.cart_router import cart_router
    
    # Import Q&A and Notification routers
    from app.routers.question_router import question_router
    from app.routers.answer_router import answer_router
    from app.routers.comment_router import comment_router
    from app.routers.vote_router import vote_router
    from app.routers.tag_router import tag_router
    from app.routers.notification_router import notification_router
    
    # Register routers with URL prefixes
    routers = [
        (auth_router, '/api/auth'),
        (user_router, '/api/users'),
        (course_router, '/api/courses'),
        (instructor_router, '/api/instructor'),
        (enrollment_router, '/api/enrollments'),
        (payment_router, '/api/payments'),
        (progress_router, '/api/progress'),
        (qa_router, '/api/qa'),
        (cart_router, '/api/cart'),
        
        # Q&A System routers
        (question_router, '/api/questions'),
        (answer_router, '/api/answers'),
        (comment_router, '/api/comments'),
        (vote_router, '/api/votes'),
        (tag_router, '/api/tags'),
        
        # Notification System router
        (notification_router, '/api/notifications')
    ]
    
    for router, url_prefix in routers:
        app.register_blueprint(router, url_prefix=url_prefix)


def setup_middleware(app):
    """Setup application middleware"""
    
    @app.before_request
    def track_user_activity():
        """Track user activity for session management"""
        from flask import request, jsonify
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from app.models.user import User
        
        # Skip activity tracking for certain endpoints
        skip_endpoints = [
            'auth.login', 'auth.register', 'auth.confirm_email', 
            'auth.resend_confirmation', 'health_check',
            'enrollments.health', 'enrollments.debug_my_courses'
        ]
        
        if request.endpoint in skip_endpoints:
            return
        
        try:
            # Check if request has valid JWT token
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            
            if user_id:
                try:
                    user = User.query.get(int(user_id))
                    if user and user.is_active:
                        # Check if session has expired
                        if user.is_session_expired():
                            return jsonify({
                                'success': False,
                                'error': 'Session expired',
                                'message': 'Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại'
                            }), 401
                        
                        # Update activity timestamp
                        user.update_activity()
                except Exception as db_error:
                    # Log database error but don't crash the request
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Database error in middleware for user {user_id}: {str(db_error)}")
                    # Continue without tracking activity
                    pass
        except Exception as jwt_error:
            # If JWT verification fails, continue without tracking
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"JWT verification failed in middleware: {str(jwt_error)}")
            pass


def setup_error_handlers(app):
    """Setup global error handlers"""
    from app.utils.response import error_response
    
    @app.errorhandler(404)
    def not_found(error):
        return error_response('Resource not found', 404)
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {str(error)}")
        return error_response('Internal server error', 500)
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return error_response('Request entity too large', 413)


def setup_health_check(app):
    """Setup health check endpoint"""
    
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy', 
            'message': 'Online Learning System API is running',
            'version': '1.0.0'
        }


def create_app(config_name=None):
    """
    Application factory pattern
    
    Creates and configures Flask application instance with:
    - Configuration loading
    - Extension initialization
    - Blueprint registration
    - Middleware setup
    - Error handling
    
    Args:
        config_name (str): Configuration environment name
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    load_config(app, config_name)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register routers
    register_routers(app)
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Setup health check
    setup_health_check(app)
    
    return app