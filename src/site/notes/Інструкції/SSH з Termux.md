---
{"title":"SSH з Termux","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/instrukcziyi/ssh-z-termux/","dgPassFrontmatter":true,"noteIcon":""}
---

Нижче наведено покрокову інструкцію з налаштування тунелю Cloudflare (`cloudflared`) у Docker-контейнері на сервері та доступу до нього через SSH із смартфона (Termux).

---

## 1. Підготовка сервера

### 1.1 Створення робочої директорії

~~~bash
mkdir -p /home/vokov/cloudflared-tunnel
cd /home/vokov/cloudflared-tunnel
~~~

### 1.2 Авторизація в обліковому записі Cloudflare через Docker

~~~bash
docker run -it --rm \
  -v $PWD:/etc/cloudflared \
  -e HOME=/etc/cloudflared \
  erisamoe/cloudflared \
  tunnel login
~~~

**Пояснення:**

- `-v $PWD:/etc/cloudflared` – монтує поточну директорію в контейнер для зберігання конфігів.
- `-e HOME=/etc/cloudflared` – встановлює змінну оточення HOME для cloudflared, щоб він міг зберегти необхідні файли (сертифікати тощо).

Після входу у свій аккаунт Cloudflare у браузері, у директорії `/home/vokov/cloudflared-tunnel` з’явиться папка `.cloudflared` з сертифікатом.

### 1.3 Перейменування та переміщення файлів

1. **Перейменуйте `.cloudflared` у `cloudflared`:**

   ~~~bash
   mv .cloudflared cloudflared
   ~~~

2. **Перемістіть файл `cert.pem` до `/home/vokov/cloudflared-tunnel` (якщо він там не з’явився автоматично):**

   ~~~bash
   mv /home/vokov/cloudflared-tunnel/cloudflared/cert.pem /home/vokov/cloudflared-tunnel
   ~~~

3. **Надайте файлам відповідні права:**

   ~~~bash
   chmod -R 0777 /home/vokov/cloudflared-tunnel
   ~~~

---

## 2. Додавання DNS-записів (маршрути) для тунелю

### 2.1 DNS-запис для Portainer

~~~bash
docker run --rm \
  -v $PWD/cloudflared:/etc/cloudflared \
  cloudflare/cloudflared:latest \
  tunnel route dns exodus-tunnel portainer.exodus.pp.ua
~~~

### 2.2 DNS-запис для SSH-доступу

~~~bash
docker run --rm \
  -v $PWD/cloudflared:/etc/cloudflared \
  cloudflare/cloudflared:latest \
  tunnel route dns exodus-tunnel ssh.exodus.pp.ua
~~~

**Пояснення:**

- `exodus-tunnel` – це ім’я вашого тунелю, яке згенерувалося при авторизації та збережене у файлах конфігурації.
- `portainer.exodus.pp.ua` і `ssh.exodus.pp.ua` – це хостнейми, які ви створюєте у Cloudflare.

---

## 3. Створення `config.yml` для `cloudflared`

У директорії `cloudflared` створіть або відредагуйте файл `config.yml` (шлях: `/home/vokov/cloudflared-tunnel/cloudflared/config.yml`):

~~~yaml
tunnel: 7c2d896d-2c77-4486-af56-ef30969ca942  # замініть на свій tunnel ID
credentials-file: /etc/cloudflared/7c2d896d-2c77-4486-af56-ef30969ca942.json

ingress:
  - hostname: portainer.exodus.pp.ua
    service: http://192.168.1.234:9000

  - hostname: dangerboys.exodus.pp.ua
    service: http://192.168.1.234:8181

  - hostname: ssh.exodus.pp.ua
    service: ssh://192.168.1.234:22

  - service: http_status:404
~~~

**Пояснення:**

- `tunnel` – ID вашого тунелю (візьміть із файлу JSON, що був згенерований при авторизації, або з панелі керування Cloudflare).
- `credentials-file` – шлях до файлу ключа JSON, який також створюється при авторизації.
- `ingress` – список правил для різних хостнеймів і портів.
  - `hostname: …` – домен, який ви налаштували у Cloudflare.
  - `service: …` – протокол та внутрішня IP-адреса з портом або `http_status:404`, якщо не знайдено жодного match.

---

## 4. Створення `docker-compose.yml`

У кореневій директорії (наприклад, `/home/vokov/cloudflared-tunnel`), створіть файл `docker-compose.yml` з таким вмістом:

~~~yaml
version: '3.8'
services:
  cloudflared:
    image: cloudflare/cloudflared
    container_name: cloudflared
    restart: unless-stopped
    volumes:
      - ./cloudflared:/etc/cloudflared
    command: tunnel run exodus-tunnel  # замініть на свою назву тунелю, якщо інша
~~~

---

## 5. Запуск контейнера

~~~bash
docker-compose up -d
~~~

**Перевірте логи, якщо треба:**

~~~bash
docker logs -f cloudflared
~~~

Після успішного запуску, ви матимете працюючий тунель через Cloudflare, який забезпечить доступ до вказаних сервісів (Portainer, SSH тощо) через ваші налаштовані домени.

---

## 6. Налаштування SSH-доступу зі смартфона (Termux)

### 6.1 Встановлення залежностей

~~~bash
pkg update && pkg upgrade
pkg install git
~~~

### 6.2 Клонування репозиторію

~~~bash
git clone https://github.com/rajbhx/cloudflared-termux
cd cloudflared-termux
~~~

### 6.3 Встановлення `cloudflared` у Termux

~~~bash
bash Cloudflared-termux_@rajbhx.bash
~~~

**Перевірте версію:**

~~~bash
cloudflared --version
~~~

### 6.4 Запуск SSH-тунелю через Cloudflare

~~~bash
cloudflared access tcp --hostname ssh.exodus.pp.ua --url localhost:2222 --destination localhost:22
~~~

**Пояснення:**

- `ssh.exodus.pp.ua` – ваш домен, налаштований на тунель у Cloudflare.
- `--url localhost:2222` – порт, на який буде спрямований трафік локально на вашому смартфоні.
- `--destination localhost:22` – куди Cloudflare має прокидати трафік (в даному випадку ваш реальний SSH-сервер на порту 22).

Після цього в Termux достатньо підключатися до `localhost:2222` через SSH-клієнт (скажімо, з використанням `ssh`, ConnectBot чи іншого).

**Наприклад:**

~~~bash
ssh -p 2222 your_username@localhost
~~~

---

## Додаткові поради

### 1. Безпека та доступи

- Рекомендується обмежити права доступу до сертифікату та файлів конфігурації (`config.yml`) лише тим, хто має розгортати або змінювати налаштування тунелю.
- Ви можете використовувати SSH-ключі для підключення до свого сервера замість пароля, щоб посилити безпеку.

### 2. Оновлення Cloudflared

Контейнер `cloudflare/cloudflared` можна оновлювати, регулярно перезапускаючи:

~~~bash
docker-compose pull && docker-compose up -d
~~~

### 3. Додаткові сервіси

Ви можете додавати інші сервіси до списку `ingress` у `config.yml`. Наприклад, веб-додатки (HTTP/HTTPS), TCP/UDP, RDP тощо.

### 4. Логування та моніторинг

Щоб слідкувати за роботою тунелю, використовуйте:

~~~bash
docker logs -f cloudflared
~~~

Або додайте інструменти моніторингу (наприклад, Cloudflare Zero Trust панель).

---

**Готово!** Ви налаштували Cloudflare Tunnel у Docker для Portainer та SSH, а також отримали можливість зручно підключатися з мобільного пристрою через Cloudflare.

Якщо у вас виникнуть додаткові питання або потрібна допомога, будь ласка, звертайтеся!