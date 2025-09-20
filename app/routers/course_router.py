"""
Courses Blueprint - Placeholder
Will be implemented in Sprint 2: Course Discovery
"""

from flask import Blueprint

course_router = Blueprint('courses', __name__)

@course_router.route('/health')
def health():
    return {'status': 'Courses blueprint ready for Sprint 2'}