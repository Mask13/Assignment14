# 📦 Assignment 14 - BREAD Operations (Final Project: Extra User Functions)

> **Docker Repository**: Same as Assignment 13 - [happymask13/assignment14](https://hub.docker.com/repository/docker/happymask13/assignment14/general) on Docker Hub  
> **GitHub Repository**: Assignment 14 extends Assignment 13 with BREAD functionality (Browse, Read, Edit, Add, Delete)  
> **Base Assignment**: Ends at "Updates to test and reach 95% commit"

## 📘 Assignment Scope
- **Assignment 14 (Core)**: Implement BREAD (Browse, Read, Edit, Add, Delete) functionality for all calculator operations and related views/APIs.
- **Final Project (Extension)**: Add extra user functions including profile management, password change, client-side form validation, and E2E test coverage.

### 🎯 Key Features
- **BREAD Operations (Assignment 14)**: Full Browse, Read, Edit, Add, Delete functionality for all calculator operations
- **Extra User Functions (Final Project)**: User Profile Management and Password Change
   - View and update profile information (first name, last name, username, email)
   - Secure password changing with strength validation
- **Password Hashing**: Bcrypt-based password hashing with verification
- **Client-Side Validation**: Real-time form validation with error/success messages
- **Backend Validation**: Comprehensive server-side validation for security
- **Responsive UI**: Modern profile page with TailwindCSS styling
- **Complete Test Coverage**: Unit, integration, and E2E tests for all functionality
- **Polymorphic Calculation Models**: Complete calculator with database storage
- **Authentication**: JWT-based auth with role management
- **User Registration**: Secure user registration with validation

### 📊 Test Results
```
✅ BREAD operations implemented and covered by integration/E2E tests
✅ 68/68 profile feature tests passing (Final Project)
   - 22 unit tests for schemas and password logic
   - 25 integration tests for API endpoints
   - 21 E2E tests for complete user workflows
✅ All features tested: CRUD, validation, security, polymorphic behavior
✅ CI/CD Pipeline: Automated testing with coverage enforcement
```

## 🧪 Running Tests Locally

To run the tests locally, follow these steps:

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install
```

3. Run all tests with coverage:
```bash
# Run all tests with coverage report
pytest

# Run profile feature tests only
pytest tests/unit/test_user_profile.py tests/integration/test_profile_endpoints.py tests/e2e/test_profile_flow.py -v

# Run specific test suites
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Run calculator tests (polymorphic models)
pytest tests/integration/test_calculation.py -v
pytest tests/integration/test_calculation_schema.py -v

# Generate HTML coverage report
pytest --cov-report=html
open htmlcov/index.html
```

### 🔗 Integration Tests

Integration tests cover the interaction between the API, database, and authentication systems. They ensure that:
- API endpoints return correct status codes and data.
- Database operations (CRUD) are performed correctly.
- Authentication and authorization rules are enforced.
- Profile updates persist correctly in the database.
- Password changes are securely hashed and verified.

To run only the integration tests:
```bash
pytest tests/integration/ -v
```

### 🎯 Profile Feature Tests

The user profile feature includes comprehensive tests:

**Unit Tests** (22 tests):
- Password schema validation
- Password hashing and verification
- User update operations

**Integration Tests** (25 tests):
- Profile retrieval (`GET /users/me`)
- Profile updates (`PUT /users/me/profile`)
- Password changes (`PUT /users/me/password`)
- Validation of duplicate usernames/emails
- Authentication and authorization

**E2E Tests** (21 tests):
- Complete user workflows (login → profile → update → logout)
- Form submission and validation
- Error and success message display
- Password visibility toggle
- Username and email updates

## 🔍 Manual Verification via OpenAPI

FastAPI provides an interactive API documentation interface (Swagger UI) that allows you to manually test the API endpoints.

1. **Start the Application**:
   Ensure your application is running locally or via Docker.
   ```bash
   # Locally
   uvicorn app.main:app --reload
   
   # Or via Docker
   docker-compose up --build
   ```

2. **Access Swagger UI**:
   Open your browser and navigate to:
   [http://localhost:8000/docs](http://localhost:8000/docs)

3. **Test Profile Endpoints**:
   - **Authorize**: Use the `/users/login` endpoint to get a token, then click the "Authorize" button
   - **Get Profile**: `GET /users/me` - Retrieve current user profile
   - **Update Profile**: `PUT /users/me/profile` - Update user information
   - **Change Password**: `PUT /users/me/password` - Change password with validation
   - **Try it out**: Click on an endpoint, fill parameters, and click "Execute"
   - **View Response**: Check the "Server response" section for status code and body
```

## 🐳 Docker Hub Repository

The Docker image for this project is available on Docker Hub:
[happymask13/assignment14](https://hub.docker.com/repository/docker/happymask13/assignment14/general)

This is the same Docker image as Assignment 13, extended with:
- **Assignment 14**: BREAD (Browse, Read, Edit, Add, Delete) operations for calculator functions
- **Additional Feature**: User profile management system with password change functionality

To pull and run the image:
```bash
docker pull happymask13/assignment14:latest
docker run -p 8000:8000 happymask13/assignment14:latest
```

Or use docker-compose:
```bash
docker-compose up --build
```

The application will be available at: [http://localhost:8000](http://localhost:8000)

---

# � User Profile & Password Management Feature

## Overview

This feature extends Assignment 14 with comprehensive user profile management capabilities, allowing users to:
- **View Profile**: Access current user information (first name, last name, username, email, account status)
- **Update Profile**: Change first name, last name, username, or email
- **Change Password**: Securely change password with strength validation
- **Real-time Validation**: Client-side and server-side validation with error messages

## API Endpoints

### Profile Management

**Get Current User Profile**
```bash
GET /users/me
Authorization: Bearer <token>
```
Returns current authenticated user's profile data.

**Update User Profile**
```bash
PUT /users/me/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "email": "john@example.com"
}
```
Updates user information with validation for duplicate usernames/emails.

**Change Password**
```bash
PUT /users/me/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!",
  "confirm_new_password": "NewPassword456!"
}
```
Changes password with strength requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)

## Frontend Pages

### Profile Page (`/profile`)

Responsive profile management page with:
- **Profile Information Section**: Display and edit user details
- **Account Status**: Shows if account is active/inactive
- **Member Since**: Display account creation date
- **Password Change Form**: Secure password changing interface
- **Form Validation**: Real-time feedback with error/success messages
- **Password Visibility Toggle**: Show/hide password inputs

## Validation

### Client-Side Validation
- HTML5 validation for required fields
- Email format validation
- Username length requirements (3+ characters)
- Password strength validation
- Password confirmation matching
- Real-time error messages with auto-dismiss

### Server-Side Validation
- Duplicate username/email detection with proper error handling
- Password hashing with bcrypt
- Current password verification before change
- Password strength enforcement
- UUID-based unique constraint handling

## Testing

### Test Coverage: 68 Tests (100% Passing)

**Unit Tests (22 tests)** - `tests/unit/test_user_profile.py`
- Password schema validation
- Password hashing and verification
- User update operations
- Password strength validation

**Integration Tests (25 tests)** - `tests/integration/test_profile_endpoints.py`
- Profile retrieval endpoint
- Profile update endpoint
- Password change endpoint
- Duplicate detection
- Authentication and authorization
- Database persistence

**E2E Tests (21 tests)** - `tests/e2e/test_profile_flow.py`
- Complete user workflows
- Form submission and validation
- Error and success message display
- Password visibility toggle
- Logout and re-login with new credentials
- Profile data persistence

Run profile tests:
```bash
pytest tests/unit/test_user_profile.py tests/integration/test_profile_endpoints.py tests/e2e/test_profile_flow.py -v
```

---



## 🧩 1. Install Homebrew (Mac Only)

> Skip this step if you're on Windows.

Homebrew is a package manager for macOS.  
You’ll use it to easily install Git, Python, Docker, etc.

**Install Homebrew:**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Verify Homebrew:**

```bash
brew --version
```

If you see a version number, you're good to go.

---

# 🧩 2. Install and Configure Git

## Install Git

- **MacOS (using Homebrew)**

```bash
brew install git
```

- **Windows**

Download and install [Git for Windows](https://git-scm.com/download/win).  
Accept the default options during installation.

**Verify Git:**

```bash
git --version
```

---

## Configure Git Globals

Set your name and email so Git tracks your commits properly:

```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

Confirm the settings:

```bash
git config --list
```

---

## Generate SSH Keys and Connect to GitHub

> Only do this once per machine.

1. Generate a new SSH key:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

(Press Enter at all prompts.)

2. Start the SSH agent:

```bash
eval "$(ssh-agent -s)"
```

3. Add the SSH private key to the agent:

```bash
ssh-add ~/.ssh/id_ed25519
```

4. Copy your SSH public key:

- **Mac/Linux:**

```bash
cat ~/.ssh/id_ed25519.pub | pbcopy
```

- **Windows (Git Bash):**

```bash
cat ~/.ssh/id_ed25519.pub | clip
```

5. Add the key to your GitHub account:
   - Go to [GitHub SSH Settings](https://github.com/settings/keys)
   - Click **New SSH Key**, paste the key, save.

6. Test the connection:

```bash
ssh -T git@github.com
```

You should see a success message.

---

# 🧩 3. Clone the Repository

Now you can safely clone the course project:

```bash
git clone <repository-url>
cd <repository-directory>
```

---

# 🛠️ 4. Install Python 3.10+

## Install Python

- **MacOS (Homebrew)**

```bash
brew install python
```

- **Windows**

Download and install [Python for Windows](https://www.python.org/downloads/).  
✅ Make sure you **check the box** `Add Python to PATH` during setup.

**Verify Python:**

```bash
python3 --version
```
or
```bash
python --version
```

---

## Create and Activate a Virtual Environment

(Optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate.bat  # Windows
```

### Install Required Packages

```bash
pip install -r requirements.txt
```

---

# 🐳 5. (Optional) Docker Setup

> Skip if Docker isn't used in this module.

## Install Docker

- [Install Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
- [Install Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

## Build Docker Image

```bash
docker build -t <image-name> .
```

## Run Docker Container

```bash
docker run -it --rm <image-name>
```

---

# 🚀 6. Running the Project

- **Without Docker**:

```bash
python main.py
```

(or update this if the main script is different.)

- **With Docker**:

```bash
docker run -it --rm <image-name>
```

---

# 📝 7. Submission Instructions

After finishing your work:

```bash
git add .
git commit -m "Complete Module X"
git push origin main
```

Then submit the GitHub repository link as instructed.

---

# 🔥 Useful Commands Cheat Sheet

| Action                         | Command                                          |
| ------------------------------- | ------------------------------------------------ |
| Install Homebrew (Mac)          | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| Install Git                     | `brew install git` or Git for Windows installer |
| Configure Git Global Username  | `git config --global user.name "Your Name"`      |
| Configure Git Global Email     | `git config --global user.email "you@example.com"` |
| Clone Repository                | `git clone <repo-url>`                          |
| Create Virtual Environment     | `python3 -m venv venv`                           |
| Activate Virtual Environment   | `source venv/bin/activate` / `venv\Scripts\activate.bat` |
| Install Python Packages        | `pip install -r requirements.txt`               |
| Build Docker Image              | `docker build -t <image-name> .`                |
| Run Docker Container            | `docker run -it --rm <image-name>`               |
| Push Code to GitHub             | `git add . && git commit -m "message" && git push` |

---

# 📋 Notes

- Install **Homebrew** first on Mac.
- Install and configure **Git** and **SSH** before cloning.
- Use **Python 3.10+** and **virtual environments** for Python projects.
- **Docker** is optional depending on the project.

---

# 📎 Quick Links

- [Homebrew](https://brew.sh/)
- [Git Downloads](https://git-scm.com/downloads)
- [Python Downloads](https://www.python.org/downloads/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [GitHub SSH Setup Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

---

## 🧠 Polymorphic Calculation Model - Design Overview

### Architecture

This project implements **SQLAlchemy polymorphic inheritance** for flexible calculation types using the single-table inheritance pattern.

#### Polymorphic Models (`app/models/calculation.py`)

**Base Class:**
```python
class Calculation(Base):
    __tablename__ = "calculations"
    type = Column(String(50))  # Discriminator column
    inputs = Column(ARRAY(Float))  # PostgreSQL array of floats
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    
    __mapper_args__ = {
        "polymorphic_identity": "calculation",
        "polymorphic_on": type,
    }
```

**Subclasses:**
- `Addition` - Sums all inputs: `sum(inputs)`
- `Subtraction` - First minus rest: `inputs[0] - sum(inputs[1:])`
- `Multiplication` - Product of all: `product(inputs)`
- `Division` - First divided by rest: `inputs[0] / inputs[1] / ...`

**Factory Pattern:**
```python
# Returns appropriate subclass automatically
calc = Calculation.create('addition', user_id, [1, 2, 3])
assert isinstance(calc, Addition)
assert calc.get_result() == 6
```

#### Pydantic Schemas (`app/schemas/calculation.py`)

**Validation Schemas:**
- `CalculationType` - Enum: `addition`, `subtraction`, `multiplication`, `division`
- `CalculationBase` - Base with type normalization and division-by-zero validation (LBYL)
- `CalculationCreate` - For creating calculations (includes optional `user_id`)
- `CalculationUpdate` - For updates (all fields optional)
- `CalculationResponse` - For API responses (includes computed `result`, no validation)

**Key Features:**
- Field validators for case-insensitive type normalization
- Model validators for cross-field validation
- Division by zero prevention at schema level (LBYL approach)
- Minimum 2 inputs requirement
- Clear error messages

### Design Decisions

**Why polymorphic inheritance?**
- Single table stores all calculation types efficiently
- SQLAlchemy automatically resolves correct subclass on query
- Each subclass implements `get_result()` with type-specific logic
- Type-safe: `isinstance()` checks work correctly
- Easy to extend with new operation types

**Why compute result on-demand?**
- Avoids storing stale/redundant data
- Keeps database schema simple
- Result is always correct for current inputs
- If performance becomes issue, can add caching layer

**Why array of inputs instead of a/b?**
- Supports operations on multiple values (e.g., `1 + 2 + 3 + 4`)
- More flexible for future extensions
- Matches real-world calculator behavior

**LBYL vs EAFP:**
- **LBYL (schemas)**: Check division by zero before creation
- **EAFP (models)**: Catch errors during `get_result()` execution
- Both approaches demonstrated per Module 11 requirements

### Testing Strategy

**Polymorphic Model Tests** (22 tests):
- Individual operations (addition, subtraction, multiplication, division)
- Factory pattern (correct subclass creation, case-insensitive)
- Polymorphic behavior (mixed types in queries, type resolution)
- Edge cases (empty inputs, division by zero, large numbers)

**Schema Validation Tests** (29 tests):
- Valid data acceptance for all types
- Invalid data rejection with clear errors
- Type normalization and case-insensitivity
- Division by zero prevention (LBYL)
- Minimum inputs validation
- Update schema optional fields behavior

**Coverage:** 96.47% overall, 94% for calculation models, 88% for schemas

### Database Schema

```sql
CREATE TABLE calculations (
    id UUID PRIMARY KEY,
    type VARCHAR(50) NOT NULL,  -- Discriminator: 'addition', 'subtraction', etc.
    inputs FLOAT[] NOT NULL,     -- PostgreSQL array
    user_id UUID REFERENCES users(id)
);
```

### Usage Examples

**Creating calculations:**
```python
# Using factory (recommended)
calc = Calculation.create('addition', user_id=None, inputs=[1, 2, 3])
result = calc.get_result()  # Returns 6

# Direct instantiation
calc = Addition(user_id=None, inputs=[10, 5])
result = calc.get_result()  # Returns 15

# With Pydantic validation
from app.schemas.calculation import CalculationCreate
schema = CalculationCreate(type='division', inputs=[10, 2], user_id=None)
calc = Calculation.create(schema.type, schema.user_id, schema.inputs)
```

**Querying calculations:**
```python
# All calculations (returns mixed subclass instances)
calcs = session.query(Calculation).all()

# Filter by type
additions = session.query(Addition).all()

# Polymorphic behavior maintained
for calc in calcs:
    print(f"{type(calc).__name__}: {calc.get_result()}")
```

For complete implementation details, see:
- `app/models/calculation.py` - Polymorphic models
- `app/schemas/calculation.py` - Pydantic schemas  
- `tests/integration/test_calculation.py` - Model tests
- `tests/integration/test_calculation_schema.py` - Schema tests
- `MODULE11_SUMMARY.md` - Comprehensive summary