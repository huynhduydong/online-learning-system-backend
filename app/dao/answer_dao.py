"""
Answer DAO - Data Access Object cho Answer model
Chịu trách nhiệm tất cả database operations liên quan đến Answer
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, desc, asc, func

from app.dao.base_dao import BaseDAO
from app.models.answer import Answer
from app.models.vote import Vote
from app.models.comment import Comment
from app.models.qa import Question
from app import db


class AnswerDAO(BaseDAO):
    """
    AnswerDAO class cung cấp các phương thức database operations cho Answer model
    """
    
    def __init__(self):
        super().__init__(Answer)
    
    def get_answers_by_question(self, question_id, page=1, per_page=20, sort_by='votes'):
        """
        Lấy danh sách câu trả lời của một câu hỏi
        
        Args:
            question_id: ID câu hỏi
            page: Số trang
            per_page: Số câu trả lời mỗi trang
            sort_by: Sắp xếp theo (votes, newest, oldest)
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            query = self.session.query(Answer).options(
                joinedload(Answer.author)
            ).filter(Answer.question_id == question_id)
            
            # Sắp xếp
            if sort_by == 'votes':
                # Câu trả lời được chấp nhận lên đầu, sau đó theo created_at (vote_score sẽ được sort trong Python)
                query = query.order_by(
                    desc(Answer.is_accepted),
                    desc(Answer.created_at)
                )
            elif sort_by == 'newest':
                query = query.order_by(desc(Answer.created_at))
            elif sort_by == 'oldest':
                query = query.order_by(asc(Answer.created_at))
            else:
                # Mặc định theo accepted và created_at
                query = query.order_by(
                    desc(Answer.is_accepted),
                    desc(Answer.created_at)
                )
            
            total = query.count()
            answers = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [answer.to_dict() for answer in answers],
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                }
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_answer_by_id(self, answer_id, include_question=False):
        """
        Lấy câu trả lời theo ID
        
        Args:
            answer_id: ID câu trả lời
            include_question: Có bao gồm thông tin câu hỏi không
            
        Returns:
            Answer hoặc None
        """
        try:
            query = self.session.query(Answer).options(
                joinedload(Answer.author)
            )
            
            if include_question:
                query = query.options(joinedload(Answer.question))
            
            answer = query.filter(Answer.id == answer_id).first()
            if answer:
                return answer.to_dict()
            return None
        except SQLAlchemyError as e:
            raise e
    
    def get_user_answers(self, user_id, page=1, per_page=20, status=None):
        """
        Lấy danh sách câu trả lời của user
        
        Args:
            user_id: ID người dùng
            page: Số trang
            per_page: Số câu trả lời mỗi trang
            status: Trạng thái (accepted, not_accepted)
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            query = self.session.query(Answer).options(
                joinedload(Answer.question)
            ).filter(Answer.author_id == user_id)
            
            if status == 'accepted':
                query = query.filter(Answer.is_accepted == True)
            elif status == 'not_accepted':
                query = query.filter(Answer.is_accepted == False)
            
            query = query.order_by(desc(Answer.created_at))
            
            total = query.count()
            answers = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [answer.to_dict() for answer in answers],
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                }
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_top_answers(self, days=7, limit=10):
        """
        Lấy câu trả lời có vote cao nhất trong khoảng thời gian
        
        Args:
            days: Số ngày gần đây
            limit: Số lượng câu trả lời
            
        Returns:
            List[Answer]: Danh sách câu trả lời top
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            return self.session.query(Answer).options(
                joinedload(Answer.author),
                joinedload(Answer.question)
            ).filter(
                Answer.created_at >= since_date
            ).order_by(
                desc(Answer.created_at)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            raise e
    
    def accept_answer(self, answer_id, question_author_id):
        """
        Chấp nhận câu trả lời (chỉ tác giả câu hỏi mới được chấp nhận)
        
        Args:
            answer_id: ID câu trả lời
            question_author_id: ID tác giả câu hỏi
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Lấy câu trả lời và kiểm tra quyền
            answer = self.session.query(Answer).options(
                joinedload(Answer.question)
            ).filter(Answer.id == answer_id).first()
            
            if not answer:
                return False
            
            # Kiểm tra quyền chấp nhận (chỉ tác giả câu hỏi)
            if answer.question.author_id != question_author_id:
                return False
            
            # Bỏ chấp nhận câu trả lời cũ (nếu có)
            self.session.query(Answer).filter(
                and_(
                    Answer.question_id == answer.question_id,
                    Answer.is_accepted == True
                )
            ).update({'is_accepted': False})
            
            # Chấp nhận câu trả lời mới
            answer.is_accepted = True
            answer.accepted_at = datetime.utcnow()
            
            # Cập nhật accepted_answer_id trong question
            self.session.query(Question).filter(
                Question.id == answer.question_id
            ).update({'accepted_answer_id': answer_id})
            
            self.session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def unaccept_answer(self, answer_id, question_author_id):
        """
        Bỏ chấp nhận câu trả lời
        
        Args:
            answer_id: ID câu trả lời
            question_author_id: ID tác giả câu hỏi
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Lấy câu trả lời và kiểm tra quyền
            answer = self.session.query(Answer).options(
                joinedload(Answer.question)
            ).filter(Answer.id == answer_id).first()
            
            if not answer:
                return False
            
            # Kiểm tra quyền (chỉ tác giả câu hỏi)
            if answer.question.author_id != question_author_id:
                return False
            
            # Bỏ chấp nhận
            answer.is_accepted = False
            answer.accepted_at = None
            
            # Cập nhật accepted_answer_id trong question
            self.session.query(Question).filter(
                Question.id == answer.question_id
            ).update({'accepted_answer_id': None})
            
            self.session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def get_answer_statistics(self, answer_id):
        """
        Lấy thống kê của câu trả lời
        
        Args:
            answer_id: ID câu trả lời
            
        Returns:
            dict: Thống kê câu trả lời
        """
        try:
            answer = self.get_by_id(answer_id)
            if not answer:
                return None
            
            # Đếm votes
            upvotes = self.session.query(Vote).filter(
                and_(
                    Vote.votable_type == 'answer',
                    Vote.votable_id == answer_id,
                    Vote.vote_type == 'upvote'
                )
            ).count()
            
            downvotes = self.session.query(Vote).filter(
                and_(
                    Vote.votable_type == 'answer',
                    Vote.votable_id == answer_id,
                    Vote.vote_type == 'downvote'
                )
            ).count()
            
            # Đếm comments
            comments_count = self.session.query(Comment).filter(
                and_(
                    Comment.commentable_type == 'answer',
                    Comment.commentable_id == answer_id
                )
            ).count()
            
            return {
                'answerId': answer_id,
                'voteScore': upvotes - downvotes,  # Calculate vote score
                'upvotes': upvotes,
                'downvotes': downvotes,
                'commentsCount': comments_count,
                'isAccepted': answer.is_accepted,
                'acceptedAt': answer.accepted_at.isoformat() if answer.accepted_at else None,
                'createdAt': answer.created_at.isoformat() if answer.created_at else None
            }
        except SQLAlchemyError as e:
            raise e
    
    def search_answers(self, search_term, filters=None, page=1, per_page=20):
        """
        Tìm kiếm câu trả lời theo từ khóa
        
        Args:
            search_term: Từ khóa tìm kiếm
            filters: Bộ lọc bổ sung
            page: Số trang
            per_page: Số câu trả lời mỗi trang
            
        Returns:
            dict: Kết quả tìm kiếm
        """
        try:
            search_pattern = f"%{search_term}%"
            
            query = self.session.query(Answer).options(
                joinedload(Answer.author),
                joinedload(Answer.question)
            ).filter(
                Answer.content.ilike(search_pattern)
            )
            
            # Áp dụng bộ lọc
            if filters:
                if filters.get('author_id'):
                    query = query.filter(Answer.author_id == filters['author_id'])
                
                if filters.get('is_accepted') is not None:
                    query = query.filter(Answer.is_accepted == filters['is_accepted'])
                
                if filters.get('question_id'):
                    query = query.filter(Answer.question_id == filters['question_id'])
            
            # Sắp xếp theo độ liên quan
            query = query.order_by(
                desc(Answer.is_accepted),
                desc(Answer.created_at)
            )
            
            total = query.count()
            answers = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [answer.to_dict() for answer in answers],
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
    
    def get_recent_answers(self, limit=10):
        """
        Lấy câu trả lời gần đây
        
        Args:
            limit: Số lượng câu trả lời
            
        Returns:
            List[Answer]: Danh sách câu trả lời gần đây
        """
        try:
            return self.session.query(Answer).options(
                joinedload(Answer.author),
                joinedload(Answer.question)
            ).order_by(desc(Answer.created_at)).limit(limit).all()
        except SQLAlchemyError as e:
            raise e
    
    def get_answers_by_user_for_question(self, user_id, question_id):
        """
        Lấy câu trả lời của user cho một câu hỏi cụ thể
        
        Args:
            user_id: ID người dùng
            question_id: ID câu hỏi
            
        Returns:
            List[Answer]: Danh sách câu trả lời
        """
        try:
            return self.session.query(Answer).filter(
                and_(
                    Answer.author_id == user_id,
                    Answer.question_id == question_id
                )
            ).order_by(desc(Answer.created_at)).all()
        except SQLAlchemyError as e:
            raise e
    
    def create_answer(self, question_id, author_id, content, attachment_url=None):
        """
        Tạo câu trả lời mới
        
        Args:
            question_id: ID câu hỏi
            author_id: ID tác giả
            content: Nội dung câu trả lời
            attachment_url: URL file đính kèm (optional)
            
        Returns:
            Answer: Câu trả lời vừa được tạo
            
        Raises:
            SQLAlchemyError: Lỗi database
        """
        try:
            answer = Answer(
                content=content,
                question_id=question_id,
                author_id=author_id,
                attachment_url=attachment_url
            )
            
            self.session.add(answer)
            self.session.commit()
            
            # Refresh to get all relationships loaded
            self.session.refresh(answer)
            
            return answer
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    