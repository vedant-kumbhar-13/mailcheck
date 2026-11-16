# MailCheck

A privacy-first email validation web app.

## Stack

- **Backend**: Python 3.12, FastAPI, uvicorn, pydantic-settings, dnspython, email-validator
- **Frontend**: React 18 + TypeScript + Vite (plain CSS, no UI kit)

## Features

- ✅ Single email check (syntax, DNS/MX, disposable, role-based detection)
- ✅ Bulk CSV upload (up to 1,000 rows, 2 MB)
- ✅ Async job processing with live progress bar
- ✅ Paginated results table with status filters
- ✅ CSV download of results
- ✅ Per-IP rate limiting (no Redis)
- ✅ No database, no external APIs, privacy-first

## Quick Start

```powershell
# Backend
cd backend
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/validations/single` | Validate a single email |
| POST | `/api/validations/bulk` | Upload CSV for bulk validation |
| GET | `/api/jobs/{id}` | Job status |
| GET | `/api/jobs/{id}/results` | Paginated results |
| GET | `/api/jobs/{id}/download` | Download results as CSV |
| DELETE | `/api/jobs/{id}` | Delete job |

## Running Tests

```powershell
cd backend
.venv\Scripts\pytest tests/ -v
```
