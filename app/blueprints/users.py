"""
Users Blueprint
Implements User Story: OLS-US-003 (User Profile Management)

Business Requirements:
- User xem và cập nhật thông tin profile
- Upload ảnh đại diện với validation
- User dashboard với enrolled courses
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from werkzeug.utils import secure_filename
from PIL import Image
import os
from app import db
from app.models.user import User

users_bp = Blueprint('users', __name__)


class UserProfileUpdateSchema(Schema):
    """Schema validation cho profile update"""
    first_name = fields.Str(validate=lambda x: len(x.strip()) >= 2)
    last_name = fields.Str(validate=lambda x: len(x.strip()) >= 2)


def allowed_file(filename):
    """Check if file extension is allowed for profile images"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def resize_image(image_path, size=(200, 200)):
    """
    Resize image to specified size
    Business Rule: Ảnh đại diện được resize về 200x200px
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize image maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Create a new image with the exact size and paste the resized image
            new_img = Image.new('RGB', size, (255, 255, 255))
            
            # Calculate position to center the image
            x = (size[0] - img.size[0]) // 2
            y = (size[1] - img.size[1]) // 2
            
            new_img.paste(img, (x, y))
            # Determine format from file extension
            ext = os.path.splitext(image_path)[1].lower()
            format_map = {
                '.jpg': 'JPEG',
                '.jpeg': 'JPEG',
                '.png': 'PNG',
                '.gif': 'GIF'
            }
            img_format = format_map.get(ext, 'JPEG')
            save_kwargs = {'quality': 85} if img_format == 'JPEG' else {}
            new_img.save(image_path, img_format, **save_kwargs)
            
        return True
    except Exception as e:
        current_app.logger.error(f"Error resizing image: {str(e)}")
        return False


@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get User Profile
    
    Implements User Story OLS-US-003: User Profile Management
    
    Business Rule: User xem thông tin profile hiện tại
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get additional profile stats
        profile_data = user.to_dict()
        
        # Add enrollment statistics
        total_enrollments = user.enrollments.count()
        completed_courses = user.enrollments.filter_by(status='completed').count() if hasattr(user.enrollments.first(), 'status') else 0
        
        profile_data.update({
            'total_enrollments': total_enrollments,
            'completed_courses': completed_courses,
            'join_date': user.created_at.strftime('%B %Y')
        })
        
        return jsonify({
            'success': True,
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get profile',
            'message': str(e)
        }), 500


@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update User Profile
    
    Implements User Story OLS-US-003: User Profile Management
    
    Business Rules:
    - User cập nhật tên (không thể đổi email)
    - Thông tin profile được audit log để tracking changes
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Validate input data
        schema = UserProfileUpdateSchema()
        data = schema.load(request.json)
        
        # Track changes for audit log
        changes = {}
        
        # Update allowed fields
        if 'first_name' in data:
            old_value = user.first_name
            user.first_name = data['first_name'].strip()
            if old_value != user.first_name:
                changes['first_name'] = {'old': old_value, 'new': user.first_name}
        
        if 'last_name' in data:
            old_value = user.last_name
            user.last_name = data['last_name'].strip()
            if old_value != user.last_name:
                changes['last_name'] = {'old': old_value, 'new': user.last_name}
        
        # Save changes
        if changes:
            db.session.commit()
            
            # TODO: Log audit trail (implement in future sprint)
            current_app.logger.info(f"User {user.id} profile updated: {changes}")
            
            return jsonify({
                'success': True,
                'message': 'Thông tin profile đã được cập nhật thành công',
                'profile': user.to_dict()
            }), 200
        else:
            return jsonify({
                'success': True,
                'message': 'Không có thay đổi nào được thực hiện',
                'profile': user.to_dict()
            }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.messages
        }), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update profile',
            'message': str(e)
        }), 500


@users_bp.route('/upload-avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """
    Upload Profile Avatar
    
    Implements User Story OLS-US-003: User Profile Management
    
    Business Rules:
    - Upload ảnh đại diện với format JPG/PNG, tối đa 2MB
    - Ảnh đại diện được resize về 200x200px
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Only JPG, PNG, GIF files are allowed'
            }), 400
        
        # Check file size (2MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 2 * 1024 * 1024:  # 2MB
            return jsonify({
                'success': False,
                'error': 'File quá lớn, tối đa 2MB'
            }), 400
        
        # Create upload directory if it doesn't exist
        upload_folder = current_app.config['UPLOAD_FOLDER']
        avatars_folder = os.path.join(upload_folder, 'avatars')
        os.makedirs(avatars_folder, exist_ok=True)
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        # Always use .jpg extension since resize_image saves as JPEG
        new_filename = f"user_{user.id}_{int(datetime.now().timestamp())}.jpg"
        file_path = os.path.join(avatars_folder, new_filename)
        
        # Save file
        file.save(file_path)
        
        # Resize image
        if not resize_image(file_path):
            # If resize fails, delete the file and return error
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({
                'success': False,
                'error': 'Failed to process image'
            }), 500
        
        # Delete old avatar if exists
        if user.profile_image:
            old_file_path = os.path.join(current_app.root_path, '..', user.profile_image)
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                except:
                    pass  # Ignore errors when deleting old file
        
        # Update user profile
        user.profile_image = f"uploads/avatars/{new_filename}"
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avatar đã được cập nhật thành công',
            'profile_image': user.profile_image
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to upload avatar',
            'message': str(e)
        }), 500


@users_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """
    Get User Dashboard
    
    Implements User Story OLS-US-002: Redirect về trang dashboard sau khi login thành công
    Implements User Story OLS-US-003: User dashboard với course overview
    
    Returns dashboard data including enrolled courses and progress
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Update last activity for session tracking
        user.update_last_login()
        
        # Get user's enrolled courses (placeholder - will implement in Sprint 3)
        enrolled_courses = []
        
        # Get basic statistics
        dashboard_data = {
            'user': user.to_dict(),
            'welcome_message': f'Chào mừng trở lại, {user.first_name}!',
            'statistics': {
                'total_enrollments': 0,  # Will be implemented in Sprint 3
                'completed_courses': 0,
                'in_progress_courses': 0,
                'total_learning_time': 0  # Will be implemented in Sprint 4
            },
            'recent_courses': enrolled_courses,
            'achievements': [],  # Will be implemented in Sprint 4
            'notifications': [],  # Will be implemented in Sprint 4
            'quick_actions': [
                {
                    'title': 'Khám phá khóa học',
                    'description': 'Tìm kiếm khóa học phù hợp với bạn',
                    'action': 'browse_courses',
                    'icon': 'search'
                },
                {
                    'title': 'Tiếp tục học',
                    'description': 'Quay lại khóa học đang học',
                    'action': 'continue_learning',
                    'icon': 'play'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get dashboard',
            'message': str(e)
        }), 500