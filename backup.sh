#!/bin/bash

# Güvenli yedekleme betiği
DB_USER="root"
DB_PASSWORD="root"
DB_NAME="hospital"
BACKUP_DIR="/home/yedekler"
LOG_FILE="/var/log/backup.log"

# Dizinleri oluştur
mkdir -p "$BACKUP_DIR"
touch "$LOG_FILE"

# Yedekleme tarihini ve dosya adını oluştur
DATE=$(date +'%Y-%m-%d_%H-%M-%S')
BACKUP_FILE="$BACKUP_DIR/hospital_backup_$DATE.sql"

# Yedekleme işlemini gerçekleştir
echo "$(date +'%Y-%m-%d %H:%M:%S') - Yedekleme işlemi başlatılıyor..." >> "$LOG_FILE"

# Yedekleme komutunu çalıştır
mysqldump -h db -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE" 2>> "$LOG_FILE"
STATUS=$?

# Yedekleme durumunu kontrol et
if [ $STATUS -eq 0 ] && [ -s "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Yedekleme başarıyla alındı: $BACKUP_FILE (Boyut: $BACKUP_SIZE)" >> "$LOG_FILE"
    
    # Yedek dosyasının izinlerini ayarla
    chmod 600 "$BACKUP_FILE"
    
    # Eski yedekleri temizle (30 günden eski)
    find "$BACKUP_DIR" -name "hospital_backup_*.sql" -type f -mtime +30 -delete
    echo "$(date +'%Y-%m-%d %H:%M:%S') - 30 günden eski yedekler temizlendi." >> "$LOG_FILE"
else
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Yedekleme alınamadı! Hata kodu: $STATUS" >> "$LOG_FILE"
    exit 1
fi

echo "$(date +'%Y-%m-%d %H:%M:%S') - Yedekleme işlemi tamamlandı." >> "$LOG_FILE"
