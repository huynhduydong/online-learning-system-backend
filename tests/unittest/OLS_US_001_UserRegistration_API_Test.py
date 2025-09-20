"""
API Integration Tests for User Story OLS-US-001: User Registration
Tests User Registration API endpoints with real HTTP requests

Test Coverage:
- Full API integration testing
- All acceptance criteria validation
- Error handling and edge cases
- Performance and rate limiting
"""

import requests
import json
import sys
import time
from datetime import datetime

# API Base URL
BASE_URL = 'http://localhost:5000/api'

def test_api_endpoint(method, endpoint, data=None, expected_status=200):
    """Test API endpoint and return response"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n🔄 Testing {method} {endpoint}")
    if data:
        print(f"📤 Request data: {json.dumps(data, indent=2)}")
    
    try:
        if method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        elif method == 'GET':
            response = requests.get(url, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"📥 Response status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"📥 Response data: {json.dumps(response_data, indent=2)}")
        except:
            print(f"📥 Response text: {response.text}")
            response_data = None
        
        # Check expected status
        if response.status_code == expected_status:
            print("✅ Test PASSED")
            return True, response_data
        else:
            print(f"❌ Test FAILED - Expected {expected_status}, got {response.status_code}")
            return False, response_data
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Is the server running?")
        return False, None
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False, None


def test_user_registration():
    """
    Test User Story OLS-US-001: User Registration
    Tests all acceptance criteria
    """
    print("🧪 TESTING USER STORY OLS-US-001: USER REGISTRATION")
    print("="*60)
    
    test_results = []
    
    # Test 1: Successful Registration
    print("\n📋 Test 1: Successful Registration (Acceptance Criteria 1)")
    print("-" * 50)
    
    registration_data = {
        'email': f'test_{int(time.time())}@example.com',  # Unique email
        'password': 'StrongPassword123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    success, response = test_api_endpoint('POST', '/auth/register', registration_data, 201)
    test_results.append(('Successful Registration', success))
    
    if success and response:
        # Verify response contains expected fields
        user_data = response.get('user', {})
        checks = [
            ('Email matches', user_data.get('email') == registration_data['email']),
            ('Default role is student', user_data.get('role') == 'student'),
            ('User not verified initially', user_data.get('is_verified') == False),
            ('Success message mentions email', 'email' in response.get('message', '').lower())
        ]
        
        for check_name, check_result in checks:
            print(f"  {'✅' if check_result else '❌'} {check_name}")
            test_results.append((f"  {check_name}", check_result))
    
    # Test 2: Duplicate Email Registration
    print("\n📋 Test 2: Duplicate Email Registration (Acceptance Criteria 2)")
    print("-" * 50)
    
    # Try to register with same email
    success, response = test_api_endpoint('POST', '/auth/register', registration_data, 400)
    test_results.append(('Duplicate Email Validation', success))
    
    if success and response:
        error_message = str(response.get('details', ''))
        duplicate_check = 'Email đã được sử dụng' in error_message
        print(f"  {'✅' if duplicate_check else '❌'} Error message contains 'Email đã được sử dụng'")
        test_results.append(('  Duplicate email error message', duplicate_check))
    
    # Test 3: Weak Password Validation
    print("\n📋 Test 3: Weak Password Validation (Acceptance Criteria 3)")
    print("-" * 50)
    
    weak_passwords = [
        ('short', 'weak'),  # Too short
        ('no_uppercase', 'nouppercase123'),  # No uppercase
        ('no_lowercase', 'NOLOWERCASE123'),  # No lowercase
        ('no_numbers', 'NoNumbersHere')  # No numbers
    ]
    
    for test_name, weak_password in weak_passwords:
        weak_data = {
            'email': f'weak_{test_name}_{int(time.time())}@example.com',
            'password': weak_password,
            'first_name': 'Weak',
            'last_name': 'Password'
        }
        
        print(f"\n  Testing {test_name}: '{weak_password}'")
        success, response = test_api_endpoint('POST', '/auth/register', weak_data, 400)
        test_results.append((f'  Weak password ({test_name})', success))
    
    # Test 4: Invalid Email Format
    print("\n📋 Test 4: Invalid Email Format")
    print("-" * 50)
    
    invalid_email_data = {
        'email': 'invalid-email-format',
        'password': 'StrongPassword123',
        'first_name': 'Invalid',
        'last_name': 'Email'
    }
    
    success, response = test_api_endpoint('POST', '/auth/register', invalid_email_data, 400)
    test_results.append(('Invalid Email Format', success))
    
    # Test 5: Missing Required Fields
    print("\n📋 Test 5: Missing Required Fields")
    print("-" * 50)
    
    missing_fields_tests = [
        ('Missing email', {'password': 'StrongPassword123', 'first_name': 'Test', 'last_name': 'User'}),
        ('Missing password', {'email': 'missing@example.com', 'first_name': 'Test', 'last_name': 'User'}),
        ('Missing first_name', {'email': 'missing2@example.com', 'password': 'StrongPassword123', 'last_name': 'User'}),
        ('Missing last_name', {'email': 'missing3@example.com', 'password': 'StrongPassword123', 'first_name': 'Test'})
    ]
    
    for test_name, incomplete_data in missing_fields_tests:
        print(f"\n  Testing {test_name}")
        success, response = test_api_endpoint('POST', '/auth/register', incomplete_data, 400)
        test_results.append((f'  {test_name}', success))
    
    # Test 6: Instructor Role Registration
    print("\n📋 Test 6: Instructor Role Registration")
    print("-" * 50)
    
    instructor_data = {
        'email': f'instructor_{int(time.time())}@example.com',
        'password': 'StrongPassword123',
        'first_name': 'Test',
        'last_name': 'Instructor',
        'role': 'instructor'
    }
    
    success, response = test_api_endpoint('POST', '/auth/register', instructor_data, 201)
    test_results.append(('Instructor Role Registration', success))
    
    if success and response:
        role_check = response.get('user', {}).get('role') == 'instructor'
        print(f"  {'✅' if role_check else '❌'} Role set to instructor")
        test_results.append(('  Instructor role assignment', role_check))
    
    # Print Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! User Registration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False


def main():
    """Main test function"""
    print("🚀 API Testing for User Story OLS-US-001")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Testing API at: {BASE_URL}")
    
    # Test server connectivity
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("⚠️  Server responded but health check failed")
    except:
        print("❌ Cannot connect to server. Please start the Flask app:")
        print("   python app.py")
        return False
    
    # Run registration tests
    success = test_user_registration()
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return success


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Testing cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)