# ==============================================================
# Dockerfile — PestGuard AI Backend
# Department 2 Capstone · BAU 2026
# ==============================================================
# Multi-stage build for a lean production image.
#
# Build:  docker build -t pestguard-api .
# Run:    docker run -p 8000:8000 --env-file .env pestguard-api
# ==============================================================

# ── Stage 1: Builder ──────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build deps for native wheels (chromadb, numpy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements-render.txt requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────
FROM python:3.11-slim

LABEL maintainer="Department 2 — BAU Capstone 2026"
LABEL description="PestGuard AI — Deep Learning Insect Pest Recognition API"
LABEL version="0.5.0"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Runtime system deps (none needed for pure-python stack)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r pestguard && useradd -r -g pestguard -d /app pestguard

# Copy application code
COPY main.py mock_api.py economics.py risk_engine.py ./
COPY agent/ agent/
COPY rag/ rag/
COPY vlm/ vlm/
COPY weather/ weather/
COPY core/ core/
COPY static/ static/
COPY data/documents/ data/documents/
COPY data/chroma_db/ data/chroma_db/
COPY .env.example .env.example

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh

# Create runtime directories (chroma_db will be built at first startup)
RUN mkdir -p uploads logs data/chroma_db && \
    sed -i 's/\r$//' /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh && \
    chown -R pestguard:pestguard /app

# Switch to non-root user
USER pestguard

# Expose the API port
EXPOSE 8000

# Health check — verifies the API is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Entrypoint builds index on first run, then starts server
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
