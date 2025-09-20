"""
Payments Blueprint - Placeholder
Will be implemented in Sprint 3: Enrollment & Payment
"""

from flask import Blueprint

payment_router = Blueprint('payments', __name__)

@payment_router.route('/health')
def health():
    return {'status': 'Payments blueprint ready for Sprint 3'}
