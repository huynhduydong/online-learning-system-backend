"""
Payment models for Course Registration Workflow
Implements payment processing and transaction tracking
"""

import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import Numeric
from app import db

class PaymentMethod(Enum):
    CREDIT_CARD = 'credit_card'
    PAYPAL = 'paypal'
    BANK_TRANSFER = 'bank_transfer'

class PaymentStatus(Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'

class Payment(db.Model):
    """
    Payment model for tracking enrollment payments
    
    Business Rules:
    - Each enrollment can have multiple payment attempts
    - Payment details are stored securely (minimal sensitive data)
    - Transaction IDs are provided by payment gateways
    - Failed payments can be retried
    """
    __tablename__ = 'payments'
    
    # Primary key using UUID
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    enrollment_id = db.Column(db.String(36), db.ForeignKey('enrollments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Payment information
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    status = db.Column(db.Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    amount = db.Column(Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='VND')
    
    # Transaction tracking
    transaction_id = db.Column(db.String(255), nullable=True)  # From payment gateway
    gateway_response = db.Column(db.Text, nullable=True)  # JSON response from gateway
    payment_gateway = db.Column(db.String(50), nullable=True)  # stripe, paypal, etc.
    
    # Payment details (stored securely - minimal data only)
    last_four_digits = db.Column(db.String(4), nullable=True)  # For credit cards
    card_holder_name = db.Column(db.String(255), nullable=True)
    paypal_email = db.Column(db.String(255), nullable=True)
    bank_account_last_four = db.Column(db.String(4), nullable=True)
    bank_code = db.Column(db.String(10), nullable=True)
    
    # Error handling
    error_code = db.Column(db.String(50), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrollment = db.relationship('Enrollment', backref='payments')
    user = db.relationship('User', backref='payments')
    
    def __init__(self, enrollment_id, user_id, payment_method, amount, **kwargs):
        """Initialize payment with required fields"""
        self.enrollment_id = enrollment_id
        self.user_id = user_id
        self.payment_method = payment_method
        self.amount = amount
        
        # Set optional fields from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def mark_completed(self, transaction_id, gateway_response=None):
        """Mark payment as completed"""
        self.status = PaymentStatus.COMPLETED
        self.transaction_id = transaction_id
        self.processed_at = datetime.utcnow()
        self.gateway_response = gateway_response
        self.error_code = None
        self.error_message = None
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_code, error_message, gateway_response=None):
        """Mark payment as failed"""
        self.status = PaymentStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.gateway_response = gateway_response
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_cancelled(self):
        """Mark payment as cancelled"""
        self.status = PaymentStatus.CANCELLED
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def set_payment_details(self, payment_details):
        """Set payment method specific details"""
        if self.payment_method == PaymentMethod.CREDIT_CARD:
            self.last_four_digits = payment_details.get('last_four_digits')
            self.card_holder_name = payment_details.get('card_holder_name')
        elif self.payment_method == PaymentMethod.PAYPAL:
            self.paypal_email = payment_details.get('paypal_email')
        elif self.payment_method == PaymentMethod.BANK_TRANSFER:
            self.bank_account_last_four = payment_details.get('bank_account_last_four')
            self.bank_code = payment_details.get('bank_code')
    
    def to_dict(self, include_sensitive=False):
        """Convert payment to dictionary for API responses"""
        data = {
            'id': self.id,
            'enrollment_id': self.enrollment_id,
            'payment_method': self.payment_method.value,
            'status': self.status.value,
            'amount': float(self.amount),
            'currency': self.currency,
            'transaction_id': self.transaction_id,
            'payment_gateway': self.payment_gateway,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
        
        # Include payment method specific details
        if self.payment_method == PaymentMethod.CREDIT_CARD and self.last_four_digits:
            data['payment_details'] = {
                'last_four_digits': self.last_four_digits,
                'payment_gateway': self.payment_gateway
            }
        elif self.payment_method == PaymentMethod.PAYPAL and self.paypal_email:
            data['payment_details'] = {
                'paypal_email': self.paypal_email[:3] + '***' + self.paypal_email[-4:] if not include_sensitive else self.paypal_email
            }
        elif self.payment_method == PaymentMethod.BANK_TRANSFER and self.bank_account_last_four:
            data['payment_details'] = {
                'bank_account_last_four': self.bank_account_last_four,
                'bank_code': self.bank_code
            }
        
        # Include error details if payment failed
        if self.status == PaymentStatus.FAILED:
            data['error'] = {
                'code': self.error_code,
                'message': self.error_message
            }
        
        return data
    
    def __repr__(self):
        return f'<Payment {self.id}: {self.amount} {self.currency} - {self.status.value}>'


class Transaction(db.Model):
    """
    Transaction model for detailed payment tracking and audit trail
    Stores complete transaction history for reporting and reconciliation
    """
    __tablename__ = 'transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = db.Column(db.String(36), db.ForeignKey('payments.id'), nullable=False)
    
    # Transaction details
    transaction_type = db.Column(db.String(50), nullable=False)  # payment, refund, chargeback
    external_transaction_id = db.Column(db.String(255), nullable=True)
    gateway_reference = db.Column(db.String(255), nullable=True)
    
    # Financial details
    amount = db.Column(Numeric(10, 2), nullable=False)
    fee_amount = db.Column(Numeric(10, 2), default=0.00)
    net_amount = db.Column(Numeric(10, 2), nullable=False)
    
    # Status and metadata
    status = db.Column(db.String(50), nullable=False)
    gateway_response = db.Column(db.Text, nullable=True)  # Full gateway response
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    payment = db.relationship('Payment', backref='transactions')
    
    def __init__(self, payment_id, transaction_type, amount, **kwargs):
        """Initialize transaction with required fields"""
        self.payment_id = payment_id
        self.transaction_type = transaction_type
        self.amount = amount
        self.net_amount = amount  # Default, will be updated after fees
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def calculate_net_amount(self):
        """Calculate net amount after fees"""
        self.net_amount = self.amount - self.fee_amount
    
    def to_dict(self):
        """Convert transaction to dictionary for API responses"""
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'transaction_type': self.transaction_type,
            'external_transaction_id': self.external_transaction_id,
            'amount': float(self.amount),
            'fee_amount': float(self.fee_amount),
            'net_amount': float(self.net_amount),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    def __repr__(self):
        return f'<Transaction {self.id}: {self.transaction_type} - {self.amount}>'