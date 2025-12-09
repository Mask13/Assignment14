"""
Comprehensive Playwright E2E Tests for Calculations API

This test suite covers:
- Positive Scenarios: Successful CRUD operations
- Negative Scenarios: Invalid inputs, unauthorized access, error responses
- BREAD operations: Browse, Read, Edit, Add, Delete
"""

import pytest
import asyncio
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, expect
import random
import string

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api"

# Test data
TEST_USER = {
    "username": f"testuser_{random.randint(1000, 9999)}",
    "email": f"test_{random.randint(1000, 9999)}@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def browser():
    """Launch browser for the test session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()

@pytest.fixture
async def context(browser: Browser):
    """Create a new browser context for each test."""
    context = await browser.new_context()
    yield context
    await context.close()

@pytest.fixture
async def page(context: BrowserContext):
    """Create a new page for each test."""
    page = await context.new_page()
    yield page
    await page.close()


# ==============================================================================
# Authentication Tests
# ==============================================================================

@pytest.mark.asyncio
class TestAuthentication:
    """Test user registration and login."""
    
    async def test_user_registration_positive(self, page: Page):
        """Test successful user registration."""
        await page.goto(f"{BASE_URL}/register")
        
        # Fill registration form
        await page.fill('input[name="username"]', TEST_USER["username"])
        await page.fill('input[name="email"]', TEST_USER["email"])
        await page.fill('input[name="first_name"]', TEST_USER["first_name"])
        await page.fill('input[name="last_name"]', TEST_USER["last_name"])
        await page.fill('input[name="password"]', TEST_USER["password"])
        await page.fill('input[name="confirm_password"]', TEST_USER["confirm_password"])
        
        # Submit form
        await page.click('button[type="submit"]')
        
        # Wait for success message
        await page.wait_for_selector('#successAlert', state="visible", timeout=5000)
        
        # Should redirect to login page
        await page.wait_for_url(f"{BASE_URL}/login", timeout=10000)
    
    async def test_user_registration_password_mismatch(self, page: Page):
        """Test registration fails with password mismatch."""
        await page.goto(f"{BASE_URL}/register")
        
        # Fill form with mismatched passwords
        await page.fill('input[name="username"]', "testuser_mismatch")
        await page.fill('input[name="email"]', "mismatch@example.com")
        await page.fill('input[name="first_name"]', "Test")
        await page.fill('input[name="last_name"]', "User")
        await page.fill('input[name="password"]', "SecurePass123!")
        await page.fill('input[name="confirm_password"]', "DifferentPass123!")
        
        # Submit form
        await page.click('button[type="submit"]')
        
        # Should show error
        await page.wait_for_selector('#errorAlert', state="visible", timeout=5000)
        error_text = await page.inner_text('#errorMessage')
        assert "do not match" in error_text.lower()
    
    async def test_user_registration_weak_password(self, page: Page):
        """Test registration fails with weak password."""
        await page.goto(f"{BASE_URL}/register")
        
        # Fill form with weak password
        await page.fill('input[name="username"]', "testuser_weak")
        await page.fill('input[name="email"]', "weak@example.com")
        await page.fill('input[name="first_name"]', "Test")
        await page.fill('input[name="last_name"]', "User")
        await page.fill('input[name="password"]', "weak")
        await page.fill('input[name="confirm_password"]', "weak")
        
        # Submit form
        await page.click('button[type="submit"]')
        
        # Should show error
        await page.wait_for_selector('#errorAlert', state="visible", timeout=5000)
    
    async def test_user_login_positive(self, page: Page):
        """Test successful user login."""
        await page.goto(f"{BASE_URL}/login")
        
        # Fill login form
        await page.fill('input[name="username"]', TEST_USER["username"])
        await page.fill('input[name="password"]', TEST_USER["password"])
        
        # Submit form
        await page.click('button[type="submit"]')
        
        # Wait for success and redirect to dashboard
        await page.wait_for_selector('#successAlert', state="visible", timeout=5000)
        await page.wait_for_url(f"{BASE_URL}/dashboard", timeout=10000)
    
    async def test_user_login_invalid_credentials(self, page: Page):
        """Test login fails with invalid credentials."""
        await page.goto(f"{BASE_URL}/login")
        
        # Fill login form with invalid credentials
        await page.fill('input[name="username"]', "invalid_user")
        await page.fill('input[name="password"]', "InvalidPass123!")
        
        # Submit form
        await page.click('button[type="submit"]')
        
        # Should show error
        await page.wait_for_selector('#errorAlert', state="visible", timeout=5000)
        error_text = await page.inner_text('#errorMessage')
        assert "incorrect" in error_text.lower() or "failed" in error_text.lower()


# ==============================================================================
# Calculation BREAD Tests (Browse, Read, Edit, Add, Delete)
# ==============================================================================

@pytest.mark.asyncio
class TestCalculationBREAD:
    """Test BREAD operations for calculations."""
    
    @pytest.fixture(autouse=True)
    async def login(self, page: Page):
        """Auto-login before each test."""
        # Login via API
        response = await page.request.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
        )
        
        if response.ok:
            data = await response.json()
            # Set token in localStorage
            await page.goto(f"{BASE_URL}/dashboard")
            await page.evaluate(f"localStorage.setItem('access_token', '{data['access_token']}')")
            await page.evaluate(f"localStorage.setItem('refresh_token', '{data['refresh_token']}')")
    
    async def test_add_calculation_positive(self, page: Page):
        """Test successfully adding a calculation."""
        await page.goto(f"{BASE_URL}/calculations/new")
        
        # Fill form
        await page.select_option('select[name="type"]', "addition")
        await page.fill('input[name="inputs"]', "10, 20, 30")
        
        # Submit
        await page.click('button[type="submit"]')
        
        # Should show success and redirect
        await page.wait_for_selector('#successMessage', state="visible", timeout=5000)
        success_text = await page.inner_text('#successText')
        assert "60" in success_text  # Result should be 60
    
    async def test_add_calculation_division_by_zero(self, page: Page):
        """Test adding calculation fails with division by zero."""
        await page.goto(f"{BASE_URL}/calculations/new")
        
        # Fill form with division by zero
        await page.select_option('select[name="type"]', "division")
        await page.fill('input[name="inputs"]', "100, 0")
        
        # Submit
        await page.click('button[type="submit"]')
        
        # Should show error
        await page.wait_for_selector('#errorMessage', state="visible", timeout=5000)
        error_text = await page.inner_text('#errorText')
        assert "divide by zero" in error_text.lower()
    
    async def test_add_calculation_insufficient_inputs(self, page: Page):
        """Test adding calculation fails with insufficient inputs."""
        await page.goto(f"{BASE_URL}/calculations/new")
        
        # Fill form with only one input
        await page.select_option('select[name="type"]', "addition")
        await page.fill('input[name="inputs"]', "10")
        
        # Submit
        await page.click('button[type="submit"]')
        
        # Should show error
        await page.wait_for_selector('#errorMessage', state="visible", timeout=5000)
        error_text = await page.inner_text('#errorText')
        assert "at least 2" in error_text.lower()
    
    async def test_add_calculation_invalid_inputs(self, page: Page):
        """Test adding calculation fails with non-numeric inputs."""
        await page.goto(f"{BASE_URL}/calculations/new")
        
        # Fill form with invalid inputs
        await page.select_option('select[name="type"]', "addition")
        await page.fill('input[name="inputs"]', "10, abc, 30")
        
        # Submit
        await page.click('button[type="submit"]')
        
        # Should show error
        await page.wait_for_selector('#errorMessage', state="visible", timeout=5000)
        error_text = await page.inner_text('#errorText')
        assert "invalid" in error_text.lower()
    
    async def test_browse_calculations(self, page: Page):
        """Test browsing all calculations."""
        # First, create a calculation
        await page.goto(f"{BASE_URL}/calculations/new")
        await page.select_option('select[name="type"]', "multiplication")
        await page.fill('input[name="inputs"]', "5, 4")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(2000)
        
        # Navigate to dashboard
        await page.goto(f"{BASE_URL}/dashboard")
        
        # Wait for calculations to load
        await page.wait_for_selector('#calculationsList', timeout=5000)
        
        # Check that at least one calculation is displayed
        calculations = await page.query_selector_all('#calculationsList > div')
        assert len(calculations) > 0
    
    async def test_read_calculation(self, page: Page):
        """Test reading a specific calculation."""
        # First, create a calculation via API
        token = await page.evaluate("localStorage.getItem('access_token')")
        
        response = await page.request.post(
            f"{API_BASE_URL}/calculations",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "type": "subtraction",
                "inputs": [100, 25, 15]
            }
        )
        
        assert response.ok
        calc_data = await response.json()
        calc_id = calc_data["id"]
        
        # Navigate to view page
        await page.goto(f"{BASE_URL}/calculations/{calc_id}")
        
        # Wait for calculation to load
        await page.wait_for_selector('#calculationDetail', timeout=5000)
        
        # Verify details are displayed
        content = await page.content()
        assert "Subtraction" in content
        assert "60" in content  # Result
    
    async def test_edit_calculation_positive(self, page: Page):
        """Test successfully editing a calculation."""
        # First, create a calculation
        token = await page.evaluate("localStorage.getItem('access_token')")
        
        response = await page.request.post(
            f"{API_BASE_URL}/calculations",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "type": "addition",
                "inputs": [10, 20]
            }
        )
        
        calc_data = await response.json()
        calc_id = calc_data["id"]
        
        # Navigate to edit page
        await page.goto(f"{BASE_URL}/calculations/{calc_id}/edit")
        
        # Wait for form to load
        await page.wait_for_selector('#editForm', state="visible", timeout=5000)
        
        # Edit the calculation
        await page.select_option('select[name="type"]', "multiplication")
        await page.fill('input[name="inputs"]', "5, 6")
        
        # Submit
        await page.click('button[type="submit"]')
        
        # Should show success
        await page.wait_for_selector('#successMessage', state="visible", timeout=5000)
        success_text = await page.inner_text('#successText')
        assert "30" in success_text  # New result
    
    async def test_delete_calculation_positive(self, page: Page):
        """Test successfully deleting a calculation."""
        # First, create a calculation
        token = await page.evaluate("localStorage.getItem('access_token')")
        
        response = await page.request.post(
            f"{API_BASE_URL}/calculations",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "type": "division",
                "inputs": [100, 5]
            }
        )
        
        calc_data = await response.json()
        calc_id = calc_data["id"]
        
        # Navigate to dashboard
        await page.goto(f"{BASE_URL}/dashboard")
        await page.wait_for_timeout(2000)
        
        # Find and click delete button (using JavaScript to confirm)
        await page.evaluate("window.confirm = () => true")
        
        # Delete via API call to verify endpoint
        response = await page.request.delete(
            f"{API_BASE_URL}/calculations/{calc_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status == 204
    
    async def test_unauthorized_access(self, page: Page):
        """Test that unauthorized users cannot access calculations."""
        # Clear token
        await page.goto(f"{BASE_URL}/dashboard")
        await page.evaluate("localStorage.clear()")
        
        # Try to access dashboard
        await page.goto(f"{BASE_URL}/dashboard")
        
        # Should redirect to login
        await page.wait_for_url(f"{BASE_URL}/login", timeout=5000)


# ==============================================================================
# API Direct Tests
# ==============================================================================

@pytest.mark.asyncio
class TestCalculationAPI:
    """Test calculation API endpoints directly."""
    
    @pytest.fixture(autouse=True)
    async def get_token(self, page: Page):
        """Get authentication token."""
        response = await page.request.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
        )
        
        data = await response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    async def test_api_create_calculation_positive(self, page: Page):
        """Test creating calculation via API - positive."""
        response = await page.request.post(
            f"{API_BASE_URL}/calculations",
            headers=self.headers,
            data={
                "type": "addition",
                "inputs": [15, 25, 10]
            }
        )
        
        assert response.ok
        data = await response.json()
        assert data["type"] == "addition"
        assert data["result"] == 50
    
    async def test_api_create_calculation_division_by_zero(self, page: Page):
        """Test creating calculation via API - division by zero."""
        response = await page.request.post(
            f"{API_BASE_URL}/calculations",
            headers=self.headers,
            data={
                "type": "division",
                "inputs": [100, 0]
            }
        )
        
        assert response.status == 400
        data = await response.json()
        assert "divide by zero" in data["error"].lower() or "divide by zero" in data["detail"].lower()
    
    async def test_api_get_calculations(self, page: Page):
        """Test getting all calculations via API."""
        response = await page.request.get(
            f"{API_BASE_URL}/calculations",
            headers=self.headers
        )
        
        assert response.ok
        data = await response.json()
        assert isinstance(data, list)
    
    async def test_api_update_calculation(self, page: Page):
        """Test updating calculation via API."""
        # Create a calculation first
        create_response = await page.request.post(
            f"{API_BASE_URL}/calculations",
            headers=self.headers,
            data={
                "type": "addition",
                "inputs": [10, 10]
            }
        )
        
        calc_data = await create_response.json()
        calc_id = calc_data["id"]
        
        # Update it
        update_response = await page.request.put(
            f"{API_BASE_URL}/calculations/{calc_id}",
            headers=self.headers,
            data={
                "type": "multiplication",
                "inputs": [5, 5]
            }
        )
        
        assert update_response.ok
        updated_data = await update_response.json()
        assert updated_data["type"] == "multiplication"
        assert updated_data["result"] == 25
    
    async def test_api_delete_calculation(self, page: Page):
        """Test deleting calculation via API."""
        # Create a calculation first
        create_response = await page.request.post(
            f"{API_BASE_URL}/calculations",
            headers=self.headers,
            data={
                "type": "subtraction",
                "inputs": [100, 50]
            }
        )
        
        calc_data = await create_response.json()
        calc_id = calc_data["id"]
        
        # Delete it
        delete_response = await page.request.delete(
            f"{API_BASE_URL}/calculations/{calc_id}",
            headers=self.headers
        )
        
        assert delete_response.status == 204
        
        # Verify it's deleted
        get_response = await page.request.get(
            f"{API_BASE_URL}/calculations/{calc_id}",
            headers=self.headers
        )
        
        assert get_response.status == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
