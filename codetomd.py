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
    Конвертує кожен Markdown-файл у HTML, виправляє відносні посилання на зображення (перетворюючи їх у абсолютні file URI)
    та об'єднує результати в один HTML-документ.
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
    print("=== Перетворення всіх .md у PDF ===\n")
    
    # За замовчуванням беремо директорію, де знаходиться скрипт
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = input(f"Введіть шлях до проєкту (за замовчуванням {script_dir}): ").strip() or script_dir
    output_pdf = input("Вкажіть ім'я вихідного PDF (за замовчуванням merged.pdf): ").strip() or "merged.pdf"
    additional_ignore_str = input("Додаткові папки для ігнорування (через кому чи пробіл) або Enter: ").strip()
    additional_ignore = set()
    if additional_ignore_str:
        additional_ignore = {d.strip() for d in additional_ignore_str.replace(',', ' ').split()}

    # Знаходимо Markdown-файли та посилання на зображення
    md_files, img_paths = find_markdown_and_images(
        root_dir=root_dir,
        ignore_dirs={'.git', 'node_modules', 'venv', 'dist', '__pycache__'}.union(additional_ignore),
        image_extensions={'.png', '.jpg', '.jpeg', '.gif', '.svg'}
    )
    if not md_files:
        print("Не знайдено жодного .md-файлу. Завершення.")
        return

    print("\nЗнайдено Markdown-файли:")
    for m in md_files:
        print("  ", m)

    # Перевірка існування зображень (опційно)
    missing_images = [img for img in img_paths if not os.path.isfile(img)]
    if missing_images:
        print("\nУВАГА! Зображення, які згадано, але не існують:")
        for mi in missing_images:
            print("  ", mi)
        print("Перевірте правильність шляхів до зображень.\n")

    print("Генеруємо об'єднаний HTML з усіх Markdown-файлів...")
    combined_html = convert_markdown_files_to_combined_html(md_files)

    print("Конвертуємо HTML у PDF за допомогою WeasyPrint...")
    try:
        # base_url потрібен для коректного завантаження ресурсів
        HTML(string=combined_html, base_url=root_dir).write_pdf(output_pdf)
        print(f"PDF успішно сформовано: {output_pdf}")
    except Exception as e:
        print("Помилка під час конвертації у PDF:", e)

    print("Скрипт завершено.")

if __name__ == "__main__":
    main()