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