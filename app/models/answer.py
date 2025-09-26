from datetime import datetime
from app import db
from app.models.vote import Vote
from app.models.comment import Comment


class Answer(db.Model):
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_accepted = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    attachment_url = db.Column(db.String(500), nullable=True)  # URL tạm thời cho file đính kèm
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    question = db.relationship('Question', back_populates='answers')
    author = db.relationship('User', backref='answers')
    
    # Indexes for better performance
    __table_args__ = (
        db.Index('idx_question_id', 'question_id'),
        db.Index('idx_author_id', 'author_id'),
        db.Index('idx_is_accepted', 'is_accepted'),
    )
    
    def __init__(self, content, question_id, author_id, **kwargs):
        self.content = content
        self.question_id = question_id
        self.author_id = author_id
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f'<Answer {self.id} for Question {self.question_id}>'
    
    def to_dict(self, current_user_id=None, include_comments=False):
        result = {
            'id': self.id,
            'content': self.content,
            'question_id': self.question_id,
            'is_accepted': self.is_accepted,
            'is_pinned': self.is_pinned,
            'vote_score': self.get_vote_score(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'author': {
                'id': self.author.id,
                'full_name': self.author.full_name,
                'email': self.author.email,
                'avatar_url': getattr(self.author, 'avatar_url', None),
                'role': getattr(self.author, 'role', 'student').value if hasattr(getattr(self.author, 'role', 'student'), 'value') else str(getattr(self.author, 'role', 'student'))
            },
            'attachment_url': self.attachment_url,
            'comment_count': 0  # Temporarily disabled due to schema issue
        }
        
        # Add user-specific data
        if current_user_id:
            result['user_vote'] = Vote.get_user_vote(current_user_id, 'answer', self.id)
            result['user_permissions'] = self.get_user_permissions(current_user_id)
        
        return result
    
    def get_vote_score(self):
        """Get the vote score for this answer"""
        return Vote.get_vote_score('answer', self.id)
    
    def get_comment_count(self):
        """Get the number of comments for this answer"""
        return Comment.get_comment_count('answer', self.id)
    
    def get_user_permissions(self, user_id):
        """Get user permissions for this answer"""
        from app.models.user import User
        
        user = User.query.get(user_id)
        if not user:
            return {
                'can_edit': False,
                'can_delete': False,
                'can_accept': False,
                'can_pin': False
            }
        
        # Author can edit/delete their own answer
        can_edit = self.author_id == user_id
        can_delete = self.author_id == user_id
        
        # Question author can accept answers
        can_accept = self.question.author_id == user_id
        
        # Instructors and admins have additional permissions
        can_pin = False
        if hasattr(user, 'role') and user.role in ['instructor', 'admin']:
            can_delete = True
            can_pin = True
            can_accept = True
        
        return {
            'can_edit': can_edit,
            'can_delete': can_delete,
            'can_accept': can_accept,
            'can_pin': can_pin
        }
    
    def accept(self):
        """Mark this answer as accepted and unaccept others"""
        # Unaccept other answers for the same question
        Answer.query.filter_by(question_id=self.question_id).update({'is_accepted': False})
        
        # Accept this answer
        self.is_accepted = True
        self.updated_at = datetime.utcnow()
        
        # Update question status
        self.question.status = 'answered'
        self.question.last_activity_at = datetime.utcnow()
        
        db.session.commit()
    
    def unaccept(self):
        """Unaccept this answer"""
        self.is_accepted = False
        self.updated_at = datetime.utcnow()
        
        # Check if question has other accepted answers
        has_accepted = Answer.query.filter_by(
            question_id=self.question_id,
            is_accepted=True
        ).filter(Answer.id != self.id).first()
        
        if not has_accepted:
            self.question.status = 'in_progress'
        
        self.question.last_activity_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_answers_for_question(question_id, page=1, per_page=10):
        """Get paginated answers for a question"""
        return Answer.query.filter_by(question_id=question_id)\
            .order_by(Answer.is_accepted.desc(), Answer.created_at.asc())\
            .paginate(page=page, per_page=per_page, error_out=False)