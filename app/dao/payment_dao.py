"""
Payment DAO (Data Access Object)
Provides data access methods for payment operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, desc
from app.dao.base_dao import BaseDAO
from app.models.payment import Payment, PaymentStatus, PaymentMethod, Transaction
from app.models.enrollment import Enrollment
from app import db


class PaymentDAO(BaseDAO):
    """
    DAO class for payment operations
    Extends BaseDAO with payment-specific methods
    """
    
    def __init__(self):
        super().__init__(Payment)
    
    def get_by_id(self, payment_id: str) -> Optional[Payment]:
        """
        Get payment by UUID string ID
        
        Args:
            payment_id: UUID string of payment
            
        Returns:
            Optional[Payment]: Payment instance or None
        """
        try:
            return self.session.query(Payment).filter(
                Payment.id == payment_id
            ).first()
        except SQLAlchemyError as e:
            raise e
    
    def get_by_enrollment(self, enrollment_id: str) -> List[Payment]:
        """
        Get all payments for an enrollment
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            List[Payment]: List of payments
        """
        try:
            return self.session.query(Payment).filter(
                Payment.enrollment_id == enrollment_id
            ).order_by(desc(Payment.created_at)).all()
        except SQLAlchemyError as e:
            raise e
    
    def get_latest_payment(self, enrollment_id: str) -> Optional[Payment]:
        """
        Get the latest payment for an enrollment
        
        Args:
            enrollment_id: Enrollment ID
            
        Returns:
            Optional[Payment]: Latest payment or None
        """
        try:
            return self.session.query(Payment).filter(
                Payment.enrollment_id == enrollment_id
            ).order_by(desc(Payment.created_at)).first()
        except SQLAlchemyError as e:
            raise e
    
    def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """
        Get payment by transaction ID
        
        Args:
            transaction_id: Transaction ID from payment gateway
            
        Returns:
            Optional[Payment]: Payment instance or None
        """
        try:
            return self.session.query(Payment).filter(
                Payment.transaction_id == transaction_id
            ).first()
        except SQLAlchemyError as e:
            raise e
    
    def get_user_payments(self, user_id: int, status_filter: Optional[str] = None,
                         page: int = 1, limit: int = 10) -> tuple[List[Payment], int]:
        """
        Get user's payments with pagination and optional status filter
        
        Args:
            user_id: User ID
            status_filter: Optional payment status filter
            page: Page number (1-based)
            limit: Number of items per page
            
        Returns:
            tuple[List[Payment], int]: (payments list, total count)
        """
        try:
            query = self.session.query(Payment).filter(
                Payment.user_id == user_id
            ).options(
                joinedload(Payment.enrollment),
                joinedload(Payment.user)
            )
            
            # Apply status filter if provided
            if status_filter:
                try:
                    status_enum = PaymentStatus(status_filter)
                    query = query.filter(Payment.status == status_enum)
                except ValueError:
                    # Invalid status, return empty result
                    return [], 0
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            payments = query.order_by(desc(Payment.created_at)).offset(offset).limit(limit).all()
            
            return payments, total_count
        except SQLAlchemyError as e:
            raise e
    
    def get_payments_by_status(self, status: PaymentStatus,
                              limit: Optional[int] = None) -> List[Payment]:
        """
        Get payments by status
        
        Args:
            status: Payment status
            limit: Optional limit for results
            
        Returns:
            List[Payment]: List of payments
        """
        try:
            query = self.session.query(Payment).filter(
                Payment.status == status
            ).options(
                joinedload(Payment.enrollment),
                joinedload(Payment.user)
            )
            
            if limit:
                query = query.limit(limit)
                
            return query.order_by(desc(Payment.created_at)).all()
        except SQLAlchemyError as e:
            raise e
    
    def create_payment(self, enrollment_id: str, user_id: int, payment_method: PaymentMethod,
                      amount: float, **kwargs) -> Payment:
        """
        Create new payment
        
        Args:
            enrollment_id: Enrollment ID
            user_id: User ID
            payment_method: Payment method
            amount: Payment amount
            **kwargs: Additional payment data
            
        Returns:
            Payment: Created payment instance
            
        Raises:
            SQLAlchemyError: Database error
        """
        try:
            payment = Payment(
                enrollment_id=enrollment_id,
                user_id=user_id,
                payment_method=payment_method,
                amount=amount,
                **kwargs
            )
            
            self.session.add(payment)
            self.session.commit()
            return payment
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def update_payment_status(self, payment_id: str, status: PaymentStatus,
                            transaction_id: Optional[str] = None,
                            gateway_response: Optional[str] = None,
                            error_code: Optional[str] = None,
                            error_message: Optional[str] = None) -> Optional[Payment]:
        """
        Update payment status
        
        Args:
            payment_id: Payment ID
            status: New payment status
            transaction_id: Optional transaction ID
            gateway_response: Optional gateway response
            error_code: Optional error code
            error_message: Optional error message
            
        Returns:
            Optional[Payment]: Updated payment or None
        """
        try:
            payment = self.get_by_id(payment_id)
            if not payment:
                return None
            
            if status == PaymentStatus.COMPLETED:
                payment.mark_completed(transaction_id, gateway_response)
            elif status == PaymentStatus.FAILED:
                payment.mark_failed(error_code, error_message, gateway_response)
            elif status == PaymentStatus.CANCELLED:
                payment.mark_cancelled()
            else:
                payment.status = status
                if transaction_id:
                    payment.transaction_id = transaction_id
                if gateway_response:
                    payment.gateway_response = gateway_response
                    
            self.session.commit()
            return payment
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def set_payment_details(self, payment_id: str, payment_details: Dict[str, Any]) -> Optional[Payment]:
        """
        Set payment method specific details
        
        Args:
            payment_id: Payment ID
            payment_details: Payment details dictionary
            
        Returns:
            Optional[Payment]: Updated payment or None
        """
        try:
            payment = self.get_by_id(payment_id)
            if not payment:
                return None
            
            payment.set_payment_details(payment_details)
            self.session.commit()
            return payment
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def search_payments(self, user_id: Optional[int] = None,
                       enrollment_id: Optional[str] = None,
                       status: Optional[str] = None,
                       payment_method: Optional[str] = None,
                       transaction_id: Optional[str] = None,
                       page: int = 1, limit: int = 10) -> tuple[List[Payment], int]:
        """
        Search payments with multiple filters
        
        Args:
            user_id: Optional user ID filter
            enrollment_id: Optional enrollment ID filter
            status: Optional status filter
            payment_method: Optional payment method filter
            transaction_id: Optional transaction ID filter
            page: Page number
            limit: Items per page
            
        Returns:
            tuple[List[Payment], int]: (payments, total_count)
        """
        try:
            query = self.session.query(Payment).options(
                joinedload(Payment.enrollment),
                joinedload(Payment.user)
            )
            
            # Apply filters
            if user_id:
                query = query.filter(Payment.user_id == user_id)
            if enrollment_id:
                query = query.filter(Payment.enrollment_id == enrollment_id)
            if status:
                try:
                    status_enum = PaymentStatus(status)
                    query = query.filter(Payment.status == status_enum)
                except ValueError:
                    return [], 0
            if payment_method:
                try:
                    method_enum = PaymentMethod(payment_method)
                    query = query.filter(Payment.payment_method == method_enum)
                except ValueError:
                    return [], 0
            if transaction_id:
                query = query.filter(Payment.transaction_id.ilike(f"%{transaction_id}%"))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            payments = query.order_by(desc(Payment.created_at)).offset(offset).limit(limit).all()
            
            return payments, total_count
            
        except SQLAlchemyError as e:
            raise e
    
    def get_payment_statistics(self, user_id: Optional[int] = None,
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get payment statistics
        
        Args:
            user_id: Optional user ID filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dict[str, Any]: Payment statistics
        """
        try:
            query = self.session.query(Payment)
            
            # Apply filters
            if user_id:
                query = query.filter(Payment.user_id == user_id)
            if start_date:
                query = query.filter(Payment.created_at >= start_date)
            if end_date:
                query = query.filter(Payment.created_at <= end_date)
            
            # Calculate statistics
            total_payments = query.count()
            completed_payments = query.filter(Payment.status == PaymentStatus.COMPLETED).count()
            failed_payments = query.filter(Payment.status == PaymentStatus.FAILED).count()
            pending_payments = query.filter(Payment.status == PaymentStatus.PENDING).count()
            
            # Calculate total amounts
            completed_query = query.filter(Payment.status == PaymentStatus.COMPLETED)
            total_amount = completed_query.with_entities(db.func.sum(Payment.amount)).scalar() or 0
            
            return {
                'total_payments': total_payments,
                'completed_payments': completed_payments,
                'failed_payments': failed_payments,
                'pending_payments': pending_payments,
                'success_rate': (completed_payments / total_payments * 100) if total_payments > 0 else 0,
                'total_amount': float(total_amount),
                'average_amount': float(total_amount / completed_payments) if completed_payments > 0 else 0
            }
            
        except SQLAlchemyError as e:
            raise e


class TransactionDAO(BaseDAO):
    """
    DAO class for transaction operations
    """
    
    def __init__(self):
        super().__init__(Transaction)
    
    def get_by_payment(self, payment_id: str) -> List[Transaction]:
        """
        Get all transactions for a payment
        
        Args:
            payment_id: Payment ID
            
        Returns:
            List[Transaction]: List of transactions
        """
        try:
            return self.session.query(Transaction).filter(
                Transaction.payment_id == payment_id
            ).order_by(desc(Transaction.created_at)).all()
        except SQLAlchemyError as e:
            raise e
    
    def create_transaction(self, payment_id: str, transaction_type: str,
                          amount: float, **kwargs) -> Transaction:
        """
        Create new transaction
        
        Args:
            payment_id: Payment ID
            transaction_type: Type of transaction
            amount: Transaction amount
            **kwargs: Additional transaction data
            
        Returns:
            Transaction: Created transaction instance
        """
        try:
            transaction = Transaction(
                payment_id=payment_id,
                transaction_type=transaction_type,
                amount=amount,
                **kwargs
            )
            
            self.session.add(transaction)
            self.session.commit()
            return transaction
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
