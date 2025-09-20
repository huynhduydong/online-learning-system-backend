# Online Learning System - Backend

Hệ thống học tập trực tuyến được xây dựng với Flask, MySQL và Next.js.

## 🚀 Sprint 1: User Authentication & Profile Management

### ✅ Implemented Features

#### User Stories Completed:
- **OLS-US-001**: ✅ **User Registration** - Đăng ký tài khoản với email validation và confirmation
- **OLS-US-002**: User Login - Đăng nhập với JWT authentication  
- **OLS-US-003**: User Profile Management - Quản lý thông tin cá nhân và avatar

#### OLS-US-001 Implementation Details:
- ✅ Email format validation và password strength requirements
- ✅ Duplicate email detection với proper error messages
- ✅ Email confirmation system với secure tokens
- ✅ Default "Student" role assignment
- ✅ Instructor role option during registration
- ✅ Comprehensive validation cho all input fields
- ✅ Rate limiting để prevent abuse
- ✅ Full test coverage với automated tests

#### API Endpoints:
```
POST /api/auth/register              - Đăng ký tài khoản với email confirmation
POST /api/auth/login                 - Đăng nhập
POST /api/auth/refresh               - Refresh JWT token
POST /api/auth/logout                - Đăng xuất
GET  /api/auth/me                   - Thông tin user hiện tại
GET  /api/auth/confirm-email/<token> - Xác nhận email
POST /api/auth/resend-confirmation   - Gửi lại email xác nhận

GET  /api/users/profile              - Xem profile
PUT  /api/users/profile              - Cập nhật profile  
POST /api/users/upload-avatar        - Upload ảnh đại diện
GET  /api/users/dashboard            - Dashboard overview
```

## 🛠️ Quick Setup (Recommended)

### Option 1: Automatic Setup
```bash
# Clone repository
git clone <repository-url>
cd online-learning-system

# Run automatic setup
python setup.py
```

### Option 2: Manual Setup

#### Prerequisites
- Python 3.8+
- MySQL 8.0+
- pip và virtualenv

#### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment file
cp .env.example .env
```

#### 2. Database Setup
```bash
# Tạo MySQL database (xem database_setup.md để biết chi tiết)
mysql -u root -p
CREATE DATABASE online_learning_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ols_user'@'localhost' IDENTIFIED BY 'ols_password_2024';
GRANT ALL PRIVILEGES ON online_learning_dev.* TO 'ols_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 3. Configure Environment
Cập nhật `.env` file:
```
DATABASE_URL=mysql+pymysql://ols_user:ols_password_2024@localhost/online_learning_dev
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

#### 4. Initialize Database
```bash
# Test database connection
python scripts/test_connection.py

# Initialize database với mock data
python scripts/init_database.py
```

#### 5. Run Application
```bash
python app.py
```

Server sẽ chạy tại: http://127.0.0.1:5000

## 🎭 Mock Data

Script `init_database.py` sẽ tạo sẵn các test accounts:

### Test Accounts:
- **Admin**: admin@ols.com / Admin123456
- **Instructor**: instructor1@ols.com / Instructor123
- **Student**: student1@ols.com / Student123

### Mock Data Includes:
- 1 Admin user
- 3 Instructor users (2 Vietnamese, 1 English)
- 22+ Student users (2 fixed + 20 random generated)
- All users có verified status
- Random creation dates trong năm qua

### Database Management Scripts:
```bash
# Test database connection
python scripts/test_connection.py

# Initialize database với mock data
python scripts/init_database.py

# Reset database (xóa tất cả data)
python scripts/reset_database.py
```

## 🧪 Testing

### Automated Tests
```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov requests

# Run all tests (unit + API integration)
python unittest/run_tests.py

# Run specific User Story tests
python unittest/run_tests.py --ticket OLS-US-001

# Run only unit tests
python unittest/run_tests.py --unit-only

# Run only API integration tests
python unittest/run_tests.py --api-only

# Run with pytest directly
pytest unittest/ -v

# Run with coverage
pytest unittest/ --cov=app --cov-report=html --cov-report=term
```

### Test Organization
```
unittest/
├── OLS_US_001_UserRegistration_Test.py      # Unit tests
├── OLS_US_001_UserRegistration_API_Test.py  # API integration tests
├── OLS_US_002_UserLogin_Test.py             # Login tests
├── OLS_US_003_UserProfile_Test.py           # Profile tests
└── run_tests.py                             # Test runner
```

### Email Testing
```bash
# Start email development server (for testing email confirmation)
python scripts/email_dev_server.py
```

### Test API Endpoints

#### 1. User Registration
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "StrongPassword123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

#### 2. User Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com", 
    "password": "StrongPassword123"
  }'
```

#### 3. Get Profile (với JWT token)
```bash
curl -X GET http://localhost:5000/api/users/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📁 Project Structure

```
online-learning-system/
├── app/
│   ├── __init__.py              # Application factory
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── user.py             # User model (✅ Implemented)
│   │   ├── course.py           # Course models (🔄 Sprint 2)
│   │   ├── enrollment.py       # Enrollment models (🔄 Sprint 3)
│   │   ├── progress.py         # Progress models (🔄 Sprint 4)
│   │   ├── payment.py          # Payment models (🔄 Sprint 3)
│   │   └── qa.py              # Q&A models (🔄 Sprint 6)
│   └── blueprints/             # API endpoints
│       ├── __init__.py
│       ├── auth.py             # Authentication (✅ Implemented)
│       ├── users.py            # User management (✅ Implemented)
│       ├── courses.py          # Course management (🔄 Sprint 2)
│       ├── enrollments.py      # Enrollment (🔄 Sprint 3)
│       ├── payments.py         # Payment processing (🔄 Sprint 3)
│       ├── progress.py         # Progress tracking (🔄 Sprint 4)
│       └── qa.py              # Q&A system (🔄 Sprint 6)
├── tests/                      # Test files
│   ├── __init__.py
│   └── test_auth.py           # Auth tests (✅ Implemented)
├── uploads/                    # File uploads directory
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── app.py                     # Main application entry
├── .env.example               # Environment template
└── README.md                  # This file
```

## 🔒 Security Features

### Implemented:
- ✅ Password hashing với Werkzeug
- ✅ JWT authentication với access/refresh tokens
- ✅ Rate limiting cho API endpoints
- ✅ Input validation với marshmallow
- ✅ Account lockout sau 5 failed login attempts
- ✅ File upload validation và size limits
- ✅ CORS configuration

### Business Rules Implemented:
- ✅ Email phải unique trong hệ thống
- ✅ Mật khẩu tối thiểu 8 ký tự, có chữ hoa, chữ thường, số
- ✅ Tài khoản mới mặc định là "Student"
- ✅ Email không thể thay đổi sau khi tạo tài khoản
- ✅ Ảnh đại diện được resize về 200x200px
- ✅ File upload tối đa 2MB

## 🚧 Next Sprint: Course Discovery (Sprint 2)

### Upcoming Features:
- Course và Category models
- Course catalog API với search và filtering
- Course detail pages với preview content
- Rating và review system

### API Endpoints to Implement:
```
GET  /api/courses              # Course catalog với pagination
GET  /api/courses/search       # Search courses
GET  /api/courses/categories   # List categories  
GET  /api/courses/:id          # Course details
GET  /api/courses/:id/preview  # Preview content
```

## 📊 Development Status

| Sprint | Feature | Status | Progress |
|--------|---------|--------|----------|
| 1 | Authentication & Profile | ✅ Complete | 100% |
| 2 | Course Discovery | 🔄 Next | 0% |
| 3 | Enrollment & Payment | ⏳ Planned | 0% |
| 4 | Progress Tracking | ⏳ Planned | 0% |
| 5 | Course Creation | ⏳ Planned | 0% |
| 6 | Q&A System | ⏳ Planned | 0% |
| 7 | Security & Deployment | ⏳ Planned | 0% |

## 🤝 Contributing

1. Tạo feature branch từ main
2. Implement theo User Stories trong tasks.md
3. Viết tests cho new features
4. Submit pull request với description rõ ràng

## 📝 License

This project is licensed under the MIT License.