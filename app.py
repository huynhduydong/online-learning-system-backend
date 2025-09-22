"""
Main application entry point
Online Learning System Backend
"""

from app import create_app, db
from app.models import User, Course, Enrollment, Progress, Payment, Question, Answer, LessonProgress, CourseProgress
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask application
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Make database models available in flask shell"""
    return {
        'db': db,
        'User': User,
        'Course': Course,
        'Enrollment': Enrollment,
        'Progress': Progress,
        'LessonProgress': LessonProgress,
        'CourseProgress': CourseProgress,
        'Payment': Payment,
        'Question': Question,
        'Answer': Answer
    }

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
    
    # Run development server
    app.run(
        host=os.environ.get('FLASK_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    )