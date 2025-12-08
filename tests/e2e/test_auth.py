import pytest
from playwright.sync_api import expect
from faker import Faker
import requests

fake = Faker()

@pytest.mark.e2e
def test_register_success(page, fastapi_server):
    username = fake.unique.user_name()
    email = fake.unique.email()
    password = "Password123"
    
    page.goto("http://localhost:8000/register")
    
    page.fill("#username", username)
    page.fill("#email", email)
    page.fill("#first_name", fake.first_name())
    page.fill("#last_name", fake.last_name())
    page.fill("#password", password)
    page.fill("#confirm_password", password)
    
    page.click("button[type='submit']")
    
    # Check for success message
    expect(page.locator("#successMessage")).to_contain_text("Registration successful")
    
    # Wait for redirect to login
    page.wait_for_url("**/login")

@pytest.mark.e2e
def test_login_success(page, fastapi_server):
    username = fake.unique.user_name()
    email = fake.unique.email()
    password = "Password123"
    
    # Register via API
    response = requests.post("http://localhost:8000/users/register", json={
        "username": username,
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "password": password
    })
    assert response.status_code == 201
    
    page.goto("http://localhost:8000/login")
    
    page.fill("#username", username)
    page.fill("#password", password)
    
    page.click("button[type='submit']")
    
    # Check for success message
    expect(page.locator("#successMessage")).to_contain_text("Login successful")
    
    # Wait for redirect to home
    page.wait_for_url("**/")

@pytest.mark.e2e
def test_register_short_password(page, fastapi_server):
    page.goto("http://localhost:8000/register")
    
    page.fill("#username", fake.unique.user_name())
    page.fill("#email", fake.unique.email())
    page.fill("#first_name", fake.first_name())
    page.fill("#last_name", fake.last_name())
    page.fill("#password", "123")
    page.fill("#confirm_password", "123")
    
    page.click("button[type='submit']")
    
    # Check for error message
    expect(page.locator("#errorMessage")).to_contain_text("Password must be at least 6 characters long")

@pytest.mark.e2e
def test_login_invalid_credentials(page, fastapi_server):
    page.goto("http://localhost:8000/login")
    
    page.fill("#username", "nonexistentuser")
    page.fill("#password", "wrongpassword")
    
    page.click("button[type='submit']")
    
    # Check for error message
    expect(page.locator("#errorMessage")).to_contain_text("Incorrect username or password")
