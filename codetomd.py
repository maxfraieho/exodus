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

    # Рекурсивний обхід директорії
    for current_path, dirs, files in os.walk(root_dir):
        # Фільтруємо директорії для ігнорування
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
        for file_name in files:
            full_file_path = os.path.join(current_path, file_name)
            _, ext = os.path.splitext(file_name.lower())
            if ext == '.md':
                list_md_files.append(full_file_path)

    # Обробка стандартних Markdown-зображень: ![alt](image.png)
    std_image_pattern = re.compile(r'!\[.*?\]\(([^)]+)\)')
    # Обробка Obsidian-синтаксису: ![[image.png]] або ![[image.png|alt text]]
    obsidian_image_pattern = re.compile(r'!\[\[([^|\]]+)(?:\|[^\]]+)?\]\]')

    for md_path in list_md_files:
        try:
            with open(md_path, 'r', encoding='utf-8') as md_file:
                content = md_file.read()
        except Exception as e:
            print(f"Не вдалося прочитати {md_path}: {e}")
            continue

        # Знаходимо стандартні зображення
        std_matches = std_image_pattern.findall(content)
        for img_src in std_matches:
            if not (img_src.startswith("http") or img_src.startswith("data:")):
                _, img_ext = os.path.splitext(img_src.lower())
                if img_ext in image_extensions:
                    full_img_path = os.path.normpath(os.path.join(os.path.dirname(md_path), img_src))
                    set_image_paths.add(full_img_path)

        # Знаходимо зображення у форматі Obsidian
        obsidian_matches = obsidian_image_pattern.findall(content)
        for img_src in obsidian_matches:
            if not (img_src.startswith("http") or img_src.startswith("data:")):
                _, img_ext = os.path.splitext(img_src.lower())
                if img_ext in image_extensions:
                    full_img_path = os.path.normpath(os.path.join(os.path.dirname(md_path), img_src))
                    set_image_paths.add(full_img_path)

    return list_md_files, set_image_paths

def convert_markdown_files_to_combined_html(md_files):
    """
    Конвертує кожен Markdown-файл у HTML, коригує відносні посилання на зображення 
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
                # Перетворюємо у file URI (це дозволяє WeasyPrint завантажувати зображення з файлової системи)
                img["src"] = Path(abs_img_path).as_uri()
        html_fragment = str(soup)
        # Додаємо фрагмент до загального HTML із розділювальною горизонтальною лінією
        combined_html += html_fragment
        combined_html += "<hr style='page-break-after: always; border: none;'>"
    combined_html += "</body></html>"
    return combined_html

def main():
    print("=== Генеруємо PDF для кожної підпапки з Markdown ===\n")
    
    # Встановлюємо базову директорію. За замовчуванням використовуємо "src/site/notes"
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
        
        # Знаходимо Markdown-файли у поточній підпапці (рекурсивно)
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
