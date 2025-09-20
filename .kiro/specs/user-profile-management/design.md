# Design Document

## Overview

The User Profile Management system provides authenticated users with the ability to view and update their personal information, including profile details and avatar images. The system is built using Flask with JWT authentication, SQLAlchemy ORM for data persistence, and follows RESTful API design principles. The design emphasizes security, data validation, and user experience through proper error handling and feedback mechanisms.

## Architecture

### System Architecture
The User Profile Management feature follows a layered architecture pattern:

```
┌─────────────────────────────────────────┐
│           Frontend Client               │
│     (React/Next.js - Future)           │
└─────────────────┬───────────────────────┘
                  │ HTTP/JSON API
┌─────────────────▼───────────────────────┐
│         Flask Application Layer         │
│  ┌─────────────────────────────────────┐│
│  │     Users Blueprint (API Routes)    ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │    Authentication Middleware        ││
│  │      (JWT Token Validation)         ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │     Input Validation Layer          ││
│  │      (Marshmallow Schemas)          ││
│  └─────────────────────────────────────┘│
└─────────────────┬───────────────────────┘
                  │ SQLAlchemy ORM
┌─────────────────▼───────────────────────┐
│         Data Persistence Layer          │
│  ┌─────────────────────────────────────┐│
│  │         User Model                  ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │        MySQL Database               ││
│  └─────────────────────────────────────┘│
└─────────────────┬───────────────────────┘
                  │ File System
┌─────────────────▼───────────────────────┐
│         File Storage Layer              │
│       (Avatar Images Storage)           │
└─────────────────────────────────────────┘
```

### Technology Stack
- **Backend Framework**: Flask with Blueprint architecture
- **Authentication**: JWT (JSON Web Tokens) with Flask-JWT-Extended
- **Database**: MySQL with SQLAlchemy ORM
- **Validation**: Marshmallow for input validation and serialization
- **Image Processing**: Pillow (PIL) for avatar image resizing
- **File Storage**: Local file system with secure filename handling
- **Security**: Rate limiting with Flask-Limiter, CORS support

## Components and Interfaces

### 1. API Endpoints

#### GET /api/users/profile
**Purpose**: Retrieve current user's profile information
**Authentication**: Required (JWT token)
**Response Format**:
```json
{
  "success": true,
  "profile": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "profile_image": "uploads/avatars/user_1_1234567890.jpg",
    "role": "student",
    "is_active": true,
    "is_verified": true,
    "created_at": "2024-01-01T00:00:00",
    "total_enrollments": 5,
    "completed_courses": 2,
    "join_date": "January 2024"
  }
}
```

#### PUT /api/users/profile
**Purpose**: Update user profile information
**Authentication**: Required (JWT token)
**Request Format**:
```json
{
  "first_name": "John",
  "last_name": "Smith"
}
```
**Response Format**:
```json
{
  "success": true,
  "message": "Thông tin profile đã được cập nhật thành công",
  "profile": { /* updated profile data */ }
}
```

#### POST /api/users/upload-avatar
**Purpose**: Upload and update user avatar image
**Authentication**: Required (JWT token)
**Request Format**: Multipart form data with 'file' field
**Response Format**:
```json
{
  "success": true,
  "message": "Avatar đã được cập nhật thành công",
  "profile_image": "uploads/avatars/user_1_1234567890.jpg"
}
```

### 2. Data Models

#### User Model Extensions
The existing User model supports profile management with the following relevant fields:
```python
class User(db.Model):
    # Profile fields
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    profile_image = db.Column(db.String(500), nullable=True)
    
    # Computed properties
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    # Profile serialization
    def to_dict(self, include_sensitive=False):
        # Returns profile data for API responses
```

### 3. Validation Schemas

#### UserProfileUpdateSchema
```python
class UserProfileUpdateSchema(Schema):
    first_name = fields.Str(validate=lambda x: len(x.strip()) >= 2)
    last_name = fields.Str(validate=lambda x: len(x.strip()) >= 2)
```

### 4. File Processing Components

#### Image Upload Handler
- **File Type Validation**: Accepts JPG, PNG, GIF formats
- **Size Validation**: Maximum 2MB file size limit
- **Security**: Uses `secure_filename()` to prevent path traversal attacks
- **Storage**: Organized in `uploads/avatars/` directory with timestamped filenames

#### Image Processing Pipeline
```python
def resize_image(image_path, size=(200, 200)):
    # 1. Open and validate image
    # 2. Convert to RGB if necessary (handle transparency)
    # 3. Resize maintaining aspect ratio
    # 4. Center image in 200x200 canvas
    # 5. Save with optimized quality
```

## Data Models

### User Profile Data Structure
```sql
-- Relevant User table fields for profile management
users (
    id INT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    profile_image VARCHAR(500) NULL,
    role ENUM('student', 'instructor', 'admin'),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_activity_at DATETIME NULL
);
```

### File Storage Structure
```
uploads/
└── avatars/
    ├── user_1_1640995200.jpg
    ├── user_2_1640995300.jpg
    └── user_N_timestamp.jpg
```

## Error Handling

### Validation Errors
- **Input Validation**: Marshmallow schemas validate all input data
- **File Validation**: Custom validators for file type, size, and format
- **Business Rule Validation**: Enforce email immutability and name length requirements

### Error Response Format
```json
{
  "success": false,
  "error": "Error category",
  "message": "User-friendly error message",
  "details": { /* Additional error details */ }
}
```

### Common Error Scenarios
1. **Authentication Errors**: Invalid or expired JWT tokens
2. **Validation Errors**: Invalid input data or file formats
3. **File Processing Errors**: Image corruption or processing failures
4. **Database Errors**: Connection issues or constraint violations
5. **File System Errors**: Storage permission or disk space issues

### Error Recovery Mechanisms
- **Database Rollback**: Automatic rollback on transaction failures
- **File Cleanup**: Remove uploaded files if processing fails
- **Graceful Degradation**: Continue operation when non-critical features fail

## Testing Strategy

### Unit Testing
- **Model Tests**: User model methods and properties
- **Validation Tests**: Schema validation for all input scenarios
- **Image Processing Tests**: Avatar upload and resize functionality
- **Authentication Tests**: JWT token validation and user identification

### Integration Testing
- **API Endpoint Tests**: Full request-response cycle testing
- **Database Integration**: Test data persistence and retrieval
- **File System Integration**: Test file upload and storage operations
- **Authentication Flow**: Test JWT authentication in API calls

### Test Data Management
- **Mock Users**: Create test users with various profile states
- **Test Images**: Sample images for upload testing (valid and invalid)
- **Database Fixtures**: Consistent test data setup and teardown

### Security Testing
- **Authentication Bypass**: Attempt to access endpoints without valid tokens
- **File Upload Security**: Test malicious file uploads and path traversal
- **Input Validation**: Test SQL injection and XSS prevention
- **Rate Limiting**: Test API rate limiting effectiveness

### Performance Testing
- **Image Processing**: Test avatar resize performance with various image sizes
- **Database Queries**: Optimize profile data retrieval queries
- **File Storage**: Test file system performance under load
- **Memory Usage**: Monitor memory consumption during image processing

## Security Considerations

### Authentication and Authorization
- **JWT Token Validation**: All profile endpoints require valid JWT tokens
- **User Identity Verification**: Ensure users can only access their own profiles
- **Session Management**: Track user activity and enforce session timeouts

### Input Validation and Sanitization
- **SQL Injection Prevention**: Use parameterized queries through SQLAlchemy ORM
- **XSS Prevention**: Validate and sanitize all user input
- **File Upload Security**: Validate file types, sizes, and content
- **Path Traversal Prevention**: Use secure filename generation

### Data Protection
- **Sensitive Data Handling**: Exclude sensitive fields from API responses
- **Audit Logging**: Log all profile changes for security monitoring
- **Data Encryption**: Store sensitive data with appropriate encryption
- **Backup and Recovery**: Implement data backup strategies

### File Security
- **File Type Validation**: Strict validation of uploaded file types
- **Virus Scanning**: Consider implementing virus scanning for uploads
- **Storage Permissions**: Restrict file system permissions appropriately
- **Content Validation**: Validate image content, not just file extensions