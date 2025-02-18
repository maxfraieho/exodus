---
{"title":"Cloudflare R2","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/instrukcziyi/cloudflare-r2/","dgPassFrontmatter":true,"noteIcon":""}
---



Щоб налаштувати **Cloudflare R2** і інтегрувати його з **NocoDB**, потрібно виконати кілька етапів:

---

### **1. Створення R2 Bucket у Cloudflare**

1. **Увійдіть в Cloudflare**:
    
    - Перейдіть на [Cloudflare Dashboard](https://dash.cloudflare.com).
    - Авторизуйтеся або зареєструйтеся, якщо ще не маєте облікового запису.
2. **Перейдіть до R2**:
    
    - У верхньому меню натисніть **R2** (або знайдіть його в розділі **Developer Tools**).
    - Натисніть **Create Bucket** (Створити бакет).
3. **Налаштуйте бакет**:
    
    - Введіть назву (наприклад, `nocodb-storage`).
    - Виберіть **Private** або **Public**, залежно від ваших потреб.
    - Натисніть **Create Bucket**.

---

### **2. Створення API-ключів (Access Keys)**

1. **У вкладці R2 Storage перейдіть до "Access Keys"**.
2. **Створіть новий ключ**:
    - Натисніть **Create API Token**.
    - Виберіть **Read/Write** доступ для керування файлами.
    - Збережіть **Access Key ID** і **Secret Access Key** (вони знадобляться для інтеграції).

---

### **3. Підключення R2 до NocoDB**

1. **Перейдіть в NocoDB**.
    
2. **Відкрийте Налаштування > Storage**.
    
3. **Оберіть Cloudflare R2** зі списку.
    
4. **Введіть необхідні дані**:
    
    - **Endpoint**: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`  
        (Замініть `<ACCOUNT_ID>` на ваш ідентифікатор Cloudflare.)
    - **Access Key**: (Скопіюйте з Cloudflare)
    - **Secret Key**: (Скопіюйте з Cloudflare)
    - **Bucket Name**: `nocodb-storage` (або вашу назву)
5. **Збережіть налаштування**.
    

---

### **4. Тестування**

1. Завантажте файл у NocoDB, використовуючи поле типу **File**.
2. Переконайтеся, що файл успішно завантажується і доступний.

**Готово!** Тепер файли зберігатимуться в Cloudflare R2, а NocoDB буде їх використовувати для ваших проектів. Якщо потрібна допомога на якомусь етапі, питай!