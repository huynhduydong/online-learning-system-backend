"""
Database Migration: Add Email Confirmation Fields
For User Story OLS-US-001: User Registration

Adds confirmation_token and confirmed_at fields to users table
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import create_app, db
from sqlalchemy import text

def upgrade():
    """Add email confirmation fields to users table"""
    print("🔄 Adding email confirmation fields to users table...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Add confirmation_token column
            with db.engine.connect() as connection:
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN confirmation_token VARCHAR(255) NULL
                """))
                
                # Add confirmed_at column
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN confirmed_at DATETIME NULL
                """))
                
                connection.commit()
            
            print("✅ Email confirmation fields added successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False

def downgrade():
    """Remove email confirmation fields from users table"""
    print("🔄 Removing email confirmation fields from users table...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Remove confirmation_token column
            with db.engine.connect() as connection:
                connection.execute(text("""
                    ALTER TABLE users 
                    DROP COLUMN confirmation_token
                """))
                
                # Remove confirmed_at column
                connection.execute(text("""
                    ALTER TABLE users 
                    DROP COLUMN confirmed_at
                """))
                
                connection.commit()
            
            print("✅ Email confirmation fields removed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Downgrade failed: {e}")
            return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        downgrade()
    else:
        upgrade()