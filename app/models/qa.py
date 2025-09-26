from datetime import datetime
from app import db
from app.models.vote import Vote
from app.models.comment import Comment
from app.models.tag import QuestionTag


class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # technical_question, course_content, etc.
    scope = db.Column(db.String(20), nullable=False)  # course, chapter, lesson, quiz, assignment
    scope_id = db.Column(db.Integer, nullable=False)  # ID of the scope item
    status = db.Column(db.String(20), default='new')  # new, in_progress, answered, closed
    is_pinned = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    attachment_url = db.Column(db.String(500), nullable=True)  # URL tạm thời cho file đính kèm
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='questions')
    answers = db.relationship('Answer', back_populates='question', cascade='all, delete-orphan')
    question_tags = db.relationship('QuestionTag', back_populates='question', cascade='all, delete-orphan')
    
    # Indexes for better performance
    __table_args__ = (
        db.Index('idx_author_id', 'author_id'),
        db.Index('idx_category', 'category'),
        db.Index('idx_scope', 'scope', 'scope_id'),
        db.Index('idx_status', 'status'),
        db.Index('idx_created_at', 'created_at'),
        db.Index('idx_last_activity', 'last_activity_at'),
    )
    
    def __init__(self, title, content, author_id, category, scope, scope_id, **kwargs):
        self.title = title
        self.content = content
        self.author_id = author_id
        self.category = category
        self.scope = scope
        self.scope_id = scope_id
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f'<Question {self.id}: {self.title[:50]}>'
    
    def to_dict(self, current_user_id=None, include_answers=False, include_comments=False):
        import logging
        
        try:
            # Basic fields
            result = {
                'id': self.id,
                'title': self.title,
                'content': self.content,
                'category': self.category,
                'scope': self.scope,
                'scope_id': self.scope_id,
                'status': self.status,
                'is_pinned': self.is_pinned,
                'is_featured': self.is_featured,
                'view_count': self.view_count,
                'attachment_url': self.attachment_url,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            }
            
            # Vote score with error handling
            try:
                result['vote_score'] = self.get_vote_score()
            except Exception as e:
                logging.error(f"Error getting vote_score for question {self.id}: {str(e)}")
                result['vote_score'] = 0
            
            # Answer count with error handling
            try:
                result['answer_count'] = self.get_answer_count()
            except Exception as e:
                logging.error(f"Error getting answer_count for question {self.id}: {str(e)}")
                result['answer_count'] = 0
            
            # Author with error handling
            try:
                if self.author:
                    result['author'] = {
                        'id': self.author.id,
                        'full_name': self.author.full_name,
                        'email': self.author.email,
                        'avatar_url': getattr(self.author, 'avatar_url', None),
                        'role': getattr(self.author, 'role', 'student').value if hasattr(getattr(self.author, 'role', 'student'), 'value') else getattr(self.author, 'role', 'student')
                    }
                else:
                    result['author'] = {
                        'id': self.author_id,
                        'full_name': 'Unknown User',
                        'email': 'unknown@example.com',
                        'avatar_url': None,
                        'role': 'student'
                    }
            except Exception as e:
                logging.error(f"Error getting author for question {self.id}: {str(e)}")
                result['author'] = {
                    'id': self.author_id,
                    'full_name': 'Unknown User',
                    'email': 'unknown@example.com',
                    'avatar_url': None,
                    'role': 'student'
                }
            
            # Tags with error handling
            try:
                result['tags'] = [qt.tag.to_dict() for qt in self.question_tags if qt.tag is not None]
            except Exception as e:
                logging.error(f"Error getting tags for question {self.id}: {str(e)}")
                result['tags'] = []
                
        except Exception as e:
            logging.error(f"Error in to_dict for question {self.id}: {str(e)}")
            raise e
        
        # Add user-specific data
        if current_user_id:
            result['user_vote'] = Vote.get_user_vote(current_user_id, 'question', self.id)
            result['user_permissions'] = self.get_user_permissions(current_user_id)
        
        # Include answers if requested
        if include_answers:
            result['answers'] = [
                answer.to_dict(current_user_id=current_user_id) 
                for answer in self.answers
            ]
        
        # Include comments if requested
        if include_comments:
            comments = Comment.query.filter_by(
                commentable_type='question',
                commentable_id=self.id,
                parent_id=None
            ).order_by(Comment.created_at.asc()).all()
            
            result['comments'] = [
                comment.to_dict(current_user_id=current_user_id) 
                for comment in comments
            ]
        
        return result
    
    def get_vote_score(self):
        """Get the vote score for this question"""
        return Vote.get_vote_score('question', self.id)
    
    def get_answer_count(self):
        """Get the number of answers for this question"""
        return len(self.answers)
    
    def get_comment_count(self):
        """Get the number of comments for this question"""
        return Comment.get_comment_count('question', self.id)
    
    def get_user_permissions(self, user_id):
        """Get user permissions for this question"""
        from app.models.user import User
        
        user = User.query.get(user_id)
        if not user:
            return {
                'can_edit': False,
                'can_delete': False,
                'can_pin': False,
                'can_feature': False,
                'can_change_status': False
            }
        
        # Author can edit/delete their own question
        can_edit = self.author_id == user_id
        can_delete = self.author_id == user_id
        
        # Instructors and admins have additional permissions
        can_pin = False
        can_feature = False
        can_change_status = False
        
        if hasattr(user, 'role') and user.role in ['instructor', 'admin']:
            can_delete = True
            can_pin = True
            can_feature = True
            can_change_status = True
        
        return {
            'can_edit': can_edit,
            'can_delete': can_delete,
            'can_pin': can_pin,
            'can_feature': can_feature,
            'can_change_status': can_change_status
        }
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        db.session.commit()
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
        db.session.commit()
    
    def get_related_questions(self, limit=5):
        """Get related questions based on tags and category"""
        tag_ids = [qt.tag_id for qt in self.question_tags]
        
        if not tag_ids:
            # If no tags, find by category
            return Question.query.filter(
                Question.id != self.id,
                Question.category == self.category
            ).order_by(Question.view_count.desc()).limit(limit).all()
        
        # Find questions with similar tags
        related = db.session.query(Question)\
            .join(QuestionTag)\
            .filter(
                Question.id != self.id,
                QuestionTag.tag_id.in_(tag_ids)
            )\
            .group_by(Question.id)\
            .order_by(db.func.count(QuestionTag.tag_id).desc())\
            .limit(limit).all()
        
        return related
    
    @staticmethod
    def search_questions(query_params):
        """Search questions with filters"""
        query = Question.query
        
        # Text search
        if query_params.get('q'):
            search_term = f"%{query_params['q']}%"
            query = query.filter(
                db.or_(
                    Question.title.ilike(search_term),
                    Question.content.ilike(search_term)
                )
            )
        
        # Status filter
        if query_params.get('status'):
            query = query.filter(Question.status.in_(query_params['status']))
        
        # Category filter
        if query_params.get('category'):
            query = query.filter(Question.category.in_(query_params['category']))
        
        # Scope filter
        if query_params.get('scope'):
            query = query.filter(Question.scope.in_(query_params['scope']))
        
        if query_params.get('scope_id'):
            query = query.filter(Question.scope_id == query_params['scope_id'])
        
        # Tag filter
        if query_params.get('tag_ids'):
            query = query.join(QuestionTag).filter(
                QuestionTag.tag_id.in_(query_params['tag_ids'])
            )
        
        # Author filter
        if query_params.get('author_id'):
            query = query.filter(Question.author_id == query_params['author_id'])
        
        # Special filters
        if query_params.get('unanswered_only'):
            query = query.filter(~Question.answers.any())
        
        if query_params.get('pinned_only'):
            query = query.filter(Question.is_pinned == True)
        
        if query_params.get('featured_only'):
            query = query.filter(Question.is_featured == True)
        
        # Sorting
        sort_by = query_params.get('sort_by', 'newest')
        sort_order = query_params.get('sort_order', 'desc')
        
        if sort_by == 'newest':
            order_field = Question.created_at
        elif sort_by == 'oldest':
            order_field = Question.created_at
        elif sort_by == 'most_votes':
            # This would need a subquery for vote counts
            order_field = Question.created_at  # Fallback
        elif sort_by == 'most_answers':
            # This would need a subquery for answer counts
            order_field = Question.created_at  # Fallback
        elif sort_by == 'most_views':
            order_field = Question.view_count
        elif sort_by == 'last_activity':
            order_field = Question.last_activity_at
        else:
            order_field = Question.created_at
        
        if sort_order == 'desc':
            query = query.order_by(order_field.desc())
        else:
            query = query.order_by(order_field.asc())
        
        return query