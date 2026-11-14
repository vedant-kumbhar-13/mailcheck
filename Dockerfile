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
