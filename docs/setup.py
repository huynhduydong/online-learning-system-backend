"""
Quick Setup Script cho Online Learning System
Tự động setup toàn bộ development environment

Usage:
    python setup.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description=""):
    """Run shell command và hiển thị kết quả"""
    if description:
        print(f"🔄 {description}...")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"   {e.stderr.strip()}")
        return False


def check_python_version():
    """Kiểm tra Python version"""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_mysql():
    """Kiểm tra MySQL installation"""
    print("🐬 Checking MySQL...")
    
    try:
        result = subprocess.run("mysql --version", shell=True, 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
            return True
        else:
            print("❌ MySQL not found")
            return False
    except:
        print("❌ MySQL not found")
        return False


def setup_virtual_environment():
    """Setup virtual environment"""
    print("📦 Setting up virtual environment...")
    
    if os.path.exists('venv'):
        print("   Virtual environment already exists")
        return True
    
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
    
    print("✅ Virtual environment created")
    return True


def install_dependencies():
    """Install Python dependencies"""
    print("📚 Installing dependencies...")
    
    # Determine pip command based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        pip_cmd = "venv/bin/pip"
    
    commands = [
        f"{pip_cmd} install --upgrade pip",
        f"{pip_cmd} install -r requirements.txt"
    ]
    
    for cmd in commands:
        if not run_command(cmd):
            return False
    
    print("✅ Dependencies installed")
    return True


def setup_environment_file():
    """Setup .env file"""
    print("⚙️  Setting up environment file...")
    
    if os.path.exists('.env'):
        print("   .env file already exists")
        return True
    
    if os.path.exists('.env.example'):
        shutil.copy('.env.example', '.env')
        print("✅ .env file created from template")
        print("⚠️  Please update .env with your database credentials!")
        return True
    else:
        print("❌ .env.example not found")
        return False


def create_upload_directories():
    """Tạo upload directories"""
    print("📁 Creating upload directories...")
    
    directories = [
        'uploads',
        'uploads/avatars',
        'uploads/courses',
        'uploads/content'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Upload directories created")
    return True


def main():
    """Main setup function"""
    print("🚀 Online Learning System - Quick Setup")
    print("="*50)
    
    # Step 1: Check prerequisites
    if not check_python_version():
        print("\n❌ Setup failed: Python version requirement not met")
        return False
    
    if not check_mysql():
        print("\n⚠️  MySQL not detected. Please install MySQL first:")
        print("   - Windows: https://dev.mysql.com/downloads/installer/")
        print("   - macOS: brew install mysql")
        print("   - Linux: sudo apt install mysql-server")
        return False
    
    # Step 2: Setup virtual environment
    if not setup_virtual_environment():
        print("\n❌ Setup failed: Could not create virtual environment")
        return False
    
    # Step 3: Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed: Could not install dependencies")
        return False
    
    # Step 4: Setup environment file
    if not setup_environment_file():
        print("\n❌ Setup failed: Could not setup environment file")
        return False
    
    # Step 5: Create directories
    if not create_upload_directories():
        print("\n❌ Setup failed: Could not create directories")
        return False
    
    # Success message
    print("\n" + "="*50)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("="*50)
    
    print("\n📋 NEXT STEPS:")
    print("1. Update .env file with your database credentials")
    print("2. Create MySQL database (see database_setup.md)")
    print("3. Test database connection:")
    print("   python scripts/test_connection.py")
    print("4. Initialize database with mock data:")
    print("   python scripts/init_database.py")
    print("5. Run the application:")
    print("   python app.py")
    
    print("\n📖 For detailed instructions, see README.md")
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)