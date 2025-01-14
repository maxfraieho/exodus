---
{"title":"OneShot","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/instrukcziyi/one-shot/","dgPassFrontmatter":true,"noteIcon":""}
---


# Інструкція з встановлення OneShot у Termuх

---

## 1. Підготовка середовища

1. **Оновіть пакети Termux:**
   ```bash
   pkg update && pkg upgrade -y

2. Встановіть базові пакети:

pkg install wget root-repo openssl dpkg apt -y


3. Перевірте наявність apt та оновіть його, якщо потрібно:

apt update -y && apt upgrade -y




---

2. Завантаження та встановлення OneShot

1. Завантажте .deb файл OneShot:

wget https://github.com/Rem01Gaming/OneShot-Termux/releases/download/v1.0.1/oneshot.deb


2. Встановіть пакет за допомогою dpkg:

dpkg -i ./oneshot.deb


3. Якщо виникають помилки залежностей, виправте їх:

apt --fix-broken install -y




---

3. Встановлення залежностей

OneShot потребує наступних пакетів: pixiewps, wpa-supplicant, tsu, iw. Виконайте наступні кроки:

1. Встановіть pixiewps:

git clone https://github.com/wiire/pixiewps.git
cd pixiewps
make
make install


2. Встановіть інші пакети:

```bash
pkg install wpa-supplicant tsu iw -y


3. Якщо виникають помилки залежностей, скористайтеся:
```badh
apt --fix-broken install -y




---

4. Перевірка встановлення

1. Запустіть OneShot для перевірки:

oneshot

Ви повинні побачити короткий опис доступних параметрів.


2. Якщо OneShot працює коректно, налаштування завершене.




---

5. Використання OneShot

Запустіть OneShot із необхідними параметрами. Наприклад:

```bash
oneshot -i <interface> -b <BSSID> -p <PIN>



Готово! Ви успішно встановили та налаштували OneShot у Termux.

```badh
sudo oneshot -i wlan0 -K
```

