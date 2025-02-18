---
{"title":"Minio github action","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/instrukcziyi/minio-github-action/","dgPassFrontmatter":true,"noteIcon":""}
---



Bucket: # exodusbase

credentials.json:

{"url":"https://minio.exodus.pp.ua/api/v1/service-account-credentials","accessKey":"77icD4OgvRKPKF198eiC","secretKey":"B3kWQMmF4zZLb9W6dboJrdDQAMWBrVyAG4ySFBIx","api":"s3v4","path":"auto"}

Сервіс minio працює в контейнері :
services:
  noco-db:
    container_name: "noco-db"
    image: nocodb/nocodb:latest
    restart: always
    depends_on:
      - noco-db-postgres
      - minio
    environment:
      - NC_DB=pg://noco-db-postgres:5432?u=typebot&p=typebot&d=nocodb
      # Налаштування для інтеграції з S3-сумісним сховищем (MinIO)
      - NC_STORAGE=s3
      - NC_S3_ENDPOINT=http://minio:9000
      - NC_S3_BUCKET=noco-files
      - NC_S3_ACCESS_KEY=minioadmin
      - NC_S3_SECRET_KEY=minioadminpassword
    ports:
      - "8090:8080"  # NocoDB доступний зовні на порту 8090
    volumes:
      - noco_db_data:/usr/app/data
    networks:
      - app-tier

  noco-db-postgres:
    container_name: "noco-db-postgres"
    image: postgres:14-alpine
    restart: always
    environment:
      - POSTGRES_DB=nocodb
      - POSTGRES_USER=typebot
      - POSTGRES_PASSWORD=typebot
    volumes:
      - noco_db_pgdata:/var/lib/postgresql/data
    networks:
      - app-tier

  minio:
    container_name: "minio"
    image: bitnami/minio:latest
    # Оскільки Portainer працює на ipпорту 9000, для MinIO використаємо інші публічні порти
    ports:
      - "9002:9000"  # публічний порт 9002 -> контейнерний 9000 (S3 API)
      - "9003:9001"  # публічний порт 9003 -> контейнерний 9001 (консоль управління)
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadminpassword
    volumes:
      - minio_data:/bitnami/minio
    networks:
      - app-tier

volumes:
  noco_db_data:
  noco_db_pgdata:
  minio_data:

networks:
  app-tier:
    driver: bridge
Доступний через cloudflared:

tunnel: 7c2d896d-2c77-4486-af56-ef30969ca942
credentials-file: /etc/cloudflared/7c2d896d-2c77-4486-af56-ef30969ca942.json

ingress:
  - hostname: portainer.exodus.pp.ua
    service: http://192.168.1.234:9000

  - hostname: dangerboys.exodus.pp.ua
    service: http://192.168.1.234:8181
    
  - hostname: kofajoh.exodus.pp.ua
    service: http://192.168.1.234:8000

  - hostname: minio.exodus.pp.ua
    service: http://192.168.1.234:9003

  - hostname: nocodb.exodus.pp.ua
    service: http://192.168.1.234:8090
    
  - hostname: ssh.exodus.pp.ua
    service: ssh://192.168.1.234:22

  - service: http_status:404

Доступ до web інтерфейсу по адресі  : minio.exodus.pp.ua


Завдання: треба за допомогою aws-cli налаштувати передачу згенерованих pdf файлів до бакету minio переробивши скрипт, що мав мету надсилати ці файли за допомогою github action до nocodb, що не вдалося. Ось скрипт, що потребує переробки : 

name: Generate PDF and Update Noco-DB

on:
  push:
    branches:
      - main
    paths:
      - "src/site/notes/**"
  pull_request:
    branches:
      - main
    paths:
      - "src/site/notes/**"

jobs:
  generate-and-update-pdf:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            libcairo2 \
            libpango-1.0-0 \
            libpangocairo-1.0-0 \
            libgdk-pixbuf2.0-0 \
            libffi-dev \
            shared-mime-info \
            jq

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install markdown weasyprint beautifulsoup4

      - name: Generate PDFs per topic
        run: |
          printf "src/site/notes\n\n\n" | python codetomd.py

      - name: Update PDF records in Noco-DB
        env:
          NOCO_DB_API_URL: "https://nocodb.soyka.pp.ua"
          NOCO_DB_TABLE_ID: "mdb4f2t1ngchrom"
          NOCO_DB_VIEW_ID: "vwknikxbrl1mobu9"
          NOCO_DB_API_TOKEN: ${{ secrets.NOCO_DB_API_KEY }}
          ATTACHMENT_FIELD_ID: "cyl3kusky2kreq3"  # ID поля для прикріплень
        run: |
          echo "Закидаємо PDF files for Noco-DB update..."

          for pdf in src/site/notes/*.pdf; do
            # Транслітерація кирилиці в латиницю
            filename=$(basename "$pdf" | sed '
              y/абвгґдеєжзиіїйклмнопрстуфхцчшщюяьАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЮЯЬ/abvhgdeyezhzyiijklmnoprstufxczchshshchyuyaABVHGDEYeZhZYIIJKLmnoprstufxczchshshchYUYa/;
              s/ё/yo/g; s/ъ//g; s/ы/y/g; s/э/e/g; s/Ё/Yo/g; s/Ъ//g; s/Ы/Y/g; s/Э/E/g;
            ' | iconv -f UTF-8 -t ASCII//TRANSLIT//IGNORE | tr -cd '[:alnum:]._-' | tr ' ' '_')

            echo "Оригінальне ім'я: $(basename "$pdf"), транслітероване ім'я: $filename"
            
            # Кодовано параметр пошуку
            where=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote('filename,eq,' + sys.argv[1]))" "$filename")
            
            # Пошук запису за filename з параметрами offset, limit та viewId
            response=$(curl -s --request GET \
              --url "$NOCO_DB_API_URL/api/v2/tables/$NOCO_DB_TABLE_ID/records?where=$where&offset=0&limit=25&viewId=$NOCO_DB_VIEW_ID" \
              --header "xc-token: $NOCO_DB_API_TOKEN")
            
            if echo "$response" | jq -e '.data | length == 0' > /dev/null; then
              echo "Створення нового запису для $filename..."
              
              attempt=0
              max_attempts=3
              while [ $attempt -lt $max_attempts ]; do
                response=$(curl --silent --show-error --fail --request POST \
                  --url "$NOCO_DB_API_URL/api/v2/tables/$NOCO_DB_TABLE_ID/records" \
                  --header "xc-token: $NOCO_DB_API_TOKEN" \
                  -F "filename=$filename" \
                  -F "$ATTACHMENT_FIELD_ID=@$pdf")
            
                if [[ $? -eq 0 \| $? -eq 0 ]]; then
                  echo "Успішно створено запис для $filename"
                  break
                fi
                
                attempt=$((attempt+1))
                echo "Повторна спроба... ($attempt/$max_attempts)"
                sleep 20
              done

              # Debugging information for failures
              if [[ $? -ne 0 \| $? -ne 0 ]]; then
                echo "Помилка при створенні запису для $filename. Відповідь сервера:"
                echo "$response"
              fi

            else
              recordId=$(echo "$response" | jq -r '.data[0].id')
              
              if [[ "$recordId" == "null" \| "$recordId" == "null" ]]; then
                echo "Помилка: recordId відсутній, пропускаємо $filename"
                continue
              fi
              
              echo "Оновлення існуючого запису $recordId для $filename..."
              
              attempt=0
              max_attempts=3
              while [ $attempt -lt $max_attempts ]; do
                response=$(curl --silent --show-error --fail --request PATCH \
                  --url "$NOCO_DB_API_URL/api/v2/tables/$NOCO_DB_TABLE_ID/records/$recordId" \
                  --header "xc-token: $NOCO_DB_API_TOKEN" \
                  -F "filename=$filename" \
                  -F "$ATTACHMENT_FIELD_ID=@$pdf")
            
                if [[ $? -eq 0 \| $? -eq 0 ]]; then
                  echo "Успішно оновлено запис для $filename"
                  break
                fi
                
                attempt=$((attempt+1))
                echo "Повторна спроба... ($attempt/$max_attempts)"
                sleep 20
              done

              # Debugging information for failures
              if [[ $? -ne 0 \| $? -ne 0 ]]; then
                echo "Помилка при оновленні запису для $filename. Відповідь сервера:"
                echo "$response"
              fi

            fi
            
          done          

Ч