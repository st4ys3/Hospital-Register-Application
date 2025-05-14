# Hospital-Register-Application

Bu proje, Flask ve MySQL kullanılarak geliştirilen bir Hasta Kayıt Web Uygulamasıdır.

## Proje Özeti

Bu uygulama, hastane personelinin sisteme güvenli şekilde kayıt olmasını ve giriş yapmasını
sağlar. Giriş yapan kullanıcılar, gelen hastaların bilgilerini kaydedebilir, bu veriler MySQL
veritabanında saklanır. Sistemde ayrıca veritabanı yedeği alma özelliği vardır. Bu yedekler hem
manuel hem de otomatik olarak alınabilir. Tüm sistem, Docker Compose ile kolayca ayağa
kaldırılabilir ve kullanıcı dostu bir web arayüzü sunar. Sistem, SQL Injection (SQLi) ve CSRF gibi
yaygın web güvenlik açıklarına karşı korunacak şekilde geliştirilmiştir.

---

## Kurulum Adımları

### 1. Repoyu Klonlayın Veya Zip Dosyası Olarak İndirip Dosyayı Çıkarın.

```bash
git clone https://github.com/berriesyl/Hospital-Register-Application.git
cd Hospital-Register-Application
```

### 2. Ortam Değişkenlerini Oluşturun (.env)

Proje dizinine eğer yoksa .env dosyası oluşturun ve aşağıdaki gibi düzenleyin (Password'leri
kendinize göre değiştirebilirsiniz.):

```env
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=hospitaldb
MYSQL_USER=hospitaluser

MYSQL_PASSWORD=hospitalpass
FLASK_SECRET_KEY=secretkey123
```

### 3. Docker Kurulumu

Docker ve Docker Compose sisteminizde yüklü değilse:

- Docker: https://docs.docker.com/get-docker/
- Docker Compose: https://docs.docker.com/compose/install/

### 4. Docker Compose ile İndirilen Dosyanın İçinde Terminal Açıp Aşağıdaki Komut İle Sistemi
Başlatın.

```bash
docker-compose up --build
```

- Web arayüzü: http://localhost:5000
- MySQL servisi: 3306 portunda çalışır.

---

## Veritabanı & Backup Sistemi

Veriler MySQL veritabanında saklanır. Backup işlemleri bir Bash scripti ile yapılır.

### Script ile Elle Yedek Alma

```bash
bash scripts/backup.sh

```

- Yedekler /yedekler klasörüné .sql dosyası olarak kaydedilir.
- İşlem sonucu /backup.log dosyasına yazılır.

Örnek log satırı:

```
[2025-05-14 10:23:01] Backup successful: backup_2025-05-14_10-23.sql (35K)
```

### Otomatik Backup (Crontab)

Yedekler, crontab.sh ile haftalık otomatik olarak alınması için ayarlanmıştır.
Kontrol etmek için Docker'ın web konteynırından aşağıdaki komutu çalıştırarak bakabilirsiniz:

```bash
crontab -l
```

---

## Güvenlik

- SQL Injection’a karşı korunmalı (parametrik sorgular)
- Kullanıcı girdileri doğrulanır ve filtrelenir.
- IDOR ve LFI açıklarına karşı önlemler alınmıştır.
- Session kontrolü ve kullanıcı yetkilendirmesi yapılır.

---

Bu proje Altay Takımından [Berra SÖYLER](https://github.com/berriesyl) [Ayşe BALCI](https://github.com/st4ys3) ve [Hasan KARACA](https://github.com/HasanKrc0)  tarafından eğitim amaçlı olarak geliştirilmiştir.
