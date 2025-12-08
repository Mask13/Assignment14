# main.py

from contextlib import asynccontextmanager
from typing import List
from uuid import UUID
import logging

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
import uvicorn
from pydantic import BaseModel

from app.database import Base, engine, get_db
from app.models.user import User
from app.models.calculation import Calculation
from app.schemas.user import UserResponse, Token
from app.schemas.base import UserCreate
from app.schemas.calculation import CalculationCreate, CalculationResponse, CalculationUpdate
from app.auth.dependencies import get_current_active_user
from app.operations import add, subtract, multiply, divide

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Calculations API",
    description="API for managing calculations and users",
    version="1.0.0",
    lifespan=lifespan
)

# Setup templates directory
templates = Jinja2Templates(directory="templates")

# Custom Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Extracting error messages
    error_messages = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    logger.error(f"ValidationError on {request.url.path}: {error_messages}")
    return JSONResponse(
        status_code=400,
        content={"error": error_messages},
    )

@app.get("/")
async def read_root(request: Request):
    """
    Serve the index.html template.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Simple Calculator Endpoints

class SimpleCalculationRequest(BaseModel):
    a: float
    b: float

@app.post("/calculate/add", response_model=float, tags=["calculations"])
def calculate_addition(request: SimpleCalculationRequest):
    result = add(request.a, request.b)
    return result

@app.post("/calculate/subtract", response_model=float, tags=["calculations"])
def calculate_subtraction(request: SimpleCalculationRequest):
    result = subtract(request.a, request.b)
    return result

@app.post("/calculate/multiply", response_model=float, tags=["calculations"])
def calculate_multiplication(request: SimpleCalculationRequest):
    result = multiply(request.a, request.b)
    return result

@app.post("/calculate/divide", response_model=float, tags=["calculations"])
def calculate_division(request: SimpleCalculationRequest):
    result = divide(request.a, request.b)
    return result

@app.post("/add", tags=["simple_calculator"])
def simple_add(request: SimpleCalculationRequest):
    return {"result": add(request.a, request.b)}

@app.post("/subtract", tags=["simple_calculator"])
def simple_subtract(request: SimpleCalculationRequest):
    return {"result": subtract(request.a, request.b)}

@app.post("/multiply", tags=["simple_calculator"])
def simple_multiply(request: SimpleCalculationRequest):
    return {"result": multiply(request.a, request.b)}

@app.post("/divide", tags=["simple_calculator"])
def simple_divide(request: SimpleCalculationRequest):
    try:
        return {"result": divide(request.a, request.b)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# User Endpoints

@app.post("/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["users"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return User.register(db, user.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/users/login", response_model=Token, tags=["users"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    token = User.authenticate(db, form_data.username, form_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# Calculation Endpoints

@app.get("/calculations", response_model=List[CalculationResponse], tags=["calculations"])
def read_calculations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_active_user)):
    calculations = db.query(Calculation).offset(skip).limit(limit).all()
    return [CalculationResponse.from_orm_with_result(c) for c in calculations]

@app.get("/calculations/{calculation_id}", response_model=CalculationResponse, tags=["calculations"])
def read_calculation(calculation_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_active_user)):
    calculation = db.query(Calculation).filter(Calculation.id == calculation_id).first()
    if calculation is None:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return CalculationResponse.from_orm_with_result(calculation)

@app.post("/calculations", response_model=CalculationResponse, status_code=status.HTTP_201_CREATED, tags=["calculations"])
def create_calculation(calculation: CalculationCreate, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_active_user)):
    try:
        # Create calculation using factory method
        db_calculation = Calculation.create(
            calc_type=calculation.type,
            user_id=current_user.id, # Associate with current user
            inputs=calculation.inputs
        )
        db.add(db_calculation)
        db.commit()
        db.refresh(db_calculation)
        return CalculationResponse.from_orm_with_result(db_calculation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/calculations/{calculation_id}", response_model=CalculationResponse, tags=["calculations"])
def update_calculation(calculation_id: UUID, calculation_update: CalculationUpdate, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_active_user)):
    db_calculation = db.query(Calculation).filter(Calculation.id == calculation_id).first()
    if db_calculation is None:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    if calculation_update.inputs is not None:
        db_calculation.inputs = calculation_update.inputs
    
    if calculation_update.type is not None:
        db_calculation.type = calculation_update.type
        
    db.commit()
    db.refresh(db_calculation)
    return CalculationResponse.from_orm_with_result(db_calculation)

@app.delete("/calculations/{calculation_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["calculations"])
def delete_calculation(calculation_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_active_user)):
    db_calculation = db.query(Calculation).filter(Calculation.id == calculation_id).first()
    if db_calculation is None:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    db.delete(db_calculation)
    db.commit()
    return None

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
