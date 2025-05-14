#!/bin/bash

set -a
source /app/.env
set +a

service cron start

CRON_PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
CRON_JOB="@weekly $BACKUP_PATH"

if crontab -l 2>/dev/null | grep -q "$BACKUP_PATH"; then
    echo "Cron job zaten var."
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Yeni cron job eklendi: $CRON_JOB"
fi

exec flask run --host=0.0.0.0
