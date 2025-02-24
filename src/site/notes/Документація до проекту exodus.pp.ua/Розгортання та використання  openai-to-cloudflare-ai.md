---
{"title":"Докладна інструкція з розгортання та використання проекту openai-to-cloudflare-ai","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/rozgortannya-ta-vikoristannya-openai-to-cloudflare-ai/","dgPassFrontmatter":true,"noteIcon":""}
---

# Розгортання  openai-to-cloudflare-ai для обходу обмежень безкоштовного білінгу Cloudflare AI

Привіт! У цій статті я розповім, як розгорнути проєкт [openai-to-cloudflare-ai](https://github.com/pa4080/openai-to-cloudflare-ai) на Cloudflare Workers за допомогою Docker і Wrangler, а також як використати його для обходу обмежень безкоштовного плану Cloudflare AI, зокрема для роботи з API-ендпоінтами потоків (`/v1/threads` і `/v1/threads/:id/runs`). Формат статті адаптовано для зручного використання в Obsidian.

---

## Вступ

Cloudflare AI у безкоштовному плані має обмеження на кількість запитів і обсяг даних, що може ускладнити роботу з API, наприклад, для створення та управління потоками (`threads`). Проєкт **openai-to-cloudflare-ai** дозволяє перенаправляти запити до Cloudflare AI через ваш власний Worker, імітуючи API OpenAI, а також оптимізувати використання ресурсів за допомогою Cloudflare KV. У цій статті ми розглянемо процес розгортання та методи обходу лімітів.

---

## Налаштування проєкту

### 1. Підготовка середовища

Для початку переконайтеся, що у вас встановлено **Docker** і **Docker Compose**. Потім виконайте наступні кроки:

- **Створіть файл `.env`** у кореневій директорії проєкту з вашими Cloudflare-даними:
  ```plaintext
  CLOUDFLARE_API_TOKEN=your_api_token
  CLOUDFLARE_ACCOUNT_ID=your_account_id
  ```

- Завантажте репозиторій проєкту (це буде зроблено автоматично в Dockerfile).

---

### 2. Конфігурація `wrangler.toml`

Файл `wrangler.toml` визначає налаштування вашого Worker’а. Ось приклад конфігурації:

```toml
name = "ai-forwarder"
compatibility_date = "2025-02-21"
main = "src/index.ts"
assets = { directory = "public", binding = "ASSETS" }

[ai]
binding = "AI"

[vars]
DEFAULT_AI_MODEL = "@hf/meta-llama/meta-llama-3-8b-instruct"

[[kv_namespaces]]
binding = "CACHE"
id = "0c34b71fd97f428089974a20bc8e04e6"
preview_id = "523914b9aed14f7a9131b4c6349de83a"

[observability.logs]
enabled = true
```

- `name`: Ім’я вашого Worker’а.
- `compatibility_date`: Дата сумісності для Wrangler.
- `[ai]`: Прив’язка до Cloudflare AI.
- `[vars]`: Змінні, наприклад, модель за замовчуванням.
- `[[kv_namespaces]]`: Налаштування KV для кешування (замініть `id` і `preview_id` на ваші після створення KV namespace).

---

### 3. Створення Dockerfile

Ось Dockerfile для побудови образу з Wrangler і залежностями:

```dockerfile
FROM node:18-alpine

# 1. Встановлюємо системні пакети
RUN apk add --no-cache git curl ca-certificates

# 2. Задаємо версії Wrangler та esbuild
ARG WRANGLER_VERSION=3.109.3
ARG ESBUILD_VERSION=0.20.1

# 3. Встановлюємо Wrangler, esbuild і pnpm глобально
RUN npm install --global --omit=dev \
    wrangler@${WRANGLER_VERSION} \
    esbuild@${ESBUILD_VERSION} \
    pnpm@latest \
    && npm cache clean --force

# 4. Створюємо теку /app і надаємо права користувачу node
RUN mkdir -p /app && chown node:node /app

# 5. Перемикаємося на користувача node
USER node
WORKDIR /app

# 6. Клонуємо репозиторій
RUN git clone https://github.com/pa4080/openai-to-cloudflare-ai.git .

# 7. Встановлюємо залежності
RUN pnpm install

# 8. Задаємо точку входу
ENTRYPOINT ["wrangler"]
```

Цей файл:
- Використовує Node.js 18 на базі Alpine Linux.
- Встановлює Wrangler, esbuild і pnpm глобально.
- Клонує проєкт і встановлює його залежності.

---

### 4. Налаштування `docker-compose.yml`

Файл `docker-compose.yml` дозволяє запускати різні команди Wrangler:

```yaml
version: "3.9"

services:
  base:
    image: ktoschu/wrangler3-109-3-arm-alpine:latest
    container_name: wrangler-base
    env_file:
      - .env
    volumes:
      - ./:/app
    working_dir: /app
    command: ["echo", "Base service: use docker-compose run <service> for commands"]

  create-kv:
    image: ktoschu/wrangler3-109-3-arm-alpine:latest
    container_name: wrangler-create-kv
    env_file:
      - .env
    volumes:
      - ./:/app
    working_dir: /app
    command: ["kv:namespace", "create", "KV"]

  create-kv-preview:
    image: ktoschu/wrangler3-109-3-arm-alpine:latest
    container_name: wrangler-create-kv-preview
    env_file:
      - .env
    volumes:
      - ./:/app
    working_dir: /app
    command: ["kv:namespace", "create", "KV", "--preview"]

  install:
    image: ktoschu/wrangler3-109-3-arm-alpine:latest
    container_name: wrangler-install
    env_file:
      - .env
    volumes:
      - ./:/app
    working_dir: /app
    command: ["pnpm", "install"]

  deploy:
    image: ktoschu/wrangler3-109-3-arm-alpine:latest
    container_name: wrangler-deploy
    env_file:
      - .env
    volumes:
      - ./:/app
    working_dir: /app
    command: ["deploy"]

  dev:
    image: ktoschu/wrangler3-109-3-arm-alpine:latest
    container_name: wrangler-dev
    env_file:
      - .env
    volumes:
      - ./:/app
    working_dir: /app
    command: ["dev"]
```

---

### 5. Розгортання проєкту

1. **Побудуйте образ**:
   ```bash
   docker build -t wrangler-custom .
   ```
   (Або використовуйте готовий образ `ktoschu/wrangler3-109-3-arm-alpine:latest`).

2. **Створіть KV namespace**:
   ```bash
   docker-compose run create-kv
   docker-compose run create-kv-preview
   ```
   Оновіть `wrangler.toml` з отриманими `id` і `preview_id`.

3. **Встановіть залежності**:
   ```bash
   docker-compose run install
   ```

4. **Розгорніть проєкт**:
   ```bash
   docker-compose run deploy
   ```

5. **Тестування локально (опціонально)**:
   ```bash
   docker-compose run dev
   ```

---

## Обхід обмежень Cloudflare AI

Тепер, коли проєкт розгорнуто, розглянемо, як обійти обмеження безкоштовного плану Cloudflare AI, зокрема для ендпоінтів потоків:

### Підтримувані ендпоінти
- **`/v1/threads` POST**: Створює новий потік.
- **`/v1/threads/:id` GET**: Отримує дані потоку.
- **`/v1/threads/:id` POST**: Модифікує потік.
- **`/v1/threads/:id` DELETE**: Видаляє потік.
- **`/v1/threads/:id/runs` POST**: Створює виконання для потоку (звичайне або зі стрімінгом).

### Методи оптимізації

1. **Кешування відповідей у KV**  
   - Зберігайте відповіді на часті запити (наприклад, GET-запити до `/v1/threads/:id`) у Cloudflare KV.  
   - Приклад: якщо потік не змінився, повертайте кешовані дані замість нового запиту до AI.  
   - Це зменшує кількість звернень до API.

2. **Збереження стану потоків**  
   - Для `/v1/threads` і `/v1/threads/:id/runs` зберігайте стан потоків у KV замість створення нових.  
   - Наприклад, після створення потоку за POST-запитом до `/v1/threads`, запишіть його ID і метадані в KV. При наступних запитах (GET або POST) використовуйте ці дані.

3. **Мінімізація запитів**  
   - Об’єднуйте операції в одному запиті, де це можливо. Наприклад, модифікацію потоку (`/v1/threads/:id` POST) можна виконувати локально в KV, а потім синхронізувати з AI лише за потреби.

4. **Локальне тестування**  
   - Використовуйте `docker-compose run dev` для налагодження, щоб не витрачати квоту на реальні запити.

5. **Розподіл навантаження**  
   - Якщо у вас кілька Worker’ів, розподіляйте запити між ними, щоб уникнути перевищення лімітів одного Worker’а.

---

## Висновок

Розгортання **openai-to-cloudflare-ai** за допомогою Docker і Wrangler дозволяє ефективно використовувати Cloudflare AI у безкоштовному плані. Завдяки кешуванню в KV, оптимізації потоків і локальному тестуванню ви можете значно зменшити кількість запитів і обійти обмеження. Цей підхід ідеально підходить для роботи з потоками (`/v1/threads` і `/v1/threads/:id/runs`), забезпечуючи гнучкість і економію ресурсів. Успіхів у вашому проєкті!