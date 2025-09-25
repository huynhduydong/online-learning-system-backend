"""
Question Service
Business logic for Q&A questions management
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.dao.question_dao import QuestionDAO
from app.dao.tag_dao import TagDAO
from app.dao.vote_dao import VoteDAO
from app.dao.comment_dao import CommentDAO
from app.models.qa import Question
from app.models.tag import Tag
from app.exceptions.base import ValidationException, BusinessLogicException
from app import db

# Setup logging
logger = logging.getLogger(__name__)


class QuestionService:
    """Service class cho question operations"""
    
    def __init__(self):
        self.question_dao = QuestionDAO()
        self.tag_dao = TagDAO()
        self.vote_dao = VoteDAO()
        self.comment_dao = CommentDAO()
    
    def get_questions(self, page=1, per_page=20, sort_by='newest', sort_order='desc', filters=None, user_id=None):
        """
        Lấy danh sách câu hỏi với phân trang và lọc
        
        Args:
            page: Số trang
            per_page: Số câu hỏi mỗi trang
            sort_by: Sắp xếp theo
            sort_order: Thứ tự sắp xếp (asc/desc)
            filters: Bộ lọc
            user_id: ID người dùng hiện tại
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Validate sort
            valid_sorts = ['newest', 'oldest', 'votes', 'views', 'answers', 'activity']
            if sort_by not in valid_sorts:
                sort_by = 'newest'
            
            # Process filters
            processed_filters = self._process_filters(filters or {})
            
            # Get questions from DAO
            result = self.question_dao.get_questions_with_pagination(
                page=page,
                per_page=per_page,
                filters=processed_filters,
                sort_by=sort_by,
                sort_order=sort_order,
                user_id=user_id
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy danh sách câu hỏi: {str(e)}")
    
    def get_question_by_id(self, question_id, user_id=None):
        """
        Lấy chi tiết câu hỏi theo ID
        
        Args:
            question_id: ID câu hỏi
            user_id: ID người dùng (để kiểm tra quyền)
            
        Returns:
            dict: Chi tiết câu hỏi
        """
        try:
            question = self.question_dao.get_question_by_id(question_id)
            
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            # Tăng view count nếu không phải tác giả
            if user_id != question['author']['id']:
                self.question_dao.increment_view_count(question_id)
                question['viewCount'] += 1
            
            # Lấy thông tin vote của user
            if user_id:
                user_vote = self.vote_dao.get_user_vote(user_id, 'question', question_id)
                question['userVote'] = user_vote.vote_type if user_vote else None
            else:
                question['userVote'] = None
            
            # Lấy tag của question
            tags = self.tag_dao.get_question_tags(question_id)
            question['tags'] = [tag.to_dict() for tag in tags]
            
            return {
                'success': True,
                'data': question
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy chi tiết câu hỏi: {str(e)}")
    
    def create_question(self, user_id, data):
        """
        Tạo câu hỏi mới
        
        Args:
            user_id: ID người tạo
            data: Dữ liệu câu hỏi
            
        Returns:
            dict: Câu hỏi được tạo
        """
        try:
            logger.info(f"🚀 Starting create_question - user_id: {user_id}, data: {data}")
            
            # Validate required fields
            logger.info("📝 Validating question data...")
            self._validate_question_data(data)
            logger.info("✅ Question data validation passed")
            
            # Create question
            logger.info("💾 Creating question in database...")
            logger.info(f"📋 Question params - title: {data['title']}, content length: {len(data['content'])}, author_id: {user_id}")
            logger.info(f"📋 Optional params - category: {data.get('category')}, scope: {data.get('scope', 'lesson')}, scope_id: {data.get('scope_id', 0)}")
            
            question = self.question_dao.create_question(
                title=data['title'],
                content=data['content'],
                author_id=user_id,
                category=data.get('category'),
                scope=data.get('scope', 'lesson'),
                scope_id=data.get('scope_id', 0)
            )
            logger.info(f"✅ Question created successfully with ID: {question.id}")

            # Add tags if provided
            if data.get('tags'):
                logger.info(f"🏷️ Processing tags: {data['tags']}")
                self._process_question_tags(question.id, data['tags'])
                logger.info("✅ Tags processed successfully")

            # Get formatted question data
            logger.info("📊 Getting formatted question data...")
            question_data = self.question_dao.get_question_by_id(question.id)
            logger.info("✅ Question data retrieved successfully")

            result = {
                'success': True,
                'data': question_data,
                'message': 'Câu hỏi đã được tạo thành công'
            }
            logger.info(f"🎉 create_question completed successfully: {result}")
            return result
            
        except ValidationException as ve:
            logger.error(f"❌ ValidationException in create_question: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"💥 Unexpected error in create_question: {str(e)}")
            logger.error(f"🔍 Error type: {type(e).__name__}")
            import traceback
            logger.error(f"📚 Full traceback: {traceback.format_exc()}")
            db.session.rollback()
            raise ValidationException(f"Lỗi khi tạo câu hỏi: {str(e)}")
    
    def update_question(self, question_id, user_id, data):
        """
        Cập nhật câu hỏi
        
        Args:
            question_id: ID câu hỏi
            user_id: ID người cập nhật
            data: Dữ liệu mới
            
        Returns:
            dict: Câu hỏi đã cập nhật
        """
        try:
            # Check permission
            question = self.question_dao.get_question_by_id(question_id)
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            if question['author']['id'] != user_id:
                raise ValidationException("Bạn không có quyền chỉnh sửa câu hỏi này")
            
            # Validate data
            self._validate_question_data(data, is_update=True)
            
            # Update question
            updated = self.question_dao.update_question(
                question_id=question_id,
                title=data.get('title'),
                content=data.get('content'),
                category=data.get('category')
            )
            
            if not updated:
                raise ValidationException("Không thể cập nhật câu hỏi")
            
            # Update tags if provided
            if 'tags' in data:
                self._process_question_tags(question_id, data['tags'])
            
            # Get updated question data
            question_data = self.question_dao.get_question_by_id(question_id)
            
            return {
                'success': True,
                'data': question_data,
                'message': 'Câu hỏi đã được cập nhật thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi cập nhật câu hỏi: {str(e)}")
    
    def delete_question(self, question_id, user_id):
        """
        Xóa câu hỏi
        
        Args:
            question_id: ID câu hỏi
            user_id: ID người xóa
            
        Returns:
            dict: Kết quả xóa
        """
        try:
            # Check permission
            question = self.question_dao.get_question_by_id(question_id)
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            if question['author']['id'] != user_id:
                raise ValidationException("Bạn không có quyền xóa câu hỏi này")
            
            # Delete question
            deleted = self.question_dao.delete_question(question_id)
            
            if not deleted:
                raise ValidationException("Không thể xóa câu hỏi")
            
            return {
                'success': True,
                'message': 'Câu hỏi đã được xóa thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi xóa câu hỏi: {str(e)}")
    
    def vote_question(self, question_id, user_id, vote_type):
        """
        Vote cho câu hỏi
        
        Args:
            question_id: ID câu hỏi
            user_id: ID người vote
            vote_type: Loại vote (upvote, downvote)
            
        Returns:
            dict: Kết quả vote
        """
        try:
            # Validate vote type
            if vote_type not in ['upvote', 'downvote']:
                raise ValidationException("Loại vote không hợp lệ")
            
            # Check if question exists
            question = self.question_dao.get_question_by_id(question_id)
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            # Check if user is not the author
            if question['author']['id'] == user_id:
                raise ValidationException("Bạn không thể vote cho câu hỏi của chính mình")
            
            # Cast vote
            vote = self.vote_dao.cast_vote(user_id, 'question', question_id, vote_type)
            
            # Get updated vote score
            vote_score = self.vote_dao.get_vote_score('question', question_id)
            
            return {
                'success': True,
                'data': {
                    'voteScore': vote_score,
                    'userVote': vote.vote_type if vote else None
                },
                'message': f'Đã {vote_type} câu hỏi'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi vote câu hỏi: {str(e)}")
    
    def search_questions(self, search_term, page=1, per_page=20, filters=None):
        """
        Tìm kiếm câu hỏi
        
        Args:
            search_term: Từ khóa tìm kiếm
            page: Số trang
            per_page: Số câu hỏi mỗi trang
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
            
            # Search questions
            result = self.question_dao.search_questions(
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
            raise ValidationException(f"Lỗi khi tìm kiếm câu hỏi: {str(e)}")
    
    def get_user_questions(self, user_id, page=1, per_page=20):
        """
        Lấy danh sách câu hỏi của user
        
        Args:
            user_id: ID người dùng
            page: Số trang
            per_page: Số câu hỏi mỗi trang
            
        Returns:
            dict: Danh sách câu hỏi của user
        """
        try:
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Get user questions
            result = self.question_dao.get_user_questions(
                user_id=user_id,
                page=page,
                per_page=per_page
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy câu hỏi của người dùng: {str(e)}")
    
    def get_trending_questions(self, limit=10, time_frame='week'):
        """
        Lấy câu hỏi trending
        
        Args:
            limit: Số lượng câu hỏi
            time_frame: Khung thời gian (day, week, month)
            
        Returns:
            dict: Danh sách câu hỏi trending
        """
        try:
            questions = self.question_dao.get_trending_questions(
                limit=limit,
                time_frame=time_frame
            )
            
            return {
                'success': True,
                'data': [q.to_dict() for q in questions]
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy câu hỏi trending: {str(e)}")
    
    def get_related_questions(self, question_id, limit=5):
        """
        Lấy câu hỏi liên quan
        
        Args:
            question_id: ID câu hỏi
            limit: Số lượng câu hỏi liên quan
            
        Returns:
            dict: Danh sách câu hỏi liên quan
        """
        try:
            questions = self.question_dao.get_related_questions(
                question_id=question_id,
                limit=limit
            )
            
            return {
                'success': True,
                'data': [q.to_dict() for q in questions]
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy câu hỏi liên quan: {str(e)}")
    
    def _validate_question_data(self, data, is_update=False):
        """Validate question data"""
        errors = {}
        
        # Title validation
        if not is_update or 'title' in data:
            title = data.get('title', '').strip()
            if not title:
                errors['title'] = ['Tiêu đề không được để trống']
            elif len(title) < 10:
                errors['title'] = ['Tiêu đề phải có ít nhất 10 ký tự']
            elif len(title) > 200:
                errors['title'] = ['Tiêu đề không được quá 200 ký tự']
        
        # Content validation
        if not is_update or 'content' in data:
            content = data.get('content', '').strip()
            if not content:
                errors['content'] = ['Nội dung không được để trống']
            elif len(content) < 20:
                errors['content'] = ['Nội dung phải có ít nhất 20 ký tự']
        
        # Category validation
        if data.get('category'):
            valid_categories = ['general', 'technical', 'course', 'assignment']
            if data['category'] not in valid_categories:
                errors['category'] = ['Danh mục không hợp lệ']
        
        # Scope validation
        if data.get('scope'):
            valid_scopes = ['course', 'chapter', 'lesson', 'quiz', 'assignment']
            if data['scope'] not in valid_scopes:
                errors['scope'] = ['Phạm vi không hợp lệ. Các giá trị hợp lệ: course, chapter, lesson, quiz, assignment']
        
        if errors:
            raise ValidationException(errors)
    
    def _process_filters(self, filters):
        """Process and validate filters"""
        processed = {}
        
        if filters.get('category'):
            processed['category'] = filters['category']
        
        if filters.get('scope'):
            processed['scope'] = filters['scope']
        
        if filters.get('scope_id'):
            processed['scope_id'] = filters['scope_id']
        
        if filters.get('status'):
            processed['status'] = filters['status']
        
        if filters.get('authorId'):
            processed['author_id'] = filters['authorId']
        
        if filters.get('courseId'):
            processed['course_id'] = filters['courseId']
        
        if filters.get('tags'):
            processed['tags'] = filters['tags']
        
        if filters.get('hasAnswers') is not None:
            processed['has_answers'] = filters['hasAnswers']
        
        if filters.get('isAccepted') is not None:
            processed['is_accepted'] = filters['isAccepted']
        
        return processed
    
    def _process_question_tags(self, question_id, tag_names):
        """Process and update question tags"""
        try:
            tag_ids = []
            
            for tag_name in tag_names:
                tag_name = tag_name.strip().lower()
                if not tag_name:
                    continue
                
                # Get or create tag
                tag = self.tag_dao.get_tag_by_name(tag_name)
                if not tag:
                    tag = self.tag_dao.create_tag(tag_name)
                
                tag_ids.append(tag.id)
            
            # Update question tags
            self.tag_dao.update_question_tags(question_id, tag_ids)
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi xử lý tag: {str(e)}")