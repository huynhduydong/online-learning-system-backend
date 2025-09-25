from datetime import datetime
from app import db


class Vote(db.Model):
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    votable_type = db.Column(db.String(20), nullable=False)  # 'question' or 'answer'
    votable_id = db.Column(db.Integer, nullable=False)  # ID of question or answer
    vote_type = db.Column(db.String(10), nullable=False)  # 'up' or 'down'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='votes')
    
    # Unique constraint to prevent multiple votes from same user on same item
    __table_args__ = (
        db.UniqueConstraint('user_id', 'votable_type', 'votable_id', name='unique_user_vote'),
        db.Index('idx_votable', 'votable_type', 'votable_id'),
    )
    
    def __init__(self, user_id, votable_type, votable_id, vote_type, **kwargs):
        self.user_id = user_id
        self.votable_type = votable_type
        self.votable_id = votable_id
        self.vote_type = vote_type
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f'<Vote {self.vote_type} on {self.votable_type}:{self.votable_id} by user:{self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'votable_type': self.votable_type,
            'votable_id': self.votable_id,
            'vote_type': self.vote_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_vote_score(votable_type, votable_id):
        """Calculate total vote score for a votable item"""
        up_votes = Vote.query.filter_by(
            votable_type=votable_type,
            votable_id=votable_id,
            vote_type='up'
        ).count()
        
        down_votes = Vote.query.filter_by(
            votable_type=votable_type,
            votable_id=votable_id,
            vote_type='down'
        ).count()
        
        return up_votes - down_votes
    
    @staticmethod
    def get_user_vote(user_id, votable_type, votable_id):
        """Get user's vote for a specific item"""
        vote = Vote.query.filter_by(
            user_id=user_id,
            votable_type=votable_type,
            votable_id=votable_id
        ).first()
        
        return vote.vote_type if vote else None
    
    @staticmethod
    def cast_vote(user_id, votable_type, votable_id, vote_type):
        """Cast or update a vote"""
        existing_vote = Vote.query.filter_by(
            user_id=user_id,
            votable_type=votable_type,
            votable_id=votable_id
        ).first()
        
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Remove vote if same type
                db.session.delete(existing_vote)
                return None
            else:
                # Update vote type
                existing_vote.vote_type = vote_type
                existing_vote.updated_at = datetime.utcnow()
                return existing_vote
        else:
            # Create new vote
            new_vote = Vote(
                user_id=user_id,
                votable_type=votable_type,
                votable_id=votable_id,
                vote_type=vote_type
            )
            db.session.add(new_vote)
            return new_vote