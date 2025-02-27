---
{"title":"Розгортання проекту cloudflare-retrieval-augmented-generation-example на основі Docker","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/rozgortannya-proektu-cloudflare-retrieval-augmented-generation-example-na-osnovi-docker/","dgPassFrontmatter":true,"noteIcon":""}
---



Проект **cloudflare-retrieval-augmented-generation-example** демонструє створення Retrieval-Augmented Generation (RAG) додатку з використанням інструментів Cloudflare AI, таких як Workers AI, Vectorize та D1. У цій статті ми розглянемо процес розгортання цього проекту за допомогою Docker, адаптуючи шаблон, аналогічний до проекту **openai-to-cloudflare-ai**. Оскільки Cloudflare AI у безкоштовному плані має обмеження на кількість запитів і обсяг даних, ми також запропонуємо методи оптимізації для обходу цих лімітів.

---

## Налаштування проєкту

### 1. Підготовка середовища

Для початку переконайтеся, що у вас встановлено **Docker** і **Docker Compose**. Потім виконайте наступні кроки:

- **Створіть файл `.env`** у кореневій директорії проекту з вашими Cloudflare-даними:
  ```
  CLOUDFLARE_API_TOKEN=your_api_token
  CLOUDFLARE_ACCOUNT_ID=your_account_id
  ```
- Репозиторій проекту буде автоматично завантажено через Dockerfile.

---

### 2. Конфігурація `wrangler.toml`

Файл `wrangler.toml` визначає налаштування вашого Cloudflare Worker’а. Ось приклад конфігурації для проекту RAG:

```toml
name = "rag-example"
compatibility_date = "2025-02-21"
main = "src/index.ts"
assets = { directory = "public", binding = "ASSETS" }

[ai]
binding = "AI"

[vars]
DEFAULT_AI_MODEL = "@hf/meta-llama/meta-llama-3-8b-instruct"

[[d1_databases]]
binding = "DATABASE"
database_name = "<your_database_name>"
database_id = "<your_database_id>"

[[vectorize]]
binding = "VECTOR_INDEX"
index_name = "<your_vector_index_name>"

[[kv_namespaces]]
binding = "CACHE"
id = "<your_kv_id>"
preview_id = "<your_kv_preview_id>"

[observability.logs]
enabled = true
```

#### Пояснення:
- **`name`**: Ім’я вашого Worker’а.
- **`compatibility_date`**: Дата сумісності для Wrangler.
- **`[ai]`**: Прив’язка до Cloudflare AI.
- **`[vars]`**: Змінні, наприклад, модель за замовчуванням.
- **`[[d1_databases]]`**: Налаштування бази даних D1 (замініть `<your_database_name>` і `<your_database_id>` на ваші дані).
- **`[[vectorize]]`**: Налаштування для Vectorize (замініть `<your_vector_index_name>` на ваше ім’я індексу).
- **`[[kv_namespaces]]`**: Налаштування KV для кешування (замініть `<your_kv_id>` і `<your_kv_preview_id>` після створення KV namespace).

---

### 3. Створення `Dockerfile`

Ось приклад `Dockerfile` для побудови образу з Wrangler і залежностями:

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
RUN git clone https://github.com/kristianfreeman/cloudflare-retrieval-augmented-generation-example.git .

# 7. Встановлюємо залежності
RUN pnpm install

# 8. Задаємо точку входу
ENTRYPOINT ["wrangler"]
```

#### Пояснення:
- Використовується **Node.js 18** на базі Alpine Linux для легкості образу.
- Встановлюються **Wrangler**, **esbuild** і **pnpm** глобально.
- Репозиторій клонується з GitHub, після чого встановлюються залежності.

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

#### Пояснення:
- **`base`**: Базовий сервіс для запуску команд.
- **`create-kv` та `create-kv-preview`**: Створення KV namespace для кешування.
- **`install`**: Встановлення залежностей проекту.
- **`deploy`**: Розгортання проекту на Cloudflare.
- **`dev`**: Локальний запуск для тестування.

---

### 5. Розгортання проєкту

Виконайте наступні кроки для розгортання:

#### Побудова образу
```bash
docker build -t wrangler-custom .
```
(Або використовуйте готовий образ `ktoschu/wrangler3-109-3-arm-alpine:latest`).

#### Створення KV namespace
```bash
docker-compose run create-kv
docker-compose run create-kv-preview
```
- Після цього оновіть `wrangler.toml` з отриманими `id` і `preview_id`.

#### Встановлення залежностей
```bash
docker-compose run install
```

#### Розгортання проєкту
```bash
docker-compose run deploy
```

#### Тестування локально (опціонально)
```bash
docker-compose run dev
```

---

## Обхід обмежень Cloudflare AI

Безкоштовний план Cloudflare AI має обмеження на кількість запитів і обсяг даних, що може ускладнити роботу з RAG-додатком. Ось методи оптимізації для ефективного використання ресурсів:

### 1. Кешування відповідей у KV
- Зберігайте часті запити (наприклад, результати пошуку чи генерації тексту) у Cloudflare KV.
- **Приклад**: Якщо користувач повторно запитує ту саму інформацію, повертайте кешовані дані замість звернення до AI.
- **Ефект**: Зменшує кількість запитів до API.

### 2. Збереження стану
- Використовуйте KV для зберігання стану (наприклад, контексту розмови чи метаданих).
- **Приклад**: Після створення векторного індексу чи виконання запиту запишіть результат у KV і використовуйте його для наступних операцій.
- **Ефект**: Уникайте повторних дорогих запитів до AI.

### 3. Мінімізація запитів
- Об’єднуйте кілька операцій в одному запиті до Worker’а.
- **Приклад**: Виконуйте фільтрацію даних і запит до AI в одному виклику.
- **Ефект**: Зменшує загальну кількість звернень до API.

### 4. Використання локальних обчислень
- Попередньо обробляйте дані локально перед відправкою до Cloudflare AI.
- **Приклад**: Фільтруйте або агрегуйте дані перед індексацією у Vectorize.
- **Ефект**: Знижує навантаження на API.

---

## Висновок

Розгортання проекту **cloudflare-retrieval-augmented-generation-example** за допомогою Docker на основі шаблону від **openai-to-cloudflare-ai** дозволяє легко інтегрувати Cloudflare Workers AI у ваш додаток. Використовуйте Dockerfile і Docker Compose для автоматизації процесу, а методи оптимізації (кешування, збереження стану, мінімізація запитів) допоможуть обійти обмеження безкоштовного плану Cloudflare AI, забезпечуючи стабільну роботу вашого RAG-додатку.