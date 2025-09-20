"""
UserDAO - Data Access Object cho User model
Chịu trách nhiệm tất cả database operations liên quan đến User
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_, or_

from app.models.user import User, UserRole
from app.dao.base_dao import BaseDAO


class UserDAO(BaseDAO):
    """
    UserDAO class cung cấp các phương thức database operations cho User model
    Kế thừa từ BaseDAO và bổ sung các phương thức specific cho User
    """
    
    def __init__(self):
        """Khởi tạo UserDAO với User model"""
        super().__init__(User)
    
    # Authentication related methods
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Lấy user theo email
        
        Args:
            email: Email của user
            
        Returns:
            Optional[User]: User instance hoặc None
        """
        try:
            return self.session.query(User).filter(
                User.email == email.lower().strip()
            ).first()
        except SQLAlchemyError as e:
            raise e
    
    def create_user(self, email: str, password: str, first_name: str, 
                   last_name: str, role: UserRole = UserRole.STUDENT) -> User:
        """
        Tạo user mới
        
        Args:
            email: Email của user
            password: Mật khẩu
            first_name: Tên
            last_name: Họ
            role: Vai trò (mặc định STUDENT)
            
        Returns:
            User: User instance được tạo
            
        Raises:
            IntegrityError: Email đã tồn tại
            ValueError: Dữ liệu không hợp lệ
        """
        try:
            # Validate dữ liệu
            User.validate_email(email)
            User.validate_password_strength(password)
            User.validate_name(first_name, "First name")
            User.validate_name(last_name, "Last name")
            
            # Tạo user mới
            user = User(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            
            self.session.add(user)
            self.session.commit()
            return user
            
        except IntegrityError as e:
            self.session.rollback()
            if 'email' in str(e.orig):
                raise ValueError("Email already exists")
            raise e
        except (ValueError, SQLAlchemyError) as e:
            self.session.rollback()
            raise e
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Xác thực user với email và password
        
        Args:
            email: Email của user
            password: Mật khẩu
            
        Returns:
            Optional[User]: User instance nếu xác thực thành công, None nếu thất bại
        """
        try:
            user = self.get_by_email(email)
            if user and user.check_password(password):
                return user
            return None
        except SQLAlchemyError as e:
            raise e
    
    def update_last_login(self, user_id: int) -> bool:
        """
        Cập nhật thời gian đăng nhập cuối
        
        Args:
            user_id: ID của user
            
        Returns:
            bool: True nếu cập nhật thành công
        """
        try:
            return self.update(user_id, 
                             last_login_at=datetime.utcnow(),
                             last_activity_at=datetime.utcnow()) is not None
        except SQLAlchemyError as e:
            raise e
    
    def update_activity(self, user_id: int) -> bool:
        """
        Cập nhật thời gian hoạt động cuối
        
        Args:
            user_id: ID của user
            
        Returns:
            bool: True nếu cập nhật thành công
        """
        try:
            return self.update(user_id, last_activity_at=datetime.utcnow()) is not None
        except SQLAlchemyError as e:
            raise e
    
    # Profile management methods
    def update_profile(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """
        Cập nhật thông tin profile
        
        Args:
            user_id: ID của user
            update_data: Dictionary chứa các trường cần cập nhật (e.g., 'first_name', 'last_name')
            
        Returns:
            Optional[User]: User instance đã cập nhật hoặc None
        """
        try:
            update_fields = {}
            
            first_name = update_data.get('first_name')
            if first_name is not None:
                User.validate_name(first_name, "First name")
                update_fields['first_name'] = first_name.strip()
            
            last_name = update_data.get('last_name')
            if last_name is not None:
                User.validate_name(last_name, "Last name")
                update_fields['last_name'] = last_name.strip()
            
            if update_fields:
                update_fields['updated_at'] = datetime.utcnow()
                return self.update(user_id, **update_fields)
            
            return self.get_by_id(user_id)
            
        except (ValueError, SQLAlchemyError) as e:
            raise e
    
    def update_profile_image(self, user_id: int, image_path: str) -> Optional[User]:
        """
        Cập nhật ảnh profile
        
        Args:
            user_id: ID của user
            image_path: Đường dẫn ảnh mới
            
        Returns:
            Optional[User]: User instance đã cập nhật hoặc None
        """
        try:
            return self.update(user_id, 
                             profile_image=image_path,
                             updated_at=datetime.utcnow())
        except SQLAlchemyError as e:
            raise e
    
    def remove_profile_image(self, user_id: int) -> Optional[User]:
        """
        Xóa ảnh profile
        
        Args:
            user_id: ID của user
            
        Returns:
            Optional[User]: User instance đã cập nhật hoặc None
        """
        try:
            return self.update(user_id, 
                             profile_image=None,
                             updated_at=datetime.utcnow())
        except SQLAlchemyError as e:
            raise e
    
    # Security methods
    def increment_failed_login(self, user_id: int) -> Optional[User]:
        """
        Tăng số lần đăng nhập thất bại
        
        Args:
            user_id: ID của user
            
        Returns:
            Optional[User]: User instance đã cập nhật hoặc None
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                return None
            
            failed_attempts = user.failed_login_attempts + 1
            update_data = {'failed_login_attempts': failed_attempts}
            
            # Lock account nếu quá 5 lần thất bại
            if failed_attempts >= 5:
                update_data['locked_until'] = datetime.utcnow() + timedelta(minutes=30)
            
            return self.update(user_id, **update_data)
            
        except SQLAlchemyError as e:
            raise e
    
    def reset_failed_login(self, user_id: int) -> Optional[User]:
        """
        Reset số lần đăng nhập thất bại
        
        Args:
            user_id: ID của user
            
        Returns:
            Optional[User]: User instance đã cập nhật hoặc None
        """
        try:
            return self.update(user_id, 
                             failed_login_attempts=0,
                             locked_until=None)
        except SQLAlchemyError as e:
            raise e
    
    def change_password(self, user_id: int, new_password: str) -> Optional[User]:
        """
        Thay đổi mật khẩu
        
        Args:
            user_id: ID của user
            new_password: Mật khẩu mới
            
        Returns:
            Optional[User]: User instance đã cập nhật hoặc None
        """
        try:
            User.validate_password_strength(new_password)
            
            user = self.get_by_id(user_id)
            if not user:
                return None
            
            user.set_password(new_password)
            user.updated_at = datetime.utcnow()
            
            self.session.commit()
            return user
            
        except (ValueError, SQLAlchemyError) as e:
            self.session.rollback()
            raise e
    
    # Query methods
    def get_active_users(self, limit: Optional[int] = None, 
                        offset: Optional[int] = None) -> List[User]:
        """
        Lấy danh sách users đang active
        
        Args:
            limit: Giới hạn số lượng
            offset: Bỏ qua số lượng
            
        Returns:
            List[User]: Danh sách users active
        """
        try:
            return self.get_by_filters(
                filters={'is_active': True},
                limit=limit,
                offset=offset
            )
        except SQLAlchemyError as e:
            raise e
    
    def get_users_by_role(self, role: UserRole, limit: Optional[int] = None, 
                         offset: Optional[int] = None) -> List[User]:
        """
        Lấy users theo role
        
        Args:
            role: UserRole
            limit: Giới hạn số lượng
            offset: Bỏ qua số lượng
            
        Returns:
            List[User]: Danh sách users theo role
        """
        try:
            return self.get_by_filters(
                filters={'role': role, 'is_active': True},
                limit=limit,
                offset=offset
            )
        except SQLAlchemyError as e:
            raise e
    
    def search_users(self, search_term: str, limit: Optional[int] = None, 
                    offset: Optional[int] = None) -> List[User]:
        """
        Tìm kiếm users theo tên hoặc email
        
        Args:
            search_term: Từ khóa tìm kiếm
            limit: Giới hạn số lượng
            offset: Bỏ qua số lượng
            
        Returns:
            List[User]: Danh sách users tìm được
        """
        try:
            search_pattern = f"%{search_term.lower()}%"
            
            query = self.session.query(User).filter(
                and_(
                    User.is_active == True,
                    or_(
                        User.email.ilike(search_pattern),
                        User.first_name.ilike(search_pattern),
                        User.last_name.ilike(search_pattern)
                    )
                )
            )
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
                
            return query.all()
            
        except SQLAlchemyError as e:
            raise e
    
    def get_recently_active_users(self, days: int = 7, limit: Optional[int] = None) -> List[User]:
        """
        Lấy users hoạt động gần đây
        
        Args:
            days: Số ngày gần đây
            limit: Giới hạn số lượng
            
        Returns:
            List[User]: Danh sách users hoạt động gần đây
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = self.session.query(User).filter(
                and_(
                    User.is_active == True,
                    User.last_activity_at >= cutoff_date
                )
            ).order_by(User.last_activity_at.desc())
            
            if limit:
                query = query.limit(limit)
                
            return query.all()
            
        except SQLAlchemyError as e:
            raise e
    
    # Account management
    def activate_user(self, user_id: int) -> Optional[User]:
        """
        Kích hoạt tài khoản user
        
        Args:
            user_id: ID của user
            
        Returns:
            Optional[User]: User instance đã cập nhật hoặc None
        """
        try:
            return self.update(user_id, 
                             is_active=True,
                             updated_at=datetime.utcnow())
        except SQLAlchemyError as e:
            raise e
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        """
        Vô hiệu hóa tài khoản user
        
        Args:
            user_id: ID của user
            
        Returns:
            Optional[User]: User instance đã cập nhật hoặc None
        """
        try:
            return self.update(user_id, 
                             is_active=False,
                             updated_at=datetime.utcnow())
        except SQLAlchemyError as e:
            raise e
    
    def verify_user(self, user_id: int) -> Optional[User]:
        """
        Xác minh tài khoản user
        
        Args:
            user_id: ID của user
            
        Returns:
            Optional[User]: User instance đã cập nhật hoặc None
        """
        try:
            return self.update(user_id, 
                             is_verified=True,
                             confirmed_at=datetime.utcnow(),
                             updated_at=datetime.utcnow())
        except SQLAlchemyError as e:
            raise e