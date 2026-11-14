# C6 — Deploy
**Paste this entire prompt into Claude Code (antygravity) as your first message for this chunk.**
**Model: Claude Sonnet 4.6 Thinking**
**Prerequisite: C5 exit gate fully green.**
**⚠️ Several steps in this chunk require YOU to do things manually. See the MANUAL STEPS section.**

---

## PROMPT (copy everything below this line)

---

You are a senior DevOps engineer. We are building **MailCheck**. This is **Chunk 6 – Deploy**: optimise the Dockerfile for the smallest possible image, verify the GitHub Actions CI pipeline is correct and passing, and prepare the Render.com deployment configuration.

### What to do in this chunk

#### 1. Final Dockerfile (optimised multi-stage)

Replace `Dockerfile` at the project root with this:

```dockerfile
# ── Stage 1: build React ───────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --prefer-offline
COPY frontend/ .
RUN npm run build          # output: /build/backend/static

# ── Stage 2: Python app ────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime
# Security: don't run as root
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser
WORKDIR /app
# Install deps first (layer cache)
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir . && \
    pip cache purge
# Copy app code
COPY backend/ .
# Copy built frontend
COPY --from=frontend-build /build/backend/static ./static
# Drop to non-root user
USER appuser
EXPOSE 8000
# Health check for Render
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--access-log"]
```

#### 2. `.dockerignore`

```
node_modules/
frontend/.vite/
frontend/dist/
backend/static/
.git/
.env
*.egg-info/
__pycache__/
.mypy_cache/
.ruff_cache/
.pytest_cache/
backend/tests/
*.md
.github/
```

#### 3. `render.yaml` (Infrastructure-as-Code for Render)

```yaml
services:
  - type: web
    name: mailcheck
    env: docker
    plan: free
    dockerfilePath: ./Dockerfile
    envVars:
      - key: ALLOW_ORIGINS
        sync: false          # you will fill this in the dashboard after first deploy
      - key: MAX_CSV_BYTES
        value: "2097152"
      - key: MAX_CSV_ROWS
        value: "1000"
      - key: MAX_RUNNING_JOBS
        value: "2"
      - key: MAX_WAITING_JOBS
        value: "3"
      - key: JOB_RESULT_TTL_SECONDS
        value: "900"
      - key: FAILED_JOB_TTL_SECONDS
        value: "60"
      - key: MAX_JOB_LIFETIME_SECONDS
        value: "1800"
      - key: DNS_TIMEOUT_SECONDS
        value: "3"
      - key: DNS_CONCURRENCY
        value: "20"
      - key: RATE_SINGLE_PER_MIN
        value: "20"
      - key: RATE_BULK_PER_HOUR
        value: "5"
      - key: MEMORY_GUARD_MB
        value: "380"
    healthCheckPath: /api/health
```

#### 4. Verify `.github/workflows/ci.yml`

The CI file from C0 must have this structure. Update it if anything is missing:

```yaml
name: CI
on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["main"]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -e "backend[dev]"
      - run: ruff check backend/app backend/tests
      - run: mypy backend/app
      - run: pytest backend/tests -v --tb=short

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: cd frontend && npm ci
      - run: cd frontend && npm test -- --reporter=verbose
      - run: cd frontend && npm run build

  docker-build:
    runs-on: ubuntu-latest
    needs: [backend, frontend]
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t mailcheck:ci .
      - name: Smoke-test container
        run: |
          docker run -d --name mailcheck-test -p 8000:8000 mailcheck:ci
          sleep 5
          curl -f http://localhost:8000/api/health
          docker stop mailcheck-test
```

#### 5. `README.md` (minimal, in project root)

```markdown
# MailCheck

Privacy-first email validation — single address and CSV bulk.

## Stack

- Backend: Python 3.12, FastAPI, dnspython, email-validator
- Frontend: React 18, TypeScript, Vite, plain CSS
- Hosting: Render free web service

## Run locally

```bash
# Backend
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Run tests

```bash
cd backend && pytest -v
cd frontend && npm test
```

## Docker

```bash
docker build -t mailcheck .
docker run -p 8000:8000 --env ALLOW_ORIGINS=http://localhost:8000 mailcheck
```

## Deploy

Deployed automatically to Render on every push to `main`.
See `render.yaml` for configuration.
```
```

---

### ⚠️ MANUAL STEPS REQUIRED (you must do these yourself)

The AI cannot do these for you. Work through them in order.

#### M4: Create Render account

1. Go to **https://render.com** and click "Get Started for Free".
2. Sign up with your GitHub account (easiest — links your repos automatically).
3. No credit card required for the free tier.

#### M5: Connect your GitHub repo to Render

1. In the Render dashboard, click **New → Web Service**.
2. Under "Connect a repository", select your `mail-validator` GitHub repo.
3. Render detects the `Dockerfile` automatically.
4. Click **Continue**.
5. Settings:
   - **Name:** `mailcheck`
   - **Region:** nearest to you
   - **Branch:** `main`
   - **Runtime:** Docker
   - **Plan:** Free
6. Click **Create Web Service** (let it build the first time — may take 5–10 minutes).

#### M6: Set environment variables in Render

After the first deploy completes:
1. Go to your service → **Environment** tab.
2. Add these variables (click **Add Environment Variable** for each):

| Key | Value |
|-----|-------|
| `ALLOW_ORIGINS` | `https://your-app-name.onrender.com` (use YOUR actual Render URL) |
| `MAX_CSV_BYTES` | `2097152` |
| `MAX_CSV_ROWS` | `1000` |
| `MAX_RUNNING_JOBS` | `2` |
| `MAX_WAITING_JOBS` | `3` |
| `JOB_RESULT_TTL_SECONDS` | `900` |
| `FAILED_JOB_TTL_SECONDS` | `60` |
| `MAX_JOB_LIFETIME_SECONDS` | `1800` |
| `DNS_TIMEOUT_SECONDS` | `3` |
| `DNS_CONCURRENCY` | `20` |
| `RATE_SINGLE_PER_MIN` | `20` |
| `RATE_BULK_PER_HOUR` | `5` |
| `MEMORY_GUARD_MB` | `380` |

3. Click **Save Changes** — Render will redeploy automatically.

#### M7: Verify the live deployment

After the second deploy completes (the one that includes your env vars):

1. Open your Render URL: `https://your-app-name.onrender.com`
2. Verify: the MailCheck UI loads.
3. Open: `https://your-app-name.onrender.com/api/health` → `{"status":"ok",...}`
4. Test single check with `user@gmail.com` → result appears.
5. Upload a small CSV → job completes and results display.

---

### Local Docker test (run before pushing)

```powershell
# Build the image
docker build -t mailcheck:local .

# Run it (replace the ALLOW_ORIGINS value with your Render URL later)
docker run -d --name mailcheck-local `
  -p 8000:8000 `
  -e ALLOW_ORIGINS="http://localhost:8000" `
  mailcheck:local

# Verify
Start-Sleep 5
Invoke-WebRequest http://localhost:8000/api/health

# Stop
docker stop mailcheck-local
docker rm mailcheck-local
```

Expected response: `{"status":"ok","ts":<timestamp>}`

---

### Exit gate for C6

- [ ] `docker build -t mailcheck .` completes without errors
- [ ] Local Docker run → `/api/health` returns 200
- [ ] GitHub Actions CI: all three jobs (backend, frontend, docker-build) are green on the latest push
- [ ] Render: service deployed and healthy (green dot in dashboard)
- [ ] `https://your-app-name.onrender.com/api/health` → 200
- [ ] MailCheck UI loads at the Render URL
- [ ] Git commit: `git commit -m "C6: Dockerfile optimised, render.yaml, CI docker-build job"`
