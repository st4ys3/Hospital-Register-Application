#!/bin/bash

service cron start

BACKUP_PATH="/app/backup.sh"

CRON_JOB="@weekly $BACKUP_PATH"

if crontab -l 2>/dev/null | grep -q "$CRON_JOB"; then
:
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "$CRON_JOB"
    echo "Cron job başarıyla eklendi:"
fi

exec flask run --host=0.0.0.0
