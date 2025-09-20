"""
Flask Application Factory
Hệ thống Học tập Trực tuyến - Online Learning System
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
    default_limits=["200 per day", "50 per hour"]
)


def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    if config_name == 'development':
        from config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    elif config_name == 'production':
        from config import ProductionConfig
        app.config.from_object(ProductionConfig)
    elif config_name == 'testing':
        from config import TestingConfig
        app.config.from_object(TestingConfig)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)
    
    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.users import users_bp
    from app.blueprints.courses import courses_bp
    from app.blueprints.enrollments import enrollments_bp
    from app.blueprints.payments import payments_bp
    from app.blueprints.progress import progress_bp
    from app.blueprints.qa import qa_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(courses_bp, url_prefix='/api/courses')
    app.register_blueprint(enrollments_bp, url_prefix='/api/enrollments')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(qa_bp, url_prefix='/api/qa')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Online Learning System API is running'}
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    return app