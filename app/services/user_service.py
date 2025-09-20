"""
User Service
Chứa business logic cho user operations
Tuân thủ kiến trúc: Route → Service → DAO → DB
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from werkzeug.datastructures import FileStorage
from flask import current_app

from app import db
from app.models.user import User
from app.dao.user_dao import UserDAO
from app.utils.security import allowed_file, validate_image_file
from app.exceptions.base import ValidationException, BusinessLogicException


class UserService:
    """Service class cho user operations"""
    
    def __init__(self):
        self.user_dao = UserDAO()
    
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Lấy thông tin profile của user
        
        Args:
            user_id: ID của user
        
        Returns:
            Dict chứa thông tin user
        
        Raises:
            ValidationException: Nếu user không tồn tại
        """
        user = self.user_dao.get_by_id(user_id)
        if not user:
            raise ValidationException("User not found")
        
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'role': user.role.value,
            'avatar_url': user.get_avatar_url(),
            'is_active': user.is_active,
            'email_confirmed': bool(user.confirmed_at),
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login_at.isoformat() if user.last_login_at else None,
            'last_activity': user.last_activity_at.isoformat() if user.last_activity_at else None
        }
    
    def update_user_profile(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cập nhật profile của user
        
        Args:
            user_id: ID của user
            data: Data cần update
        
        Returns:
            Dict chứa thông tin user đã update
        
        Raises:
            ValidationException: Nếu user không tồn tại
            BusinessLogicException: Nếu có lỗi khi update
        """
        user = self.user_dao.get_by_id(user_id)
        if not user:
            raise ValidationException("User not found")
        
        try:
            # Prepare update data
            update_data = {}
            
            if 'first_name' in data and data['first_name'] is not None:
                update_data['first_name'] = data['first_name'].strip()
            
            if 'last_name' in data and data['last_name'] is not None:
                update_data['last_name'] = data['last_name'].strip()
            
            # Update using DAO
            updated_user = self.user_dao.update_profile(user_id, update_data)
            
            return self.get_user_profile(user_id)
            
        except Exception as e:
            raise BusinessLogicException(f"Failed to update user profile: {str(e)}")
    
    def upload_avatar(self, user_id: int, file: FileStorage) -> Dict[str, Any]:
        """
        Upload avatar cho user
        
        Args:
            user_id: ID của user
            file: File upload
        
        Returns:
            Dict chứa thông tin avatar đã upload
        
        Raises:
            ValidationException: Nếu file không hợp lệ
            BusinessLogicException: Nếu có lỗi khi upload
        """
        user = self.user_dao.get_by_id(user_id)
        if not user:
            raise ValidationException("User not found")
        
        if not file or file.filename == '':
            raise ValidationException("No file selected")
        
        # Validate file
        if not allowed_file(file.filename):
            raise ValidationException("Invalid file type. Only JPG, JPEG, PNG, GIF files are allowed")
        
        try:
            # Validate image file
            is_valid, error_message = validate_image_file(file)
            if not is_valid:
                raise ValidationException(error_message)
            
            # Generate unique filename
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            filename = f"avatar_{user_id}_{uuid.uuid4().hex}.{file_extension}"
            
            # Create upload directory if not exists
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            # Delete old avatar if exists
            if user.avatar_filename:
                old_file_path = os.path.join(upload_dir, user.avatar_filename)
                if os.path.exists(old_file_path):
                    try:
                        os.remove(old_file_path)
                    except OSError:
                        pass  # Ignore if can't delete old file
            
            # Update user avatar using DAO
            self.user_dao.update_profile(user_id, {'avatar_filename': filename})
            
            # Get updated user
            updated_user = self.user_dao.get_by_id(user_id)
            
            return {
                'avatar_url': updated_user.get_avatar_url(),
                'filename': filename,
                'message': 'Avatar uploaded successfully'
            }
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            # Clean up uploaded file if exists
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
            raise BusinessLogicException(f"Failed to upload avatar: {str(e)}")
    
    def delete_avatar(self, user_id: int) -> Dict[str, str]:
        """
        Xóa avatar của user
        
        Args:
            user_id: ID của user
        
        Returns:
            Dict chứa message
        
        Raises:
            ValidationException: Nếu user không tồn tại
            BusinessLogicException: Nếu có lỗi khi xóa
        """
        user = self.user_dao.get_by_id(user_id)
        if not user:
            raise ValidationException("User not found")
        
        if not user.avatar_filename:
            raise ValidationException("No avatar to delete")
        
        try:
            # Delete file
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
            file_path = os.path.join(upload_dir, user.avatar_filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Update user using DAO
            self.user_dao.update_profile(user_id, {'avatar_filename': None})
            
            return {'message': 'Avatar deleted successfully'}
            
        except Exception as e:
            raise BusinessLogicException(f"Failed to delete avatar: {str(e)}")
    
    def search_users(self, query: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Tìm kiếm users
        
        Args:
            query: Search query
            page: Page number
            per_page: Items per page
        
        Returns:
            Dict chứa kết quả search và pagination info
        """
        try:
            # Use DAO to search users
            result = self.user_dao.search_users(query, page, per_page)
            
            users = []
            for user in result['users']:
                users.append({
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role.value,
                    'avatar_url': user.get_avatar_url()
                })
            
            return {
                'users': users,
                'pagination': result['pagination']
            }
            
        except Exception as e:
            raise BusinessLogicException(f"Failed to search users: {str(e)}")
    
    def get_user_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """
        Lấy data cho dashboard của user
        
        Args:
            user_id: ID của user
        
        Returns:
            Dict chứa dashboard data
        
        Raises:
            ValidationException: Nếu user không tồn tại
        """
        user = self.user_dao.get_by_id(user_id)
        if not user:
            raise ValidationException("User not found")
        
        try:
            # Basic user info
            dashboard_data = {
                'user': self.get_user_profile(user_id),
                'stats': {
                    'total_courses': 0,  # Will be implemented when course service is ready
                    'completed_courses': 0,
                    'in_progress_courses': 0,
                    'total_hours_learned': 0
                },
                'recent_activity': [],  # Will be implemented with activity tracking
                'notifications': []  # Will be implemented with notification system
            }
            
            return dashboard_data
            
        except Exception as e:
            raise BusinessLogicException(f"Failed to get dashboard data: {str(e)}")
    
    def update_user_activity(self, user_id: int) -> None:
        """
        Cập nhật last activity của user
        
        Args:
            user_id: ID của user
        """
        try:
            self.user_dao.update_last_activity(user_id)
        except Exception:
            # Ignore errors for activity tracking
            pass