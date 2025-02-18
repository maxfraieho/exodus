---
{"title":"Створення pdf для exodus.pp.ua","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/instrukcziyi/stvorennya-pdf-dlya-exodus-pp-ua/","dgPassFrontmatter":true,"noteIcon":""}
---

оригінал

name: Generate PDF and Upload to MinIO via Cloudflare (one-by-one, put-object)

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
  generate-and-upload:
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
            unzip

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

      - name: Install AWS CLI v2
        run: |
          curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
          unzip awscliv2.zip
          sudo ./aws/install --update

      - name: Configure AWS CLI for MinIO via Cloudflare
        env:
          AWS_ACCESS_KEY_ID: 77icD4OgvRKPKF198eiC
          AWS_SECRET_ACCESS_KEY: B3kWQMmF4zZLb9W6dboJrdDQAMWBrVyAG4ySFBIx
        run: |
          aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
          aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
          aws configure set default.region us-east-1
          # path-style потрібен для MinIO, щоб уникнути редіректів
          aws configure set default.s3.addressing_style path

      - name: Upload PDFs to MinIO (put-object, transliteration)
        env:
          # Вимкнути multipart, щоб уникнути chunked-uploads (Cloudflare іноді з цим має проблеми)
          AWS_S3_DISABLE_MULTIPART: "1"
        shell: bash
        run: |
          echo "Uploading PDF files to MinIO via Cloudflare Tunnel (using s3api put-object, one-by-one)"

          # Знайти всі PDF у каталозі src/site/notes
          mapfile -t pdf_files < <(find src/site/notes -type f -iname "*.pdf")

          for pdf in "${pdf_files[@]}"; do
            orig_name="$(basename "$pdf")"

            # Транслітеруємо ім'я файлу (кирилиця/діакритика -> латиниця/ASCII)
            safe_name="$(
              echo "$orig_name" \
                | sed -E '
                  s/щ/shch/g; s/ш/sh/g;   s/ч/ch/g;   s/ц/ts/g;   s/х/kh/g;
                  s/ю/yu/g;  s/я/ya/g;   s/ж/zh/g;   s/ї/yi/g;   s/і/i/g;
                  s/є/ye/g;  s/ґ/g/g;    s/ё/yo/g;   s/ъ//g;     s/ь//g;
                  s/ы/y/g;   s/э/e/g;    s/…/.../g; s/«//g;      s/»//g;
                  s/А/A/g;   s/Б/B/g;    s/В/V/g;    s/Г/H/g;    s/Ґ/G/g;
                  s/Д/D/g;   s/Е/E/g;    s/Є/Ye/g;   s/Ж/Zh/g;   s/З/Z/g;
                  s/И/Y/g;   s/І/I/g;    s/Ї/Yi/g;   s/Й/Y/g;    s/К/K/g;
                  s/Л/L/g;   s/М/M/g;    s/Н/N/g;    s/О/O/g;    s/П/P/g;
                  s/Р/R/g;   s/С/S/g;    s/Т/T/g;    s/У/U/g;    s/Ф/F/g;
                  s/Х/Kh/g;  s/Ц/Ts/g;   s/Ч/Ch/g;   s/Ш/Sh/g;   s/Щ/Shch/g;
                  s/Ю/Yu/g;  s/Я/Ya/g;   s/Ё/Yo/g;   s/Ъ//g;     s/Ь//g;
                  s/Ы/Y/g;   s/Э/E/g; 
                ' \
                | tr -cd '[:alnum:]._-' 
            )"

            echo "→ Original: $orig_name"
            echo "→ Transliterated: $safe_name"

            # Використовуємо s3api put-object (не s3 cp/sync!)
            # Звертаємося до HTTPS (Cloudflare примушує HTTPS інакше recursion depth error)
            aws --endpoint-url https://apiminio.exodus.pp.ua \
                s3api put-object \
                --bucket exodusbase \
                --key "$safe_name" \
                --body "$pdf" \
                --content-type application/pdf \
                --cli-read-timeout 360 \
                --cli-connect-timeout 360

            if [[ $? -ne 0 \| $? -ne 0 ]]; then
              echo "Помилка під час завантаження: $orig_name"
              exit 1
            fi
          done

          echo "Успішно завантажено PDF-файли."



Нижче наведено **оновлений** workflow, в якому:

1. **Залишено всі налаштування та логіку** надсилання PDF до MinIO з попереднього робочого варіанту.
2. **Замінено** етап **транслітерації** на **просту** обробку назв:
    - **Видалення** будь-яких символів, крім літер (латинських, кириличних), цифр, крапки (`.`), дефіса (`-`), нижнього підкреслення (`_`) та пробілу.
    - **Заміна** пробілів на дефіси.
3. **Інше** (інсталяція залежностей, виклик `codetomd.py`) залишається без змін.

> **Зверніть увагу**: у цьому прикладі обмежено набір кириличних символів до українського алфавіту + `Ёё` (якщо потрібно більше/менше, підкоригуйте регулярний вираз).

```yaml
name: Generate PDF and Upload to MinIO via Cloudflare (one-by-one, put-object)

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
  generate-and-upload:
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
            unzip

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

      - name: Install AWS CLI v2
        run: |
          curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
          unzip awscliv2.zip
          sudo ./aws/install --update

      - name: Configure AWS CLI for MinIO via Cloudflare
        env:
          # Краще зберігати секрети в GitHub Secrets, це приклад
          AWS_ACCESS_KEY_ID: 77icD4OgvRKPKF198eiC
          AWS_SECRET_ACCESS_KEY: B3kWQMmF4zZLb9W6dboJrdDQAMWBrVyAG4ySFBIx
        run: |
          aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
          aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
          aws configure set default.region us-east-1
          # path-style потрібен для MinIO, щоб уникнути редіректів
          aws configure set default.s3.addressing_style path

      - name: Upload PDFs to MinIO (put-object, simple rename)
        env:
          # Вимкнути multipart, щоб уникнути chunked-uploads (Cloudflare іноді з цим має проблеми)
          AWS_S3_DISABLE_MULTIPART: "1"
        shell: bash
        run: |
          echo "Uploading PDF files to MinIO via Cloudflare Tunnel (using s3api put-object, one-by-one)"

          # Знайти всі PDF у каталозі src/site/notes
          mapfile -t pdf_files < <(find src/site/notes -type f -iname "*.pdf")

          for pdf in "${pdf_files[@]}"; do
            orig_name="$(basename "$pdf")"

            # 1) Залишаємо літери (лат/кир), цифри, . _ - і пробіли
            # 2) Видаляємо інші спецсимволи
            # 3) Пробіли замінюємо на дефіси
            safe_name="$(
              echo "$orig_name" \
                | sed -E 's/[^[:alnum:]А-Яа-яЁёІіЇїЄєҐґ._\- ]//g' \
                | sed 's/ /-/g'
            )"

            echo "→ Original: $orig_name"
            echo "→ Cleaned : $safe_name"

            # Використовуємо s3api put-object (не s3 cp/sync!)
            # Звертаємося до HTTPS (Cloudflare примушує HTTPS інакше recursion depth error)
            aws --endpoint-url https://apiminio.exodus.pp.ua \
                s3api put-object \
                --bucket exodusbase \
                --key "$safe_name" \
                --body "$pdf" \
                --content-type application/pdf \
                --cli-read-timeout 360 \
                --cli-connect-timeout 360

            if [[ $? -ne 0 ]]; then
              echo "Помилка під час завантаження: $orig_name"
              exit 1
            fi
          done

          echo "Успішно завантажено PDF-файли."
```

### Пояснення основних змін у кроці `Upload PDFs to MinIO`

- Раніше виконувався цілий блок `sed -E 's/щ/shch/g; s/ш/sh/g; ...'` для транслітерації.
- Тепер залишено лише:
    
    ```bash
    sed -E 's/[^[:alnum:]А-Яа-яЁёІіЇїЄєҐґ._\- ]//g'
    sed 's/ /-/g'
    ```
    
    Це **видаляє** всі недозволені символи (тобто все, що не входить до латиниці, кирилиці, цифр, крапки, дефісу, підкреслення, пробілу) і **заміщає** пробіли на `-`.

Усе інше лишається без змін, зокрема виклик `aws s3api put-object`, передача `--endpoint-url`, `--bucket` тощо.