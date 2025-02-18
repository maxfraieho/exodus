---
{"title":"Minio github action","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/instrukcziyi/minio-github-action/","dgPassFrontmatter":true,"noteIcon":""}
---

#!/usr/bin/env python3
import os
import re
import markdown
from weasyprint import HTML
from bs4 import BeautifulSoup
from pathlib import Path

def find_markdown_and_images(root_dir, ignore_dirs=None, image_extensions=None):
    """
    Повертає кортеж (list_md_files, set_image_paths), де:
      - list_md_files: список шляхів до файлів .md;
      - set_image_paths: множина шляхів до зображень, на які посилаються у Markdown.
    """
    if ignore_dirs is None:
        ignore_dirs = {'.git', 'node_modules', 'venv', 'dist', '__pycache__'}
    if image_extensions is None:
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg'}

    list_md_files = []
    set_image_paths = set()

    # Рекурсивний обхід директорії
    for current_path, dirs, files in os.walk(root_dir):
        # Фільтруємо директорії для ігнорування
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
        for file_name in files:
            full_file_path = os.path.join(current_path, file_name)
            _, ext = os.path.splitext(file_name.lower())
            if ext == '.md':
                list_md_files.append(full_file_path)

    # Знаходимо посилання на зображення в Markdown-файлах
    # (якщо потрібно, можна поправити регулярний вираз до стандартного формату: r'!.*?([^)]+)')
    image_pattern = re.compile(r'!.*?([^)]+)')
    for md_path in list_md_files:
        try:
            with open(md_path, 'r', encoding='utf-8') as md_file:
                content = md_file.read()
        except Exception as e:
            print(f"Не вдалося прочитати {md_path}: {e}")
            continue

        matches = image_pattern.findall(content)
        for img_src in matches:
            # Пропускаємо абсолютні URL (http/https) або data URI
            if not (img_src.startswith('http') or img_src.startswith("data:")):
                _, img_ext = os.path.splitext(img_src.lower())
                if img_ext in image_extensions:
                    full_img_path = os.path.normpath(os.path.join(os.path.dirname(md_path), img_src))
                    set_image_paths.add(full_img_path)
    return list_md_files, set_image_paths

def convert_markdown_files_to_combined_html(md_files):
    """
    Конвертує кожен Markdown-файл у HTML, виправляє відносні посилання на зображення 
    (перетворюючи їх у абсолютні file URI) та об'єднує результати в один HTML-документ.
    """
    combined_html = (
        "<html><head><meta charset='utf-8'>"
        "<title>Об'єднаний Markdown</title></head><body>"
    )
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                md_text = f.read()
        except Exception as e:
            print(f"Не вдалося прочитати {md_file}: {e}")
            continue

        # Конвертуємо Markdown у HTML
        html_fragment = markdown.markdown(md_text, output_format="html5")
        # Обробляємо HTML для коректної роботи з відносними шляхами до зображень
        soup = BeautifulSoup(html_fragment, "html.parser")
        md_dir = os.path.dirname(md_file)
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and not (src.startswith("http") or src.startswith("data:")):
                abs_img_path = os.path.normpath(os.path.join(md_dir, src))
                # Перетворюємо у file URI (це дозволяє WeasyPrint завантажувати зображення з локальної файлової системи)
                img["src"] = Path(abs_img_path).as_uri()
        html_fragment = str(soup)
        # Додаємо фрагмент до загального HTML із горизонтальною лінією як роздільником (з можливим розривом сторінки)
        combined_html += html_fragment
        combined_html += "<hr style='page-break-after: always; border: none;'>"
    combined_html += "</body></html>"
    return combined_html

def main():
    print("=== Генеруємо PDF для кожної підпапки з Markdown ===\n")
    
    # Встановлюємо базову директорію. За замовчуванням використовуємо "src/site/notes" 
    # відносно розташування скрипту.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_base_dir = os.path.join(script_dir, "src/site/notes")
    base_dir = input(f"Введіть шлях до базової директорії з нотатками (за замовчуванням {default_base_dir}): ").strip() or default_base_dir
    output_dir = input("Введіть шлях до папки, куди зберігати PDF (за замовчуванням базова директорія): ").strip() or base_dir
    additional_ignore_str = input("Додаткові папки для ігнорування (через кому чи пробіл) або Enter: ").strip()
    additional_ignore = set()
    if additional_ignore_str:
        additional_ignore = {d.strip() for d in additional_ignore_str.replace(',', ' ').split()}

    # Отримуємо список підпапок у базовій директорії, які не входять до списку ігнорування.
    subdirs = []
    for entry in os.listdir(base_dir):
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(full_path) and entry not in {'.git', 'node_modules', 'venv', 'dist', '__pycache__'} and entry not in additional_ignore:
            subdirs.append(full_path)

    if not subdirs:
        print("Не знайдено підпапок у", base_dir)
        return

    for subdir in subdirs:
        folder_name = os.path.basename(subdir)
        print(f"\nОбробка папки: {subdir}")
        
        # Знаходимо Markdown-файли в поточній підпапці
        md_files, img_paths = find_markdown_and_images(
            root_dir=subdir,
            ignore_dirs={'.git', 'node_modules', 'venv', 'dist', '__pycache__'}.union(additional_ignore),
            image_extensions={'.png', '.jpg', '.jpeg', '.gif', '.svg'}
        )
        if not md_files:
            print(f"У папці {subdir} не знайдено жодного .md-файлу, пропускаємо.")
            continue

        print("Знайдено Markdown-файли:")
        for m in md_files:
            print("  ", m)

        print(f"Генеруємо об'єднаний HTML для папки {folder_name}...")
        combined_html = convert_markdown_files_to_combined_html(md_files)

        # Ім'я PDF відповідає назві папки (наприклад, "topic1.pdf")
        output_pdf = os.path.join(output_dir, f"{folder_name}.pdf")
        try:
            # base_url встановлено на поточну підпапку, щоб WeasyPrint правильно знаходив ресурси
            HTML(string=combined_html, base_url=subdir).write_pdf(output_pdf)
            print(f"PDF успішно сформовано: {output_pdf}")
        except Exception as e:
            print(f"Помилка при конвертації у PDF для {folder_name}:", e)

    print("\nСкрипт завершено.")

if __name__ == "__main__":
    main()


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