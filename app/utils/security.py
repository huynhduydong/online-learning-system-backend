"""
Security utilities
"""

import re
import os
from PIL import Image
from werkzeug.utils import secure_filename
from typing import Optional, Tuple


def sanitize_input(text: str) -> str:
    """
    Sanitize user input để prevent XSS và injection attacks
    
    Args:
        text: Input text cần sanitize
    
    Returns:
        Sanitized text
    """
    if not text or not isinstance(text, str):
        return text
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Limit length để prevent buffer overflow attacks
    sanitized = sanitized[:1000]
    
    return sanitized.strip()


def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """
    Kiểm tra file extension có được phép không
    
    Args:
        filename: Tên file
        allowed_extensions: Set các extension được phép
    
    Returns:
        True nếu file được phép
    """
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def validate_image_file(file) -> Tuple[bool, Optional[str]]:
    """
    Validate image file để đảm bảo security
    
    Args:
        file: File object từ request
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    if not allowed_file(file.filename):
        return False, "File type not allowed. Only PNG, JPG, JPEG, GIF are supported"
    
    # Check file size (5MB limit)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        return False, "File size too large. Maximum 5MB allowed"
    
    # Validate image format
    try:
        image = Image.open(file)
        image.verify()
        file.seek(0)  # Reset file pointer
        return True, None
    except Exception:
        return False, "Invalid image file"


def secure_filename_with_timestamp(filename: str, user_id: int = None) -> str:
    """
    Tạo secure filename với timestamp
    
    Args:
        filename: Original filename
        user_id: User ID để tạo unique filename
    
    Returns:
        Secure filename
    """
    import time
    
    # Get secure filename
    secure_name = secure_filename(filename)
    
    # Get file extension
    if '.' in secure_name:
        name, ext = secure_name.rsplit('.', 1)
        ext = ext.lower()
    else:
        name = secure_name
        ext = ''
    
    # Create unique filename
    timestamp = int(time.time())
    if user_id:
        unique_name = f"{name}_{user_id}_{timestamp}"
    else:
        unique_name = f"{name}_{timestamp}"
    
    if ext:
        unique_name = f"{unique_name}.{ext}"
    
    return unique_name


def check_file_security(file_path: str) -> bool:
    """
    Kiểm tra file security sau khi upload
    
    Args:
        file_path: Đường dẫn file
    
    Returns:
        True nếu file an toàn
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return False
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > 5 * 1024 * 1024:  # 5MB
            return False
        
        # For images, verify format
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            try:
                with Image.open(file_path) as img:
                    img.verify()
                return True
            except Exception:
                return False
        
        return True
    except Exception:
        return False


def resize_image(image_path: str, size: Tuple[int, int] = (200, 200)) -> bool:
    """
    Resize image để optimize storage
    
    Args:
        image_path: Đường dẫn image
        size: Target size (width, height)
    
    Returns:
        True nếu resize thành công
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize with maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            img.save(image_path, optimize=True, quality=85)
            
        return True
    except Exception:
        return False