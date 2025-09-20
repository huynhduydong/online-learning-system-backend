"""
Database Connection Test Script
Kiểm tra kết nối database trước khi init

Usage:
    python scripts/test_connection.py
"""

import sys
import os
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mysql_connection():
    """Test raw MySQL connection"""
    print("🔌 Testing MySQL connection...")
    
    try:
        # Parse DATABASE_URL
        database_url = os.getenv('DATABASE_URL', '')
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False
        
        # Extract connection info from URL
        # Format: mysql+pymysql://user:password@host/database
        if database_url.startswith('mysql+pymysql://'):
            url_part = database_url.replace('mysql+pymysql://', '')
            
            # Split user:password@host/database
            if '@' in url_part:
                auth_part, host_db_part = url_part.split('@', 1)
                user, password = auth_part.split(':', 1)
                
                if '/' in host_db_part:
                    host, database = host_db_part.split('/', 1)
                else:
                    host = host_db_part
                    database = ''
            else:
                print("❌ Invalid DATABASE_URL format")
                return False
        else:
            print("❌ DATABASE_URL must start with mysql+pymysql://")
            return False
        
        # Test connection
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        # Test query
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL connection successful!")
            print(f"   MySQL Version: {version[0]}")
            print(f"   Host: {host}")
            print(f"   Database: {database}")
            print(f"   User: {user}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return False


def test_flask_app_connection():
    """Test Flask app database connection"""
    print("\n🌶️  Testing Flask app connection...")
    
    try:
        # Add parent directory to path
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from app import create_app, db
        
        app = create_app('development')
        
        with app.app_context():
            # Test database connection
            with db.engine.connect() as connection:
                connection.execute(db.text('SELECT 1'))
            print("✅ Flask app database connection successful!")
            
            # Show current tables
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if tables:
                print(f"📋 Existing tables: {', '.join(tables)}")
            else:
                print("📋 No tables found (database is empty)")
            
            return True
            
    except Exception as e:
        print(f"❌ Flask app connection failed: {e}")
        return False


def main():
    """Main test function"""
    print("🧪 Database Connection Test")
    print("="*40)
    
    # Test 1: Raw MySQL connection
    mysql_ok = test_mysql_connection()
    
    # Test 2: Flask app connection
    flask_ok = test_flask_app_connection()
    
    print("\n" + "="*40)
    print("📊 TEST RESULTS:")
    print(f"   MySQL Connection: {'✅ PASS' if mysql_ok else '❌ FAIL'}")
    print(f"   Flask App Connection: {'✅ PASS' if flask_ok else '❌ FAIL'}")
    
    if mysql_ok and flask_ok:
        print("\n🎉 All tests passed! Ready to initialize database.")
        print("💡 Run: python scripts/init_database.py")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
        print("💡 Check your .env file and database setup.")
    
    return mysql_ok and flask_ok


if __name__ == '__main__':
    main()