---
{"title":"Оптимізована конфігурація SSH тунелю з Cloudflare Tunnel","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/optimizovana-konfiguracziya-ssh-tunelyu-z-cloudflare-tunnel/","dgPassFrontmatter":true,"noteIcon":""}
---



## Архітектура

- **Основний хост**: `192.168.3.99` (Droidian, ARM64, Docker) - запускає сервіси та SSH тунель
- **Віддалений сервер**: `192.168.3.161` (Debian 6.11.10-arm64) - приймає SSH тунелі та запускає Cloudflare Tunnel
- **Мережа Docker**: `exodus-net` (bridge)
- **SSH-тунель**: Перенаправлення портів з `192.168.3.99` на `192.168.3.161` через зворотний тунель
- **Cloudflare Tunnel**: Працює на `192.168.3.161` для публічного доступу через домени

## Файлова структура

```
/home/droidian/Documents/sshtunelapp/
├── docker-compose.yml
├── .env
├── ssh/
│   ├── id_rsa (SSH приватний ключ)
│   └── known_hosts
└── entrypoint.sh
```

## Конфігураційні файли

### 1. `docker-compose.yml`

```yaml
version: '3.8'

services:
  minio:
    image: minio/minio:latest
    container_name: minio
    environment:
      - MINIO_ROOT_USER=vokov
      - MINIO_ROOT_PASSWORD=805235io
    networks:
      - exodus-net
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    networks:
      - exodus-net
    ports:
      - "9002:9000"  # Змінено порт, щоб уникнути конфлікту з MinIO
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
    restart: unless-stopped

  nextcloud-aio-mastercontainer:
    image: nextcloud/all-in-one:latest
    container_name: nextcloud-aio
    environment:
      - NEXTCLOUD_TRUSTED_DOMAINS=next.kofayokh.pp.ua,localhost,192.168.3.99,192.168.3.161
      - SKIP_DOMAIN_VALIDATION=true
    networks:
      - exodus-net
    ports:
      - "8080:8080"
    volumes:
      - nextcloud_aio_mastercontainer:/mnt/docker-aio-config
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped

  ssh-tunnel:
    image: alpine:latest
    container_name: ssh-tunnel
    environment:
      - SSH_USER=${SSH_USER}
      - SSH_HOST=${SSH_HOST}
    volumes:
      - ./ssh:/root/.ssh:ro
      - ./entrypoint.sh:/entrypoint.sh:ro
    entrypoint: /entrypoint.sh
    networks:
      - exodus-net
    depends_on:
      - minio
      - portainer
      - nextcloud-aio-mastercontainer
    restart: unless-stopped



networks:
  exodus-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  minio_data:
  portainer_data:
  nextcloud_aio_mastercontainer:
```

### 2. `.env` (спрощений)

```env
SSH_USER=vokov
SSH_HOST=192.168.3.161
NEXTCLOUD_TRUSTED_DOMAINS=next.kofayokh.pp.ua,localhost,192.168.3.99,192.168.3.161
```

### 3. `ssh/id_rsa` (створити окремий файл)

```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZWQyNTUx
OQAAACAOf6kYgoAEYQwCUAbIe5zPv9yVdWR+Ai/RqqF7jHcz2AAAAJhBXIMPQVyDDwAAAAtzc2gt
ZWQyNTUxOQAAACAOf6kYgoAEYQwCUAbIe5zPv9yVdWR+Ai/RqqF7jHcz2AAAAAED1MW8OR61NRKi
jnAoD84+AEGnyS/MIFRAebln6eAdz2w5/qRiCgARhDAJQBsh7nM+/3JV1ZH4CL9GqoXuMdzPYAAA
AE2RvY2tlci10dW5uZWwtcmVkbQkA
-----END OPENSSH PRIVATE KEY-----
```

### 4. `ssh/known_hosts`

```
192.168.3.161 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA5/qRiCgARhDAJQBsh7nM+/3JV1ZH4CL9GqoXuMdzPY
```

### 5. `entrypoint.sh` (виправлений)

```bash
#!/bin/sh
set -e

# Перевірка обов'язкових змінних середовища
if [ -z "$SSH_USER" ] || [ -z "$SSH_HOST" ]; then
    echo "Error: Missing required environment variables (SSH_USER, SSH_HOST)"
    exit 1
fi

echo "Starting SSH tunnel setup..."
echo "SSH_USER: $SSH_USER"
echo "SSH_HOST: $SSH_HOST"

# Встановлення необхідних пакетів
apk add --no-cache openssh-client autossh netcat-openbsd curl

# Перевірка наявності SSH файлів
if [ ! -f /root/.ssh/id_rsa ]; then
    echo "Error: SSH private key not found at /root/.ssh/id_rsa"
    ls -la /root/.ssh/ || echo "SSH directory does not exist"
    exit 1
fi

if [ ! -f /root/.ssh/known_hosts ]; then
    echo "Error: SSH known_hosts not found at /root/.ssh/known_hosts"
    ls -la /root/.ssh/ || echo "SSH directory does not exist"
    exit 1
fi

# Встановлення правильних дозволів
chmod 700 /root/.ssh
chmod 600 /root/.ssh/id_rsa
chmod 644 /root/.ssh/known_hosts

echo "SSH files permissions set correctly"

# Очікування запуску сервісів
echo "Waiting for services to start..."
sleep 15

# Перевірка доступності сервісів
check_service() {
    local service=$1
    local port=$2
    echo "Checking $service on port $port..."
    if nc -z $service $port 2>/dev/null; then
        echo "$service is ready"
        return 0
    else
        echo "$service is not ready"
        return 1
    fi
}

# Очікування готовності сервісів з більш тривалими таймаутами
echo "Checking service availability..."
for i in $(seq 1 60); do
    services_ready=0
    
    if check_service minio 9000; then
        services_ready=$((services_ready + 1))
    fi
    
    if check_service minio 9001; then
        services_ready=$((services_ready + 1))
    fi
    
    if check_service nextcloud-aio-mastercontainer 8080; then
        services_ready=$((services_ready + 1))
    fi
    
    if check_service portainer 9000; then
        services_ready=$((services_ready + 1))
    fi
    
    echo "Services ready: $services_ready/4"
    
    if [ $services_ready -eq 4 ]; then
        echo "All services are ready!"
        break
    fi
    
    if [ $i -eq 60 ]; then
        echo "Warning: Not all services are ready, but continuing with tunnel setup..."
        break
    fi
    
    echo "Waiting for services... ($i/60)"
    sleep 5
done

# Тестування SSH підключення
echo "Testing SSH connection to ${SSH_HOST}..."
if ssh -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=yes ${SSH_USER}@${SSH_HOST} "echo 'SSH connection successful'" 2>/dev/null; then
    echo "SSH connection test successful"
else
    echo "Warning: SSH connection test failed, but attempting to start tunnels..."
fi

echo "Starting SSH tunnels..."

# Запуск SSH тунелів з autossh
exec autossh -M 0 -N \
    -o "ServerAliveInterval=30" \
    -o "ServerAliveCountMax=3" \
    -o "ExitOnForwardFailure=yes" \
    -o "StrictHostKeyChecking=yes" \
    -o "BatchMode=yes" \
    -R 0.0.0.0:9100:minio:9000 \
    -R 0.0.0.0:9101:minio:9001 \
    -R 0.0.0.0:8180:nextcloud-aio-mastercontainer:8080 \
    -R 0.0.0.0:9102:portainer:9000 \
    ${SSH_USER}@${SSH_HOST}
```

### 6. `cloudflared/config.yml` (на 192.168.3.161)

```yaml
tunnel: your-tunnel-id
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: minio.kofayokh.pp.ua
    service: http://127.0.0.1:9100
    originRequest:
      httpHostHeader: minio.kofayokh.pp.ua
      originServerName: minio.kofayokh.pp.ua
  
  - hostname: minio-console.kofayokh.pp.ua
    service: http://127.0.0.1:9101
    originRequest:
      httpHostHeader: minio-console.kofayokh.pp.ua
      originServerName: minio-console.kofayokh.pp.ua
  
  - hostname: next.kofayokh.pp.ua
    service: https://127.0.0.1:8180
    originRequest:
      noTLSVerify: true
      httpHostHeader: next.kofayokh.pp.ua
      originServerName: next.kofayokh.pp.ua
  
  - hostname: portainer.kofayokh.pp.ua
    service: http://127.0.0.1:9102
    originRequest:
      httpHostHeader: portainer.kofayokh.pp.ua
      originServerName: portainer.kofayokh.pp.ua
      
  - service: http_status:404

warp-routing:
  enabled: false

metrics: 127.0.0.1:8081
```

### 7. `/etc/ssh/sshd_config` (на 192.168.3.161)

```conf
# Основні налаштування
Port 22
Protocol 2

# Аутентифікація
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication no
ChallengeResponseAuthentication no
UsePAM yes

# Тунелювання
AllowTcpForwarding yes
GatewayPorts yes
X11Forwarding no

# Безпека
PermitRootLogin no
MaxAuthTries 3
ClientAliveInterval 60
ClientAliveCountMax 3

# Логування
SyslogFacility AUTH
LogLevel INFO

# Обмеження користувачів
AllowUsers vokov
```

## Інструкції по розгортанню

### 1. Підготовка файлів на 192.168.3.99

```bash
# Створити структуру папок
mkdir -p /home/droidian/Documents/sshtunelapp/ssh
cd /home/droidian/Documents/sshtunelapp

# Створити SSH ключ файл
cat > ssh/id_rsa << 'EOF'
-----BEGIN OPENSSH PRIVATE KEY-----
[ваш приватний ключ тут]
-----END OPENSSH PRIVATE KEY-----
EOF

# Створити known_hosts
echo "192.168.3.161 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA5/qRiCgARhDAJQBsh7nM+/3JV1ZH4CL9GqoXuMdzPY" > ssh/known_hosts

# Встановити дозволи
chmod 600 ssh/id_rsa
chmod 644 ssh/known_hosts
chmod +x entrypoint.sh
```

### 2. Налаштування SSH на 192.168.3.161

```bash
# Додати публічний ключ до authorized_keys
mkdir -p ~/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA5/qRiCgARhDAJQBsh7nM+/3JV1ZH4CL9GqoXuMdzPY docker-tunnel-redmi" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

# Перезапустити SSH сервіс
sudo systemctl restart ssh
```

### 3. Налаштування Cloudflare Tunnel на 192.168.3.161

```bash
# Встановити cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb

# Створити тунель (виконати один раз)
cloudflared tunnel login
cloudflared tunnel create your-tunnel-name

# Скопіювати credentials.json до /etc/cloudflared/
sudo cp ~/.cloudflared/[tunnel-id].json /etc/cloudflared/credentials.json

# Створити конфігурацію
sudo cp config.yml /etc/cloudflared/config.yml

# Встановити як сервіс
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### 4. Запуск на 192.168.3.99

```bash
cd /home/droidian/Documents/sshtunelapp

# Запустити сервіси
docker-compose up -d

# Перевірити логи
docker-compose logs -f ssh-tunnel
```

## Перевірка роботи

### На 192.168.3.161:

```bash
# Перевірити відкриті порти
sudo netstat -tlnp | grep -E "(9100|9101|8180|9102)"

# Перевірити тунелі
sudo ss -tlnp | grep -E "(9100|9101|8180|9102)"

# Тестування підключення
curl -I http://127.0.0.1:9100/minio/health/live
curl -I http://127.0.0.1:9101
curl -k -I https://127.0.0.1:8180
curl -I http://127.0.0.1:9102
```

### Через Cloudflare домени:

```bash
curl -I https://minio.kofayokh.pp.ua/minio/health/live
curl -I https://minio-console.kofayokh.pp.ua
curl -I https://next.kofayokh.pp.ua
curl -I https://portainer.kofayokh.pp.ua
```

## Troubleshooting

### Якщо SSH тунелі не працюють:

1. Перевірити SSH підключення:
```bash
docker-compose exec ssh-tunnel ssh -v vokov@192.168.3.161
```

2. Перевірити логи:
```bash
docker-compose logs ssh-tunnel
```

3. Перевірити конфігурацію SSH на сервері:
```bash
sudo sshd -T | grep -E "(GatewayPorts|AllowTcpForwarding)"
```

### Якщо Cloudflare Tunnel не працює:

1. Перевірити статус сервісу:
```bash
sudo systemctl status cloudflared
```

2. Перевірити логи:
```bash
sudo journalctl -u cloudflared -f
```

3. Перевірити DNS записи в Cloudflare Dashboard.

## Оптимізації безпеки

1. **Обмеження SSH доступу**:
   - Використовувати тільки ключі
   - Обмежити користувачів
   - Встановити timeout

2. **Firewall правила на 192.168.3.161**:
```bash
sudo ufw allow 22/tcp
sudo ufw allow from 192.168.3.99 to any port 9100:9102
sudo ufw allow from 192.168.3.99 to any port 8180
sudo ufw enable
```

3. **Моніторинг**:
   - Логування SSH підключень
   - Моніторинг використання ресурсів
   - Alerting при відключенні тунелів

Щоб налаштувати SSH-тунель "вручну" та перевірити кожен крок, ми пройдемо через усі етапи налаштування на хостах (`192.168.3.99` та `192.168.3.161`), включаючи створення ключів, налаштування SSH, перевірку підключень та встановлення тунелю. Ми також протестуємо кожен компонент, щоб виявити, де саме виникає проблема. Я припускаю, що Cloudflare Tunnel уже налаштовано на `192.168.3.161`, але ми перевіримо і його конфігурацію.

---

## Крок 1: Перевірка базової мережевої доступності

Перед початком налаштування переконаємося, що хости можуть "бачити" один одного в мережі.

### На `192.168.3.99` (Droidian):
1. Виконайте команду для перевірки доступності `192.168.3.161`:
   ```bash
   ping -c 4 192.168.3.161
   ```
   Очікуваний результат: Успішні відповіді без втрати пакетів.

2. Перевірте, чи відкритий порт SSH (22) на `192.168.3.161`:
   ```bash
   nc -zv 192.168.3.161 22
   ```
   Очікуваний результат: `Connection to 192.168.3.161 22 port [tcp/ssh] succeeded!`

### На `192.168.3.161` (Debian):
1. Перевірте доступність `192.168.3.99`:
   ```bash
   ping -c 4 192.168.3.99
   ```

2. Переконайтеся, що SSH-сервер запущений:
   ```bash
   sudo systemctl status ssh
   ```
   Очікуваний результат: Статус `active (running)`.

3. Перевірте, чи прослуховується порт 22:
   ```bash
   sudo netstat -tlnp | grep :22
   ```
   Очікуваний результат: Ви побачите рядок, де `sshd` слухає `0.0.0.0:22` або `:::22`.

**Якщо є проблеми**: Перевірте налаштування брандмауера (`ufw` або `iptables`) на обох хостах. Наприклад, на `192.168.3.161`:
```bash
sudo ufw status
sudo ufw allow 22/tcp
```

---

## Крок 2: Створення SSH-ключів

Ми створимо нову пару ключів спеціально для тунелю, щоб уникнути проблем із наявними ключами.

### На `192.168.3.99` (Droidian):
1. Створіть нову пару ключів для користувача `vokov`:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/tunnel_key -C "tunnel_key" -N ""
   ```
   - Це створить:
     - Приватний ключ: `~/.ssh/tunnel_key`
     - Публічний ключ: `~/.ssh/tunnel_key.pub`

2. Перевірте створені ключі:
   ```bash
   ls -l ~/.ssh/
   cat ~/.ssh/tunnel_key.pub
   ```
   Скопіюйте вміст `tunnel_key.pub` для наступного кроку.

3. Встановіть правильні дозволи:
   ```bash
   chmod 600 ~/.ssh/tunnel_key
   chmod 644 ~/.ssh/tunnel_key.pub
   ```

### На `192.168.3.161` (Debian):
1. Додайте публічний ключ до файлу `~/.ssh/authorized_keys` для користувача `vokov`:
   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   echo "<вставте вміст tunnel_key.pub сюди>" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```
   Наприклад, якщо публічний ключ виглядає так:
   ```
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA5/qRiCgARhDAJQBsh7nM+/3JV1ZH4CL9GqoXuMdzPY tunnel_key
   ```
   Виконайте:
   ```bash
   echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA5/qRiCgARhDAJQBsh7nM+/3JV1ZH4CL9GqoXuMdzPY tunnel_key" >> ~/.ssh/authorized_keys
   ```

2. Перевірте права доступу:
   ```bash
   ls -ld ~ ~/.ssh ~/.ssh/authorized_keys
   ```
   Очікуваний результат:
   ```
   drwxr-xr-x ... /home/vokov
   drwx------ ... /home/vokov/.ssh
   -rw------- ... /home/vokov/.ssh/authorized_keys
   ```

---

## Крок 3: Налаштування SSH-сервера на `192.168.3.161`

Переконаємося, що SSH-сервер налаштований для підтримки тунелювання.

1. Відредагуйте конфігурацію SSH (`/etc/ssh/sshd_config`):
   ```bash
   sudo nano /etc/ssh/sshd_config
   ```
   Переконайтеся, що наступні параметри присутні або додайте їх:
   ```conf
   AllowTcpForwarding yes
   GatewayPorts yes
   PermitRootLogin no
   PasswordAuthentication no
   PubkeyAuthentication yes
   AllowUsers vokov
   ClientAliveInterval 60
   ClientAliveCountMax 3
   ```

2. Перевірте синтаксис конфігурації:
   ```bash
   sudo sshd -T
   ```
   Якщо немає помилок, продовжуйте.

3. Перезапустіть SSH-сервер:
   ```bash
   sudo systemctl restart ssh
   ```

4. Перевірте статус:
   ```bash
   sudo systemctl status ssh
   ```

---

## Крок 4: Тестування SSH-підключення

Тестуємо підключення з `192.168.3.99` до `192.168.3.161` без тунелювання.

### На `192.168.3.99`:
1. Виконайте SSH-підключення з використанням створеного ключа:
   ```bash
   ssh -i ~/.ssh/tunnel_key -o StrictHostKeyChecking=no vokov@192.168.3.161
   ```
   - Якщо запитують пароль, перевірте, чи правильно доданий публічний ключ до `authorized_keys` на `192.168.3.161`.
   - Якщо підключення успішне, ви увійдете в оболонку на `192.168.3.161`.

2. Якщо виникають помилки, увімкніть детальний режим для діагностики:
   ```bash
   ssh -i ~/.ssh/tunnel_key -v vokov@192.168.3.161
   ```

3. Додайте відбиток хоста до `known_hosts` (якщо потрібно):
   ```bash
   ssh-keyscan -t ed25519 192.168.3.161 >> ~/.ssh/known_hosts
   chmod 644 ~/.ssh/known_hosts
   ```

**Якщо підключення не працює**:
- Перевірте логи SSH на `192.168.3.161`:
  ```bash
  sudo journalctl -u ssh -f
  ```
- Переконайтеся, що брандмауер дозволяє вхідні з'єднання на порт 22.

---

## Крок 5: Налаштування зворотного SSH-тунелю вручну

Тепер спробуємо налаштувати зворотний тунель вручну, щоб перенаправити порти з `192.168.3.99` на `192.168.3.161`.

### На `192.168.3.99`:
1. Запустіть команду для створення зворотного тунелю:
   ```bash
   ssh -i ~/.ssh/tunnel_key -N -R 0.0.0.0:9100:localhost:9000 vokov@192.168.3.161
   ```
   - Пояснення:
     - `-N`: Не виконувати команди, лише тунелювання.
     - `-R 0.0.0.0:9100:localhost:9000`: Перенаправити порт `9100` на `192.168.3.161` до `localhost:9000` на `192.168.3.99` (порт MinIO).
     - `vokov@192.168.3.161`: Користувач і хост.

2. Залиште термінал відкритим і перейдіть до перевірки.

### На `192.168.3.161`:
1. Перевірте, чи прослуховується порт `9100`:
   ```bash
   sudo netstat -tlnp | grep 9100
   ```
   Очікуваний результат: Ви побачите, що `sshd` слухає `0.0.0.0:9100`.

2. Перевірте доступність сервісу MinIO через тунель:
   ```bash
   curl -I http://127.0.0.1:9100/minio/health/live
   ```
   Очікуваний результат: HTTP-відповідь `200 OK`.

**Якщо тунель не працює**:
- Перевірте логи SSH на `192.168.3.161`:
  ```bash
  sudo journalctl -u ssh -f
  ```
- Переконайтеся, що `GatewayPorts yes` увімкнено в `sshd_config`.
- Перевірте, чи MinIO запущений на `192.168.3.99`:
  ```bash
  docker ps
  curl -I http://localhost:9000/minio/health/live
  ```

---

## Крок 6: Перевірка Docker-сервісів на `192.168.3.99`

Оскільки тунель перенаправляє порти Docker-контейнерів, переконаємося, що сервіси (MinIO, Portainer, Nextcloud) працюють.

1. Перевірте статус контейнерів:
   ```bash
   docker ps
   ```
   Переконайтеся, що контейнери `minio`, `portainer`, `nextcloud-aio-mastercontainer` запущені.

2. Перевірте доступність сервісів локально:
   ```bash
   curl -I http://localhost:9000/minio/health/live  # MinIO
   curl -I http://localhost:9001                    # MinIO Console
   curl -I http://localhost:9002                    # Portainer
   curl -k -I https://localhost:8080   с
3. # Nextcloud
   ```

**Якщо сервіси не відповідають**:
- Перегляньте логи контейнерів:
  ```bash
  docker logs minio
  docker logs portainer
  docker logs nextcloud-aio
  ```
- Переконайтеся, що порти в `docker-compose.yml` правильно зіставлені.

---

## Крок 7: Налаштування autossh для постійного тунелю

Після успішного тестування вручну, ми налаштуємо `autossh` для автоматичного підтримання тунелю.

### На `192.168.3.99`:
1. Встановіть `autossh`, якщо його ще немає:
   ```bash
   sudo apt-get update
   sudo apt-get install autossh
   ```

2. Тестовий запуск `autossh`:
   ```bash
   autossh -M 0 -N \
     -o "ServerAliveInterval=30" \
     -o "ServerAliveCountMax=3" \
     -o "ExitOnForwardFailure=yes" \
     -i ~/.ssh/tunnel_key \
     -R 0.0.0.0:9100:localhost:9000 \
     -R 0.0.0.0:9101:localhost:9001 \
     -R 0.0.0.0:8180:localhost:8080 \
     -R 0.0.0.0:9102:localhost:9002 \
     vokov@192.168.3.161
   ```

3. Перевірте порти на `192.168.3.161`:
   ```bash
   sudo netstat -tlnp | grep -E "(9100|9101|8180|9102)"
   ```

---

## Крок 8: Перевірка Cloudflare Tunnel на `192.168.3.161`

Переконаємося, що Cloudflare Tunnel перенаправляє запити до тунельованих портів.

1. Перевірте статус сервісу `cloudflared`:
   ```bash
   sudo systemctl status cloudflared
   ```

2. Перегляньте логи:
   ```bash
   sudo journalctl -u cloudflared -f
   ```

3. Перевірте конфігурацію `/etc/cloudflared/config.yml`:
   ```yaml
   tunnel: your-tunnel-id
   credentials-file: /etc/cloudflared/credentials.json

   ingress:
     - hostname: minio.kofayokh.pp.ua
       service: http://127.0.0.1:9100
     - hostname: minio-console.kofayokh.pp.ua
       service: http://127.0.0.1:9101
     - hostname: next.kofayokh.pp.ua
       service: https://127.0.0.1:8180
       originRequest:
         noTLSVerify: true
     - hostname: portainer.kofayokh.pp.ua
       service: http://127.0.0.1:9102
     - service: http_status:404
   ```

4. Перевірте доступність через домени:
   ```bash
   curl -I https://minio.kofayokh.pp.ua/minio/health/live
   curl -I https://minio-console.kofayokh.pp.ua
   curl -I https://next.kofayokh.pp.ua
   curl -I https://portainer.kofayokh.pp.ua
   ```

**Якщо не працює**:
- Перевірте DNS-записи в Cloudflare Dashboard.
- Переконайтеся, що `credentials.json` містить правильний `tunnel-id`.
- Спробуйте запустити `cloudflared` вручну:
  ```bash
  cloudflared --config /etc/cloudflared/config.yml tunnel run
  ```

---

## Крок 9: Інтеграція з Docker

Якщо всі попередні кроки працюють, повернемося до вашого `docker-compose.yml` і виправимо контейнер `ssh-tunnel`.

1. Оновіть `docker-compose.yml` для використання нового ключа:
   ```yaml
   services:
     ssh-tunnel:
       image: alpine:latest
       container_name: ssh-tunnel
       environment:
         - SSH_USER=vokov
         - SSH_HOST=192.168.3.161
       volumes:
         - ~/.ssh/tunnel_key:/root/.ssh/id_rsa:ro
         - ~/.ssh/known_hosts:/root/.ssh/known_hosts:ro
         - ./entrypoint.sh:/entrypoint.sh:ro
       entrypoint: /entrypoint.sh
       networks:
         - exodus-net
       depends_on:
         - minio
         - portainer
         - nextcloud-aio-mastercontainer
       restart: unless-stopped
   ```

2. Переконайтеся, що `entrypoint.sh` правильний (ваш приклад виглядає коректно).

3. Запустіть:
   ```bash
   docker-compose up -d
   docker-compose logs -f ssh-tunnel
   ```

---

## Крок 10: Діагностика проблем

Якщо тунель усе ще не працює, виконайте наступні перевірки:

1. **Логи `ssh-tunnel`**:
   ```bash
   docker-compose logs ssh-tunnel
   ```

2. **Перевірка SSH у контейнері**:
   ```bash
   docker-compose exec ssh-tunnel ssh -v -i /root/.ssh/id_rsa vokov@192.168.3.161
   ```

3. **Перевірка мережі Docker**:
   Переконайтеся, що контейнери можуть бачити один одного:
   ```bash
   docker-compose exec ssh-tunnel ping minio
   docker-compose exec ssh-tunnel nc -zv minio 9000
   ```

4. **Логи `cloudflared`**:
   ```bash
   sudo journalctl -u cloudflared -f
   ```

---

## Результати

Після виконання всіх кроків ви повинні мати:
- Робочий SSH-тунель між `192.168.3.99` і `192.168.3.161`.
- Доступ до сервісів через Cloudflare-домени (`minio.kofayokh.pp.ua`, тощо).
- Автоматичне підтримання тунелю через `autossh` у Docker.

Якщо проблема зберігається, надайте:
- Логи `docker-compose logs ssh-tunnel`.
- Логи `journalctl -u ssh` та `journalctl -u cloudflared` з `192.168.3.161`.
- Результати команд `curl` для перевірки доменів.

Це допоможе точно визначити, де саме виникає помилка.
   