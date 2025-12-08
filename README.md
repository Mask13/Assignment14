# 📦 Assignment 13 - Login/Registration with Client-Side Validation & Playwright E2E

### 🎯 Key Features
- **Polymorphic Models**: Single-table inheritance with `Calculation` base class and `Addition`, `Subtraction`, `Multiplication`, `Division` subclasses
- **Factory Pattern**: `Calculation.create()` returns appropriate subclass based on type
- **Pydantic Validation**: Comprehensive schemas with LBYL (Look Before You Leap) approach
- **96% Test Coverage**: 137 tests covering models, schemas, auth, and edge cases
- **CI/CD Pipeline**: Automated testing with 95% coverage threshold enforcement
- **User Registration**: Salted passwords with user registration and login endpoints

### 📊 Test Results
```
✅ 144 tests passed, 1 skipped
✅ Coverage: 97.38% (exceeds 95% threshold)
✅ All polymorphic behaviors verified
✅ All validation rules tested
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
# Run all tests with coverage report (enforces 95% minimum)
pytest

# Run specific test suites
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Run polymorphic calculation tests
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

To run only the integration tests:
```bash
pytest tests/integration/ -v
```

## 🔍 Manual Verification via OpenAPI

FastAPI provides an interactive API documentation interface (Swagger UI) that allows you to manually test the API endpoints.

1. **Start the Application**:
   Ensure your application is running locally or via Docker.
   ```bash
   # Locally
   uvicorn main:app --reload
   
   # Or via Docker
   docker-compose up --build
   ```

2. **Access Swagger UI**:
   Open your browser and navigate to:
   [http://localhost:8000/docs](http://localhost:8000/docs)

3. **Test Endpoints**:
   - **Authorize**: If testing protected endpoints, first use the `/users/login` endpoint to get a token, then click the "Authorize" button at the top right and enter the token.
   - **Try it out**: Click on an endpoint (e.g., `POST /calculate/add`), click "Try it out", enter the required parameters, and click "Execute".
   - **View Response**: Check the "Server response" section to see the status code and response body.
```

## 🐳 Docker Hub Repository

The Docker image for this project is available on Docker Hub:
[happymask13/assignment13](https://hub.docker.com/repository/docker/happymask13/assignment13/general)

To pull and run the image:
```bash
docker pull happymask13/assignment13:latest
docker run -p 8000:8000 happymask13/assignment13:latest
```

---

# 🔧 Development Setup

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