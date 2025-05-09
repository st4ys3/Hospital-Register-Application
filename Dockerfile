FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including MySQL dev packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-mysql-client \
    default-libmysqlclient-dev \
    build-essential \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Make scripts executable
RUN chmod +x backup.sh crontab.sh

# Create a non-root user
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=False
ENV PYTHONUNBUFFERED=1

# Run the application
ENTRYPOINT ["/app/crontab.sh"]
