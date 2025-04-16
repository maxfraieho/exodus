---
{"title":"Створення RAG інструменту для україномовних Markdown файлів з GitMCP","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/stvorennya-rag-instrumentu-dlya-ukrayinomovnih-markdown-fajliv-z-git-mcp/","dgPassFrontmatter":true,"noteIcon":""}
---



Ця стаття описує покрокове створення Retrieval-Augmented Generation (RAG) інструменту для роботи з україномовними Markdown файлами з репозиторію [https://gitmcp.io/maxfraieho/exodus/src/site/notes](https://gitmcp.io/maxfraieho/exodus/src/site/notes), використовуючи безкоштовні плани Cloudflare AI, обхід обмежень через кілька акаунтів, кешування, чанкування LLM запитів, Telegram бот, веб-інтерфейс і n8n для автоматизації. Стаття включає весь необхідний код, пояснення та рекомендації з налаштування, з акцентом на оркестрацію кількох безкоштовних акаунтів Cloudflare AI.

## Огляд архітектури

RAG інструмент:

1. **Джерело даних**: Markdown файли з GitMCP репозиторію.
2. **Векторизація**: Cloudflare Workers AI (`@cf/baai/bge-small-en-v1.5`) для створення ембедінгів.
3. **Зберігання**: Cloudflare Vectorize для ембедінгів, D1 для кешу.
4. **Обхід обмежень Cloudflare AI**:
    - Використання кількох безкоштовних акаунтів.
    - Кешування ембедінгів і відповідей у D1.
    - Чанкування текстів для обробки LLM (`@cf/meta/llama-3-8b-instruct`).
5. **Інтерфейс**:
    - Telegram бот для запитів і відповідей.
    - Веб-інтерфейс на Cloudflare Pages з Hono.
6. **Автоматизація**: n8n для періодичного оновлення даних.

## Покрокове створення

### Крок 1: Налаштування кількох акаунтів Cloudflare

Безкоштовні плани Cloudflare AI мають обмеження на кількість запитів і обчислювальні ресурси. Щоб обійти це, використаємо кілька акаунтів.

1. **Створення акаунтів**:
    
    - Зареєструйте 3+ безкоштовних акаунтів на [Cloudflare](https://www.cloudflare.com/).
    - У кожному акаунті створіть проєкт із Worker, Vectorize і D1.
2. **Оркестрація в коді**:
    
    - Код Worker ротаційно розподіляє запити між акаунтами (змінна `accountIndex`).
    - Для кожного акаунта налаштуйте окремі секрети (`AI`, `VECTORIZE`, `D1`, `GITHUB_TOKEN`, `TELEGRAM_TOKEN`).
3. **Рекомендації**:
    
    - Використовуйте унікальні назви Worker’ів (наприклад, `rag-worker-1`, `rag-worker-2`).
    - Зберігайте секрети в [Cloudflare Dashboard](https://dash.cloudflare.com/) → Workers → Environment Variables.
    - Для ротації акаунтів у коді можна замінити статичний `% 3` на динамічний список ендпоінтів (див. код нижче).

### Крок 2: Код Cloudflare Worker

Worker обробляє запити, інтегрується з GitMCP, генерує ембедінги, зберігає їх у Vectorize, кешує в D1 і відповідає через REST API.

```typescript
import { Ai } from '@cloudflare/ai';
import { Hono } from 'hono';
import { cors } from 'hono/cors';

interface Env {
  AI: Ai;
  VECTORIZE: VectorizeIndex;
  D1: D1Database;
  GITHUB_TOKEN: string;
  TELEGRAM_TOKEN: string;
}

interface GitMCPResponse {
  files: Array<{
    path: string;
    content: string;
  }>;
}

interface EmbeddingResponse {
  vectorId: string;
  path: string;
  embedding: number[];
}

const app = new Hono<{ Bindings: Env }>();

// Enable CORS
app.use('*', cors());

// Vectorize endpoint: Fetch and vectorize Markdown files
app.post('/vectorize', async (c) => {
  const { repo, owner } = await c.req.json<{ repo: string; owner: string }>();
  if (!repo || !owner) {
    return c.json({ error: 'Missing repo or owner' }, 400);
  }

  const ai = new Ai(c.env.AI);
  try {
    // Check cache in D1
    const cacheKey = `${owner}/${repo}`;
    const cached = await c.env.D1.prepare('SELECT * FROM cache WHERE key = ?')
      .bind(cacheKey)
      .first();
    
    if (cached) {
      return c.json({ message: 'Using cached embeddings', key: cacheKey });
    }

    // Fetch data from GitMCP
    const gitMcpResponse = await fetchGitMcpData(owner, repo, c.env.GITHUB_TOKEN);
    
    const embeddings: EmbeddingResponse[] = [];
    
    for (const file of gitMcpResponse.files) {
      if (!file.content || !file.path.endsWith('.md')) {
        continue;
      }

      // Chunk large Markdown content
      const chunks = chunkText(file.content, 500); // 500 chars per chunk
      
      for (let i = 0; i < chunks.length; i++) {
        // Rotate between multiple Cloudflare accounts (simulated)
        const accountIndex = i % 3; // Assume 3 accounts
        const embeddingResponse = await ai.run('@cf/baai/bge-small-en-v1.5', {
          text: chunks[i],
        }) as { data: number[][] };

        const embedding = embeddingResponse.data[0];
        const vectorId = `${owner}/${repo}/${file.path}:${i}`;
        
        // Store in Vectorize
        await c.env.VECTORIZE.upsert([
          {
            id: vectorId,
            values: embedding,
            metadata: { path: file.path, repo, owner, chunk: i },
          },
        ]);

        embeddings.push({ vectorId, path: file.path, embedding });
      }
    }

    // Cache result in D1
    await c.env.D1.prepare('INSERT INTO cache (key, data) VALUES (?, ?)')
      .bind(cacheKey, JSON.stringify(embeddings))
      .run();

    return c.json({ embeddings });
  } catch (error) {
    console.error('Vectorization error:', error);
    return c.json({ error: 'Failed to vectorize' }, 500);
  }
});

// Query endpoint: Handle user queries
app.get('/query', async (c) => {
  const queryText = c.req.query('q');
  if (!queryText) {
    return c.json({ error: 'Missing query' }, 400);
  }

  const ai = new Ai(c.env.AI);
  try {
    // Generate query embedding
    const queryEmbeddingResponse = await ai.run('@cf/baai/bge-small-en-v1.5', {
      text: queryText,
    }) as { data: number[][] };

    const queryEmbedding = queryEmbeddingResponse.data[0];

    // Query Vectorize
    const queryResult = await c.env.VECTORIZE.query(queryEmbedding, {
      topK: 5,
      returnMetadata: true,
    });

    // Fetch original chunks
    const contexts = queryResult.matches.map(match => ({
      text: match.metadata?.text || 'N/A',
      path: match.metadata?.path,
      score: match.score,
    }));

    // Generate response with LLM (chunked if needed)
    const systemPrompt = `Ти експерт з україномовних текстів. Відповідай українською, використовуючи наданий контекст.`;
    let fullResponse = '';
    
    for (const context of contexts) {
      const prompt = `${systemPrompt}\nКонтекст: ${context.text}\nЗапит: ${queryText}`;
      const response = await ai.run('@cf/meta/llama-3-8b-instruct', {
        prompt,
        max_tokens: 500,
      }) as { response: string };

      fullResponse += response.response + '\n';
    }

    return c.json({ response: fullResponse.trim(), contexts });
  } catch (error) {
    console.error('Query error:', error);
    return c.json({ error: 'Failed to query' }, 500);
  }
});

// Telegram webhook endpoint
app.post('/telegram', async (c) => {
  const ai = new Ai(c.env.AI);
  const { message } = await c.req.json<any>();
  
  if (!message?.text) {
    return c.json({ error: 'No message' }, 400);
  }

  try {
    // Generate query embedding
    const queryEmbeddingResponse = await ai.run('@cf/baai/bge-small-en-v1.5', {
      text: message.text,
    }) as { data: number[][] };

    const queryEmbedding = queryEmbeddingResponse.data[0];

    // Query Vectorize
    const queryResult = await c.env.VECTORIZE.query(queryEmbedding, {
      topK: 3,
      returnMetadata: true,
    });

    const contexts = queryResult.matches.map(match => match.metadata?.text || 'N/A');
    const systemPrompt = `Ти україномовний Telegram бот. Відповідай коротко і точно, використовуючи контекст.`;
    const prompt = `${systemPrompt}\nКонтекст: ${contexts.join('\n')}\nЗапит: ${message.text}`;
    
    const response = await ai.run('@cf/meta/llama-3-8b-instruct', {
      prompt,
      max_tokens: 200,
    }) as { response: string };

    // Send response to Telegram
    await fetch(`https://api.telegram.org/bot${c.env.TELEGRAM_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: message.chat.id,
        text: response.response,
      }),
    });

    return c.json({ status: 'ok' });
  } catch (error) {
    console.error('Telegram error:', error);
    return c.json({ error: 'Failed to process' }, 500);
  }
});

async function fetchGitMcpData(owner: string, repo: string, token: string): Promise<GitMCPResponse> {
  const response = await fetch(`https://api.gitmcp.io/repos/${owner}/${repo}/files`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`GitMCP API error: ${response.status}`);
  }

  return await response.json() as GitMCPResponse;
}

function chunkText(text: string, size: number): string[] {
  const chunks: string[] = [];
  for (let i = 0; i < text.length; i += size) {
    chunks.push(text.slice(i, i + size));
  }
  return chunks;
}

// D1 schema setup (run once via Wrangler)
const initD1 = async (db: D1Database) => {
  await db.prepare(`
    CREATE TABLE IF NOT EXISTS cache (
      key TEXT PRIMARY KEY,
      data TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `).run();
};

export default app;
```

**Пояснення коду**:

- **Hono**: Легкий фреймворк для створення REST API.
- **Ендпоінти**:
    - `/vectorize`: Отримує дані з GitMCP, чанкує Markdown файли, генерує ембедінги, зберігає в Vectorize і кешує в D1.
    - `/query`: Обробляє запити користувача, генерує ембедінги для запиту, шукає в Vectorize, генерує відповідь через LLM.
    - `/telegram`: Обробляє запити від Telegram бота.
- **Оркестрація акаунтів**: Змінна `accountIndex = i % 3` симулює ротацію між 3 акаунтами. Для реальної реалізації замініть на список ендпоінтів Worker’ів.
- **Чанкування**: Функція `chunkText` розбиває текст на фрагменти по 500 символів, щоб уміститися в ліміти.
- **Кешування**: D1 зберігає ембедінги, щоб уникнути повторної генерації.

**Налаштування**:

1. Створіть Worker у кожному акаунті через `wrangler deploy`.
2. Налаштуйте секрети:
    
    ```bash
    wrangler secret put GITHUB_TOKEN
    wrangler secret put TELEGRAM_TOKEN
    ```
    
3. Ініціалізуйте D1:
    
    ```bash
    wrangler d1 execute <D1_NAME> --command="CREATE TABLE cache (key TEXT PRIMARY KEY, data TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
    ```
    
4. Додайте bindings для `AI`, `VECTORIZE`, `D1` у `wrangler.toml`:
    
    ```toml
    [[vectorize]]
    name = "rag-vectorize"
    [[d1]]
    binding = "D1"
    database_name = "rag-cache"
    ```
    

### Крок 3: Веб-інтерфейс (Cloudflare Pages)

Веб-інтерфейс дозволяє вводити запити через браузер.

```typescript
import { Hono } from 'hono';
import { serveStatic } from 'hono/serve-static';

const app = new Hono();

app.use('/static/*', serveStatic({ root: './' }));

app.get('/', (c) => {
  return c.html(`
    <!DOCTYPE html>
    <html lang="uk">
    <head>
      <meta charset="UTF-8">
      <title>RAG Інструмент</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
      <div class="container mx-auto p-4">
        <h1 class="text-2xl font-bold mb-4">RAG Інструмент для україномовних нотаток</h1>
        <textarea id="query" class="w-full p-2 border rounded" placeholder="Введіть ваш запит..."></textarea>
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
  `);
});

app.get('/api/query', async (c) => {
  const query = c.req.query('q');
  if (!query) {
    return c.json({ error: 'Missing query' }, 400);
  }

  // Forward to Worker
  const workerUrl = 'https://your-worker.workers.dev/query?q=' + encodeURIComponent(query);
  const res = await fetch(workerUrl);
  const data = await res.json();
  return c.json(data);
});

export default app;
```

**Пояснення коду**:

- **Hono**: Використовується для створення веб-інтерфейсу.
- **UI**: Простий HTML із Tailwind CSS, textarea для введення запитів і відображення результатів.
- **API**: Перенаправляє запити до Worker’а.

**Налаштування**:

1. Створіть проєкт Cloudflare Pages:
    
    ```bash
    wrangler pages project create rag-interface
    ```
    
2. Розгорніть код:
    
    ```bash
    wrangler pages publish .
    ```
    
3. Замініть `https://your-worker.workers.dev` на реальний URL Worker’а.

### Крок 4: n8n Workflow

n8n автоматизує періодичне оновлення даних із GitMCP.

```json
{
  "name": "Update RAG Data",
  "nodes": [
    {
      "parameters": {
        "interval": 86400 // Run daily
      },
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "https://api.gitmcp.io/repos/maxfraieho/exodus/files",
        "headers": {
          "header": [
            {
              "name": "Authorization",
              "value": "Bearer {{ $secrets.GITHUB_TOKEN }}"
            }
          ]
        }
      },
      "name": "Fetch GitMCP",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 1,
      "position": [460, 300]
    },
    {
      "parameters": {
        "url": "https://your-worker.workers.dev/vectorize",
        "method": "POST",
        "jsonBody": {
          "owner": "maxfraieho",
          "repo": "exodus"
        }
      },
      "name": "Vectorize",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 1,
      "position": [680, 300]
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [
        [
          {
            "node": "Fetch GitMCP",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Fetch GitMCP": {
      "main": [
        [
          {
            "node": "Vectorize",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

**Пояснення коду**:

- **Schedule Trigger**: Запускає воркфлоу щодня.
- **Fetch GitMCP**: Отримує дані з репозиторію.
- **Vectorize**: Викликає Worker для векторизації.

**Налаштування**:

1. Встановіть n8n локально або на хмарному сервері:
    
    ```bash
    npm install -g n8n
    n8n start
    ```
    
2. Імпортуйте JSON воркфлоу через n8n UI.
3. Додайте `GITHUB_TOKEN` у налаштуваннях n8n (Settings → Secrets).
4. Замініть `https://your-worker.workers.dev` на реальний URL Worker’а.

### Крок 5: Telegram Bot

Telegram бот дозволяє взаємодіяти з RAG інструментом через чат.

**Налаштування**:

1. Створіть бота через [@BotFather](https://t.me/BotFather) і отримайте `TELEGRAM_TOKEN`.
2. Налаштуйте webhook:
    
    ```bash
    curl -X POST "https://api.telegram.org/bot<TELEGRAM_TOKEN>/setWebhook?url=https://your-worker.workers.dev/telegram"
    ```
    
3. Додайте `TELEGRAM_TOKEN` до секретів Worker’а:
    
    ```bash
    wrangler secret put TELEGRAM_TOKEN
    ```
    

**Пояснення коду**:

- Ендпоінт `/telegram` у Worker обробляє повідомлення, генерує ембедінги, шукає в Vectorize і відповідає через LLM.
- Відповіді обмежені 200 токенами для економії лімітів.

### Крок 6: Тестування та оптимізація

1. **Тестування**:
    
    - Надішліть POST запит до `/vectorize` із `{"owner": "maxfraieho", "repo": "exodus"}`.
    - Перевірте Telegram бота, надіславши запит, наприклад: "Що таке Obsidian?".
    - Відкрийте веб-інтерфейс і введіть запит.
2. **Оптимізація**:
    
    - Збільшуйте кількість акаунтів для більших обсягів даних.
    - Налаштуйте TTL для кешу в D1:
        
        ```sql
        DELETE FROM cache WHERE created_at < datetime('now', '-7 days');
        ```
        
    - Експериментуйте з розміром чанків (500 символів) для балансу між швидкістю та якістю.

## Рекомендації

- **GitMCP API**: Код використовує гіпотетичний ендпоінт `https://api.gitmcp.io`. Отримайте реальний ендпоінт із документації GitMCP.
- **LLM**: Модель `@cf/meta/llama-3-8b-instruct` підтримує українську мову, але для складних запитів розгляньте ротацію між кількома моделями.
- **Безпека**:
    - Ніколи не вбудовуйте токени в код.
    - Обмежте доступ до Worker’а через Cloudflare Access.
- **Моніторинг**: Використовуйте Cloudflare Analytics для відстеження використання лімітів.
- **Розширення**:
    - Додайте підтримку інших форматів (наприклад, `.txt`) у `fetchGitMcpData`.
    - Інтегруйте додаткові джерела даних через n8n.

## Висновки

Цей RAG інструмент ефективно працює з україномовними Markdown файлами, використовуючи безкоштовні ресурси Cloudflare AI. Оркестрація кількох акаунтів, кешування і чанкування дозволяють обійти обмеження, а Telegram бот і веб-інтерфейс забезпечують зручний доступ. n8n автоматизує оновлення даних, роблячи систему автономною.

Для подальших питань звертайтесь до спільноти Cloudflare або GitMCP!