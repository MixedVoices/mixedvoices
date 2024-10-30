# Dockerfile
FROM python:3.10-slim as base
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set common environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=mixedvoices.server
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5001

EXPOSE 5001

# Development stage
FROM base as development
# Keep this stage minimal as we'll mount the code directory

# Production stage
FROM base as production
# Copy the application code
COPY . .
# Install the package
RUN pip install -e .