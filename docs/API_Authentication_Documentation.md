# API Authentication Documentation
## Online Learning System - Backend API

**Base URL:** `http://localhost:5000/api`  
**Version:** 1.0  
**Last Updated:** 2025-09-20

---

## 📋 Table of Contents

1. [Authentication Overview](#authentication-overview)
2. [User Registration](#user-registration)
3. [User Login](#user-login)
4. [Email Confirmation](#email-confirmation)
5. [User Profile Management](#user-profile-management)
6. [JWT Token Management](#jwt-token-management)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Frontend Integration Examples](#frontend-integration-examples)

---

## 🔐 Authentication Overview

### Authentication Flow
1. **Registration** → User creates account → Email confirmation sent
2. **Email Confirmation** → User clicks link → Account verified
3. **Login** → User provides credentials → JWT tokens returned
4. **API Access** → Include JWT token in Authorization header

### Token Types
- **Access Token**: Short-lived (1 hour), used for API requests
- **Refresh Token**: Long-lived (30 days), used to get new access tokens

### Headers Required
```http
Content-Type: application/json
Authorization: Bearer <access_token>  # For protected endpoints
```

---

## 👤 User Registration

### Endpoint
```http
POST /api/auth/register
```

### Request Body
```json
{
  "email": "user@example.com",
  "password": "StrongPassword123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student"  // Optional: "student" (default) or "instructor"
}
```

### Validation Rules
- **Email**: Valid email format, must be unique
- **Password**: Minimum 8 characters, must contain:
  - At least 1 uppercase letter
  - At least 1 lowercase letter  
  - At least 1 number
- **First Name**: Minimum 2 characters
- **Last Name**: Minimum 2 characters
- **Role**: "student" or "instructor" (defaults to "student")

### Success Response (201)
```json
{
  "success": true,
  "message": "Tài khoản được tạo thành công. Tài khoản đã được tạo. Email xác nhận sẽ được gửi sau.",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "student",
    "is_active": true,
    "is_verified": false,
    "profile_image": null,
    "created_at": "2025-09-20T10:30:00",
    "confirmed_at": null
  }
}
```

### Error Responses

#### Validation Error (400)
```json
{
  "success": false,
  "error": "Validation failed",
  "details": {
    "email": ["Email đã được sử dụng"],
    "password": ["Password must contain at least one uppercase letter"]
  }
}
```

#### Rate Limit Error (429)
```json
{
  "success": false,
  "error": "Too Many Requests",
  "message": "20 per 1 minute"
}
```

### Frontend Example
```javascript
// Registration function
async function registerUser(userData) {
  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Show success message
      alert('Registration successful! Please check your email for confirmation.');
      return data.user;
    } else {
      // Handle validation errors
      displayErrors(data.details);
      return null;
    }
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
}

// Usage
const newUser = await registerUser({
  email: 'john@example.com',
  password: 'StrongPassword123',
  first_name: 'John',
  last_name: 'Doe',
  role: 'student'
});
```

---

## 🔑 User Login

### Endpoint
```http
POST /api/auth/login
```

### Request Body
```json
{
  "email": "user@example.com",
  "password": "StrongPassword123",
  "remember_me": false  // Optional: extends token lifetime
}
```

### Success Response (200)
```json
{
  "success": true,
  "message": "Đăng nhập thành công",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "student",
    "is_active": true,
    "is_verified": true,
    "profile_image": null,
    "last_login_at": "2025-09-20T10:35:00"
  }
}
```

### Error Responses

#### Invalid Credentials (401)
```json
{
  "success": false,
  "error": "Thông tin đăng nhập không chính xác"
}
```

#### Account Locked (423)
```json
{
  "success": false,
  "error": "Tài khoản đã bị khóa do nhiều lần đăng nhập sai. Vui lòng thử lại sau."
}
```

#### Account Disabled (403)
```json
{
  "success": false,
  "error": "Tài khoản đã bị vô hiệu hóa"
}
```

### Frontend Example
```javascript
// Login function
async function loginUser(credentials) {
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(credentials)
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      return data;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

// Usage
try {
  const loginResult = await loginUser({
    email: 'john@example.com',
    password: 'StrongPassword123'
  });
  
  // Redirect to dashboard
  window.location.href = '/dashboard';
} catch (error) {
  alert('Login failed: ' + error.message);
}
```

---

## ✉️ Email Confirmation

### Confirm Email
```http
GET /api/auth/confirm-email/<token>
```

### Success Response (200)
```json
{
  "success": true,
  "message": "Email đã được xác nhận thành công! Bạn có thể đăng nhập ngay bây giờ."
}
```

### Error Response (400)
```json
{
  "success": false,
  "error": "Invalid or expired confirmation token"
}
```

### Resend Confirmation Email
```http
POST /api/auth/resend-confirmation
```

### Request Body
```json
{
  "email": "user@example.com"
}
```

### Success Response (200)
```json
{
  "success": true,
  "message": "Email xác nhận đã được gửi lại."
}
```

### Frontend Example
```javascript
// Resend confirmation email
async function resendConfirmation(email) {
  try {
    const response = await fetch('/api/auth/resend-confirmation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email })
    });
    
    const data = await response.json();
    
    if (data.success) {
      alert('Confirmation email sent! Please check your inbox.');
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Resend confirmation error:', error);
    throw error;
  }
}
```

---

## 👥 User Profile Management

### Get Current User Profile
```http
GET /api/users/profile
Authorization: Bearer <access_token>
```

### Success Response (200)
```json
{
  "success": true,
  "profile": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "student",
    "is_active": true,
    "is_verified": true,
    "profile_image": "uploads/avatars/user_1_1234567890.jpg",
    "created_at": "2025-09-20T10:30:00",
    "total_enrollments": 3,
    "completed_courses": 1,
    "join_date": "September 2025"
  }
}
```

### Update User Profile
```http
PUT /api/users/profile
Authorization: Bearer <access_token>
```

### Request Body
```json
{
  "first_name": "John Updated",
  "last_name": "Doe Updated"
}
```

### Success Response (200)
```json
{
  "success": true,
  "message": "Thông tin profile đã được cập nhật thành công",
  "profile": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John Updated",
    "last_name": "Doe Updated",
    "full_name": "John Updated Doe Updated",
    // ... other fields
  }
}
```

### Upload Avatar
```http
POST /api/users/upload-avatar
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

### Request Body (Form Data)
```
file: <image_file>  // JPG, PNG, GIF, max 2MB
```

### Success Response (200)
```json
{
  "success": true,
  "message": "Avatar đã được cập nhật thành công",
  "profile_image": "uploads/avatars/user_1_1234567890.jpg"
}
```

### Error Response (400)
```json
{
  "success": false,
  "error": "File quá lớn, tối đa 2MB"
}
```

### Get User Dashboard
```http
GET /api/users/dashboard
Authorization: Bearer <access_token>
```

### Success Response (200)
```json
{
  "success": true,
  "dashboard": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "student"
    },
    "statistics": {
      "total_enrollments": 0,
      "completed_courses": 0,
      "in_progress_courses": 0,
      "total_learning_time": 0
    },
    "recent_courses": [],
    "achievements": []
  }
}
```

### Frontend Example
```javascript
// Get user profile
async function getUserProfile() {
  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch('/api/users/profile', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
      return data.profile;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Get profile error:', error);
    throw error;
  }
}

// Update profile
async function updateProfile(profileData) {
  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch('/api/users/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(profileData)
    });
    
    const data = await response.json();
    
    if (data.success) {
      return data.profile;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Update profile error:', error);
    throw error;
  }
}

// Upload avatar
async function uploadAvatar(file) {
  try {
    const token = localStorage.getItem('access_token');
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/users/upload-avatar', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });
    
    const data = await response.json();
    
    if (data.success) {
      return data.profile_image;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Upload avatar error:', error);
    throw error;
  }
}
```

---

## 🔄 JWT Token Management

### Refresh Access Token
```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

### Success Response (200)
```json
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Get Current User Info
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

### Success Response (200)
```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student",
    "is_verified": true
  }
}
```

### Logout
```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

### Success Response (200)
```json
{
  "success": true,
  "message": "Đăng xuất thành công"
}
```

### Frontend Token Management
```javascript
// Token refresh utility
async function refreshAccessToken() {
  try {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
      localStorage.setItem('access_token', data.access_token);
      return data.access_token;
    } else {
      // Refresh token expired, redirect to login
      logout();
      return null;
    }
  } catch (error) {
    console.error('Token refresh error:', error);
    logout();
    return null;
  }
}

// API request with automatic token refresh
async function apiRequest(url, options = {}) {
  let token = localStorage.getItem('access_token');
  
  const makeRequest = async (accessToken) => {
    return fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
        ...options.headers
      }
    });
  };
  
  let response = await makeRequest(token);
  
  // If token expired, try to refresh
  if (response.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      response = await makeRequest(newToken);
    }
  }
  
  return response;
}

// Logout function
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.href = '/login';
}
```

---

## ⚠️ Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": "Error type or message",
  "message": "Detailed error description",
  "details": {
    // Field-specific validation errors
  }
}
```

### HTTP Status Codes
- **200**: Success
- **201**: Created (successful registration)
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (invalid credentials, expired token)
- **403**: Forbidden (account disabled, insufficient permissions)
- **404**: Not Found (resource not found)
- **423**: Locked (account locked due to failed attempts)
- **429**: Too Many Requests (rate limit exceeded)
- **500**: Internal Server Error

### Frontend Error Handling
```javascript
// Generic error handler
function handleApiError(error, response) {
  if (response) {
    switch (response.status) {
      case 400:
        // Validation errors
        if (response.data && response.data.details) {
          displayValidationErrors(response.data.details);
        } else {
          alert('Invalid request: ' + response.data.error);
        }
        break;
      
      case 401:
        // Unauthorized - redirect to login
        logout();
        break;
      
      case 403:
        alert('Access denied: ' + response.data.error);
        break;
      
      case 423:
        alert('Account locked: ' + response.data.error);
        break;
      
      case 429:
        alert('Too many requests. Please try again later.');
        break;
      
      case 500:
        alert('Server error. Please try again later.');
        break;
      
      default:
        alert('An error occurred: ' + response.data.error);
    }
  } else {
    alert('Network error: ' + error.message);
  }
}

// Display validation errors
function displayValidationErrors(errors) {
  for (const [field, messages] of Object.entries(errors)) {
    const fieldElement = document.querySelector(`[name="${field}"]`);
    if (fieldElement) {
      // Show error message near the field
      showFieldError(fieldElement, messages[0]);
    }
  }
}
```

---

## 🚦 Rate Limiting

### Current Limits
- **Registration**: 20 requests per minute
- **Login**: 10 requests per minute  
- **Email Confirmation Resend**: 3 requests per minute
- **General API**: 200 requests per day, 50 requests per hour

### Rate Limit Headers
```http
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 19
X-RateLimit-Reset: 1632150000
```

### Rate Limit Error Response (429)
```json
{
  "success": false,
  "error": "Too Many Requests",
  "message": "20 per 1 minute"
}
```

---

## 🚀 Frontend Integration Examples

### React Hook for Authentication
```javascript
import { useState, useEffect, createContext, useContext } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in on app start
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const login = async (credentials) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });
      
      const data = await response.json();
      
      if (data.success) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        setUser(data.user);
        return data;
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const register = async (userData) => {
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });
      
      const data = await response.json();
      
      if (data.success) {
        return data;
      } else {
        throw new Error(data.error || 'Registration failed');
      }
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      logout,
      register,
      loading,
      isAuthenticated: !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### Protected Route Component
```javascript
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
```

### API Service Class
```javascript
class ApiService {
  constructor() {
    this.baseURL = '/api';
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = localStorage.getItem('access_token');

    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Auth methods
  async register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  async login(credentials) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
  }

  async getProfile() {
    return this.request('/users/profile');
  }

  async updateProfile(profileData) {
    return this.request('/users/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  }

  async uploadAvatar(file) {
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/users/upload-avatar', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it for FormData
      body: formData
    });
  }
}

export const apiService = new ApiService();
```

---

## 📝 Notes for Frontend Developers

### Security Best Practices
1. **Store tokens securely**: Use httpOnly cookies in production instead of localStorage
2. **Validate on client**: Implement client-side validation matching server rules
3. **Handle token expiry**: Implement automatic token refresh
4. **Logout on errors**: Clear tokens on 401 responses
5. **HTTPS only**: Never send tokens over HTTP in production

### Performance Tips
1. **Cache user data**: Store user info locally to avoid repeated API calls
2. **Debounce validation**: Don't validate on every keystroke
3. **Lazy load**: Load user profile data only when needed
4. **Optimize images**: Compress avatar uploads before sending

### Testing
1. **Test all error scenarios**: Invalid credentials, expired tokens, validation errors
2. **Test rate limiting**: Ensure UI handles rate limit responses gracefully
3. **Test offline**: Handle network errors appropriately
4. **Test token refresh**: Ensure seamless user experience during token refresh

---

## 🔗 Related Documentation

- [User Stories Specification](../tasks.md)
- [Database Schema](../design.md)
- [Unit Tests](../unittest/README.md)
- [Deployment Guide](../README.md)

---

**Contact:** Backend Team  
**Last Updated:** 2025-09-20  
**API Version:** 1.0