# C0 — Foundation
**Paste this entire prompt into Claude Code (antygravity) as your first message for this chunk.**
**Model: Claude Sonnet 4.6 Thinking**
**Prerequisite: Python 3.12, Node 20, Git installed. Empty repo at P:\mail_validator.**

---

## PROMPT (copy everything below this line)

---

You are a senior Python and TypeScript engineer. We are building **MailCheck**, a privacy-first email validation web app. This is **Chunk 0 – Foundation**: create the entire project skeleton so that every later chunk has a stable base to build on.

### Project constraints (read before writing any code)

- One Docker container, one uvicorn worker, no database, no Redis, no Celery, no Nginx.
- Backend: Python 3.12, FastAPI, pydantic-settings, uvicorn.
- Frontend: React 18 + TypeScript + Vite, plain CSS, **no Tailwind, no UI kit, no state library**.
- Runtime backend deps (exactly 6): `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `email-validator`, `dnspython`, `python-multipart`.
- Dev/test deps: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`.
- Frontend runtime deps: `react`, `react-dom` only.
- Dev frontend deps: `vite`, `@vitejs/plugin-react`, `typescript`, `@types/react`, `@types/react-dom`, `vitest`, `@testing-library/react`, `@testing-library/user-event`.
- Project root: `P:\mail_validator` (Windows path; use forward slashes in all file paths inside the project).

### What to create in this chunk

Create **every file listed below** with the exact content described. Do not skip any file.

#### 1. `backend/pyproject.toml`

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "mailcheck-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "pydantic-settings>=2.5",
    "email-validator>=2.2",
    "dnspython>=2.7",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
    "ruff>=0.7",
    "mypy>=1.12",
]

[tool.ruff]
target-version = "py312"
line-length = 100
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

#### 2. `backend/app/__init__.py` — empty

#### 3. `backend/app/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    allow_origins: str = "http://localhost:5173"
    max_csv_bytes: int = 2_097_152        # 2 MB
    max_csv_rows: int = 1_000
    max_running_jobs: int = 2
    max_waiting_jobs: int = 3
    job_result_ttl_seconds: int = 900     # 15 min after READY
    failed_job_ttl_seconds: int = 60      # 1 min after FAILED
    max_job_lifetime_seconds: int = 1_800 # 30-min hard cap
    dns_timeout_seconds: float = 3.0
    dns_concurrency: int = 20
    rate_single_per_min: int = 20
    rate_bulk_per_hour: int = 5
    memory_guard_mb: int = 380            # [verify in C7]

settings = Settings()
```

#### 4. `backend/app/main.py`

```python
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MailCheck API", version="0.1.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins.split(","),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Job-Key"],
)

app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup() -> None:
    logger.info("MailCheck starting up")
```

#### 5. `backend/app/api/__init__.py` — empty

#### 6. `backend/app/api/routes.py`

```python
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "ts": int(time.time())})
```

#### 7. `backend/app/api/schemas.py`

```python
from pydantic import BaseModel

class ErrorEnvelope(BaseModel):
    error: str
    code: str
    detail: str = ""
```

#### 8. `backend/app/core/__init__.py` — empty
#### 9. `backend/app/services/__init__.py` — empty

#### 10. `backend/tests/__init__.py` — empty

#### 11. `backend/tests/test_health.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_returns_ok() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert isinstance(body["ts"], int)
```

#### 12. `frontend/package.json`

```json
{
  "name": "mailcheck-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "vitest": "^2.0.0"
  }
}
```

#### 13. `frontend/vite.config.ts`

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: { outDir: "../backend/static", emptyOutDir: true },
  server: {
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
  test: { environment: "jsdom" },
});
```

#### 14. `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["src"]
}
```

#### 15. `frontend/index.html`

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MailCheck</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

#### 16. `frontend/src/main.tsx`

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

#### 17. `frontend/src/App.tsx`

```tsx
export default function App() {
  return (
    <main className="app">
      <h1>MailCheck</h1>
      <p>Email validation — coming soon.</p>
    </main>
  );
}
```

#### 18. `frontend/src/index.css`

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; background: #0f0f0f; color: #e8e8e8; }
.app { max-width: 720px; margin: 4rem auto; padding: 0 1rem; }
h1 { font-size: 2rem; margin-bottom: 0.5rem; }
```

#### 19. `Dockerfile` (multi-stage)

```dockerfile
# ── Stage 1: build React ──────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN npm run build          # output goes to /build/backend/static

# ── Stage 2: Python app ───────────────────────────────────────────────────────
FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir --break-system-packages ".[dev]" 2>/dev/null || \
    pip install --no-cache-dir .
COPY backend/ .
COPY --from=frontend-build /build/backend/static ./static
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

Add static-file serving to `backend/app/main.py` after the CORS middleware:

```python
from fastapi.staticfiles import StaticFiles
import os
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
```

#### 20. `.github/workflows/ci.yml`

```yaml
name: CI
on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e "backend[dev]"
      - run: ruff check backend/app backend/tests
      - run: mypy backend/app
      - run: pytest backend/tests -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci
      - run: cd frontend && npm test
      - run: cd frontend && npm run build
```

#### 21. `.gitignore`

```
__pycache__/
*.py[cod]
.env
*.egg-info/
.mypy_cache/
.ruff_cache/
.pytest_cache/
backend/static/
node_modules/
dist/
frontend/.vite/
```

#### 22. `.env.example`

```
ALLOW_ORIGINS=http://localhost:5173
MAX_CSV_BYTES=2097152
MAX_CSV_ROWS=1000
DNS_TIMEOUT_SECONDS=3
```

---

### How to run locally (after generating files)

```powershell
# Terminal 1 — backend
cd P:\mail_validator\backend
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd P:\mail_validator\frontend
npm install
npm run dev
```

Open `http://localhost:5173` → you should see "MailCheck — Email validation — coming soon."
Open `http://localhost:8000/api/health` → `{"status":"ok","ts":<timestamp>}`.

---

### Tests to run

```powershell
cd P:\mail_validator\backend
pytest tests/ -v
```

**Expected output:**

```
tests/test_health.py::test_health_returns_ok  PASSED
1 passed in <1s
```

---

### Exit gate for C0

All of these must be true before moving to C1:

- [ ] `pytest tests/ -v` → 1 passed, 0 failed
- [ ] `ruff check app tests` → no issues
- [ ] `npm run build` completes without errors
- [ ] `http://localhost:8000/api/health` returns `{"status":"ok",...}`
- [ ] `http://localhost:5173` renders "MailCheck" heading
- [ ] Git commit made: `git commit -m "C0: project skeleton and health endpoint"`
