# User Profile & Password Management Feature

## Overview

This feature allows authenticated users to view and update their profile information and change their passwords securely. The implementation includes comprehensive backend API routes, frontend UI, and extensive test coverage.

## Features Implemented

### 1. Backend (FastAPI)

#### API Endpoints

- **GET `/users/me`** - Retrieve current user's profile
  - Returns: User profile information (username, email, first_name, last_name, account status)
  - Requires: Authentication

- **PUT `/users/me/profile`** - Update profile information
  - Accepts: first_name, last_name, email, username (all optional)
  - Validates: Email uniqueness, username uniqueness, email format, username length
  - Returns: Updated user profile
  - Requires: Authentication

- **PUT `/users/me/password`** - Change password
  - Accepts: current_password, new_password, confirm_new_password
  - Validates: Current password correctness, password strength, password match
  - Returns: Success message
  - Requires: Authentication
  - Security: Auto-logout after password change (frontend)

#### Data Validation (Pydantic Schemas)

**UserUpdate Schema** ([app/schemas/user.py](app/schemas/user.py))
- All fields optional for partial updates
- Email format validation
- Username length validation (3-50 characters)
- Name length validation (1-50 characters)

**PasswordUpdate Schema** ([app/schemas/user.py](app/schemas/user.py))
- Current password required
- New password strength requirements:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
- New password must differ from current password
- Password confirmation must match new password

### 2. Frontend (HTML/JavaScript)

#### Profile Page ([templates/profile.html](templates/profile.html))

**Features:**
- Clean, responsive design using TailwindCSS
- Breadcrumb navigation
- Two main sections:
  1. Profile Information Form
  2. Password Change Form

**Profile Information Form:**
- Pre-populated with current user data
- Real-time validation
- Update all or individual fields
- Shows account status and member since date

**Password Change Form:**
- Password visibility toggle
- Client-side validation
- Password strength requirements displayed
- Confirmation matching

**User Experience:**
- Loading states on button clicks
- Success/error alert messages
- Auto-dismiss alerts (5 seconds)
- Scroll to top on alerts
- Form reset after password change
- Auto-logout after password change (3 seconds)

#### Navigation
- Profile link added to navigation bar
- Accessible from any authenticated page

### 3. Testing

#### Unit Tests ([tests/unit/test_user_profile.py](tests/unit/test_user_profile.py))

**Password Schema Tests:**
- Valid password update
- Password mismatch detection
- Same as current password detection
- Password strength validation (no uppercase, lowercase, digit, special char)
- Password too short

**User Update Schema Tests:**
- All fields update
- Partial fields update
- Empty optional fields
- Invalid email format
- Username too short/long
- Empty name fields

**Password Logic Tests:**
- Password hashing produces different hashes
- Password verification (correct/incorrect)
- User update method
- Complete password change flow

**Total: 15 unit tests**

#### Integration Tests ([tests/integration/test_profile_endpoints.py](tests/integration/test_profile_endpoints.py))

**Get Profile Tests:**
- Successful profile retrieval
- No authentication fails
- Invalid token fails

**Update Profile Tests:**
- Update all fields
- Update partial fields
- Email only update
- Username only update
- No fields error
- Duplicate email/username detection
- Same email allowed (own email)
- Invalid email format
- Username too short
- No authentication fails

**Change Password Tests:**
- Successful password change
- Wrong current password
- Password mismatch
- Same as current password
- Weak password
- No uppercase/special character
- No authentication
- Timestamp updates

**Workflow Tests:**
- Update then login with new username
- Update email then verify profile

**Total: 24 integration tests**

#### E2E Tests ([tests/e2e/test_profile_flow.py](tests/e2e/test_profile_flow.py))

**Profile Access Tests:**
- Access profile page
- Page shows user data
- Redirect without login
- Profile link in navbar

**Profile Update Tests:**
- Update profile success
- Update username
- Update email
- Invalid email format
- Duplicate username

**Password Change Tests:**
- Change password success
- Wrong current password
- Password mismatch
- Weak password
- Same as current password

**Complete Workflow Tests:**
- Login → Profile → Update → Logout → Login
- Login → Change Password → Logout → Re-login with new password
- Update username → Login with new username
- Navigate from dashboard to profile and back

**UI/UX Tests:**
- Password visibility toggle
- Form validation
- Error message display and dismiss

**Total: 19 E2E tests**

## Security Features

1. **Password Hashing**: Using bcrypt for secure password storage
2. **JWT Authentication**: All profile endpoints require valid JWT tokens
3. **Password Strength Validation**: Both client-side and server-side
4. **Current Password Verification**: Required before password change
5. **Auto-logout**: After password change for security
6. **Unique Constraints**: Email and username uniqueness enforced

## Installation & Running

### Prerequisites
- Python 3.12+
- PostgreSQL database
- Node.js (for frontend assets)

### Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start database (if using Docker)
docker-compose up -d

# Run the application
uvicorn app.main:app --reload
```

### Running Tests

```bash
# Run all unit tests
pytest tests/unit/test_user_profile.py -v

# Run all integration tests
pytest tests/integration/test_profile_endpoints.py -v

# Run all E2E tests
pytest tests/e2e/test_profile_flow.py -v --headed

# Run with coverage
pytest tests/unit/test_user_profile.py tests/integration/test_profile_endpoints.py --cov=app --cov-report=html
```

## Usage

### For Users

1. **Access Profile:**
   - Log in to the application
   - Click "Profile" button in navigation bar
   - Or navigate to `/profile`

2. **Update Profile:**
   - Edit any fields (first name, last name, username, email)
   - Click "Update Profile"
   - See success message

3. **Change Password:**
   - Enter current password
   - Enter new password (must meet strength requirements)
   - Confirm new password
   - Click "Change Password"
   - You'll be logged out automatically
   - Log in with new password

### For Developers

1. **Adding New Profile Fields:**
   - Update `UserUpdate` schema in [app/schemas/user.py](app/schemas/user.py)
   - Update profile endpoint in [app/main.py](app/main.py)
   - Update HTML form in [templates/profile.html](templates/profile.html)
   - Add JavaScript handlers for new fields
   - Write tests

2. **Customizing Password Requirements:**
   - Modify `validate_password_strength` in `PasswordUpdate` schema
   - Update client-side validation in profile.html
   - Update help text in UI

## API Examples

### Get Current User Profile

```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Profile

```bash
curl -X PUT "http://localhost:8000/users/me/profile" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
  }'
```

### Change Password

```bash
curl -X PUT "http://localhost:8000/users/me/password" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "OldPassword123!",
    "new_password": "NewPassword456!",
    "confirm_new_password": "NewPassword456!"
  }'
```

## Files Modified/Created

### Backend
- [app/main.py](app/main.py) - Added profile endpoints and web route
- [app/schemas/user.py](app/schemas/user.py) - Enhanced password validation

### Frontend
- [templates/profile.html](templates/profile.html) - New profile page
- [templates/layout.html](templates/layout.html) - Added profile link to navbar

### Tests
- [tests/unit/test_user_profile.py](tests/unit/test_user_profile.py) - Unit tests
- [tests/integration/test_profile_endpoints.py](tests/integration/test_profile_endpoints.py) - Integration tests
- [tests/e2e/test_profile_flow.py](tests/e2e/test_profile_flow.py) - E2E tests

## Test Coverage Summary

- **Unit Tests**: 15 tests covering schemas and password logic
- **Integration Tests**: 24 tests covering API endpoints and database interactions
- **E2E Tests**: 19 tests covering complete user workflows
- **Total**: 58 comprehensive tests

## Future Enhancements

1. **Email Verification**: Send verification email when email changes
2. **Password Reset**: Forgot password functionality
3. **Two-Factor Authentication**: Add 2FA support
4. **Profile Picture**: Upload and manage profile pictures
5. **Account Deletion**: Soft/hard delete account option
6. **Activity Log**: Track profile changes history
7. **Password History**: Prevent reuse of recent passwords
8. **Session Management**: View and manage active sessions

## License

This feature is part of the Calculations App project.
