"""
Enrollments Blueprint - Placeholder
Will be implemented in Sprint 3: Enrollment & Payment
"""

from flask import Blueprint

enrollment_router = Blueprint('enrollments', __name__)

@enrollment_router.route('/health')
def health():
    return {'status': 'Enrollments blueprint ready for Sprint 3'}
