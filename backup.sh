#!/bin/bash

DB_USER="root"
DB_PASSWORD="root"
DB_NAME="hospital"
BACKUP_DIR="/home/yedekler"
LOG_FILE="/var/log/backup.log"

DATE=$(date +'%Y-%m-%d_%H-%M-%S')
BACKUP_FILE="$BACKUP_DIR/hospital_backup_$DATE.sql"

mkdir -p "$BACKUP_DIR"


mysqldump -h db -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE"
STATUS=$?


if [ $STATUS -eq 0 ] && [ -s "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Yedekleme başarıyla alındı: $BACKUP_FILE (Boyut: $BACKUP_SIZE)" >> "$LOG_FILE"
else
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Yedekleme alınamadı! Hata kodu: $STATUS" >> "$LOG_FILE"
    exit 1
fi
