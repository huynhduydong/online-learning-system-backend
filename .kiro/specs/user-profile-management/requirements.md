# Requirements Document

## Introduction

The User Profile Management feature enables logged-in users to view and update their personal information, including profile details and avatar images. This feature ensures users can maintain current and accurate personal information while providing a personalized experience through profile customization.

## Requirements

### Requirement 1: Profile Information Viewing

**User Story:** As a logged-in user, I want to view my profile information, so that I can see my current personal details and account status.

#### Acceptance Criteria

1. WHEN I am logged in and access the profile page THEN the system SHALL display my current profile information including name, email, profile image, and join date
2. WHEN I view my profile THEN the system SHALL show my enrollment statistics including total enrollments and completed courses
3. WHEN I access my profile THEN the system SHALL display my account creation date in a user-friendly format
4. WHEN my profile loads THEN the system SHALL show my current avatar image or a default placeholder if none is set
5. IF I have a profile image THEN the system SHALL display it at 200x200px resolution

### Requirement 2: Profile Information Updates

**User Story:** As a logged-in user, I want to update my name and profile information, so that I can keep my personal information current and accurate.

#### Acceptance Criteria

1. WHEN I want to update my first name THEN the system SHALL allow me to modify it and save the changes
2. WHEN I want to update my last name THEN the system SHALL allow me to modify it and save the changes
3. WHEN I successfully update my profile THEN the system SHALL display a success message "Thông tin profile đã được cập nhật thành công"
4. WHEN I try to update my email THEN the system SHALL NOT allow this change as email cannot be modified after account creation
5. WHEN I submit profile updates THEN the system SHALL validate that names are at least 2 characters long
6. WHEN profile changes are made THEN the system SHALL log the changes for audit tracking

### Requirement 3: Avatar Image Upload

**User Story:** As a logged-in user, I want to upload and update my profile picture, so that I can personalize my account and be easily recognized by others.

#### Acceptance Criteria

1. WHEN I upload an avatar image THEN the system SHALL accept JPG, PNG, and GIF file formats
2. WHEN I try to upload a file larger than 2MB THEN the system SHALL display error message "File quá lớn, tối đa 2MB"
3. WHEN I upload an invalid file format THEN the system SHALL display error message "Invalid file type. Only JPG, PNG, GIF files are allowed"
4. WHEN I successfully upload an avatar THEN the system SHALL resize it to exactly 200x200px while maintaining aspect ratio
5. WHEN I upload a new avatar THEN the system SHALL replace my previous avatar image
6. WHEN avatar upload is successful THEN the system SHALL display success message "Avatar đã được cập nhật thành công"
7. WHEN I upload an avatar THEN the system SHALL store it securely in the uploads/avatars directory
8. WHEN avatar processing fails THEN the system SHALL remove the uploaded file and display an appropriate error message

### Requirement 4: Profile Security and Validation

**User Story:** As a system administrator, I want profile updates to be secure and validated, so that data integrity is maintained and unauthorized changes are prevented.

#### Acceptance Criteria

1. WHEN a user attempts to access profile endpoints THEN the system SHALL require valid JWT authentication
2. WHEN profile data is submitted THEN the system SHALL validate all input fields before processing
3. WHEN file uploads occur THEN the system SHALL check file size limits before processing
4. WHEN images are uploaded THEN the system SHALL process them securely to prevent malicious file execution
5. WHEN profile changes are made THEN the system SHALL log the changes with user ID and timestamp
6. WHEN database operations fail THEN the system SHALL rollback changes and return appropriate error messages
7. IF a user tries to access another user's profile THEN the system SHALL deny access and return authorization error