"""
Notification DAO - Data Access Object cho Notification model
Chịu trách nhiệm tất cả database operations liên quan đến Notification
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, desc, asc, func

from app.dao.base_dao import BaseDAO
from app.models.notification import Notification
from app import db


class NotificationDAO(BaseDAO):
    """
    NotificationDAO class cung cấp các phương thức database operations cho Notification model
    """
    
    def __init__(self):
        super().__init__(Notification)
    
    def get_user_notifications(self, user_id, page=1, per_page=20, unread_only=False):
        """
        Lấy danh sách notification của user
        
        Args:
            user_id: ID người dùng
            page: Số trang
            per_page: Số notification mỗi trang
            unread_only: Chỉ lấy notification chưa đọc
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            query = self.session.query(Notification).filter(
                Notification.user_id == user_id
            )
            
            if unread_only:
                query = query.filter(Notification.is_read == False)
            
            query = query.order_by(desc(Notification.created_at))
            
            total = query.count()
            notifications = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [notification.to_dict() for notification in notifications],
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                }
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_notification_by_id(self, notification_id, user_id=None):
        """
        Lấy notification theo ID
        
        Args:
            notification_id: ID notification
            user_id: ID người dùng (để kiểm tra quyền)
            
        Returns:
            Notification hoặc None
        """
        try:
            query = self.session.query(Notification).filter(Notification.id == notification_id)
            
            if user_id:
                query = query.filter(Notification.user_id == user_id)
            
            return query.first()
        except SQLAlchemyError as e:
            raise e
    
    def create_notification(self, user_id, notification_type, title, message, data=None):
        """
        Tạo notification mới
        
        Args:
            user_id: ID người dùng
            notification_type: Loại notification
            title: Tiêu đề
            message: Nội dung
            data: Dữ liệu bổ sung (JSON)
            
        Returns:
            Notification: Notification được tạo
        """
        try:
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                data=data
            )
            
            self.session.add(notification)
            self.session.commit()
            
            return notification
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def create_bulk_notifications(self, notifications_data):
        """
        Tạo nhiều notification cùng lúc
        
        Args:
            notifications_data: Danh sách dữ liệu notification
            
        Returns:
            List[Notification]: Danh sách notification được tạo
        """
        try:
            notifications = []
            
            for data in notifications_data:
                notification = Notification(
                    user_id=data['user_id'],
                    type=data['type'],
                    title=data['title'],
                    message=data['message'],
                    data=data.get('data')
                )
                notifications.append(notification)
                self.session.add(notification)
            
            self.session.commit()
            return notifications
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def mark_as_read(self, notification_id, user_id):
        """
        Đánh dấu notification đã đọc
        
        Args:
            notification_id: ID notification
            user_id: ID người dùng
            
        Returns:
            bool: True nếu thành công
        """
        try:
            notification = self.session.query(Notification).filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            ).first()
            
            if not notification:
                return False
            
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def mark_all_as_read(self, user_id):
        """
        Đánh dấu tất cả notification của user đã đọc
        
        Args:
            user_id: ID người dùng
            
        Returns:
            int: Số notification được cập nhật
        """
        try:
            updated_count = self.session.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            ).update({
                'is_read': True,
                'read_at': datetime.utcnow()
            })
            
            self.session.commit()
            return updated_count
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def delete_notification(self, notification_id, user_id):
        """
        Xóa notification
        
        Args:
            notification_id: ID notification
            user_id: ID người dùng
            
        Returns:
            bool: True nếu thành công
        """
        try:
            notification = self.session.query(Notification).filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            ).first()
            
            if not notification:
                return False
            
            self.session.delete(notification)
            self.session.commit()
            
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def delete_old_notifications(self, days=30):
        """
        Xóa notification cũ
        
        Args:
            days: Số ngày (xóa notification cũ hơn số ngày này)
            
        Returns:
            int: Số notification được xóa
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted_count = self.session.query(Notification).filter(
                Notification.created_at < cutoff_date
            ).delete()
            
            self.session.commit()
            return deleted_count
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def get_unread_count(self, user_id):
        """
        Lấy số lượng notification chưa đọc
        
        Args:
            user_id: ID người dùng
            
        Returns:
            int: Số notification chưa đọc
        """
        try:
            return self.session.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            ).count()
        except SQLAlchemyError as e:
            raise e
    
    def get_notifications_by_type(self, user_id, notification_type, page=1, per_page=20):
        """
        Lấy notification theo loại
        
        Args:
            user_id: ID người dùng
            notification_type: Loại notification
            page: Số trang
            per_page: Số notification mỗi trang
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            query = self.session.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.type == notification_type
                )
            ).order_by(desc(Notification.created_at))
            
            total = query.count()
            notifications = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [notification.to_dict() for notification in notifications],
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                }
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_notification_statistics(self, user_id):
        """
        Lấy thống kê notification của user
        
        Args:
            user_id: ID người dùng
            
        Returns:
            dict: Thống kê notification
        """
        try:
            total = self.session.query(Notification).filter(
                Notification.user_id == user_id
            ).count()
            
            unread = self.session.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            ).count()
            
            # Thống kê theo loại
            type_stats = self.session.query(
                Notification.type,
                func.count(Notification.id).label('count'),
                func.sum(func.case([(Notification.is_read == False, 1)], else_=0)).label('unread_count')
            ).filter(
                Notification.user_id == user_id
            ).group_by(Notification.type).all()
            
            # Thống kê theo thời gian (7 ngày gần đây)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent = self.session.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.created_at >= seven_days_ago
                )
            ).count()
            
            return {
                'total': total,
                'unread': unread,
                'read': total - unread,
                'recent': recent,
                'byType': [
                    {
                        'type': stat.type,
                        'total': stat.count,
                        'unread': stat.unread_count
                    }
                    for stat in type_stats
                ]
            }
        except SQLAlchemyError as e:
            raise e
    
    def search_notifications(self, user_id, search_term, page=1, per_page=20):
        """
        Tìm kiếm notification
        
        Args:
            user_id: ID người dùng
            search_term: Từ khóa tìm kiếm
            page: Số trang
            per_page: Số notification mỗi trang
            
        Returns:
            dict: Kết quả tìm kiếm
        """
        try:
            search_pattern = f"%{search_term}%"
            
            query = self.session.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    or_(
                        Notification.title.ilike(search_pattern),
                        Notification.message.ilike(search_pattern)
                    )
                )
            ).order_by(desc(Notification.created_at))
            
            total = query.count()
            notifications = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [notification.to_dict() for notification in notifications],
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                },
                'searchTerm': search_term
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_recent_notifications(self, user_id, limit=10):
        """
        Lấy notification gần đây
        
        Args:
            user_id: ID người dùng
            limit: Số lượng notification
            
        Returns:
            List[Notification]: Danh sách notification gần đây
        """
        try:
            return self.session.query(Notification).filter(
                Notification.user_id == user_id
            ).order_by(desc(Notification.created_at)).limit(limit).all()
        except SQLAlchemyError as e:
            raise e
    
    def create_system_notification(self, title, message, notification_type='system', target_users=None):
        """
        Tạo notification hệ thống cho nhiều user
        
        Args:
            title: Tiêu đề
            message: Nội dung
            notification_type: Loại notification
            target_users: Danh sách user ID (None = tất cả user)
            
        Returns:
            int: Số notification được tạo
        """
        try:
            if target_users is None:
                # Lấy tất cả user ID từ database
                from app.models.user import User
                target_users = [user.id for user in self.session.query(User.id).all()]
            
            notifications_data = [
                {
                    'user_id': user_id,
                    'type': notification_type,
                    'title': title,
                    'message': message
                }
                for user_id in target_users
            ]
            
            self.create_bulk_notifications(notifications_data)
            return len(notifications_data)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e