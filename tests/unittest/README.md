# Unit Tests - Online Learning System

Thư mục này chứa tất cả unit tests và integration tests cho Online Learning System, được tổ chức theo User Stories.

## 📁 File Structure

```
unittest/
├── README.md                              # This file
├── pytest.ini                             # Pytest configuration
├── run_tests.py                           # Test runner script
├── __init__.py                            # Package init
├── OLS_US_001_UserRegistration_Test.py    # Unit tests cho User Registration
├── OLS_US_001_UserRegistration_API_Test.py # API tests cho User Registration
├── OLS_US_002_UserLogin_Test.py           # Unit tests cho User Login
├── OLS_US_003_UserProfile_Test.py         # Unit tests cho User Profile
└── [Future test files...]                 # Tests cho các User Stories khác
```

## 🎯 Naming Convention

**Format:** `OLS_US_XXX_FeatureName_Test.py`

- `OLS` = Online Learning System
- `US` = User Story
- `XXX` = User Story number (001, 002, etc.)
- `FeatureName` = Tên feature (UserRegistration, UserLogin, etc.)
- `Test` = Suffix để identify test files

**Examples:**
- `OLS_US_001_UserRegistration_Test.py` - Unit tests cho User Registration
- `OLS_US_001_UserRegistration_API_Test.py` - API integration tests
- `OLS_US_002_UserLogin_Test.py` - Unit tests cho User Login

## 🚀 Running Tests

### Run All Tests
```bash
# Run all unit tests và API tests
python unittest/run_tests.py

# Run với pytest directly
pytest unittest/ -v
```

### Run Specific Tests
```bash
# Run tests cho specific User Story
python unittest/run_tests.py --ticket OLS-US-001

# Run only unit tests (no API tests)
python unittest/run_tests.py --unit-only

# Run only API integration tests
python unittest/run_tests.py --api-only

# Run specific test file
pytest unittest/OLS_US_001_UserRegistration_Test.py -v

# Run specific test class
pytest unittest/OLS_US_001_UserRegistration_Test.py::TestUserRegistration -v

# Run specific test method
pytest unittest/OLS_US_001_UserRegistration_Test.py::TestUserRegistration::test_successful_registration_with_email_confirmation -v
```

### Run with Coverage
```bash
# Install coverage first
pip install pytest-cov

# Run với coverage report
pytest unittest/ --cov=app --cov-report=html --cov-report=term
```

## 📊 Test Categories

### Unit Tests
- **Purpose:** Test individual functions và methods in isolation
- **Scope:** Single components, mocked dependencies
- **Files:** `*_Test.py` (không có API suffix)
- **Example:** `OLS_US_001_UserRegistration_Test.py`

### API Integration Tests  
- **Purpose:** Test complete API endpoints với real HTTP requests
- **Scope:** Full request-response cycle
- **Files:** `*_API_Test.py`
- **Example:** `OLS_US_001_UserRegistration_API_Test.py`

## 🎯 Test Coverage by User Story

### ✅ OLS-US-001: User Registration
- **Unit Tests:** `OLS_US_001_UserRegistration_Test.py`
- **API Tests:** `OLS_US_001_UserRegistration_API_Test.py`
- **Coverage:** 
  - Successful registration với email confirmation
  - Duplicate email validation
  - Password strength validation
  - Email format validation
  - Required fields validation
  - Role assignment (Student/Instructor)
  - Email confirmation flow

### 🔄 OLS-US-002: User Login
- **Unit Tests:** `OLS_US_002_UserLogin_Test.py`
- **Coverage:**
  - Successful login với JWT tokens
  - Invalid credentials handling
  - Account lockout functionality

### 🔄 OLS-US-003: User Profile Management
- **Unit Tests:** `OLS_US_003_UserProfile_Test.py`
- **Coverage:**
  - Profile information retrieval
  - Profile updates
  - Dashboard functionality

## 🛠️ Test Setup

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov requests

# Ensure database is setup
python scripts/init_database.py
```

### Environment Setup
- Tests sử dụng `testing` configuration
- In-memory SQLite database cho unit tests
- Real MySQL database cho API integration tests
- Mock email service để avoid sending real emails

## 📝 Writing New Tests

### 1. Create New Test File
```python
# unittest/OLS_US_XXX_FeatureName_Test.py
"""
Unit Tests for User Story OLS-US-XXX: Feature Name
Tests Feature functionality

Test Coverage:
- List what the tests cover
"""

import pytest
import json
from app import create_app, db
from app.models.user import User

@pytest.fixture
def app():
    """Create test application"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

class TestFeatureName:
    """Test User Story OLS-US-XXX: Feature Name"""
    
    def test_feature_functionality(self, client):
        """Test specific functionality"""
        # Test implementation
        pass
```

### 2. Follow Naming Conventions
- Class names: `TestFeatureName`
- Method names: `test_specific_functionality`
- Descriptive docstrings cho mỗi test

### 3. Include Acceptance Criteria
- Map tests đến specific acceptance criteria
- Include Given-When-Then scenarios trong docstrings
- Test both positive và negative cases

## 🔍 Debugging Tests

### Run Single Test với Debug Info
```bash
pytest unittest/OLS_US_001_UserRegistration_Test.py::TestUserRegistration::test_successful_registration_with_email_confirmation -v -s
```

### Check Test Database
```python
# Add này vào test để inspect database
with client.application.app_context():
    users = User.query.all()
    print(f"Users in database: {[u.email for u in users]}")
```

### Mock External Services
```python
# Mock email service trong tests
from unittest.mock import patch

@patch('app.blueprints.auth.send_confirmation_email')
def test_registration_without_email(mock_send_email, client):
    mock_send_email.return_value = True
    # Test implementation
```

## 📈 Continuous Integration

Tests được run automatically trong CI/CD pipeline:
- Pre-commit hooks run unit tests
- Pull requests run full test suite
- Deployment pipeline requires all tests pass

## 🎯 Best Practices

1. **Test Isolation:** Mỗi test độc lập, không depend on other tests
2. **Clear Naming:** Test names mô tả exactly what they test
3. **Arrange-Act-Assert:** Structure tests với clear setup, action, và verification
4. **Mock External Dependencies:** Don't rely on external services trong unit tests
5. **Test Edge Cases:** Include boundary conditions và error scenarios
6. **Keep Tests Fast:** Unit tests should run quickly
7. **Meaningful Assertions:** Assert specific expected outcomes, not just "no error"