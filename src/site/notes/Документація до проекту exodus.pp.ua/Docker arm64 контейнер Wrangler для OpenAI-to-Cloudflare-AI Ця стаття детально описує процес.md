---
{"title":"Docker arm64 контейнер Wrangler для OpenAI-to-Cloudflare-AI Ця стаття детально описує процес","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/docker-arm64-kontejner-wrangler-dlya-open-ai-to-cloudflare-ai-czya-stattya-detalno-opisuye-proczes/","dgPassFrontmatter":true,"noteIcon":""}
---


Ця стаття детально описує процес створення Docker-контейнерів для Wrangler, інструменту командного рядка Cloudflare Workers, у двох версіях: на базі `node:18-bullseye-slim` та `node:18-alpine`, оптимізованих для архітектури arm64. Ми також адаптуємо ці контейнери для розгортання проекту з GitHub: [pa4080/openai-to-cloudflare-ai](https://github.com/pa4080/openai-to-cloudflare-ai.git). Стаття написана для використання в Obsidian, тому вона структурована з використанням Markdown.

---

## Вступ

Wrangler — це інструмент для роботи з Cloudflare Workers, який дозволяє розробляти, тестувати та розгортати серверні функції. У цій статті ми створимо два Docker-контейнери для Wrangler, використовуючи різні базові образи: `node:18-bullseye-slim` (на базі Debian) та `node:18-alpine` (на базі легковажного Alpine Linux). Обидва контейнери будуть оптимізовані для архітектури arm64, що ідеально підходить для сучасних пристроїв, таких як Apple Silicon або Raspberry Pi. У другій частині ми адаптуємо контейнер для роботи з проектом [OpenAI-to-Cloudflare-AI](https://github.com/pa4080/openai-to-cloudflare-ai.git), враховуючи його вимоги та додаючи необхідні модифікації.

---

## Частина 1: Створення контейнерів

### Версія 1: На базі `node:18-bullseye-slim`

Цей контейнер базується на образі `node:18-bullseye-slim`, який є легковажною версією Debian Bullseye з встановленим Node.js 18.

#### Кроки створення

1. **Вибір базового образу**:
   - Використовуємо `FROM node:18-bullseye-slim` як основу. Цей образ забезпечує баланс між розміром і функціональністю.

2. **Оновлення та встановлення пакетів**:
   - Виконуємо `apt-get update`, щоб оновити список пакетів.
   - Встановлюємо `curl` (для завантаження даних) та `ca-certificates` (для роботи з SSL) з опцією `--no-install-recommends`, щоб уникнути зайвих залежностей.
   - Очищаємо кеш пакетів командою `apt-get clean -y` і видаляємо тимчасові файли з `/var/lib/apt/lists/*`, щоб зменшити розмір образу.

3. **Встановлення Wrangler та Esbuild**:
   - Визначаємо версії як аргументи: `WRANGLER_VERSION=3.25.0` та `ESBUILD_VERSION=0.20.1`.
   - Встановлюємо їх глобально за допомогою `npm install --global --omit=dev`, де `--omit=dev` виключає встановлення залежностей для розробки.
   - Очищаємо кеш npm командою `npm cache clean --force`.

4. **Налаштування користувача та робочої директорії**:
   - Перемикаємося на користувача `node` для підвищення безпеки (уникнення root).
   - Встановлюємо робочу директорію `/app`.
   - Додаємо том `VOLUME ["/app"]` для монтування коду проекту.
   - Встановлюємо точку входу `ENTRYPOINT ["wrangler"]`, щоб контейнер запускав Wrangler за замовчуванням.

#### Dockerfile для версії 1

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

---

### Версія 2: На базі `node:18-alpine`

Цей контейнер використовує `node:18-alpine`, який базується на Alpine Linux — надзвичайно легковажному дистрибутиві.

#### Кроки створення

1. **Вибір базового образу**:
   - Використовуємо `FROM node:18-alpine`. Цей образ значно менший за розміром порівняно з `bullseye-slim`.

2. **Встановлення пакетів**:
   - Встановлюємо `curl` та `ca-certificates` за допомогою `apk add --no-cache`, де `--no-cache` запобігає збереженню кешу пакетів.

3. **Встановлення Wrangler та Esbuild**:
   - Визначаємо версії: `WRANGLER_VERSION=3.25.0` та `ESBUILD_VERSION=0.20.1`.
   - Встановлюємо глобально через `npm install --global --omit=dev`.
   - Очищаємо кеш npm за допомогою `npm cache clean --force`.

4. **Налаштування користувача та робочої директорії**:
   - Перемикаємося на користувача `node`.
   - Встановлюємо робочу директорію `/app`.
   - Додаємо том `VOLUME ["/app"]`.
   - Встановлюємо точку входу `ENTRYPOINT ["wrangler"]`.

#### Dockerfile для версії 2

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

---

## Частина 2: Адаптація для розгортання проекту OpenAI-to-Cloudflare-AI

Проект [pa4080/openai-to-cloudflare-ai](https://github.com/pa4080/openai-to-cloudflare-ai.git) призначений для інтеграції OpenAI з Cloudflare AI через Cloudflare Workers. Ми адаптуємо наш контейнер для його розгортання, враховуючи вимоги проекту.

### Аналіз проекту

1. **Вимоги до середовища**:
   - Проект використовує Node.js і Wrangler, що вже є в наших контейнерах.
   - Потрібен доступ до GitHub для завантаження коду.
   - Потрібен `CLOUDFLARE_API_TOKEN` для аутентифікації в Cloudflare.

2. **Менеджер пакетів**:
   - Проект використовує npm (наявність `package.json` у репозиторії), тому змінювати менеджер пакетів (наприклад, на Yarn) не потрібно.

3. **Залежності**:
   - Проект має файл `package.json`, тому потрібно встановити залежності перед розгортанням.

### Модифікація контейнера

Ми базуватимемося на версії з `node:18-alpine` через її менший розмір, але додамо кроки для роботи з проектом.

#### Оновлені кроки

1. **Додавання Git**:
   - Встановлюємо `git` для клонування репозиторію.

2. **Клонування проекту**:
   - Завантажуємо код із GitHub у робочу директорію `/app`.

3. **Встановлення залежностей**:
   - Виконуємо `npm install` для встановлення залежностей із `package.json`.

4. **Точка входу**:
   - Встановлюємо `ENTRYPOINT ["wrangler", "deploy"]` для автоматичного розгортання.

5. **Змінні середовища**:
   - `CLOUDFLARE_API_TOKEN` передаватимемо при запуску контейнера, а не вбудовуватимемо в образ для безпеки.

#### Оновлений Dockerfile

```dockerfile
FROM node:18-alpine

RUN apk add --no-cache curl ca-certificates git

ARG WRANGLER_VERSION=3.25.0
ARG ESBUILD_VERSION=0.20.1

RUN npm install --global --omit=dev \
    wrangler@${WRANGLER_VERSION} \
    esbuild@${ESBUILD_VERSION} \
    && npm cache clean --force

USER node
WORKDIR /app

# Клонуємо репозиторій
RUN git clone https://github.com/pa4080/openai-to-cloudflare-ai.git .

# Встановлюємо залежності проекту
RUN npm install

# Точка входу для розгортання
ENTRYPOINT ["wrangler", "deploy"]
```

---

### Використання контейнера

#### 1. Побудова образу
- Збережіть Dockerfile у файл, наприклад, `Dockerfile.openai`.
- Виконайте команду в терміналі:
  ```bash
  docker build -t openai-to-cloudflare-ai .
  ```

#### 2. Запуск контейнера
- Запустіть контейнер, передавши `CLOUDFLARE_API_TOKEN` як змінну середовища:
  ```bash
  docker run -e CLOUDFLARE_API_TOKEN=your_api_token_here openai-to-cloudflare-ai
  ```
- Це розгорне проект на Cloudflare Workers.

#### Примітка
- Замініть `your_api_token_here` на ваш реальний API-токен Cloudflare.
- Для локального тестування можна змонтувати том із кодом проекту вручну, замість клонування через Git:
  ```bash
  docker run -v /шлях/до/проекту:/app -e CLOUDFLARE_API_TOKEN=your_api_token_here openai-to-cloudflare-ai
  ```

---

## Висновок

Ми створили два Docker-контейнери для Wrangler на базі `node:18-bullseye-slim` та `node:18-alpine`, оптимізовані для arm64. Далі ми адаптували контейнер для розгортання проекту [OpenAI-to-Cloudflare-AI](https://github.com/pa4080/openai-to-cloudflare-ai.git), додавши підтримку Git, встановлення залежностей і автоматичне розгортання через Wrangler. Цей підхід забезпечує зручність і повторюваність при роботі з Cloudflare Workers у контейнеризованому середовищі.

Сподіваюся, ця стаття стане корисною для вашої роботи в Obsidian!