---
{"title":"Практичне розгортання LiteLLM на Cloudflare Workers з трьома акаунтами","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/praktichne-rozgortannya-lite-llm-na-cloudflare-workers-z-troma-akauntami/","dgPassFrontmatter":true,"noteIcon":""}
---



У цій статті я розгляну, як розгорнути **LiteLLM** на **Cloudflare Workers** для управління трьома акаунтами Cloudflare AI, розмістивши сам Worker на четвертому акаунті. Таке рішення дозволяє обійти обмеження безкоштовного плану Cloudflare AI, зокрема на довжину відповідей, завдяки розподілу запитів між кількома акаунтами та каскадній обробці великих текстів.

---

## Передумови

Для реалізації цього рішення вам знадобляться:

- **Чотири акаунти Cloudflare**: три для доступу до Cloudflare AI та один для розміщення Worker.
- **API-ключі** для кожного акаунта (інструкція нижче).
- Базові знання **JavaScript** та роботи з **Cloudflare Workers**.
- Встановлений інструмент **Cloudflare Wrangler** для розгортання Worker.

---

## Крок 1: Підготовка акаунтів Cloudflare

1. **Створіть чотири акаунти Cloudflare**, якщо їх ще немає. Ви можете використовувати різні email-адреси для цього.
2. **Отримайте API-ключі**:
   - Увійдіть у кожен акаунт.
   - Перейдіть у розділ *My Profile* → *API Tokens* → *Create Token*.
   - Для акаунтів AI оберіть шаблон із доступом до *Cloudflare AI*.
   - Для четвертого акаунта (Worker) виберіть *Edit Cloudflare Workers*.
   - Збережіть згенеровані ключі та ID акаунтів.

---

## Крок 2: Налаштування Cloudflare Worker на четвертому акаунті

Worker виступатиме як проксі-сервер (LiteLLM), що розподілятиме запити між трьома акаунтами Cloudflare AI.

### 2.1. Встановлення Wrangler

Встановіть Wrangler глобально за допомогою npm:

```
npm install -g @cloudflare/wrangler
```

### 2.2. Створення нового Worker

Створіть проєкт для Worker:

```
wrangler generate litellm-proxy
cd litellm-proxy
```

### 2.3. Налаштування `wrangler.toml`

Відкрийте файл `wrangler.toml` і додайте наступне:

```toml
name = "litellm-proxy"
main = "src/index.js"
account_id = "<YOUR_FOURTH_ACCOUNT_ID>"
compatibility_date = "2023-01-01"

[vars]
ACCOUNT_1_API_KEY = "<API_KEY_1>"
ACCOUNT_2_API_KEY = "<API_KEY_2>"
ACCOUNT_3_API_KEY = "<API_KEY_3>"
ACCOUNT_1_ID = "<ACCOUNT_1_ID>"
ACCOUNT_2_ID = "<ACCOUNT_2_ID>"
ACCOUNT_3_ID = "<ACCOUNT_3_ID>"
```

- Замініть `<YOUR_FOURTH_ACCOUNT_ID>` на ID четвертого акаунта.
- Вставте відповідні `<API_KEY_X>` та `<ACCOUNT_X_ID>` для кожного з трьох акаунтів AI.

---

## Крок 3: Розробка LiteLLM Worker

Створіть файл `src/index.js` із кодом для Worker. Цей код реалізує балансування запитів методом *round-robin* між трьома акаунтами.

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

const ACCOUNTS = [
  { id: ACCOUNT_1_ID, apiKey: ACCOUNT_1_API_KEY },
  { id: ACCOUNT_2_ID, apiKey: ACCOUNT_2_API_KEY },
  { id: ACCOUNT_3_ID, apiKey: ACCOUNT_3_API_KEY },
];

let currentAccount = 0;

async function handleRequest(request) {
  const account = ACCOUNTS[currentAccount];
  currentAccount = (currentAccount + 1) % ACCOUNTS.length;

  const url = `https://api.cloudflare.com/client/v4/accounts/${account.id}/ai/run`;
  const headers = {
    'Authorization': `Bearer ${account.apiKey}`,
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    method: request.method,
    headers: headers,
    body: request.body,
  });

  const text = await response.text();
  if (text.length >= 4096) {  // Умовний ліміт відповіді
    return new Response(text + " [TRUNCATED]", { status: 200 });
  }
  return new Response(text, { status: 200 });
}
```

### Пояснення коду:
- **Масив `ACCOUNTS`**: Містить ID та API-ключі трьох акаунтів AI, взяті з змінних оточення.
- **Лічильник `currentAccount`**: Використовується для циклічного перемикання між акаунтами.
- **Обробка запитів**: Worker надсилає запит до API Cloudflare AI відповідного акаунта.
- **Перевірка ліміту**: Якщо відповідь перевищує 4096 символів (умовний ліміт), додається маркер `[TRUNCATED]`.

---

## Крок 4: Розгортання Worker

Розгорніть Worker за допомогою команди:

```
wrangler publish
```

Після успішного розгортання ви отримаєте URL, наприклад: `https://litellm-proxy.yourdomain.workers.dev`.

---

## Крок 5: Інтеграція з n8n (опціонально)

Для автоматизації запитів можна інтегрувати Worker із **n8n**:

1. **Налаштуйте HTTP Request вузол**:
   - **URL**: `https://litellm-proxy.yourdomain.workers.dev`
   - **Метод**: POST
   - **Тіло запиту**: JSON із параметрами для Cloudflare AI, наприклад:
     ```json
     {
       "prompt": "Ваш запит тут",
       "max_tokens": 1000
     }
     ```

2. **Обробка `[TRUNCATED]`**:
   - Додайте умовний вузол у n8n для перевірки наявності маркера `[TRUNCATED]`.
   - Якщо маркер присутній, налаштуйте повторний запит із оновленим промптом для продовження генерації.

---

## Крок 6: Тестування

1. Надішліть тестовий запит через n8n або за допомогою `curl`:
   ```
   curl -X POST https://litellm-proxy.yourdomain.workers.dev \
   -H "Content-Type: application/json" \
   -d '{"prompt": "Розкажи про Cloudflare Workers", "max_tokens": 1000}'
   ```
2. Перевірте, чи Worker розподіляє запити між трьома акаунтами (можна додати логування через `console.log` та переглянути логи в `wrangler tail`).
3. Переконайтеся, що великі відповіді коректно позначаються маркером `[TRUNCATED]`.

---

## Висновок

Розгортання **LiteLLM** на Cloudflare Workers із використанням чотирьох акаунтів дозволяє ефективно обходити обмеження безкоштовного плану Cloudflare AI. Завдяки балансуванню запитів між трьома акаунтами та обробці великих текстів через каскадні запити ви можете масштабувати свою систему, наприклад, для RAG-додатків чи генеративних задач.