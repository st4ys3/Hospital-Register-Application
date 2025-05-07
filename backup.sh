#!/bin/bash

# Yedekleme işlemi için gerekli değişkenler
DB_USER="root"               # Veritabanı kullanıcı adı
DB_PASSWORD="root"           # Veritabanı şifresi
DB_NAME="hospital"           # Yedek alınacak veritabanı adı
BACKUP_DIR="/home/yedekler" # Yedeklerin saklanacağı dizin (örneğin: /backups)
LOG_FILE="/var/log/backup.log" # Log dosyasının yolu

# Yedekleme dosyasının ismi ve yolu (tarih ve saat eklenerek)
DATE=$(date +'%Y-%m-%d_%H-%M-%S')
BACKUP_FILE="$BACKUP_DIR/hospital_backup_$DATE.sql"

# Veritabanını yedekleme komutu
mysqldump -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE"

# Yedekleme sonucu kontrolü
if [ $? -eq 0 ]; then
    # Yedekleme başarılıysa, log dosyasına bilgi ekle
    BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1) # Yedek dosyasının boyutunu al
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Yedekleme başarıyla alındı: $BACKUP_FILE (Boyut: $BACKUP_SIZE)" >> "$LOG_FILE"
else
    # Yedekleme başarısızsa, hata logu kaydet
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Yedekleme alınamadı! Hata kodu: $?" >> "$LOG_FILE"
fi
