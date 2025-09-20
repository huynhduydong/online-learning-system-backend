"""
Base DAO (Data Access Object) class
Cung cấp các phương thức CRUD cơ bản cho tất cả các DAO classes
"""
from typing import List, Optional, Type, TypeVar, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app import db

# Generic type cho model
T = TypeVar('T')


class BaseDAO:
    """
    Base DAO class cung cấp các phương thức CRUD cơ bản
    """
    
    def __init__(self, model_class: Type[T]):
        """
        Khởi tạo DAO với model class
        
        Args:
            model_class: SQLAlchemy model class
        """
        self.model_class = model_class
        self.session: Session = db.session
    
    def create(self, **kwargs) -> T:
        """
        Tạo mới một record
        
        Args:
            **kwargs: Dữ liệu để tạo record
            
        Returns:
            T: Instance của model được tạo
            
        Raises:
            SQLAlchemyError: Lỗi database
        """
        try:
            instance = self.model_class(**kwargs)
            self.session.add(instance)
            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Lấy record theo ID
        
        Args:
            id: ID của record
            
        Returns:
            Optional[T]: Instance của model hoặc None
        """
        try:
            return self.session.query(self.model_class).filter(
                self.model_class.id == id
            ).first()
        except SQLAlchemyError as e:
            raise e
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """
        Lấy record theo một field cụ thể
        
        Args:
            field_name: Tên field
            value: Giá trị cần tìm
            
        Returns:
            Optional[T]: Instance của model hoặc None
        """
        try:
            field = getattr(self.model_class, field_name)
            return self.session.query(self.model_class).filter(
                field == value
            ).first()
        except (AttributeError, SQLAlchemyError) as e:
            raise e
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        Lấy tất cả records
        
        Args:
            limit: Giới hạn số lượng records
            offset: Bỏ qua số lượng records
            
        Returns:
            List[T]: Danh sách instances
        """
        try:
            query = self.session.query(self.model_class)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
                
            return query.all()
        except SQLAlchemyError as e:
            raise e
    
    def get_by_filters(self, filters: Dict[str, Any], 
                      limit: Optional[int] = None, 
                      offset: Optional[int] = None) -> List[T]:
        """
        Lấy records theo nhiều filters
        
        Args:
            filters: Dictionary chứa field_name: value
            limit: Giới hạn số lượng records
            offset: Bỏ qua số lượng records
            
        Returns:
            List[T]: Danh sách instances
        """
        try:
            query = self.session.query(self.model_class)
            
            for field_name, value in filters.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    query = query.filter(field == value)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
                
            return query.all()
        except SQLAlchemyError as e:
            raise e
    
    def update(self, id: int, **kwargs) -> Optional[T]:
        """
        Cập nhật record theo ID
        
        Args:
            id: ID của record
            **kwargs: Dữ liệu cần cập nhật
            
        Returns:
            Optional[T]: Instance đã được cập nhật hoặc None
            
        Raises:
            SQLAlchemyError: Lỗi database
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None
            
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def update_by_filters(self, filters: Dict[str, Any], **kwargs) -> int:
        """
        Cập nhật nhiều records theo filters
        
        Args:
            filters: Dictionary chứa field_name: value để filter
            **kwargs: Dữ liệu cần cập nhật
            
        Returns:
            int: Số lượng records được cập nhật
            
        Raises:
            SQLAlchemyError: Lỗi database
        """
        try:
            query = self.session.query(self.model_class)
            
            for field_name, value in filters.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    query = query.filter(field == value)
            
            # Chỉ cập nhật các fields tồn tại trong model
            update_data = {}
            for key, value in kwargs.items():
                if hasattr(self.model_class, key):
                    update_data[key] = value
            
            count = query.update(update_data)
            self.session.commit()
            return count
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def delete(self, id: int) -> bool:
        """
        Xóa record theo ID
        
        Args:
            id: ID của record
            
        Returns:
            bool: True nếu xóa thành công, False nếu không tìm thấy
            
        Raises:
            SQLAlchemyError: Lỗi database
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False
            
            self.session.delete(instance)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def delete_by_filters(self, filters: Dict[str, Any]) -> int:
        """
        Xóa nhiều records theo filters
        
        Args:
            filters: Dictionary chứa field_name: value để filter
            
        Returns:
            int: Số lượng records được xóa
            
        Raises:
            SQLAlchemyError: Lỗi database
        """
        try:
            query = self.session.query(self.model_class)
            
            for field_name, value in filters.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    query = query.filter(field == value)
            
            count = query.delete()
            self.session.commit()
            return count
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Đếm số lượng records
        
        Args:
            filters: Dictionary chứa field_name: value để filter (optional)
            
        Returns:
            int: Số lượng records
        """
        try:
            query = self.session.query(self.model_class)
            
            if filters:
                for field_name, value in filters.items():
                    if hasattr(self.model_class, field_name):
                        field = getattr(self.model_class, field_name)
                        query = query.filter(field == value)
            
            return query.count()
        except SQLAlchemyError as e:
            raise e
    
    def exists(self, **kwargs) -> bool:
        """
        Kiểm tra record có tồn tại không
        
        Args:
            **kwargs: Điều kiện để kiểm tra
            
        Returns:
            bool: True nếu tồn tại, False nếu không
        """
        try:
            query = self.session.query(self.model_class)
            
            for field_name, value in kwargs.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    query = query.filter(field == value)
            
            return query.first() is not None
        except SQLAlchemyError as e:
            raise e