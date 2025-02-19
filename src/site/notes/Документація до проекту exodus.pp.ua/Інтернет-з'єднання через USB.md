---
{"title":"Інтернет-з'єднання через USB","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/internet-z-yednannya-cherez-usb/","dgPassFrontmatter":true,"noteIcon":""}
---


Для налаштування Інтернет-з'єднання через USB між вашим пристроєм `PocoX3Pro` з `Droidian` та хост-машиною на базі `Debian`, виконайте наступні докладні кроки. Ця інструкція базується на вашій переписці та наданих логах команд.

---

## **1. Підготовка Хост-Машини (Debian)**

### **1.1. Підключення Пристрою через USB**

1. **Підключіть `PocoX3Pro` до хост-машини через USB-кабель.**
    
2. **Перевірте, чи система розпізнала новий мережевий інтерфейс:**
    
    ```bash
    ip a
    ```
    
    Ви повинні побачити інтерфейс типу `enxba7d5f900a21` або `rndis0` з відповідною MAC-адресою.
    

### **1.2. Налаштування IP-Адреси на Хост-Машині**

1. **Призначте IP-адресу на USB-інтерфейсі хост-машини:**
    
    ```bash
    sudo ip addr add 10.15.19.100/24 dev enxba7d5f900a21
    ```
    
    _Примітка:_ Замініть `enxba7d5f900a21` на актуальний інтерфейс, якщо він відрізняється.
    
2. **Увімкніть інтерфейс, якщо він ще не активний:**
    
    ```bash
    sudo ip link set enxba7d5f900a21 up
    ```
    

### **1.3. Увімкнення IP-Forwarding та Налаштування NAT**

1. **Увімкніть IP-Forwarding:**
    
    ```bash
    sudo sysctl -w net.ipv4.ip_forward=1
    ```
    
    Для постійного увімкнення додайте рядок у `/etc/sysctl.conf`:
    
    ```bash
    echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
    ```
    
2. **Налаштуйте `iptables` для NAT (маскарадінгу):**
    
    ```bash
    sudo iptables -t nat -A POSTROUTING -o end0 -s 10.15.19.0/24 -j MASQUERADE
    ```
    
    _Примітка:_ Переконайтеся, що `end0` — це інтерфейс, який має доступ до Інтернету. Якщо інший інтерфейс забезпечує Інтернет-з'єднання, замініть `end0` на відповідний.
    
3. **Налаштуйте `iptables` для Docker (якщо використовується Docker):** У вашому випадку вже налаштовані правила Docker. Переконайтеся, що вони не конфліктують з NAT-настройками.
    
4. **Збережіть правила `iptables`, щоб вони застосовувалися після перезавантаження:**
    
    ```bash
    sudo apt install iptables-persistent
    sudo netfilter-persistent save
    ```
    
    _Примітка:_ Під час встановлення `iptables-persistent` вас попросять зберегти поточні правила. Погодьтеся з цим.
    

### **1.4. Перевірка Налаштувань `iptables`**

1. **Перегляньте поточні правила NAT:**
    
    ```bash
    sudo iptables -t nat -S
    ```
    
    Переконайтеся, що правило маскараду додано правильно:
    
    ```
    -A POSTROUTING -s 10.15.19.0/24 -o end0 -j MASQUERADE
    ```
    
2. **Перевірте, чи IP-Forwarding увімкнено:**
    
    ```bash
    sysctl net.ipv4.ip_forward
    ```
    
    Вивід повинен бути:
    
    ```
    net.ipv4.ip_forward = 1
    ```
    

---

## **2. Налаштування Клієнта (PocoX3Pro з Droidian)**

### **2.1. Перевірка Мережевих Інтерфейсів**

1. **Перевірте наявність USB-інтерфейсу:**
    
    ```bash
    ip a
    ```
    
    Ви повинні побачити інтерфейс `rndis0` з IP-адресою 10.15.19.82/24.

### **2.2. Налаштування IP-Адреси та Маршруту**

1. **Призначте статичну IP-адресу на USB-інтерфейсі:**
    
    ```bash
    sudo ip addr add 10.15.19.2/24 dev rndis0
    ```
    
2. **Додайте шлюз за замовчуванням:**
    
    ```bash
    sudo ip route add default via 10.15.19.100 dev rndis0
    ```
    
3. **Перевірте, чи успішно доданий маршрут:**
    
    ```bash
    ip route
    ```
    
    Ви повинні побачити рядок:
    
    ```
    default via 10.15.19.100 dev rndis0
    ```
    

### **2.3. Налаштування DNS**

1. **Відредагуйте файл `/etc/resolv.conf`:**
    
    ```bash
    sudo nano /etc/resolv.conf
    ```
    
    Додайте наступні рядки:
    
    ```
    nameserver 8.8.8.8
    nameserver 8.8.4.4
    ```
    
    Збережіть файл (`Ctrl + O`, потім `Enter`) та закрийте (`Ctrl + X`).
    
2. **Налаштуйте `systemd-resolved`:**
    
    - **Увімкніть та запустіть `systemd-resolved`:**
        
        ```bash
        sudo systemctl enable systemd-resolved
        sudo systemctl start systemd-resolved
        ```
        
    - **Вкажіть DNS-сервери для `rndis0`:**
        
        ```bash
        sudo resolvectl dns rndis0 8.8.8.8 8.8.4.4
        sudo resolvectl default rndis0
        ```
        
3. **Перевірте статус `systemd-resolved`:**
    
    ```bash
    systemctl status systemd-resolved
    ```
    
    Переконайтеся, що сервіс активний і працює без помилок.
    
4. **Створіть символьне посилання на `systemd-resolved`:**
    
    ```bash
    sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
    ```
    
    Переконайтеся, що вміст `/etc/resolv.conf` відповідає:
    
    ```
    nameserver 127.0.0.53
    ```
    

### **2.4. Тестування З'єднання**

1. **Перевірте пінг до зовнішніх IP-адрес:**
    
    ```bash
    ping -c 4 8.8.8.8
    ```
    
    Ви повинні побачити успішні відповіді.
    
2. **Перевірте пінг до доменного імені:**
    
    ```bash
    ping -c 4 google.com
    ```
    
    Якщо пінг успішний, Інтернет-з'єднання працює на рівні DNS.
    

---

## **3. Налаштування Часу та Синхронізації (Вирішення Проблем)**

### **3.1. Налаштування `systemd-timesyncd`**

1. **Перевірте статус `systemd-timesyncd`:**
    
    ```bash
    systemctl status systemd-timesyncd
    ```
    
    Якщо сервіс не активний, увімкніть та запустіть його:
    
    ```bash
    sudo systemctl enable systemd-timesyncd
    sudo systemctl start systemd-timesyncd
    ```
    
2. **Відредагуйте файл конфігурації `timesyncd`:**
    
    ```bash
    sudo nano /etc/systemd/timesyncd.conf
    ```
    
    Переконайтеся, що секція `[Time]` містить коректні NTP-сервери. Наприклад:
    
    ```
    [Time]
    NTP=0.debian.pool.ntp.org 1.debian.pool.ntp.org 2.debian.pool.ntp.org 3.debian.pool.ntp.org
    FallbackNTP=ntp.ubuntu.com
    ```
    
    Збережіть файл і закрийте його.
    
3. **Перезапустіть сервіс `systemd-timesyncd`:**
    
    ```bash
    sudo systemctl restart systemd-timesyncd
    ```
    
4. **Перевірте статус синхронізації часу:**
    
    ```bash
    timedatectl status
    ```
    
    Якщо виникають помилки "Failed to query server: Access denied", виконайте наступні кроки.
    

### **3.2. Налаштування `polkit` для `timedatectl`**

1. **Переконайтеся, що `polkit` працює:**
    
    ```bash
    systemctl status polkit
    ```
    
    Якщо сервіс не активний, увімкніть та запустіть його:
    
    ```bash
    sudo systemctl enable polkit
    sudo systemctl start polkit
    ```
    
2. **Додайте вашого користувача до групи `sudo`:**
    
    ```bash
    sudo usermod -aG sudo droidian
    ```
    
    Після цього вийдіть із системи та увійдіть знову, щоб зміни набули чинності.
    
3. **Перевірте права доступу користувача:**
    
    ```bash
    groups
    ```
    
    Ви повинні бачити групу `sudo` у списку.
    

### **3.3. Виправлення Дозволів для `timedatectl`**

1. **Переконайтеся, що ваш користувач має необхідні права:** Якщо `timedatectl` все ще не працює, можливо, потрібно перевірити політики `polkit`.
    
2. **Створіть файл політики для `timedatectl`:**
    
    ```bash
    sudo nano /etc/polkit-1/rules.d/50-timedatectl.rules
    ```
    
    Додайте наступний вміст:
    
    ```javascript
    polkit.addRule(function(action, subject) {
        if (action.id == "org.freedesktop.timedate1.set-time" ||
            action.id == "org.freedesktop.timedate1.set-timezone" ||
            action.id == "org.freedesktop.timedate1.set-ntp") {
            return polkit.Result.YES;
        }
    });
    ```
    
    Збережіть файл та закрийте його.
    
3. **Перезапустіть `polkit`:**
    
    ```bash
    sudo systemctl restart polkit
    ```
    
4. **Перевірте статус часу:**
    
    ```bash
    timedatectl status
    ```
    
    Тепер команда повинна працювати без помилок.
    

---

## **4. Остаточна Перевірка та Перезавантаження**

1. **Перезавантажте обидва пристрої (хост та клієнт):**
    
    - **На хост-машині:**
        
        ```bash
        sudo reboot
        ```
        
    - **На клієнті:**
        
        ```bash
        sudo reboot
        ```
        
2. **Після перезавантаження перевірте з'єднання:**
    
    - **На хост-машині:**
        
        ```bash
        ip a
        sudo iptables -t nat -S
        ```
        
    - **На клієнті:**
        
        ```bash
        ip a
        ping -c 4 8.8.8.8
        ping -c 4 google.com
        timedatectl status
        ```
        
3. **Переконайтеся, що Інтернет-з'єднання працює стабільно та час синхронізується автоматично.**
    

---

## **5. Додаткові Налаштування та Вирішення Проблем**

### **5.1. Перевірка Правильності Конфігурації DNS**

1. **Перевірте, чи правильно налаштований файл `/etc/resolv.conf`:**
    
    ```bash
    cat /etc/resolv.conf
    ```
    
    Він повинен містити:
    
    ```
    nameserver 127.0.0.53
    ```
    
    або ваші вказані DNS-сервери:
    
    ```
    nameserver 8.8.8.8
    nameserver 8.8.4.4
    ```
    
2. **Якщо необхідно, перезапустіть `systemd-resolved`:**
    
    ```bash
    sudo systemctl restart systemd-resolved
    ```
    

### **5.2. Перевірка `iptables` та Правил NAT**

1. **Перегляньте поточні правила NAT:**
    
    ```bash
    sudo iptables -t nat -S
    ```
    
    Переконайтеся, що правила маскараду та перенаправлення (`DNAT`) налаштовані правильно.
    
2. **При необхідності видаліть зайві або неправильні правила:**
    
    ```bash
    sudo iptables -t nat -D POSTROUTING -o end0 -s 10.15.19.0/24 -j MASQUERADE
    ```
    
    Потім додайте їх знову коректно.
    

### **5.3. Перевірка Логів Мережі**

1. **Перегляньте лог-файли для діагностики:**
    
    ```bash
    sudo journalctl -xe
    sudo journalctl -u systemd-timesyncd
    sudo journalctl -u systemd-resolved
    sudo journalctl -u polkit
    ```
    
    Шукайте помилки або попередження, які можуть вказувати на причину проблем.

### **5.4. Встановлення Додаткових Інструментів для Налаштування Мережі**

1. **Встановіть `net-tools` (хоча у вас вже встановлений):**
    
    ```bash
    sudo apt install net-tools
    ```
    
2. **Використовуйте `nmcli` або `nmtui` для більш зручного налаштування мережі, якщо необхідно:**
    
    ```bash
    sudo apt install network-manager
    sudo systemctl enable NetworkManager
    sudo systemctl start NetworkManager
    ```
    

### **5.5. Виправлення Проблем з `systemd-timesyncd`**

1. **Переконайтеся, що NTP-сервери доступні:** Використайте пінг або `ntpdate` (якщо встановлений) для перевірки доступності NTP-серверів:
    
    ```bash
    ping -c 4 pool.ntp.org
    ```
    
2. **Встановіть пакет `chrony` (якщо `systemd-timesyncd` не працює належним чином):**
    
    ```bash
    sudo apt install chrony
    sudo systemctl enable chrony
    sudo systemctl start chrony
    ```
    
    _Примітка:_ У вашому випадку спроба встановити `chrony` не вдалася, оскільки пакет не існує. Переконайтеся, що `systemd-timesyncd` налаштований правильно.
    

---

## **6. Рекомендації та Заключні Дії**

- **Переконайтеся, що всі мережеві інтерфейси активні та правильно налаштовані.**
    
- **Регулярно перевіряйте оновлення системи та встановлених пакетів для забезпечення стабільності та безпеки:**
    
    ```bash
    sudo apt update
    sudo apt upgrade
    ```
    
- **Якщо ви використовуєте Docker або інші контейнерні технології, переконайтеся, що їх мережеві налаштування не конфліктують з налаштуваннями USB-з'єднання.**
    
- **Переконайтеся, що файрвол хост-машини не блокує потрібні порти та протоколи:**
    
    ```bash
    sudo ufw status
    ```
    
    Якщо необхідно, дозвольте трафік через USB-інтерфейс:
    
    ```bash
    sudo ufw allow in on enxba7d5f900a21
    sudo ufw allow out on enxba7d5f900a21
    ```
    
- **Якщо виникають додаткові питання або проблеми, звертайтеся до логів системи або спільнот підтримки `Droidian` та `Debian`.**
    

---

Сподіваюсь, ця інструкція допоможе вам успішно налаштувати Інтернет-з'єднання через USB між хост-машиною на `Debian` та вашим пристроєм `PocoX3Pro` з `Droidian`. Якщо виникнуть додаткові питання або проблеми, будь ласка, надайте додаткову інформацію для подальшої допомоги.