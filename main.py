"""
FastAPI Main Application Module

This module defines the main FastAPI application, including:
- Application initialization and configuration
- API endpoints for user authentication
- API endpoints for calculation management (BREAD operations)
- Web routes for HTML templates
- Database table creation on startup

The application follows a RESTful API design with proper separation of concerns:
- Routes handle HTTP requests and responses
- Models define database structure
- Schemas validate request/response data
- Dependencies handle authentication and database sessions
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import List

# FastAPI imports
from fastapi import Body, FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError

from sqlalchemy.orm import Session
import uvicorn

# Application imports
from app.auth.dependencies import get_current_active_user
from app.auth.jwt import create_token, get_password_hash
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import CalculationBase, CalculationResponse, CalculationUpdate, CalculationType
from app.schemas.token import TokenResponse, TokenType
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.database import Base, get_db, engine
from app.config import get_settings

import logging

settings = get_settings()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables on startup using the lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    
    Creates database tables on startup and cleans up on shutdown.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    yield
    logger.info("Application shutdown")

app = FastAPI(
    title="Calculations API",
    description="API for managing calculations and users with BREAD operations",
    version="2.0.0",
    lifespan=lifespan
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Setup templates directory
templates = Jinja2Templates(directory="templates")

# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with logging."""
    logger.error(f"HTTPException on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed error messages."""
    error_messages = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    logger.error(f"ValidationError on {request.url.path}: {error_messages}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": error_messages},
    )

# ============================================================================
# Web Routes (HTML Templates)
# ============================================================================

@app.get("/", response_class=HTMLResponse, tags=["web"])
async def read_index(request: Request):
    """Serve the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse, tags=["web"])
async def register_page(request: Request):
    """Serve the user registration page."""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse, tags=["web"])
async def login_page(request: Request):
    """Serve the user login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse, tags=["web"])
async def dashboard_page(request: Request):
    """Serve the user dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/calculations/new", response_class=HTMLResponse, tags=["web"])
async def new_calculation_page(request: Request):
    """Serve the create calculation page."""
    return templates.TemplateResponse("create_calculation.html", {"request": request})

@app.get("/calculations/{calculation_id}", response_class=HTMLResponse, tags=["web"])
async def view_calculation_page(request: Request, calculation_id: UUID):
    """Serve the view calculation page."""
    return templates.TemplateResponse("view_calculation.html", {"request": request, "calculation_id": calculation_id})

@app.get("/calculations/{calculation_id}/edit", response_class=HTMLResponse, tags=["web"])
async def edit_calculation_page(request: Request, calculation_id: UUID):
    """Serve the edit calculation page."""
    return templates.TemplateResponse("edit_calculation.html", {"request": request, "calculation_id": calculation_id})

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["auth"])
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **email**: User's email address
    - **username**: User's unique username (3-50 characters)
    - **password**: Password (8-128 characters, must include upper, lower, digit, special char)
    - **confirm_password**: Password confirmation
    """
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Create new user
    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        username=user_data.username,
        password=User.hash_password(user_data.password),
        is_active=True,
        is_verified=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.model_validate(new_user)

@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
async def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return tokens.
    
    - **username**: Username or email
    - **password**: User's password
    """
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == user_login.username) | (User.email == user_login.username)
    ).first()
    
    if not user or not user.verify_password(user_login.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not active"
        )
    
    # Create tokens
    access_token = create_token(str(user.id), TokenType.ACCESS)
    refresh_token = create_token(str(user.id), TokenType.REFRESH)
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified
    )

@app.post("/auth/token", response_model=TokenResponse, tags=["auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible token endpoint.
    
    Used for form-based login from web interface.
    """
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_token(str(user.id), TokenType.ACCESS)
    refresh_token = create_token(str(user.id), TokenType.REFRESH)
    
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified
    )

# ============================================================================
# Calculation BREAD Endpoints (Browse, Read, Edit, Add, Delete)
# ============================================================================

@app.get("/api/calculations", response_model=List[CalculationResponse], tags=["calculations"])
async def browse_calculations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Browse (GET) all calculations for the logged-in user.
    
    Returns a list of calculations with optional pagination.
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    """
    calculations = db.query(Calculation).filter(
        Calculation.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return [
        CalculationResponse(
            id=c.id,
            type=c.type,
            inputs=c.inputs,
            user_id=c.user_id,
            result=c.get_result()
        ) for c in calculations
    ]

@app.get("/api/calculations/{calculation_id}", response_model=CalculationResponse, tags=["calculations"])
async def read_calculation(
    calculation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Read (GET) a specific calculation by ID.
    
    Returns detailed information about a single calculation.
    """
    calculation = db.query(Calculation).filter(
        Calculation.id == calculation_id
    ).first()
    
    if not calculation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found"
        )
    
    # Verify ownership
    if calculation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this calculation"
        )
    
    return CalculationResponse(
        id=calculation.id,
        type=calculation.type,
        inputs=calculation.inputs,
        user_id=calculation.user_id,
        result=calculation.get_result()
    )

@app.post("/api/calculations", response_model=CalculationResponse, status_code=status.HTTP_201_CREATED, tags=["calculations"])
async def add_calculation(
    calculation: CalculationBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add (POST) a new calculation.
    
    Creates a new calculation and associates it with the current user.
    - **type**: Type of operation (addition, subtraction, multiplication, division)
    - **inputs**: List of numeric inputs (minimum 2 required)
    """
    # Validate inputs
    if not calculation.inputs or len(calculation.inputs) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 inputs are required"
        )
    
    # Prevent division by zero
    if calculation.type == CalculationType.DIVISION:
        if any(x == 0 for x in calculation.inputs[1:]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot divide by zero"
            )
    
    # Create calculation using factory method
    db_calculation = Calculation.create(
        calc_type=calculation.type.value,
        user_id=current_user.id,
        inputs=calculation.inputs
    )
    
    db.add(db_calculation)
    db.commit()
    db.refresh(db_calculation)
    
    return CalculationResponse(
        id=db_calculation.id,
        type=db_calculation.type,
        inputs=db_calculation.inputs,
        user_id=db_calculation.user_id,
        result=db_calculation.get_result()
    )

@app.put("/api/calculations/{calculation_id}", response_model=CalculationResponse, tags=["calculations"])
async def edit_calculation(
    calculation_id: UUID,
    calculation_update: CalculationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Edit (PUT) an existing calculation.
    
    Updates fields of an existing calculation.
    """
    db_calculation = db.query(Calculation).filter(
        Calculation.id == calculation_id
    ).first()
    
    if not db_calculation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found"
        )
    
    # Verify ownership
    if db_calculation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this calculation"
        )
    
    # Update fields
    if calculation_update.type is not None:
        db_calculation.type = str(calculation_update.type)
    
    if calculation_update.inputs is not None:
        # Validate inputs
        if len(calculation_update.inputs) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 inputs are required"
            )
        
        # Prevent division by zero
        if db_calculation.type == "division" and any(x == 0 for x in calculation_update.inputs[1:]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot divide by zero"
            )
        
        db_calculation.inputs = calculation_update.inputs
    
    db.commit()
    db.refresh(db_calculation)
    
    return CalculationResponse(
        id=db_calculation.id,
        type=db_calculation.type,
        inputs=db_calculation.inputs,
        user_id=db_calculation.user_id,
        result=db_calculation.get_result()
    )

@app.patch("/api/calculations/{calculation_id}", response_model=CalculationResponse, tags=["calculations"])
async def partial_edit_calculation(
    calculation_id: UUID,
    calculation_update: CalculationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Partial Edit (PATCH) an existing calculation.
    
    Same as PUT but allows partial updates.
    """
    return await edit_calculation(calculation_id, calculation_update, db, current_user)

@app.delete("/api/calculations/{calculation_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["calculations"])
async def delete_calculation(
    calculation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a calculation by ID.
    
    Permanently removes a calculation from the database.
    """
    db_calculation = db.query(Calculation).filter(
        Calculation.id == calculation_id
    ).first()
    
    if not db_calculation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found"
        )
    
    # Verify ownership
    if db_calculation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this calculation"
        )
    
    db.delete(db_calculation)
    db.commit()
    
    return None

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
