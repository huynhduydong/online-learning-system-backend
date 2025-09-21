# Online Learning System Backend - Project Rules

## 📁 Project Structure Rules

### Core Architecture
```
app/
├── models/          # Database models (SQLAlchemy)
├── services/        # Business logic layer
├── routers/         # API endpoints (FastAPI)
├── dao/            # Data Access Objects
├── validators/     # Input validation
├── utils/          # Utility functions
└── exceptions/     # Custom exceptions
```

### File Naming Conventions
- **Models**: `{entity}.py` (e.g., `user.py`, `course.py`)
- **Services**: `{entity}_service.py` (e.g., `user_service.py`, `auth_service.py`)
- **Routers**: `{entity}_router.py` (e.g., `user_router.py`, `auth_router.py`)
- **DAOs**: `{entity}_dao.py` (e.g., `user_dao.py`)
- **Validators**: `{entity}.py` (e.g., `user.py`, `auth.py`)

## 🏗️ Code Architecture Rules

### 1. Model Layer (`app/models/`)
```python
# REQUIRED: All models must inherit from db.Model
class User(db.Model):
    __tablename__ = 'users'
    
    # REQUIRED: Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # REQUIRED: Timestamps for all models
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # REQUIRED: Constructor with all required fields
    def __init__(self, required_field1, required_field2, **kwargs):
        self.required_field1 = required_field1
        self.required_field2 = required_field2
        # Set optional fields from kwargs
        
    # REQUIRED: __repr__ method
    def __repr__(self):
        return f'<User {self.id}>'
```

### 2. Service Layer (`app/services/`)
```python
# REQUIRED: All services must handle business logic only
class UserService:
    @staticmethod
    def create_user(data):
        try:
            # Validation
            # Business logic
            # Database operations via DAO
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            raise ValidationException(str(e))
    
    # REQUIRED: Always use try-catch with rollback
    # REQUIRED: Use ValidationException for business errors
```

### 3. Router Layer (`app/routers/`)
```python
# REQUIRED: Use FastAPI router pattern
from fastapi import APIRouter, Depends, HTTPException
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/")
async def create_user(data: UserCreateRequest):
    try:
        result = UserService.create_user(data.dict())
        return success_response(result, "User created successfully")
    except ValidationException as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("Internal server error", 500)

# REQUIRED: Always use success_response/error_response
# REQUIRED: Handle ValidationException separately
```

### 4. DAO Layer (`app/dao/`)
```python
# REQUIRED: All DAOs must inherit from BaseDAO
class UserDAO(BaseDAO):
    model = User
    
    @classmethod
    def find_by_email(cls, email):
        return cls.model.query.filter_by(email=email).first()
    
    # REQUIRED: Use class methods
    # REQUIRED: Specific query methods for each entity
```

## 🔒 Security Rules

### Authentication & Authorization
```python
# REQUIRED: Use JWT tokens with proper expiration
# REQUIRED: Always validate session activity
def require_auth():
    token = request.headers.get('Authorization')
    if not token:
        raise HTTPException(401, "Token required")
    
    user = verify_token(token)
    if user.is_session_expired():
        raise HTTPException(401, "Session expired")
    
    user.update_activity()  # REQUIRED: Update last_activity_at
    return user
```

### Password Security
```python
# REQUIRED: Minimum 8 characters, hash with bcrypt
def set_password(self, password):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
```

## 📝 Database Rules

### Field Naming Conventions
- **REQUIRED**: Use snake_case for all database fields
- **REQUIRED**: Use `_at` suffix for datetime fields: `created_at`, `updated_at`, `last_login_at`, `last_activity_at`
- **REQUIRED**: Use `_id` suffix for foreign keys: `user_id`, `course_id`

### Common Required Fields
```python
# REQUIRED for all models:
id = db.Column(db.Integer, primary_key=True)
created_at = db.Column(db.DateTime, default=datetime.utcnow)
updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# REQUIRED for User model:
last_login_at = db.Column(db.DateTime)  # NOT last_login
last_activity_at = db.Column(db.DateTime)  # NOT last_activity
```

### Migration Rules
```python
# REQUIRED: Always create migrations for schema changes
# REQUIRED: Use descriptive migration names
# Example: "add_last_activity_at_to_users"
```

## 🔧 Error Handling Rules

### Exception Hierarchy
```python
# REQUIRED: Use custom exceptions
class ValidationException(Exception):
    pass

class AuthenticationException(Exception):
    pass

class AuthorizationException(Exception):
    pass
```

### Response Format
```python
# REQUIRED: Consistent response format
def success_response(data=None, message="Success"):
    return {
        "success": True,
        "message": message,
        "data": data
    }

def error_response(message, status_code=400):
    return {
        "success": False,
        "message": message,
        "data": None
    }
```

## 🧪 Testing Rules

### Test Structure
```
tests/
├── unittest/           # Unit tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_routers.py
└── integration/        # Integration tests
```

### Test Naming
```python
# REQUIRED: Descriptive test names
def test_user_registration_with_valid_data():
    pass

def test_user_login_with_invalid_password():
    pass
```

## 📦 Dependencies Rules

### Import Order
```python
# 1. Standard library imports
import os
from datetime import datetime

# 2. Third-party imports
from flask import Flask
from sqlalchemy import Column

# 3. Local imports
from app.models.user import User
from app.services.auth_service import AuthService
```

### Required Dependencies
```python
# REQUIRED in requirements.txt:
Flask>=2.0.0
SQLAlchemy>=1.4.0
bcrypt>=3.2.0
PyJWT>=2.0.0
python-dotenv>=0.19.0
```

## 🔄 Session Management Rules

### Session Timeout
```python
# REQUIRED: 24-hour session timeout
SESSION_TIMEOUT_HOURS = 24

def is_session_expired(self):
    if not self.last_activity_at:
        return True
    return datetime.utcnow() - self.last_activity_at > timedelta(hours=SESSION_TIMEOUT_HOURS)
```

### Activity Tracking
```python
# REQUIRED: Update activity on every authenticated request
def update_activity(self):
    self.last_activity_at = datetime.utcnow()
    db.session.commit()
```

## 🚀 Deployment Rules

### Environment Variables
```python
# REQUIRED: Use .env for configuration
DATABASE_URL=sqlite:///instance/app.db
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

### Production Checklist
- [ ] All secrets in environment variables
- [ ] Database migrations applied
- [ ] Email service configured
- [ ] HTTPS enabled
- [ ] CORS properly configured

## 📋 Code Review Checklist

### Before Committing
- [ ] All field names use correct conventions (`last_login_at`, not `last_login`)
- [ ] All models have required timestamps
- [ ] All services handle exceptions properly
- [ ] All routers use consistent response format
- [ ] All database operations include rollback on error
- [ ] Session activity is updated on authenticated requests
- [ ] Tests are written and passing

### Common Mistakes to Avoid
❌ **DON'T**: Use `last_login` (use `last_login_at`)
❌ **DON'T**: Use `last_activity` (use `last_activity_at`)
❌ **DON'T**: Forget to update `last_activity_at` on login
❌ **DON'T**: Create User without password in constructor
❌ **DON'T**: Forget try-catch with rollback in services
❌ **DON'T**: Return raw exceptions to API responses

✅ **DO**: Follow the established patterns
✅ **DO**: Use consistent naming conventions
✅ **DO**: Handle errors gracefully
✅ **DO**: Update activity tracking properly
✅ **DO**: Use the service layer for business logic

## 🤖 AI Work History & Context Management Rules

### Work History Documentation
```markdown
# REQUIRED: AI must maintain work history in this section
# Format: ## [Date] - [Session Summary]
# Include: What was accomplished, files modified, issues resolved

## 2025-01-XX - Session Summary
### Accomplished:
- [List of completed tasks]
- [Files created/modified]
- [Issues resolved]

### Current Status:
- [Current state of the project]
- [Pending tasks]
- [Known issues]
```

### Context Management Requirements
```python
# REQUIRED: AI must read project history before starting work
def start_new_session():
    # 1. Read project_rules.md for current guidelines
    # 2. Review work history section for context
    # 3. Check recent commits/changes
    # 4. Understand current project state
    # 5. Identify pending tasks from previous sessions
```

### Session Documentation Rules
- **REQUIRED**: Document all significant changes made during each session
- **REQUIRED**: Update work history at the end of each session
- **REQUIRED**: Include file paths for all modified files
- **REQUIRED**: Note any breaking changes or important decisions
- **REQUIRED**: List any new dependencies or configuration changes

### Context Preservation
```markdown
# REQUIRED: Maintain these context elements
- Current project architecture state
- Recent feature implementations
- Known bugs or issues
- Pending tasks and their priorities
- Database schema changes
- API endpoint modifications
- Test coverage status
```

### Work History Template
```markdown
## [YYYY-MM-DD] - [Brief Session Description]

### 🎯 Session Goals:
- [Primary objectives for this session]

### ✅ Completed Tasks:
- [Task 1] - [Brief description and files affected]
- [Task 2] - [Brief description and files affected]

### 📁 Files Modified:
- `path/to/file1.py` - [What was changed]
- `path/to/file2.py` - [What was changed]

### 🐛 Issues Resolved:
- [Issue description] - [How it was fixed]

### ⚠️ Known Issues:
- [Any remaining issues or technical debt]

### 📋 Next Session Tasks:
- [Task 1] - [Priority level]
- [Task 2] - [Priority level]

### 🔧 Technical Notes:
- [Any important technical decisions or considerations]
- [Dependencies added/removed]
- [Configuration changes]
```

### AI Behavior Requirements
- **REQUIRED**: Always read the work history section before starting any new work
- **REQUIRED**: Reference previous sessions when making decisions
- **REQUIRED**: Maintain consistency with previous architectural decisions
- **REQUIRED**: Update work history before ending each session
- **REQUIRED**: Ask for clarification if work history conflicts with current request

---

## 📚 Work History

### Current Project Status
- **Architecture**: Flask-based REST API with SQLAlchemy ORM
- **Database**: SQLite for development
- **Authentication**: JWT-based with session management
- **Current Features**: User registration, login, profile management
- **Test Coverage**: Unit tests for user management features

### Recent Sessions
*[Work history will be documented here by AI in future sessions]*

---

**Last Updated**: January 2025
**Version**: 1.1
**Maintainer**: Development Team