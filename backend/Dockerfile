# ============================================
# VESTIGIUM — Backend Dockerfile
# ============================================
# Multi-stage build for production deployment

FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- Dependencies Stage ----
FROM base AS dependencies

COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[all]" 2>/dev/null || pip install --no-cache-dir .

# ---- Production Stage ----
FROM base AS production

COPY --from=dependencies /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

COPY . .

RUN mkdir -p /app/data /app/uploads /app/backups /app/plugins /app/logs

RUN addgroup --system --gid 1001 vestigium && \
    adduser --system --uid 1001 --ingroup vestigium vestigium && \
    chown -R vestigium:vestigium /app
USER vestigium

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health')" || exit 1

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
