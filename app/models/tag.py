from datetime import datetime
from app import db


class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    color = db.Column(db.String(7), nullable=False, default='#3B82F6')  # Hex color code
    description = db.Column(db.Text)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    question_tags = db.relationship('QuestionTag', back_populates='tag', cascade='all, delete-orphan')
    
    def __init__(self, name, color='#3B82F6', description=None, **kwargs):
        self.name = name
        self.color = color
        self.description = description
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f'<Tag {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def increment_usage(self):
        """Increment usage count when tag is used"""
        self.usage_count += 1
        db.session.commit()
    
    def decrement_usage(self):
        """Decrement usage count when tag is removed"""
        if self.usage_count > 0:
            self.usage_count -= 1
            db.session.commit()


# Association table for many-to-many relationship between questions and tags
class QuestionTag(db.Model):
    __tablename__ = 'question_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    question = db.relationship('Question', back_populates='question_tags')
    tag = db.relationship('Tag', back_populates='question_tags')
    
    # Unique constraint to prevent duplicate tags on same question
    __table_args__ = (db.UniqueConstraint('question_id', 'tag_id', name='unique_question_tag'),)
    
    def __repr__(self):
        return f'<QuestionTag question_id={self.question_id} tag_id={self.tag_id}>'