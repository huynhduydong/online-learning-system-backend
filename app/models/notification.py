from datetime import datetime, timedelta
from app import db
import json


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Auto increment ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # question_answered, answer_accepted, etc.
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    data = db.Column(db.JSON)  # JSON data for additional information
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)  # Timestamp when notification was read
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    # Indexes for better performance
    __table_args__ = (
        db.Index('idx_notifications_user_id', 'user_id'),
        db.Index('idx_notifications_type', 'type'),
        db.Index('idx_notifications_is_read', 'is_read'),
        db.Index('idx_notifications_created_at', 'created_at'),
    )
    
    def __init__(self, user_id, type, title, message, data=None, **kwargs):
        self.user_id = user_id
        self.type = type
        self.title = title
        self.message = message
        self.data = data  # JSON data will be handled by SQLAlchemy JSON type
        
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.type}>'
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'userId': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,  # JSON data handled by SQLAlchemy
            'isRead': self.is_read,
            'readAt': self.read_at.isoformat() if self.read_at else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def create_notification(user_id, notification_type, title, message, data=None):
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=data
        )
        
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @staticmethod
    def get_user_notifications(user_id, read=None, notification_type=None, start_date=None, end_date=None, limit=20, offset=0):
        """Get user notifications with filters"""
        query = Notification.query.filter_by(user_id=user_id)
        
        # Filter by read status
        if read is not None:
            query = query.filter(Notification.is_read == read)
        
        # Filter by type
        if notification_type:
            types = notification_type.split(',')
            query = query.filter(Notification.type.in_(types))
        
        # Filter by date range
        if start_date:
            query = query.filter(Notification.created_at >= start_date)
        
        if end_date:
            query = query.filter(Notification.created_at <= end_date)
        
        # Order by creation date (newest first)
        query = query.order_by(Notification.created_at.desc())
        
        # Apply pagination
        total = query.count()
        notifications = query.offset(offset).limit(limit).all()
        
        return {
            'data': [notif.to_dict() for notif in notifications],
            'pagination': {
                'total': total,
                'page': (offset // limit) + 1,
                'limit': limit,
                'totalPages': (total + limit - 1) // limit
            }
        }
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications for user"""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    @staticmethod
    def get_notification_stats(user_id):
        """Get notification statistics for user"""
        total = Notification.query.filter_by(user_id=user_id).count()
        unread = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        
        # Get count by type
        type_counts = db.session.query(
            Notification.type,
            db.func.count(Notification.id)
        ).filter_by(user_id=user_id).group_by(Notification.type).all()
        
        by_type = {type_name: count for type_name, count in type_counts}
        
        return {
            'total': total,
            'unread': unread,
            'byType': by_type
        }
    
    @staticmethod
    def mark_multiple_as_read(user_id, notification_ids):
        """Mark multiple notifications as read"""
        Notification.query.filter(
            Notification.user_id == user_id,
            Notification.id.in_(notification_ids)
        ).update({
            'is_read': True, 
            'read_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        db.session.commit()
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read for a user"""
        Notification.query.filter_by(user_id=user_id).update({
            'is_read': True,
            'read_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        db.session.commit()
    
    @staticmethod
    def delete_notification(user_id, notification_id):
        """Delete a specific notification"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return True
        
        return False
    



class NotificationTemplate:
    """Notification templates for different types"""
    
    TEMPLATES = {
        'question_answered': {
            'title': 'Câu hỏi của bạn có câu trả lời mới',
            'message': '{answerer_name} đã trả lời câu hỏi "{question_title}"'
        },
        'answer_accepted': {
            'title': 'Câu trả lời của bạn được chấp nhận',
            'message': 'Câu trả lời của bạn cho câu hỏi "{question_title}" đã được chấp nhận'
        },
        'answer_voted': {
            'title': 'Câu trả lời của bạn được vote',
            'message': 'Câu trả lời của bạn cho câu hỏi "{question_title}" đã nhận được {vote_type} vote'
        },
        'question_voted': {
            'title': 'Câu hỏi của bạn được vote',
            'message': 'Câu hỏi "{question_title}" của bạn đã nhận được {vote_type} vote'
        },
        'comment_added': {
            'title': 'Có bình luận mới',
            'message': '{commenter_name} đã bình luận về {item_type} "{item_title}"'
        },
        'question_pinned': {
            'title': 'Câu hỏi của bạn được ghim',
            'message': 'Câu hỏi "{question_title}" của bạn đã được ghim bởi {moderator_name}'
        },
        'question_closed': {
            'title': 'Câu hỏi của bạn được đóng',
            'message': 'Câu hỏi "{question_title}" của bạn đã được đóng bởi {moderator_name}'
        },
        'course_announcement': {
            'title': 'Thông báo khóa học mới',
            'message': 'Có thông báo mới từ khóa học "{course_title}"'
        },
        'assignment_due': {
            'title': 'Bài tập sắp hết hạn',
            'message': 'Bài tập "{assignment_title}" sẽ hết hạn vào {due_date}'
        }
    }
    
    @staticmethod
    def create_notification_from_template(user_id, template_type, data):
        """Create notification using template"""
        if template_type not in NotificationTemplate.TEMPLATES:
            raise ValueError(f"Unknown notification template: {template_type}")
        
        template = NotificationTemplate.TEMPLATES[template_type]
        
        try:
            title = template['title']
            message = template['message'].format(**data)
        except KeyError as e:
            raise ValueError(f"Missing template data: {e}")
        
        return Notification.create_notification(
            user_id=user_id,
            notification_type=template_type,
            title=title,
            message=message,
            data=data
        )