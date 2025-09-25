"""
Tag DAO - Data Access Object cho Tag model
Chịu trách nhiệm tất cả database operations liên quan đến Tag
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, desc, asc, func

from app.dao.base_dao import BaseDAO
from app.models.tag import Tag, QuestionTag
from app.models.qa import Question
from app import db


class TagDAO(BaseDAO):
    """
    TagDAO class cung cấp các phương thức database operations cho Tag model
    """
    
    def __init__(self):
        super().__init__(Tag)
    
    def get_all_tags(self, page=1, per_page=50, sort_by='usage_count'):
        """
        Lấy danh sách tất cả tag
        
        Args:
            page: Số trang
            per_page: Số tag mỗi trang
            sort_by: Sắp xếp theo (usage_count, name, created_at)
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            query = self.session.query(Tag)
            
            # Sắp xếp
            if sort_by == 'name':
                query = query.order_by(asc(Tag.name))
            elif sort_by == 'created_at':
                query = query.order_by(desc(Tag.created_at))
            else:  # usage_count (mặc định)
                query = query.order_by(desc(Tag.usage_count))
            
            total = query.count()
            tags = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'data': [tag.to_dict() for tag in tags],
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': per_page,
                    'totalPages': (total + per_page - 1) // per_page
                }
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_tag_by_id(self, tag_id):
        """
        Lấy tag theo ID
        
        Args:
            tag_id: ID tag
            
        Returns:
            Tag hoặc None
        """
        try:
            return self.session.query(Tag).filter(Tag.id == tag_id).first()
        except SQLAlchemyError as e:
            raise e
    
    def get_tag_by_name(self, name):
        """
        Lấy tag theo tên
        
        Args:
            name: Tên tag
            
        Returns:
            Tag hoặc None
        """
        try:
            return self.session.query(Tag).filter(Tag.name == name).first()
        except SQLAlchemyError as e:
            raise e
    
    def create_tag(self, name, description=None, color=None):
        """
        Tạo tag mới
        
        Args:
            name: Tên tag
            description: Mô tả tag
            color: Màu sắc tag
            
        Returns:
            Tag: Tag được tạo
        """
        try:
            # Kiểm tra tag đã tồn tại chưa
            existing_tag = self.get_tag_by_name(name)
            if existing_tag:
                return existing_tag
            
            tag = Tag(
                name=name,
                description=description,
                color=color or '#007bff'  # Màu mặc định
            )
            
            self.session.add(tag)
            self.session.commit()
            
            return tag
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def update_tag(self, tag_id, name=None, description=None, color=None):
        """
        Cập nhật tag
        
        Args:
            tag_id: ID tag
            name: Tên mới
            description: Mô tả mới
            color: Màu mới
            
        Returns:
            bool: True nếu thành công
        """
        try:
            tag = self.session.query(Tag).filter(Tag.id == tag_id).first()
            
            if not tag:
                return False
            
            if name is not None:
                # Kiểm tra tên mới có trùng không
                existing_tag = self.session.query(Tag).filter(
                    and_(Tag.name == name, Tag.id != tag_id)
                ).first()
                if existing_tag:
                    return False
                tag.name = name
            
            if description is not None:
                tag.description = description
            
            if color is not None:
                tag.color = color
            
            tag.updated_at = datetime.utcnow()
            
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def delete_tag(self, tag_id):
        """
        Xóa tag
        
        Args:
            tag_id: ID tag
            
        Returns:
            bool: True nếu thành công
        """
        try:
            tag = self.session.query(Tag).filter(Tag.id == tag_id).first()
            
            if not tag:
                return False
            
            # Xóa tất cả liên kết với question
            self.session.query(QuestionTag).filter(QuestionTag.tag_id == tag_id).delete()
            
            # Xóa tag
            self.session.delete(tag)
            self.session.commit()
            
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def search_tags(self, search_term, limit=20):
        """
        Tìm kiếm tag theo tên
        
        Args:
            search_term: Từ khóa tìm kiếm
            limit: Số lượng kết quả tối đa
            
        Returns:
            List[Tag]: Danh sách tag
        """
        try:
            search_pattern = f"%{search_term}%"
            
            return self.session.query(Tag).filter(
                Tag.name.ilike(search_pattern)
            ).order_by(desc(Tag.usage_count)).limit(limit).all()
        except SQLAlchemyError as e:
            raise e
    
    def get_popular_tags(self, limit=20):
        """
        Lấy danh sách tag phổ biến
        
        Args:
            limit: Số lượng tag
            
        Returns:
            List[Tag]: Danh sách tag phổ biến
        """
        try:
            return self.session.query(Tag).filter(
                Tag.usage_count > 0
            ).order_by(desc(Tag.usage_count)).limit(limit).all()
        except SQLAlchemyError as e:
            raise e
    
    def get_question_tags(self, question_id):
        """
        Lấy danh sách tag của một question
        
        Args:
            question_id: ID question
            
        Returns:
            List[Tag]: Danh sách tag
        """
        try:
            return self.session.query(Tag).join(QuestionTag).filter(
                QuestionTag.question_id == question_id
            ).all()
        except SQLAlchemyError as e:
            raise e
    
    def add_tag_to_question(self, question_id, tag_id):
        """
        Thêm tag vào question
        
        Args:
            question_id: ID question
            tag_id: ID tag
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Kiểm tra liên kết đã tồn tại chưa
            existing = self.session.query(QuestionTag).filter(
                and_(
                    QuestionTag.question_id == question_id,
                    QuestionTag.tag_id == tag_id
                )
            ).first()
            
            if existing:
                return True  # Đã tồn tại
            
            # Tạo liên kết mới
            question_tag = QuestionTag(
                question_id=question_id,
                tag_id=tag_id
            )
            
            self.session.add(question_tag)
            
            # Tăng usage_count của tag
            self.session.query(Tag).filter(Tag.id == tag_id).update({
                'usage_count': Tag.usage_count + 1
            })
            
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def remove_tag_from_question(self, question_id, tag_id):
        """
        Xóa tag khỏi question
        
        Args:
            question_id: ID question
            tag_id: ID tag
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Xóa liên kết
            deleted = self.session.query(QuestionTag).filter(
                and_(
                    QuestionTag.question_id == question_id,
                    QuestionTag.tag_id == tag_id
                )
            ).delete()
            
            if deleted > 0:
                # Giảm usage_count của tag
                tag = self.session.query(Tag).filter(Tag.id == tag_id).first()
                if tag and tag.usage_count > 0:
                    tag.usage_count -= 1
            
            self.session.commit()
            return deleted > 0
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def update_question_tags(self, question_id, tag_ids):
        """
        Cập nhật toàn bộ tag của question
        
        Args:
            question_id: ID question
            tag_ids: Danh sách ID tag mới
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Lấy tag hiện tại
            current_tags = self.session.query(QuestionTag.tag_id).filter(
                QuestionTag.question_id == question_id
            ).all()
            current_tag_ids = [tag.tag_id for tag in current_tags]
            
            # Tag cần thêm
            tags_to_add = set(tag_ids) - set(current_tag_ids)
            
            # Tag cần xóa
            tags_to_remove = set(current_tag_ids) - set(tag_ids)
            
            # Xóa tag cũ
            for tag_id in tags_to_remove:
                self.remove_tag_from_question(question_id, tag_id)
            
            # Thêm tag mới
            for tag_id in tags_to_add:
                self.add_tag_to_question(question_id, tag_id)
            
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def get_tag_statistics(self, tag_id):
        """
        Lấy thống kê của tag
        
        Args:
            tag_id: ID tag
            
        Returns:
            dict: Thống kê tag
        """
        try:
            tag = self.session.query(Tag).filter(Tag.id == tag_id).first()
            
            if not tag:
                return None
            
            # Số lượng question sử dụng tag
            question_count = self.session.query(QuestionTag).filter(
                QuestionTag.tag_id == tag_id
            ).count()
            
            # Lấy question gần đây nhất
            recent_questions = self.session.query(Question).join(QuestionTag).filter(
                QuestionTag.tag_id == tag_id
            ).order_by(desc(Question.created_at)).limit(5).all()
            
            return {
                'tag': tag.to_dict(),
                'questionCount': question_count,
                'recentQuestions': [q.to_dict() for q in recent_questions]
            }
        except SQLAlchemyError as e:
            raise e
    
    def get_related_tags(self, tag_id, limit=10):
        """
        Lấy tag liên quan (tag thường xuất hiện cùng)
        
        Args:
            tag_id: ID tag
            limit: Số lượng tag liên quan
            
        Returns:
            List[Tag]: Danh sách tag liên quan
        """
        try:
            # Lấy question có tag này
            question_ids = self.session.query(QuestionTag.question_id).filter(
                QuestionTag.tag_id == tag_id
            ).subquery()
            
            # Lấy tag khác xuất hiện trong các question đó
            related_tags = self.session.query(
                Tag,
                func.count(QuestionTag.question_id).label('frequency')
            ).join(QuestionTag).filter(
                and_(
                    QuestionTag.question_id.in_(question_ids),
                    QuestionTag.tag_id != tag_id
                )
            ).group_by(Tag.id).order_by(
                desc('frequency')
            ).limit(limit).all()
            
            return [tag for tag, frequency in related_tags]
        except SQLAlchemyError as e:
            raise e
    
    def get_tags_by_category(self, category=None, limit=50):
        """
        Lấy tag theo danh mục (dựa trên tên hoặc mô tả)
        
        Args:
            category: Từ khóa danh mục
            limit: Số lượng tag
            
        Returns:
            List[Tag]: Danh sách tag
        """
        try:
            query = self.session.query(Tag)
            
            if category:
                search_pattern = f"%{category}%"
                query = query.filter(
                    or_(
                        Tag.name.ilike(search_pattern),
                        Tag.description.ilike(search_pattern)
                    )
                )
            
            return query.order_by(desc(Tag.usage_count)).limit(limit).all()
        except SQLAlchemyError as e:
            raise e