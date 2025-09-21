# 📋 Course Registration Workflow API Specification

## Overview
This document outlines the complete API specification for the Course Registration Workflow system. All endpoints require proper authentication and follow RESTful conventions.

## 🔐 Authentication
All APIs require **Authorization header**: `Bearer <access_token>`

---

## 1. Course Registration Initiation

### `POST /api/enrollments/register`

**Purpose**: Initialize the course registration process

**Request Headers**:
```
Content-Type: application/json
Authorization: Bearer <access_token>
```

**Request Payload**:
```json
{
  "course_id": "string",        // Course ID (required)
  "full_name": "string",        // Student's full name (required)
  "email": "string",            // Email for certificate delivery (required)
  "discount_code": "string"     // Discount code (optional)
}
```

**Validation Rules**:
- `course_id`: Must be a valid existing course ID
- `full_name`: Minimum 2 characters, maximum 100 characters, letters and spaces only
- `email`: Valid email format, maximum 255 characters
- `discount_code`: Must be a valid active discount code if provided

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Registration started successfully",
  "data": {
    "enrollment": {
      "id": "string",                    // Enrollment ID (UUID recommended)
      "course_id": "string",             // Course ID
      "user_id": "string",               // User ID
      "status": "pending|payment_pending|enrolled|activating|active",
      "payment_status": "pending|completed|failed|cancelled",
      "enrollment_date": "2024-01-01T00:00:00Z",
      "activation_date": "2024-01-01T00:00:00Z",  // nullable
      "payment_amount": 299000,          // Amount in VND
      "discount_applied": 50000,         // Discount amount in VND
      "access_granted": false            // Access permission status
    },
    "payment_required": true,            // Whether payment is required
    "payment_url": "string",            // Payment URL (if needed)
    "access_immediate": false           // Immediate access for free courses
  }
}
```

**Error Response (400/422)**:
```json
{
  "success": false,
  "error": "Validation failed",
  "message": "Email is already registered for this course",
  "details": {
    "email": ["This email is already enrolled in this course"],
    "discount_code": ["Invalid discount code"],
    "course_id": ["Course not found or not available for enrollment"]
  }
}
```

---

## 2. Payment Processing

### `POST /api/enrollments/payment`

**Purpose**: Process payment for course enrollment

**Request Payload**:
```json
{
  "enrollment_id": "string",           // Enrollment ID (required)
  "payment_method": "credit_card|paypal|bank_transfer",
  "payment_details": {                 // Varies by payment method
    // For credit_card:
    "card_number": "string",           // Credit card number
    "card_expiry": "string",           // MM/YY format
    "card_cvv": "string",              // CVV code
    "card_holder_name": "string",      // Cardholder name
    
    // For paypal:
    "paypal_email": "string",          // PayPal email
    
    // For bank_transfer:
    "bank_account": "string",          // Bank account number
    "bank_code": "string"              // Bank code
  }
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Payment processed successfully",
  "data": {
    "id": "string",                    // Enrollment ID
    "course_id": "string",
    "user_id": "string",
    "status": "enrolled|payment_failed",
    "payment_status": "completed|failed|cancelled",
    "enrollment_date": "2024-01-01T00:00:00Z",
    "activation_date": "2024-01-01T00:00:00Z", // If payment successful
    "payment_amount": 299000,
    "discount_applied": 50000,
    "access_granted": true,            // true if payment successful
    "transaction_id": "string",        // Payment transaction ID
    "payment_method": "credit_card",
    "payment_details": {
      "last_four_digits": "1234",      // Last 4 digits of card
      "payment_gateway": "stripe"      // Payment gateway used
    }
  }
}
```

**Error Response (400/422)**:
```json
{
  "success": false,
  "error": "Payment failed",
  "message": "Credit card declined",
  "details": {
    "payment_error": "Insufficient funds",
    "error_code": "CARD_DECLINED",
    "gateway_response": "Transaction declined by issuer"
  }
}
```

---

## 3. Course Access Activation

### `POST /api/enrollments/{enrollmentId}/activate`

**Purpose**: Activate course access after successful enrollment/payment

**URL Parameters**:
- `enrollmentId`: The enrollment ID (string)

**Request Payload**: `{}` (Empty JSON object)

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Course access activated",
  "data": {
    "success": true,
    "access_granted": true,
    "first_lesson_url": "/courses/react-basics/lessons/1", // First lesson URL
    "retry_available": false,          // Retry option availability
    "activation_time": "2024-01-01T00:00:00Z"
  }
}
```

**Delayed/Retry Response (200)**:
```json
{
  "success": true,
  "message": "Activation in progress",
  "data": {
    "success": false,
    "access_granted": false,
    "first_lesson_url": null,
    "retry_available": true,
    "estimated_completion": "2024-01-01T00:05:00Z" // Estimated completion time
  }
}
```

---

## 4. Enrollment Status Check

### `GET /api/enrollments/{enrollmentId}`

**Purpose**: Retrieve enrollment status by ID

**URL Parameters**:
- `enrollmentId`: The enrollment ID (string)

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Enrollment status retrieved",
  "data": {
    "id": "string",
    "course_id": "string",
    "user_id": "string",
    "status": "pending|payment_pending|enrolled|activating|active",
    "payment_status": "pending|completed|failed|cancelled",
    "enrollment_date": "2024-01-01T00:00:00Z",
    "activation_date": "2024-01-01T00:00:00Z", // nullable
    "payment_amount": 299000,
    "discount_applied": 50000,
    "access_granted": true,
    "course_title": "React Fundamentals", // Course title for display
    "course_slug": "react-fundamentals",  // Course slug
    "progress": {                         // Learning progress (optional)
      "completed_lessons": 5,
      "total_lessons": 20,
      "percentage": 25,
      "last_accessed": "2024-01-15T10:30:00Z"
    },
    "certificate": {                      // Certificate info (if completed)
      "issued": true,
      "issue_date": "2024-02-01T00:00:00Z",
      "certificate_url": "/certificates/enrollment-123.pdf"
    }
  }
}
```

---

## 5. User Enrollments

### `GET /api/enrollments/my-courses`

**Purpose**: Retrieve all course enrollments for the authenticated user

**Query Parameters**:
- `status`: Filter by enrollment status (optional)
- `page`: Page number for pagination (default: 1)
- `limit`: Number of items per page (default: 10, max: 50)

**Success Response (200)**:
```json
{
  "success": true,
  "message": "User enrollments retrieved",
  "data": [
    {
      "id": "enrollment-1",
      "course_id": "1",
      "user_id": "1",
      "status": "active",
      "payment_status": "completed",
      "enrollment_date": "2024-01-01T00:00:00Z",
      "activation_date": "2024-01-01T00:00:00Z",
      "payment_amount": 299000,
      "discount_applied": 0,
      "access_granted": true,
      "course": {                       // Course information
        "id": "1",
        "title": "React Fundamentals",
        "slug": "react-fundamentals",
        "thumbnail_url": "/images/react-course.jpg",
        "difficulty_level": "beginner",
        "instructor": {
          "id": "instructor-1",
          "name": "John Doe",
          "avatar": "/images/john-doe.jpg"
        }
      },
      "progress": {
        "completed_lessons": 5,
        "total_lessons": 20,
        "percentage": 25,
        "last_accessed": "2024-01-15T10:30:00Z",
        "total_time_spent": 1800        // In seconds
      }
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "total_items": 25,
    "per_page": 10
  }
}
```

---

## 6. Course Access Check

### `GET /api/enrollments/check-access/{courseId}`

**Purpose**: Check if the authenticated user has access to a specific course

**URL Parameters**:
- `courseId`: The course ID (string)

**Success Response (200) - Has Access**:
```json
{
  "success": true,
  "message": "Course access checked",
  "data": {
    "hasAccess": true,
    "enrollmentStatus": {              // null if not enrolled
      "id": "enrollment-1",
      "course_id": "1",
      "user_id": "1",
      "status": "active",
      "payment_status": "completed",
      "enrollment_date": "2024-01-01T00:00:00Z",
      "activation_date": "2024-01-01T00:00:00Z",
      "payment_amount": 299000,
      "discount_applied": 0,
      "access_granted": true
    },
    "nextLessonUrl": "/courses/react-fundamentals/lessons/6", // Next lesson to continue
    "canDownloadCertificate": false    // Certificate availability
  }
}
```

**Success Response (200) - No Access**:
```json
{
  "success": true,
  "message": "No access to course",
  "data": {
    "hasAccess": false,
    "enrollmentStatus": null,
    "reasonCode": "NOT_ENROLLED|PAYMENT_PENDING|ENROLLMENT_EXPIRED",
    "message": "You need to enroll in this course to access the content"
  }
}
```

---

## 7. Retry Activation

### `POST /api/enrollments/{enrollmentId}/retry-activation`

**Purpose**: Retry course activation when the initial process failed

**URL Parameters**:
- `enrollmentId`: The enrollment ID (string)

**Request Payload**: `{}` (Empty JSON object)

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Retry activation completed",
  "data": {
    "success": true,
    "access_granted": true,
    "first_lesson_url": "/courses/react-basics/lessons/1",
    "retry_available": false,
    "activation_time": "2024-01-01T00:00:00Z"
  }
}
```

**Failed Retry Response (200)**:
```json
{
  "success": true,
  "message": "Retry activation failed",
  "data": {
    "success": false,
    "access_granted": false,
    "first_lesson_url": null,
    "retry_available": true,
    "max_retries_reached": false,
    "next_retry_available_at": "2024-01-01T00:15:00Z"
  }
}
```

---

## 🚨 Common Error Responses

### Authentication Error (401)
```json
{
  "success": false,
  "error": "Unauthorized",
  "message": "Access token is missing or invalid",
  "error_code": "AUTH_REQUIRED"
}
```

### Forbidden Error (403)
```json
{
  "success": false,
  "error": "Forbidden",
  "message": "You don't have permission to access this resource",
  "error_code": "INSUFFICIENT_PERMISSIONS"
}
```

### Not Found Error (404)
```json
{
  "success": false,
  "error": "Not found",
  "message": "Enrollment not found",
  "error_code": "ENROLLMENT_NOT_FOUND"
}
```

### Validation Error (422)
```json
{
  "success": false,
  "error": "Validation failed",
  "message": "The given data was invalid",
  "details": {
    "field_name": ["Field specific error message"],
    "another_field": ["Another error message"]
  }
}
```

### Rate Limit Error (429)
```json
{
  "success": false,
  "error": "Too many requests",
  "message": "Rate limit exceeded. Please try again later",
  "retry_after": 60
}
```

### Server Error (500)
```json
{
  "success": false,
  "error": "Internal server error",
  "message": "An unexpected error occurred",
  "error_code": "INTERNAL_ERROR",
  "request_id": "req_123456789"
}
```

---

## 📊 Status Workflows

### Enrollment Status Flow
```
pending → payment_pending → enrolled → activating → active
                ↓
         payment_failed → cancelled
```

### Payment Status Flow
```
pending → completed
    ↓
  failed → cancelled
```

---

## 📝 Implementation Notes

### 1. Security Considerations
- All payment data must be handled securely and comply with PCI DSS standards
- Use HTTPS for all API endpoints
- Implement rate limiting to prevent abuse
- Validate all input data thoroughly
- Log all payment transactions for audit purposes

### 2. Payment Gateway Integration
- Support multiple payment methods (credit card, PayPal, local payment gateways)
- Handle webhook notifications from payment providers
- Implement proper error handling for payment failures
- Store minimal payment information (avoid storing full card details)

### 3. Database Considerations
- Use UUIDs for enrollment IDs for better security
- Index frequently queried fields (user_id, course_id, status)
- Implement soft deletes for audit trail
- Store payment transactions in separate table

### 4. Email Notifications
- Send confirmation email after successful enrollment
- Send payment receipts after successful payment
- Send course access notifications after activation
- Send reminder emails for incomplete enrollments

### 5. Caching Strategy
- Cache course access checks for frequently accessed courses
- Cache user enrollment lists with appropriate TTL
- Invalidate cache when enrollment status changes

### 6. Monitoring and Analytics
- Track enrollment conversion rates
- Monitor payment success/failure rates
- Log API response times and errors
- Track user engagement post-enrollment

### 7. Testing Requirements
- Unit tests for all business logic
- Integration tests for payment workflows
- End-to-end tests for complete enrollment flow
- Load testing for high-traffic scenarios

---

## 🔄 Webhook Events (Optional)

### Payment Webhook
```json
{
  "event": "payment.completed",
  "data": {
    "enrollment_id": "string",
    "payment_id": "string",
    "amount": 299000,
    "currency": "VND",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Enrollment Webhook
```json
{
  "event": "enrollment.activated",
  "data": {
    "enrollment_id": "string",
    "course_id": "string",
    "user_id": "string",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

This specification provides a complete foundation for implementing the Course Registration Workflow backend APIs. All endpoints follow RESTful conventions and include comprehensive error handling and validation rules.
