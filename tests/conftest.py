# tests/conftest.py

import subprocess
import time
import logging
from typing import Generator, Dict, List
from contextlib import contextmanager

import pytest
import requests
from faker import Faker
from playwright.sync_api import sync_playwright, Browser, Page
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.database import Base, get_engine, get_sessionmaker
from app.models.user import User
from app.config import settings
from app.database_init import init_db, drop_db

# ======================================================================================
# Logging Configuration
# ======================================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ======================================================================================
# Database Configuration
# ======================================================================================
fake = Faker()
Faker.seed(12345)

logger.info(f"Using database URL: {settings.DATABASE_URL}")

# Create an engine and sessionmaker based on DATABASE_URL using factory functions
test_engine = get_engine(database_url=settings.DATABASE_URL)
TestingSessionLocal = get_sessionmaker(engine=test_engine)

# ======================================================================================
# Helper Functions
# ======================================================================================
def create_fake_user() -> Dict[str, str]:
    """
    Generate a dictionary of fake user data for testing.
    """
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "username": fake.unique.user_name(),
        "password": fake.password(length=12)
    }

@contextmanager
def managed_db_session():
    """
    Context manager for safe database session handling.
    """
    session = TestingSessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def wait_for_server(url: str, timeout: int = 30) -> bool:
    """
    Wait for server to be ready, raising an error if it never becomes available.
    """
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    return False

class ServerStartupError(Exception):
    """Raised when the test server fails to start properly"""
    pass

# ======================================================================================
# Primary Database Fixtures
# ======================================================================================
@pytest.fixture(scope="session", autouse=True)
def setup_test_database(request):
    """
    Initialize the test database once per session.
    """
    logger.info("Setting up test database...")
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    init_db()

    yield

    preserve_db = request.config.getoption("--preserve-db")
    if preserve_db:
        logger.info("Skipping drop_db due to --preserve-db flag.")
    else:
        logger.info("Cleaning up test database...")
        drop_db()

@pytest.fixture
def db_session(request) -> Generator[Session, None, None]:
    """
    Provide a test-scoped database session.
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        preserve_db = request.config.getoption("--preserve-db")
        if not preserve_db:
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        session.close()

# ======================================================================================
# Test Data Fixtures
# ======================================================================================
@pytest.fixture
def fake_user_data() -> Dict[str, str]:
    """Provide a dictionary of fake user data."""
    return create_fake_user()

@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create and return a single test user."""
    user_data = create_fake_user()
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def seed_users(db_session: Session, request) -> List[User]:
    """Create multiple test users in the database."""
    try:
        num_users = request.param
    except AttributeError:
        num_users = 5

    users = []
    for _ in range(num_users):
        user_data = create_fake_user()
        user = User(**user_data)
        users.append(user)
        db_session.add(user)

    db_session.commit()
    return users

# ======================================================================================
# FastAPI Server and Browser Fixtures
# ======================================================================================
@pytest.fixture(scope="session")
def fastapi_server():
    """Start and manage a FastAPI test server."""
    server_url = 'http://127.0.0.1:8000/'
    
    # Check if server is already running
    if wait_for_server(server_url, timeout=1):
        logger.info("Server already running, skipping startup...")
        yield
        return

    logger.info("Starting FastAPI server...")

    process = subprocess.Popen(
        ['python', 'main.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if not wait_for_server(server_url, timeout=30):
        process.terminate()
        raise ServerStartupError("FastAPI server failed to start within timeout period")

    yield

    logger.info("Shutting down FastAPI server...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

@pytest.fixture(scope="session")
def browser_context():
    """Provide a Playwright browser context for UI tests."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        try:
            yield browser
        finally:
            browser.close()

@pytest.fixture
def page(browser_context: Browser) -> Page:
    """Provide a new browser page for each test."""
    context = browser_context.new_context(
        viewport={'width': 1920, 'height': 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    yield page
    page.close()
    context.close()

# ======================================================================================
# Pytest Configuration
# ======================================================================================
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--preserve-db",
        action="store_true",
        default=False,
        help="Keep test database after tests, and skip table truncation."
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run tests marked as slow"
    )

def pytest_collection_modifyitems(config, items):
    """Skip slow tests unless --run-slow is specified."""
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="use --run-slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
