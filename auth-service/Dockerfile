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

WORKDIR /app

# Copy the installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]