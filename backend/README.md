# ShebaBondhu Backend

FastAPI modular monolith backend for the ShebaBondhu digital health assistant for elderly patients in Bangladesh.

## Prerequisites

- Python 3.12+
- Firebase service account credentials JSON (for production or non-mocked local Firestore access)

## Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Populate the environment variables in `.env`:
   - `FIREBASE_PROJECT_ID`: Your Firebase project ID
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to your `serviceAccountKey.json`
   - `APP_ENV`: `development` | `staging` | `production`
   - `CRON_SECRET`: Secret token for protecting internal cron tasks

> **Important:** Never commit `.env` or `serviceAccountKey.json` to version control. Both are ignored in `.gitignore`.

## Installation

Create and activate a virtual environment, then install pinned dependencies:

### Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Server

Start the development server with hot-reload enabled:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running:
- **API Base URL:** `http://localhost:8000`
- **Health Check:** `http://localhost:8000/health`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Running Tests

Run the test suite with `pytest`:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

## Implemented Architecture (Slice 0.1 & 0.2 Core)

- **`app/main.py`**: FastAPI application entry point with request-logging middleware injecting `request_id` into every request header (`X-Request-ID`), request state, and every log line via a structured logging filter.
- **`app/core/config.py`**: Pydantic `BaseSettings` reading environment variables (`FIREBASE_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `APP_ENV`, `CRON_SECRET`).
- **`app/core/firebase.py`**: Firebase Admin SDK singleton initializer and Firestore client provider.
- **`app/core/errors.py`**: Standardized domain exception hierarchy (`ShebaBondhuError`, `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `NotRegisteredError`, `ValidationError`, `RateLimitError`, `LLMError`) with global FastAPI error handlers returning the unified error envelope.
- **`app/core/security.py`**:
  - `get_firebase_user`: Verifies the Bearer ID token only.
  - `get_current_user`: Verifies token and loads the Firestore user document; raises `404 NOT_REGISTERED` (not 401) if unregistered.
  - `require_role(*roles)`: Returns `403 FORBIDDEN` if the authenticated user lacks the required role.
  - `UserRepository`: Repository for fetching user records by UID.
- **`app/modules/health/router.py`**: Public `GET /health` endpoint reporting system status, version, Firestore connectivity, and timestamp.
