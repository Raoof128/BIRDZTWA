# Browser Isolation System - Docker Image
# Production-ready containerized deployment

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install core system dependencies; playwright will handle browser-specific libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    gnupg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and system requirements
RUN playwright install-deps chromium
RUN playwright install chromium

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs reports

# Create non-root user for security
RUN useradd -m -u 1000 isolation && \
    chown -R isolation:isolation /app

USER isolation

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')"

# Default command: run API server
CMD ["python", "api/server.py"]

