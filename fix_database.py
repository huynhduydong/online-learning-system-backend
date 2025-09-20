"""
Simple script to add missing columns to users table
"""

import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app import create_app, db
from sqlalchemy import text

def fix_database():
    """Add missing columns to users table"""
    print("🔧 Fixing database schema...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                # Check if columns already exist
                result = connection.execute(text("DESCRIBE users"))
                columns = [row[0] for row in result]
                
                print(f"📋 Current columns: {columns}")
                
                # Add confirmation_token if not exists
                if 'confirmation_token' not in columns:
                    print("➕ Adding confirmation_token column...")
                    connection.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN confirmation_token VARCHAR(255) NULL
                    """))
                    print("✅ confirmation_token added")
                else:
                    print("✅ confirmation_token already exists")
                
                # Add confirmed_at if not exists
                if 'confirmed_at' not in columns:
                    print("➕ Adding confirmed_at column...")
                    connection.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN confirmed_at DATETIME NULL
                    """))
                    print("✅ confirmed_at added")
                else:
                    print("✅ confirmed_at already exists")
                
                connection.commit()
            
            print("🎉 Database schema fixed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == '__main__':
    fix_database()