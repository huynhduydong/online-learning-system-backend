# 📋 API Requirements - Q&A và Notification Features

## 🎯 Tổng quan

Tài liệu này mô tả chi tiết các API endpoints mà backend cần implement để hỗ trợ Q&A và Notification features trong hệ thống Online Learning System.

**Base URL**: `http://localhost:5000/api`

## 🔐 Authentication

Tất cả APIs đều yêu cầu JWT Authentication:
```
Authorization: Bearer <access_token>
```

## 📊 Standard Response Format

Tất cả APIs trả về response theo format chuẩn:
```json
{
  "success": true|false,
  "message": "Response message",
  "data": { /* actual response data */ }
}
```

---

# 🤔 Q&A APIs

## 1. Questions Management

### 1.1 Get Questions List
**GET** `/qa/questions`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 10 | Items per page (max: 50) |
| `q` | string | No | - | Search query |
| `status` | array | No | - | Filter by status: `new`, `in_progress`, `answered`, `closed` |
| `category` | array | No | - | Filter by category |
| `scope` | array | No | - | Filter by scope: `course`, `chapter`, `lesson`, `quiz`, `assignment` |
| `scope_id` | integer | No | - | Filter by specific scope ID |
| `tag_ids` | array | No | - | Filter by tag IDs |
| `author_id` | integer | No | - | Filter by author |
| `sort_by` | string | No | `newest` | Sort by: `newest`, `oldest`, `most_votes`, `most_answers`, `most_views`, `last_activity` |
| `sort_order` | string | No | `desc` | Sort order: `asc`, `desc` |
| `unanswered_only` | boolean | No | false | Show only unanswered questions |
| `pinned_only` | boolean | No | false | Show only pinned questions |
| `featured_only` | boolean | No | false | Show only featured questions |

**Response:**
```json
{
  "success": true,
  "message": "Questions retrieved successfully",
  "data": {
    "questions": [
      {
        "id": 1,
        "title": "How to implement authentication?",
        "content": "I need help with JWT authentication...",
        "category": "technical_question",
        "scope": "course",
        "scope_id": 123,
        "status": "new",
        "is_pinned": false,
        "is_featured": false,
        "vote_score": 5,
        "answer_count": 3,
        "view_count": 45,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T14:20:00Z",
        "last_activity_at": "2024-01-15T14:20:00Z",
        "author": {
          "id": 1,
          "full_name": "John Doe",
          "email": "john@example.com",
          "avatar_url": "https://example.com/avatar.jpg",
          "role": "student"
        },
        "tags": [
          {
            "id": 1,
            "name": "authentication",
            "color": "#3B82F6",
            "description": "Authentication related questions"
          }
        ],
        "attachments": [
          {
            "id": 1,
            "filename": "error_screenshot.png",
            "original_filename": "Screenshot 2024-01-15.png",
            "file_url": "https://example.com/files/error_screenshot.png",
            "file_size": 1024000,
            "file_type": "image/png",
            "uploaded_at": "2024-01-15T10:30:00Z"
          }
        ],
        "user_vote": "up",
        "user_permissions": {
          "can_edit": true,
          "can_delete": false,
          "can_pin": false,
          "can_feature": false,
          "can_change_status": false
        }
      }
    ],
    "pagination": {
      "current_page": 1,
      "per_page": 10,
      "total": 150,
      "total_pages": 15,
      "has_next": true,
      "has_prev": false,
      "next_page": 2,
      "prev_page": null
    },
    "filters_applied": {
      "status": ["new", "in_progress"],
      "category": ["technical_question"]
    },
    "stats": {
      "total_questions": 150,
      "answered_questions": 120,
      "unanswered_questions": 30
    }
  }
}
```

### 1.2 Get Question Detail
**GET** `/qa/questions/{questionId}`

**Response:**
```json
{
  "success": true,
  "message": "Question retrieved successfully",
  "data": {
    "id": 1,
    "title": "How to implement authentication?",
    "content": "I need help with JWT authentication...",
    "category": "technical_question",
    "scope": "course",
    "scope_id": 123,
    "status": "answered",
    "is_pinned": false,
    "is_featured": false,
    "vote_score": 5,
    "answer_count": 3,
    "view_count": 46,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T14:20:00Z",
    "last_activity_at": "2024-01-15T16:45:00Z",
    "author": {
      "id": 1,
      "full_name": "John Doe",
      "email": "john@example.com",
      "avatar_url": "https://example.com/avatar.jpg",
      "role": "student"
    },
    "tags": [
      {
        "id": 1,
        "name": "authentication",
        "color": "#3B82F6"
      }
    ],
    "attachments": [],
    "answers": [
      {
        "id": 1,
        "content": "You can use JWT tokens for authentication...",
        "is_accepted": true,
        "is_pinned": false,
        "vote_score": 8,
        "created_at": "2024-01-15T12:00:00Z",
        "updated_at": "2024-01-15T12:00:00Z",
        "author": {
          "id": 2,
          "full_name": "Jane Smith",
          "email": "jane@example.com",
          "avatar_url": "https://example.com/avatar2.jpg",
          "role": "instructor"
        },
        "attachments": [],
        "user_vote": null,
        "user_permissions": {
          "can_edit": false,
          "can_delete": false,
          "can_accept": true,
          "can_pin": false
        },
        "comment_count": 2
      }
    ],
    "comments": [
      {
        "id": 1,
        "content": "Great question! I had the same issue.",
        "commentable_type": "question",
        "commentable_id": 1,
        "parent_id": null,
        "created_at": "2024-01-15T11:00:00Z",
        "author": {
          "id": 3,
          "full_name": "Bob Wilson",
          "email": "bob@example.com",
          "avatar_url": null,
          "role": "student"
        },
        "replies": [],
        "user_permissions": {
          "can_edit": false,
          "can_delete": false
        }
      }
    ],
    "related_questions": [
      {
        "id": 2,
        "title": "JWT token expiration handling",
        "vote_score": 3,
        "answer_count": 1,
        "created_at": "2024-01-14T09:00:00Z"
      }
    ],
    "user_vote": "up",
    "user_permissions": {
      "can_edit": true,
      "can_delete": false,
      "can_pin": false,
      "can_feature": false,
      "can_change_status": false
    }
  }
}
```

### 1.3 Create Question
**POST** `/qa/questions`

**Request Body:**
```json
{
  "title": "How to implement authentication?",
  "content": "I need help with JWT authentication implementation...",
  "category": "technical_question",
  "scope": "course",
  "scope_id": 123,
  "tag_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Question created successfully",
  "data": {
    "id": 1,
    "title": "How to implement authentication?",
    "content": "I need help with JWT authentication implementation...",
    "category": "technical_question",
    "scope": "course",
    "scope_id": 123,
    "status": "new",
    "is_pinned": false,
    "is_featured": false,
    "vote_score": 0,
    "answer_count": 0,
    "view_count": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "last_activity_at": "2024-01-15T10:30:00Z",
    "author": {
      "id": 1,
      "full_name": "John Doe",
      "email": "john@example.com",
      "avatar_url": "https://example.com/avatar.jpg",
      "role": "student"
    },
    "tags": [
      {
        "id": 1,
        "name": "authentication",
        "color": "#3B82F6"
      }
    ],
    "attachments": [],
    "user_vote": null,
    "user_permissions": {
      "can_edit": true,
      "can_delete": true,
      "can_pin": false,
      "can_feature": false,
      "can_change_status": false
    }
  }
}
```

### 1.4 Update Question
**PUT** `/qa/questions/{questionId}`

**Request Body:**
```json
{
  "title": "Updated: How to implement authentication?",
  "content": "Updated content...",
  "category": "technical_question",
  "status": "in_progress",
  "tag_ids": [1, 2],
  "is_pinned": false,
  "is_featured": false
}
```

### 1.5 Delete Question
**DELETE** `/qa/questions/{questionId}`

**Response:**
```json
{
  "success": true,
  "message": "Question deleted successfully",
  "data": null
}
```

### 1.6 Vote on Question
**POST** `/qa/questions/{questionId}/vote`

**Request Body:**
```json
{
  "vote_type": "up"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Vote recorded successfully",
  "data": {
    "vote_score": 6,
    "user_vote": "up"
  }
}
```

### 1.7 Get Question Suggestions
**GET** `/qa/questions/suggestions`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | Question title to find similar questions |
| `scope_type` | string | No | Scope type filter |
| `scope_id` | integer | No | Scope ID filter |

**Response:**
```json
{
  "success": true,
  "message": "Suggestions retrieved successfully",
  "data": [
    {
      "id": 2,
      "title": "JWT authentication best practices",
      "vote_score": 10,
      "answer_count": 5,
      "status": "answered",
      "created_at": "2024-01-10T09:00:00Z"
    }
  ]
}
```

## 2. Answers Management

### 2.1 Get Answers for Question
**GET** `/qa/questions/{questionId}/answers`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 10 | Items per page |

**Response:**
```json
{
  "success": true,
  "message": "Answers retrieved successfully",
  "data": {
    "answers": [
      {
        "id": 1,
        "content": "You can use JWT tokens for authentication...",
        "is_accepted": true,
        "is_pinned": false,
        "vote_score": 8,
        "created_at": "2024-01-15T12:00:00Z",
        "updated_at": "2024-01-15T12:00:00Z",
        "author": {
          "id": 2,
          "full_name": "Jane Smith",
          "email": "jane@example.com",
          "avatar_url": "https://example.com/avatar2.jpg",
          "role": "instructor"
        },
        "attachments": [],
        "user_vote": null,
        "user_permissions": {
          "can_edit": false,
          "can_delete": false,
          "can_accept": true,
          "can_pin": false
        },
        "comment_count": 2
      }
    ],
    "pagination": {
      "current_page": 1,
      "per_page": 10,
      "total": 3,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false,
      "next_page": null,
      "prev_page": null
    }
  }
}
```

### 2.2 Create Answer
**POST** `/qa/answers`

**Request Body:**
```json
{
  "question_id": 1,
  "content": "You can implement JWT authentication by..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Answer created successfully",
  "data": {
    "id": 1,
    "content": "You can implement JWT authentication by...",
    "question_id": 1,
    "is_accepted": false,
    "is_pinned": false,
    "vote_score": 0,
    "created_at": "2024-01-15T12:00:00Z",
    "updated_at": "2024-01-15T12:00:00Z",
    "author": {
      "id": 2,
      "full_name": "Jane Smith",
      "email": "jane@example.com",
      "avatar_url": "https://example.com/avatar2.jpg",
      "role": "instructor"
    },
    "attachments": [],
    "user_vote": null,
    "user_permissions": {
      "can_edit": true,
      "can_delete": true,
      "can_accept": false,
      "can_pin": false
    },
    "comment_count": 0
  }
}
```

### 2.3 Update Answer
**PUT** `/qa/answers/{answerId}`

**Request Body:**
```json
{
  "content": "Updated answer content...",
  "is_pinned": false
}
```

### 2.4 Delete Answer
**DELETE** `/qa/answers/{answerId}`

### 2.5 Accept Answer
**POST** `/qa/answers/{answerId}/accept`

**Response:**
```json
{
  "success": true,
  "message": "Answer accepted successfully",
  "data": {
    "id": 1,
    "is_accepted": true,
    "updated_at": "2024-01-15T15:00:00Z"
  }
}
```

### 2.6 Vote on Answer
**POST** `/qa/answers/{answerId}/vote`

**Request Body:**
```json
{
  "vote_type": "up"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Vote recorded successfully",
  "data": {
    "vote_score": 9,
    "user_vote": "up"
  }
}
```

## 3. Comments Management

### 3.1 Get Comments
**GET** `/qa/questions/{questionId}/comments`
**GET** `/qa/answers/{answerId}/comments`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 10 | Items per page |

**Response:**
```json
{
  "success": true,
  "message": "Comments retrieved successfully",
  "data": {
    "comments": [
      {
        "id": 1,
        "content": "Great question! I had the same issue.",
        "commentable_type": "question",
        "commentable_id": 1,
        "parent_id": null,
        "created_at": "2024-01-15T11:00:00Z",
        "updated_at": "2024-01-15T11:00:00Z",
        "author": {
          "id": 3,
          "full_name": "Bob Wilson",
          "email": "bob@example.com",
          "avatar_url": null,
          "role": "student"
        },
        "replies": [
          {
            "id": 2,
            "content": "Yes, it's a common issue for beginners.",
            "commentable_type": "question",
            "commentable_id": 1,
            "parent_id": 1,
            "created_at": "2024-01-15T11:30:00Z",
            "author": {
              "id": 4,
              "full_name": "Alice Brown",
              "email": "alice@example.com",
              "avatar_url": null,
              "role": "ta"
            },
            "replies": [],
            "user_permissions": {
              "can_edit": false,
              "can_delete": false
            }
          }
        ],
        "user_permissions": {
          "can_edit": false,
          "can_delete": false
        }
      }
    ],
    "pagination": {
      "current_page": 1,
      "per_page": 10,
      "total": 5,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false,
      "next_page": null,
      "prev_page": null
    }
  }
}
```

### 3.2 Create Comment
**POST** `/qa/comments`

**Request Body:**
```json
{
  "content": "This is a helpful comment.",
  "commentable_type": "question",
  "commentable_id": 1,
  "parent_id": null,
  "mentioned_user_ids": [2, 3]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Comment created successfully",
  "data": {
    "id": 1,
    "content": "This is a helpful comment.",
    "commentable_type": "question",
    "commentable_id": 1,
    "parent_id": null,
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z",
    "author": {
      "id": 3,
      "full_name": "Bob Wilson",
      "email": "bob@example.com",
      "avatar_url": null,
      "role": "student"
    },
    "replies": [],
    "user_permissions": {
      "can_edit": true,
      "can_delete": true
    }
  }
}
```

### 3.3 Update Comment
**PUT** `/qa/comments/{commentId}`

**Request Body:**
```json
{
  "content": "Updated comment content..."
}
```

### 3.4 Delete Comment
**DELETE** `/qa/comments/{commentId}`

## 4. Tags Management

### 4.1 Get Tags
**GET** `/qa/tags`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | No | - | Search query |
| `popular` | boolean | No | false | Get popular tags only |
| `limit` | integer | No | 50 | Limit results |

**Response:**
```json
{
  "success": true,
  "message": "Tags retrieved successfully",
  "data": {
    "tags": [
      {
        "id": 1,
        "name": "authentication",
        "color": "#3B82F6",
        "description": "Authentication related questions",
        "usage_count": 25
      },
      {
        "id": 2,
        "name": "javascript",
        "color": "#F59E0B",
        "description": "JavaScript programming questions",
        "usage_count": 45
      }
    ],
    "pagination": {
      "current_page": 1,
      "per_page": 50,
      "total": 2,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false,
      "next_page": null,
      "prev_page": null
    }
  }
}
```

### 4.2 Create Tag
**POST** `/qa/tags`

**Request Body:**
```json
{
  "name": "react",
  "color": "#06B6D4",
  "description": "React framework questions"
}
```

## 5. Statistics

### 5.1 Get Q&A Statistics
**GET** `/qa/stats`

**Response:**
```json
{
  "success": true,
  "message": "Statistics retrieved successfully",
  "data": {
    "total_questions": 150,
    "answered_questions": 120,
    "unanswered_questions": 30,
    "questions_by_status": {
      "new": 30,
      "in_progress": 20,
      "answered": 90,
      "closed": 10
    },
    "questions_by_category": {
      "technical_question": 80,
      "course_content": 40,
      "assignment_help": 20,
      "general_discussion": 10
    },
    "top_tags": [
      {
        "tag": {
          "id": 1,
          "name": "javascript",
          "color": "#F59E0B"
        },
        "question_count": 45
      }
    ],
    "most_active_users": [
      {
        "user": {
          "id": 1,
          "full_name": "John Doe",
          "email": "john@example.com",
          "avatar_url": "https://example.com/avatar.jpg",
          "role": "student"
        },
        "question_count": 15,
        "answer_count": 25
      }
    ]
  }
}
```

---

# 🔔 Notification APIs

## 1. Get Notifications
**GET** `/notifications`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `read` | boolean | No | - | Filter by read status |
| `type` | string | No | - | Filter by notification type (comma-separated) |
| `startDate` | string | No | - | Filter from date (ISO format) |
| `endDate` | string | No | - | Filter to date (ISO format) |
| `limit` | integer | No | 20 | Items per page |
| `offset` | integer | No | 0 | Offset for pagination |

**Response:**
```json
{
  "success": true,
  "message": "Notifications retrieved successfully",
  "data": {
    "data": [
      {
        "id": "notif_123",
        "userId": "user_456",
        "type": "question_answered",
        "title": "Câu hỏi của bạn có câu trả lời mới",
        "message": "Jane Smith đã trả lời câu hỏi \"How to implement authentication?\"",
        "data": {
          "questionId": "1",
          "answerId": "1",
          "userId": "2",
          "url": "/qa/1",
          "metadata": {
            "questionTitle": "How to implement authentication?",
            "answererName": "Jane Smith"
          }
        },
        "read": false,
        "createdAt": "2024-01-15T12:00:00Z",
        "updatedAt": "2024-01-15T12:00:00Z",
        "expiresAt": null
      }
    ],
    "pagination": {
      "total": 25,
      "page": 1,
      "limit": 20,
      "totalPages": 2
    }
  }
}
```

## 2. Get Unread Count
**GET** `/notifications/unread-count`

**Response:**
```json
{
  "success": true,
  "message": "Unread count retrieved successfully",
  "data": {
    "count": 5
  }
}
```

## 3. Get Notification Statistics
**GET** `/notifications/stats`

**Response:**
```json
{
  "success": true,
  "message": "Notification statistics retrieved successfully",
  "data": {
    "total": 100,
    "unread": 15,
    "byType": {
      "question_answered": 25,
      "answer_accepted": 10,
      "answer_voted": 15,
      "question_voted": 8,
      "comment_added": 20,
      "question_pinned": 2,
      "question_closed": 3,
      "course_announcement": 12,
      "assignment_due": 5
    }
  }
}
```

## 4. Mark Notification as Read
**PATCH** `/notifications/{notificationId}/read`

**Response:**
```json
{
  "success": true,
  "message": "Notification marked as read successfully",
  "data": null
}
```

## 5. Mark Multiple Notifications as Read
**PATCH** `/notifications/mark-read`

**Request Body:**
```json
{
  "notificationIds": ["notif_123", "notif_124", "notif_125"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notifications marked as read successfully",
  "data": null
}
```

## 6. Mark All Notifications as Read
**PATCH** `/notifications/mark-all-read`

**Response:**
```json
{
  "success": true,
  "message": "All notifications marked as read successfully",
  "data": null
}
```

## 7. Delete Notification
**DELETE** `/notifications/{notificationId}`

**Response:**
```json
{
  "success": true,
  "message": "Notification deleted successfully",
  "data": null
}
```

## 8. Delete Multiple Notifications
**DELETE** `/notifications/batch`

**Request Body:**
```json
{
  "notificationIds": ["notif_123", "notif_124", "notif_125"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notifications deleted successfully",
  "data": null
}
```

## 9. Get Notification Preferences
**GET** `/notifications/preferences`

**Response:**
```json
{
  "success": true,
  "message": "Notification preferences retrieved successfully",
  "data": {
    "userId": "user_456",
    "emailNotifications": true,
    "pushNotifications": true,
    "inAppNotifications": true,
    "preferences": {
      "question_answered": {
        "email": true,
        "push": true,
        "inApp": true
      },
      "answer_accepted": {
        "email": true,
        "push": true,
        "inApp": true
      },
      "answer_voted": {
        "email": false,
        "push": true,
        "inApp": true
      },
      "question_voted": {
        "email": false,
        "push": true,
        "inApp": true
      },
      "comment_added": {
        "email": true,
        "push": true,
        "inApp": true
      },
      "question_pinned": {
        "email": true,
        "push": true,
        "inApp": true
      },
      "question_closed": {
        "email": true,
        "push": false,
        "inApp": true
      },
      "course_announcement": {
        "email": true,
        "push": true,
        "inApp": true
      },
      "assignment_due": {
        "email": true,
        "push": true,
        "inApp": true
      },
      "grade_released": {
        "email": true,
        "push": true,
        "inApp": true
      },
      "system_maintenance": {
        "email": true,
        "push": false,
        "inApp": true
      },
      "account_security": {
        "email": true,
        "push": true,
        "inApp": true
      },
      "mention": {
        "email": true,
        "push": true,
        "inApp": true
      },
      "follow": {
        "email": false,
        "push": true,
        "inApp": true
      }
    }
  }
}
```

## 10. Update Notification Preferences
**PATCH** `/notifications/preferences`

**Request Body:**
```json
{
  "emailNotifications": true,
  "pushNotifications": false,
  "preferences": {
    "question_answered": {
      "email": true,
      "push": false,
      "inApp": true
    },
    "answer_voted": {
      "email": false,
      "push": false,
      "inApp": true
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notification preferences updated successfully",
  "data": {
    "userId": "user_456",
    "emailNotifications": true,
    "pushNotifications": false,
    "inAppNotifications": true,
    "preferences": {
      "question_answered": {
        "email": true,
        "push": false,
        "inApp": true
      }
    }
  }
}
```

## 11. Create Notification (Admin/System)
**POST** `/notifications`

**Request Body:**
```json
{
  "userId": "user_456",
  "type": "course_announcement",
  "title": "Thông báo khóa học",
  "message": "Thông báo mới từ khóa học \"React Fundamentals\": Bài tập mới đã được thêm",
  "data": {
    "courseId": "123",
    "url": "/courses/123/assignments",
    "metadata": {
      "courseName": "React Fundamentals",
      "announcement": "Bài tập mới đã được thêm"
    }
  },
  "expiresAt": "2024-02-15T00:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notification created successfully",
  "data": {
    "id": "notif_789",
    "userId": "user_456",
    "type": "course_announcement",
    "title": "Thông báo khóa học",
    "message": "Thông báo mới từ khóa học \"React Fundamentals\": Bài tập mới đã được thêm",
    "data": {
      "courseId": "123",
      "url": "/courses/123/assignments",
      "metadata": {
        "courseName": "React Fundamentals",
        "announcement": "Bài tập mới đã được thêm"
      }
    },
    "read": false,
    "createdAt": "2024-01-15T14:00:00Z",
    "updatedAt": "2024-01-15T14:00:00Z",
    "expiresAt": "2024-02-15T00:00:00Z"
  }
}
```

## 12. Subscribe to Push Notifications
**POST** `/notifications/push/subscribe`

**Request Body:**
```json
{
  "subscription": {
    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
    "keys": {
      "p256dh": "...",
      "auth": "..."
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully subscribed to push notifications",
  "data": null
}
```

## 13. Unsubscribe from Push Notifications
**DELETE** `/notifications/push/unsubscribe`

**Response:**
```json
{
  "success": true,
  "message": "Successfully unsubscribed from push notifications",
  "data": null
}
```

## 14. Send Test Notification (Development/Admin)
**POST** `/notifications/test`

**Request Body:**
```json
{
  "type": "question_answered",
  "data": {
    "questionId": "1",
    "answerId": "1",
    "questionTitle": "Test Question",
    "answererName": "Test User"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Test notification sent successfully",
  "data": null
}
```

---

# 📋 Data Types & Enums

## Q&A Enums

### QuestionStatus
- `new` - Câu hỏi mới
- `in_progress` - Đang xử lý
- `answered` - Đã trả lời
- `closed` - Đã đóng

### QuestionCategory
- `technical_question` - Câu hỏi kỹ thuật
- `course_content` - Nội dung khóa học
- `assignment_help` - Hỗ trợ bài tập
- `general_discussion` - Thảo luận chung
- `lesson_content` - Nội dung bài học
- `technical_issue` - Vấn đề kỹ thuật
- `administrative` - Thủ tục hành chính
- `support_request` - Yêu cầu hỗ trợ
- `bug_report` - Báo cáo lỗi hệ thống

### QuestionScope
- `course` - Khóa học
- `chapter` - Chương
- `lesson` - Bài học
- `quiz` - Bài kiểm tra
- `assignment` - Bài tập

### QAUserRole
- `student` - Học viên
- `instructor` - Giảng viên
- `ta` - Trợ giảng
- `admin` - Quản trị viên
- `guest` - Khách

## Notification Types

### NotificationType
- `question_answered` - Câu hỏi được trả lời
- `answer_accepted` - Câu trả lời được chấp nhận
- `answer_voted` - Câu trả lời được vote
- `question_voted` - Câu hỏi được vote
- `comment_added` - Bình luận mới
- `question_pinned` - Câu hỏi được ghim
- `question_closed` - Câu hỏi được đóng
- `course_announcement` - Thông báo khóa học
- `assignment_due` - Bài tập sắp hết hạn
- `grade_released` - Điểm số được công bố
- `system_maintenance` - Bảo trì hệ thống
- `account_security` - Bảo mật tài khoản
- `mention` - Được nhắc đến
- `follow` - Người theo dõi mới

---

# 🔧 Implementation Notes

## Error Handling
Tất cả APIs phải handle các error cases sau:
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server errors

## Validation Rules
- **Question title**: 10-200 characters
- **Question content**: 20-10000 characters
- **Answer content**: 10-5000 characters
- **Comment content**: 1-1000 characters
- **Tag name**: 2-50 characters, alphanumeric and hyphens only

## Permissions
Implement role-based permissions cho:
- **Students**: Có thể tạo questions, answers, comments, vote
- **TAs**: Có thể pin answers, moderate comments
- **Instructors**: Có thể pin/feature questions, change status, moderate content
- **Admins**: Full access to all features

## Real-time Features
Cân nhắc implement WebSocket/Server-Sent Events cho:
- Real-time notifications
- Live Q&A updates
- Comment threads updates

## Performance Considerations
- Implement caching cho popular questions và tags
- Use pagination cho tất cả list endpoints
- Optimize database queries với proper indexing
- Consider implementing search với Elasticsearch

## Security
- Sanitize tất cả user input
- Implement rate limiting
- Validate file uploads (nếu có)
- Use HTTPS cho tất cả endpoints
- Implement CSRF protection

---

**Lưu ý**: Tài liệu này dựa trên phân tích frontend code hiện tại. Backend team cần review và adjust theo architecture và business requirements cụ thể.