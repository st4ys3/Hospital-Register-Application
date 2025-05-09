#!/bin/bash

# Cron servisini başlat
service cron start

# Yedekleme betiğinin yolu
BACKUP_PATH="/app/backup.sh"

# Yedekleme betiğine çalıştırma izni ver
chmod +x "$BACKUP_PATH"

# Haftalık yedekleme için cron görevi
CRON_JOB="0 0 * * 0 $BACKUP_PATH >> /var/log/cron.log 2>&1"

# Log dizinini oluştur
mkdir -p /app/backup_logs
touch /var/log/backup.log
chmod 666 /var/log/backup.log

# Cron görevini ekle
if crontab -l 2>/dev/null | grep -q "$BACKUP_PATH"; then
    echo "Cron görevi zaten mevcut."
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Cron görevi başarıyla eklendi: $CRON_JOB"
fi

# Flask uygulamasını başlat
exec flask run --host=0.0.0.0
