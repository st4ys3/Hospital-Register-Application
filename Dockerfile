FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    default-mysql-client \
    default-libmysqlclient-dev \
    build-essential \
    cron \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x backup.sh crontab.sh

RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

ENV FLASK_APP=app.py
ENV FLASK_DEBUG=False
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/app/crontab.sh"]
