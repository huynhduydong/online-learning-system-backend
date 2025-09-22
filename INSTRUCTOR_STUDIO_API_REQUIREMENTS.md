# Instructor Studio - API Requirements

## 📋 Danh Sách API Endpoints Cần Backend Cung Cấp

> **📅 Cập nhật**: 2025-09-21  
> **✅ Tình trạng**: Đã triển khai hoàn tất  
> **🔗 Base URL**: `http://localhost:5000/api`

### **1. Authentication & Authorization**

#### **1.1 Login Enhancement** ✅ **IMPLEMENTED**
```http
POST /api/auth/login
```

**Current Response cần bổ sung:**
```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "expires_in": 3600,
  "user": {
    "id": 117,
    "email": "instructor@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "instructor", // ⚠️ Quan trọng: cần support role "instructor"
    "is_active": true,
    "is_verified": true,
    "profile_image": "/avatar.jpg",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login_at": "2024-01-15T10:30:00Z"
  }
}
```

### **2. Instructor Course Management**

#### **2.1 Get Instructor's Courses** ✅ **IMPLEMENTED**
```http
GET /api/instructor/courses
```

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**
- `page` (optional): Page number, default = 1
- `per_page` (optional): Items per page, default = 10
- `status` (optional): "draft" | "published" | "all", default = "all"
- `sort_by` (optional): "created_at" | "updated_at" | "title", default = "updated_at"
- `sort_order` (optional): "asc" | "desc", default = "desc"

**Response:**
```json
{
  "success": true,
  "message": "Courses retrieved successfully",
  "data": {
    "courses": [
      {
        "id": 1,
        "title": "Advanced React Development",
        "short_description": "Learn React from basics to advanced",
        "slug": "advanced-react-development",
        "status": "published", // "draft" | "published"
        "language": "vi",
        "difficulty_level": "intermediate", // "beginner" | "intermediate" | "advanced"
        "category": {
          "id": 1,
          "name": "Programming",
          "slug": "programming"
        },
        "price": {
          "amount": 299000,
          "is_free": false,
          "currency": "VND"
        },
        "thumbnail_url": "https://example.com/thumbnail.jpg",
        "stats": {
          "total_enrollments": 45,
          "total_lessons": 12,
          "duration_hours": 8.5
        },
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-02-01T15:30:00Z",
        "published_at": "2024-01-20T09:00:00Z" // null if draft
      }
    ],
    "pagination": {
      "current_page": 1,
      "per_page": 10,
      "total": 25,
      "total_pages": 3,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

#### **2.2 Create New Course** ✅ **IMPLEMENTED**
```http
POST /api/instructor/courses
```

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Payload:**
```json
{
  "title": "TypeScript Fundamentals", // Required
  "short_description": "Master TypeScript from basics to advanced", // Required
  "slug": "typescript-fundamentals", // Auto-generated from title
  "language": "vi", // Optional, default "vi"
  "difficulty_level": "beginner", // Optional, default "beginner"
  "category_id": 1, // Optional
  "price": 0, // Optional, default 0
  "is_free": true, // Optional, default true
  "status": "draft" // Always "draft" for new courses
}
```

**Response:**
```json
{
  "success": true,
  "message": "Course created successfully",
  "data": {
    "id": 123,
    "title": "TypeScript Fundamentals",
    "short_description": "Master TypeScript from basics to advanced",
    "slug": "typescript-fundamentals",
    "status": "draft",
    "language": "vi",
    "difficulty_level": "beginner",
    "category": {
      "id": 1,
      "name": "Programming",
      "slug": "programming"
    },
    "price": {
      "amount": 0,
      "is_free": true,
      "currency": "VND"
    },
    "thumbnail_url": null,
    "stats": {
      "total_enrollments": 0,
      "total_lessons": 0,
      "duration_hours": 0
    },
    "created_at": "2024-02-15T10:00:00Z",
    "updated_at": "2024-02-15T10:00:00Z",
    "published_at": null
  }
}
```

#### **2.3 Get Single Course Details** ✅ **IMPLEMENTED**
```http
GET /api/instructor/courses/{id}
```

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "message": "Course retrieved successfully",
  "data": {
    "id": 123,
    "title": "TypeScript Fundamentals",
    "short_description": "Master TypeScript from basics to advanced",
    "description": "Full detailed description...", // Optional long description
    "slug": "typescript-fundamentals",
    "status": "draft",
    "language": "vi",
    "difficulty_level": "beginner",
    "category": {
      "id": 1,
      "name": "Programming",
      "slug": "programming"
    },
    "price": {
      "amount": 299000,
      "is_free": false,
      "currency": "VND"
    },
    "thumbnail_url": "https://example.com/thumbnail.jpg",
    "preview_video_url": null,
    "requirements": ["Basic JavaScript knowledge"],
    "what_you_will_learn": ["TypeScript basics", "Advanced types"],
    "tags": ["typescript", "javascript", "programming"],
    "stats": {
      "total_enrollments": 0,
      "total_lessons": 5,
      "duration_hours": 3.5
    },
    "created_at": "2024-02-15T10:00:00Z",
    "updated_at": "2024-02-15T15:30:00Z",
    "published_at": null
  }
}
```

#### **2.4 Update Course** ✅ **IMPLEMENTED**
```http
PUT /api/instructor/courses/{id}
```

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Payload:**
```json
{
  "title": "TypeScript Fundamentals - Updated",
  "short_description": "Updated description",
  "slug": "typescript-fundamentals-updated",
  "language": "en",
  "difficulty_level": "intermediate",
  "category_id": 2,
  "price": 399000,
  "is_free": false
  // Note: status không được update qua endpoint này
}
```

**Response:**
```json
{
  "success": true,
  "message": "Course updated successfully",
  "data": {
    // Full course object với thông tin đã update
    "id": 123,
    "title": "TypeScript Fundamentals - Updated",
    // ... rest of course data
    "updated_at": "2024-02-15T16:00:00Z"
  }
}
```

#### **2.5 Publish Course** ✅ **IMPLEMENTED**
```http
POST /api/instructor/courses/{id}/publish
```

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Payload:** (Empty body hoặc optional validation)
```json
{}
```

**Response:**
```json
{
  "success": true,
  "message": "Course published successfully",
  "data": {
    "id": 123,
    "status": "published",
    "published_at": "2024-02-15T16:30:00Z",
    "public_url": "https://yoursite.com/courses/typescript-fundamentals-updated"
  }
}
```

#### **2.6 Unpublish Course** ✅ **IMPLEMENTED**
```http
POST /api/instructor/courses/{id}/unpublish
```

**Response:**
```json
{
  "success": true,
  "message": "Course unpublished successfully",
  "data": {
    "id": 123,
    "status": "draft",
    "published_at": null
  }
}
```

#### **2.7 Delete Course** ✅ **IMPLEMENTED**
```http
DELETE /api/instructor/courses/{id}
```

**Response:**
```json
{
  "success": true,
  "message": "Course deleted successfully"
}
```

### **3. Supporting Data APIs**

#### **3.1 Get Categories** ✅ **IMPLEMENTED**
```http
GET /api/courses/categories
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Programming",
      "slug": "programming",
      "description": "Programming and software development courses"
    },
    {
      "id": 2,
      "name": "Design",
      "slug": "design",
      "description": "Design and creativity courses"
    }
  ]
}
```

#### **3.2 Get Languages** ✅ **IMPLEMENTED**
```http
GET /api/courses/languages
```

**Response:**
```json
{
  "success": true,
  "data": [
    { "code": "vi", "name": "Vietnamese" },
    { "code": "en", "name": "English" },
    { "code": "zh", "name": "Chinese" }
  ]
}
```

### **4. Error Responses**

**Validation Errors (400):**
```json
{
  "success": false,
  "error": "Validation failed",
  "message": "The given data was invalid",
  "details": {
    "title": ["The title field is required"],
    "short_description": ["The short description must not exceed 500 characters"]
  }
}
```

**Unauthorized (401):**
```json
{
  "success": false,
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

**Forbidden (403):**
```json
{
  "success": false,
  "error": "Forbidden",
  "message": "You don't have permission to access this resource"
}
```

**Not Found (404):**
```json
{
  "success": false,
  "error": "Not Found",
  "message": "Course not found"
}
```

**Server Error (500):**
```json
{
  "success": false,
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

### **5. Business Rules & Validation**

#### **5.1 Course Creation Rules:**
- Title: Required, 1-100 characters
- Short description: Required, 1-500 characters
- Slug: Auto-generated from title, must be unique
- Status: Always "draft" when created
- Instructor ID: Automatically set from authenticated user

#### **5.2 Course Publishing Rules:**
- Only draft courses can be published
- Published courses can be unpublished back to draft
- Course must have minimum required content (implement based on business needs)

#### **5.3 Authorization Rules:**
- Only instructors can access `/api/instructor/*` endpoints
- Instructors can only manage their own courses
- Admin can manage all courses (if needed)

### **6. Database Schema Requirements**

```

### **7. Frontend Integration Points**

Khi có real APIs, cần thay thế:

1. **Mock handlers** trong `src/mocks/handlers.ts`
2. **API service methods** trong `lib/api/instructor.ts` (tạo mới)
3. **Course store updates** để sử dụng real data
4. **Form submissions** trong create/edit pages

### **8. Testing Requirements**

Backend cần cung cấp:
- **Unit tests** cho tất cả endpoints
- **Integration tests** cho instructor workflow
- **Postman collection** hoặc OpenAPI documentation
- **Seeder data** cho development/testing

### **9. Additional Features (Future)**

Có thể mở rộng sau:
- Course analytics/statistics
- Student management
- Course reviews management
- Bulk course operations
- Course templates
- Content management (lessons, videos, quizzes)

---

**📌 Priority Implementation Order:**
1. ✅ Authentication with instructor role
2. ✅ Get instructor courses (2.1)
3. ✅ Create course (2.2)
4. ✅ Update course (2.4)
5. ✅ Publish course (2.5)
6. ✅ Supporting data APIs (3.1, 3.2)

---

## 🔧 **Thông Tin Triển Khai**

### **✅ Đã Có Sẵn Trong Codebase:**

#### **User System & Authentication:**
- ✅ User model với UserRole enum (`student`, `instructor`, `admin`)
- ✅ JWT authentication system
- ✅ Role-based authorization với `@instructor_required` decorator
- ✅ Enhanced login response với đầy đủ thông tin user

#### **Course System:**
- ✅ Course model với đầy đủ relationships
- ✅ CourseStatus enum: `draft`, `published`, `archived`
- ✅ DifficultyLevel enum: `beginner`, `intermediate`, `advanced`
- ✅ Category model với slug support
- ✅ Auto slug generation từ course title

#### **Database Schema:**
- ✅ Users table với role support
- ✅ Courses table với instructor foreign key
- ✅ Categories table
- ✅ Migration files đã setup

### **🆕 APIs Đã Triển Khai:**

#### **Instructor Management:**
- ✅ `GET /api/instructor/courses` - Lấy danh sách khóa học của instructor
- ✅ `POST /api/instructor/courses` - Tạo khóa học mới
- ✅ `GET /api/instructor/courses/{id}` - Lấy chi tiết khóa học
- ✅ `PUT /api/instructor/courses/{id}` - Cập nhật khóa học
- ✅ `POST /api/instructor/courses/{id}/publish` - Publish khóa học
- ✅ `POST /api/instructor/courses/{id}/unpublish` - Unpublish khóa học
- ✅ `DELETE /api/instructor/courses/{id}` - Xóa khóa học

#### **Supporting APIs:**
- ✅ `GET /api/courses/categories` - Lấy danh sách categories
- ✅ `GET /api/courses/languages` - Lấy danh sách ngôn ngữ

### **🔒 Authorization Rules:**
- ✅ Chỉ instructor và admin mới access được `/api/instructor/*`
- ✅ Instructor chỉ quản lý được courses của mình
- ✅ Auto-verify instructor permissions trong mỗi request

### **📝 Validation & Business Rules:**
- ✅ Course title: 1-100 ký tự
- ✅ Short description: 1-500 ký tự  
- ✅ Auto-generate unique slug từ title
- ✅ Course status luôn là "draft" khi tạo mới
- ✅ Validate pricing consistency (free/paid)

### **🚀 Ready for Frontend Integration:**
Tất cả API endpoints đã sẵn sàng sử dụng với:
- ✅ Consistent response format
- ✅ Proper error handling
- ✅ Input validation
- ✅ JWT authentication
- ✅ Role-based authorization
