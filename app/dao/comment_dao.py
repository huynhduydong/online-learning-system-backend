"""
Comment DAO - Data Access Object cho Comment model
Chịu trách nhiệm tất cả database operations liên quan đến Comment
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, desc, asc, func

from app.dao.base_dao import BaseDAO
from app.models.comment import Comment, CommentMention
from app.models.qa import Question
from app.models.answer import Answer
from app import db


class CommentDAO(BaseDAO):
    """
    CommentDAO class cung cấp các phương thức database operations cho Comment model
    """
    
    def __init__(self):
        super().__init__(Comment)
    
    def get_comments_by_item(self, commentable_type, commentable_id, page=1, per_page=20, sort_by='oldest'):
        """
        Lấy danh sách comment của một item
        
        Args:
            commentable_type: Loại item (question, answer)
            commentable_id: ID của item
            page: Số trang
            per_page: Số comment mỗi trang
            sort_by: Sắp xếp theo (oldest, newest)
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            query = self.session.query(Comment).options(
                joinedload(Comment.author)
            ).filter(
                and_(
                    Comment.commentable_type == commentable_type,
                    Comment.commentable_id == commentable_id,
                    Comment.parent_id.is_(None)  # Chỉ lấy comment gốc
                )
            )
            
            # Sắp xếp
            if sort_by == 'newest':
                query = query.order_by(desc(Comment.created_at))
            else:  # oldest (mặc định)
                query = query.order_by(asc(Comment.created_at))
            
            total = query.count()
            comments = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Lấy replies cho mỗi comment
            comment_data = []
            for comment in comments:
                comment_dict = comment.to_dict()
                comment_dict['replies'] = self._get_comment_replies(comment.id)
                comment_data.append(comment_dict)
            
            return {
                'data': comment_data,
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                }
            }
        except SQLAlchemyError as e:
            raise e
    
    def _get_comment_replies(self, parent_id, limit=10):
        """
        Lấy replies của một comment
        
        Args:
            parent_id: ID comment cha
            limit: Số lượng reply tối đa
            
        Returns:
            List: Danh sách reply
        """
        try:
            replies = self.session.query(Comment).options(
                joinedload(Comment.author)
            ).filter(Comment.parent_id == parent_id).order_by(
                asc(Comment.created_at)
            ).limit(limit).all()
            
            return [reply.to_dict() for reply in replies]
        except SQLAlchemyError as e:
            raise e
    
    def get_comment_by_id(self, comment_id, include_replies=True):
        """
        Lấy comment theo ID
        
        Args:
            comment_id: ID comment
            include_replies: Có bao gồm replies không
            
        Returns:
            dict hoặc None
        """
        try:
            comment = self.session.query(Comment).options(
                joinedload(Comment.author)
            ).filter(Comment.id == comment_id).first()
            
            if not comment:
                return None
            
            comment_dict = comment.to_dict()
            
            if include_replies and not comment.parent_id:  # Chỉ lấy replies cho comment gốc
                comment_dict['replies'] = self._get_comment_replies(comment.id)
            
            return comment_dict
        except SQLAlchemyError as e:
            raise e
    
    def create_comment(self, author_id, commentable_type, commentable_id, content, parent_id=None, mentions=None):
        """
        Tạo comment mới
        
        Args:
            author_id: ID tác giả
            commentable_type: Loại item
            commentable_id: ID item
            content: Nội dung comment
            parent_id: ID comment cha (nếu là reply)
            mentions: Danh sách user được mention
            
        Returns:
            Comment: Comment được tạo
        """
        try:
            comment = Comment(
                author_id=author_id,
                commentable_type=commentable_type,
                commentable_id=commentable_id,
                content=content,
                parent_id=parent_id
            )
            
            self.session.add(comment)
            self.session.flush()  # Để lấy ID
            
            # Thêm mentions nếu có
            if mentions:
                for user_id in mentions:
                    mention = CommentMention(
                        comment_id=comment.id,
                        mentioned_user_id=user_id
                    )
                    self.session.add(mention)
            
            self.session.commit()
            
            # Cập nhật comment count
            self._update_comment_count(commentable_type, commentable_id)
            
            return comment
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def update_comment(self, comment_id, content, author_id):
        """
        Cập nhật comment
        
        Args:
            comment_id: ID comment
            content: Nội dung mới
            author_id: ID tác giả (để kiểm tra quyền)
            
        Returns:
            bool: True nếu thành công
        """
        try:
            comment = self.session.query(Comment).filter(Comment.id == comment_id).first()
            
            if not comment:
                return False
            
            # Kiểm tra quyền sửa (chỉ tác giả)
            if comment.author_id != author_id:
                return False
            
            comment.content = content
            comment.updated_at = datetime.utcnow()
            
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def delete_comment(self, comment_id, author_id):
        """
        Xóa comment
        
        Args:
            comment_id: ID comment
            author_id: ID tác giả (để kiểm tra quyền)
            
        Returns:
            bool: True nếu thành công
        """
        try:
            comment = self.session.query(Comment).filter(Comment.id == comment_id).first()
            
            if not comment:
                return False
            
            # Kiểm tra quyền xóa (chỉ tác giả)
            if comment.author_id != author_id:
                return False
            
            commentable_type = comment.commentable_type
            commentable_id = comment.commentable_id
            
            # Xóa mentions liên quan
            self.session.query(CommentMention).filter(
                CommentMention.comment_id == comment_id
            ).delete()
            
            # Xóa replies nếu có
            self.session.query(Comment).filter(Comment.parent_id == comment_id).delete()
            
            # Xóa comment
            self.session.delete(comment)
            self.session.commit()
            
            # Cập nhật comment count
            self._update_comment_count(commentable_type, commentable_id)
            
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def _update_comment_count(self, commentable_type, commentable_id):
        """
        Cập nhật số lượng comment
        
        Args:
            commentable_type: Loại item
            commentable_id: ID item
        """
        try:
            comment_count = self.session.query(Comment).filter(
                and_(
                    Comment.commentable_type == commentable_type,
                    Comment.commentable_id == commentable_id
                )
            ).count()
            
            if commentable_type == 'question':
                self.session.query(Question).filter(Question.id == commentable_id).update({
                    'comment_count': comment_count
                })
            elif commentable_type == 'answer':
                self.session.query(Answer).filter(Answer.id == commentable_id).update({
                    'comment_count': comment_count
                })
            
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def get_user_comments(self, user_id, page=1, per_page=20):
        """
        Lấy danh sách comment của user
        
        Args:
            user_id: ID người dùng
            page: Số trang
            per_page: Số comment mỗi trang
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            query = self.session.query(Comment).filter(
                Comment.author_id == user_id
            ).order_by(desc(Comment.created_at))
            
            total = query.count()
            comments = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Lấy thông tin chi tiết của item được comment
            comment_data = []
            for comment in comments:
                comment_dict = comment.to_dict()
                
                # Lấy thông tin item được comment
                if comment.commentable_type == 'question':
                    item = self.session.query(Question).filter(Question.id == comment.commentable_id).first()
                    if item:
                        comment_dict['item'] = {
                            'id': item.id,
                            'title': item.title,
                            'type': 'question'
                        }
                elif comment.commentable_type == 'answer':
                    item = self.session.query(Answer).options(
                        joinedload(Answer.question)
                    ).filter(Answer.id == comment.commentable_id).first()
                    if item:
                        comment_dict['item'] = {
                            'id': item.id,
                            'content': item.content[:100] + '...' if len(item.content) > 100 else item.content,
                            'type': 'answer',
                            'questionTitle': item.question.title if item.question else None
                        }
                
                comment_data.append(comment_dict)
            
            return {
                'data': comment_data,
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                }
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_recent_comments(self, limit=10):
        """
        Lấy comment gần đây
        
        Args:
            limit: Số lượng comment
            
        Returns:
            List[Comment]: Danh sách comment gần đây
        """
        try:
            return self.session.query(Comment).options(
                joinedload(Comment.author)
            ).order_by(desc(Comment.created_at)).limit(limit).all()
        except SQLAlchemyError as e:
            raise e
    
    def search_comments(self, search_term, filters=None, page=1, per_page=20):
        """
        Tìm kiếm comment theo từ khóa
        
        Args:
            search_term: Từ khóa tìm kiếm
            filters: Bộ lọc bổ sung
            page: Số trang
            per_page: Số comment mỗi trang
            
        Returns:
            dict: Kết quả tìm kiếm
        """
        try:
            search_pattern = f"%{search_term}%"
            
            query = self.session.query(Comment).options(
                joinedload(Comment.author)
            ).filter(
                Comment.content.ilike(search_pattern)
            )
            
            # Áp dụng bộ lọc
            if filters:
                if filters.get('author_id'):
                    query = query.filter(Comment.author_id == filters['author_id'])
                
                if filters.get('commentable_type'):
                    query = query.filter(Comment.commentable_type == filters['commentable_type'])
                
                if filters.get('commentable_id'):
                    query = query.filter(Comment.commentable_id == filters['commentable_id'])
            
            query = query.order_by(desc(Comment.created_at))
            
            total = query.count()
            comments = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [comment.to_dict() for comment in comments],
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
    
    def get_comment_mentions(self, user_id, page=1, per_page=20):
        """
        Lấy danh sách comment mà user được mention
        
        Args:
            user_id: ID người dùng
            page: Số trang
            per_page: Số comment mỗi trang
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            query = self.session.query(Comment).join(CommentMention).options(
                joinedload(Comment.author)
            ).filter(
                CommentMention.mentioned_user_id == user_id
            ).order_by(desc(Comment.created_at))
            
            total = query.count()
            comments = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [comment.to_dict() for comment in comments],
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                }
            }
        except SQLAlchemyError as e:
            raise e