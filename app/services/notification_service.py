"""
Notification Service
Business logic for notifications management
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError

from app.dao.notification_dao import NotificationDAO
from app.models.notification import NotificationTemplate
from app.exceptions.base import ValidationException, BusinessLogicException
from app import db


class NotificationService:
    """Service class cho notification operations"""
    
    def __init__(self):
        self.notification_dao = NotificationDAO()
    
    def get_user_notifications(self, user_id, page=1, per_page=20, unread_only=False):
        """
        Lấy danh sách thông báo của user
        
        Args:
            user_id: ID người dùng
            page: Số trang
            per_page: Số thông báo mỗi trang
            unread_only: Chỉ lấy thông báo chưa đọc
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Get notifications from DAO
            result = self.notification_dao.get_user_notifications(
                user_id=user_id,
                page=page,
                per_page=per_page,
                unread_only=unread_only
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy danh sách thông báo: {str(e)}")
    
    def get_notification_by_id(self, notification_id, user_id):
        """
        Lấy chi tiết thông báo theo ID
        
        Args:
            notification_id: ID thông báo
            user_id: ID người dùng (để kiểm tra quyền)
            
        Returns:
            dict: Chi tiết thông báo
        """
        try:
            notification = self.notification_dao.get_notification_by_id(notification_id)
            
            if not notification:
                raise ValidationException("Không tìm thấy thông báo")
            
            # Check permission
            if notification['userId'] != user_id:
                raise ValidationException("Bạn không có quyền xem thông báo này")
            
            return {
                'success': True,
                'data': notification
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy chi tiết thông báo: {str(e)}")
    
    def create_notification(self, user_id, notification_type, title, message, data=None):
        """
        Tạo thông báo mới
        
        Args:
            user_id: ID người nhận
            notification_type: Loại thông báo
            title: Tiêu đề
            message: Nội dung
            data: Dữ liệu bổ sung (JSON)
            
        Returns:
            dict: Thông báo được tạo
        """
        try:
            # Validate notification data
            self._validate_notification_data(notification_type, title, message)
            
            # Create notification
            notification = self.notification_dao.create_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data
            )
            
            return {
                'success': True,
                'data': notification.to_dict(),
                'message': 'Thông báo đã được tạo thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi tạo thông báo: {str(e)}")
    
    def create_bulk_notifications(self, user_ids, notification_type, title, message, data=None):
        """
        Tạo thông báo hàng loạt
        
        Args:
            user_ids: Danh sách ID người nhận
            notification_type: Loại thông báo
            title: Tiêu đề
            message: Nội dung
            data: Dữ liệu bổ sung (JSON)
            
        Returns:
            dict: Kết quả tạo thông báo
        """
        try:
            # Validate notification data
            self._validate_notification_data(notification_type, title, message)
            
            # Validate user IDs
            if not user_ids or not isinstance(user_ids, list):
                raise ValidationException("Danh sách người nhận không hợp lệ")
            
            if len(user_ids) > 1000:
                raise ValidationException("Không thể gửi thông báo cho quá 1000 người cùng lúc")
            
            # Create bulk notifications
            created_count = self.notification_dao.create_bulk_notifications(
                user_ids=user_ids,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data
            )
            
            return {
                'success': True,
                'data': {
                    'createdCount': created_count,
                    'totalUsers': len(user_ids)
                },
                'message': f'Đã tạo {created_count} thông báo'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi tạo thông báo hàng loạt: {str(e)}")
    
    def mark_as_read(self, notification_id, user_id):
        """
        Đánh dấu thông báo đã đọc
        
        Args:
            notification_id: ID thông báo
            user_id: ID người dùng
            
        Returns:
            dict: Kết quả đánh dấu
        """
        try:
            # Check permission
            notification = self.notification_dao.get_notification_by_id(notification_id)
            if not notification:
                raise ValidationException("Không tìm thấy thông báo")
            
            if notification['userId'] != user_id:
                raise ValidationException("Bạn không có quyền thao tác với thông báo này")
            
            # Mark as read
            marked = self.notification_dao.mark_as_read(notification_id, user_id)
            
            if not marked:
                raise ValidationException("Không thể đánh dấu thông báo đã đọc")
            
            return {
                'success': True,
                'message': 'Đã đánh dấu thông báo đã đọc'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi đánh dấu thông báo: {str(e)}")
    
    def mark_all_as_read(self, user_id):
        """
        Đánh dấu tất cả thông báo đã đọc
        
        Args:
            user_id: ID người dùng
            
        Returns:
            dict: Kết quả đánh dấu
        """
        try:
            marked_count = self.notification_dao.mark_all_as_read(user_id)
            
            return {
                'success': True,
                'data': {
                    'markedCount': marked_count
                },
                'message': f'Đã đánh dấu {marked_count} thông báo đã đọc'
            }
            
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi đánh dấu tất cả thông báo: {str(e)}")
    
    def delete_notification(self, notification_id, user_id):
        """
        Xóa thông báo
        
        Args:
            notification_id: ID thông báo
            user_id: ID người dùng
            
        Returns:
            dict: Kết quả xóa
        """
        try:
            # Check permission
            notification = self.notification_dao.get_notification_by_id(notification_id)
            if not notification:
                raise ValidationException("Không tìm thấy thông báo")
            
            if notification['userId'] != user_id:
                raise ValidationException("Bạn không có quyền xóa thông báo này")
            
            # Delete notification
            deleted = self.notification_dao.delete_notification(notification_id, user_id)
            
            if not deleted:
                raise ValidationException("Không thể xóa thông báo")
            
            return {
                'success': True,
                'message': 'Thông báo đã được xóa'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi xóa thông báo: {str(e)}")
    
    def delete_old_notifications(self, days_old=30):
        """
        Xóa thông báo cũ (dùng cho maintenance)
        
        Args:
            days_old: Số ngày cũ (mặc định 30 ngày)
            
        Returns:
            dict: Kết quả xóa
        """
        try:
            deleted_count = self.notification_dao.delete_old_notifications(days_old)
            
            return {
                'success': True,
                'data': {
                    'deletedCount': deleted_count
                },
                'message': f'Đã xóa {deleted_count} thông báo cũ'
            }
            
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi xóa thông báo cũ: {str(e)}")
    
    def get_unread_count(self, user_id):
        """
        Lấy số lượng thông báo chưa đọc
        
        Args:
            user_id: ID người dùng
            
        Returns:
            dict: Số lượng thông báo chưa đọc
        """
        try:
            count = self.notification_dao.get_unread_count(user_id)
            
            return {
                'success': True,
                'data': {
                    'unreadCount': count
                }
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy số thông báo chưa đọc: {str(e)}")
    
    def get_notifications_by_type(self, user_id, notification_type, page=1, per_page=20):
        """
        Lấy thông báo theo loại
        
        Args:
            user_id: ID người dùng
            notification_type: Loại thông báo
            page: Số trang
            per_page: Số thông báo mỗi trang
            
        Returns:
            dict: Danh sách thông báo theo loại
        """
        try:
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Validate notification type
            self._validate_notification_type(notification_type)
            
            result = self.notification_dao.get_notifications_by_type(
                user_id=user_id,
                notification_type=notification_type,
                page=page,
                per_page=per_page
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy thông báo theo loại: {str(e)}")
    
    def get_notification_statistics(self, user_id):
        """
        Lấy thống kê thông báo của user
        
        Args:
            user_id: ID người dùng
            
        Returns:
            dict: Thống kê thông báo
        """
        try:
            stats = self.notification_dao.get_notification_statistics(user_id)
            
            return {
                'success': True,
                'data': stats
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy thống kê thông báo: {str(e)}")
    
    def search_notifications(self, user_id, search_term, page=1, per_page=20):
        """
        Tìm kiếm thông báo
        
        Args:
            user_id: ID người dùng
            search_term: Từ khóa tìm kiếm
            page: Số trang
            per_page: Số thông báo mỗi trang
            
        Returns:
            dict: Kết quả tìm kiếm
        """
        try:
            if not search_term or len(search_term.strip()) < 2:
                raise ValidationException("Từ khóa tìm kiếm phải có ít nhất 2 ký tự")
            
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            result = self.notification_dao.search_notifications(
                user_id=user_id,
                search_term=search_term.strip(),
                page=page,
                per_page=per_page
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi tìm kiếm thông báo: {str(e)}")
    
    def get_recent_notifications(self, user_id, limit=10):
        """
        Lấy thông báo gần đây
        
        Args:
            user_id: ID người dùng
            limit: Số lượng thông báo
            
        Returns:
            dict: Danh sách thông báo gần đây
        """
        try:
            notifications = self.notification_dao.get_recent_notifications(
                user_id=user_id,
                limit=limit
            )
            
            return {
                'success': True,
                'data': [notification.to_dict() for notification in notifications]
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy thông báo gần đây: {str(e)}")
    
    def create_system_notification(self, user_ids, notification_type, template_data=None):
        """
        Tạo thông báo hệ thống từ template
        
        Args:
            user_ids: Danh sách ID người nhận
            notification_type: Loại thông báo
            template_data: Dữ liệu cho template
            
        Returns:
            dict: Kết quả tạo thông báo
        """
        try:
            # Validate notification type
            self._validate_notification_type(notification_type)
            
            # Get notification content from template
            template = NotificationTemplate()
            title, message = template.get_notification_content(notification_type, template_data or {})
            
            # Create bulk notifications
            created_count = self.notification_dao.create_system_notifications(
                user_ids=user_ids,
                notification_type=notification_type,
                title=title,
                message=message,
                data=template_data
            )
            
            return {
                'success': True,
                'data': {
                    'createdCount': created_count,
                    'totalUsers': len(user_ids)
                },
                'message': f'Đã tạo {created_count} thông báo hệ thống'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi tạo thông báo hệ thống: {str(e)}")
    
    # Notification templates for common scenarios
    def notify_question_answered(self, question_author_id, answer_author_name, question_title):
        """Thông báo khi câu hỏi được trả lời"""
        return self.create_system_notification(
            user_ids=[question_author_id],
            notification_type='question_answered',
            template_data={
                'answer_author_name': answer_author_name,
                'question_title': question_title
            }
        )
    
    def notify_answer_accepted(self, answer_author_id, question_title):
        """Thông báo khi câu trả lời được chấp nhận"""
        return self.create_system_notification(
            user_ids=[answer_author_id],
            notification_type='answer_accepted',
            template_data={
                'question_title': question_title
            }
        )
    
    def notify_comment_replied(self, comment_author_id, replier_name, content_title):
        """Thông báo khi comment được reply"""
        return self.create_system_notification(
            user_ids=[comment_author_id],
            notification_type='comment_replied',
            template_data={
                'replier_name': replier_name,
                'content_title': content_title
            }
        )
    
    def notify_vote_received(self, content_author_id, vote_type, content_type, content_title):
        """Thông báo khi nhận được vote"""
        return self.create_system_notification(
            user_ids=[content_author_id],
            notification_type='vote_received',
            template_data={
                'vote_type': vote_type,
                'content_type': content_type,
                'content_title': content_title
            }
        )
    
    def notify_mentioned(self, mentioned_user_id, mentioner_name, content_type, content_title):
        """Thông báo khi được mention"""
        return self.create_system_notification(
            user_ids=[mentioned_user_id],
            notification_type='mentioned',
            template_data={
                'mentioner_name': mentioner_name,
                'content_type': content_type,
                'content_title': content_title
            }
        )
    
    def _validate_notification_data(self, notification_type, title, message):
        """Validate notification data"""
        # Validate type
        self._validate_notification_type(notification_type)
        
        # Validate title
        if not title or not title.strip():
            raise ValidationException("Tiêu đề thông báo không được để trống")
        
        if len(title) > 200:
            raise ValidationException("Tiêu đề thông báo không được quá 200 ký tự")
        
        # Validate message
        if not message or not message.strip():
            raise ValidationException("Nội dung thông báo không được để trống")
        
        if len(message) > 1000:
            raise ValidationException("Nội dung thông báo không được quá 1000 ký tự")
    
    def _validate_notification_type(self, notification_type):
        """Validate notification type"""
        valid_types = [
            'question_answered', 'answer_accepted', 'comment_replied',
            'vote_received', 'mentioned', 'system_announcement',
            'course_update', 'assignment_due', 'grade_released'
        ]
        
        if notification_type not in valid_types:
            raise ValidationException(f"Loại thông báo không hợp lệ: {notification_type}")