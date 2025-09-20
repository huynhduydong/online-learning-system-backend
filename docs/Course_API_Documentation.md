# Course API Documentation

## Overview
This document provides comprehensive documentation for all Course-related API endpoints in the Online Learning System.

**Base URL**: `/api/courses`

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Response Format
All endpoints return responses in the following format:
```json
{
  "success": true|false,
  "message": "Response message",
  "data": {...}
}
```

---

## Endpoints

### 1. Get Course Catalog
**GET** `/catalog`

Retrieve paginated course catalog with filtering and sorting options.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number for pagination |
| `per_page` | integer | No | 12 | Items per page (max: 50) |
| `category` | string | No | - | Filter by category name |
| `difficulty` | string | No | - | Filter by difficulty level (beginner, intermediate, advanced) |
| `min_price` | float | No | - | Minimum price filter |
| `max_price` | float | No | - | Maximum price filter |
| `rating` | float | No | - | Minimum rating filter |
| `sort_by` | string | No | popularity | Sort field (popularity, price, rating, newest) |
| `sort_order` | string | No | desc | Sort order (asc, desc) |

#### Example Request
```bash
GET /api/courses/catalog?page=1&per_page=12&category=programming&difficulty=beginner&sort_by=rating&sort_order=desc
```

#### Example Response
```json
{
  "success": true,
  "message": "Course catalog retrieved successfully",
  "data": {
    "data": {
      "courses": [
        {
          "id": 1,
          "title": "Python cho người mới bắt đầu",
          "slug": "python-cho-nguoi-moi-bat-dau",
          "short_description": "Học Python từ con số 0, phù hợp cho người mới bắt đầu",
          "difficulty_level": "beginner",
          "language": "vi",
          "price": {
            "amount": 299000.0,
            "display": "299,000đ",
            "is_free": false,
            "original_price": 499000.0
          },
          "rating": {
            "average": null,
            "has_enough_ratings": false,
            "total_ratings": 0
          },
          "stats": {
            "duration_hours": 40,
            "total_enrollments": 0,
            "total_lessons": 50
          },
          "instructor": {
            "id": 117,
            "name": "Giảng viên Mẫu"
          },
          "category": {
            "id": 1,
            "name": "Lập trình"
          },
          "thumbnail_url": "https://example.com/python-course.jpg",
          "published_at": "2025-09-21T01:04:59"
        }
      ],
      "filters_applied": {},
      "pagination": {
        "current_page": 1,
        "per_page": 12,
        "total": 8,
        "pages": 1,
        "has_next": false,
        "has_prev": false,
        "next_page": null,
        "prev_page": null
      },
      "sort_by": "popularity"
    },
    "success": true
  }
}
```

---

### 2. Get Catalog Filters
**GET** `/catalog/filters`

Get available filter options for the course catalog.

#### Example Response
```json
{
  "success": true,
  "message": "Catalog filters retrieved successfully",
  "data": {
    "categories": [
      {"id": 1, "name": "Programming", "slug": "programming"},
      {"id": 2, "name": "Design", "slug": "design"}
    ],
    "levels": ["beginner", "intermediate", "advanced"],
    "price_range": {
      "min": 0,
      "max": 299.99
    },
    "instructors": [
      {"id": 1, "full_name": "John Doe"},
      {"id": 2, "full_name": "Jane Smith"}
    ]
  }
}
```

---

### 3. Get Popular Courses
**GET** `/popular`

Retrieve most popular courses based on enrollment numbers.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 10 | Number of courses to return (max: 20) |

#### Example Response
```json
{
  "success": true,
  "message": "Popular courses retrieved successfully",
  "data": [
    {
      "id": 1,
      "title": "Complete Web Development Bootcamp",
      "slug": "complete-web-development-bootcamp",
      "price": 199.99,
      "rating": 4.8,
      "total_students": 5420,
      "instructor": {
        "id": 1,
        "full_name": "John Doe"
      },
      "thumbnail_url": "https://example.com/thumbnail.jpg"
    }
  ]
}
```

---

### 4. Get Top-Rated Courses
**GET** `/top-rated`

Retrieve highest-rated courses.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 10 | Number of courses to return (max: 20) |

#### Example Response
```json
{
  "success": true,
  "message": "Top-rated courses retrieved successfully",
  "data": [
    {
      "id": 2,
      "title": "Advanced JavaScript Concepts",
      "slug": "advanced-javascript-concepts",
      "price": 149.99,
      "rating": 4.9,
      "total_students": 2100,
      "instructor": {
        "id": 2,
        "full_name": "Jane Smith"
      },
      "thumbnail_url": "https://example.com/thumbnail.jpg"
    }
  ]
}
```

---

### 5. Get Free Courses
**GET** `/free`

Retrieve all free courses with pagination.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number for pagination |
| `per_page` | integer | No | 12 | Items per page (max: 50) |

#### Example Response
```json
{
  "success": true,
  "message": "Free courses retrieved successfully",
  "data": {
    "courses": [
      {
        "id": 3,
        "title": "HTML Basics",
        "slug": "html-basics",
        "description": "Learn HTML fundamentals",
        "price": 0.00,
        "level": "beginner",
        "rating": 4.3,
        "total_students": 8900,
        "is_free": true
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 12,
      "total": 15,
      "pages": 2,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

### 6. Search Courses
**GET** `/search`

Search courses by keyword in title and description.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | Yes | - | Search query keyword |
| `page` | integer | No | 1 | Page number for pagination |
| `per_page` | integer | No | 12 | Items per page (max: 50) |

#### Example Request
```bash
GET /api/courses/search?q=python&page=1&per_page=10
```

#### Example Response
```json
{
  "success": true,
  "message": "Search results retrieved successfully",
  "data": {
    "courses": [
      {
        "id": 1,
        "title": "Introduction to Python",
        "slug": "introduction-to-python",
        "description": "Learn Python programming from scratch",
        "price": 99.99,
        "rating": 4.5,
        "total_students": 1250,
        "match_score": 0.95
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 8,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    },
    "search_query": "python"
  }
}
```

---

### 7. Get Categories
**GET** `/categories`

Retrieve all course categories.

#### Example Response
```json
{
  "success": true,
  "message": "Categories retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "Programming",
      "slug": "programming",
      "description": "Learn programming languages and frameworks"
    },
    {
      "id": 2,
      "name": "Design",
      "slug": "design",
      "description": "UI/UX design and graphic design courses"
    }
  ]
}
```

---

### 8. Get Categories with Course Count
**GET** `/categories/with-count`

Retrieve categories with the number of courses in each category.

#### Example Response
```json
{
  "success": true,
  "message": "Categories with count retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "Programming",
      "slug": "programming",
      "description": "Learn programming languages and frameworks",
      "course_count": 25
    },
    {
      "id": 2,
      "name": "Design",
      "slug": "design",
      "description": "UI/UX design and graphic design courses",
      "course_count": 18
    }
  ]
}
```

---

### 9. Get Course by Slug
**GET** `/{slug}`

Retrieve detailed information about a specific course by its slug.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `slug` | string | Yes | Course slug identifier |

#### Example Request
```bash
GET /api/courses/introduction-to-python
```

#### Example Response
```json
{
  "success": true,
  "message": "Course details retrieved successfully",
  "data": {
    "id": 1,
    "title": "Introduction to Python",
    "slug": "introduction-to-python",
    "description": "Comprehensive Python programming course for beginners",
    "long_description": "This course covers all Python fundamentals...",
    "price": 99.99,
    "level": "beginner",
    "duration_hours": 20,
    "rating": 4.5,
    "total_students": 1250,
    "total_reviews": 340,
    "language": "English",
    "last_updated": "2024-01-10T15:30:00Z",
    "instructor": {
      "id": 1,
      "full_name": "John Doe",
      "bio": "Experienced Python developer with 10+ years",
      "avatar_url": "https://example.com/avatar.jpg",
      "total_students": 15000,
      "total_courses": 8
    },
    "category": {
      "id": 1,
      "name": "Programming",
      "slug": "programming"
    },
    "thumbnail_url": "https://example.com/thumbnail.jpg",
    "preview_video_url": "https://example.com/preview.mp4",
    "is_free": false,
    "requirements": [
      "Basic computer knowledge",
      "No programming experience required"
    ],
    "what_you_will_learn": [
      "Python syntax and fundamentals",
      "Object-oriented programming",
      "Working with files and databases"
    ],
    "modules": [
      {
        "id": 1,
        "title": "Getting Started",
        "order": 1,
        "lessons_count": 5,
        "duration_minutes": 120
      }
    ],
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T14:45:00Z"
  }
}
```

---

### 10. Get Course Reviews
**GET** `/{course_id}/reviews`

Retrieve reviews for a specific course with pagination.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | integer | Yes | Course ID |

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number for pagination |
| `per_page` | integer | No | 10 | Items per page (max: 20) |

#### Example Request
```bash
GET /api/courses/1/reviews?page=1&per_page=5
```

#### Example Response
```json
{
  "success": true,
  "message": "Course reviews retrieved successfully",
  "data": {
    "reviews": [
      {
        "id": 1,
        "rating": 5,
        "comment": "Excellent course! Very well explained.",
        "user": {
          "id": 10,
          "full_name": "Alice Johnson",
          "avatar_url": "https://example.com/avatar.jpg"
        },
        "created_at": "2024-01-18T09:15:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 5,
      "total": 340,
      "pages": 68,
      "has_next": true,
      "has_prev": false
    },
    "rating_summary": {
      "average_rating": 4.5,
      "total_reviews": 340,
      "rating_distribution": {
        "5": 180,
        "4": 120,
        "3": 30,
        "2": 8,
        "1": 2
      }
    }
  }
}
```

---

### 11. Get Similar Courses
**GET** `/{course_id}/similar`

Get courses similar to the specified course.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | integer | Yes | Course ID |

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 6 | Number of courses to return (max: 12) |

#### Example Response
```json
{
  "success": true,
  "message": "Similar courses retrieved successfully",
  "data": [
    {
      "id": 4,
      "title": "Python for Data Science",
      "slug": "python-for-data-science",
      "price": 129.99,
      "rating": 4.6,
      "total_students": 890,
      "instructor": {
        "id": 3,
        "full_name": "Bob Wilson"
      },
      "thumbnail_url": "https://example.com/thumbnail.jpg",
      "similarity_score": 0.85
    }
  ]
}
```

---

### 12. Health Check
**GET** `/health`

Health check endpoint for monitoring course service status.

#### Example Response
```json
{
  "success": true,
  "message": "Course service is running",
  "data": {
    "status": "healthy"
  }
}
```

---

## Error Responses

### Common Error Codes
- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Course or resource not found
- **500 Internal Server Error**: Server error

### Error Response Format
```json
{
  "success": false,
  "message": "Error description",
  "data": null
}
```

### Example Error Responses

#### Course Not Found (404)
```json
{
  "success": false,
  "message": "Course not found",
  "data": null
}
```

#### Invalid Search Query (400)
```json
{
  "success": false,
  "message": "Search query is required",
  "data": null
}
```

#### Internal Server Error (500)
```json
{
  "success": false,
  "message": "Internal server error",
  "data": null
}
```

---

## Rate Limiting
Currently, no rate limiting is implemented for course endpoints. However, it's recommended to implement rate limiting in production environments.

---

## Notes
- All datetime fields are returned in ISO 8601 format (UTC)
- Pagination follows the standard format with `page`, `per_page`, `total`, `pages`, `has_next`, and `has_prev` fields
- Course slugs are unique and URL-friendly identifiers
- Prices are in USD format with 2 decimal places
- Ratings are on a scale of 1-5 with decimal precision

---

**Last Updated**: January 2025  
**API Version**: 1.0  
**Contact**: Development Team