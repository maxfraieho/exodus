---
{"title":"Побудова українськомовної RAG-системи на базі Cloudflare Workers AI пошук у Markdown-нотатках з GitMCP","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/pobudova-ukrayinskomovnoyi-rag-sistemi-na-bazi-cloudflare-workers-ai-poshuk-u-markdown-notatkah-z-git-mcp/","dgPassFrontmatter":true,"noteIcon":""}
---



У цій статті я поясню, як створити систему пошуку та генерації відповідей (Retrieval-Augmented Generation, RAG) для україномовних Markdown-файлів із репозиторію GitMCP, використовуючи безкоштовний план Cloudflare Workers AI. Ми обійдемо обмеження безкоштовного плану, оптимізуємо систему за допомогою кешування, каскадних запитів і ротації акаунтів, а також додамо зручні інтерфейси через Telegram і веб-сторінку.

Ця інструкція підійде як для новачків, так і для досвідчених розробників, які хочуть повторити проєкт або адаптувати його під власні потреби.

## Вступ: яка проблема вирішується

Уявіть, що у вас є колекція україномовних Markdown-нотаток у GitMCP (наприклад, [maxfraieho/exodus](https://gitmcp.io/maxfraieho/exodus/src/site/notes)), і ви хочете:

1. Швидко знаходити релевантні фрагменти тексту за запитами.
2. Отримувати структуровані відповіді українською мовою на основі цих нотаток.
3. Робити це через Telegram-бот або веб-інтерфейс.

При цьому ми обмежені безкоштовним планом Cloudflare AI, який має ліміти на кількість запитів, розмір тексту та обчислювальні ресурси. Наша мета — створити систему, яка працює в межах цих обмежень, але залишається функціональною та масштабованою.

## Огляд архітектури

![RAG Архітектура](https://via.placeholder.com/800x500)

Система складається з таких компонентів:

1. **Джерело даних**: Markdown-файли з GitMCP.
2. **Векторизація**: Cloudflare Workers AI (модель `@cf/baai/bge-small-en-v1.5`) для створення ембедінгів.
3. **Зберігання векторів**: Cloudflare Vectorize.
4. **Кешування**: Cloudflare D1 (SQL-база).
5. **Генерація відповідей**: Cloudflare Workers AI (модель `@cf/meta/llama-3-8b-instruct`).
6. **Обхід обмежень**:
    - Ротація між кількома безкоштовними акаунтами через LiteLLM.
    - Каскадні запити з маркуванням `[TRUNCATED]`.
    - Кешування результатів у D1.
7. **Інтерфейси**: Telegram-бот і веб-інтерфейс на Cloudflare Pages (з Hono).
8. **Автоматизація**: n8n для періодичного оновлення даних.

## Обхід обмежень безкоштовного плану

Безкоштовний план Cloudflare AI має такі обмеження:

- Ліміт запитів до AI-моделей (~10 000 на день).
- Обмеження на розмір тексту в запитах і відповідях.
- Ліміти Vectorize і D1 за обсягом операцій.

Ми обійдемо їх так:

1. **Оркестрація кількох акаунтів**: Розподілимо навантаження між кількома безкоштовними акаунтами через LiteLLM.
2. **Каскадні запити**: Розіб’ємо великі тексти на фрагменти й оброблятимемо їх послідовно, позначаючи обрізані відповіді як `[TRUNCATED]`.
3. **Кешування**: Зберігатимемо ембедінги та відповіді в D1, щоб уникнути повторних запитів.

## Покрокове налаштування системи

### Крок 1: Налаштування кількох акаунтів Cloudflare

1. Зареєструйте 3+ безкоштовних акаунтів на [Cloudflare](https://www.cloudflare.com/).
2. У кожному акаунті створіть:
    - Workers AI проєкт.
    - Vectorize індекс.
    - D1 базу даних.
3. Збережіть API-ключи та ID акаунтів для подальшої інтеграції.

### Крок 2: Налаштування Cloudflare Vectorize

Створіть Vectorize індекс у кожному акаунті для зберігання ембедінгів:

```bash
npx wrangler vectorize create rag-vectorize \
  --dimensions=384 \
  --metric=cosine
```

Розмірність 384 відповідає моделі `@cf/baai/bge-small-en-v1.5`.

### Крок 3: Налаштування D1 бази даних

Створіть D1 базу для кешування:

```bash
npx wrangler d1 create rag-cache
npx wrangler d1 execute rag-cache --command="
CREATE TABLE IF NOT EXISTS cache (
  key TEXT PRIMARY KEY,
  data TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)"
```

### Крок 4: Код основного Cloudflare Worker

Ось основний код Worker’а, який обробляє векторизацію, запити користувача й інтеграцію з Telegram:

```typescript
import { Ai } from '@cloudflare/ai';
import { Hono } from 'hono';
import { cors } from 'hono/cors';

interface Env {
  AI: Ai;
  VECTORIZE: any;
  D1: D1Database;
  GITHUB_TOKEN: string;
  TELEGRAM_TOKEN: string;
  ACCOUNT_ENDPOINTS: string;
}

interface GitMCPFile { path: string; content: string; }
interface GitMCPResponse { files: GitMCPFile[]; }
interface EmbeddingResponse { vectorId: string; path: string; embedding: number[]; }

const app = new Hono<{ Bindings: Env }>();
app.use('*', cors());

app.post('/vectorize', async (c) => {
  const { repo, owner } = await c.req.json<{ repo: string; owner: string }>();
  if (!repo || !owner) return c.json({ error: 'Відсутній репозиторій або власник' }, 400);

  const ai = new Ai(c.env.AI);
  try {
    const cacheKey = `${owner}/${repo}`;
    const cached = await c.env.D1.prepare('SELECT * FROM cache WHERE key = ?').bind(cacheKey).first();
    if (cached) return c.json({ message: 'Використовуємо кешовані ембедінги', key: cacheKey });

    const gitMcpResponse = await fetchGitMcpData(owner, repo, c.env.GITHUB_TOKEN);
    const embeddings: EmbeddingResponse[] = [];

    for (const file of gitMcpResponse.files) {
      if (!file.content || !file.path.endsWith('.md')) continue;
      const chunks = chunkMarkdown(file.content, 1000);

      for (let i = 0; i < chunks.length; i++) {
        const embeddingResponse = await ai.run('@cf/baai/bge-small-en-v1.5', { text: chunks[i] }) as { data: number[][] };
        const embedding = embeddingResponse.data[0];
        const vectorId = `${owner}/${repo}/${file.path}:${i}`;

        await c.env.VECTORIZE.upsert([{ id: vectorId, values: embedding, metadata: { path: file.path, repo, owner, chunk: i, text: chunks[i] } }]);
        embeddings.push({ vectorId, path: file.path, embedding });
      }
    }

    await c.env.D1.prepare('INSERT INTO cache (key, data) VALUES (?, ?)').bind(cacheKey, JSON.stringify(embeddings)).run();
    return c.json({ message: 'Векторизація успішна', embeddings });
  } catch (error) {
    console.error('Помилка векторизації:', error);
    return c.json({ error: `Не вдалося векторизувати: ${(error as Error).message}` }, 500);
  }
});

app.get('/query', async (c) => {
  const queryText = c.req.query('q');
  if (!queryText) return c.json({ error: 'Відсутній запит' }, 400);

  const ai = new Ai(c.env.AI);
  try {
    const cacheKey = `query:${queryText}`;
    const cachedResult = await c.env.D1.prepare('SELECT data FROM cache WHERE key = ?').bind(cacheKey).first();
    if (cachedResult) return c.json(JSON.parse(cachedResult.data));

    const queryEmbeddingResponse = await ai.run('@cf/baai/bge-small-en-v1.5', { text: queryText }) as { data: number[][] };
    const queryEmbedding = queryEmbeddingResponse.data[0];
    const queryResult = await c.env.VECTORIZE.query(queryEmbedding, { topK: 5, returnMetadata: true });

    const contexts = queryResult.matches.map(match => ({ text: match.metadata?.text || 'Дані відсутні', path: match.metadata?.path, score: match.score }));
    const systemPrompt = `Ти експерт з україномовних текстів. Відповідай українською мовою, використовуючи наданий контекст. Якщо в контексті немає відповіді, чесно скажи про це.`;
    const contextText = contexts.map(c => c.text).join('\n\n');

    let response = await generateResponseWithLLM(ai, systemPrompt, contextText, queryText);
    if (response.endsWith('[TRUNCATED]')) response = await handleTruncatedResponse(ai, response, systemPrompt, contextText, queryText);

    const result = { response, contexts };
    await c.env.D1.prepare('INSERT INTO cache (key, data) VALUES (?, ?)').bind(cacheKey, JSON.stringify(result)).run();
    return c.json(result);
  } catch (error) {
    console.error('Помилка запиту:', error);
    return c.json({ error: `Не вдалося обробити запит: ${(error as Error).message}` }, 500);
  }
});

app.post('/telegram', async (c) => {
  const ai = new Ai(c.env.AI);
  const payload = await c.req.json<any>();
  const message = payload.message;
  if (!message?.text) return c.json({ error: 'Повідомлення відсутнє' }, 400);

  try {
    const queryEmbeddingResponse = await ai.run('@cf/baai/bge-small-en-v1.5', { text: message.text }) as { data: number[][] };
    const queryEmbedding = queryEmbeddingResponse.data[0];
    const queryResult = await c.env.VECTORIZE.query(queryEmbedding, { topK: 3, returnMetadata: true });

    const contexts = queryResult.matches.map(match => match.metadata?.text || 'Дані відсутні');
    const systemPrompt = `Ти україномовний Telegram-бот. Відповідай коротко, точно та інформативно, використовуючи наданий контекст.`;
    const contextText = contexts.join('\n\n');

    const response = await ai.run('@cf/meta/llama-3-8b-instruct', {
      prompt: `${systemPrompt}\n\nКонтекст: ${contextText}\n\nЗапит: ${message.text}`,
      max_tokens: 300,
    }) as { response: string };

    await fetch(`https://api.telegram.org/bot${c.env.TELEGRAM_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: message.chat.id, text: response.response }),
    });

    return c.json({ status: 'ok' });
  } catch (error) {
    console.error('Помилка Telegram:', error);
    await fetch(`https://api.telegram.org/bot${c.env.TELEGRAM_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: message.chat.id, text: 'Вибачте, сталася помилка. Спробуйте пізніше.' }),
    });
    return c.json({ error: `Не вдалося обробити запит: ${(error as Error).message}` }, 500);
  }
});

async function fetchGitMcpData(owner: string, repo: string, token: string): Promise<GitMCPResponse> {
  const response = await fetch(`https://api.gitmcp.io/repos/${owner}/${repo}/files`, {
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
  });
  if (!response.ok) throw new Error(`Помилка API GitMCP: ${response.status}`);
  return await response.json() as GitMCPResponse;
}

function chunkMarkdown(text: string, maxChunkSize: number): string[] {
  const headerRegex = /^(#+)\s+(.*)/gm;
  const sections = [];
  let lastIndex = 0;
  let match;

  while ((match = headerRegex.exec(text)) !== null) {
    if (lastIndex < match.index) sections.push(text.substring(lastIndex, match.index));
    lastIndex = match.index;
  }
  if (lastIndex < text.length) sections.push(text.substring(lastIndex));

  const chunks = [];
  for (const section of sections) {
    if (section.length <= maxChunkSize) {
      chunks.push(section);
    } else {
      const paragraphs = section.split('\n\n');
      let currentChunk = '';
      for (const paragraph of paragraphs) {
        if (currentChunk.length + paragraph.length + 2 <= maxChunkSize) {
          currentChunk += (currentChunk ? '\n\n' : '') + paragraph;
        } else {
          if (currentChunk) chunks.push(currentChunk);
          if (paragraph.length > maxChunkSize) {
            const sentences = paragraph.match(/[^.!?]+[.!?]+/g) || [paragraph];
            let sentenceChunk = '';
            for (const sentence of sentences) {
              if (sentenceChunk.length + sentence.length <= maxChunkSize) {
                sentenceChunk += sentence;
              } else {
                if (sentenceChunk) chunks.push(sentenceChunk);
                if (sentence.length > maxChunkSize) {
                  for (let i = 0; i < sentence.length; i += maxChunkSize) chunks.push(sentence.substring(i, i + maxChunkSize));
                } else {
                  sentenceChunk = sentence;
                }
              }
            }
            if (sentenceChunk) chunks.push(sentenceChunk);
          } else {
            currentChunk = paragraph;
          }
        }
      }
      if (currentChunk) chunks.push(currentChunk);
    }
  }
  return chunks;
}

async function generateResponseWithLLM(ai: Ai, systemPrompt: string, context: string, query: string): Promise<string> {
  const response = await ai.run('@cf/meta/llama-3-8b-instruct', {
    prompt: `${systemPrompt}\n\nКонтекст: ${context}\n\nЗапит: ${query}`,
    max_tokens: 800,
  }) as { response: string };
  return response.response.length >= 1500 ? response.response + ' [TRUNCATED]' : response.response;
}

async function handleTruncatedResponse(ai: Ai, partialResponse: string, systemPrompt: string, context: string, query: string): Promise<string> {
  const cleanResponse = partialResponse.replace('[TRUNCATED]', '').trim();
  const continuationPrompt = `${systemPrompt}\n\nКонтекст: ${context}\n\nЗапит: ${query}\n\nОсь початок відповіді, продовжи її: ${cleanResponse}`;
  const continuation = await ai.run('@cf/meta/llama-3-8b-instruct', { prompt: continuationPrompt, max_tokens: 800 }) as { response: string };
  const fullResponse = cleanResponse + ' ' + continuation.response;
  return continuation.response.length >= 1500 ? fullResponse + ' [TRUNCATED]' : fullResponse;
}

export default app;
```

**Налаштування Worker’а**:

1. Розгорніть через `npx wrangler deploy`.
2. Додайте секрети:
    
    ```bash
    npx wrangler secret put GITHUB_TOKEN
    npx wrangler secret put TELEGRAM_TOKEN
    npx wrangler secret put ACCOUNT_ENDPOINTS
    ```
    
3. Налаштуйте `wrangler.toml`:
    
    ```toml
    name = "rag-worker"
    main = "src/main.ts"
    compatibility_date = "2023-10-30"
    
    [[vectorize]]
    binding = "VECTORIZE"
    index_name = "rag-vectorize"
    
    [[d1_databases]]
    binding = "D1"
    database_name = "rag-cache"
    database_id = "your-database-id"
    ```
    

### Крок 5: Інтеграція LiteLLM для ротації акаунтів

Встановіть LiteLLM як проксі для розподілу запитів між акаунтами:

```yaml
model_list:
  - model_name: cloudflare-ai
    litellm_params:
      model: "@cf/meta/llama-3-8b-instruct"
      api_key: "$CLOUDFLARE_API_KEY_1"
      api_base: "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID_1/ai"
  - model_name: cloudflare-ai
    litellm_params:
      model: "@cf/meta/llama-3-8b-instruct"
      api_key: "$CLOUDFLARE_API_KEY_2"
      api_base: "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID_2/ai"
  - model_name: cloudflare-ai
    litellm_params:
      model: "@cf/meta/llama-3-8b-instruct"
      api_key: "$CLOUDFLARE_API_KEY_3"
      api_base: "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID_3/ai"

router_settings:
  routing_strategy: "simple-shuffle"
  log_requests: true
  num_retries: 3
  timeout: 30

general_settings:
  port: 8000
```

**Скрипт запуску**:

```bash
#!/bin/bash
export CLOUDFLARE_API_KEY_1="your-api-key-1"
export CLOUDFLARE_API_KEY_2="your-api-key-2"
export CLOUDFLARE_API_KEY_3="your-api-key-3"
export ACCOUNT_ID_1="your-account-id-1"
export ACCOUNT_ID_2="your-account-id-2"
export ACCOUNT_ID_3="your-account-id-3"
litellm --config litellm_config.yaml
```

### Крок 6: Веб-інтерфейс на Cloudflare Pages

Створіть простий веб-інтерфейс:

```typescript
import { Hono } from 'hono';

const app = new Hono();

app.get('/', (c) => c.html(`
  <!DOCTYPE html>
  <html lang="uk">
  <head>
    <meta charset="UTF-8">
    <title>RAG Інструмент</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="bg-gray-100">
    <div class="container mx-auto p-4">
      <h1 class="text-2xl font-bold mb-4">RAG Інструмент</h1>
      <textarea id="query" class="w-full p-2 border rounded" placeholder="Введіть запит..."></textarea>
      <button onclick="sendQuery()" class="mt-2 bg-blue-500 text-white p-2 rounded">Надіслати</button>
      <div id="response" class="mt-4"></div>
    </div>
    <script>
      async function sendQuery() {
        const query = document.getElementById('query').value;
        const responseDiv = document.getElementById('response');
        responseDiv.innerHTML = 'Завантаження...';
        const res = await fetch('/api/query?q=' + encodeURIComponent(query));
        const data = await res.json();
        responseDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
      }
    </script>
  </body>
  </html>
`));

app.get('/api/query', async (c) => {
  const query = c.req.query('q');
  if (!query) return c.json({ error: 'Відсутній запит' }, 400);
  const workerUrl = 'https://your-worker.workers.dev/query?q=' + encodeURIComponent(query);
  const res = await fetch(workerUrl);
  return c.json(await res.json());
});

export default app;
```

**Розгортання**:

```bash
npx wrangler pages project create rag-interface
npx wrangler pages publish .
```

### Крок 7: Автоматизація через n8n

Налаштуйте n8n для оновлення даних:

```json
{
  "name": "Update RAG Data",
  "nodes": [
    { "parameters": { "interval": 86400 }, "name": "Schedule Trigger", "type": "n8n-nodes-base.scheduleTrigger", "position": [240, 300] },
    { "parameters": { "url": "https://api.gitmcp.io/repos/maxfraieho/exodus/files", "headers": { "header": [{ "name": "Authorization", "value": "Bearer {{ $secrets.GITHUB_TOKEN }}" }] } }, "name": "Fetch GitMCP", "type": "n8n-nodes-base.httpRequest", "position": [460, 300] },
    { "parameters": { "url": "https://your-worker.workers.dev/vectorize", "method": "POST", "jsonBody": { "owner": "maxfraieho", "repo": "exodus" } }, "name": "Vectorize", "type": "n8n-nodes-base.httpRequest", "position": [680, 300] }
  ],
  "connections": {
    "Schedule Trigger": { "main": [[{ "node": "Fetch GitMCP", "type": "main", "index": 0 }]] },
    "Fetch GitMCP": { "main": [[{ "node": "Vectorize", "type": "main", "index": 0 }]] }
  }
}
```

**Налаштування**:

1. Встановіть n8n: `npm install -g n8n && n8n start`.
2. Імпортуйте JSON у n8n UI.
3. Додайте `GITHUB_TOKEN` у секрети n8n.

### Крок 8: Інтеграція з Telegram

1. Створіть бота через [@BotFather](https://t.me/BotFather) і отримайте `TELEGRAM_TOKEN`.
2. Налаштуйте webhook:
    
    ```bash
    curl -X POST "https://api.telegram.org/bot<TELEGRAM_TOKEN>/setWebhook?url=https://your-worker.workers.dev/telegram"
    ```
    

## Оптимізації, кешування, обхід обмежень

- **Кешування**: Зберігайте ембедінги та відповіді в D1. Очищайте старі записи:
    
    ```sql
    DELETE FROM cache WHERE created_at < datetime('now', '-7 days');
    ```
    
- **Чанкування**: Розбивайте тексти на фрагменти по 1000 символів.
- **Ротація акаунтів**: LiteLLM автоматично розподіляє запити.

## Безпекові поради

- Не вбудовуйте токени в код — використовуйте секрети Cloudflare.
- Обмежте доступ до Worker’а через [Cloudflare Access](https://developers.cloudflare.com/cloudflare-one/).
- Перевірте права доступу до GitMCP API.

## Заключення з ідеями для розширення

Ця RAG-система дозволяє ефективно працювати з україномовними Markdown-нотатками, використовуючи безкоштовні ресурси Cloudflare. Для розширення можна:

- Додати підтримку інших форматів (PDF, TXT).
- Інтегрувати додаткові джерела даних через n8n.
- Покращити веб-інтерфейс із фільтрами та історією запитів.

Детальніше про Cloudflare Workers AI — у [офіційній документації](https://developers.cloudflare.com/workers-ai/).

### Відповідь

- Дослідження показують, що інтеграція сервісу з n8n та Cloudflare AI є можливою.  
- n8n підтримує протокол MCP, що дозволяє підключатися до GitMCP.  
- Cloudflare AI агенти можуть використовувати зовнішні MCP-сервери, включаючи GitMCP.  

#### Короткий огляд  
Сервіс, описаний на сторінці ([GitMCP](https://gitmcp.io/maxfraieho/exodus)), є віддаленим сервером Model Context Protocol (MCP), який надає доступ до документації та коду GitHub-проєктів для AI-асистентів. n8n має вбудовану підтримку MCP через вузол MCP Client Tool, що дозволяє легко інтегруватися з GitMCP, використовуючи URL-сервера. Cloudflare AI підтримує створення агентів, які можуть підключатися до віддалених MCP-серверів, таких як GitMCP, для доступу до зовнішніх ресурсів. Для публічних репозиторіїв не потрібна додаткова авторизація, що спрощує інтеграцію.

#### Технічні деталі  
- Для n8n інтеграція передбачає використання вузла MCP Client Tool та конфігурацію з URL GitMCP, наприклад, [https://gitmcp.io/maxfraieho/exodus](https://gitmcp.io/maxfraieho/exodus).  
- Для Cloudflare AI агенти можуть бути налаштовані для використання GitMCP як зовнішнього MCP-сервера, забезпечуючи доступ до документації GitHub-проєктів.  

---

### Докладний звіт

Цей звіт надає детальний аналіз можливості інтеграції сервісу, описаного на сторінці [https://gitmcp.io/maxfraieho/exodus](https://gitmcp.io/maxfraieho/exodus), з платформами n8n та Cloudflare AI. Аналіз базується на дослідженні вмісту сторінки, документації та додаткових джерел, доступних станом на 17 квітня 2025 року.

#### Опис сервісу  
Сторінка [https://gitmcp.io/maxfraieho/exodus](https://gitmcp.io/maxfraieho/exodus) стосується проєкту GitMCP, який є безкоштовним, відкритим і віддаленим сервером Model Context Protocol (MCP). GitMCP перетворює будь-який GitHub-проєкт (репозиторії або GitHub Pages) на хаб документації, дозволяючи AI-асистентам отримувати актуальну інформацію про код і документацію, тим самим зменшуючи "галюцинації" коду. Сервіс сумісний з популярними AI-інструментами, такими як Cursor, Claude Desktop, Windsurf, VSCode та Cline, і не потребує складної конфігурації для публічних репозиторіїв.

Таблиця 1. Основна інформація про GitMCP з дослідженої сторінки:  
| Інформація                  | Деталі                                      |  
|-----------------------------|---------------------------------------------|  
| Назва проєкту               | GitMCP                                      |  
| URL MCP-сервера             | https://gitmcp.io/maxfraieho/exodus         |  
| Приклад інтеграції          | Додавання до Cursor через оновлення `~/.cursor/mcp.json` з URL MCP-сервера |  
| Можливості інтеграції       | Підтримує інтеграцію з Cursor за допомогою вказаної JSON-конфігурації |  

GitMCP не згадує явних вимог до авторизації для публічних репозиторіїв, що полегшує доступ для зовнішніх інструментів.

#### Інтеграція з n8n  
n8n є платформою для автоматизації робочих процесів із підтримкою понад 400 інтеграцій, включаючи нативні AI-функції. Дослідження показують, що n8n підтримує протокол MCP через вузли MCP Client Tool та MCP Server Trigger, що дозволяє взаємодіяти з зовнішніми MCP-серверами, такими як GitMCP.  

Зокрема:  
- Вузол MCP Client Tool дозволяє n8n діяти як клієнт MCP, підключаючись до серверів, таких як GitMCP, шляхом надання URL-сервера. Наприклад, для підключення до [https://gitmcp.io/maxfraieho/exodus](https://gitmcp.io/maxfraieho/exodus) користувач може налаштувати цей вузол у робочому процесі n8n.  
- Документація n8n ([n8n MCP Client Tool Documentation](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp/)) підтверджує, що цей вузол підтримує взаємодію з MCP-серверами, забезпечуючи доступ до інструментів і ресурсів.  
- Оскільки GitMCP не потребує авторизації для публічних репозиторіїв, інтеграція з n8n є простий і не потребує додаткових налаштувань авторизації.  

Це дозволяє створювати автоматизовані робочі процеси, які використовують документацію GitHub-проєктів через GitMCP, наприклад, для аналізу коду або генерації звітів.

#### Інтеграція з Cloudflare AI  
Cloudflare AI є набором AI-інструментів і послуг, що включають платформу для створення та розгортання AI-агентів. Дослідження показують, що Cloudflare підтримує протокол MCP, дозволяючи розробникам будувати та розгортати віддалені MCP-сервери, а також використовувати зовнішні MCP-сервери для своїх агентів.  

Ключові моменти:  
- Cloudflare надає документацію ([Cloudflare Model Context Protocol Documentation](https://developers.cloudflare.com/agents/model-context-protocol/)), яка пояснює, що AI-агенти можуть підключатися до віддалених MCP-серверів через Інтернет, використовуючи HTTP і Server-Sent Events (SSE) з авторизацією через OAuth, якщо потрібно.  
- GitMCP, як віддалений MCP-сервер, доступний публічно, і для публічних репозиторіїв не потрібна авторизація, що робить його сумісним з агентами Cloudflare AI.  
- Блог Cloudflare ([Build and deploy Remote Model Context Protocol (MCP) servers to Cloudflare](https://blog.cloudflare.com/remote-model-context-protocol-servers-mcp/)) згадує, що AI-агенти можуть підключатися до зовнішніх MCP-серверів, відкриваючи нові можливості для взаємодії з сервісами, такими як GitMCP.  
- Приклад: агент Cloudflare AI може бути налаштований для використання URL GitMCP, наприклад, [https://gitmcp.io/maxfraieho/exodus](https://gitmcp.io/maxfraieho/exodus), для доступу до документації GitHub-проєкту, що дозволяє виконувати завдання, такі як аналіз коду або відповіді на запити, засновані на контексті.

Таким чином, Cloudflare AI агенти можуть інтегруватися з GitMCP, забезпечуючи доступ до ресурсів GitHub-проєктів у рамках своїх операцій.

#### Висновки та обмеження  
Дослідження підтверджують, що інтеграція GitMCP з n8n і Cloudflare AI є можливою. Для n8n це реалізується через вузол MCP Client Tool, а для Cloudflare AI — через конфігурацію агентів для використання віддалених MCP-серверів. Важливо зазначити, що для приватних репозиторіїв можуть бути потрібні додаткові налаштування авторизації, але для публічних репозиторіїв, як передбачається в запиті, інтеграція є простою і не потребує додаткових кроків.

Таблиця 2. Порівняння можливостей інтеграції:  
| Платформа   | Спосіб інтеграції                          | Вимоги до авторизації для публічних репозиторіїв |  
|-------------|--------------------------------------------|--------------------------------------------------|  
| n8n         | Використання MCP Client Tool з URL GitMCP  | Не потрібна                                      |  
| Cloudflare AI | Налаштування агента для підключення до GitMCP | Не потрібна                                      |  

Цей аналіз базується на доступній документації та джерелах, станом на 17 квітня 2025 року, і враховує, що користувач не вказав конкретних вимог до приватних репозиторіїв.

#### Ключові цитати  
- [GitMCP Official Website, Detailed Project Overview](https://gitmcp.io/)  
- [n8n MCP Client Tool Documentation, Integration Guide](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp/)  
- [Cloudflare Model Context Protocol Documentation, AI Agent Setup](https://developers.cloudflare.com/agents/model-context-protocol/)  
- [Build and deploy Remote Model Context Protocol (MCP) servers to Cloudflare, Blog Post](https://blog.cloudflare.com/remote-model-context-protocol-servers-mcp/)