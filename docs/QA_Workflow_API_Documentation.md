# Q&A Workflow API Documentation

## Overview
This document provides comprehensive API documentation for the Question & Answer workflow in the Online Learning System. The workflow supports complete interaction between students, teachers, and the system with proper authentication, notifications, and data persistence.

## Table of Contents
1. [Authentication](#authentication)
2. [Student Workflow APIs](#student-workflow-apis)
3. [Teacher Workflow APIs](#teacher-workflow-apis)
4. [System APIs](#system-apis)
5. [Notification APIs](#notification-apis)
6. [Vote & Engagement APIs](#vote--engagement-apis)
7. [Complete Workflow Examples](#complete-workflow-examples)

---

## Authentication

All Q&A endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### Authentication Endpoints

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "email": "student@example.com",
      "role": "student"
    }
  }
}
```

---

## Student Workflow APIs

### 1. Question Management

#### Create Question
```http
POST /api/questions
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "title": "How to implement JWT authentication?",
  "content": "I'm having trouble understanding how to properly implement JWT authentication in my Flask application. Can someone provide guidance?",
  "category": "technical_question",
  "scope": "course",
  "scope_id": 1,
  "tags": ["authentication", "jwt", "flask"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Question created successfully",
  "data": {
    "id": 123,
    "title": "How to implement JWT authentication?",
    "content": "I'm having trouble understanding...",
    "category": "technical_question",
    "scope": "course",
    "scope_id": 1,
    "status": "open",
    "author": {
      "id": 1,
      "name": "John Student",
      "email": "student@example.com"
    },
    "tags": [
      {"id": 1, "name": "authentication"},
      {"id": 2, "name": "jwt"},
      {"id": 3, "name": "flask"}
    ],
    "vote_score": 0,
    "answer_count": 0,
    "view_count": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Get Questions (with pagination and filters)
```http
GET /api/questions?page=1&per_page=20&category=technical_question&scope=course&scope_id=1&sort_by=newest
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Questions retrieved successfully",
  "data": [
    {
      "id": 123,
      "title": "How to implement JWT authentication?",
      "content": "I'm having trouble understanding...",
      "category": "technical_question",
      "status": "open",
      "author": {
        "id": 1,
        "name": "John Student"
      },
      "tags": ["authentication", "jwt", "flask"],
      "vote_score": 5,
      "answer_count": 3,
      "view_count": 45,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "limit": 20,
    "totalPages": 8
  }
}
```

#### Get Question Details
```http
GET /api/questions/123
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Question retrieved successfully",
  "data": {
    "id": 123,
    "title": "How to implement JWT authentication?",
    "content": "I'm having trouble understanding how to properly implement JWT authentication...",
    "category": "technical_question",
    "scope": "course",
    "scope_id": 1,
    "status": "answered",
    "author": {
      "id": 1,
      "name": "John Student",
      "email": "student@example.com",
      "avatar": "/uploads/avatars/user_1.jpg"
    },
    "tags": [
      {"id": 1, "name": "authentication"},
      {"id": 2, "name": "jwt"},
      {"id": 3, "name": "flask"}
    ],
    "vote_score": 5,
    "answer_count": 3,
    "view_count": 45,
    "is_pinned": false,
    "is_featured": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "answers": [
      {
        "id": 456,
        "content": "Here's how you can implement JWT authentication...",
        "author": {
          "id": 2,
          "name": "Dr. Smith",
          "role": "instructor"
        },
        "is_accepted": true,
        "vote_score": 8,
        "created_at": "2024-01-15T11:00:00Z"
      }
    ]
  }
}
```

#### Update Question
```http
PUT /api/questions/123
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "title": "Updated: How to implement JWT authentication?",
  "content": "Updated content with more specific details...",
  "tags": ["authentication", "jwt", "flask", "security"]
}
```

#### Delete Question
```http
DELETE /api/questions/123
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Question deleted successfully",
  "data": null
}
```

#### Vote on Question
```http
POST /api/questions/123/vote
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "vote_type": "upvote"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Vote recorded successfully",
  "data": {
    "vote_score": 6,
    "user_vote": "upvote"
  }
}
```

### 2. Search and Discovery

#### Search Questions
```http
GET /api/questions/search?q=authentication&category=technical_question&page=1&per_page=10
Authorization: Bearer <jwt_token>
```

#### Get Trending Questions
```http
GET /api/questions/trending?days=7&limit=10
Authorization: Bearer <jwt_token>
```

#### Get Related Questions
```http
GET /api/questions/123/related?limit=5
Authorization: Bearer <jwt_token>
```

---

## Teacher Workflow APIs

### 1. Answer Management

#### Get Answers for Question
```http
GET /api/answers/question/123?page=1&per_page=10&sort_by=votes
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Answers retrieved successfully",
  "data": [
    {
      "id": 456,
      "content": "Here's a comprehensive guide to implementing JWT authentication...",
      "question_id": 123,
      "author": {
        "id": 2,
        "name": "Dr. Smith",
        "role": "instructor",
        "avatar": "/uploads/avatars/user_2.jpg"
      },
      "is_accepted": true,
      "is_pinned": false,
      "vote_score": 8,
      "comment_count": 2,
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:05:00Z"
    }
  ],
  "pagination": {
    "total": 3,
    "page": 1,
    "limit": 10,
    "totalPages": 1
  }
}
```

#### Create Answer
```http
POST /api/answers/question/123
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "content": "Here's a comprehensive guide to implementing JWT authentication in Flask:\n\n1. Install required packages:\n```bash\npip install PyJWT flask-jwt-extended\n```\n\n2. Configure your Flask app:\n```python\nfrom flask_jwt_extended import JWTManager\n\napp.config['JWT_SECRET_KEY'] = 'your-secret-key'\njwt = JWTManager(app)\n```\n\n3. Create login endpoint:\n```python\n@app.route('/login', methods=['POST'])\ndef login():\n    # Validate credentials\n    access_token = create_access_token(identity=user.id)\n    return {'access_token': access_token}\n```\n\nThis approach ensures secure authentication with proper token management."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Answer created successfully",
  "data": {
    "id": 789,
    "content": "Here's a comprehensive guide to implementing JWT authentication...",
    "question_id": 123,
    "author": {
      "id": 2,
      "name": "Dr. Smith",
      "role": "instructor"
    },
    "is_accepted": false,
    "is_pinned": false,
    "vote_score": 0,
    "comment_count": 0,
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
}
```

#### Update Answer
```http
PUT /api/answers/789
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "content": "Updated answer with additional examples and best practices..."
}
```

#### Accept Answer (Question Author Only)
```http
POST /api/answers/789/accept
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Answer accepted successfully",
  "data": {
    "id": 789,
    "is_accepted": true,
    "question": {
      "id": 123,
      "status": "answered"
    }
  }
}
```

#### Unaccept Answer
```http
POST /api/answers/789/unaccept
Authorization: Bearer <jwt_token>
```

#### Vote on Answer
```http
POST /api/answers/789/vote
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "vote_type": "upvote"
}
```

#### Delete Answer
```http
DELETE /api/answers/789
Authorization: Bearer <jwt_token>
```

---

## System APIs

### 1. Statistics and Analytics

#### Get Question Statistics
```http
GET /api/questions/123/statistics
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "question_id": 123,
    "view_count": 45,
    "vote_score": 5,
    "upvotes": 7,
    "downvotes": 2,
    "answer_count": 3,
    "comment_count": 5,
    "created_at": "2024-01-15T10:30:00Z",
    "last_activity_at": "2024-01-15T14:30:00Z"
  }
}
```

#### Get Answer Statistics
```http
GET /api/answers/789/statistics
Authorization: Bearer <jwt_token>
```

### 2. User Activity

#### Get User Questions
```http
GET /api/questions/user/1?page=1&per_page=10&status=open
Authorization: Bearer <jwt_token>
```

#### Get User Answers
```http
GET /api/answers/user/2?page=1&per_page=10
Authorization: Bearer <jwt_token>
```

---

## Notification APIs

### 1. Get Notifications
```http
GET /api/notifications?page=1&per_page=20&read=false&type=qa
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Notifications retrieved successfully",
  "data": [
    {
      "id": 1,
      "type": "question_answered",
      "title": "New Answer to Your Question",
      "message": "Dr. Smith answered your question 'How to implement JWT authentication?'",
      "data": {
        "question_id": 123,
        "answer_id": 789,
        "author_name": "Dr. Smith"
      },
      "read": false,
      "created_at": "2024-01-15T14:30:00Z"
    },
    {
      "id": 2,
      "type": "answer_accepted",
      "title": "Your Answer Was Accepted",
      "message": "Your answer to 'How to implement JWT authentication?' was accepted",
      "data": {
        "question_id": 123,
        "answer_id": 789
      },
      "read": false,
      "created_at": "2024-01-15T15:00:00Z"
    }
  ],
  "pagination": {
    "total": 25,
    "page": 1,
    "limit": 20,
    "totalPages": 2
  }
}
```

### 2. Mark Notification as Read
```http
PUT /api/notifications/1/read
Authorization: Bearer <jwt_token>
```

### 3. Get Unread Count
```http
GET /api/notifications/unread-count
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "unread_count": 5,
    "by_type": {
      "question_answered": 2,
      "answer_accepted": 1,
      "answer_voted": 2
    }
  }
}
```

---

## Vote & Engagement APIs

### 1. Vote Management
```http
GET /api/votes/user/1?item_type=question&page=1&per_page=20
Authorization: Bearer <jwt_token>
```

### 2. Vote Statistics
```http
GET /api/votes/statistics?item_type=question&item_id=123
Authorization: Bearer <jwt_token>
```

### 3. Vote Trends
```http
GET /api/votes/trends?time_range=week&item_type=question
Authorization: Bearer <jwt_token>
```

---

## Complete Workflow Examples

### Scenario 1: Student Asks Question, Teacher Responds

#### Step 1: Student Creates Question
```http
POST /api/questions
Authorization: Bearer <student_jwt_token>

{
  "title": "How to handle database migrations in Flask?",
  "content": "I'm working on a Flask project and need to understand the best practices for handling database migrations...",
  "category": "technical_question",
  "scope": "course",
  "scope_id": 1,
  "tags": ["flask", "database", "migrations"]
}
```

#### Step 2: System Sends Notification to Teachers
*Automatic system process - teachers receive notifications*

#### Step 3: Teacher Views Question
```http
GET /api/questions/124
Authorization: Bearer <teacher_jwt_token>
```

#### Step 4: Teacher Creates Answer
```http
POST /api/answers/question/124
Authorization: Bearer <teacher_jwt_token>

{
  "content": "Great question! Here's a comprehensive guide to handling database migrations in Flask using Flask-Migrate..."
}
```

#### Step 5: System Notifies Student
*Automatic system process - student receives notification*

#### Step 6: Student Views Answer and Accepts It
```http
GET /api/answers/question/124
Authorization: Bearer <student_jwt_token>

POST /api/answers/790/accept
Authorization: Bearer <student_jwt_token>
```

#### Step 7: System Notifies Teacher of Acceptance
*Automatic system process - teacher receives acceptance notification*

### Scenario 2: Community Engagement with Voting

#### Step 1: Other Students View Question
```http
GET /api/questions/124
Authorization: Bearer <other_student_jwt_token>
```

#### Step 2: Students Vote on Question and Answers
```http
POST /api/questions/124/vote
Authorization: Bearer <other_student_jwt_token>
{
  "vote_type": "upvote"
}

POST /api/answers/790/vote
Authorization: Bearer <other_student_jwt_token>
{
  "vote_type": "upvote"
}
```

#### Step 3: View Updated Statistics
```http
GET /api/questions/124/statistics
Authorization: Bearer <any_jwt_token>
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "message": "Error description",
  "data": null
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

### Validation Error Response
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "title": ["Title is required"],
    "content": ["Content must be at least 20 characters"]
  }
}
```

---

## Rate Limiting

- **Questions**: 10 per hour per user
- **Answers**: 20 per hour per user
- **Votes**: 100 per hour per user
- **Search**: 60 requests per minute per user

---

## Webhook Events (Future Enhancement)

The system can be extended to support webhooks for external integrations:

- `question.created`
- `question.answered`
- `answer.accepted`
- `vote.cast`

---

## API Versioning

Current API version: `v1`
Base URL: `/api/v1/`

Future versions will maintain backward compatibility for at least 6 months.

---

## Security Considerations

1. **Authentication**: All endpoints require valid JWT tokens
2. **Authorization**: Users can only modify their own content (except instructors/admins)
3. **Rate Limiting**: Prevents abuse and spam
4. **Input Validation**: All inputs are validated and sanitized
5. **SQL Injection Protection**: Using SQLAlchemy ORM with parameterized queries
6. **XSS Protection**: Content is properly escaped when rendered

---

## Support

For API support and questions:
- Documentation: `/docs/api`
- Support Email: api-support@onlinelearning.com
- GitHub Issues: [Repository Issues](https://github.com/your-org/online-learning-system/issues)

---

*Last Updated: January 2025*
*API Version: 1.0*