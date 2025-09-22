# 📚 Course Lessons & Progress Tracking API Documentation

## 🎯 Overview

API này cung cấp 5 endpoints để quản lý bài học và theo dõi tiến trình học tập của user trong khóa học.

## 🔐 Authentication

**Tất cả APIs đều yêu cầu JWT Authentication:**
```
Authorization: Bearer <your_jwt_token>
```

## 📋 API Endpoints

### 1. 📖 **Get Course with All Lessons**

**Endpoint:** `GET /api/courses/{courseSlug}/lessons`

**Mô tả:** Lấy thông tin khóa học với tất cả modules, lessons và tiến trình của user

**Parameters:**
- `courseSlug` (path): Slug của khóa học

**Response:**
```json
{
  "success": true,
  "message": "Course lessons retrieved successfully",
  "data": {
    "course": {
      "id": 1,
      "title": "Python Programming Fundamentals",
      "slug": "python-programming-fundamentals",
      "description": "Learn Python from basics to advanced",
      "thumbnail_url": "https://example.com/thumbnail.jpg",
      "total_lessons": 25,
      "duration_hours": 40,
      "instructor": {
        "id": 1,
        "name": "John Doe"
      }
    },
    "progress": {
      "id": 1,
      "completed_lessons": 5,
      "total_lessons": 25,
      "completion_percentage": 20.0,
      "total_watch_time_seconds": 3600,
      "is_completed": false,
      "started_at": "2024-01-15T10:00:00Z",
      "last_accessed_at": "2024-01-20T14:30:00Z"
    },
    "modules": [
      {
        "id": 1,
        "title": "Introduction to Python",
        "sort_order": 1,
        "lessons": [
          {
            "id": 1,
            "title": "What is Python?",
            "sort_order": 1,
            "duration_minutes": 15,
            "is_preview": true,
            "progress": {
              "status": "completed",
              "completion_percentage": 100.0,
              "watch_time_seconds": 900,
              "is_completed": true,
              "last_accessed_at": "2024-01-15T10:30:00Z"
            }
          }
        ]
      }
    ]
  }
}
```

**Error Responses:**
- `400`: Invalid course slug
- `401`: Unauthorized (missing or invalid JWT)
- `404`: Course not found or user not enrolled
- `403`: User doesn't have access to course

---

### 2. 📄 **Get Specific Lesson Details**

**Endpoint:** `GET /api/courses/{courseSlug}/lessons/{lessonId}`

**Mô tả:** Lấy chi tiết bài học cụ thể với nội dung và tiến trình

**Parameters:**
- `courseSlug` (path): Slug của khóa học
- `lessonId` (path): ID của bài học

**Response:**
```json
{
  "success": true,
  "message": "Lesson details retrieved successfully",
  "data": {
    "id": 1,
    "title": "What is Python?",
    "description": "Introduction to Python programming language",
    "content_type": "video",
    "duration_minutes": 15,
    "sort_order": 1,
    "is_preview": true,
    "contents": [
      {
        "id": 1,
        "title": "Video Content",
        "content_data": null,
        "file_url": "https://example.com/video1.mp4",
        "sort_order": 1
      },
      {
        "id": 2,
        "title": "Lesson Notes",
        "content_data": "Python is a high-level programming language...",
        "file_url": null,
        "sort_order": 2
      }
    ],
    "module": {
      "id": 1,
      "title": "Introduction to Python",
      "sort_order": 1
    },
    "course": {
      "id": 1,
      "title": "Python Programming Fundamentals",
      "slug": "python-programming-fundamentals"
    },
    "progress": {
      "status": "completed",
      "watch_time_seconds": 900,
      "completion_percentage": 100.0,
      "is_completed": true,
      "started_at": "2024-01-15T10:15:00Z",
      "completed_at": "2024-01-15T10:30:00Z",
      "last_accessed_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

**Error Responses:**
- `400`: Invalid parameters
- `401`: Unauthorized
- `404`: Course or lesson not found
- `403`: Access denied

---

### 3. ✅ **Mark Lesson Complete**

**Endpoint:** `POST /api/courses/{courseSlug}/lessons/{lessonId}/complete`

**Mô tả:** Đánh dấu bài học đã hoàn thành (100%)

**Parameters:**
- `courseSlug` (path): Slug của khóa học
- `lessonId` (path): ID của bài học

**Request Body:** Không cần

**Response:**
```json
{
  "success": true,
  "message": "Lesson marked as completed",
  "data": {
    "id": 1,
    "user_id": 1,
    "lesson_id": 1,
    "course_id": 1,
    "status": "completed",
    "watch_time_seconds": 900,
    "completion_percentage": 100.0,
    "is_completed": true,
    "started_at": "2024-01-15T10:15:00Z",
    "completed_at": "2024-01-15T10:30:00Z",
    "last_accessed_at": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-15T10:15:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Responses:**
- `400`: Invalid parameters
- `401`: Unauthorized
- `404`: Course or lesson not found
- `403`: Access denied

---

### 4. 📊 **Track Lesson Progress**

**Endpoint:** `POST /api/courses/{courseSlug}/lessons/{lessonId}/progress`

**Mô tả:** Cập nhật tiến trình học và thời gian xem bài học

**Parameters:**
- `courseSlug` (path): Slug của khóa học
- `lessonId` (path): ID của bài học

**Request Body:**
```json
{
  "watch_time": 300,           // Thời gian xem (giây) - optional
  "completion_percentage": 45.5 // Phần trăm hoàn thành 0-100 - optional
}
```

**Note:** Ít nhất một trong hai fields `watch_time` hoặc `completion_percentage` phải có.

**Response:**
```json
{
  "success": true,
  "message": "Lesson progress updated successfully",
  "data": {
    "id": 1,
    "user_id": 1,
    "lesson_id": 1,
    "course_id": 1,
    "status": "in_progress",
    "watch_time_seconds": 300,
    "completion_percentage": 45.5,
    "is_completed": false,
    "started_at": "2024-01-15T10:15:00Z",
    "completed_at": null,
    "last_accessed_at": "2024-01-15T10:20:00Z",
    "created_at": "2024-01-15T10:15:00Z",
    "updated_at": "2024-01-15T10:20:00Z"
  }
}
```

**Auto-Completion:** Nếu `completion_percentage >= 100`, bài học sẽ tự động được đánh dấu hoàn thành.

**Error Responses:**
- `400`: Missing required fields hoặc invalid values
- `401`: Unauthorized
- `404`: Course or lesson not found
- `403`: Access denied

---

### 5. 📈 **Get User Course Progress**

**Endpoint:** `GET /api/users/me/courses/{courseSlug}/progress`

**Mô tả:** Lấy tổng quan tiến trình khóa học của user với breakdown theo bài học

**Parameters:**
- `courseSlug` (path): Slug của khóa học

**Response:**
```json
{
  "success": true,
  "message": "Course progress retrieved successfully",
  "data": {
    "course_progress": {
      "id": 1,
      "user_id": 1,
      "course_id": 1,
      "enrollment_id": "550e8400-e29b-41d4-a716-446655440000",
      "completed_lessons": 5,
      "total_lessons": 25,
      "completion_percentage": 20.0,
      "total_watch_time_seconds": 3600,
      "is_completed": false,
      "started_at": "2024-01-15T10:00:00Z",
      "completed_at": null,
      "last_accessed_at": "2024-01-20T14:30:00Z",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-20T14:30:00Z"
    },
    "modules": [
      {
        "id": 1,
        "title": "Introduction to Python",
        "sort_order": 1,
        "lessons": [
          {
            "id": 1,
            "title": "What is Python?",
            "sort_order": 1,
            "duration_minutes": 15,
            "is_preview": true,
            "progress": {
              "status": "completed",
              "completion_percentage": 100.0,
              "watch_time_seconds": 900,
              "is_completed": true,
              "last_accessed_at": "2024-01-15T10:30:00Z"
            }
          },
          {
            "id": 2,
            "title": "Installing Python",
            "sort_order": 2,
            "duration_minutes": 20,
            "is_preview": false,
            "progress": {
              "status": "not_started",
              "completion_percentage": 0.0,
              "watch_time_seconds": 0,
              "is_completed": false,
              "last_accessed_at": null
            }
          }
        ]
      }
    ],
    "course": {
      "id": 1,
      "title": "Python Programming Fundamentals",
      "slug": "python-programming-fundamentals",
      "description": "Learn Python from basics to advanced",
      "thumbnail_url": "https://example.com/thumbnail.jpg",
      "instructor": {
        "id": 1,
        "name": "John Doe"
      }
    }
  }
}
```

**Error Responses:**
- `400`: Invalid course slug
- `401`: Unauthorized
- `404`: Course not found or user not enrolled
- `403`: Access denied

---

## 🔄 Progress Status Values

```typescript
enum ProgressStatus {
  NOT_STARTED = 'not_started',    // Chưa bắt đầu
  IN_PROGRESS = 'in_progress',    // Đang học
  COMPLETED = 'completed'         // Đã hoàn thành
}
```

## 🚀 Usage Examples

### JavaScript/Frontend Implementation

```javascript
// 1. Get course lessons
const getCourselessons = async (courseSlug) => {
  const response = await fetch(`/api/courses/${courseSlug}/lessons`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// 2. Get lesson details
const getLessonDetails = async (courseSlug, lessonId) => {
  const response = await fetch(`/api/courses/${courseSlug}/lessons/${lessonId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// 3. Mark lesson complete
const markLessonComplete = async (courseSlug, lessonId) => {
  const response = await fetch(`/api/courses/${courseSlug}/lessons/${lessonId}/complete`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// 4. Update progress
const updateProgress = async (courseSlug, lessonId, watchTime, completionPercentage) => {
  const response = await fetch(`/api/courses/${courseSlug}/lessons/${lessonId}/progress`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      watch_time: watchTime,
      completion_percentage: completionPercentage
    })
  });
  return response.json();
};

// 5. Get user progress
const getUserProgress = async (courseSlug) => {
  const response = await fetch(`/api/users/me/courses/${courseSlug}/progress`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};
```

### cURL Examples

```bash
# 1. Get course lessons
curl -X GET "http://localhost:5000/api/courses/python-fundamentals/lessons" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 2. Get lesson details  
curl -X GET "http://localhost:5000/api/courses/python-fundamentals/lessons/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 3. Mark lesson complete
curl -X POST "http://localhost:5000/api/courses/python-fundamentals/lessons/1/complete" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 4. Update progress
curl -X POST "http://localhost:5000/api/courses/python-fundamentals/lessons/1/progress" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"watch_time": 300, "completion_percentage": 45.5}'

# 5. Get user progress
curl -X GET "http://localhost:5000/api/users/me/courses/python-fundamentals/progress" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🛡️ Security Notes

1. **Authentication Required**: Tất cả endpoints yêu cầu JWT token hợp lệ
2. **Enrollment Validation**: User phải được enrolled và có access granted
3. **Course Access Control**: Lessons phải thuộc về course được chỉ định
4. **Rate Limiting**: APIs có rate limiting để prevent abuse
5. **Input Validation**: Tất cả inputs được validate và sanitize

## 🐛 Common Error Scenarios

1. **Missing JWT Token**
   ```json
   {
     "success": false,
     "error": "Authentication required"
   }
   ```

2. **Not Enrolled in Course**
   ```json
   {
     "success": false,
     "error": "Bạn chưa đăng ký khóa học này"
   }
   ```

3. **Lesson Not Found**
   ```json
   {
     "success": false,
     "error": "Không tìm thấy bài học trong khóa học này"
   }
   ```

4. **Invalid Progress Data**
   ```json
   {
     "success": false,
     "error": "Either watch_time or completion_percentage must be provided"
   }
   ```

## 📦 Database Setup

### Migration Command
```bash
# Tạo migration
python -m flask db migrate -m "Add lesson and course progress tracking tables"

# Apply migration
python -m flask db upgrade
```

### New Tables Created
- `lesson_progress`: Individual lesson tracking
- `course_progress`: Course-wide progress summaries

## 🔧 Configuration

Đảm bảo các environment variables được set:
```
DATABASE_URL=your_database_url
JWT_SECRET_KEY=your_jwt_secret
FLASK_ENV=development  # or production
```

## 🚀 Ready to Use!

Tất cả 5 APIs đã sẵn sàng để integrate với frontend. Database models, business logic, và security đều đã được implement đầy đủ theo best practices.
