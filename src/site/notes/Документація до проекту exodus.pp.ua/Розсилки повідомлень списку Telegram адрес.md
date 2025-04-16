---
{"title":"Розсилки повідомлень списку Telegram адрес","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/rozsilki-povidomlen-spisku-telegram-adres/","dgPassFrontmatter":true,"noteIcon":""}
---


# Налаштування Moon-Userbot для автоматизованої розсилки повідомлень

Ця стаття описує покроковий процес налаштування Moon-Userbot у Termux на Android для автоматизованої розсилки персоналізованих повідомлень через Telegram. Ми розглянемо встановлення Termux, розгортання бота, створення скриптів для генерації списку отримувачів, розсилки повідомлень, відстеження відповідей і пошуку нових контактів за допомогою OSINT. Усі скрипти наведено у фінальних версіях, які підтримують чотири мови (uk, ru, fr, fa), транслітерацію імен та персоналізовані прохання.

## 1. Встановлення Termux

Termux — це емулятор терміналу для Android, який дозволяє запускати Python-скрипти та керувати Telegram-ботами.

### Завантажте Termux:

- Завантажте з F-Droid або офіційного GitHub (Termux releases).
- Уникайте Google Play, оскільки версія там застаріла.

### Оновіть пакети:
```bash
pkg update && pkg upgrade
```

### Встановіть необхідні інструменти:
```bash
pkg install python git nano
pip install --upgrade pip
```

### Налаштуйте сховище:

- Дозвольте доступ до пам'яті:
```bash
termux-setup-storage
```

- Перевірте доступ:
```bash
ls /storage/emulated/0
```

### Увімкніть wake-lock:

- Щоб Termux не вимикався:
```bash
termux-wake-lock
```

## 2. Розгортання Moon-Userbot

Moon-Userbot — це модульний Telegram-бот на основі Pyrogram, який дозволяє автоматизувати розсилку та обробку повідомлень.

### Клонуйте репозиторій:
```bash
git clone https://github.com/TheMoonBotDev/Moon-Userbot /storage/emulated/0/termux/Moon-Userbot
cd /storage/emulated/0/termux/Moon-Userbot
```

### Встановіть залежності:
```bash
pip install -r requirements.txt
```

### Налаштуйте API:

- Отримайте api_id і api_hash на my.telegram.org:
  - Увійдіть у Telegram.
  - Перейдіть до "API development tools".
  - Створіть додаток і скопіюйте api_id та api_hash.

- Відкрийте конфігурацію:
```bash
nano config.ini
```

- Додайте:
```ini
[pyrogram]
api_id = ВАШ_API_ID
api_hash = ВАШ_API_HASH
```

- Збережіть (Ctrl+O, Enter, Ctrl+X).

### Запустіть бота:
```bash
python3 main.py
```

- Увійдіть у Telegram-акаунт (введіть номер телефону та код).
- Перевірте лог: має бути Imported X modules.

### Створіть папку для контактів:
```bash
mkdir -p /storage/emulated/0/Documents/exodus/olena/Контакти
```

## 3. Налаштування розсилки

Ми створили три основні модулі для розсилки:

- generate_recipients.py: Генерує список отримувачів із .md файлів.
- bulk_message.py: Надсилає персоналізовані повідомлення.
- response_tracker.py: Відстежує відповіді, надсилає подяки та видаляє контакти.
- Додатковий модуль telegram_osint.py для пошуку нових контактів.

### 3.1. Генерація списку отримувачів (generate_recipients.py)

Цей модуль сканує .md файли в папці /storage/emulated/0/Documents/exodus/olena/Контакти, витягує номери телефонів або @ніки, визначає мову та транслітерує імена з латиниці на кирилицю для uk/ru.

#### Код:
```python
from pyrogram import Client, filters
import os
import re

@Client.on_message(filters.command("generate_recipients", prefixes=".") & filters.me)
async def generate_recipients(client, message):
    # Шлях до папки з .md файлами
    contacts_dir = "/storage/emulated/0/Documents/exodus/olena/Контакти"
    output_file = "recipients.txt"

    # Перевірка, чи папка існує
    if not os.path.exists(contacts_dir):
        await message.edit(f"Помилка: папка {contacts_dir} не знайдена!")
        return

    recipients = []

    # Словник транслітерації
    translit_map = {
        "Sergey": "Сергій", "Aleksandrovich": "Олександрович",
        "Veronika": "Вероніка", "Sadovska": "Садовська",
        "Andrey": "Андрій", "Khmelnitsky": "Хмельницький",
        "Valeria": "Валерія", "Khruliova": "Хрульова",
        "Nataliya": "Наталія", "Urtikova": "Уртікова",
        "Olga": "Ольга", "Moldavanova": "Молдованова",
        "Tania": "Таня", "Cherniy": "Чорний",
        "Viktoriia": "Вікторія", "Sysoieva": "Сисоєва",
        "Zhanna": "Жанна", "Lytvynenko": "Литвиненко",
        "Vadim": "Вадим", "Karlovskij": "Карловський",
        "Tetiana": "Тетяна", "Allgower": "Аллговер",
        "Nadezhda": "Надія", "Mishchenko": "Міщенко",
        "Oleg": "Олег",
        "Oleh": "Олег", "Prikhodko": "Приходько",
        "Anna": "Анна", "Prisyazhnyuk": "Присяжнюк",
        "Roman": "Роман", "Hnatiuk": "Гнатюк",
        "Irina": "Ірина", "Primak": "Примак",
        "Yuliya": "Юлія", "Zasadnaya": "Засадна",
        "Lyuda": "Люда", "Gland": "Гланд",
        "Aleksandra": "Олександра",
        "Anastasiya": "Анастасія",
        "Rostislav": "Ростислав",
        "Mariia": "Марія", "Marriya": "Марія",
        "Inna": "Інна",
        "Karolina": "Кароліна",
        "Victoria": "Вікторія", "Lisovaya": "Лісова",
        "Myroslav": "Мирослав",
        "Oleksandr": "Олександр", "Levchenko": "Левченко",
        "Mikhail": "Михайло",
        "Elvira": "Ельвіра",
        "Elena": "Олена",
        "Alena": "Альона",
        "Anzhela": "Анжела",
        "Katia": "Катя",
        "Nadiia": "Надія",
        "Maria": "Марія",
        "Artem": "Артем",
        "Vika": "Віка",
        "Vlad": "Влад",
        "Lyuba": "Люба",
        "Anya": "Аня",
        "Zyrianova": "Зирянова"
    }

    # Прості списки для визначення мови
    ukrainian_names = {"Олена", "Андрій", "Вікторія", "Іван", "Марія", "Вадим", "Тетяна", "Надія", "Олег", "Анна", "Роман", "Ірина", "Юлія", "Мирослав", "Жанна", "Кароліна", "Катя", "Влад", "Люба", "Аня", "Вероніка", "Таня", "Ельвіра", "Артем", "Віка", "Альона", "Анжела"}
    russian_names = {"Ольга", "Сергій", "Наталія", "Олександра", "Михайло", "Олена", "Анастасія", "Анна"}
    french_names = {"Louise", "Felix", "Annie", "Frank", "Loret"}
    persian_names = {"Javad", "Rahmat", "Murtaza", "Daira", "RM"}

    # Сканування .md файлів
    for filename in os.listdir(contacts_dir):
        if filename.endswith(".md"):
            # Ім'я отримувача — назва файлу без .md
            recipient_name = filename[:-3].strip()

            # Читання вмісту файлу
            file_path = os.path.join(contacts_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()

                # Пошук номера телефону (починається з +)
                phone_match = re.search(r"\+\d[\d\s]*\d", content)
                phone_number = None
                if phone_match:
                    # Видалити пробіли з номера
                    phone_number = "".join(phone_match.group().split())

                # Пошук @ніка (починається з @)
                nick_match = re.search(r"@[a-zA-Z0-9_]+", content)
                nick = nick_match.group() if nick_match else None

                # Визначення мови
                language = "uk"  # За замовчуванням українська
                name_parts = recipient_name.split()
                first_name = name_parts[0] if name_parts else recipient_name

                # Транслітерація імені
                translit_name = recipient_name
                for latin, cyrillic in translit_map.items():
                    translit_name = translit_name.replace(latin, cyrillic)

                if phone_number and phone_number.startswith("+380"):
                    language = "uk"
                elif phone_number and phone_number.startswith("+417"):
                    if first_name in russian_names or (nick and "rus" in nick.lower()):
                        language = "ru"
                    elif first_name in french_names:
                        language = "fr"
                    elif first_name in persian_names:
                        language = "fa"
                elif nick:
                    if first_name in russian_names or (nick and "rus" in nick.lower()):
                        language = "ru"
                    elif first_name in french_names or (nick and "fr" in nick.lower()):
                        language = "fr"
                    elif first_name in persian_names or (nick and any(x in nick.lower() for x in ["java", "rahmat", "murtaza"])):
                        language = "fa"
                    elif first_name in ukrainian_names or (nick and "ukr" in nick.lower()):
                        language = "uk"

                # Застосовуємо транслітерацію лише для uk/ru
                final_name = translit_name if language in ["uk", "ru"] else recipient_name

                # Пріоритет: номер телефону, якщо є, інакше @нік
                if phone_number:
                    recipients.append(f"{phone_number},{final_name},{language}")
                elif nick:
                    recipients.append(f"{nick},{final_name},{language}")
                else:
                    print(f"У файлі {filename} немає номера телефону або @ніка")

            except Exception as e:
                print(f"Помилка при обробці файлу {filename}: {e}")

    # Запис у recipients.txt
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            for recipient in recipients:
                file.write(f"{recipient}\n")
        await message.edit(f"Файл {output_file} створено! Знайдено {len(recipients)} контактів.")
    except Exception as e:
        await message.edit(f"Помилка при записі {output_file}: {e}")
```

#### Налаштування:

- Збережіть:
```bash
nano /storage/emulated/0/termux/Moon-Userbot/modules/generate_recipients.py
```

- Скопіюйте код, збережіть (Ctrl+O, Enter, Ctrl+X).

#### Створіть .md файли:

Наприклад:
```bash
echo "Телефон: +380930949209" > /storage/emulated/0/Documents/exodus/olena/Контакти/Олена.md
echo "@IvanP" > /storage/emulated/0/Documents/exodus/olena/Контакти/Іван\ Петренко.md
```

#### Запустіть:
```bash
.generate_recipients
```

Вихід: recipients.txt із рядками ідентифікатор,ім'я,мова.

### 3.2. Розсилка повідомлень (bulk_message.py)

Цей модуль надсилає персоналізовані повідомлення із проханням допомогти знайти Олену Коваленко, адаптовані до мови контакту.

#### Код:
```python
from pyrogram import Client, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from pyrogram.types import InputPhoneContact

# Ініціалізація планувальника
scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")

@Client.on_message(filters.command("bulksend", prefixes=".") & filters.me)
async def bulk_send(client, message):
    async def send_messages():
        sent_count = 0
        failed_count = 0

        try:
            with open("recipients.txt", "r") as file:
                recipients = [line.strip().split(",", 2) for line in file if line.strip()]
        except FileNotFoundError:
            await message.edit("Помилка: файл recipients.txt не знайдено!")
            return

        # Тексти повідомлень для кожної мови
        messages = {
            "uk": "{name}, добрий день! Мене звати [Ваше ім'я]. Моя дружина, Олена Коваленко (можливо, Суворова), перебуває в Швейцарії як біженка. Я шукаю людей, які можуть її знати, щоб допомогти зберегти нашу сім'ю. Якщо ви маєте будь-яку інформацію, будь ласка, зв'яжіться зі мною. Дякую!",
            "ru": "{name}, здравствуйте! Меня зовут [Ваше имя]. Моя жена, Олена Коваленко (возможно, Суворова), находится в Швейцарии как беженка. Я ищу людей, которые могут её знать, чтобы помочь сохранить нашу семью. Если у вас есть какая-либо информация, пожалуйста, свяжитесь со мной. Спасибо!",
            "fr": "{name}, bonjour ! Je m'appelle [Votre nom]. Ma femme, Olena Kovalenko (peut-être Suvorova), est en Suisse en tant que réfugiée. Je cherche des personnes qui pourraient la connaître pour aider à préserver notre famille. Si vous avez des informations, veuillez me contacter. Merci !",
            "fa": "{name}, سلام! نام من [نام شما] است. همسرم، اولنا کووالنکو (شاید سوورووا)، به عنوان پناهنده در سوئیس است. من به دنبال افرادی هستم که ممکن است او را بشناسند تا به حفظ خانواده‌مان کمک کنم. اگر اطلاعاتی دارید، لطفاً با من تماس بگیرید. متشکریم!"
        }

        for recipient_data in recipients:
            if len(recipient_data) != 3:
                failed_count += 1
                print(f"Неправильний формат для {recipient_data}: очікується ідентифікатор,ім'я,мова")
                continue

            recipient, name, language = recipient_data
            recipient = recipient.strip()
            name = name.strip()
            language = language.strip()

            # Перевірка, чи контакт ще в списку
            with open("recipients.txt", "r") as file:
                current_recipients = [line.strip().split(",", 2)[0] for line in file if line.strip()]
            if recipient not in current_recipients:
                continue

            # Формуємо повідомлення
            base_text = messages.get(language, messages["uk"]).format(name=name)
            personalized_text = base_text

            try:
                if recipient.startswith("+"):
                    contact = InputPhoneContact(phone=recipient, first_name=f"Contact_{recipient[-4:]}")
                    imported_contacts = await client.import_contacts([contact])
                    user = imported_contacts.users[0] if imported_contacts.users else None

                    if user:
                        user_id = user.id
                        try:
                            await client.send_message(user_id, personalized_text)
                            sent_count += 1
                            await asyncio.sleep(1)
                        except Exception as e:
                            failed_count += 1
                            print(f"Помилка при відправці до {recipient} ({name}): {e}")
                    else:
                        failed_count += 1
                        print(f"Не вдалося імпортувати контакт {recipient} ({name})")
                else:
                    await client.send_message(recipient, personalized_text)
                    sent_count += 1
                    await asyncio.sleep(1)
            except Exception as e:
                failed_count += 1
                print(f"Помилка при відправці до {recipient} ({name}): {e}")

        await client.send_message(
            message.chat.id,
            f"Розсилка завершена! Надіслано: {sent_count}, Помилок: {failed_count}"
        )

    await send_messages()

    if not scheduler.get_job("bulk_send_messages"):
        scheduler.add_job(send_messages, "cron", hour=9, minute=0, id="bulk_send_messages")
        if not scheduler.running:
            scheduler.start()
            await message.edit("Розсилка запущена та запланована на 9:00 щодня!")
        else:
            await message.edit("Розсилка запущена, розклад уже активний!")
    else:
        await message.edit("Розсилка запущена, розклад уже налаштовано!")

@Client.on_message(filters.command("stopbulksend", prefixes=".") & filters.me)
async def stop_bulk_send(client, message):
    if scheduler.get_job("bulk_send_messages"):
        scheduler.remove_job("bulk_send_messages")
        await message.edit("Розклад розсилки зупинено!")
    else:
        await message.edit("Розклад розсилки не активний!")
```

#### Налаштування:

- Збережіть:
```bash
nano /storage/emulated/0/termux/Moon-Userbot/modules/bulk_message.py
```

- Замініть [Ваше ім'я] на ваше ім'я.
- Запустіть:
```bash
.bulksend
```

Повідомлення надсилаються з розкладом о 9:00 щодня.
Зупиніть розклад:
```bash
.stopbulksend
```

### 3.3. Відстеження відповідей (response_tracker.py)

Цей модуль реагує на відповіді від контактів, надсилає подяку відповідною мовою, сповіщає @kroschu та видаляє контакт із recipients.txt.

#### Код:
```python
from pyrogram import Client, filters
import os

@Client.on_message(filters.private & ~filters.me)
async def track_response(client, message):
    # Шлях до recipients.txt
    recipients_file = "recipients.txt"
    
    # Перевірка, чи файл існує
    if not os.path.exists(recipients_file):
        return

    # Отримання інформації про відправника
    sender_id = str(message.from_user.id)
    sender_username = f"@{message.from_user.username}" if message.from_user.username else None
    sender_phone = message.from_user.phone_number if message.from_user.phone_number else None

    # Читання recipients.txt
    try:
        with open(recipients_file, "r", encoding="utf-8") as file:
            recipients = [line.strip().split(",", 2) for line in file if line.strip()]
    except Exception as e:
        print(f"Помилка при читанні {recipients_file}: {e}")
        return

    # Пошук абонента
    recipient_data = None
    for data in recipients:
        if len(data) != 3:
            continue
        identifier, name, language = data
        identifier = identifier.strip()

        # Перевірка збігу за user_id, @ніком або номером телефону
        if (
            identifier == sender_id
            or (sender_username and identifier.lower() == sender_username.lower())
            or (sender_phone and identifier.replace(" ", "") == f"+{sender_phone.replace(' ', '')}")
        ):
            recipient_data = data
            break

    if not recipient_data:
        return

    # Витягуємо дані абонента
    identifier, name, language = recipient_data

    # Тексти подяки для кожної мови
    thank_you_messages = {
        "uk": f"{name}, дякуємо за вашу відповідь!",
        "ru": f"{name}, спасибо за ваш ответ!",
        "fr": f"{name}, merci pour votre réponse !",
        "fa": f"{name}, از پاسخ شما متشکریم!"
    }

    # Вибираємо текст подяки
    thank_you_text = thank_you_messages.get(language, thank_you_messages["uk"])  # За замовчуванням uk

    # Формуємо повідомлення для @kroschu
    response_text = message.text or message.caption or "(немає тексту)"
    notification = f"!!! Відповідь від {name} ({identifier}): {response_text} !!!"

    try:
        # Надсилаємо подяку абоненту
        await message.reply(thank_you_text)

        # Надсилаємо повідомлення @kroschu
        await client.send_message("@kroschu", notification)

        # Видаляємо абонента з recipients.txt
        recipients.remove(recipient_data)
        with open(recipients_file, "w", encoding="utf-8") as file:
            for data in recipients:
                file.write(f"{','.join(data)}\n")
        
        print(f"Абонента {name} ({identifier}) видалено з {recipients_file}")

    except Exception as e:
        print(f"Помилка при обробці відповіді від {name} ({identifier}): {e}")
```

#### Налаштування:

- Збережіть:
```bash
nano /storage/emulated/0/termux/Moon-Userbot/modules/response_tracker.py
```

- Перевірте, чи @kroschu доступний для userbot:
```bash
python3 -c "from pyrogram import Client; Client('userbot').start().send_message('@kroschu', 'Тест').stop()"
```

### 3.4. Пошук нових контактів (telegram_osint.py)

Цей модуль шукає Telegram-групи за ключовим словом (наприклад, "Ukrainian refugees Switzerland") і витягує учасників для додавання до recipients.txt.

#### Код:
```python
from pyrogram import Client, filters
import os
import asyncio

app = Client("userbot")

@app.on_message(filters.command("find_groups", prefixes=".") & filters.me)
async def find_groups(client, message):
    # Шлях для збереження результатів
    output_file = "telegram_groups.txt"
    search_query = "Ukrainian refugees Switzerland"  # Запит для пошуку груп

    try:
        groups = []
        # Пошук чатів за ключовим словом
        async for dialog in client.search_global(search_query, limit=50):
            if dialog.chat.type in ["group", "supergroup"]:
                groups.append(f"{dialog.chat.title},@{dialog.chat.username or dialog.chat.id}")
        
        # Збереження результатів
        with open(output_file, "w", encoding="utf-8") as file:
            for group in groups:
                file.write(f"{group}\n")
        
        await message.edit(f"Знайдено {len(groups)} груп. Результати збережено в {output_file}")
    
    except Exception as e:
        await message.edit(f"Помилка: {e}")

@app.on_message(filters.command("scrape_members", prefixes=".") & filters.me)
async def scrape_members(client, message):
    if not message.reply_to_message:
        await message.edit("Відповідайте на повідомлення з назвою групи (@username або ID)")
        return
    
    chat_id = message.reply_to_message.text.split(",")[1].strip()
    output_file = "telegram_members.txt"
    
    try:
        members = []
        async for member in client.get_chat_members(chat_id):
            user = member.user
            username = f"@{user.username}" if user.username else None
            phone = user.phone_number if user.phone_number else None
            name = f"{user.first_name} {user.last_name or ''}".strip()
            if username or phone:
                members.append(f"{username or phone},{name},uk")  # Припускаємо uk
                
        # Збереження результатів
        with open(output_file, "w", encoding="utf-8") as file:
            for member in members:
                file.write(f"{member}\n")
        
        await message.edit(f"Знайдено {len(members)} учасників. Результати збережено в {output_file}")
    
    except Exception as e:
        await message.edit(f"Помилка: {e}")

if __name__ == "__main__":
    app.run()
```

#### Налаштування:

- Збережіть:
```bash
nano /storage/emulated/0/termux/Moon-Userbot/modules/telegram_osint.py
```

- Запустіть:
```bash
.find_groups
```

- Отримайте telegram_groups.txt.

- Виберіть групу та виконайте:
```bash
.scrape_members
```

- Отримайте telegram_members.txt.

- Додайте контакти:
```bash
cat telegram_members.txt >> recipients.txt
```

## 4. Тестування системи

### Підготовка:

- Переконайтеся, що recipients.txt містить контакти:
```bash
cat /storage/emulated/0/termux/Moon-Userbot/recipients.txt
```

- Тестовий приклад:
```bash
echo -e "@testuser1,Тест Український,uk\n@testuser2,Тест Русский,ru" > recipients.txt
```

### Генерація:
```bash
.generate_recipients
```

- Перевірте recipients.txt.

### Розсилка:
```bash
.bulksend
```

- Перевірте, чи контакти отримали повідомлення:
  - Тест Український, добрий день! ...
  - Тест Русский, здравствуйте! ...

### Відповіді:

- Надішліть відповідь від @testuser1: Дякую за повідомлення.
- Очікуйте:
  - Подяку: Тест Український, дякуємо за вашу відповідь!.
  - Сповіщення @kroschu: !!! Відповідь від Тест Український (@testuser1): Дякую за повідомлення !!!.
  - Видалення з recipients.txt.

### OSINT:

- Виконайте:
```bash
.find_groups
.scrape_members
```

- Додайте нові контакти до recipients.txt.

## 5. Вирішення проблем

### Termux вимикається:

- Увімкніть wake-lock:
```bash
termux-wake-lock
```

- Вимкніть оптимізацію батареї в налаштуваннях Android.

### Помилка Flood control:

- Збільште затримку в bulk