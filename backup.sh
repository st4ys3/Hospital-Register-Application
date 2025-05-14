#!/bin/bash

set -a
source /app/.env
set +a

DB_USER="root"
DB_PASSWORD="$MYSQL_ROOT_PASSWORD"
DB_NAME="$MYSQL_DATABASE"
BACKUP_DIR="$BACKUP_DIR"
LOG_FILE="$LOG_FILE"

mkdir -p "$BACKUP_DIR"
touch "$LOG_FILE"

DATE=$(date +'%Y-%m-%d_%H-%M-%S')
BACKUP_FILE="$BACKUP_DIR/hospital_backup_$DATE.sql"

echo "$(date +'%Y-%m-%d %H:%M:%S') - Yedekleme başlatılıyor..." >> "$LOG_FILE"

mysqldump -h db -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE" 2>> "$LOG_FILE"
STATUS=$?

if [ $STATUS -eq 0 ] && [ -s "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Yedekleme tamamlandı: $BACKUP_FILE (Boyut: $BACKUP_SIZE)" >> "$LOG_FILE"
    chmod 600 "$BACKUP_FILE"
    find "$BACKUP_DIR" -name "hospital_backup_*.sql" -type f -mtime +30 -delete
    echo "$(date +'%Y-%m-%d %H:%M:%S') - 30 günden eski yedekler silindi." >> "$LOG_FILE"
else
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Hata! Yedekleme başarısız. Kod: $STATUS" >> "$LOG_FILE"
    exit 1
fi

echo "$(date +'%Y-%m-%d %H:%M:%S') - Yedekleme süreci tamamlandı." >> "$LOG_FILE"
