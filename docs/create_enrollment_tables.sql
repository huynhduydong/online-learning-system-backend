
-- =====================================================================
CREATE TABLE enrollments (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    
    -- Enrollment details
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    
    -- Status tracking
    status ENUM('pending', 'payment_pending', 'enrolled', 'activating', 'active', 'cancelled') 
           NOT NULL DEFAULT 'pending',
    payment_status ENUM('pending', 'completed', 'failed', 'cancelled') 
                   NOT NULL DEFAULT 'pending',
    
    -- Financial information
    payment_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount_applied DECIMAL(10,2) DEFAULT 0.00,
    discount_code VARCHAR(50) NULL,
    
    -- Access control
    access_granted BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    enrollment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activation_date DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Retry mechanism for activation
    activation_attempts INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at DATETIME NULL,
    
    -- Foreign key constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicate enrollments
    UNIQUE KEY unique_user_course_enrollment (user_id, course_id),
    
    -- Indexes for performance
    INDEX idx_enrollments_user_id (user_id),
    INDEX idx_enrollments_course_id (course_id),
    INDEX idx_enrollments_status (status),
    INDEX idx_enrollments_payment_status (payment_status),
    INDEX idx_enrollments_email (email),
    INDEX idx_enrollments_enrollment_date (enrollment_date)
);

-- =====================================================================
-- PAYMENTS TABLE
-- =====================================================================
CREATE TABLE payments (
    id VARCHAR(36) PRIMARY KEY,
    
    -- Foreign keys
    enrollment_id VARCHAR(36) NOT NULL,
    user_id INTEGER NOT NULL,
    
    -- Payment information
    payment_method ENUM('credit_card', 'paypal', 'bank_transfer') NOT NULL,
    status ENUM('pending', 'completed', 'failed', 'cancelled', 'refunded') 
           NOT NULL DEFAULT 'pending',
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'VND',
    
    -- Transaction tracking
    transaction_id VARCHAR(255) NULL,
    gateway_response TEXT NULL,
    payment_gateway VARCHAR(50) NULL,
    
    -- Payment details (stored securely - minimal data only)
    last_four_digits VARCHAR(4) NULL,
    card_holder_name VARCHAR(255) NULL,
    paypal_email VARCHAR(255) NULL,
    bank_account_last_four VARCHAR(4) NULL,
    bank_code VARCHAR(10) NULL,
    
    -- Error handling
    error_code VARCHAR(50) NULL,
    error_message TEXT NULL,
    
    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_payments_enrollment_id (enrollment_id),
    INDEX idx_payments_user_id (user_id),
    INDEX idx_payments_status (status),
    INDEX idx_payments_transaction_id (transaction_id),
    INDEX idx_payments_created_at (created_at)
);

-- =====================================================================
-- TRANSACTIONS TABLE
-- =====================================================================
CREATE TABLE  transactions (
    id VARCHAR(36) PRIMARY KEY,
    payment_id VARCHAR(36) NOT NULL,
    
    -- Transaction details
    transaction_type VARCHAR(50) NOT NULL,
    external_transaction_id VARCHAR(255) NULL,
    gateway_reference VARCHAR(255) NULL,
    
    -- Financial details
    amount DECIMAL(10,2) NOT NULL,
    fee_amount DECIMAL(10,2) DEFAULT 0.00,
    net_amount DECIMAL(10,2) NOT NULL,
    
    -- Status and metadata
    status VARCHAR(50) NOT NULL,
    gateway_response TEXT NULL,
    
    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME NULL,
    
    -- Foreign key constraints
    FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_transactions_payment_id (payment_id),
    INDEX idx_transactions_status (status),
    INDEX idx_transactions_created_at (created_at)
);

-- =====================================================================
-- COUPON_USAGE TABLE ()
-- =====================================================================
CREATE TABLE  coupon_usage (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    
    -- Foreign keys
    coupon_id INTEGER NOT NULL,
    user_id INTEGER NULL,
    cart_id INTEGER NULL,
    
    -- Usage details
    order_amount DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) NOT NULL,
    session_id VARCHAR(255) NULL,
    
    -- Timestamp
    used_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (coupon_id) REFERENCES coupons(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (cart_id) REFERENCES carts(id) ON DELETE SET NULL,
    
    -- Indexes
    INDEX idx_coupon_usage_coupon_id (coupon_id),
    INDEX idx_coupon_usage_user_id (user_id),
    INDEX idx_coupon_usage_used_at (used_at)
);

-- =====================================================================
-- INSERT SAMPLE DATA (Optional - for testing)
-- =====================================================================

-- Sample discount codes (if coupons table exists)
INSERT IGNORE INTO coupons (code, name, type, value, minimum_order_amount, valid_from, valid_until, created_at) VALUES
('WELCOME10', 'Welcome 10% Discount', 'percentage', 10.00, 0.00, NOW(), DATE_ADD(NOW(), INTERVAL 1 YEAR), NOW()),
('SAVE50K', 'Save 50,000 VND', 'fixed_amount', 50000.00, 100000.00, NOW(), DATE_ADD(NOW(), INTERVAL 6 MONTH), NOW()),
('STUDENT20', 'Student 20% Discount', 'percentage', 20.00, 0.00, NOW(), DATE_ADD(NOW(), INTERVAL 1 YEAR), NOW());

-- =====================================================================
-- VERIFICATION QUERIES
-- =====================================================================

-- Check if tables were created successfully
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    DATA_LENGTH,
    INDEX_LENGTH
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME IN ('enrollments', 'payments', 'transactions', 'coupon_usage')
ORDER BY TABLE_NAME;

-- Show table structures
-- DESCRIBE enrollments;
-- DESCRIBE payments;
-- DESCRIBE transactions;

-- =====================================================================
-- CLEANUP SCRIPT (Uncomment if you need to remove tables)
-- =====================================================================
/*
-- WARNING: This will delete all data!
-- USE WITH CAUTION!

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS coupon_usage;
DROP TABLE IF EXISTS enrollments;
*/

-- =====================================================================
-- NOTES:
-- =====================================================================
-- 1. All tables use InnoDB engine by default
-- 2. UUIDs are stored as VARCHAR(36) for better compatibility
-- 3. Foreign key constraints ensure data integrity
-- 4. Indexes are added for common query patterns
-- 5. ENUM values match the Python model definitions
-- 6. Timestamps use DATETIME for better precision
-- 7. ON UPDATE CURRENT_TIMESTAMP for automatic update tracking
-- =====================================================================
