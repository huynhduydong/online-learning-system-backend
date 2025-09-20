"""
Payments Blueprint - Placeholder
Will be implemented in Sprint 3: Enrollment & Payment
"""

from flask import Blueprint

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/health')
def health():
    return {'status': 'Payments blueprint ready for Sprint 3'}