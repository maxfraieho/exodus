---
{"title":"Розгортання api2app-frontend з Docker та Cloudflared на ARM64","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/rozgortannya-api2app-frontend-z-docker-ta-cloudflared-na-arm-64/","dgPassFrontmatter":true,"noteIcon":""}
---



Цей посібник допоможе вам розгорнути проект `api2app-frontend` з [GitHub](https://github.com/andchir/api2app-frontend) локально на хості з архітектурою ARM64. Ми будемо використовувати Docker для контейнеризації проекту та `cloudflared` у Docker-контейнері для тунелювання трафіку до локального сервера. Припускається, що ваш цільовий сервер (наприклад, локальний API) працює на тому ж хості. Для додаткового контексту зверніться до статті автора на [Habr](https://habr.com/ru/articles/791146/).

---

## Передумови

Перед початком переконайтеся, що у вас є:

- **Архітектура хосту**: ARM64 (наприклад, Raspberry Pi, Mac M1 або хмарний інстанс на базі ARM).
- **Docker**: Встановлений і запущений. Перевірте командою:
  ```bash
  docker --version
  ```
- **Docker Compose**: Рекомендується для зручного управління контейнерами. Перевірте:
  ```bash
  docker-compose --version
  ```
- **Git**: Встановлений для клонування репозиторію. Перевірте:
  ```bash
  git --version
  ```
- **Обліковий запис Cloudflare**: Потрібен токен тунелю від Cloudflare. Дивіться [документацію](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/).
- **Цільовий API**: Локальний сервер, що працює на тому ж хості (наприклад, на `http://localhost:8080`).

---

## Крок 1: Клонування репозиторію

1. Відкрийте термінал на вашому ARM64 хості.
2. Склонуйте репозиторій:
   ```bash
   git clone https://github.com/andchir/api2app-frontend.git
   ```
3. Перейдіть до директорії проекту:
   ```bash
   cd api2app-frontend
   ```

---

## Крок 2: Підготовка проекту для Docker

Оскільки репозиторій не містить `Dockerfile`, ми створимо його для ARM64.

### Створення Dockerfile

1. Створіть файл `Dockerfile` у директорії `api2app-frontend`:
   ```bash
   touch Dockerfile
   ```
2. Відкрийте файл у текстовому редакторі (наприклад, `nano Dockerfile`) і додайте:
   ```dockerfile
   # Базовий образ Node.js для ARM64
   FROM node:18-bullseye-slim

   # Робоча директорія
   WORKDIR /app

   # Копіювання package.json та package-lock.json
   COPY package*.json ./

   # Встановлення залежностей
   RUN npm install

   # Встановлення Angular CLI
   RUN npm install -g @angular/cli

   # Копіювання решти файлів
   COPY . .

   # Збірка Angular-додатку
   RUN npm run build -- --configuration production

   # Легкий веб-сервер Nginx
   FROM nginx:alpine

   # Копіювання збудованого додатку
   COPY --from=0 /app/dist/api2app-frontend /usr/share/nginx/html

   # Відкриття порту 80
   EXPOSE 80

   # Запуск Nginx
   CMD ["nginx", "-g", "daemon off;"]
   ```
3. Збережіть і закрийте файл (`Ctrl+O`, `Enter`, `Ctrl+X` у nano).

**Примітка**: Цей `Dockerfile` використовує багатоступеневу збірку: спочатку компілює Angular-додаток, потім обслуговує його через Nginx.

---

## Крок 3: Налаштування Docker Compose

Для управління контейнерами створимо `docker-compose.yml`.

1. Створіть файл у директорії `api2app-frontend`:
   ```bash
   touch docker-compose.yml
   ```
2. Відкрийте його і додайте:
   ```yaml
   version: '3.8'

   services:
     api2app:
       build:
         context: .
         dockerfile: Dockerfile
       ports:
         - "8081:80"  # Порт хоста 8081 -> порт контейнера 80
       restart: unless-stopped

     cloudflared:
       image: cloudflare/cloudflared:latest
       command: tunnel --no-autoupdate run --token ${CLOUDFLARED_TOKEN}
       restart: unless-stopped
       depends_on:
         - api2app
   ```
3. Збережіть і закрийте файл.

**Примітка**: Порт `8081` використовується для уникнення конфліктів із вашим API (наприклад, на `8080`).

---

## Крок 4: Налаштування тунелю Cloudflare

1. **Створення тунелю**:
   - Увійдіть до Cloudflare, перейдіть до *Zero Trust* > *Tunnels*.
   - Натисніть *Create a Tunnel*, назвіть його (наприклад, `api2app-tunnel`) і збережіть.
   - Скопіюйте токен тунелю.

2. **Збереження токена**:
   - Створіть файл `.env`:
     ```bash
     touch .env
     ```
   - Додайте токен:
     ```
     CLOUDFLARED_TOKEN=ваш-токен-тут
     ```
   - Збережіть файл.

3. **Налаштування тунелю**:
   - У Cloudflare відредагуйте тунель.
   - Додайте публічне ім’я хоста (наприклад, `api2app.yourdomain.com`).
   - Вкажіть сервіс: `http://api2app:80`.

---

## Крок 5: Збірка та запуск контейнерів

1. Переконайтеся, що ви в директорії `api2app-frontend`.
2. Запустіть контейнери:
   ```bash
   docker-compose up -d --build
   ```
3. Перевірте стан:
   ```bash
   docker ps
   ```
   Ви побачите два контейнери: `api2app-frontend_api2app` і `api2app-frontend_cloudflared`.

---

## Крок 6: Тестування розгортання

1. **Локальний доступ**:
   - Відкрийте браузер і перейдіть до `http://localhost:8081`.
   - Перевірте, чи завантажується інтерфейс.

2. **Доступ через тунель**:
   - Відвідайте `https://api2app.yourdomain.com` (ваше публічне ім’я хоста).
   - Переконайтеся, що інтерфейс доступний.

3. **Інтеграція з API**:
   - Налаштуйте фронтенд для роботи з вашим API (наприклад, `http://localhost:8080`).
   - Змініть `src/environments/environment.prod.ts` перед збіркою, якщо потрібно.

---

## Крок 7: Вирішення проблем

- **Перевірка логів**:
  ```bash
  docker-compose logs api2app
  docker-compose logs cloudflared
  ```
- **Конфлікти портів**: Якщо `8081` зайнятий, змініть його в `docker-compose.yml`.
- **Cloudflared**: Перевірте токен і статус тунелю в Cloudflare.

---

## Висновок

Ви розгорнули `api2app-frontend` у Docker-контейнері на ARM64, доступному локально через `http://localhost:8081` і публічно через Cloudflare-тунель. Налаштуйте API-інтеграцію за вашими потребами.

Додаткову інформацію дивіться в [статті на Habr](https://habr.com/ru/articles/791146/) або [репозиторії](https://github.com/andchir/api2app-frontend).