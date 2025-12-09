# tests/e2e/test_e2e.py

import pytest  # Import the pytest framework for writing and running tests
from playwright.sync_api import expect

# The following decorators and functions define E2E tests for the FastAPI calculator application.

@pytest.mark.e2e
def test_hello_world(page, fastapi_server):
    """
    Test that the homepage displays "Hello World".

    This test verifies that when a user navigates to the homepage of the application,
    the main header (`<h1>`) correctly displays the text "Hello World". This ensures
    that the server is running and serving the correct template.
    """
    # Navigate the browser to the homepage URL of the FastAPI application.
    page.goto(f'{fastapi_server}')
    
    # Use an assertion to check that the text within the first <h1> tag is exactly "Welcome to the Calculations App".
    # If the text does not match, the test will fail.
    expect(page.locator('h1')).to_have_text('Welcome to the Calculations App')

@pytest.mark.e2e
def test_calculator_add(page, fastapi_server):
    """
    Test the addition functionality of the calculator.
    
    This test is now covered by test_calculator_auth.py as calculation requires authentication.
    We will just verify that the calculator is NOT present on the home page.
    """
    # Navigate the browser to the homepage URL of the FastAPI application.
    page.goto(f'{fastapi_server}')
    
    # Verify that the calculator inputs are NOT visible
    expect(page.locator('#a')).not_to_be_visible()
    expect(page.locator('#b')).not_to_be_visible()

@pytest.mark.e2e
def test_calculator_divide_by_zero(page, fastapi_server):
    """
    Test the divide by zero functionality of the calculator.
    
    This test is now covered by test_calculator_auth.py as calculation requires authentication.
    We will just verify that the calculator is NOT present on the home page.
    """
    # Navigate the browser to the homepage URL of the FastAPI application.
    page.goto(f'{fastapi_server}')
    
    # Verify that the calculator inputs are NOT visible
    expect(page.locator('#a')).not_to_be_visible()
    expect(page.locator('#b')).not_to_be_visible()
