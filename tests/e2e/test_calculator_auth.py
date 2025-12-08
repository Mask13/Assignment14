import pytest
from playwright.sync_api import expect
from faker import Faker
import requests

fake = Faker()

@pytest.mark.e2e
def test_authenticated_calculation_history(page, fastapi_server):
    # 1. Register and Login
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
    
    # Login via UI
    page.goto("http://localhost:8000/login")
    page.fill("#username", username)
    page.fill("#password", password)
    page.click("button[type='submit']")
    
    # Wait for redirect to home
    page.wait_for_url("**/")
    
    # Verify we are logged in (Logout button visible)
    expect(page.locator("button:text('Logout')")).to_be_visible()
    
    # 2. Perform Calculation
    page.fill("#a", "10")
    page.fill("#b", "5")
    page.click("button:text('Add')")
    
    # Verify result
    expect(page.locator("#resultText")).to_contain_text("Result: 15")
    
    # 3. Verify History
    # Wait for the history table to populate
    expect(page.locator("#historyTableBody tr")).to_have_count(1)
    
    # Check content of the history row
    row = page.locator("#historyTableBody tr").first
    expect(row).to_contain_text("addition")
    expect(row).to_contain_text("[10, 5]")
    expect(row).to_contain_text("15")

@pytest.mark.e2e
def test_unauthenticated_calculation(page, fastapi_server):
    # 1. Go to home page (not logged in)
    page.goto("http://localhost:8000/")
    
    # Verify Login link is visible
    expect(page.locator("a[href='/login']")).to_be_visible()
    
    # 2. Perform Calculation
    page.fill("#a", "20")
    page.fill("#b", "4")
    page.click("button:text('Divide')")
    
    # Verify result
    expect(page.locator("#resultText")).to_contain_text("Result: 5")
    
    # 3. Verify History is NOT visible
    expect(page.locator("#historySection")).not_to_be_visible()
