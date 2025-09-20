"""
Database Initialization Script
Tạo tables và insert mock data cho development

Usage:
    python scripts/init_database.py
"""

import sys
import os
from datetime import datetime, timedelta
import random
import string
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path để import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User, UserRole

# Mock data generators (thay thế Faker)
VIETNAMESE_FIRST_NAMES = [
    'Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng',
    'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương', 'Lý', 'Đinh', 'Đào', 'Lương', 'Tô'
]

VIETNAMESE_LAST_NAMES = [
    'Văn Anh', 'Thị Hoa', 'Minh Tuấn', 'Thu Hương', 'Đức Nam', 'Thị Lan', 
    'Văn Hùng', 'Thị Mai', 'Quốc Bảo', 'Thị Linh', 'Văn Đức', 'Thị Nga',
    'Minh Khoa', 'Thu Thảo', 'Văn Long', 'Thị Hạnh', 'Đức Thắng', 'Thị Vân'
]

ENGLISH_FIRST_NAMES = [
    'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa',
    'James', 'Maria', 'William', 'Jennifer', 'Richard', 'Linda', 'Thomas', 'Patricia'
]

ENGLISH_LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Taylor'
]

def generate_email():
    """Generate random email"""
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'example.com']
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    domain = random.choice(domains)
    return f"{username}@{domain}"

def generate_vietnamese_name():
    """Generate Vietnamese name"""
    first = random.choice(VIETNAMESE_FIRST_NAMES)
    last = random.choice(VIETNAMESE_LAST_NAMES)
    return first, last

def generate_english_name():
    """Generate English name"""
    first = random.choice(ENGLISH_FIRST_NAMES)
    last = random.choice(ENGLISH_LAST_NAMES)
    return first, last

def generate_random_date(start_date, end_date):
    """Generate random date between start and end"""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)


def create_tables():
    """Tạo tất cả database tables"""
    print("🔨 Creating database tables...")
    
    try:
        db.create_all()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def create_mock_users():
    """Tạo mock users cho testing"""
    print("👥 Creating mock users...")
    
    users_data = [
        # Admin user
        {
            'email': 'admin@ols.com',
            'password': 'Admin123456',
            'first_name': 'System',
            'last_name': 'Administrator',
            'role': UserRole.ADMIN,
            'is_verified': True
        },
        # Instructor users
        {
            'email': 'instructor1@ols.com',
            'password': 'Instructor123',
            'first_name': 'Nguyễn',
            'last_name': 'Văn Giảng',
            'role': UserRole.INSTRUCTOR,
            'is_verified': True
        },
        {
            'email': 'instructor2@ols.com',
            'password': 'Instructor123',
            'first_name': 'Trần',
            'last_name': 'Thị Hương',
            'role': UserRole.INSTRUCTOR,
            'is_verified': True
        },
        {
            'email': 'john.doe@ols.com',
            'password': 'Instructor123',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': UserRole.INSTRUCTOR,
            'is_verified': True
        },
        # Student users
        {
            'email': 'student1@ols.com',
            'password': 'Student123',
            'first_name': 'Lê',
            'last_name': 'Văn Học',
            'role': UserRole.STUDENT,
            'is_verified': True
        },
        {
            'email': 'student2@ols.com',
            'password': 'Student123',
            'first_name': 'Phạm',
            'last_name': 'Thị Sinh',
            'role': UserRole.STUDENT,
            'is_verified': True
        }
    ]
    
    created_users = []
    
    for user_data in users_data:
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if existing_user:
                print(f"⚠️  User {user_data['email']} already exists, skipping...")
                created_users.append(existing_user)
                continue
            
            # Create new user
            user = User(
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role']
            )
            user.is_verified = user_data['is_verified']
            
            db.session.add(user)
            created_users.append(user)
            print(f"✅ Created user: {user_data['email']} ({user_data['role'].value})")
            
        except Exception as e:
            print(f"❌ Error creating user {user_data['email']}: {e}")
    
    # Generate additional random students
    print("🎲 Generating additional random students...")
    
    for i in range(20):
        try:
            email = generate_email()
            
            # Check if email already exists
            if User.query.filter_by(email=email).first():
                continue
            
            first_name, last_name = generate_english_name()
            user = User(
                email=email,
                password='Student123',
                first_name=first_name,
                last_name=last_name,
                role=UserRole.STUDENT
            )
            user.is_verified = random.choice([True, False])
            user.created_at = generate_random_date(datetime.now() - timedelta(days=365), datetime.now())
            
            db.session.add(user)
            created_users.append(user)
            
        except Exception as e:
            print(f"❌ Error creating random user: {e}")
    
    try:
        db.session.commit()
        print(f"✅ Successfully created {len(created_users)} users!")
        return created_users
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving users: {e}")
        return []


def create_mock_categories():
    """Tạo mock categories cho courses (placeholder for Sprint 2)"""
    print("📚 Creating course categories (placeholder)...")
    
    # This will be implemented in Sprint 2
    categories_data = [
        'Lập trình',
        'Thiết kế',
        'Marketing',
        'Kinh doanh',
        'Ngoại ngữ',
        'Kỹ năng mềm',
        'Công nghệ thông tin',
        'Khoa học dữ liệu'
    ]
    
    print(f"📝 Prepared {len(categories_data)} categories for Sprint 2")
    return categories_data


def print_summary():
    """In tổng kết database"""
    print("\n" + "="*50)
    print("📊 DATABASE SUMMARY")
    print("="*50)
    
    # Count users by role
    total_users = User.query.count()
    admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
    instructor_count = User.query.filter_by(role=UserRole.INSTRUCTOR).count()
    student_count = User.query.filter_by(role=UserRole.STUDENT).count()
    verified_count = User.query.filter_by(is_verified=True).count()
    
    print(f"👥 Total Users: {total_users}")
    print(f"   - Admins: {admin_count}")
    print(f"   - Instructors: {instructor_count}")
    print(f"   - Students: {student_count}")
    print(f"   - Verified: {verified_count}")
    
    print("\n🔑 Test Accounts:")
    print("   Admin: admin@ols.com / Admin123456")
    print("   Instructor: instructor1@ols.com / Instructor123")
    print("   Student: student1@ols.com / Student123")
    
    print("\n🚀 Ready for development!")
    print("="*50)


def main():
    """Main initialization function"""
    print("🚀 Initializing Online Learning System Database...")
    print("="*60)
    
    # Create Flask app context
    app = create_app('development')
    
    with app.app_context():
        # Step 1: Create tables
        if not create_tables():
            print("❌ Failed to create tables. Exiting...")
            return False
        
        # Step 2: Create mock users
        users = create_mock_users()
        if not users:
            print("❌ Failed to create users. Exiting...")
            return False
        
        # Step 3: Prepare categories (for Sprint 2)
        categories = create_mock_categories()
        
        # Step 4: Print summary
        print_summary()
        
        return True


if __name__ == '__main__':
    try:
        success = main()
        if success:
            print("\n🎉 Database initialization completed successfully!")
        else:
            print("\n💥 Database initialization failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)