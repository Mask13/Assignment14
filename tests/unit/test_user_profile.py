"""
Unit tests for user profile functionality
Tests password change logic, profile update validation, and edge cases
"""
import pytest
import uuid
from pydantic import ValidationError
from app.schemas.user import UserUpdate, PasswordUpdate
from app.models.user import User
from sqlalchemy.orm import Session


# ======================================================================================
# PasswordUpdate Schema Tests
# ======================================================================================

def test_password_update_valid():
    """Test valid password update data"""
    password_data = PasswordUpdate(
        current_password="OldPassword123!",
        new_password="NewPassword123!",
        confirm_new_password="NewPassword123!"
    )
    assert password_data.current_password == "OldPassword123!"
    assert password_data.new_password == "NewPassword123!"


def test_password_update_passwords_dont_match():
    """Test password update with mismatched new passwords"""
    with pytest.raises(ValidationError, match="do not match"):
        PasswordUpdate(
            current_password="OldPassword123!",
            new_password="NewPassword123!",
            confirm_new_password="DifferentPassword123!"
        )


def test_password_update_same_as_current():
    """Test password update with new password same as current"""
    with pytest.raises(ValidationError, match="must be different from current password"):
        PasswordUpdate(
            current_password="SamePassword123!",
            new_password="SamePassword123!",
            confirm_new_password="SamePassword123!"
        )


def test_password_update_too_short():
    """Test password update with password too short"""
    with pytest.raises(ValidationError):
        PasswordUpdate(
            current_password="OldPass123!",
            new_password="New1!",
            confirm_new_password="New1!"
        )


def test_password_update_no_uppercase():
    """Test password update with no uppercase letter"""
    with pytest.raises(ValidationError, match="at least one uppercase letter"):
        PasswordUpdate(
            current_password="OldPassword123!",
            new_password="newpassword123!",
            confirm_new_password="newpassword123!"
        )


def test_password_update_no_lowercase():
    """Test password update with no lowercase letter"""
    with pytest.raises(ValidationError, match="at least one lowercase letter"):
        PasswordUpdate(
            current_password="OldPassword123!",
            new_password="NEWPASSWORD123!",
            confirm_new_password="NEWPASSWORD123!"
        )


def test_password_update_no_digit():
    """Test password update with no digit"""
    with pytest.raises(ValidationError, match="at least one digit"):
        PasswordUpdate(
            current_password="OldPassword123!",
            new_password="NewPassword!",
            confirm_new_password="NewPassword!"
        )


def test_password_update_no_special_character():
    """Test password update with no special character"""
    with pytest.raises(ValidationError, match="at least one special character"):
        PasswordUpdate(
            current_password="OldPassword123!",
            new_password="NewPassword123",
            confirm_new_password="NewPassword123"
        )


# ======================================================================================
# UserUpdate Schema Tests
# ======================================================================================

def test_user_update_all_fields():
    """Test updating all profile fields"""
    update_data = UserUpdate(
        first_name="NewFirst",
        last_name="NewLast",
        email="newemail@example.com",
        username="newusername"
    )
    assert update_data.first_name == "NewFirst"
    assert update_data.last_name == "NewLast"
    assert update_data.email == "newemail@example.com"
    assert update_data.username == "newusername"


def test_user_update_partial_fields():
    """Test updating only some profile fields"""
    update_data = UserUpdate(
        first_name="NewFirst",
        email="newemail@example.com"
    )
    assert update_data.first_name == "NewFirst"
    assert update_data.email == "newemail@example.com"
    assert update_data.last_name is None
    assert update_data.username is None


def test_user_update_empty_optional():
    """Test UserUpdate with all optional fields empty"""
    update_data = UserUpdate()
    assert update_data.first_name is None
    assert update_data.last_name is None
    assert update_data.email is None
    assert update_data.username is None


def test_user_update_invalid_email():
    """Test UserUpdate with invalid email format"""
    with pytest.raises(ValidationError):
        UserUpdate(email="not-an-email")


def test_user_update_short_username():
    """Test UserUpdate with username too short"""
    with pytest.raises(ValidationError):
        UserUpdate(username="ab")


def test_user_update_long_username():
    """Test UserUpdate with username too long"""
    with pytest.raises(ValidationError):
        UserUpdate(username="a" * 51)


def test_user_update_empty_first_name():
    """Test UserUpdate with empty first name string"""
    with pytest.raises(ValidationError):
        UserUpdate(first_name="")


def test_user_update_empty_last_name():
    """Test UserUpdate with empty last name string"""
    with pytest.raises(ValidationError):
        UserUpdate(last_name="")


# ======================================================================================
# User Model Password Verification Tests
# ======================================================================================

def test_user_verify_password_correct(db_session: Session):
    """Test verifying correct password"""
    # Create a test user with unique email/username
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        first_name="Test",
        last_name="User",
        password=User.hash_password("TestPassword123!")
    )
    db_session.add(user)
    db_session.commit()
    
    # Verify correct password
    assert user.verify_password("TestPassword123!")


def test_user_verify_password_incorrect(db_session: Session):
    """Test verifying incorrect password"""
    # Create a test user with unique email/username
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        first_name="Test",
        last_name="User",
        password=User.hash_password("TestPassword123!")
    )
    db_session.add(user)
    db_session.commit()
    
    # Verify incorrect password
    assert not user.verify_password("WrongPassword123!")


def test_user_hash_password_different_hashes():
    """Test that hashing the same password twice produces different hashes"""
    password = "TestPassword123!"
    hash1 = User.hash_password(password)
    hash2 = User.hash_password(password)
    
    # Hashes should be different (bcrypt uses salt)
    assert hash1 != hash2
    
    # But both should verify correctly
    from app.auth.jwt import verify_password
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)


def test_user_update_method(db_session: Session):
    """Test User.update() method updates fields correctly"""
    # Create a test user with unique email/username
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        first_name="Test",
        last_name="User",
        password=User.hash_password("TestPassword123!")
    )
    db_session.add(user)
    db_session.commit()
    
    original_updated_at = user.updated_at
    
    # Update user
    import time
    time.sleep(0.1)  # Ensure time difference
    new_email = f"newemail_{unique_id}@example.com"
    user.update(
        first_name="NewFirst",
        email=new_email
    )
    db_session.commit()
    
    # Verify updates
    assert user.first_name == "NewFirst"
    assert user.email == new_email
    assert user.last_name == "User"  # Unchanged
    assert user.updated_at > original_updated_at


# ======================================================================================
# Password Change Business Logic Tests
# ======================================================================================

def test_password_change_flow(db_session: Session):
    """Test complete password change flow"""
    # Create user with initial password and unique email/username
    unique_id = str(uuid.uuid4())[:8]
    initial_password = "InitialPassword123!"
    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        first_name="Test",
        last_name="User",
        password=User.hash_password(initial_password)
    )
    db_session.add(user)
    db_session.commit()
    
    # Verify initial password works
    assert user.verify_password(initial_password)
    
    # Change password
    new_password = "NewPassword456!"
    user.password = User.hash_password(new_password)
    db_session.commit()
    
    # Verify old password no longer works
    assert not user.verify_password(initial_password)
    
    # Verify new password works
    assert user.verify_password(new_password)


def test_password_change_validates_current_password(db_session: Session):
    """Test that password change requires correct current password"""
    # Create user with unique email/username
    unique_id = str(uuid.uuid4())[:8]
    current_password = "CurrentPassword123!"
    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        first_name="Test",
        last_name="User",
        password=User.hash_password(current_password)
    )
    db_session.add(user)
    db_session.commit()
    
    # Simulate password change with wrong current password
    wrong_current = "WrongPassword123!"
    
    # This should fail verification
    assert not user.verify_password(wrong_current)
    
    # Password should remain unchanged
    assert user.verify_password(current_password)
