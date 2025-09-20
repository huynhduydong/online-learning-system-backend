# Frontend Quick Reference Guide
## Online Learning System API

### 🚀 Quick Start

1. **Import Postman Collection**: `docs/Online_Learning_System_API.postman_collection.json`
2. **Set Base URL**: `http://localhost:5000/api`
3. **Start with Registration/Login flow**

---

## 📋 Essential Endpoints

### Authentication Flow
```javascript
// 1. Register User
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "StrongPassword123",
  "first_name": "John",
  "last_name": "Doe"
}

// 2. Login User  
POST /api/auth/login
{
  "email": "user@example.com", 
  "password": "StrongPassword123"
}
// Returns: access_token, refresh_token

// 3. Use Token for Protected Routes
GET /api/users/profile
Headers: Authorization: Bearer <access_token>
```

---

## 🔑 Token Management

### Store Tokens
```javascript
// After successful login
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
localStorage.setItem('user', JSON.stringify(data.user));
```

### Use Tokens in Requests
```javascript
const token = localStorage.getItem('access_token');
fetch('/api/users/profile', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Auto-Refresh Tokens
```javascript
// When you get 401 response
if (response.status === 401) {
  const newToken = await refreshToken();
  // Retry request with new token
}
```

---

## ⚠️ Validation Rules

### Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter  
- At least 1 number

### Email Requirements
- Valid email format
- Must be unique in system

### File Upload (Avatar)
- Max size: 2MB
- Formats: JPG, PNG, GIF
- Auto-resized to 200x200px

---

## 🚦 Rate Limits

- **Registration**: 20/minute
- **Login**: 10/minute
- **Email Resend**: 3/minute
- **General**: 200/day, 50/hour

---

## 📊 Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { /* response data */ }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error type",
  "details": {
    "field": ["Error message"]
  }
}
```

---

## 🎯 Common Status Codes

- **200**: Success
- **201**: Created (registration)
- **400**: Validation error
- **401**: Unauthorized (bad credentials/expired token)
- **403**: Forbidden (account disabled)
- **423**: Locked (too many failed attempts)
- **429**: Rate limited
- **500**: Server error

---

## 🔧 Frontend Utilities

### API Service Class
```javascript
class ApiService {
  async request(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    
    const response = await fetch(`/api${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      ...options
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return response.json();
  }
}
```

### Error Handler
```javascript
function handleApiError(error) {
  if (error.status === 401) {
    // Redirect to login
    window.location.href = '/login';
  } else if (error.status === 400) {
    // Show validation errors
    displayErrors(error.details);
  } else {
    // Show generic error
    alert('An error occurred');
  }
}
```

---

## 🧪 Testing Checklist

### Registration Tests
- [ ] Valid registration succeeds
- [ ] Duplicate email shows error
- [ ] Weak password shows error
- [ ] Missing fields show errors
- [ ] Instructor role works
- [ ] Email confirmation sent

### Login Tests  
- [ ] Valid login succeeds
- [ ] Invalid credentials show error
- [ ] Tokens are returned
- [ ] User data is returned
- [ ] Account lockout after 5 failures

### Profile Tests
- [ ] Get profile works with token
- [ ] Update profile works
- [ ] Avatar upload works
- [ ] File size validation works
- [ ] Dashboard data loads

### Token Tests
- [ ] Protected routes require token
- [ ] Expired token returns 401
- [ ] Refresh token works
- [ ] Logout clears tokens

---

## 🎨 UI/UX Recommendations

### Registration Form
```javascript
// Show real-time password strength
function checkPasswordStrength(password) {
  const checks = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password)
  };
  
  return checks;
}
```

### Loading States
```javascript
// Show loading during API calls
const [loading, setLoading] = useState(false);

const handleSubmit = async () => {
  setLoading(true);
  try {
    await apiCall();
  } finally {
    setLoading(false);
  }
};
```

### Error Display
```javascript
// Show field-specific errors
function displayFieldErrors(errors) {
  Object.entries(errors).forEach(([field, messages]) => {
    const input = document.querySelector(`[name="${field}"]`);
    showError(input, messages[0]);
  });
}
```

---

## 📱 Mobile Considerations

- Use responsive design for all forms
- Handle touch events for file upload
- Consider biometric authentication
- Optimize for slow networks
- Handle offline scenarios

---

## 🔒 Security Best Practices

1. **Never log tokens** in console/analytics
2. **Use HTTPS** in production
3. **Validate on client** but trust server
4. **Clear tokens** on logout
5. **Handle token expiry** gracefully
6. **Use secure storage** (httpOnly cookies in production)

---

## 📞 Support

- **API Documentation**: `docs/API_Authentication_Documentation.md`
- **Postman Collection**: `docs/Online_Learning_System_API.postman_collection.json`
- **Unit Tests**: `unittest/` folder
- **Backend Team**: Contact for API issues

---

**Last Updated**: 2025-09-20  
**API Version**: 1.0