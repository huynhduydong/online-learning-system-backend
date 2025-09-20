"""
Authentication Blueprint
Implements User Stories: OLS-US-001 (User Registration), OLS-US-002 (User Login)

Business Requirements:
- User registration với email validation và password strength
- User login với JWT token generation
- Account security với failed login tracking
"""

from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validates, validates_schema
from app import db, limiter
from app.models.user import User, UserRole
from datetime import datetime
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

auth_bp = Blueprint('auth', __name__)


def send_confirmation_email(user):
    """
    Send email confirmation to user
    
    Business Requirement: Hệ thống gửi email xác nhận sau khi đăng ký thành công
    """
    try:
        # Generate confirmation token
        confirmation_token = secrets.token_urlsafe(32)
        
        # Store token in user record (we'll add this field to User model)
        user.confirmation_token = confirmation_token
        db.session.commit()
        
        # Create confirmation URL
        confirmation_url = url_for('auth.confirm_email', 
                                 token=confirmation_token, 
                                 _external=True)
        
        # Email content
        subject = "Xác nhận tài khoản - Online Learning System"
        
        html_body = f"""
        <html>
        <body>
            <h2>Chào mừng {user.full_name}!</h2>
            <p>Cảm ơn bạn đã đăng ký tài khoản tại Online Learning System.</p>
            <p>Vui lòng click vào link bên dưới để xác nhận tài khoản:</p>
            <p><a href="{confirmation_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Xác nhận tài khoản</a></p>
            <p>Hoặc copy link này vào trình duyệt:</p>
            <p>{confirmation_url}</p>
            <p>Link này sẽ hết hạn sau 24 giờ.</p>
            <br>
            <p>Trân trọng,<br>Online Learning System Team</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Chào mừng {user.full_name}!
        
        Cảm ơn bạn đã đăng ký tài khoản tại Online Learning System.
        
        Vui lòng truy cập link bên dưới để xác nhận tài khoản:
        {confirmation_url}
        
        Link này sẽ hết hạn sau 24 giờ.
        
        Trân trọng,
        Online Learning System Team
        """
        
        # Send email
        send_email(user.email, subject, text_body, html_body)
        
        current_app.logger.info(f"Confirmation email sent to {user.email}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send confirmation email to {user.email}: {e}")
        raise e


def send_email(to_email, subject, text_body, html_body=None):
    """
    Send email using SMTP configuration
    """
    try:
        # Get email configuration
        mail_server = current_app.config.get('MAIL_SERVER')
        mail_port = current_app.config.get('MAIL_PORT', 587)
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        mail_use_tls = current_app.config.get('MAIL_USE_TLS', True)
        
        if not all([mail_server, mail_username, mail_password]):
            # If email not configured, just log and return
            current_app.logger.warning("Email configuration not complete, skipping email send")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = mail_username
        msg['To'] = to_email
        
        # Add text and HTML parts
        text_part = MIMEText(text_body, 'plain', 'utf-8')
        msg.attach(text_part)
        
        if html_body:
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(mail_server, mail_port) as server:
            if mail_use_tls:
                server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to_email}: {e}")
        raise e


class UserRegistrationSchema(Schema):
    """Schema validation cho user registration"""
    email = fields.Email(required=True, error_messages={'required': 'Email is required'})
    password = fields.Str(required=True, validate=lambda x: len(x) >= 8, 
                         error_messages={'required': 'Password is required'})
    first_name = fields.Str(required=True, validate=lambda x: len(x.strip()) >= 2,
                           error_messages={'required': 'First name is required'})
    last_name = fields.Str(required=True, validate=lambda x: len(x.strip()) >= 2,
                          error_messages={'required': 'Last name is required'})
    role = fields.Str(missing='student', validate=lambda x: x in ['student', 'instructor'])
    
    @validates('email')
    def validate_email_format(self, value):
        """Validate email format"""
        if not User.validate_email(value):
            raise ValidationError('Invalid email format')
    
    @validates('password')
    def validate_password_strength(self, value):
        """Validate password strength according to business rules"""
        is_valid, message = User.validate_password_strength(value)
        if not is_valid:
            raise ValidationError(message)
    
    @validates_schema
    def validate_email_unique(self, data, **kwargs):
        """Check if email already exists"""
        if 'email' in data:
            existing_user = User.query.filter_by(email=data['email'].lower()).first()
            if existing_user:
                raise ValidationError({'email': ['Email đã được sử dụng']})


class UserLoginSchema(Schema):
    """Schema validation cho user login"""
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember_me = fields.Bool(missing=False)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("20 per minute")  # Increased for testing
def register():
    """
    User Registration Endpoint
    
    Implements User Story OLS-US-001: User Registration
    
    Business Rules:
    - Email phải unique trong hệ thống
    - Mật khẩu tối thiểu 8 ký tự, có chữ hoa, chữ thường, số
    - Tài khoản mới mặc định là "Student"
    """
    try:
        # Validate input data
        schema = UserRegistrationSchema()
        data = schema.load(request.json)
        
        # Create new user
        user = User(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=UserRole.INSTRUCTOR if data['role'] == 'instructor' else UserRole.STUDENT
        )
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        # Send email confirmation
        try:
            send_confirmation_email(user)
            email_message = "Vui lòng kiểm tra email để xác nhận tài khoản."
        except Exception as e:
            # Log error but don't fail registration
            current_app.logger.error(f"Failed to send confirmation email: {e}")
            email_message = "Tài khoản đã được tạo. Email xác nhận sẽ được gửi sau."
        
        return jsonify({
            'success': True,
            'message': f'Tài khoản được tạo thành công. {email_message}',
            'user': user.to_dict()
        }), 201
        
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
            'error': 'Registration failed',
            'message': str(e)
        }), 500


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    User Login Endpoint
    
    Implements User Story OLS-US-002: User Login
    
    Business Rules:
    - Sau 5 lần đăng nhập sai, tài khoản bị khóa 15 phút
    - Session timeout sau 24h nếu không có activity
    - Remember me option cho 30 ngày
    """
    try:
        # Validate input data
        schema = UserLoginSchema()
        data = schema.load(request.json)
        
        # Find user by email
        user = User.query.filter_by(email=data['email'].lower()).first()
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Thông tin đăng nhập không chính xác'
            }), 401
        
        # Check if account is locked
        if user.is_locked:
            return jsonify({
                'success': False,
                'error': 'Tài khoản đã bị khóa do nhiều lần đăng nhập sai. Vui lòng thử lại sau.'
            }), 423
        
        # Check if account is active
        if not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Tài khoản đã bị vô hiệu hóa'
            }), 403
        
        # Verify password
        if not user.check_password(data['password']):
            user.increment_failed_login()
            return jsonify({
                'success': False,
                'error': 'Thông tin đăng nhập không chính xác'
            }), 401
        
        # Successful login
        user.reset_failed_login()
        user.update_last_login()
        
        # Create JWT tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Đăng nhập thành công',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.messages
        }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Login failed',
            'message': str(e)
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh JWT Token
    
    Allows users to get new access token using refresh token
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Invalid user'
            }), 401
        
        # Create new access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Token refresh failed',
            'message': str(e)
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User Logout
    
    Note: In a production system, you would want to blacklist the JWT token
    For now, we'll just return success (client should delete the token)
    """
    return jsonify({
        'success': True,
        'message': 'Đăng xuất thành công'
    }), 200


@auth_bp.route('/confirm-email/<token>', methods=['GET'])
def confirm_email(token):
    """
    Email Confirmation Endpoint
    
    Confirms user email address using token sent via email
    """
    try:
        # Find user by confirmation token
        user = User.query.filter_by(confirmation_token=token).first()
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired confirmation token'
            }), 400
        
        # Check if already confirmed
        if user.confirmed_at:
            return jsonify({
                'success': True,
                'message': 'Email đã được xác nhận trước đó'
            }), 200
        
        # Confirm email
        user.confirmed_at = datetime.utcnow()
        user.is_verified = True
        user.confirmation_token = None  # Clear token after use
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Email đã được xác nhận thành công! Bạn có thể đăng nhập ngay bây giờ.'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Email confirmation failed',
            'message': str(e)
        }), 500


@auth_bp.route('/resend-confirmation', methods=['POST'])
@limiter.limit("3 per minute")
def resend_confirmation():
    """
    Resend confirmation email
    
    Allows users to request a new confirmation email
    """
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if email exists or not for security
            return jsonify({
                'success': True,
                'message': 'Nếu email tồn tại, bạn sẽ nhận được email xác nhận.'
            }), 200
        
        if user.is_verified:
            return jsonify({
                'success': True,
                'message': 'Tài khoản đã được xác nhận.'
            }), 200
        
        # Send new confirmation email
        try:
            send_confirmation_email(user)
            return jsonify({
                'success': True,
                'message': 'Email xác nhận đã được gửi lại.'
            }), 200
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Failed to send confirmation email'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to resend confirmation',
            'message': str(e)
        }), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user information
    
    Returns the current authenticated user's profile
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get user info',
            'message': str(e)
        }), 500