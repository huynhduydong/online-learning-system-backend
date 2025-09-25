"""
Tag Service
Business logic for tags management
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from app.dao.tag_dao import TagDAO
from app.dao.question_dao import QuestionDAO
from app.exceptions.base import ValidationException, BusinessLogicException
from app import db


class TagService:
    """Service class cho tag operations"""
    
    def __init__(self):
        self.tag_dao = TagDAO()
        self.question_dao = QuestionDAO()
    
    def get_all_tags(self, page=1, per_page=50, sort_by='name', category=None):
        """
        Lấy danh sách tất cả tag
        
        Args:
            page: Số trang
            per_page: Số tag mỗi trang
            sort_by: Sắp xếp theo (name, usage_count, created_at)
            category: Lọc theo category
            
        Returns:
            dict: Kết quả phân trang
        """
        try:
            # Validate pagination
            page = max(1, int(page))
            per_page = min(100, max(1, int(per_page)))
            
            # Validate sort
            valid_sorts = ['name', 'usage_count', 'created_at']
            if sort_by not in valid_sorts:
                sort_by = 'name'
            
            # Get tags from DAO
            result = self.tag_dao.get_all_tags(
                page=page,
                per_page=per_page,
                sort_by=sort_by,
                category=category
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy danh sách tag: {str(e)}")
    
    def get_tag_by_id(self, tag_id):
        """
        Lấy chi tiết tag theo ID
        
        Args:
            tag_id: ID tag
            
        Returns:
            dict: Chi tiết tag
        """
        try:
            tag = self.tag_dao.get_tag_by_id(tag_id)
            
            if not tag:
                raise ValidationException("Không tìm thấy tag")
            
            return {
                'success': True,
                'data': tag
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy chi tiết tag: {str(e)}")
    
    def get_tag_by_name(self, name):
        """
        Lấy tag theo tên
        
        Args:
            name: Tên tag
            
        Returns:
            dict: Tag hoặc None
        """
        try:
            tag = self.tag_dao.get_tag_by_name(name)
            
            return {
                'success': True,
                'data': tag
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy tag theo tên: {str(e)}")
    
    def create_tag(self, name, description=None, category=None, color=None):
        """
        Tạo tag mới
        
        Args:
            name: Tên tag
            description: Mô tả tag
            category: Danh mục tag
            color: Màu sắc tag
            
        Returns:
            dict: Tag được tạo
        """
        try:
            # Validate tag data
            self._validate_tag_data(name, description, category)
            
            # Check if tag already exists
            existing_tag = self.tag_dao.get_tag_by_name(name)
            if existing_tag:
                raise ValidationException(f"Tag '{name}' đã tồn tại")
            
            # Create tag
            tag = self.tag_dao.create_tag(
                name=name,
                description=description,
                category=category,
                color=color
            )
            
            return {
                'success': True,
                'data': tag.to_dict(),
                'message': 'Tag đã được tạo thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi tạo tag: {str(e)}")
    
    def update_tag(self, tag_id, name=None, description=None, category=None, color=None):
        """
        Cập nhật tag
        
        Args:
            tag_id: ID tag
            name: Tên tag mới
            description: Mô tả mới
            category: Danh mục mới
            color: Màu sắc mới
            
        Returns:
            dict: Tag đã cập nhật
        """
        try:
            # Check if tag exists
            existing_tag = self.tag_dao.get_tag_by_id(tag_id)
            if not existing_tag:
                raise ValidationException("Không tìm thấy tag")
            
            # Validate new data if provided
            if name:
                self._validate_tag_data(name, description, category)
                
                # Check if new name conflicts with existing tag
                name_conflict = self.tag_dao.get_tag_by_name(name)
                if name_conflict and name_conflict['id'] != tag_id:
                    raise ValidationException(f"Tag '{name}' đã tồn tại")
            
            # Update tag
            updated = self.tag_dao.update_tag(
                tag_id=tag_id,
                name=name,
                description=description,
                category=category,
                color=color
            )
            
            if not updated:
                raise ValidationException("Không thể cập nhật tag")
            
            # Get updated tag data
            tag_data = self.tag_dao.get_tag_by_id(tag_id)
            
            return {
                'success': True,
                'data': tag_data,
                'message': 'Tag đã được cập nhật thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi cập nhật tag: {str(e)}")
    
    def delete_tag(self, tag_id):
        """
        Xóa tag
        
        Args:
            tag_id: ID tag
            
        Returns:
            dict: Kết quả xóa
        """
        try:
            # Check if tag exists
            tag = self.tag_dao.get_tag_by_id(tag_id)
            if not tag:
                raise ValidationException("Không tìm thấy tag")
            
            # Check if tag is being used
            if tag['usageCount'] > 0:
                raise ValidationException("Không thể xóa tag đang được sử dụng")
            
            # Delete tag
            deleted = self.tag_dao.delete_tag(tag_id)
            
            if not deleted:
                raise ValidationException("Không thể xóa tag")
            
            return {
                'success': True,
                'message': 'Tag đã được xóa thành công'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi xóa tag: {str(e)}")
    
    def search_tags(self, search_term, page=1, per_page=20):
        """
        Tìm kiếm tag
        
        Args:
            search_term: Từ khóa tìm kiếm
            page: Số trang
            per_page: Số tag mỗi trang
            
        Returns:
            dict: Kết quả tìm kiếm
        """
        try:
            if not search_term or len(search_term.strip()) < 1:
                raise ValidationException("Từ khóa tìm kiếm không được để trống")
            
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            # Search tags
            result = self.tag_dao.search_tags(
                search_term=search_term.strip(),
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
            raise ValidationException(f"Lỗi khi tìm kiếm tag: {str(e)}")
    
    def get_popular_tags(self, limit=20, time_frame='all'):
        """
        Lấy tag phổ biến
        
        Args:
            limit: Số lượng tag
            time_frame: Khung thời gian (week, month, all)
            
        Returns:
            dict: Danh sách tag phổ biến
        """
        try:
            # Validate time frame
            valid_time_frames = ['week', 'month', 'all']
            if time_frame not in valid_time_frames:
                time_frame = 'all'
            
            tags = self.tag_dao.get_popular_tags(
                limit=limit,
                time_frame=time_frame
            )
            
            return {
                'success': True,
                'data': [tag.to_dict() for tag in tags]
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy tag phổ biến: {str(e)}")
    
    def get_question_tags(self, question_id):
        """
        Lấy danh sách tag của một câu hỏi
        
        Args:
            question_id: ID câu hỏi
            
        Returns:
            dict: Danh sách tag
        """
        try:
            # Validate question exists
            question = self.question_dao.get_question_by_id(question_id)
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            tags = self.tag_dao.get_question_tags(question_id)
            
            return {
                'success': True,
                'data': [tag.to_dict() for tag in tags]
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy tag của câu hỏi: {str(e)}")
    
    def add_question_tags(self, question_id, tag_names):
        """
        Thêm tag cho câu hỏi
        
        Args:
            question_id: ID câu hỏi
            tag_names: Danh sách tên tag
            
        Returns:
            dict: Kết quả thêm tag
        """
        try:
            # Validate question exists
            question = self.question_dao.get_question_by_id(question_id)
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            # Validate tag names
            if not tag_names or not isinstance(tag_names, list):
                raise ValidationException("Danh sách tag không hợp lệ")
            
            # Limit number of tags
            if len(tag_names) > 5:
                raise ValidationException("Một câu hỏi chỉ có thể có tối đa 5 tag")
            
            # Process tags
            added_tags = []
            for tag_name in tag_names:
                tag_name = tag_name.strip().lower()
                if not tag_name:
                    continue
                
                # Validate tag name
                self._validate_tag_name(tag_name)
                
                # Get or create tag
                tag = self.tag_dao.get_tag_by_name(tag_name)
                if not tag:
                    # Create new tag
                    tag_obj = self.tag_dao.create_tag(name=tag_name)
                    tag = tag_obj.to_dict()
                
                # Add tag to question
                added = self.tag_dao.add_question_tag(question_id, tag['id'])
                if added:
                    added_tags.append(tag)
            
            return {
                'success': True,
                'data': added_tags,
                'message': f'Đã thêm {len(added_tags)} tag cho câu hỏi'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi thêm tag cho câu hỏi: {str(e)}")
    
    def remove_question_tag(self, question_id, tag_id):
        """
        Xóa tag khỏi câu hỏi
        
        Args:
            question_id: ID câu hỏi
            tag_id: ID tag
            
        Returns:
            dict: Kết quả xóa tag
        """
        try:
            # Validate question exists
            question = self.question_dao.get_question_by_id(question_id)
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            # Validate tag exists
            tag = self.tag_dao.get_tag_by_id(tag_id)
            if not tag:
                raise ValidationException("Không tìm thấy tag")
            
            # Remove tag from question
            removed = self.tag_dao.remove_question_tag(question_id, tag_id)
            
            if not removed:
                raise ValidationException("Không thể xóa tag khỏi câu hỏi")
            
            return {
                'success': True,
                'message': 'Đã xóa tag khỏi câu hỏi'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi xóa tag khỏi câu hỏi: {str(e)}")
    
    def update_question_tags(self, question_id, tag_names):
        """
        Cập nhật toàn bộ tag của câu hỏi
        
        Args:
            question_id: ID câu hỏi
            tag_names: Danh sách tên tag mới
            
        Returns:
            dict: Kết quả cập nhật
        """
        try:
            # Validate question exists
            question = self.question_dao.get_question_by_id(question_id)
            if not question:
                raise ValidationException("Không tìm thấy câu hỏi")
            
            # Validate tag names
            if not isinstance(tag_names, list):
                raise ValidationException("Danh sách tag không hợp lệ")
            
            # Limit number of tags
            if len(tag_names) > 5:
                raise ValidationException("Một câu hỏi chỉ có thể có tối đa 5 tag")
            
            # Update tags
            updated_tags = self.tag_dao.update_question_tags(question_id, tag_names)
            
            return {
                'success': True,
                'data': [tag.to_dict() for tag in updated_tags],
                'message': 'Đã cập nhật tag cho câu hỏi'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationException(f"Lỗi khi cập nhật tag cho câu hỏi: {str(e)}")
    
    def get_tag_statistics(self, tag_id):
        """
        Lấy thống kê của tag
        
        Args:
            tag_id: ID tag
            
        Returns:
            dict: Thống kê tag
        """
        try:
            # Validate tag exists
            tag = self.tag_dao.get_tag_by_id(tag_id)
            if not tag:
                raise ValidationException("Không tìm thấy tag")
            
            stats = self.tag_dao.get_tag_statistics(tag_id)
            
            return {
                'success': True,
                'data': stats
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy thống kê tag: {str(e)}")
    
    def get_related_tags(self, tag_id, limit=10):
        """
        Lấy tag liên quan
        
        Args:
            tag_id: ID tag
            limit: Số lượng tag liên quan
            
        Returns:
            dict: Danh sách tag liên quan
        """
        try:
            # Validate tag exists
            tag = self.tag_dao.get_tag_by_id(tag_id)
            if not tag:
                raise ValidationException("Không tìm thấy tag")
            
            related_tags = self.tag_dao.get_related_tags(tag_id, limit)
            
            return {
                'success': True,
                'data': [tag.to_dict() for tag in related_tags]
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy tag liên quan: {str(e)}")
    
    def get_tags_by_category(self, category, page=1, per_page=20):
        """
        Lấy tag theo danh mục
        
        Args:
            category: Danh mục
            page: Số trang
            per_page: Số tag mỗi trang
            
        Returns:
            dict: Danh sách tag theo danh mục
        """
        try:
            # Validate pagination
            page = max(1, int(page))
            per_page = min(50, max(1, int(per_page)))
            
            result = self.tag_dao.get_tags_by_category(
                category=category,
                page=page,
                per_page=per_page
            )
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            raise ValidationException(f"Lỗi khi lấy tag theo danh mục: {str(e)}")
    
    def _validate_tag_data(self, name, description=None, category=None):
        """Validate tag data"""
        # Validate name
        self._validate_tag_name(name)
        
        # Validate description
        if description and len(description) > 500:
            raise ValidationException("Mô tả tag không được quá 500 ký tự")
        
        # Validate category
        if category and len(category) > 50:
            raise ValidationException("Danh mục tag không được quá 50 ký tự")
    
    def _validate_tag_name(self, name):
        """Validate tag name"""
        if not name or not name.strip():
            raise ValidationException("Tên tag không được để trống")
        
        name = name.strip()
        
        if len(name) < 2:
            raise ValidationException("Tên tag phải có ít nhất 2 ký tự")
        
        if len(name) > 30:
            raise ValidationException("Tên tag không được quá 30 ký tự")
        
        # Check for invalid characters
        import re
        if not re.match(r'^[a-zA-Z0-9\-_\+\#\.]+$', name):
            raise ValidationException("Tên tag chỉ được chứa chữ cái, số và các ký tự: - _ + # .")