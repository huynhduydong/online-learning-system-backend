"""
Database Reset Script
Xóa tất cả data và tạo lại từ đầu

Usage:
    python scripts/reset_database.py
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db


def reset_database():
    """Reset database - drop all tables và tạo lại"""
    print("⚠️  RESETTING DATABASE - This will delete all data!")
    
    # Confirm action
    confirm = input("Are you sure? Type 'yes' to continue: ")
    if confirm.lower() != 'yes':
        print("❌ Reset cancelled")
        return False
    
    app = create_app('development')
    
    with app.app_context():
        try:
            print("🗑️  Dropping all tables...")
            db.drop_all()
            
            print("🔨 Creating fresh tables...")
            db.create_all()
            
            print("✅ Database reset successfully!")
            print("💡 Run 'python scripts/init_database.py' to add mock data")
            
            return True
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            return False


if __name__ == '__main__':
    reset_database()