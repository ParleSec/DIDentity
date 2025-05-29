FROM python:3.13.3-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create necessary directories with proper permissions
RUN mkdir -p templates static && \
    chmod 755 templates static

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy static and template files first
COPY static/ static/
COPY templates/ templates/
COPY dashboard.html templates/

# Copy application files
COPY main.py .

# Set proper permissions
RUN chmod 644 static/* templates/* main.py

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]