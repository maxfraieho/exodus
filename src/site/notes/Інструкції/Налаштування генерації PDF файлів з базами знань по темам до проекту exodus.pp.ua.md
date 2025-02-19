---
{"title":"Створення pdf для exodus.pp.ua","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/instrukcziyi/nalashtuvannya-generacziyi-pdf-fajliv-z-bazami-znan-po-temam-do-proektu-exodus-pp-ua/","dgPassFrontmatter":true,"noteIcon":""}
---



У цій статті ми розглянемо, як автоматизувати процес генерації PDF файлів з нотатками, створеними в Obsidian. Для цього використовуються два основних компоненти:

1. **GitHub Actions Workflow** – автоматизує запуск процесу при внесенні змін до нотаток, встановлює залежності, генерує PDF файли та завантажує їх на сервер MinIO через Cloudflare Tunnel.
2. **Python-скрипт** – здійснює обробку Markdown файлів, конвертує їх у HTML, коригує шляхи до зображень і створює фінальний PDF файл для кожної тематики (підпапки).

Нижче наведено покроковий опис налаштування та логіки роботи обох скриптів.

---

## Архітектура рішення

Процес генерації PDF файлів складається з таких етапів:

1. **Тригер GitHub Actions**  
    Workflow налаштований на спрацьовування при `push` або `pull_request` до гілки `main` для змін у каталозі `src/site/notes/**`.
    
2. **Підготовка середовища**
    
    - Завантажується репозиторій.
    - Встановлюються системні залежності (бібліотеки для роботи WeasyPrint, наприклад, `libcairo2`, `libpango-1.0-0` тощо).
    - Налаштовується Python та встановлюються необхідні бібліотеки (наприклад, `markdown`, `weasyprint`, `beautifulsoup4`, `markdown-extra`).
3. **Генерація PDF файлів**  
    За допомогою Python-скрипту `codetomd.py` сканується вказаний каталог з нотатками, знаходяться Markdown файли, конвертуються у HTML з урахуванням зображень, а потім HTML генерується у PDF.
    
4. **Завантаження PDF файлів**
    
    - Встановлюється AWS CLI.
    - Налаштовуються дані доступу до MinIO (з використанням секретів GitHub).
    - Скрипт знаходить всі PDF файли, очищує їх імена, перевіряє розмір файлу та завантажує їх на MinIO за допомогою AWS CLI.

---

## Опис GitHub Actions Workflow

Нижче наведено YAML скрипт, який автоматизує процес генерації та завантаження PDF файлів:

```yaml
name: Generate PDF and Upload to MinIO via Cloudflare

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
          pip install markdown weasyprint beautifulsoup4 markdown-extra

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
          AWS_ACCESS_KEY_ID: ${{ secrets.MINIO_ACCESS_KEY }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.MINIO_SECRET_KEY }}
        run: |
          aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
          aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
          aws configure set default.region us-east-1
          aws configure set default.s3.addressing_style path

      - name: Upload PDFs to MinIO
        env:
          AWS_S3_DISABLE_MULTIPART: "1"
        shell: bash
        run: |
          echo "Uploading PDF files to MinIO via Cloudflare Tunnel"
          
          # Знайти всі PDF у каталозі src/site/notes
          mapfile -t pdf_files < <(find src/site/notes -type f -iname "*.pdf")
          
          for pdf in "${pdf_files[@]}"; do
            orig_name="$(basename "$pdf")"
            
            # Очищення імені файлу
            safe_name="$(
              echo "$orig_name" \
                | LC_ALL=en_US.UTF-8 sed -E 's/[^-[:alnum:]А-Яа-яЁёІіЇїЄєҐґ._ ]//g' \
                | sed 's/ /-/g'
            )"
            
            echo "→ Оригінальне ім'я: $orig_name"
            echo "→ Очищене ім'я   : $safe_name"
            
            # Перевірка розміру файлу
            if [ ! -s "$pdf" ]; then
              echo "Помилка: файл $pdf порожній"
              exit 1
            fi
            
            # Завантаження файлу
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
            
            echo "✓ Успішно завантажено: $safe_name"
          done
          
          echo "Всі PDF-файли успішно завантажено"
```

### Розбір основних етапів:

- **Checkout repository:**  
    Використання дії `actions/checkout` для отримання останньої версії коду з репозиторію.
    
- **Install system dependencies:**  
    Оновлюється список пакетів та встановлюються необхідні бібліотеки (зокрема, бібліотеки для WeasyPrint, що використовуються для генерації PDF).
    
- **Set up Python та Install Python dependencies:**  
    Налаштовується потрібна версія Python і встановлюються пакети для обробки Markdown, конвертації HTML у PDF та роботи з HTML (BeautifulSoup).
    
- **Generate PDFs per topic:**  
    Виконується Python-скрипт (`codetomd.py`), який обробляє всі Markdown файли у каталозі `src/site/notes` та генерує PDF для кожної підпапки або тематики.
    
- **Install та Configure AWS CLI:**  
    Завантажується та встановлюється AWS CLI v2, після чого налаштовуються дані доступу (секрети) для роботи з MinIO через Cloudflare.
    
- **Upload PDFs to MinIO:**  
    Скрипт знаходить усі PDF файли в каталозі, очищує їх імена (щоб уникнути небажаних символів), перевіряє, чи не є файл порожнім, і завантажує його за допомогою AWS CLI у вказаний бакет MinIO.
    

---

## Опис Python-скрипту для генерації PDF

Нижче наведено Python-скрипт `codetomd.py`, який здійснює пошук Markdown файлів, обробку контенту та генерацію PDF файлів.

```python
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
      - list_md_files: список шляхів до файлів .md (з усіх підпапок);
      - set_image_paths: множина шляхів до зображень, на які посилаються у Markdown.
    """
    if ignore_dirs is None:
        ignore_dirs = {'.git', 'node_modules', 'venv', 'dist', '__pycache__'}
    if image_extensions is None:
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg'}

    list_md_files = []
    set_image_paths = set()

    # Спочатку додаємо файли з кореневої директорії
    for file_name in os.listdir(root_dir):
        full_file_path = os.path.join(root_dir, file_name)
        if os.path.isfile(full_file_path) and file_name.lower().endswith('.md'):
            list_md_files.append(full_file_path)

    # Потім рекурсивний обхід піддиректорій
    for current_path, dirs, files in os.walk(root_dir):
        # Пропускаємо кореневу директорію, оскільки ми вже обробили її
        if current_path == root_dir:
            continue
        
        # Фільтруємо директорії для ігнорування
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
        for file_name in files:
            full_file_path = os.path.join(current_path, file_name)
            if file_name.lower().endswith('.md'):
                list_md_files.append(full_file_path)

    # Сортуємо файли за шляхом для послідовного порядку
    list_md_files.sort()

    # Сканування файлів на наявність зображень
    for md_path in list_md_files:
        try:
            with open(md_path, 'r', encoding='utf-8') as md_file:
                content = md_file.read()
        except Exception as e:
            print(f"Не вдалося прочитати {md_path}: {e}")
            continue

        # Пошук зображень у стандартному форматі Markdown
        for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', content):
            img_src = match.group(2)
            if not (img_src.startswith("http") or img_src.startswith("data:")):
                _, img_ext = os.path.splitext(img_src.lower())
                if img_ext in image_extensions:
                    full_img_path = os.path.normpath(os.path.join(os.path.dirname(md_path), img_src))
                    set_image_paths.add(full_img_path)

        # Пошук зображень у форматі Obsidian
        for match in re.finditer(r'!\[\[([^|\]]+)(?:\|[^\]]+)?\]\]', content):
            img_src = match.group(1)
            if not (img_src.startswith("http") or img_src.startswith("data:")):
                _, img_ext = os.path.splitext(img_src.lower())
                if img_ext in image_extensions:
                    full_img_path = os.path.normpath(os.path.join(os.path.dirname(md_path), img_src))
                    set_image_paths.add(full_img_path)

    return list_md_files, set_image_paths

def process_markdown_content(content, base_path):
    """
    Обробляє markdown-контент: конвертує у HTML та виправляє шляхи до зображень
    """
    # Конвертуємо Markdown у HTML
    html = markdown.markdown(content, extensions=['extra', 'tables'])
    
    # Створюємо об'єкт BeautifulSoup для обробки HTML
    soup = BeautifulSoup(html, 'html.parser')
    
    # Виправляємо шляхи до зображень
    for img in soup.find_all('img'):
        src = img.get('src')
        if src and not (src.startswith('http') or src.startswith('data:')):
            abs_path = os.path.join(base_path, src)
            if os.path.exists(abs_path):
                img['src'] = Path(abs_path).as_uri()
    
    return str(soup)

def convert_markdown_files_to_combined_html(md_files):
    """
    Конвертує всі markdown файли в один HTML документ
    """
    html_template = """
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 40px;
            }
            img {
                max-width: 100%;
                height: auto;
            }
            .file-section {
                margin-bottom: 30px;
                page-break-before: always;
            }
            .file-name {
                color: #333;
                border-bottom: 1px solid #ccc;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
    """
    
    content = []
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                print(f"Обробка файлу: {md_file}")
                md_content = f.read()
                base_path = os.path.dirname(md_file)
                
                processed_content = process_markdown_content(md_content, base_path)
                
                section = f"""
                <div class="file-section">
                    <h2 class="file-name">{os.path.basename(md_file)}</h2>
                    {processed_content}
                </div>
                """
                content.append(section)
        except Exception as e:
            print(f"Помилка при обробці {md_file}: {e}")
    
    return html_template + "\n".join(content) + "</body></html>"

def main():
    print("=== Генеруємо PDF для кожної підпапки з Markdown ===\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_base_dir = os.path.join(script_dir, "src/site/notes")
    
    # Отримуємо параметри від користувача
    base_dir = input(f"Введіть шлях до базової директорії з нотатками (за замовчуванням {default_base_dir}): ").strip() or default_base_dir
    output_dir = input(f"Введіть шлях до папки для збереження PDF (за замовчуванням {base_dir}): ").strip() or base_dir
    additional_ignore_str = input("Додаткові папки для ігнорування (через кому чи пробіл) або Enter: ").strip()
    
    additional_ignore = set()
    if additional_ignore_str:
        additional_ignore = {d.strip() for d in additional_ignore_str.replace(',', ' ').split()}

    # Отримуємо список підпапок
    subdirs = []
    for entry in os.listdir(base_dir):
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(full_path) and entry not in {'.git', 'node_modules', 'venv', 'dist', '__pycache__'} and entry not in additional_ignore:
            subdirs.append(full_path)

    if not subdirs:
        print(f"Не знайдено підпапок у {base_dir}. Обробляємо тільки кореневу папку...")
        subdirs = [base_dir]

    # Обробка кожної підпапки
    for subdir in subdirs:
        folder_name = os.path.basename(subdir)
        print(f"\nОбробка папки: {subdir}")
        
        # Знаходимо всі markdown файли та зображення
        md_files, img_paths = find_markdown_and_images(
            root_dir=subdir,
            ignore_dirs={'.git', 'node_modules', 'venv', 'dist', '__pycache__'}.union(additional_ignore),
            image_extensions={'.png', '.jpg', '.jpeg', '.gif', '.svg'}
        )
        
        if not md_files:
            print(f"У папці {subdir} не знайдено .md файлів, пропускаємо.")
            continue

        print("\nЗнайдено Markdown файли:")
        for md_file in md_files:
            print(f"  {md_file}")

        print(f"\nГенеруємо PDF для папки {folder_name}...")
        
        try:
            # Конвертуємо markdown в HTML
            html_content = convert_markdown_files_to_combined_html(md_files)
            
            # Генеруємо PDF
            output_pdf = os.path.join(output_dir, f"{folder_name}.pdf")
            HTML(string=html_content, base_url=subdir).write_pdf(output_pdf)
            
            print(f"PDF успішно створено: {output_pdf}")
            
            # Перевіряємо розмір файлу
            if os.path.getsize(output_pdf) > 0:
                print(f"Розмір файлу: {os.path.getsize(output_pdf)} байт")
            else:
                print("Попередження: згенерований PDF файл порожній!")
        except Exception as e:
            print(f"Помилка при створенні PDF для {folder_name}: {e}")

    print("\nГенерація PDF завершена.")

if __name__ == "__main__":
    main()
```

### Основні етапи роботи скрипту:

1. **Пошук Markdown файлів та зображень**  
    Функція `find_markdown_and_images` рекурсивно проходить по заданій директорії, знаходить всі `.md` файли та шукає посилання на зображення у форматах стандартного Markdown та Obsidian.
    
2. **Обробка Markdown контенту**  
    Функція `process_markdown_content` конвертує Markdown у HTML за допомогою модуля `markdown`, а потім за допомогою BeautifulSoup виправляє локальні шляхи до зображень, замінюючи їх на URI.
    
3. **Конвертація у єдиний HTML документ**  
    Функція `convert_markdown_files_to_combined_html` збирає вміст усіх Markdown файлів у єдину HTML сторінку із додаванням стилів для кращого вигляду PDF. Кожен файл розміщується в окремому розділі з заголовком.
    
4. **Генерація PDF**  
    Основна функція `main` опитує користувача щодо директорій для нотаток та збереження PDF, обробляє кожну підпапку (або кореневу директорію, якщо підпапок немає) та генерує відповідний PDF за допомогою WeasyPrint.
    

---

## Покрокова інструкція налаштування

1. **Створіть необхідну структуру проекту**
    
    - Розмістіть ваші нотатки в каталозі `src/site/notes`.
    - Додайте скрипт `codetomd.py` до кореневої директорії або в інше зручне місце.
2. **Налаштуйте GitHub репозиторій**
    
    - Додайте файл workflow (наприклад, `.github/workflows/pdf_generation.yml`) із вищенаведеним YAML кодом.
    - Переконайтеся, що у налаштуваннях репозиторію додано секрети `MINIO_ACCESS_KEY` та `MINIO_SECRET_KEY`.
3. **Перевірте локальну генерацію PDF**
    
    - Запустіть Python-скрипт локально, щоб переконатися, що конвертація Markdown у PDF проходить коректно.
    - За необхідності відредагуйте параметри (шляхи до нотаток, додаткові каталоги для ігнорування).
4. **Коміт та пуш змін до GitHub**
    
    - При внесенні змін до нотаток у каталозі `src/site/notes` автоматично спрацює GitHub Actions workflow, який згенерує PDF файли та завантажить їх на MinIO.
5. **Перевірте лог роботи Workflow**
    
    - У розділі GitHub Actions перевірте логи, щоб впевнитися, що всі кроки виконались успішно та PDF файли завантажено.

---

## Висновок

За допомогою цього рішення ви зможете автоматизувати генерацію PDF файлів з нотатками Obsidian. GitHub Actions забезпечить безперервну інтеграцію при внесенні змін, а Python-скрипт дозволить гнучко обробляти Markdown файли та зображення. Це рішення є зручним для тих, хто хоче мати завжди актуальні PDF-версії своїх нотаток з можливістю їх публікації або архівування.

Сподіваємося, що ця стаття допоможе вам налаштувати процес генерації PDF та зробити вашу роботу з Obsidian ще ефективнішою!

---

> **Примітка:** Перед розгортанням переконайтеся, що всі залежності встановлені, а права доступу до серверів (MinIO, Cloudflare) налаштовано коректно.

Happy note-taking та автоматизації!