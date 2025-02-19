---
{"title":"Cloudflared у Docker-контейнері","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/cloudflared-u-docker-kontejneri/","dgPassFrontmatter":true,"noteIcon":""}
---


Нижче наведено покрокову інструкцію для налаштування тунелю Cloudflare (cloudflared) у Docker-контейнері на сервері та доступу до нього через SSH зі смартфона (Termux).

---

## 1. Підготовка сервера

### 1.1 Створення робочої директорії
```bash
mkdir -p /home/vokov/cloudflared-tunnel
cd /home/vokov/cloudflared-tunnel
````

### 1.2 Авторизація в обліковому записі Cloudflare через Docker

```bash
docker run -it --rm \
  -v $PWD:/etc/cloudflared \
  -e HOME=/etc/cloudflared \
  cloudflare/cloudflared \
  tunnel login
```

> Після входу у свій обліковий запис Cloudflare у браузері, у директорії `/home/vokov/cloudflared-tunnel` з’явиться папка **.cloudflared** з сертифікатом.

### 1.3 Перейменування та переміщення файлів

1. Перейменуйте `.cloudflared` у `cloudflared`:
    
    ```bash
    mv .cloudflared cloudflared
    ```
    
2. Перемістіть файл `cert.pem` до `/home/vokov/cloudflared-tunnel`:
    
    ```bash
    mv /home/vokov/cloudflared-tunnel/cloudflared/cert.pem /home/vokov/cloudflared-tunnel
    ```
    
3. Надайте файлам відповідні права:
    
    ```bash
    chmod -R 0777 /home/vokov/cloudflared-tunnel
    ```
    

---

## 2. Додавання DNS-записів (маршрути) для тунелю

### 2.1 DNS-запис для Portainer

```bash
docker run --rm \
  -v $PWD/cloudflared:/etc/cloudflared \
  cloudflare/cloudflared:latest \
  tunnel route dns exodus-tunnel portainer.exodus.pp.ua
```

### 2.2 DNS-запис для SSH-доступу

```bash
docker run --rm \
  -v $PWD/cloudflared:/etc/cloudflared \
  cloudflare/cloudflared:latest \
  tunnel route dns exodus-tunnel ssh.exodus.pp.ua
```

---

## 3. Створення `config.yml` для cloudflared

У директорії `cloudflared` створіть або відредагуйте файл `config.yml`:

```yaml
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
```

---

## 4. Створення `docker-compose.yml`

У кореневій директорії (наприклад, `/home/vokov/cloudflared-tunnel`), створіть файл `docker-compose.yml`:

```yaml
version: '3.8'
services:
  cloudflared:
    image: cloudflare/cloudflared
    container_name: cloudflared
    restart: unless-stopped
    volumes:
      - ./cloudflared:/etc/cloudflared
    command: tunnel run exodus-tunnel  # замініть на свою назву тунелю, якщо інша
```

---

## 5. Запуск контейнера

Запустіть контейнер командою:

```bash
docker-compose up -d
```

> Перевірте логи, якщо потрібно:
> 
> ```bash
> docker logs -f cloudflared
> ```

---

## 6. Налаштування SSH-доступу зі смартфона (Termux)

### 6.1 Встановлення залежностей

```bash
pkg update && pkg upgrade
pkg install git
```

### 6.2 Клонування репозиторію

```bash
git clone https://github.com/rajbhx/cloudflared-termux
cd cloudflared-termux
```

### 6.3 Встановлення cloudflared у Termux

```bash
bash Cloudflared-termux_@rajbhx.bash
```

> Перевірте версію:
> 
> ```bash
> cloudflared --version
> ```

### 6.4 Запуск SSH-тунелю через Cloudflare

```bash
cloudflared access tcp --hostname ssh.exodus.pp.ua --url localhost:2222 --destination localhost:22
```

> **Примітка:**
> 
> - `ssh.exodus.pp.ua` – ваш домен, налаштований у Cloudflare.
> - `--url localhost:2222` – порт, на який буде спрямований трафік локально на вашому смартфоні.
> - `--destination localhost:22` – куди Cloudflare має перенаправляти трафік (у даному випадку ваш реальний SSH-сервер на порту 22).

Після цього в **Termux** можна підключатися до `localhost:2222` через SSH-клієнт:

```bash
ssh -p 2222 your_username@localhost
```

---

## Додаткові поради

1. **Безпека та доступи**
    
    - Рекомендується обмежити права доступу до сертифікату та файлів конфігурації (`config.yml`) лише тим, хто має розгортати або змінювати налаштування тунелю.
    - Використовуйте SSH-ключі для підключення до сервера замість пароля для підвищення безпеки.
2. **Оновлення Cloudflared**
    
    - Контейнер `cloudflare/cloudflared` можна оновлювати командою:
        
        ```bash
        docker-compose pull && docker-compose up -d
        ```
        
3. **Додаткові сервіси**
    
    - Додавайте інші сервіси до списку `ingress` у `config.yml`, наприклад, веб-додатки (HTTP/HTTPS), TCP/UDP, RDP тощо.
4. **Логування та моніторинг**
    
    - Використовуйте `docker logs -f cloudflared` для моніторингу роботи тунелю або керуйте тунелем через панель Cloudflare Zero Trust.


Без контейнера 

cloudflared tunnel route dns droidian code.stopbot.pp.ua
