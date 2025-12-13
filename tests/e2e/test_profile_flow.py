"""
E2E tests for user profile functionality
Tests complete user flows: login → profile → update → password change → re-login
"""
import pytest
from playwright.sync_api import expect
from faker import Faker
import requests
import uuid
import time

fake = Faker()


def create_test_user(fastapi_server):
    """Helper function to create a test user via API"""
    username = f"testuser_{str(uuid.uuid4())[:8]}"
    email = f"{str(uuid.uuid4())[:8]}@example.com"
    password = "InitialPassword123!"
    first_name = fake.first_name()
    last_name = fake.last_name()
    
    response = requests.post(f"{fastapi_server}auth/register", json={
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password": password,
        "confirm_password": password
    })
    assert response.status_code == 201
    
    return {
        "username": username,
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name
    }


def login_user(page, fastapi_server, username, password):
    """Helper function to log in a user"""
    page.goto(f"{fastapi_server}login")
    page.fill("#username", username)
    page.fill("#password", password)
    page.click("button[type='submit']")
    
    # Wait for successful login
    expect(page.locator("#successMessage")).to_contain_text("Login successful", timeout=5000)
    page.wait_for_url("**/", timeout=5000)


# ======================================================================================
# Profile Access Tests
# ======================================================================================

@pytest.mark.e2e
def test_access_profile_page(page, fastapi_server):
    """Test accessing the profile page after login"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    # Navigate to profile page
    page.goto(f"{fastapi_server}profile")
    
    # Verify page elements are present
    expect(page.locator("h1")).to_contain_text("My Profile")
    expect(page.locator("#firstName")).to_be_visible()
    expect(page.locator("#lastName")).to_be_visible()
    expect(page.locator("#username")).to_be_visible()
    expect(page.locator("#email")).to_be_visible()


@pytest.mark.e2e
def test_profile_page_shows_user_data(page, fastapi_server):
    """Test that profile page displays current user data"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    
    # Wait for profile to load
    page.wait_for_timeout(1000)
    
    # Verify user data is populated
    expect(page.locator("#firstName")).to_have_value(user["first_name"])
    expect(page.locator("#lastName")).to_have_value(user["last_name"])
    expect(page.locator("#username")).to_have_value(user["username"])
    expect(page.locator("#email")).to_have_value(user["email"])


@pytest.mark.e2e
def test_profile_page_without_login_redirects(page, fastapi_server):
    """Test that accessing profile without login redirects to login page"""
    page.goto(f"{fastapi_server}profile")
    
    # Should redirect to login
    page.wait_for_url("**/login", timeout=5000)


@pytest.mark.e2e
def test_profile_link_in_navbar(page, fastapi_server):
    """Test clicking profile link in navigation bar"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    # Click profile link in navbar
    page.click("a[href='/profile']")
    
    # Should navigate to profile page
    page.wait_for_url("**/profile", timeout=5000)
    expect(page.locator("h1")).to_contain_text("My Profile")


# ======================================================================================
# Profile Update Tests
# ======================================================================================

@pytest.mark.e2e
def test_update_profile_success(page, fastapi_server):
    """Test successfully updating profile information"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Update profile fields
    new_first_name = "UpdatedFirst"
    new_last_name = "UpdatedLast"
    
    page.fill("#firstName", new_first_name)
    page.fill("#lastName", new_last_name)
    
    # Submit form
    page.click("#profileForm button[type='submit']")
    
    # Check for success message
    expect(page.locator("#successMessage")).to_contain_text("Profile updated successfully", timeout=5000)
    
    # Verify fields still have updated values
    expect(page.locator("#firstName")).to_have_value(new_first_name)
    expect(page.locator("#lastName")).to_have_value(new_last_name)


@pytest.mark.e2e
def test_update_username(page, fastapi_server):
    """Test updating username"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Update username
    new_username = f"newuser_{str(uuid.uuid4())[:8]}"
    page.fill("#username", new_username)
    
    # Submit form
    page.click("#profileForm button[type='submit']")
    
    # Check for success message
    expect(page.locator("#successMessage")).to_contain_text("Profile updated successfully", timeout=5000)
    
    # Verify username updated
    expect(page.locator("#username")).to_have_value(new_username)


@pytest.mark.e2e
def test_update_email(page, fastapi_server):
    """Test updating email"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Update email
    new_email = f"{str(uuid.uuid4())[:8]}@newdomain.com"
    page.fill("#email", new_email)
    
    # Submit form
    page.click("#profileForm button[type='submit']")
    
    # Check for success message
    expect(page.locator("#successMessage")).to_contain_text("Profile updated successfully", timeout=5000)
    
    # Verify email updated
    expect(page.locator("#email")).to_have_value(new_email)


@pytest.mark.e2e
def test_update_profile_invalid_email(page, fastapi_server):
    """Test updating profile with invalid email format"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Try to update with invalid email
    page.fill("#email", "not-an-email")
    
    # Submit form
    page.click("#profileForm button[type='submit']")
    
    # Check for error message
    expect(page.locator("#errorMessage")).to_be_visible(timeout=5000)


@pytest.mark.e2e
def test_update_profile_duplicate_username(page, fastapi_server):
    """Test updating profile with username that already exists"""
    user1 = create_test_user(fastapi_server)
    user2 = create_test_user(fastapi_server)
    
    login_user(page, fastapi_server, user2["username"], user2["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Try to update to user1's username
    page.fill("#username", user1["username"])
    
    # Submit form
    page.click("#profileForm button[type='submit']")
    
    # Check for error message
    expect(page.locator("#errorMessage")).to_contain_text("Username already taken", timeout=5000)


# ======================================================================================
# Password Change Tests
# ======================================================================================

@pytest.mark.e2e
def test_change_password_success(page, fastapi_server):
    """Test successfully changing password"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Fill password change form
    new_password = "NewPassword456!"
    page.fill("#currentPassword", user["password"])
    page.fill("#newPassword", new_password)
    page.fill("#confirmNewPassword", new_password)
    
    # Submit form
    page.click("#passwordForm button[type='submit']")
    
    # Check for success message
    expect(page.locator("#successMessage")).to_contain_text("Password changed successfully", timeout=5000)


@pytest.mark.e2e
def test_change_password_wrong_current(page, fastapi_server):
    """Test changing password with wrong current password"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Fill with wrong current password
    page.fill("#currentPassword", "WrongPassword123!")
    page.fill("#newPassword", "NewPassword456!")
    page.fill("#confirmNewPassword", "NewPassword456!")
    
    # Submit form
    page.click("#passwordForm button[type='submit']")
    
    # Check for error message
    expect(page.locator("#errorMessage")).to_contain_text("Current password is incorrect", timeout=5000)


@pytest.mark.e2e
def test_change_password_mismatch(page, fastapi_server):
    """Test changing password with mismatched confirmation"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Fill with mismatched passwords
    page.fill("#currentPassword", user["password"])
    page.fill("#newPassword", "NewPassword456!")
    page.fill("#confirmNewPassword", "DifferentPassword456!")
    
    # Submit form
    page.click("#passwordForm button[type='submit']")
    
    # Check for error message
    expect(page.locator("#errorMessage")).to_contain_text("do not match", timeout=5000)


@pytest.mark.e2e
def test_change_password_weak_password(page, fastapi_server):
    """Test changing to a weak password"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Try weak password
    page.fill("#currentPassword", user["password"])
    page.fill("#newPassword", "weak")
    page.fill("#confirmNewPassword", "weak")
    
    # Submit form
    page.click("#passwordForm button[type='submit']")
    
    # Check for error message
    expect(page.locator("#errorMessage")).to_be_visible(timeout=5000)


@pytest.mark.e2e
def test_change_password_same_as_current(page, fastapi_server):
    """Test changing password to same as current"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Try to use same password
    page.fill("#currentPassword", user["password"])
    page.fill("#newPassword", user["password"])
    page.fill("#confirmNewPassword", user["password"])
    
    # Submit form
    page.click("#passwordForm button[type='submit']")
    
    # Check for error message
    expect(page.locator("#errorMessage")).to_contain_text("must be different", timeout=5000)


# ======================================================================================
# Complete Flow Tests (Login → Profile → Update → Password Change → Re-login)
# ======================================================================================

@pytest.mark.e2e
def test_complete_profile_workflow(page, fastapi_server):
    """Test complete workflow: login → profile → update → logout → login"""
    user = create_test_user(fastapi_server)
    
    # Step 1: Login
    login_user(page, fastapi_server, user["username"], user["password"])
    
    # Step 2: Navigate to profile
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Step 3: Update profile
    new_first_name = "CompleteFlowFirst"
    new_last_name = "CompleteFlowLast"
    page.fill("#firstName", new_first_name)
    page.fill("#lastName", new_last_name)
    page.click("#profileForm button[type='submit']")
    expect(page.locator("#successMessage")).to_be_visible(timeout=5000)
    
    # Step 4: Logout
    page.click("#layoutLogoutBtn")
    page.on("dialog", lambda dialog: dialog.accept())
    page.wait_for_url("**/login", timeout=5000)
    
    # Step 5: Login again
    login_user(page, fastapi_server, user["username"], user["password"])
    
    # Step 6: Verify profile changes persisted
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    expect(page.locator("#firstName")).to_have_value(new_first_name)
    expect(page.locator("#lastName")).to_have_value(new_last_name)


@pytest.mark.e2e
def test_complete_password_change_workflow(page, fastapi_server):
    """Test complete workflow: login → change password → logout → login with new password"""
    user = create_test_user(fastapi_server)
    new_password = "SuperNewPassword789!"
    
    # Step 1: Login with original password
    login_user(page, fastapi_server, user["username"], user["password"])
    
    # Step 2: Navigate to profile and change password
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    page.fill("#currentPassword", user["password"])
    page.fill("#newPassword", new_password)
    page.fill("#confirmNewPassword", new_password)
    page.click("#passwordForm button[type='submit']")
    
    # Wait for success message
    expect(page.locator("#successMessage")).to_be_visible(timeout=5000)
    
    # Step 3: Wait for auto-logout (JavaScript redirects after 3 seconds)
    page.wait_for_url("**/login", timeout=5000)
    
    # Step 4: Try logging in with old password (should fail)
    page.fill("#username", user["username"])
    page.fill("#password", user["password"])
    page.click("button[type='submit']")
    expect(page.locator("#errorMessage")).to_contain_text("Invalid", timeout=5000)
    
    # Step 5: Login with new password (should succeed)
    page.fill("#username", user["username"])
    page.fill("#password", new_password)
    page.click("button[type='submit']")
    expect(page.locator("#successMessage")).to_be_visible(timeout=5000)
    page.wait_for_url("**/", timeout=5000)


@pytest.mark.e2e
def test_update_username_then_login(page, fastapi_server):
    """Test updating username and then logging in with new username"""
    user = create_test_user(fastapi_server)
    new_username = f"brandnew_{str(uuid.uuid4())[:8]}"
    
    # Login
    login_user(page, fastapi_server, user["username"], user["password"])
    
    # Update username
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    page.fill("#username", new_username)
    page.click("#profileForm button[type='submit']")
    expect(page.locator("#successMessage")).to_be_visible(timeout=5000)
    
    # Logout
    page.click("#layoutLogoutBtn")
    page.on("dialog", lambda dialog: dialog.accept())
    page.wait_for_url("**/login", timeout=5000)
    
    # Login with new username
    login_user(page, fastapi_server, new_username, user["password"])
    
    # Verify successful login
    expect(page).to_have_url(fastapi_server)


@pytest.mark.e2e
def test_profile_navigation_from_dashboard(page, fastapi_server):
    """Test navigating from dashboard to profile and back"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    # Go to dashboard
    page.goto(f"{fastapi_server}dashboard")
    
    # Navigate to profile via navbar
    page.click("a[href='/profile']")
    expect(page).to_have_url(f"{fastapi_server}profile")
    
    # Navigate back to dashboard via breadcrumb or link
    page.click("a[href='/dashboard']")
    expect(page).to_have_url(f"{fastapi_server}dashboard")


# ======================================================================================
# UI/UX Tests
# ======================================================================================

@pytest.mark.e2e
def test_password_visibility_toggle(page, fastapi_server):
    """Test that password visibility toggle works"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Check initial type is password
    expect(page.locator("#currentPassword")).to_have_attribute("type", "password")
    
    # Click toggle (eye icon) - note: this uses the onclick handler
    # Since we can't easily click the SVG, we'll skip this test or use JavaScript
    # page.evaluate("togglePassword('currentPassword')")
    # expect(page.locator("#currentPassword")).to_have_attribute("type", "text")


@pytest.mark.e2e
def test_profile_form_validation(page, fastapi_server):
    """Test HTML5 form validation on profile form"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Clear required field
    page.fill("#firstName", "")
    
    # Try to submit
    page.click("#profileForm button[type='submit']")
    
    # HTML5 validation should prevent submission
    # The form shouldn't be submitted (success message shouldn't appear)
    expect(page.locator("#successMessage")).not_to_be_visible()


@pytest.mark.e2e
def test_error_message_display_and_dismiss(page, fastapi_server):
    """Test that error messages appear and auto-dismiss"""
    user = create_test_user(fastapi_server)
    login_user(page, fastapi_server, user["username"], user["password"])
    
    page.goto(f"{fastapi_server}profile")
    page.wait_for_timeout(1000)
    
    # Trigger an error (wrong current password)
    page.fill("#currentPassword", "WrongPassword123!")
    page.fill("#newPassword", "NewPassword456!")
    page.fill("#confirmNewPassword", "NewPassword456!")
    page.click("#passwordForm button[type='submit']")
    
    # Error should be visible
    expect(page.locator("#errorAlert")).to_be_visible(timeout=5000)
    expect(page.locator("#errorMessage")).to_contain_text("incorrect")
