"""
Authentication Service
Chứa business logic cho authentication
"""

import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, url_for
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import check_password_hash

from app import db
from app.models.user import User, UserRole
from app.exceptions.base import (
    ValidationException, 
    AuthenticationException, 
    BusinessLogicException,
    ExternalServiceException
)


class AuthService:
    """Service class cho authentication operations"""
    
    @staticmethod
    def register_user(email: str, password: str, first_name: str, last_name: str, role: str = 'student') -> User:
        """
        Đăng ký user mới
        
        Args:
            email: Email của user
            password: Password
            first_name: Tên
            last_name: Họ
            role: Role của user
        
        Returns:
            User object đã được tạo
        
        Raises:
            ValidationException: Nếu email đã tồn tại
            BusinessLogicException: Nếu có lỗi business logic
        """
        try:
            # Check if email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                raise ValidationException("Email already registered", {"email": ["Email already exists"]})
            
            # Create new user
            user = User(
                email=email,
                password=password,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                role=UserRole.STUDENT if role == 'student' else UserRole.INSTRUCTOR
            )
            
            # Generate confirmation token
            user.confirmation_token = secrets.token_urlsafe(32)
            user.confirmation_token_expires = datetime.utcnow() + timedelta(hours=24)
            
            db.session.add(user)
            db.session.commit()
            
            # Send confirmation email
            # AuthService.send_confirmation_email(user)
            
            return user
            
        except ValidationException:
            raise
        except Exception as e:
            db.session.rollback()
            raise BusinessLogicException(f"Failed to register user: {str(e)}")
    
    @staticmethod
    def login_user(email: str, password: str, remember_me: bool = False) -> dict:
        """
        Đăng nhập user
        
        Args:
            email: Email
            password: Password
            remember_me: Có remember login không
        
        Returns:
            Dict chứa tokens và user info
        
        Raises:
            AuthenticationException: Nếu login thất bại
            BusinessLogicException: Nếu account bị lock
        """
        user = User.query.filter_by(email=email).first()
        
        if not user:
            raise AuthenticationException("Invalid email or password")
        
        # Check if account is locked
        if user.is_locked:
            raise BusinessLogicException("Account is temporarily locked due to too many failed login attempts")
        
        # Verify password
        if not user.check_password(password):
            user.increment_failed_login()
            db.session.commit()
            raise AuthenticationException("Invalid email or password")
        
        # Check if email is confirmed
        # TODO: Re-enable email confirmation later
        # if not user.confirmed_at:
        #     raise BusinessLogicException("Please confirm your email before logging in")
        
        # Check if user is active
        if not user.is_active:
            raise BusinessLogicException("Account is deactivated")
        
        # Reset failed login attempts
        user.reset_failed_login()
        user.last_login_at = datetime.utcnow()
        user.last_activity_at = datetime.utcnow()
        
        # Create tokens
        expires_delta = timedelta(days=30) if remember_me else timedelta(hours=24)
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=expires_delta
        )
        refresh_token = create_refresh_token(identity=str(user.id))
        
        db.session.commit()
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role.value,
                'avatar_url': user.get_avatar_url()
            }
        }
    
    @staticmethod
    def confirm_email(token: str) -> bool:
        """
        Xác nhận email với token
        
        Args:
            token: Confirmation token
        
        Returns:
            True nếu xác nhận thành công
        
        Raises:
            ValidationException: Nếu token không hợp lệ
        """
        user = User.query.filter_by(confirmation_token=token).first()
        
        if not user:
            raise ValidationException("Invalid confirmation token")
        
        if user.confirmation_token_expires and user.confirmation_token_expires < datetime.utcnow():
            raise ValidationException("Confirmation token has expired")
        
        user.confirmed_at = datetime.utcnow()
        user.confirmation_token = None
        user.confirmation_token_expires = None
        
        db.session.commit()
        return True
    
    @staticmethod
    def resend_confirmation_email(email: str) -> bool:
        """
        Gửi lại email xác nhận
        
        Args:
            email: Email của user
        
        Returns:
            True nếu gửi thành công
        
        Raises:
            ValidationException: Nếu user không tồn tại hoặc đã confirmed
        """
        user = User.query.filter_by(email=email).first()
        
        if not user:
            raise ValidationException("User not found")
        
        if user.confirmed_at:
            raise ValidationException("Email already confirmed")
        
        # Generate new token
        user.confirmation_token = secrets.token_urlsafe(32)
        user.confirmation_token_expires = datetime.utcnow() + timedelta(hours=24)
        
        db.session.commit()
        
        # Send email
        AuthService.send_confirmation_email(user)
        return True
    
    @staticmethod
    def send_confirmation_email(user: User) -> None:
        """
        Gửi email xác nhận
        
        Args:
            user: User object
        
        Raises:
            ExternalServiceException: Nếu gửi email thất bại
        """
        try:
            confirmation_url = url_for('auth.confirm_email', 
                                     token=user.confirmation_token, 
                                     _external=True)
            
            subject = "Xác nhận tài khoản - Online Learning System"
            
            html_body = f"""
            <html>
            <body>
                <h2>Chào mừng {user.full_name}!</h2>
                <p>Cảm ơn bạn đã đăng ký tài khoản tại Online Learning System.</p>
                <p>Vui lòng click vào link bên dưới để xác nhận email của bạn:</p>
                <p><a href="{confirmation_url}">Xác nhận email</a></p>
                <p>Link này sẽ hết hạn sau 24 giờ.</p>
                <p>Nếu bạn không đăng ký tài khoản này, vui lòng bỏ qua email này.</p>
                <br>
                <p>Trân trọng,<br>Online Learning System Team</p>
            </body>
            </html>
            """
            
            text_body = f"""
            Chào mừng {user.full_name}!
            
            Cảm ơn bạn đã đăng ký tài khoản tại Online Learning System.
            
            Vui lòng truy cập link bên dưới để xác nhận email của bạn:
            {confirmation_url}
            
            Link này sẽ hết hạn sau 24 giờ.
            
            Nếu bạn không đăng ký tài khoản này, vui lòng bỏ qua email này.
            
            Trân trọng,
            Online Learning System Team
            """
            
            AuthService._send_email(user.email, subject, text_body, html_body)
            
        except Exception as e:
            raise ExternalServiceException(f"Failed to send confirmation email: {str(e)}", "email")
    
    @staticmethod
    def _send_email(to_email: str, subject: str, text_body: str, html_body: str = None) -> None:
        """
        Gửi email helper method
        
        Args:
            to_email: Email người nhận
            subject: Subject
            text_body: Text content
            html_body: HTML content
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = current_app.config['MAIL_USERNAME']
            msg['To'] = to_email
            
            # Add text part
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
                if current_app.config['MAIL_USE_TLS']:
                    server.starttls()
                
                server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
                server.send_message(msg)
                
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise