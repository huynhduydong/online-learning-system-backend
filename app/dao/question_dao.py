"""
Question DAO - Data Access Object cho Question model
Chịu trách nhiệm tất cả database operations liên quan đến Question
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, desc, asc, func, text

from app.dao.base_dao import BaseDAO
from app.models.qa import Question
from app.models.tag import Tag, QuestionTag
from app.models.vote import Vote
from app.models.answer import Answer
from app.models.comment import Comment
from app import db


class QuestionDAO(BaseDAO):
    """
    QuestionDAO class cung cấp các phương thức database operations cho Question model
    """
    
    def __init__(self):
        super().__init__(Question)
    
    def get_questions_with_pagination(self, page=1, per_page=20, filters=None, sort_by='newest', sort_order='desc', user_id=None):
        """
        Lấy danh sách câu hỏi với phân trang và lọc
        
        Args:
            page: Số trang
            per_page: Số câu hỏi mỗi trang
            filters: Bộ lọc
            sort_by: Sắp xếp theo
            sort_order: Thứ tự sắp xếp (asc/desc)
            user_id: ID người dùng hiện tại
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            query = self.session.query(Question).options(
                joinedload(Question.author),
                joinedload(Question.question_tags),
                joinedload(Question.answers)
            )
            
            # Áp dụng bộ lọc
            if filters:
                query = self._apply_filters(query, filters)
            
            # Áp dụng sắp xếp
            query = self._apply_sorting(query, sort_by, sort_order)
            
            # Phân trang
            total = query.count()
            questions = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [q.to_dict() for q in questions],
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                }
            }
        except SQLAlchemyError as e:
            raise e
    
    def _apply_filters(self, query, filters):
        """Áp dụng các bộ lọc cho query"""
        
        # Lọc theo trạng thái
        if filters.get('status'):
            query = query.filter(Question.status == filters['status'])
        
        # Lọc theo danh mục
        if filters.get('category'):
            query = query.filter(Question.category == filters['category'])
        
        # Lọc theo phạm vi
        if filters.get('scope'):
            query = query.filter(Question.scope == filters['scope'])
        
        # Lọc theo tác giả
        if filters.get('author_id'):
            query = query.filter(Question.author_id == filters['author_id'])
        
        # Lọc theo tag
        if filters.get('tags'):
            tag_names = filters['tags'].split(',') if isinstance(filters['tags'], str) else filters['tags']
            query = query.join(QuestionTag).join(Tag).filter(Tag.name.in_(tag_names))
        
        # Lọc theo từ khóa tìm kiếm
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Question.title.ilike(search_term),
                    Question.content.ilike(search_term)
                )
            )
        
        # Lọc theo trạng thái có câu trả lời
        if filters.get('has_answers') is not None:
            if filters['has_answers']:
                query = query.filter(Question.answer_count > 0)
            else:
                query = query.filter(Question.answer_count == 0)
        
        # Lọc theo trạng thái đã được giải quyết
        if filters.get('is_resolved') is not None:
            if filters['is_resolved']:
                query = query.filter(Question.accepted_answer_id.isnot(None))
            else:
                query = query.filter(Question.accepted_answer_id.is_(None))
        
        # Lọc theo câu hỏi được ghim
        if filters.get('is_pinned') is not None:
            query = query.filter(Question.is_pinned == filters['is_pinned'])
        
        # Lọc theo câu hỏi nổi bật
        if filters.get('is_featured') is not None:
            query = query.filter(Question.is_featured == filters['is_featured'])
        
        return query
    
    def _apply_sorting(self, query, sort_by, sort_order='desc'):
        """Áp dụng sắp xếp cho query"""
        
        # Determine sort direction
        order_func = desc if sort_order == 'desc' else asc
        
        if sort_by == 'newest' or sort_by == 'created_at':
            return query.order_by(order_func(Question.created_at))
        elif sort_by == 'oldest':
            return query.order_by(asc(Question.created_at))
        elif sort_by == 'most_votes' or sort_by == 'votes':
            return query.order_by(desc(Question.vote_score))
        elif sort_by == 'most_answers' or sort_by == 'answers':
            return query.order_by(desc(Question.answer_count))
        elif sort_by == 'most_views' or sort_by == 'views':
            return query.order_by(desc(Question.view_count))
        elif sort_by == 'recent_activity' or sort_by == 'activity':
            return query.order_by(desc(Question.last_activity_at))
        elif sort_by == 'unanswered':
            return query.filter(Question.answer_count == 0).order_by(desc(Question.created_at))
        else:
            # Mặc định sắp xếp theo ghim và hoạt động gần đây
            return query.order_by(
                desc(Question.is_pinned),
                desc(Question.last_activity_at)
            )
    
    def get_question_by_id(self, question_id, include_deleted=False):
        """
        Lấy câu hỏi theo ID với đầy đủ thông tin
        
        Args:
            question_id: ID câu hỏi
            include_deleted: Có bao gồm câu hỏi đã xóa không
            
        Returns:
            Question hoặc None
        """
        try:
            query = self.session.query(Question).filter(Question.id == question_id)
            
            if not include_deleted:
                query = query.filter(Question.status != 'deleted')
            
            question = query.first()
            if question:
                return question.to_dict()
            return None
        except SQLAlchemyError as e:
            raise e
    
    def search_questions(self, search_term, filters=None, page=1, per_page=20):
        """
        Tìm kiếm câu hỏi theo từ khóa
        
        Args:
            search_term: Từ khóa tìm kiếm
            filters: Bộ lọc bổ sung
            page: Số trang
            per_page: Số câu hỏi mỗi trang
            
        Returns:
            dict: Kết quả tìm kiếm
        """
        try:
            # Tìm kiếm full-text
            search_pattern = f"%{search_term}%"
            
            query = self.session.query(Question).options(
                joinedload(Question.author),
                joinedload(Question.question_tags)
            ).filter(
                or_(
                    Question.title.ilike(search_pattern),
                    Question.content.ilike(search_pattern)
                )
            )
            
            # Áp dụng bộ lọc bổ sung
            if filters:
                query = self._apply_filters(query, filters)
            
            # Sắp xếp theo độ liên quan (có thể cải thiện bằng full-text search)
            query = query.order_by(
                desc(Question.is_pinned),
                desc(Question.vote_score),
                desc(Question.last_activity_at)
            )
            
            total = query.count()
            questions = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [q.to_dict() for q in questions],
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
    
    def get_related_questions(self, question_id, limit=5):
        """
        Lấy các câu hỏi liên quan
        
        Args:
            question_id: ID câu hỏi gốc
            limit: Số lượng câu hỏi liên quan
            
        Returns:
            List[Question]: Danh sách câu hỏi liên quan
        """
        try:
            # Lấy câu hỏi gốc để biết tags
            original_question = self.get_by_id(question_id)
            if not original_question:
                return []
            
            # Lấy tag IDs của câu hỏi gốc
            tag_ids = [qt.tag.id for qt in original_question.question_tags]
            
            if not tag_ids:
                # Nếu không có tag, lấy câu hỏi cùng category
                return self.session.query(Question).filter(
                    and_(
                        Question.id != question_id,
                        Question.category == original_question.category,
                        Question.status == 'open'
                    )
                ).order_by(desc(Question.vote_score)).limit(limit).all()
            
            # Tìm câu hỏi có chung tag
            related_questions = self.session.query(Question).join(QuestionTag).filter(
                and_(
                    Question.id != question_id,
                    QuestionTag.tag_id.in_(tag_ids),
                    Question.status == 'open'
                )
            ).group_by(Question.id).order_by(
                desc(func.count(QuestionTag.tag_id)),  # Ưu tiên câu hỏi có nhiều tag chung
                desc(Question.vote_score)
            ).limit(limit).all()
            
            return related_questions
        except SQLAlchemyError as e:
            raise e
    
    def get_user_questions(self, user_id, page=1, per_page=20, status=None):
        """
        Lấy danh sách câu hỏi của user
        
        Args:
            user_id: ID người dùng
            page: Số trang
            per_page: Số câu hỏi mỗi trang
            status: Trạng thái câu hỏi
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            query = self.session.query(Question).options(
                joinedload(Question.question_tags)
            ).filter(Question.author_id == user_id)
            
            if status:
                query = query.filter(Question.status == status)
            
            query = query.order_by(desc(Question.created_at))
            
            total = query.count()
            questions = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [q.to_dict() for q in questions],
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                }
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_trending_questions(self, days=7, limit=10):
        """
        Lấy câu hỏi trending trong khoảng thời gian
        
        Args:
            days: Số ngày gần đây
            limit: Số lượng câu hỏi
            
        Returns:
            List[Question]: Danh sách câu hỏi trending
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            return self.session.query(Question).options(
                joinedload(Question.author),
                joinedload(Question.question_tags)
            ).filter(
                and_(
                    Question.created_at >= since_date,
                    Question.status == 'open'
                )
            ).order_by(
                desc(Question.vote_score + Question.view_count + Question.answer_count * 2)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            raise e
    
    def get_question_statistics(self, question_id):
        """
        Lấy thống kê của câu hỏi
        
        Args:
            question_id: ID câu hỏi
            
        Returns:
            dict: Thống kê câu hỏi
        """
        try:
            question = self.get_by_id(question_id)
            if not question:
                return None
            
            # Đếm votes
            upvotes = self.session.query(Vote).filter(
                and_(
                    Vote.votable_type == 'question',
                    Vote.votable_id == question_id,
                    Vote.vote_type == 'upvote'
                )
            ).count()
            
            downvotes = self.session.query(Vote).filter(
                and_(
                    Vote.votable_type == 'question',
                    Vote.votable_id == question_id,
                    Vote.vote_type == 'downvote'
                )
            ).count()
            
            # Đếm comments
            comments_count = self.session.query(Comment).filter(
                and_(
                    Comment.commentable_type == 'question',
                    Comment.commentable_id == question_id
                )
            ).count()
            
            return {
                'questionId': question_id,
                'viewCount': question.view_count,
                'voteScore': question.vote_score,
                'upvotes': upvotes,
                'downvotes': downvotes,
                'answerCount': question.answer_count,
                'commentsCount': comments_count,
                'createdAt': question.created_at.isoformat() if question.created_at else None,
                'lastActivityAt': question.last_activity_at.isoformat() if question.last_activity_at else None
            }
        except SQLAlchemyError as e:
            raise e
    
    def update_question_activity(self, question_id):
        """
        Cập nhật thời gian hoạt động cuối của câu hỏi
        
        Args:
            question_id: ID câu hỏi
        """
        try:
            self.session.query(Question).filter(Question.id == question_id).update({
                'last_activity_at': datetime.utcnow()
            })
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def increment_view_count(self, question_id):
        """
        Tăng số lượt xem câu hỏi
        
        Args:
            question_id: ID câu hỏi
        """
        try:
            self.session.query(Question).filter(Question.id == question_id).update({
                'view_count': Question.view_count + 1
            })
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def update_answer_count(self, question_id):
        """
        Cập nhật số lượng câu trả lời
        
        Args:
            question_id: ID câu hỏi
        """
        try:
            answer_count = self.session.query(Answer).filter(Answer.question_id == question_id).count()
            
            self.session.query(Question).filter(Question.id == question_id).update({
                'answer_count': answer_count,
                'last_activity_at': datetime.utcnow()
            })
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def create_question(self, title, content, author_id, category=None, scope='course', scope_id=None, course_id=None, lesson_id=None):
        """
        Tạo câu hỏi mới
        
        Args:
            title: Tiêu đề câu hỏi
            content: Nội dung câu hỏi
            author_id: ID tác giả
            category: Danh mục (default: 'general')
            scope: Phạm vi (default: 'course')
            scope_id: ID của scope (default: course_id hoặc 0)
            course_id: ID khóa học (optional)
            lesson_id: ID bài học (optional)
            
        Returns:
            Question: Instance câu hỏi được tạo
        """
        try:
            # Set default values for required fields
            if not category:
                category = 'general'
            if not scope_id:
                scope_id = course_id if course_id else 0
                
            question = Question(
                title=title,
                content=content,
                author_id=author_id,
                category=category,
                scope=scope,
                scope_id=scope_id,
                status='new',
                view_count=0,
                is_pinned=False,
                is_featured=False
            )
            
            self.session.add(question)
            self.session.commit()
            return question
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e