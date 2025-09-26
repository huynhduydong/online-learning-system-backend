from datetime import datetime
from app import db


class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    commentable_type = db.Column(db.String(20), nullable=False)  # 'question' or 'answer'
    commentable_id = db.Column(db.Integer, nullable=False)  # ID of question or answer
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)  # For nested comments
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='comments')
    parent = db.relationship('Comment', remote_side=[id], backref='replies')
    
    # Indexes for better performance
    __table_args__ = (
        db.Index('idx_commentable', 'commentable_type', 'commentable_id'),
        db.Index('idx_parent', 'parent_id'),
    )
    
    def __init__(self, content, author_id, commentable_type, commentable_id, parent_id=None, **kwargs):
        self.content = content
        self.author_id = author_id
        self.commentable_type = commentable_type
        self.commentable_id = commentable_id
        self.parent_id = parent_id
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f'<Comment {self.id} on {self.commentable_type}:{self.commentable_id}>'
    
    def to_dict(self, include_replies=True, current_user_id=None):
        result = {
            'id': self.id,
            'content': self.content,
            'commentable_type': self.commentable_type,
            'commentable_id': self.commentable_id,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'author': {
                'id': self.author.id,
                'full_name': self.author.full_name,
                'email': self.author.email,
                'avatar_url': getattr(self.author, 'avatar_url', None),
                'role': getattr(self.author, 'role', 'student')
            }
        }
        
        if include_replies:
            result['replies'] = [
                reply.to_dict(include_replies=False, current_user_id=current_user_id) 
                for reply in self.replies
            ]
        
        # Add user permissions
        if current_user_id:
            result['user_permissions'] = self.get_user_permissions(current_user_id)
        
        return result
    
    def get_user_permissions(self, user_id):
        """Get user permissions for this comment"""
        from app.models.user import User
        
        user = User.query.get(user_id)
        if not user:
            return {
                'can_edit': False,
                'can_delete': False
            }
        
        # Author can edit/delete their own comments
        can_edit = self.author_id == user_id
        can_delete = self.author_id == user_id
        
        # Instructors and admins can delete any comment
        if hasattr(user, 'role') and user.role in ['instructor', 'admin']:
            can_delete = True
        
        return {
            'can_edit': can_edit,
            'can_delete': can_delete
        }
    
    @staticmethod
    def get_comments_for_item(commentable_type, commentable_id, page=1, per_page=10):
        """Get paginated comments for a specific item"""
        return Comment.query.filter_by(
            commentable_type=commentable_type,
            commentable_id=commentable_id,
            parent_id=None  # Only top-level comments
        ).order_by(Comment.created_at.asc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    @staticmethod
    def get_comment_count(commentable_type, commentable_id):
        """Get total comment count for an item (including replies)"""
        return Comment.query.filter_by(
            commentable_type=commentable_type,
            commentable_id=commentable_id
        ).count()


# Association table for comment mentions
class CommentMention(db.Model):
    __tablename__ = 'comment_mentions'
    
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    mentioned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    comment = db.relationship('Comment', backref='mentions')
    mentioned_user = db.relationship('User', backref='comment_mentions')
    
    # Unique constraint to prevent duplicate mentions
    __table_args__ = (db.UniqueConstraint('comment_id', 'mentioned_user_id', name='unique_comment_mention'),)
    
    def __repr__(self):
        return f'<CommentMention comment_id={self.comment_id} user_id={self.mentioned_user_id}>'