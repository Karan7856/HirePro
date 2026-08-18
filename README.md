# HirePro AI

AI-powered placement and recruitment management platform connecting students, recruiters, companies, jobs, and applications.

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Validation | Pydantic v2 |
| Configuration | pydantic-settings |
| Server | Uvicorn |
| Testing | pytest |

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Karan7856/HirePro.git
cd HirePro
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up environment variables

```bash
copy .env.example .env
```

Edit `.env` with your configuration values if needed.

### 6. Run the development server

```bash
uvicorn app.main:app --reload
```

The server starts at `http://127.0.0.1:8000`.

### 7. Verify the health endpoint

Open in browser or use curl:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### 8. Access API documentation

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Running Tests

```bash
pytest -v
```

## Project Structure

```
HIREPRO/
├── app/
│   ├── __init__.py          # App package
│   ├── main.py              # FastAPI application instance
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Application settings (pydantic-settings)
│   └── api/
│       └── __init__.py      # Future API routers
├── tests/
│   ├── __init__.py
│   └── test_health.py       # Health endpoint tests
├── docs/
│   ├── architecture-proposal.md
│   └── requirements.md
├── .env.example             # Environment variable template
├── .gitignore
├── README.md
└── requirements.txt
```

## License

Private — All rights reserved.
