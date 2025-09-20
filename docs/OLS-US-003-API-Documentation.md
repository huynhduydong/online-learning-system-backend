# User Profile Management API Documentation (OLS-US-003)

## Overview

API endpoints cho User Profile Management cho phép người dùng đã đăng nhập xem và cập nhật thông tin cá nhân, bao gồm tên, ảnh đại diện và thống kê tài khoản.

## Base URL
```
http://localhost:5000/api/users
```

## Authentication
Tất cả endpoints yêu cầu JWT authentication token trong header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### 1. GET /profile
Lấy thông tin profile của user hiện tại.

#### Request
```http
GET /api/users/profile
Authorization: Bearer <access_token>
```

#### Response Success (200)
```json
{
  "success": true,
  "profile": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "profile_image": "uploads/avatars/user_1_1640995200.jpg",
    "role": "student",
    "is_active": true,
    "is_verified": true,
    "created_at": "2024-01-01T00:00:00",
    "last_login_at": "2024-01-15T10:30:00",
    "last_activity_at": "2024-01-15T10:35:00",
    "confirmed_at": "2024-01-01T00:15:00",
    "total_enrollments": 5,
    "completed_courses": 2,
    "in_progress_courses": 3,
    "join_date": "January 2024"
  }
}
```

#### Response Error (401)
```json
{
  "success": false,
  "error": "Authentication failed"
}
```

#### Response Error (404)
```json
{
  "success": false,
  "error": "User not found"
}
```

---

### 2. PUT /profile
Cập nhật thông tin profile của user.

#### Request
```http
PUT /api/users/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Smith"
}
```

#### Request Body Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| first_name | string | No | Tên mới (tối thiểu 2 ký tự) |
| last_name | string | No | Họ mới (tối thiểu 2 ký tự) |

**Lưu ý:** Email không thể thay đổi sau khi tạo tài khoản.

#### Response Success (200)
```json
{
  "success": true,
  "message": "Thông tin profile đã được cập nhật thành công",
  "profile": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Smith",
    "full_name": "John Smith",
    "profile_image": "uploads/avatars/user_1_1640995200.jpg",
    "role": "student",
    "is_active": true,
    "is_verified": true,
    "created_at": "2024-01-01T00:00:00"
  },
  "changes": {
    "last_name": {
      "old": "Doe",
      "new": "Smith"
    }
  }
}
```

#### Response Error (400) - Validation Failed
```json
{
  "success": false,
  "error": "Validation failed",
  "details": {
    "first_name": ["First name must be at least 2 characters long"]
  }
}
```

#### Response Error (400) - Email Change Attempted
```json
{
  "success": false,
  "error": "Email cannot be changed",
  "message": "Email address cannot be modified after account creation"
}
```

---

### 3. POST /upload-avatar
Upload ảnh đại diện cho user.

#### Request
```http
POST /api/users/upload-avatar
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <image_file>
```

#### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | File ảnh (JPG, PNG, GIF), tối đa 2MB |

#### Business Rules
- Chỉ chấp nhận file JPG, PNG, GIF
- Kích thước tối đa: 2MB
- Ảnh sẽ được resize về 200x200px tự động
- Ảnh cũ sẽ được xóa khi upload ảnh mới

#### Response Success (200)
```json
{
  "success": true,
  "message": "Avatar đã được cập nhật thành công",
  "profile_image": "uploads/avatars/user_1_1640995300.jpg",
  "profile": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "profile_image": "uploads/avatars/user_1_1640995300.jpg",
    "role": "student"
  }
}
```

#### Response Error (400) - No File
```json
{
  "success": false,
  "error": "No file provided"
}
```

#### Response Error (400) - Invalid File Type
```json
{
  "success": false,
  "error": "Invalid file type. Only JPG, PNG, GIF files are allowed"
}
```

#### Response Error (400) - File Too Large
```json
{
  "success": false,
  "error": "File quá lớn, tối đa 2MB"
}
```

#### Response Error (500) - Processing Failed
```json
{
  "success": false,
  "error": "Failed to process image"
}
```

---

### 4. DELETE /remove-avatar
Xóa ảnh đại diện của user.

#### Request
```http
DELETE /api/users/remove-avatar
Authorization: Bearer <access_token>
```

#### Response Success (200)
```json
{
  "success": true,
  "message": "Avatar đã được xóa thành công",
  "profile": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "profile_image": null,
    "role": "student"
  }
}
```

#### Response Success (200) - No Avatar to Remove
```json
{
  "success": true,
  "message": "No avatar to remove",
  "profile": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "profile_image": null,
    "role": "student"
  }
}
```

---

### 5. GET /avatar-info
Lấy thông tin về ảnh đại diện của user.

#### Request
```http
GET /api/users/avatar-info
Authorization: Bearer <access_token>
```

#### Response Success (200)
```json
{
  "success": true,
  "avatar_info": {
    "has_avatar": true,
    "avatar_path": "uploads/avatars/user_1_1640995200.jpg",
    "avatar_url": "/uploads/avatars/user_1_1640995200.jpg",
    "format": "JPEG",
    "mode": "RGB",
    "size": [200, 200],
    "file_size": 15420
  }
}
```

#### Response Success (200) - No Avatar
```json
{
  "success": true,
  "avatar_info": {
    "has_avatar": false,
    "avatar_path": null,
    "avatar_url": null
  }
}
```

---

### 6. GET /dashboard
Lấy thông tin dashboard của user (kế thừa từ OLS-US-002).

#### Request
```http
GET /api/users/dashboard
Authorization: Bearer <access_token>
```

#### Response Success (200)
```json
{
  "success": true,
  "dashboard": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "profile_image": "uploads/avatars/user_1_1640995200.jpg",
      "role": "student"
    },
    "welcome_message": "Chào mừng trở lại, John!",
    "statistics": {
      "total_enrollments": 5,
      "completed_courses": 2,
      "in_progress_courses": 3,
      "total_learning_time": 0
    },
    "recent_courses": [],
    "achievements": [],
    "notifications": [],
    "quick_actions": [
      {
        "title": "Khám phá khóa học",
        "description": "Tìm kiếm khóa học phù hợp với bạn",
        "action": "browse_courses",
        "icon": "search"
      },
      {
        "title": "Tiếp tục học",
        "description": "Quay lại khóa học đang học",
        "action": "continue_learning",
        "icon": "play"
      }
    ]
  }
}
```

## Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Validation Error | Dữ liệu đầu vào không hợp lệ |
| 401 | Authentication Error | Token không hợp lệ hoặc hết hạn |
| 403 | Authorization Error | Không có quyền truy cập |
| 404 | Not Found | User không tồn tại |
| 413 | Payload Too Large | File upload quá lớn |
| 422 | Unprocessable Entity | JWT token không đúng định dạng |
| 429 | Too Many Requests | Vượt quá rate limit |
| 500 | Internal Server Error | Lỗi server nội bộ |

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| GET /profile | 30 requests/minute |
| PUT /profile | 10 requests/minute |
| POST /upload-avatar | 5 requests/minute |
| DELETE /remove-avatar | 10 requests/minute |
| GET /avatar-info | No limit |
| GET /dashboard | No limit |

## Security Features

### Input Validation
- Tất cả input được validate và sanitize
- Tên phải có ít nhất 2 ký tự và chỉ chứa ký tự hợp lệ
- File upload được kiểm tra định dạng và kích thước

### File Security
- Chỉ chấp nhận file ảnh hợp lệ (JPG, PNG, GIF)
- Kiểm tra nội dung file để phát hiện malicious content
- Tên file được tạo an toàn với timestamp
- File cũ được xóa tự động khi upload file mới

### Authentication & Authorization
- Tất cả endpoints yêu cầu JWT token hợp lệ
- User chỉ có thể truy cập profile của chính mình
- Session tracking và timeout tự động

### Audit Logging
- Tất cả thay đổi profile được ghi log
- Security events được monitor
- File operations được track

## Example Usage

### JavaScript/Fetch Example

```javascript
// Get profile
const getProfile = async () => {
  const response = await fetch('/api/users/profile', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  const data = await response.json();
  return data;
};

// Update profile
const updateProfile = async (firstName, lastName) => {
  const response = await fetch('/api/users/profile', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      first_name: firstName,
      last_name: lastName
    })
  });
  const data = await response.json();
  return data;
};

// Upload avatar
const uploadAvatar = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/users/upload-avatar', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    },
    body: formData
  });
  const data = await response.json();
  return data;
};
```

### cURL Examples

```bash
# Get profile
curl -X GET http://localhost:5000/api/users/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Update profile
curl -X PUT http://localhost:5000/api/users/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Smith"
  }'

# Upload avatar
curl -X POST http://localhost:5000/api/users/upload-avatar \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@avatar.jpg"

# Remove avatar
curl -X DELETE http://localhost:5000/api/users/remove-avatar \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Testing

Để test các API endpoints, bạn có thể sử dụng:

1. **Unit Tests**: `python tests/test_user_profile.py`
2. **Manual Testing**: Sử dụng các script test đã tạo:
   - `python test_profile_simple.py`
   - `python test_avatar_simple.py`
3. **API Testing Tools**: Postman, Insomnia, hoặc curl

## File Storage

### Avatar Storage Structure
```
uploads/
└── avatars/
    ├── user_1_1640995200.jpg
    ├── user_2_1640995300.jpg
    └── user_N_timestamp.jpg
```

### File Naming Convention
- Format: `user_{user_id}_{timestamp}.jpg`
- Tất cả ảnh được convert về JPEG format
- Timestamp đảm bảo tên file unique

### Storage Management
- Ảnh cũ được xóa tự động khi upload ảnh mới
- File được resize về 200x200px để tiết kiệm storage
- Chất lượng ảnh được optimize (85% quality)

## Business Rules Summary

1. **Email Immutability**: Email không thể thay đổi sau khi tạo tài khoản
2. **Name Validation**: Tên phải có ít nhất 2 ký tự, tối đa 100 ký tự
3. **Avatar Size**: Ảnh đại diện tối đa 2MB, được resize về 200x200px
4. **File Formats**: Chỉ chấp nhận JPG, PNG, GIF
5. **Audit Trail**: Tất cả thay đổi profile được ghi log
6. **Session Management**: Session timeout sau 24h không hoạt động
7. **Rate Limiting**: Giới hạn số request để tránh abuse

## Future Enhancements

1. **CDN Integration**: Serve avatar images từ CDN
2. **Image Optimization**: Thêm WebP format support
3. **Bulk Operations**: API để update multiple fields cùng lúc
4. **Profile Visibility**: Settings để control profile visibility
5. **Social Features**: Profile sharing và social links