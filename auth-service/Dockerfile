# Multi-stage build to reduce final image size
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies for compiling native extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (required for pydantic-core)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage - runtime image
FROM python:3.12-slim

# Create non-root user for security
RUN groupadd -r authservice && useradd -r -g authservice authservice

WORKDIR /app

# Install only runtime dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy the installed packages from builder stage
COPY --from=builder /root/.local /home/authservice/.local

# Make sure scripts in .local are usable:
ENV PATH=/home/authservice/.local/bin:$PATH

# Copy application code
COPY . .

# Create required directories and set permissions
RUN mkdir -p /app/logs /tmp/auth-service \
    && chown -R authservice:authservice /app /home/authservice \
    && chmod 755 /app

# Switch to non-root user
USER authservice

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f -H "Accept: application/json" http://localhost:8000/status || exit 1

# Environment variables for production optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Enhanced command with production settings
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--limit-max-requests", "1000", "--timeout-keep-alive", "30", "--access-log", "--log-level", "info"]