"""
Authentication utilities for Flask application
"""

import uuid
from typing import Optional
from flask import request, session
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User


def get_current_user_optional() -> Optional[User]:
    """
    Get current authenticated user (optional)
    
    Returns:
        User instance if authenticated, None otherwise
    """
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        
        if user_id:
            user = User.query.get(int(user_id))
            if user and user.is_active:
                return user
        
        return None
    except Exception:
        return None


def get_current_user() -> User:
    """
    Get current authenticated user (required)
    
    Returns:
        User instance
        
    Raises:
        Exception if not authenticated
    """
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        
        if not user_id:
            raise Exception("Authentication required")
        
        user = User.query.get(int(user_id))
        if not user or not user.is_active:
            raise Exception("User not found or inactive")
        
        return user
    except Exception as e:
        raise Exception(f"Authentication failed: {str(e)}")


def get_session_id() -> str:
    """
    Get or create session ID for guest users
    
    Returns:
        Session ID string
    """
    # Try to get from session first
    session_id = session.get('cart_session_id')
    
    if not session_id:
        # Try to get from headers
        session_id = request.headers.get('X-Session-ID')
    
    if not session_id:
        # Generate new session ID
        session_id = str(uuid.uuid4())
        session['cart_session_id'] = session_id
    
    return session_id


def require_auth():
    """
    Decorator function to require authentication
    
    Returns:
        Current user if authenticated
        
    Raises:
        Exception if not authenticated
    """
    return get_current_user()