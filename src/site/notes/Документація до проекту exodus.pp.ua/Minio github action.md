---
{"title":"Minio github action","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/minio-github-action/","dgPassFrontmatter":true,"noteIcon":""}
---



Bucket: # exodusbase

credentials.json:

{"url":"https://minio.exodus.pp.ua/api/v1/service-account-credentials","accessKey":"77icD4OgvRKPKF198eiC","secretKey":"B3kWQMmF4zZLb9W6dboJrdDQAMWBrVyAG4ySFBIx","api":"s3v4","path":"auto"}

встановлюю  mc (MinIO Client) на termux , як синхронізувати файли з бакету до парки пристрою , наприклад documents/minio

Для синхронізації файлів з бакету MinIO до папки пристрою в Termux за допомогою `mc` (MinIO Client), виконайте наступні кроки:

1.  **[Встановіть `mc` (MinIO Client)](pplx://action/followup)**
    Якщо `mc` ще не встановлено, завантажте та встановіть його[1][2]:

    ```bash
    wget https://dl.min.io/client/mc/release/linux-arm64/mc
    chmod +x mc
    mv mc /data/data/com.termux/files/usr/bin/
    ```

2.  **[Налаштуйте підключення до MinIO](pplx://action/followup)**
    Додайте alias для вашого MinIO сервера[1][2]:

    ```bash
    mc alias set https://minio.exodus.pp.ua 77icD4OgvRKPKF198eiC B3kWQMmF4zZLb9W6dboJrdDQAMWBrVyAG4ySFBIx
    ```

    Замініть `http://your-minio-url:9000`, `YOUR_ACCESS_KEY` та `YOUR_SECRET_KEY` на відповідні значення.

3.  **[Синхронізуйте файли](pplx://action/followup)**
    Використовуйте команду `mc mirror` для синхронізації файлів з бакету MinIO до локальної папки[1]:

    ```bash
    mc mirror myminio/your-bucket-name /sdcard/Documents/minio
    ```

    Ця команда синхронізує вміст бакету `your-bucket-name` в MinIO з папкою `/sdcard/Documents/minio` на вашому пристрої.  `/sdcard/Documents/minio` - це шлях до папки Documents/minio.
