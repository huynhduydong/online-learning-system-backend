"""
Courses Blueprint - Placeholder
Will be implemented in Sprint 2: Course Discovery
"""

from flask import Blueprint

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('/health')
def health():
    return {'status': 'Courses blueprint ready for Sprint 2'}