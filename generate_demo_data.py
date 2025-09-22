"""
Comprehensive Demo Data Generator for Online Learning System
Tạo dữ liệu demo đầy đủ cho tất cả các tables để demo mượt mà
"""

import sys
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment for MySQL database
os.environ['DATABASE_URL'] = 'mysql+pymysql://ols_user:ols_password_2024@localhost/online_learning_dev'

from app import create_app, db

# Import all models
from app.models.user import User, UserRole
from app.models.course import Course, Category, Module, Lesson, Content, ContentType, DifficultyLevel, CourseStatus
from app.models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus as EnrollmentPaymentStatus
from app.models.progress import LessonProgress, CourseProgress, ProgressStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.cart import Cart, CartItem, CartStatus
from app.models.coupon import Coupon, CouponType, CouponStatus
from app.models.qa import Question, Answer, Vote

# Initialize Faker for Vietnamese locale
fake = Faker(['vi_VN', 'en_US'])
Faker.seed(42)  # For reproducible data

class DemoDataGenerator:
    def __init__(self):
        self.users = []
        self.categories = []
        self.courses = []
        self.modules = []
        self.lessons = []
        self.contents = []
        self.coupons = []
        self.enrollments = []
        self.carts = []
        self.cart_items = []
        self.payments = []
        self.lesson_progress = []
        self.course_progress = []
        
    def generate_all_data(self):
        """Tạo tất cả dữ liệu demo theo thứ tự dependencies"""
        print("🚀 Starting comprehensive DEMO data generation...")
        print("🎯 Target: Create rich data for smooth demo experience")
        
        try:
            # Create tables (don't drop to preserve existing data if any)
            db.create_all()
            print("✅ Database tables ready")
            
            # Create data in dependency order
            self.create_users()
            self.create_categories()
            self.create_coupons()
            self.create_courses()
            self.create_modules_and_lessons()
            self.create_contents()
            self.create_enrollments()
            self.create_progress_data()
            self.create_carts_and_items()
            self.create_payments()
            self.create_qa_data()
            
            # Commit all changes
            db.session.commit()
            print("\n🎉 ALL DEMO DATA CREATED SUCCESSFULLY!")
            self.print_demo_summary()
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating demo data: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def create_users(self):
        """Tạo nhiều users để demo đa dạng"""
        print("👥 Creating users for demo...")
        
        # 1. Admin user
        admin = User(
            email='admin@ols.demo',
            password='Demo123!',
            first_name='Admin',
            last_name='System',
            role=UserRole.ADMIN
        )
        admin.is_verified = True
        admin.last_login_at = fake.date_time_between(start_date='-7d', end_date='now')
        self.users.append(admin)
        
        # 2. Instructors - Tạo nhiều giảng viên với background đa dạng
        instructors_data = [
            ('minh.nguyen@ols.demo', 'Nguyễn', 'Văn Minh', 'Chuyên gia Marketing Digital với 10 năm kinh nghiệm'),
            ('hoa.tran@ols.demo', 'Trần', 'Thị Hoa', 'Senior Full Stack Developer, ex-Google'),
            ('nam.le@ols.demo', 'Lê', 'Hoàng Nam', 'Lead UI/UX Designer tại FPT Software'),
            ('trang.pham@ols.demo', 'Phạm', 'Thu Trang', 'Business Consultant & Startup Mentor'),
            ('duc.vo@ols.demo', 'Võ', 'Minh Đức', 'Data Scientist & AI Researcher'),
            ('linh.dao@ols.demo', 'Đào', 'Thùy Linh', 'Digital Marketing Manager'),
            ('quan.bui@ols.demo', 'Bùi', 'Văn Quân', 'DevOps Engineer & Cloud Architect'),
            ('mai.ngo@ols.demo', 'Ngô', 'Thị Mai', 'Product Manager & Growth Hacker'),
        ]
        
        for email, first_name, last_name, bio in instructors_data:
            instructor = User(
                email=email,
                password='Demo123!',
                first_name=first_name,
                last_name=last_name,
                role=UserRole.INSTRUCTOR
            )
            instructor.is_verified = True
            instructor.last_login_at = fake.date_time_between(start_date='-30d', end_date='now')
            self.users.append(instructor)
        
        # 3. Students - Tạo nhiều học viên
        vietnamese_names = [
            ('Nguyễn', 'Văn An'), ('Trần', 'Thị Bình'), ('Lê', 'Hoàng Cường'), 
            ('Phạm', 'Thu Dung'), ('Hoàng', 'Văn Em'), ('Vũ', 'Thị Phượng'),
            ('Đặng', 'Minh Giang'), ('Bùi', 'Thị Hạnh'), ('Đỗ', 'Văn Inh'),
            ('Ngô', 'Thị Kim'), ('Dương', 'Văn Long'), ('Lý', 'Thị Mai'),
            ('Võ', 'Minh Nam'), ('Đinh', 'Thị Oanh'), ('Tôn', 'Văn Phúc'),
            ('Lưu', 'Thị Quỳnh'), ('Trịnh', 'Văn Rực'), ('Chu', 'Thị Sao'),
            ('Phan', 'Văn Tài'), ('Huỳnh', 'Thị Uyên'), ('Cao', 'Văn Việt'),
            ('Đào', 'Thị Xuân'), ('Tạ', 'Văn Yên'), ('Mai', 'Thị Zoan'),
            ('Lâm', 'Văn Bách'), ('Hà', 'Thị Cẩm'), ('Thái', 'Văn Đạt'),
            ('Kiều', 'Thị Ell'), ('Lại', 'Văn Phát'), ('Ông', 'Thị Ghi'),
        ]
        
        for i, (last_name, first_name) in enumerate(vietnamese_names):
            student = User(
                email=f'student{i+1}@demo.com',
                password='Demo123!',
                first_name=first_name,
                last_name=last_name,
                role=UserRole.STUDENT
            )
            student.is_verified = random.choice([True, True, True, False])  # 75% verified
            if student.is_verified:
                student.last_login_at = fake.date_time_between(start_date='-60d', end_date='now')
            self.users.append(student)
        
        # Bulk add users
        db.session.add_all(self.users)
        db.session.flush()
        print(f"   ✅ Created {len(self.users)} users")
        print(f"      - 1 Admin, {len(instructors_data)} Instructors, {len(vietnamese_names)} Students")
    
    def create_categories(self):
        """Tạo categories đa dạng"""
        print("📂 Creating course categories...")
        
        categories_data = [
            ('Lập trình', 'programming', 'Lập trình và phát triển phần mềm', '💻'),
            ('Marketing', 'marketing', 'Marketing số và truyền thông', '📈'),
            ('Thiết kế', 'design', 'Thiết kế đồ họa và UI/UX', '🎨'),
            ('Kinh doanh', 'business', 'Kinh doanh và quản lý', '💼'),
            ('Data Science', 'data-science', 'Khoa học dữ liệu và AI', '📊'),
            ('DevOps', 'devops', 'DevOps và Cloud Computing', '☁️'),
            ('Mobile', 'mobile', 'Phát triển ứng dụng di động', '📱'),
            ('Blockchain', 'blockchain', 'Blockchain và Cryptocurrency', '⛓️'),
        ]
        
        for name, slug, desc, icon in categories_data:
            category = Category(
                name=name,
                slug=slug,
                description=desc,
                icon=icon,
                is_active=True,
                sort_order=len(self.categories) + 1
            )
            self.categories.append(category)
        
        db.session.add_all(self.categories)
        db.session.flush()
        print(f"   ✅ Created {len(self.categories)} categories")
    
    def create_coupons(self):
        """Tạo coupons cho demo"""
        print("🎫 Creating promotional coupons...")
        
        coupons_data = [
            ('WELCOME10', 'Chào mừng học viên mới', CouponType.PERCENTAGE, 10, 50000, None, 1000),
            ('SAVE20', 'Giảm giá 20% toàn bộ khóa học', CouponType.PERCENTAGE, 20, 100000, 300000, 500),
            ('FIXED100K', 'Giảm ngay 100K', CouponType.FIXED_AMOUNT, 100000, 300000, None, 200),
            ('STUDENT15', 'Ưu đãi sinh viên 15%', CouponType.PERCENTAGE, 15, 0, 200000, 2000),
            ('HOLIDAY30', 'Khuyến mãi lễ 30%', CouponType.PERCENTAGE, 30, 500000, 1000000, 100),
            ('EARLYBIRD', 'Early Bird 25%', CouponType.PERCENTAGE, 25, 200000, 500000, 300),
            ('SUMMER50K', 'Khuyến mãi hè', CouponType.FIXED_AMOUNT, 50000, 150000, None, 400),
            ('PREMIUM40', 'Premium member 40%', CouponType.PERCENTAGE, 40, 1000000, 2000000, 50),
        ]
        
        for code, name, coupon_type, value, min_amount, max_discount, usage_limit in coupons_data:
            coupon = Coupon(
                code=code,
                name=name,
                description=f"Mã giảm giá {name.lower()}",
                type=coupon_type,
                value=Decimal(str(value)),
                minimum_amount=Decimal(str(min_amount)),
                maximum_discount=Decimal(str(max_discount)) if max_discount else None,
                usage_limit=usage_limit,
                used_count=random.randint(0, usage_limit // 5),
                is_active=True,
                valid_from=datetime.now() - timedelta(days=30),
                valid_until=datetime.now() + timedelta(days=90)
            )
            self.coupons.append(coupon)
        
        db.session.add_all(self.coupons)
        db.session.flush()
        print(f"   ✅ Created {len(self.coupons)} coupons")
    
    def create_courses(self):
        """Tạo nhiều khóa học đa dạng"""
        print("📚 Creating comprehensive course catalog...")
        
        # Get instructors (excluding admin and students)
        instructors = [u for u in self.users if u.role == UserRole.INSTRUCTOR]
        
        courses_data = [
            # Programming Courses (Lập trình)
            ('Python từ Zero đến Hero', 'python-zero-to-hero', 'programming', 0, 
             'Học lập trình Python từ cơ bản đến nâng cao với dự án thực tế', 'Khóa học Python toàn diện nhất dành cho người mới bắt đầu', 'beginner', True, 0),
            ('JavaScript & React Mastery', 'javascript-react-mastery', 'programming', 1,
             'Thành thạo JavaScript ES6+ và React để phát triển ứng dụng web hiện đại', 'Khóa học JavaScript và React chuyên sâu', 'intermediate', False, 599000),
            ('Full Stack MERN Development', 'full-stack-mern', 'programming', 0,
             'Trở thành Full Stack Developer với MongoDB, Express, React, Node.js', 'Khóa học Full Stack hoàn chỉnh', 'advanced', False, 1299000),
            ('Java Spring Boot Ultimate', 'java-spring-boot', 'programming', 1,
             'Phát triển ứng dụng enterprise với Java Spring Boot', 'Khóa học Java Spring Boot từ cơ bản đến chuyên sâu', 'intermediate', False, 899000),
            ('PHP Laravel cho người mới', 'php-laravel-beginner', 'programming', 0,
             'Học PHP Laravel để phát triển website động', 'Khóa học PHP Laravel dành cho beginners', 'beginner', False, 399000),
            
            # Marketing Courses
            ('Digital Marketing Strategy 2024', 'digital-marketing-strategy', 'marketing', 2,
             'Chiến lược marketing số hiệu quả cho năm 2024', 'Học cách xây dựng chiến lược marketing số thành công', 'beginner', False, 449000),
            ('Social Media Marketing Pro', 'social-media-marketing-pro', 'marketing', 5,
             'Làm chủ marketing trên Facebook, Instagram, TikTok, YouTube', 'Khóa học Social Media Marketing toàn diện', 'intermediate', False, 549000),
            ('Google Ads & Analytics Mastery', 'google-ads-analytics', 'marketing', 2,
             'Tối ưu hóa quảng cáo Google và phân tích dữ liệu chuyên sâu', 'Khóa học Google Ads chuyên nghiệp', 'advanced', False, 699000),
            ('Content Marketing & SEO', 'content-marketing-seo', 'marketing', 5,
             'Tạo content viral và tối ưu SEO top Google', 'Khóa học Content Marketing và SEO', 'intermediate', False, 399000),
            
            # Design Courses (Thiết kế)
            ('UI/UX Design với Figma', 'ui-ux-design-figma', 'design', 3,
             'Thiết kế giao diện và trải nghiệm người dùng chuyên nghiệp với Figma', 'Khóa học UI/UX Design toàn diện', 'beginner', False, 499000),
            ('Adobe Photoshop cho Designer', 'photoshop-for-designer', 'design', 3,
             'Làm chủ Photoshop để thiết kế graphic chuyên nghiệp', 'Khóa học Photoshop từ cơ bản đến nâng cao', 'intermediate', False, 349000),
            ('Illustrator Vector Design', 'illustrator-vector-design', 'design', 3,
             'Thiết kế vector và logo với Adobe Illustrator', 'Khóa học Illustrator chuyên nghiệp', 'intermediate', False, 399000),
            
            # Business Courses (Kinh doanh) 
            ('Khởi nghiệp Startup từ A-Z', 'startup-business-az', 'business', 4,
             'Hướng dẫn khởi nghiệp và xây dựng startup thành công', 'Khóa học khởi nghiệp toàn diện', 'beginner', False, 599000),
            ('Quản lý dự án Agile & Scrum', 'agile-scrum-project-management', 'business', 7,
             'Quản lý dự án hiệu quả với phương pháp Agile và Scrum', 'Khóa học Agile Scrum cho Project Manager', 'intermediate', False, 799000),
            ('Digital Transformation', 'digital-transformation', 'business', 4,
             'Chuyển đổi số cho doanh nghiệp trong kỷ nguyên 4.0', 'Khóa học chuyển đổi số', 'advanced', False, 999000),
            
            # Data Science Courses
            ('Data Analysis với Python', 'data-analysis-python', 'data-science', 1,
             'Phân tích dữ liệu với Python, Pandas, NumPy, Matplotlib', 'Khóa học Data Analysis thực tế', 'intermediate', False, 699000),
            ('Machine Learning cơ bản', 'machine-learning-basics', 'data-science', 6,
             'Học Machine Learning từ cơ bản với Python và Scikit-learn', 'Khóa học Machine Learning dễ hiểu', 'intermediate', False, 899000),
            ('Deep Learning & AI', 'deep-learning-ai', 'data-science', 6,
             'Deep Learning và trí tuệ nhân tạo với TensorFlow', 'Khóa học Deep Learning chuyên sâu', 'advanced', False, 1499000),
            
            # DevOps Courses
            ('Docker & Kubernetes', 'docker-kubernetes', 'devops', 4,
             'Container hóa ứng dụng với Docker và Kubernetes', 'Khóa học DevOps container', 'intermediate', False, 799000),
            ('AWS Cloud Architecture', 'aws-cloud-architecture', 'devops', 4,
             'Thiết kế hệ thống trên AWS Cloud', 'Khóa học AWS chuyên sâu', 'advanced', False, 1199000),
            
            # Mobile Development
            ('React Native Mobile App', 'react-native-mobile', 'mobile', 1,
             'Phát triển ứng dụng di động với React Native', 'Khóa học React Native toàn diện', 'intermediate', False, 899000),
            ('Flutter cho người mới', 'flutter-beginner', 'mobile', 1,
             'Tạo ứng dụng mobile đa nền tảng với Flutter', 'Khóa học Flutter từ cơ bản', 'beginner', False, 699000),
            
            # Blockchain
            ('Blockchain & Smart Contract', 'blockchain-smart-contract', 'blockchain', 6,
             'Phát triển smart contract và DApp trên Ethereum', 'Khóa học Blockchain development', 'advanced', False, 1299000),
        ]
        
        for title, slug, cat_slug, instructor_idx, desc, short_desc, difficulty, is_free, price in courses_data:
            category = next(c for c in self.categories if c.slug == cat_slug)
            instructor = instructors[instructor_idx % len(instructors)]
            
            course = Course(
                title=title,
                slug=slug,
                description=desc,
                short_description=short_desc,
                instructor_id=instructor.id,
                instructor_name=instructor.full_name,
                category_id=category.id,
                difficulty_level=getattr(DifficultyLevel, difficulty.upper()),
                price=Decimal(str(price)),
                is_free=is_free,
                status=CourseStatus.PUBLISHED,
                is_published=True,
                language='vi',
                average_rating=round(random.uniform(4.0, 5.0), 1),
                total_ratings=random.randint(50, 500),
                total_enrollments=random.randint(100, 2000),
                thumbnail_url=f"https://demo.ols.com/thumbnails/{slug}.jpg",
                published_at=fake.date_time_between(start_date='-365d', end_date='-30d')
            )
            
            # Set original price for discount display
            if not is_free and random.choice([True, False]):
                course.original_price = course.price * Decimal('1.4')
            
            self.courses.append(course)
        
        db.session.add_all(self.courses)
        db.session.flush()
        print(f"   ✅ Created {len(self.courses)} courses across {len(self.categories)} categories")
    
    def create_modules_and_lessons(self):
        """Tạo modules và lessons cho mỗi course"""
        print("📖 Creating modules and lessons...")
        
        total_modules = 0
        total_lessons = 0
        
        # Create modules first
        for course in self.courses:
            # Mỗi course có 4-8 modules
            num_modules = random.randint(4, 8)
            
            for module_idx in range(num_modules):
                module = Module(
                    course_id=course.id,
                    title=f"Module {module_idx+1}: {fake.sentence(nb_words=4).replace('.', '')}",
                    description=fake.paragraph(nb_sentences=2),
                    sort_order=module_idx + 1
                )
                self.modules.append(module)
                total_modules += 1
        
        # Add and flush modules first to get IDs
        db.session.add_all(self.modules)
        db.session.flush()
        
        # Now create lessons with proper module_id
        for module in self.modules:
            # Mỗi module có 5-12 lessons
            num_lessons = random.randint(5, 12)
            
            for lesson_idx in range(num_lessons):
                lesson = Lesson(
                    module_id=module.id,
                    title=f"Bài {lesson_idx+1}: {fake.sentence(nb_words=6).replace('.', '')}",
                    description=fake.paragraph(nb_sentences=3),
                    content_type=random.choice(list(ContentType)),
                    duration_minutes=random.randint(15, 120),
                    sort_order=lesson_idx + 1,
                    is_preview=(lesson_idx == 0 or (lesson_idx < 3 and random.choice([True, False])))
                )
                self.lessons.append(lesson)
                total_lessons += 1
        
        # Add lessons
        db.session.add_all(self.lessons)
        db.session.flush()
        
        # Update course statistics
        for course in self.courses:
            course_lessons = [l for l in self.lessons if any(m.course_id == course.id for m in self.modules if m.id == l.module_id)]
            course.total_lessons = len(course_lessons)
            course.duration_hours = sum(l.duration_minutes for l in course_lessons) // 60
        
        print(f"   ✅ Created {total_modules} modules and {total_lessons} lessons")
    
    def create_contents(self):
        """Tạo content chi tiết cho lessons"""
        print("📄 Creating lesson contents...")
        
        total_contents = 0
        
        for lesson in self.lessons:
            # Mỗi lesson có 1-4 contents
            num_contents = random.randint(1, 4)
            
            for content_idx in range(num_contents):
                content = Content(
                    lesson_id=lesson.id,
                    title=f"Phần {content_idx+1}: {fake.sentence(nb_words=5).replace('.', '')}",
                    content_data=fake.text(max_nb_chars=2000),
                    file_url=f"https://demo.ols.com/content/{lesson.id}_{content_idx+1}.mp4" if lesson.content_type == ContentType.VIDEO else None,
                    sort_order=content_idx + 1
                )
                self.contents.append(content)
                total_contents += 1
        
        db.session.add_all(self.contents)
        db.session.flush()
        print(f"   ✅ Created {total_contents} lesson contents")
    
    def create_enrollments(self):
        """Tạo enrollments realistc"""
        print("🎓 Creating student enrollments...")
        
        students = [u for u in self.users if u.role == UserRole.STUDENT]
        
        for student in students:
            # Mỗi student đăng ký 1-6 courses
            num_enrollments = random.randint(1, 6)
            enrolled_courses = random.sample(self.courses, min(num_enrollments, len(self.courses)))
            
            for course in enrolled_courses:
                # Sử dụng constructor đúng của Enrollment model
                enrollment = Enrollment(
                    user_id=student.id,
                    course_id=course.id,
                    full_name=student.full_name,
                    email=student.email,
                    payment_amount=float(course.price)
                )
                
                # Set additional properties after initialization
                enrollment.status = random.choice([EnrollmentStatus.ACTIVE, EnrollmentStatus.ACTIVE, EnrollmentStatus.ENROLLED, EnrollmentStatus.CANCELLED])
                enrollment.access_granted = enrollment.status in [EnrollmentStatus.ACTIVE, EnrollmentStatus.ENROLLED]
                enrollment.enrollment_date = fake.date_time_between(start_date='-180d', end_date='now')
                
                # Update payment status if needed
                if not course.is_free and enrollment.status in [EnrollmentStatus.ACTIVE, EnrollmentStatus.ENROLLED]:
                    enrollment.payment_status = EnrollmentPaymentStatus.COMPLETED
                else:
                    enrollment.payment_status = EnrollmentPaymentStatus.PENDING if course.price > 0 else EnrollmentPaymentStatus.COMPLETED
                
                if enrollment.status == EnrollmentStatus.ENROLLED:
                    enrollment.activation_date = enrollment.enrollment_date + timedelta(minutes=30)
                elif enrollment.status == EnrollmentStatus.ACTIVE:
                    enrollment.activation_date = enrollment.enrollment_date + timedelta(minutes=random.randint(1, 60))
                
                self.enrollments.append(enrollment)
        
        db.session.add_all(self.enrollments)
        db.session.flush()
        print(f"   ✅ Created {len(self.enrollments)} enrollments")
    
    def create_progress_data(self):
        """Tạo progress data realistic"""
        print("📊 Creating learning progress data...")
        
        active_enrollments = [e for e in self.enrollments if e.status in [EnrollmentStatus.ACTIVE, EnrollmentStatus.ENROLLED]]
        
        course_progress_count = 0
        lesson_progress_count = 0
        
        for enrollment in active_enrollments:
            # Get lessons for this course
            course_lessons = [l for l in self.lessons if any(m.course_id == enrollment.course_id for m in self.modules if m.id == l.module_id)]
            total_lessons = len(course_lessons)
            
            if total_lessons == 0:
                continue
            
            # Determine progress based on enrollment status
            if enrollment.status == EnrollmentStatus.ENROLLED:
                # Enrolled students have completed more progress
                completed_lessons = random.randint(int(total_lessons * 0.7), total_lessons)
                completion_percentage = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
            else:
                completed_lessons = random.randint(0, int(total_lessons * 0.8))
                completion_percentage = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
            
            # Create course progress
            course_progress = CourseProgress(
                user_id=enrollment.user_id,
                course_id=enrollment.course_id,
                enrollment_id=enrollment.id,
                total_lessons=total_lessons,
                completed_lessons=completed_lessons,
                completion_percentage=round(completion_percentage, 2),
                total_watch_time_seconds=random.randint(3600, 50000),
                is_completed=(enrollment.status == EnrollmentStatus.ENROLLED and completion_percentage >= 95),
                started_at=enrollment.enrollment_date,
                last_accessed_at=fake.date_time_between(start_date=enrollment.enrollment_date, end_date='now')
            )
            
            if course_progress.is_completed:
                course_progress.completed_at = course_progress.last_accessed_at
            
            self.course_progress.append(course_progress)
            course_progress_count += 1
            
            # Create lesson progress for completed/started lessons
            num_lessons_with_progress = min(completed_lessons + random.randint(1, 3), total_lessons)
            
            for lesson in random.sample(course_lessons, min(num_lessons_with_progress, len(course_lessons))):
                completion_pct = random.uniform(75, 100) if random.choice([True, False]) else random.uniform(20, 90)
                
                lesson_progress = LessonProgress(
                    user_id=enrollment.user_id,
                    lesson_id=lesson.id,
                    course_id=enrollment.course_id,
                    status=ProgressStatus.COMPLETED if completion_pct >= 90 else ProgressStatus.IN_PROGRESS,
                    watch_time_seconds=random.randint(lesson.duration_minutes * 30, lesson.duration_minutes * 70),
                    completion_percentage=completion_pct,
                    is_completed=completion_pct >= 90,
                    started_at=fake.date_time_between(start_date=enrollment.enrollment_date, end_date='now')
                )
                
                if lesson_progress.is_completed:
                    lesson_progress.completed_at = lesson_progress.started_at + timedelta(minutes=lesson.duration_minutes)
                
                lesson_progress.last_accessed_at = lesson_progress.completed_at or lesson_progress.started_at
                self.lesson_progress.append(lesson_progress)
                lesson_progress_count += 1
        
        db.session.add_all(self.course_progress)
        db.session.add_all(self.lesson_progress)
        db.session.flush()
        print(f"   ✅ Created {course_progress_count} course progress and {lesson_progress_count} lesson progress")
    
    def create_carts_and_items(self):
        """Tạo shopping carts và items"""
        print("🛒 Creating shopping carts...")
        
        students = [u for u in self.users if u.role == UserRole.STUDENT]
        
        # Student carts
        for student in students[:15]:  # 15 students have carts
            cart = Cart(
                user_id=student.id,
                status=random.choice([CartStatus.ACTIVE, CartStatus.ACTIVE, CartStatus.ABANDONED]),
                coupon_code=random.choice(self.coupons).code if random.choice([True, False]) else None
            )
            self.carts.append(cart)
        
        # Guest carts
        for i in range(5):
            cart = Cart(
                session_id=f"guest_session_{fake.uuid4()[:8]}",
                status=CartStatus.ACTIVE
            )
            self.carts.append(cart)
        
        db.session.add_all(self.carts)
        db.session.flush()
        
        # Create cart items
        total_cart_items = 0
        for cart in self.carts:
            num_items = random.randint(1, 4)
            cart_courses = random.sample(self.courses, min(num_items, len(self.courses)))
            
            total_amount = Decimal('0')
            for course in cart_courses:
                cart_item = CartItem(
                    cart_id=cart.id,
                    course_id=course.id,
                    course_title=course.title,
                    course_instructor=course.instructor_name,
                    price=course.price,
                    original_price=course.original_price,
                    added_at=fake.date_time_between(start_date='-30d', end_date='now')
                )
                total_amount += course.price
                self.cart_items.append(cart_item)
                total_cart_items += 1
            
            # Update cart totals
            cart.item_count = len(cart_courses)
            cart.total_amount = total_amount
            cart.final_amount = total_amount
        
        db.session.add_all(self.cart_items)
        db.session.flush()
        print(f"   ✅ Created {len(self.carts)} carts with {total_cart_items} items")
    
    def create_payments(self):
        """Tạo payment records"""
        print("💳 Creating payment records...")
        
        paid_enrollments = [e for e in self.enrollments if e.payment_status == EnrollmentPaymentStatus.COMPLETED]
        
        for enrollment in paid_enrollments:
            payment = Payment(
                enrollment_id=enrollment.id,
                user_id=enrollment.user_id,
                payment_method=random.choice(list(PaymentMethod)),
                status=PaymentStatus.COMPLETED,
                amount=enrollment.final_amount,
                currency='VND',
                transaction_id=f"TXN_{fake.uuid4()[:8].upper()}",
                processed_at=enrollment.enrollment_date + timedelta(minutes=random.randint(1, 30))
            )
            self.payments.append(payment)
        
        db.session.add_all(self.payments)
        db.session.flush()
        print(f"   ✅ Created {len(self.payments)} payment records")
    
    def create_qa_data(self):
        """Tạo Q&A data"""
        print("❓ Creating Q&A discussions...")
        
        students = [u for u in self.users if u.role == UserRole.STUDENT]
        instructors = [u for u in self.users if u.role == UserRole.INSTRUCTOR]
        
        # Create questions
        questions = []
        question_topics = [
            "Làm sao để cài đặt môi trường development?",
            "Có thể giải thích thêm về phần này không?", 
            "Code ở bài này bị lỗi, ai có thể giúp không?",
            "Có tài liệu tham khảo thêm không?",
            "Cách debug lỗi này như thế nào?",
            "Có thể áp dụng kiến thức này vào dự án thực tế không?",
            "Sự khác biệt giữa X và Y là gì?",
            "Best practice cho vấn đề này là gì?",
            "Có course nào tiếp theo để học không?",
            "Làm sao để optimize performance?",
            "Có cần học thêm framework khác không?",
            "Roadmap học tập như thế nào?",
            "Cách tìm việc với skill này?",
            "Project nào để practice tốt nhất?",
            "Tool nào hỗ trợ development tốt?",
        ]
        
        for i in range(50):
            question = Question(
                user_id=random.choice(students).id,
                title=f"{random.choice(question_topics)} - {fake.sentence(nb_words=3)}"
            )
            questions.append(question)
        
        db.session.add_all(questions)
        db.session.flush()
        
        # Create answers
        answers = []
        for question in questions:
            if random.choice([True, True, False]):  # 66% questions have answers
                answer = Answer(
                    question_id=question.id,
                    user_id=random.choice(instructors + students).id
                )
                answers.append(answer)
                
                # Some questions have multiple answers
                if random.choice([True, False]):
                    answer2 = Answer(
                        question_id=question.id,
                        user_id=random.choice(instructors + students).id
                    )
                    answers.append(answer2)
        
        db.session.add_all(answers)
        db.session.flush()
        print(f"   ✅ Created {len(questions)} questions and {len(answers)} answers")
    
    def print_demo_summary(self):
        """In summary cho demo"""
        print("\n" + "="*60)
        print("🎉 DEMO DATA GENERATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"👥 USERS: {len(self.users)} total")
        print(f"   - 1 Admin")
        print(f"   - {len([u for u in self.users if u.role == UserRole.INSTRUCTOR])} Instructors")
        print(f"   - {len([u for u in self.users if u.role == UserRole.STUDENT])} Students")
        print(f"📂 CATEGORIES: {len(self.categories)}")
        print(f"📚 COURSES: {len(self.courses)}")
        print(f"📖 MODULES: {len(self.modules)}")
        print(f"📝 LESSONS: {len(self.lessons)}")
        print(f"📄 CONTENTS: {len(self.contents)}")
        print(f"🎫 COUPONS: {len(self.coupons)}")
        print(f"🎓 ENROLLMENTS: {len(self.enrollments)}")
        print(f"🛒 CARTS: {len(self.carts)}")
        print(f"🛍️ CART ITEMS: {len(self.cart_items)}")
        print(f"💳 PAYMENTS: {len(self.payments)}")
        print(f"📊 COURSE PROGRESS: {len(self.course_progress)}")
        print(f"📈 LESSON PROGRESS: {len(self.lesson_progress)}")
        
        print(f"\n🎯 DEMO ACCOUNTS:")
        print(f"Admin: admin@ols.demo / Demo123!")
        print(f"Instructor: minh.nguyen@ols.demo / Demo123!")
        print(f"Student: student1@demo.com / Demo123!")
        
        print(f"\n🧪 SAMPLE API TESTS:")
        print(f"GET /api/courses/digital-marketing-strategy/lessons")
        print(f"GET /api/courses/python-zero-to-hero/lessons")
        print(f"GET /api/courses/javascript-react-mastery/lessons/1")
        
        print(f"\n🎊 READY FOR SMOOTH DEMO!")


def main():
    """Main function"""
    app = create_app()
    
    with app.app_context():
        generator = DemoDataGenerator()
        generator.generate_all_data()


if __name__ == '__main__':
    main()
