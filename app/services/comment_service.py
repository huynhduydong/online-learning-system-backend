"""
Comment Service
Business logic for comments management
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from app.dao.comment_dao import CommentDAO
from app.dao.question_dao import QuestionDAO
from app.dao.answer_dao import AnswerDAO
from app.exceptions.base import ValidationException, BusinessLogicException
from app import db


class CommentService:
    """Service class cho comment operations"""
    
    def __init__(self):
        self.comment_dao = CommentDAO()
        self.question_dao = QuestionDAO()
        self.answer_dao = AnswerDAO()
    
    def get_item_comments(self, commentable_type, commentable_id, page=1, per_page=20, sort_by='newest'):
        """
        Lấy danh sách comment của một item (question hoặc answer)
        
        Args:
            commentable_type: Loại item (question, answer)
            commentable_id: ID của item
            page: Số trang
            per_page: Số comment mỗi trang
            sort_by: Sắp xếp theo (newest, oldest)
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            # Validate commentable type
            if commentable_type not in ['question', 'answer']:
                raise ValidationException("Loại item comment không hợp lệ")
            
            # Validate item exists
            if not self._item_exists(commentable_type, commentable_id):
                raise ValidationException(f"Không tìm thấy {commentable_type}")
            
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Validate sort
            valid_sorts = ['newest', 'oldest']
            if sort_by not in valid_sorts:
                sort_by = 'newest'
            
            # Get comments from DAO
            result = self.comment_dao.get_comments_by_item(
                commentable_type=commentable_type,
                commentable_id=commentable_id,
                page=page,
                per_page=per_page,
                sort_by=sort_by
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy danh sách comment: {str(e)}")
    
    def get_comment_replies(self, parent_comment_id, page=1, per_page=20):
        """
        Lấy danh sách reply của một comment
        
        Args:
            parent_comment_id: ID comment cha
            page: Số trang
            per_page: Số reply mỗi trang
            
        Returns:
            dict: Danh sách reply
        """
        try:
            # Validate parent comment exists
            parent_comment = self.comment_dao.get_comment_by_id(parent_comment_id)
            if not parent_comment:
                raise ValidationException("Không tìm thấy comment cha")
            
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Get replies
            result = self.comment_dao.get_comment_replies(
                parent_comment_id=parent_comment_id,
                page=page,
                per_page=per_page
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy danh sách reply: {str(e)}")
    
    def get_comment_by_id(self, comment_id):
        """
        Lấy chi tiết comment theo ID
        
        Args:
            comment_id: ID comment
            
        Returns:
            dict: Chi tiết comment
        """
        try:
            comment = self.comment_dao.get_comment_by_id(comment_id)
            
            if not comment:
                raise ValidationException("Không tìm thấy comment")
            
            return {
                'success': True,
                'data': comment
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy chi tiết comment: {str(e)}")
    
    def create_comment(self, user_id, commentable_type, commentable_id, content, parent_comment_id=None):
        """
        Tạo comment mới
        
        Args:
            user_id: ID người tạo
            commentable_type: Loại item (question, answer)
            commentable_id: ID của item
            content: Nội dung comment
            parent_comment_id: ID comment cha (nếu là reply)
            
        Returns:
            dict: Comment được tạo
        """
        try:
            # Validate commentable type
            if commentable_type not in ['question', 'answer']:
                raise ValidationException("Loại item comment không hợp lệ")
            
            # Validate item exists
            if not self._item_exists(commentable_type, commentable_id):
                raise ValidationException(f"Không tìm thấy {commentable_type}")
            
            # Validate content
            self._validate_comment_content(content)
            
            # Validate parent comment if provided
            if parent_comment_id:
                parent_comment = self.comment_dao.get_comment_by_id(parent_comment_id)
                if not parent_comment:
                    raise ValidationException("Không tìm thấy comment cha")
                
                # Check if parent comment belongs to the same item
                if (parent_comment['commentableType'] != commentable_type or 
                    parent_comment['commentableId'] != commentable_id):
                    raise ValidationException("Comment cha không thuộc về item này")
            
            # Create comment
            comment = self.comment_dao.create_comment(
                author_id=user_id,
                commentable_type=commentable_type,
                commentable_id=commentable_id,
                content=content,
                parent_comment_id=parent_comment_id
            )
            
            # Update comment count for the item
            self.comment_dao.update_comment_count(commentable_type, commentable_id)
            
            # Get formatted comment data
            comment_data = self.comment_dao.get_comment_by_id(comment.id)
            
            return {
                'success': True,
                'data': comment_data,
                'message': 'Comment đã được tạo thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi tạo comment: {str(e)}")
    
    def update_comment(self, comment_id, user_id, content):
        """
        Cập nhật comment
        
        Args:
            comment_id: ID comment
            user_id: ID người cập nhật
            content: Nội dung mới
            
        Returns:
            dict: Comment đã cập nhật
        """
        try:
            # Check permission
            comment = self.comment_dao.get_comment_by_id(comment_id)
            if not comment:
                raise ValidationException("Không tìm thấy comment")
            
            if comment['author']['id'] != user_id:
                raise ValidationException("Bạn không có quyền chỉnh sửa comment này")
            
            # Validate content
            self._validate_comment_content(content)
            
            # Update comment
            updated = self.comment_dao.update_comment(comment_id, content, user_id)
            
            if not updated:
                raise ValidationException("Không thể cập nhật comment")
            
            # Get updated comment data
            comment_data = self.comment_dao.get_comment_by_id(comment_id)
            
            return {
                'success': True,
                'data': comment_data,
                'message': 'Comment đã được cập nhật thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi cập nhật comment: {str(e)}")
    
    def delete_comment(self, comment_id, user_id):
        """
        Xóa comment
        
        Args:
            comment_id: ID comment
            user_id: ID người xóa
            
        Returns:
            dict: Kết quả xóa
        """
        try:
            # Check permission
            comment = self.comment_dao.get_comment_by_id(comment_id)
            if not comment:
                raise ValidationException("Không tìm thấy comment")
            
            if comment['author']['id'] != user_id:
                raise ValidationException("Bạn không có quyền xóa comment này")
            
            # Get item info before deletion
            commentable_type = comment['commentableType']
            commentable_id = comment['commentableId']
            
            # Delete comment
            deleted = self.comment_dao.delete_comment(comment_id, user_id)
            
            if not deleted:
                raise ValidationException("Không thể xóa comment")
            
            # Update comment count for the item
            self.comment_dao.update_comment_count(commentable_type, commentable_id)
            
            return {
                'success': True,
                'message': 'Comment đã được xóa thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi xóa comment: {str(e)}")
    
    def get_user_comments(self, user_id, page=1, per_page=20, commentable_type=None):
        """
        Lấy danh sách comment của user
        
        Args:
            user_id: ID người dùng
            page: Số trang
            per_page: Số comment mỗi trang
            commentable_type: Lọc theo loại item (question, answer)
            
        Returns:
            dict: Danh sách comment của user
        """
        try:
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Validate commentable type if provided
            if commentable_type and commentable_type not in ['question', 'answer']:
                raise ValidationException("Loại item comment không hợp lệ")
            
            # Get user comments
            result = self.comment_dao.get_user_comments(
                user_id=user_id,
                page=page,
                per_page=per_page,
                commentable_type=commentable_type
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy comment của người dùng: {str(e)}")
    
    def get_recent_comments(self, limit=10, commentable_type=None):
        """
        Lấy comment gần đây
        
        Args:
            limit: Số lượng comment
            commentable_type: Lọc theo loại item (question, answer)
            
        Returns:
            dict: Danh sách comment gần đây
        """
        try:
            # Validate commentable type if provided
            if commentable_type and commentable_type not in ['question', 'answer']:
                raise ValidationException("Loại item comment không hợp lệ")
            
            comments = self.comment_dao.get_recent_comments(
                limit=limit,
                commentable_type=commentable_type
            )
            
            return {
                'success': True,
                'data': [comment.to_dict() for comment in comments]
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy comment gần đây: {str(e)}")
    
    def search_comments(self, search_term, page=1, per_page=20, filters=None):
        """
        Tìm kiếm comment
        
        Args:
            search_term: Từ khóa tìm kiếm
            page: Số trang
            per_page: Số comment mỗi trang
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
            
            # Search comments
            result = self.comment_dao.search_comments(
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
            raise ValidationException(f"Lỗi khi tìm kiếm comment: {str(e)}")
    
    def get_comment_mentions(self, comment_id):
        """
        Lấy danh sách mention trong comment
        
        Args:
            comment_id: ID comment
            
        Returns:
            dict: Danh sách mention
        """
        try:
            mentions = self.comment_dao.get_comment_mentions(comment_id)
            
            return {
                'success': True,
                'data': mentions
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy mention: {str(e)}")
    
    def add_comment_mention(self, comment_id, mentioned_user_id):
        """
        Thêm mention vào comment
        
        Args:
            comment_id: ID comment
            mentioned_user_id: ID user được mention
            
        Returns:
            dict: Kết quả thêm mention
        """
        try:
            # Validate comment exists
            comment = self.comment_dao.get_comment_by_id(comment_id)
            if not comment:
                raise ValidationException("Không tìm thấy comment")
            
            # Add mention
            mention = self.comment_dao.add_comment_mention(comment_id, mentioned_user_id)
            
            return {
                'success': True,
                'data': mention,
                'message': 'Đã thêm mention thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi thêm mention: {str(e)}")
    
    def get_comment_count(self, commentable_type, commentable_id):
        """
        Lấy số lượng comment của một item
        
        Args:
            commentable_type: Loại item (question, answer)
            commentable_id: ID của item
            
        Returns:
            dict: Số lượng comment
        """
        try:
            # Validate commentable type
            if commentable_type not in ['question', 'answer']:
                raise ValidationException("Loại item comment không hợp lệ")
            
            count = self.comment_dao.get_comment_count(commentable_type, commentable_id)
            
            return {
                'success': True,
                'data': {
                    'commentCount': count
                }
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy số lượng comment: {str(e)}")
    
    def _validate_comment_content(self, content):
        """Validate comment content"""
        if not content or not content.strip():
            raise ValidationException("Nội dung comment không được để trống")
        
        if len(content.strip()) < 3:
            raise ValidationException("Nội dung comment phải có ít nhất 3 ký tự")
        
        if len(content) > 1000:
            raise ValidationException("Nội dung comment không được quá 1,000 ký tự")
    
    def _item_exists(self, commentable_type, commentable_id):
        """
        Kiểm tra item có tồn tại không
        
        Args:
            commentable_type: Loại item (question, answer)
            commentable_id: ID của item
            
        Returns:
            bool: True nếu item tồn tại
        """
        try:
            if commentable_type == 'question':
                return self.question_dao.get_question_by_id(commentable_id) is not None
            elif commentable_type == 'answer':
                return self.answer_dao.get_answer_by_id(commentable_id) is not None
            else:
                return False
        except Exception:
            return False