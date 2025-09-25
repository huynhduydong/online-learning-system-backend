"""
Vote DAO - Data Access Object cho Vote model
Chịu trách nhiệm tất cả database operations liên quan đến Vote
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, desc, asc, func

from app.dao.base_dao import BaseDAO
from app.models.vote import Vote
from app.models.qa import Question
from app.models.answer import Answer
from app import db


class VoteDAO(BaseDAO):
    """
    VoteDAO class cung cấp các phương thức database operations cho Vote model
    """
    
    def __init__(self):
        super().__init__(Vote)
    
    def get_user_vote(self, user_id, votable_type, votable_id):
        """
        Lấy vote của user cho một item cụ thể
        
        Args:
            user_id: ID người dùng
            votable_type: Loại item (question, answer)
            votable_id: ID của item
            
        Returns:
            Vote hoặc None
        """
        try:
            return self.session.query(Vote).filter(
                and_(
                    Vote.user_id == user_id,
                    Vote.votable_type == votable_type,
                    Vote.votable_id == votable_id
                )
            ).first()
        except SQLAlchemyError as e:
            raise e
    
    def cast_vote(self, user_id, votable_type, votable_id, vote_type):
        """
        Thực hiện vote hoặc cập nhật vote
        
        Args:
            user_id: ID người dùng
            votable_type: Loại item (question, answer)
            votable_id: ID của item
            vote_type: Loại vote (upvote, downvote)
            
        Returns:
            dict: Kết quả vote
        """
        try:
            # Kiểm tra vote hiện tại
            existing_vote = self.get_user_vote(user_id, votable_type, votable_id)
            
            if existing_vote:
                if existing_vote.vote_type == vote_type:
                    # Nếu vote giống nhau, xóa vote (toggle)
                    self.session.delete(existing_vote)
                    action = 'removed'
                else:
                    # Nếu vote khác, cập nhật
                    existing_vote.vote_type = vote_type
                    existing_vote.updated_at = datetime.utcnow()
                    action = 'updated'
            else:
                # Tạo vote mới
                new_vote = Vote(
                    user_id=user_id,
                    votable_type=votable_type,
                    votable_id=votable_id,
                    vote_type=vote_type
                )
                self.session.add(new_vote)
                action = 'created'
            
            self.session.commit()
            
            # Cập nhật vote score
            vote_score = self.calculate_vote_score(votable_type, votable_id)
            self._update_item_vote_score(votable_type, votable_id, vote_score)
            
            return {
                'action': action,
                'voteType': vote_type if action != 'removed' else None,
                'voteScore': vote_score
            }
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def calculate_vote_score(self, votable_type, votable_id):
        """
        Tính vote score cho một item
        
        Args:
            votable_type: Loại item
            votable_id: ID của item
            
        Returns:
            int: Vote score
        """
        try:
            upvotes = self.session.query(Vote).filter(
                and_(
                    Vote.votable_type == votable_type,
                    Vote.votable_id == votable_id,
                    Vote.vote_type == 'upvote'
                )
            ).count()
            
            downvotes = self.session.query(Vote).filter(
                and_(
                    Vote.votable_type == votable_type,
                    Vote.votable_id == votable_id,
                    Vote.vote_type == 'downvote'
                )
            ).count()
            
            return upvotes - downvotes
        except SQLAlchemyError as e:
            raise e
    
    def _update_item_vote_score(self, votable_type, votable_id, vote_score):
        """
        Cập nhật vote score trong bảng tương ứng
        
        Args:
            votable_type: Loại item
            votable_id: ID của item
            vote_score: Vote score mới
        """
        try:
            if votable_type == 'question':
                self.session.query(Question).filter(Question.id == votable_id).update({
                    'vote_score': vote_score
                })
            elif votable_type == 'answer':
                self.session.query(Answer).filter(Answer.id == votable_id).update({
                    'vote_score': vote_score
                })
            
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def get_vote_statistics(self, votable_type, votable_id):
        """
        Lấy thống kê vote cho một item
        
        Args:
            votable_type: Loại item
            votable_id: ID của item
            
        Returns:
            dict: Thống kê vote
        """
        try:
            upvotes = self.session.query(Vote).filter(
                and_(
                    Vote.votable_type == votable_type,
                    Vote.votable_id == votable_id,
                    Vote.vote_type == 'upvote'
                )
            ).count()
            
            downvotes = self.session.query(Vote).filter(
                and_(
                    Vote.votable_type == votable_type,
                    Vote.votable_id == votable_id,
                    Vote.vote_type == 'downvote'
                )
            ).count()
            
            total_votes = upvotes + downvotes
            vote_score = upvotes - downvotes
            
            return {
                'upvotes': upvotes,
                'downvotes': downvotes,
                'totalVotes': total_votes,
                'voteScore': vote_score,
                'upvotePercentage': (upvotes / total_votes * 100) if total_votes > 0 else 0
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_user_votes(self, user_id, votable_type=None, page=1, per_page=20):
        """
        Lấy danh sách vote của user
        
        Args:
            user_id: ID người dùng
            votable_type: Loại item (optional)
            page: Số trang
            per_page: Số vote mỗi trang
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            query = self.session.query(Vote).filter(Vote.user_id == user_id)
            
            if votable_type:
                query = query.filter(Vote.votable_type == votable_type)
            
            query = query.order_by(desc(Vote.created_at))
            
            total = query.count()
            votes = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Lấy thông tin chi tiết của các item được vote
            vote_data = []
            for vote in votes:
                vote_dict = vote.to_dict()
                
                # Lấy thông tin item được vote
                if vote.votable_type == 'question':
                    item = self.session.query(Question).filter(Question.id == vote.votable_id).first()
                    if item:
                        vote_dict['item'] = {
                            'id': item.id,
                            'title': item.title,
                            'type': 'question'
                        }
                elif vote.votable_type == 'answer':
                    item = self.session.query(Answer).options(
                        joinedload(Answer.question)
                    ).filter(Answer.id == vote.votable_id).first()
                    if item:
                        vote_dict['item'] = {
                            'id': item.id,
                            'content': item.content[:100] + '...' if len(item.content) > 100 else item.content,
                            'type': 'answer',
                            'questionTitle': item.question.title if item.question else None
                        }
                
                vote_data.append(vote_dict)
            
            return {
                'data': vote_data,
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                }
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_user_vote_summary(self, user_id):
        """
        Lấy tổng kết vote của user
        
        Args:
            user_id: ID người dùng
            
        Returns:
            dict: Tổng kết vote
        """
        try:
            # Đếm vote theo loại
            question_upvotes = self.session.query(Vote).filter(
                and_(
                    Vote.user_id == user_id,
                    Vote.votable_type == 'question',
                    Vote.vote_type == 'upvote'
                )
            ).count()
            
            question_downvotes = self.session.query(Vote).filter(
                and_(
                    Vote.user_id == user_id,
                    Vote.votable_type == 'question',
                    Vote.vote_type == 'downvote'
                )
            ).count()
            
            answer_upvotes = self.session.query(Vote).filter(
                and_(
                    Vote.user_id == user_id,
                    Vote.votable_type == 'answer',
                    Vote.vote_type == 'upvote'
                )
            ).count()
            
            answer_downvotes = self.session.query(Vote).filter(
                and_(
                    Vote.user_id == user_id,
                    Vote.votable_type == 'answer',
                    Vote.vote_type == 'downvote'
                )
            ).count()
            
            total_votes = question_upvotes + question_downvotes + answer_upvotes + answer_downvotes
            
            return {
                'totalVotes': total_votes,
                'questions': {
                    'upvotes': question_upvotes,
                    'downvotes': question_downvotes,
                    'total': question_upvotes + question_downvotes
                },
                'answers': {
                    'upvotes': answer_upvotes,
                    'downvotes': answer_downvotes,
                    'total': answer_upvotes + answer_downvotes
                }
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_top_voted_items(self, votable_type, days=7, limit=10):
        """
        Lấy các item có vote cao nhất trong khoảng thời gian
        
        Args:
            votable_type: Loại item
            days: Số ngày gần đây
            limit: Số lượng item
            
        Returns:
            List: Danh sách item top vote
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Tính vote score cho từng item
            vote_scores = self.session.query(
                Vote.votable_id,
                func.sum(
                    func.case(
                        (Vote.vote_type == 'upvote', 1),
                        (Vote.vote_type == 'downvote', -1),
                        else_=0
                    )
                ).label('vote_score')
            ).filter(
                and_(
                    Vote.votable_type == votable_type,
                    Vote.created_at >= since_date
                )
            ).group_by(Vote.votable_id).order_by(desc('vote_score')).limit(limit).all()
            
            # Lấy thông tin chi tiết của các item
            item_ids = [item.votable_id for item in vote_scores]
            
            if votable_type == 'question':
                items = self.session.query(Question).options(
                    joinedload(Question.author)
                ).filter(Question.id.in_(item_ids)).all()
            elif votable_type == 'answer':
                items = self.session.query(Answer).options(
                    joinedload(Answer.author),
                    joinedload(Answer.question)
                ).filter(Answer.id.in_(item_ids)).all()
            else:
                return []
            
            # Kết hợp vote score với thông tin item
            items_dict = {item.id: item for item in items}
            result = []
            
            for vote_data in vote_scores:
                if vote_data.votable_id in items_dict:
                    item = items_dict[vote_data.votable_id]
                    item_dict = item.to_dict()
                    item_dict['voteScore'] = vote_data.vote_score
                    result.append(item_dict)
            
            return result
        except SQLAlchemyError as e:
            raise e
    
    def bulk_update_vote_scores(self, votable_type):
        """
        Cập nhật hàng loạt vote score cho tất cả item của một loại
        
        Args:
            votable_type: Loại item
        """
        try:
            # Tính vote score cho tất cả item
            vote_scores = self.session.query(
                Vote.votable_id,
                func.sum(
                    func.case(
                        (Vote.vote_type == 'upvote', 1),
                        (Vote.vote_type == 'downvote', -1),
                        else_=0
                    )
                ).label('vote_score')
            ).filter(Vote.votable_type == votable_type).group_by(Vote.votable_id).all()
            
            # Cập nhật vote score
            for vote_data in vote_scores:
                self._update_item_vote_score(votable_type, vote_data.votable_id, vote_data.vote_score)
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e