"""
Answer Service
Business logic for Q&A answers management
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from app.dao.answer_dao import AnswerDAO
from app.dao.question_dao import QuestionDAO
from app.dao.vote_dao import VoteDAO
from app.dao.comment_dao import CommentDAO
from app.models.answer import Answer
from app.exceptions.base import ValidationException, BusinessLogicException
from app import db


class AnswerService:
    """Service class cho answer operations"""
    
    def __init__(self):
        self.answer_dao = AnswerDAO()
        self.question_dao = QuestionDAO()
        self.vote_dao = VoteDAO()
        self.comment_dao = CommentDAO()
    
    def get_question_answers(self, question_id, page=1, per_page=20, sort_by='votes', user_id=None):
        """
        Lấy danh sách câu trả lời của một câu hỏi
        
        Args:
            question_id: ID câu hỏi
            page: Số trang
            per_page: Số câu trả lời mỗi trang
            sort_by: Sắp xếp theo (votes, newest, oldest)
            user_id: ID người dùng (để lấy thông tin vote)
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            # Validate question exists
            question = self.question_dao.get_question_by_id(question_id)
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Validate sort
            valid_sorts = ['votes', 'newest', 'oldest']
            if sort_by not in valid_sorts:
                sort_by = 'votes'
            
            # Get answers from DAO
            result = self.answer_dao.get_answers_by_question(
                question_id=question_id,
                page=page,
                per_page=per_page,
                sort_by=sort_by
            )
            
            # Add user vote information if user is logged in
            if user_id:
                for answer in result['data']:
                    user_vote = self.vote_dao.get_user_vote(user_id, 'answer', answer['id'])
                    answer['userVote'] = user_vote.vote_type if user_vote else None
            
            return {
                'success': True,
                'data': result
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy danh sách câu trả lời: {str(e)}")
    
    def get_answer_by_id(self, answer_id, user_id=None):
        """
        Lấy chi tiết câu trả lời theo ID
        
        Args:
            answer_id: ID câu trả lời
            user_id: ID người dùng (để kiểm tra quyền)
            
        Returns:
            dict: Chi tiết câu trả lời
        """
        try:
            answer = self.answer_dao.get_answer_by_id(answer_id)
            
            if not answer:
                raise ValidationException("Không tìm thấy câu trả lời")
            
            # Lấy thông tin vote của user
            if user_id:
                user_vote = self.vote_dao.get_user_vote(user_id, 'answer', answer_id)
                answer['userVote'] = user_vote.vote_type if user_vote else None
            else:
                answer['userVote'] = None
            
            return {
                'success': True,
                'data': answer
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy chi tiết câu trả lời: {str(e)}")
    
    def create_answer(self, user_id, question_id, content):
        """
        Tạo câu trả lời mới
        
        Args:
            user_id: ID người tạo
            question_id: ID câu hỏi
            content: Nội dung câu trả lời
            
        Returns:
            dict: Câu trả lời được tạo
        """
        try:
            # Validate question exists
            question = self.question_dao.get_question_by_id(question_id)
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            # Validate content
            self._validate_answer_content(content)
            
            # Create answer
            answer = self.answer_dao.create_answer(
                question_id=question_id,
                author_id=user_id,
                content=content
            )
            
            # Update question activity
            self.question_dao.update_activity(question_id)
            
            # Get formatted answer data
            answer_data = self.answer_dao.get_answer_by_id(answer.id)
            
            return {
                'success': True,
                'data': answer_data,
                'message': 'Câu trả lời đã được tạo thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi tạo câu trả lời: {str(e)}")
    
    def update_answer(self, answer_id, user_id, content):
        """
        Cập nhật câu trả lời
        
        Args:
            answer_id: ID câu trả lời
            user_id: ID người cập nhật
            content: Nội dung mới
            
        Returns:
            dict: Câu trả lời đã cập nhật
        """
        try:
            # Check permission
            answer = self.answer_dao.get_answer_by_id(answer_id)
            if not answer:
                raise ValidationException("Không tìm thấy câu trả lời")
            
            if answer['author']['id'] != user_id:
                raise ValidationException("Bạn không có quyền chỉnh sửa câu trả lời này")
            
            # Validate content
            self._validate_answer_content(content)
            
            # Update answer
            updated = self.answer_dao.update_answer(answer_id, content, user_id)
            
            if not updated:
                raise ValidationException("Không thể cập nhật câu trả lời")
            
            # Get updated answer data
            answer_data = self.answer_dao.get_answer_by_id(answer_id)
            
            return {
                'success': True,
                'data': answer_data,
                'message': 'Câu trả lời đã được cập nhật thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi cập nhật câu trả lời: {str(e)}")
    
    def delete_answer(self, answer_id, user_id):
        """
        Xóa câu trả lời
        
        Args:
            answer_id: ID câu trả lời
            user_id: ID người xóa
            
        Returns:
            dict: Kết quả xóa
        """
        try:
            # Check permission
            answer = self.answer_dao.get_answer_by_id(answer_id)
            if not answer:
                raise ValidationException("Không tìm thấy câu trả lời")
            
            if answer['author']['id'] != user_id:
                raise ValidationException("Bạn không có quyền xóa câu trả lời này")
            
            # Delete answer
            deleted = self.answer_dao.delete_answer(answer_id, user_id)
            
            if not deleted:
                raise ValidationException("Không thể xóa câu trả lời")
            
            return {
                'success': True,
                'message': 'Câu trả lời đã được xóa thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi xóa câu trả lời: {str(e)}")
    
    def accept_answer(self, answer_id, user_id):
        """
        Chấp nhận câu trả lời (chỉ tác giả câu hỏi mới được phép)
        
        Args:
            answer_id: ID câu trả lời
            user_id: ID người chấp nhận (phải là tác giả câu hỏi)
            
        Returns:
            dict: Kết quả chấp nhận
        """
        try:
            # Get answer and question info
            answer = self.answer_dao.get_answer_by_id(answer_id)
            if not answer:
                raise ValidationException("Không tìm thấy câu trả lời")
            
            question = self.question_dao.get_question_by_id(answer['questionId'])
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            # Check permission (only question author can accept)
            if question['author']['id'] != user_id:
                raise ValidationException("Chỉ tác giả câu hỏi mới có thể chấp nhận câu trả lời")
            
            # Accept answer
            accepted = self.answer_dao.accept_answer(answer_id, user_id)
            
            if not accepted:
                raise ValidationException("Không thể chấp nhận câu trả lời")
            
            return {
                'success': True,
                'message': 'Câu trả lời đã được chấp nhận'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi chấp nhận câu trả lời: {str(e)}")
    
    def unaccept_answer(self, answer_id, user_id):
        """
        Hủy chấp nhận câu trả lời
        
        Args:
            answer_id: ID câu trả lời
            user_id: ID người hủy chấp nhận
            
        Returns:
            dict: Kết quả hủy chấp nhận
        """
        try:
            # Get answer and question info
            answer = self.answer_dao.get_answer_by_id(answer_id)
            if not answer:
                raise ValidationException("Không tìm thấy câu trả lời")
            
            question = self.question_dao.get_question_by_id(answer['questionId'])
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            # Check permission
            if question['author']['id'] != user_id:
                raise ValidationException("Chỉ tác giả câu hỏi mới có thể hủy chấp nhận câu trả lời")
            
            # Unaccept answer
            unaccepted = self.answer_dao.unaccept_answer(answer_id, user_id)
            
            if not unaccepted:
                raise ValidationException("Không thể hủy chấp nhận câu trả lời")
            
            return {
                'success': True,
                'message': 'Đã hủy chấp nhận câu trả lời'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi hủy chấp nhận câu trả lời: {str(e)}")
    
    def vote_answer(self, answer_id, user_id, vote_type):
        """
        Vote cho câu trả lời
        
        Args:
            answer_id: ID câu trả lời
            user_id: ID người vote
            vote_type: Loại vote (upvote, downvote)
            
        Returns:
            dict: Kết quả vote
        """
        try:
            # Validate vote type
            if vote_type not in ['upvote', 'downvote']:
                raise ValidationException("Loại vote không hợp lệ")
            
            # Check if answer exists
            answer = self.answer_dao.get_answer_by_id(answer_id)
            if not answer:
                raise ValidationException("Không tìm thấy câu trả lời")
            
            # Check if user is not the author
            if answer['author']['id'] == user_id:
                raise ValidationException("Bạn không thể vote cho câu trả lời của chính mình")
            
            # Cast vote
            vote = self.vote_dao.cast_vote(user_id, 'answer', answer_id, vote_type)
            
            # Get updated vote score
            vote_score = self.vote_dao.get_vote_score('answer', answer_id)
            
            return {
                'success': True,
                'data': {
                    'voteScore': vote_score,
                    'userVote': vote.vote_type if vote else None
                },
                'message': f'Đã {vote_type} câu trả lời'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi vote câu trả lời: {str(e)}")
    
    def get_user_answers(self, user_id, page=1, per_page=20):
        """
        Lấy danh sách câu trả lời của user
        
        Args:
            user_id: ID người dùng
            page: Số trang
            per_page: Số câu trả lời mỗi trang
            
        Returns:
            dict: Danh sách câu trả lời của user
        """
        try:
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Get user answers
            result = self.answer_dao.get_user_answers(
                user_id=user_id,
                page=page,
                per_page=per_page
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy câu trả lời của người dùng: {str(e)}")
    
    def get_top_answers(self, limit=10, time_frame='week'):
        """
        Lấy câu trả lời được vote cao nhất
        
        Args:
            limit: Số lượng câu trả lời
            time_frame: Khung thời gian (day, week, month)
            
        Returns:
            dict: Danh sách câu trả lời top
        """
        try:
            answers = self.answer_dao.get_top_answers(
                limit=limit,
                time_frame=time_frame
            )
            
            return {
                'success': True,
                'data': [answer.to_dict() for answer in answers]
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy câu trả lời top: {str(e)}")
    
    def search_answers(self, search_term, page=1, per_page=20, filters=None):
        """
        Tìm kiếm câu trả lời
        
        Args:
            search_term: Từ khóa tìm kiếm
            page: Số trang
            per_page: Số câu trả lời mỗi trang
            filters: Bộ lọc bổ sung
            
        Returns:
            dict: Kết quả tìm kiếm
        """
        try:
            if not search_term or len(search_term.strip()) < 2:
                raise ValidationException("Từ khóa tìm kiếm phải có ít nhất 2 ký tự")
            
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Search answers
            result = self.answer_dao.search_answers(
                search_term=search_term.strip(),
                page=page,
                per_page=per_page,
                filters=filters or {}
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi tìm kiếm câu trả lời: {str(e)}")
    
    def get_recent_answers(self, limit=10):
        """
        Lấy câu trả lời gần đây
        
        Args:
            limit: Số lượng câu trả lời
            
        Returns:
            dict: Danh sách câu trả lời gần đây
        """
        try:
            answers = self.answer_dao.get_recent_answers(limit=limit)
            
            return {
                'success': True,
                'data': [answer.to_dict() for answer in answers]
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy câu trả lời gần đây: {str(e)}")
    
    def _validate_answer_content(self, content):
        """Validate answer content"""
        if not content or not content.strip():
            raise ValidationException("Nội dung câu trả lời không được để trống")
        
        if len(content.strip()) < 10:
            raise ValidationException("Nội dung câu trả lời phải có ít nhất 10 ký tự")
        
        if len(content) > 10000:
            raise ValidationException("Nội dung câu trả lời không được quá 10,000 ký tự")