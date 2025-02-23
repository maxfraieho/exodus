---
{"title":"Докладна інструкція з розгортання та використання проекту openai-to-cloudflare-ai","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/rozgortannya-ta-vikoristannya-openai-to-cloudflare-ai/","dgPassFrontmatter":true,"noteIcon":""}
---


Цей посібник допоможе вам розгорнути та використовувати проект [openai-to-cloudflare-ai](https://github.com/pa4080/openai-to-cloudflare-ai.git) за допомогою Docker. Ми також розглянемо, як вибрати та змінити оптимальну LLM (Large Language Model) для ваших потреб, з урахуванням таблиці моделей, доступних у проекті.

---

### Вступ

Проект [openai-to-cloudflare-ai](https://github.com/pa4080/openai-to-cloudflare-ai.git) дозволяє використовувати моделі OpenAI через Cloudflare Workers, що забезпечує низьку затримку та високу доступність. Для розгортання цього проекту ми будемо використовувати:

- **Docker** для створення локального середовища розробки та тестування.
- **Wrangler** для розгортання Cloudflare Worker'а.

---

### Крок 1: Клонування репозиторію

Спочатку вам потрібно скопіювати репозиторій на ваш локальний комп'ютер. Виконайте наступну команду в терміналі:

```bash
git clone https://github.com/pa4080/openai-to-cloudflare-ai.git
cd openai-to-cloudflare-ai
```

---

### Крок 2: Встановлення Docker

Переконайтеся, що на вашому комп'ютері встановлено Docker. Якщо ні, завантажте та встановіть його з [офіційного сайту](https://www.docker.com/get-started).

---

### Крок 3: Створення Docker-контейнера

У проекті має бути файл `Dockerfile`, який описує, як створити Docker-образ для цього проекту. Якщо файл `Dockerfile` відсутній або потребує адаптації, ви можете використовувати один із наведених нижче прикладів, адаптованих для архітектури arm64.

#### Приклад Dockerfile для `node:18-bullseye-slim`

```dockerfile
FROM node:18-bullseye-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

ARG WRANGLER_VERSION=3.25.0
ARG ESBUILD_VERSION=0.20.1

RUN npm install --global --omit=dev \
    wrangler@${WRANGLER_VERSION} \
    esbuild@${ESBUILD_VERSION} \
    && npm cache clean --force

USER node
WORKDIR /app
VOLUME ["/app"]
ENTRYPOINT ["wrangler"]
```

#### Приклад Dockerfile для `node:18-alpine`

```dockerfile
FROM node:18-alpine

RUN apk add --no-cache curl ca-certificates

ARG WRANGLER_VERSION=3.25.0
ARG ESBUILD_VERSION=0.20.1

RUN npm install --global --omit=dev \
    wrangler@${WRANGLER_VERSION} \
    esbuild@${ESBUILD_VERSION} \
    && npm cache clean --force

USER node
WORKDIR /app
VOLUME ["/app"]
ENTRYPOINT ["wrangler"]
```

Ці Dockerfile:

1. Використовують базові образи Node.js (`node:18-bullseye-slim` або `node:18-alpine`).
2. Встановлюють необхідні залежності, такі як `curl` та `ca-certificates`.
3. Встановлюють глобально `wrangler` (CLI для Cloudflare) та `esbuild`.
4. Налаштовують робочу директорію `/app` і запускають `wrangler` як точку входу.

---

### Крок 4: Збірка Docker-образу

Виконайте наступну команду для збірки Docker-образу. Виберіть один із Dockerfile, який відповідає вашій системі.

```bash
docker build -t openai-to-cloudflare-ai .
```

Ця команда створить Docker-образ із назвою `openai-to-cloudflare-ai`.

---

### Крок 5: Запуск Docker-контейнера

Запустіть контейнер, монтуючи директорію проекту до `/app` всередині контейнера:

```bash
docker run -it -v $(pwd):/app openai-to-cloudflare-ai
```

Ця команда:

- Запускає контейнер у інтерактивному режимі (`-it`).
- Монтує поточну директорію проекту (`$(pwd)`) до `/app` у контейнері (`-v`).

---

### Крок 6: Налаштування середовища

Перед розгортанням вам потрібно налаштувати середовище, включаючи API ключі для OpenAI та Cloudflare. Зазвичай це робиться за допомогою файлу `.env` або через секрети Wrangler.

1. **Створіть файл `.env`** у кореневій директорії проекту з наступним вмістом:

```env
OPENAI_API_KEY=your_openai_api_key
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
```

Замініть:

- `your_openai_api_key` на ваш ключ API від OpenAI.
- `your_cloudflare_api_token` на ваш токен API від Cloudflare.

1. **Налаштуйте Wrangler**: Якщо ви ще не налаштували Wrangler, виконайте команду:

```bash
wrangler login
```

Ця команда відкриє браузер для авторизації у вашому Cloudflare-акаунті.

---

### Крок 7: Вибір та зміна LLM моделі

Проект, ймовірно, містить таблицю або список доступних LLM моделей, які можна використовувати. Ця таблиця може бути у файлі `README.md` або в окремому документі. Для прикладу, припустимо, що доступні наступні моделі:

| Модель                     | Опис                                  | Використання                    |
|----------------------------|---------------------------------------|---------------------------------|
| `gpt-3.5-turbo`            | Швидка та економічна модель для загальних завдань | `model: 'gpt-3.5-turbo'`        |
| `gpt-4`                    | Потужніша модель для складних завдань | `model: 'gpt-4'`                |
| `@cf/meta/llama-3-8b-instruct` | Модель LLaMA для інструкцій          | `model: '@cf/meta/llama-3-8b-instruct'` |

#### Як вибрати оптимальну модель

Щоб вибрати оптимальну LLM модель, враховуйте наступні фактори:

1. **Тип завдання**:
   - Для загальних текстових завдань (наприклад, генерація тексту, відповіді на запитання) підійде `gpt-3.5-turbo`.
   - Для складних завдань (наприклад, аналіз коду, глибокий аналіз тексту) краще використовувати `gpt-4`.
   - Для специфічних інструкцій або завдань, що потребують меншого розміру моделі, використовуйте `@cf/meta/llama-3-8b-instruct`.

2. **Продуктивність та затримка**:
   - Моделі OpenAI (наприклад, `gpt-3.5-turbo`, `gpt-4`) можуть мати вищу затримку через залежність від їхньої інфраструктури.
   - Моделі Cloudflare AI (наприклад, `@cf/meta/llama-3-8b-instruct`) можуть мати нижчу затримку завдяки Cloudflare Workers.

3. **Вартість**:
   - OpenAI моделі можуть бути дорожчими, особливо для великих обсягів запитів.
   - Cloudflare AI моделі можуть бути економічнішими, залежно від вашого тарифного плану.

4. **Тестування**:
   - Рекомендується протестувати кілька моделей із типовими запитами для вашого випадку використання.
   - Оцінюйте якість відповідей, швидкість та стабільність.

#### Як змінити модель

Щоб змінити модель, вам потрібно відредагувати конфігураційний файл або код Worker'а, де вказується назва моделі. Зазвичай це робиться у файлі `wrangler.toml` або безпосередньо в коді JavaScript.

##### Приклад зміни моделі у коді

1. Відкрийте файл `src/index.js` (або інший основний файл Worker'а).
2. Знайдіть рядок, де вказується модель, наприклад:

```javascript
const model = 'gpt-3.5-turbo';
```

1. Змініть його на бажану модель:

```javascript
const model = '@cf/meta/llama-3-8b-instruct';
```

1. Збережіть файл.

##### Приклад зміни моделі через `wrangler.toml`

Якщо модель задається через змінну середовища у `wrangler.toml`, відредагуйте цей файл:

```toml
[vars]
MODEL = "gpt-3.5-turbo"
```

Змініть на:

```toml
[vars]
MODEL = "@cf/meta/llama-3-8b-instruct"
```

---

### Крок 8: Розгортання на Cloudflare

Після налаштування середовища та вибору моделі, розгорніть проект на Cloudflare за допомогою Wrangler:

```bash
wrangler deploy
```

Ця команда:

- Завантажить ваш Worker на Cloudflare.
- Поверне URL, за яким буде доступний ваш Worker (наприклад, `https://your-worker.your-subdomain.workers.dev`).

---

### Крок 9: Тестування

Після розгортання ви можете тестувати ваш Worker, надсилаючи запити до його URL. Наприклад, використовуючи `curl`:

```bash
curl -X POST https://your-worker.your-subdomain.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!"}'
```

Очікувана відповідь залежить від моделі та конфігурації Worker'а. Наприклад, ви можете отримати згенерований текст або відповідь на ваш запит.

---

### Додаткові поради

1. **Локальне тестування з Miniflare**:
   - Якщо ви хочете тестувати Worker локально перед розгортанням, використовуйте `miniflare` (симулятор Cloudflare Workers).
   - Запустіть Worker локально командою:

```bash
wrangler dev
```

1. **Моніторинг та логи**:
   - Використовуйте `wrangler tail` для перегляду логів у реальному часі:

```bash
wrangler tail
```

1. **Оновлення моделі після тестування**:
   - Після тестування кількох моделей, виберіть оптимальну та оновіть конфігурацію.
   - Повторно розгорніть Worker командою `wrangler deploy`.

---

### Висновок

Ви успішно розгорнули та налаштували проект [openai-to-cloudflare-ai](https://github.com/pa4080/openai-to-cloudflare-ai.git) за допомогою Docker та Wrangler. Ви також навчилися вибирати та змінювати LLM моделі для оптимізації під ваші потреби. Пам'ятайте, що вибір оптимальної моделі залежить від конкретного завдання, вимог до продуктивності та бюджету. Експериментуйте з різними моделями, щоб знайти найкращу для вашого випадку.