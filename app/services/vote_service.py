"""
Vote Service
Business logic for voting system
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError

from app.dao.vote_dao import VoteDAO
from app.dao.question_dao import QuestionDAO
from app.dao.answer_dao import AnswerDAO
from app.exceptions.base import ValidationException, BusinessLogicException
from app import db


class VoteService:
    """Service class cho vote operations"""
    
    def __init__(self):
        self.vote_dao = VoteDAO()
        self.question_dao = QuestionDAO()
        self.answer_dao = AnswerDAO()
    
    def cast_vote(self, user_id, votable_type, votable_id, vote_type):
        """
        Cast vote cho question hoặc answer
        
        Args:
            user_id: ID người vote
            votable_type: Loại item (question, answer)
            votable_id: ID của item
            vote_type: Loại vote (upvote, downvote)
            
        Returns:
            dict: Kết quả vote
        """
        try:
            # Validate vote type
            if vote_type not in ['upvote', 'downvote']:
                raise ValidationException("Loại vote không hợp lệ")
            
            # Validate votable type
            if votable_type not in ['question', 'answer']:
                raise ValidationException("Loại item vote không hợp lệ")
            
            # Check if item exists and get author
            item_author_id = self._get_item_author(votable_type, votable_id)
            if not item_author_id:
                raise ValidationException(f"Không tìm thấy {votable_type}")
            
            # Check if user is not the author
            if item_author_id == user_id:
                raise ValidationException(f"Bạn không thể vote cho {votable_type} của chính mình")
            
            # Cast vote
            vote = self.vote_dao.cast_vote(user_id, votable_type, votable_id, vote_type)
            
            # Get updated vote score
            vote_score = self.vote_dao.get_vote_score(votable_type, votable_id)
            
            # Update vote score in the item table
            self.vote_dao.update_item_vote_score(votable_type, votable_id, vote_score)
            
            return {
                'success': True,
                'data': {
                    'voteScore': vote_score,
                    'userVote': vote.vote_type if vote else None,
                    'message': f'Đã {vote_type} {votable_type}'
                }
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi vote: {str(e)}")
    
    def remove_vote(self, user_id, votable_type, votable_id):
        """
        Hủy vote
        
        Args:
            user_id: ID người hủy vote
            votable_type: Loại item (question, answer)
            votable_id: ID của item
            
        Returns:
            dict: Kết quả hủy vote
        """
        try:
            # Validate votable type
            if votable_type not in ['question', 'answer']:
                raise ValidationException("Loại item vote không hợp lệ")
            
            # Check if vote exists
            existing_vote = self.vote_dao.get_user_vote(user_id, votable_type, votable_id)
            if not existing_vote:
                raise ValidationException("Bạn chưa vote cho item này")
            
            # Remove vote
            removed = self.vote_dao.remove_vote(user_id, votable_type, votable_id)
            
            if not removed:
                raise ValidationException("Không thể hủy vote")
            
            # Get updated vote score
            vote_score = self.vote_dao.get_vote_score(votable_type, votable_id)
            
            # Update vote score in the item table
            self.vote_dao.update_item_vote_score(votable_type, votable_id, vote_score)
            
            return {
                'success': True,
                'data': {
                    'voteScore': vote_score,
                    'userVote': None,
                    'message': f'Đã hủy vote {votable_type}'
                }
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi hủy vote: {str(e)}")
    
    def get_user_vote(self, user_id, votable_type, votable_id):
        """
        Lấy vote của user cho một item
        
        Args:
            user_id: ID người dùng
            votable_type: Loại item (question, answer)
            votable_id: ID của item
            
        Returns:
            dict: Thông tin vote của user
        """
        try:
            vote = self.vote_dao.get_user_vote(user_id, votable_type, votable_id)
            
            return {
                'success': True,
                'data': {
                    'userVote': vote.vote_type if vote else None,
                    'votedAt': vote.created_at.isoformat() if vote else None
                }
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy thông tin vote: {str(e)}")
    
    def get_vote_score(self, votable_type, votable_id):
        """
        Lấy điểm vote của một item
        
        Args:
            votable_type: Loại item (question, answer)
            votable_id: ID của item
            
        Returns:
            dict: Điểm vote
        """
        try:
            vote_score = self.vote_dao.get_vote_score(votable_type, votable_id)
            
            return {
                'success': True,
                'data': {
                    'voteScore': vote_score
                }
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy điểm vote: {str(e)}")
    
    def get_user_votes(self, user_id, page=1, per_page=20, votable_type=None):
        """
        Lấy danh sách vote của user
        
        Args:
            user_id: ID người dùng
            page: Số trang
            per_page: Số vote mỗi trang
            votable_type: Lọc theo loại item (question, answer)
            
        Returns:
            dict: Danh sách vote của user
        """
        try:
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Validate votable type if provided
            if votable_type and votable_type not in ['question', 'answer']:
                raise ValidationException("Loại item vote không hợp lệ")
            
            # Get user votes
            result = self.vote_dao.get_user_votes_with_items(
                user_id=user_id,
                page=page,
                per_page=per_page,
                votable_type=votable_type
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy danh sách vote: {str(e)}")
    
    def get_vote_statistics(self, user_id=None, time_frame='all'):
        """
        Lấy thống kê vote
        
        Args:
            user_id: ID người dùng (nếu muốn thống kê của user cụ thể)
            time_frame: Khung thời gian (day, week, month, all)
            
        Returns:
            dict: Thống kê vote
        """
        try:
            # Validate time frame
            valid_time_frames = ['day', 'week', 'month', 'all']
            if time_frame not in valid_time_frames:
                time_frame = 'all'
            
            # Get statistics
            stats = self.vote_dao.get_vote_statistics(
                user_id=user_id,
                time_frame=time_frame
            )
            
            return {
                'success': True,
                'data': stats
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy thống kê vote: {str(e)}")
    
    def get_user_vote_summary(self, user_id):
        """
        Lấy tóm tắt vote của user
        
        Args:
            user_id: ID người dùng
            
        Returns:
            dict: Tóm tắt vote
        """
        try:
            summary = self.vote_dao.get_user_vote_summary(user_id)
            
            return {
                'success': True,
                'data': summary
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy tóm tắt vote: {str(e)}")
    
    def get_top_voted_items(self, votable_type, limit=10, time_frame='week'):
        """
        Lấy danh sách item được vote cao nhất
        
        Args:
            votable_type: Loại item (question, answer)
            limit: Số lượng item
            time_frame: Khung thời gian (day, week, month)
            
        Returns:
            dict: Danh sách item top vote
        """
        try:
            # Validate votable type
            if votable_type not in ['question', 'answer']:
                raise ValidationException("Loại item vote không hợp lệ")
            
            # Validate time frame
            valid_time_frames = ['day', 'week', 'month']
            if time_frame not in valid_time_frames:
                time_frame = 'week'
            
            # Get top voted items
            items = self.vote_dao.get_top_voted_items(
                votable_type=votable_type,
                limit=limit,
                time_frame=time_frame
            )
            
            return {
                'success': True,
                'data': items
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy danh sách top vote: {str(e)}")
    
    def bulk_update_vote_scores(self, votable_type=None):
        """
        Cập nhật hàng loạt điểm vote (dùng cho maintenance)
        
        Args:
            votable_type: Loại item cần cập nhật (question, answer), None để cập nhật tất cả
            
        Returns:
            dict: Kết quả cập nhật
        """
        try:
            # Validate votable type if provided
            if votable_type and votable_type not in ['question', 'answer']:
                raise ValidationException("Loại item vote không hợp lệ")
            
            # Update vote scores
            updated_count = self.vote_dao.bulk_update_vote_scores(votable_type)
            
            return {
                'success': True,
                'data': {
                    'updatedCount': updated_count,
                    'message': f'Đã cập nhật {updated_count} điểm vote'
                }
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi cập nhật điểm vote: {str(e)}")
    
    def get_vote_trends(self, time_frame='week', votable_type=None):
        """
        Lấy xu hướng vote theo thời gian
        
        Args:
            time_frame: Khung thời gian (day, week, month)
            votable_type: Loại item (question, answer)
            
        Returns:
            dict: Xu hướng vote
        """
        try:
            # Validate time frame
            valid_time_frames = ['day', 'week', 'month']
            if time_frame not in valid_time_frames:
                time_frame = 'week'
            
            # Validate votable type if provided
            if votable_type and votable_type not in ['question', 'answer']:
                raise ValidationException("Loại item vote không hợp lệ")
            
            # Calculate date range
            now = datetime.utcnow()
            if time_frame == 'day':
                start_date = now - timedelta(days=7)  # Last 7 days
            elif time_frame == 'week':
                start_date = now - timedelta(weeks=4)  # Last 4 weeks
            else:  # month
                start_date = now - timedelta(days=90)  # Last 3 months
            
            # Get vote trends (this would need to be implemented in DAO)
            trends = self.vote_dao.get_vote_trends(
                start_date=start_date,
                end_date=now,
                time_frame=time_frame,
                votable_type=votable_type
            )
            
            return {
                'success': True,
                'data': trends
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy xu hướng vote: {str(e)}")
    
    def _get_item_author(self, votable_type, votable_id):
        """
        Lấy ID tác giả của item
        
        Args:
            votable_type: Loại item (question, answer)
            votable_id: ID của item
            
        Returns:
            int: ID tác giả hoặc None nếu không tìm thấy
        """
        try:
            if votable_type == 'question':
                question = self.question_dao.get_question_by_id(votable_id)
                return question['author']['id'] if question else None
            elif votable_type == 'answer':
                answer = self.answer_dao.get_answer_by_id(votable_id)
                return answer['author']['id'] if answer else None
            else:
                return None
                
        except Exception:
            return None