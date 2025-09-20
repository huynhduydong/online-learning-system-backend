# Database Setup Guide

## 1. Cài đặt MySQL

### Windows:
1. Download MySQL Installer từ https://dev.mysql.com/downloads/installer/
2. Chọn "MySQL Installer for Windows"
3. Chạy installer và chọn "Developer Default"
4. Thiết lập root password (nhớ password này!)

### macOS:
```bash
# Sử dụng Homebrew
brew install mysql
brew services start mysql

# Hoặc download từ MySQL website
```

### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

## 2. Tạo Database và User

### Bước 1: Kết nối MySQL
```bash
mysql -u root -p
# Nhập password root bạn đã thiết lập
```

### Bước 2: Tạo Database
```sql
-- Tạo database cho development
CREATE DATABASE online_learning_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Tạo database cho testing
CREATE DATABASE online_learning_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Tạo user riêng cho application
CREATE USER 'ols_user'@'localhost' IDENTIFIED BY 'ols_password_2024';

-- Cấp quyền cho user
GRANT ALL PRIVILEGES ON online_learning_dev.* TO 'ols_user'@'localhost';
GRANT ALL PRIVILEGES ON online_learning_test.* TO 'ols_user'@'localhost';

-- Refresh privileges
FLUSH PRIVILEGES;

-- Kiểm tra databases đã tạo
SHOW DATABASES;

-- Thoát MySQL
EXIT;
```

### Bước 3: Test kết nối
```bash
mysql -u ols_user -p online_learning_dev
# Nhập password: ols_password_2024
```

## 3. Cấu hình Environment

Tạo file `.env` từ template:
```bash
cp .env.example .env
```

Cập nhật `.env` với thông tin database:
```
DATABASE_URL=mysql+pymysql://ols_user:ols_password_2024@localhost/online_learning_dev
```

## 4. Kiểm tra kết nối Python

Test script:
```python
import pymysql

try:
    connection = pymysql.connect(
        host='localhost',
        user='ols_user',
        password='ols_password_2024',
        database='online_learning_dev'
    )
    print("✅ Database connection successful!")
    connection.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
```