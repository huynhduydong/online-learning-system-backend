"""
Enrollments Blueprint - Placeholder
Will be implemented in Sprint 3: Enrollment & Payment
"""

from flask import Blueprint

enrollments_bp = Blueprint('enrollments', __name__)

@enrollments_bp.route('/health')
def health():
    return {'status': 'Enrollments blueprint ready for Sprint 3'}