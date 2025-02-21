---
{"title":"Впровадження та оптимізації Cloudflare AI Gateway","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/vprovadzhennya-ta-optimizacziyi-cloudflare-ai-gateway/","dgPassFrontmatter":true,"noteIcon":""}
---

Ось оновлений текст з покращеним форматуванням Markdown та оновленими внутрішніми посиланнями:

---

### Зміст

- [Основна конфігурація та розгортання](#osnovna-konfiguratsiya-ta-rozgortannya)
  - [Налаштування проекту](#nalashtuvannya-proektu)
  - [Встановлення залежностей](#vstanovlennya-zalezhnostey)
  - [Структура проекту](#struktura-proektu)
  - [Реалізація основних компонентів](#realizatsiya-osnovnykh-komponentiv)
- [Оптимізації та покращення](#optymizatsiyi-ta-pokrashchennya)
  - [Кешування та продуктивність](#keshuvannya-ta-produktyvnist)
  - [Масштабування](#masshtabuvannya)
- [Інтеграція з n8n](#intehratsiya-z-n8n)
  - [Базова конфігурація HTTP-запиту](#bazova-konfihuratsiya-http-zapytu)
  - [Оптимізація моделей](#optymizatsiya-modeley)
  - [Обробка помилок](#obrobka-pomylok)
- [Безпека та моніторинг](#bezpeka-ta-monitorynh)
  - [Налаштування безпеки](#nalashtuvannya-bezpeky)
  - [Моніторинг продуктивності](#monitorynh-produktyvnosti)
- [Тестування та розгортання](#testuvannya-ta-rozgortannya)
  - [Налаштування тестів](#nalashtuvannya-testiv)
  - [CI/CD налаштування](#cicd-nalashtuvannya)
  - [Розгортання](#rozgortannya)

[Решта вашого контенту залишається без змін...]

---

### Основна конфігурація та розгортання

#### Налаштування проекту

1. Створіть нову директорію проекту:

   ```bash
   mkdir cloudflare-ai-gateway
   cd cloudflare-ai-gateway
   ```

2. Створіть та налаштуйте `wrangler.toml`:

   ```toml
   name = "cloudflare-ai-gateway"
   main = "src/worker.js"
   compatibility_date = "2024-05-01"

   [ai]
   binding = "AI"
   analytics = true

   [vars]
   MODEL_CONFIG = """
   {
     "models": {
       "mistral": {
         "id": "@cf/mistral/mistral-7b-instruct-v0.1",
         "prompt_wrapper": "<|{role}|>{content}</s>",
         "max_tokens": 4096
       },
       "codellama": {
         "id": "@cf/meta/llama-2-7b-code-instruct-int8",
         "prompt_wrapper": "[INST] {content} [/INST]",
         "max_tokens": 2048
       },
       "llama13b": {
         "id": "@cf/meta/llama-2-13b-chat-int8",
         "prompt_wrapper": "[INST] {content} [/INST]",
         "max_tokens": 3072
       }
     }
   }
   """
   ```

#### Встановлення залежностей

```bash
npm init -y
npm install @cloudflare/workers @cloudflare/ai honojs wrangler
```

#### Структура проекту

Створіть наступну структуру директорій:

```
cloudflare-ai-gateway/
├── src/
│   ├── worker.js
│   ├── prompt-engine.js
│   ├── scaler.js
│   └── middleware/
│       └── security.js
├── test/
│   └── worker.test.js
└── wrangler.toml
```

#### Реалізація основних компонентів

##### Файл: `src/prompt-engine.js`

```javascript
export class PromptEngine {
  constructor(config) {
    this.templates = new Map();
    this.modelConfig = new Map();

    for (const [name, cfg] of Object.entries(config)) {
      this.templates.set(name, this.createTemplate(cfg.prompt_wrapper));
      this.modelConfig.set(name, cfg);
    }
  }

  createTemplate(wrapper) {
    const roles = {
      system: 'system',
      user: 'user',
      assistant: 'assistant'
    };

    return (messages) => {
      return messages.map(msg => {
        const role = roles[msg.role] || 'user';
        const content = msg.content
          .replace(/\n/g, '\\n')
          .replace(/"/g, '\\"');

        return wrapper
          .replace('{role}', role)
          .replace('{content}', content);
      }).join('\n');
    };
  }

  getTemplate(modelName) {
    return this.templates.get(modelName);
  }

  getConfig(modelName) {
    return this.modelConfig.get(modelName) || null;
  }

  validateTokenCount(prompt, modelName) {
    const maxTokens = this.modelConfig.get(modelName)?.max_tokens || 2048;
    const tokenCount = Math.ceil(prompt.length / 4);
    return tokenCount <= maxTokens;
  }
}
```

##### Файл: `src/worker.js`

```javascript
import { PromptEngine } from './prompt-engine.js';
import { securityMiddleware } from './middleware/security.js';

const ERROR_RESPONSE = (message, status = 400) =>
  new Response(JSON.stringify({ error: message }), {
    status,
    headers: { 'Content-Type': 'application/json' }
  });

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return handleCors();
    }

    const securityCheck = await securityMiddleware(request);
    if (securityCheck) return securityCheck;

    try {
      const { model, messages, stream = false, ...params } = await request.json();

      if (!model || !messages) {
        return ERROR_RESPONSE('Missing required fields: model or messages');
      }

      const config = JSON.parse(env.MODEL_CONFIG);
      const engine = new PromptEngine(config.models);

      if (!config.models[model]) {
        return ERROR_RESPONSE(`Model ${model} not supported`, 404);
      }

      const prompt = engine.getTemplate(model)(messages);

      if (!engine.validateTokenCount(prompt, model)) {
        return ERROR_RESPONSE('Prompt exceeds maximum token limit');
      }

      const aiResponse = await env.AI.run(
        config.models[model].id,
        {
          prompt,
          ...params,
          gateway: {
            cacheTtl: 3600,
            retries: 3,
            loadBalancer: 'round-robin'
          }
        }
      );

      const response = new Response(JSON.stringify({
        model: model,
        response: aiResponse.response,
        tokens: aiResponse.tokens_used,
        latency: aiResponse.latency
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': `public, max-age=${3600}`
        }
      });

      await logAnalytics(request, response, model, env);
      return handleCache(request, response);

    } catch (error) {
      console.error(`Error: ${error.message}`);
      return ERROR_RESPONSE(error.message, 500);
    }
  }
}

function handleCors() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}

const CACHE = caches.default;

async function handleCache(request, response) {
  const cacheKey = new Request(request.url, {
    headers: request.headers,
    body: await request.clone().text()
  });

  await CACHE.put(cacheKey, response.clone());
  return response;
}

async function logAnalytics(request, response, model, env) {
  const analyticsData = {
    timestamp: new Date().toISOString(),
    model: model,
    ip: request.headers.get('CF-Connecting-IP'),
    userAgent: request.headers.get('User-Agent'),
    responseStatus: response.status,
    tokensUsed: response.body?.tokens || 0
  };

  await fetch('https://api.cloudflare.com/client/v4/analytics/engine', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.CLOUDFLARE_API_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(analyticsData)
  });
}
```

##### Файл: `src/scaler.js`

```javascript
export class ModelScaler {
  constructor(env) {
    this.env = env;
    this.modelUsage = new Map();
    this.scalingThreshold = 100;
  }

  async checkScaling(model) {
    const usage = this.modelUsage.get(model) || 0;
    if (usage > this.scalingThreshold) {
      await this.scaleModel(model);
    }
  }

  async scaleModel(model) {
    await fetch(`https://api.cloudflare.com/workers/scale/${model}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${this.env.API_TOKEN}` }
    });
  }
}
```

---

### Оптимізації та покращення

#### Кешування та продуктивність

Створіть файл `src/cache-strategies.js`:

```javascript
const CACHE_STRATEGIES = {
  'default': {
    ttl: 3600,
    varyBy: ['model', 'prompt']
  },
  'codellama': {
    ttl: 7200,
    varyBy: ['prompt']
  }
};

export function getCacheStrategy(model) {
  return CACHE_STRATEGIES[model] || CACHE_STRATEGIES.default;
}
```

#### Масштабування

Модуль масштабування знаходиться у файлі `src/scaler.js` і оновлено, як показано вище.

---

### Інтеграція з n8n

#### Базова конфігурація HTTP-запиту

Налаштуйте вузол HTTP Request в n8n:

```json
{
  "method": "POST",
  "url": "https://your-gateway.example/completion",
  "headers": {
    "Content-Type": "application/json",
    "X-API-Key": "={{$secrets.CLOUDFLARE_API_KEY}}"
  },
  "body": {
    "model": "mistral",
    "messages": [
      {"role": "user", "content": "Hello"}
    ],
    "temperature": 0.7
  }
}
```

#### Оптимізація моделей

#### Обробка помилок

```javascript
try {
  await $node["Cloudflare AI"].execute();
} catch (error) {
  if (error.code === 429) {
    const delay = Math.min(2 ** attempt * 1000, 30000);
    await new Promise(resolve => setTimeout(resolve, delay));
    await $node["Cloudflare AI"].execute();
  } else {
    await $node["Backup Model"].execute();
  }
}
```

---

### Безпека та моніторинг

#### Налаштування безпеки

Створіть файл `src/middleware/security.js`:

```javascript
export async function securityMiddleware(request) {
  const limiter = new RateLimiter({
    tokensPerInterval: 100,
    interval: "minute"
  });

  const ip = request.headers.get('CF-Connecting-IP');
  if (!await limiter.limit(ip)) {
    return new Response('Too Many Requests', { status: 429 });
  }

  const body = await request.clone().text();
  if (/[\|]/gi.test(body)) {
    return new Response('Invalid characters detected', { status: 400 });
  }

  return null;
}
```

#### Моніторинг продуктивності

---

### Тестування та розгортання

#### Налаштування тестів

Створіть файл `test/worker.test.js`:

```javascript
import { worker } from '../src/worker.js';
import { MockAgent } from 'undici';

describe('AI Gateway Worker', () => {
  const modelConfig = {
    models: {
      mistral: {
        id: '@cf/mistral/test-model',
        prompt_wrapper: '<|{role}|>{content}</s>'
      }
    }
  };

  beforeEach(() => {
    process.env.MODEL_CONFIG = JSON.stringify(modelConfig);
  });

  test('should process valid request', async () => {
    const env = {
      MODEL_CONFIG: JSON.stringify(modelConfig),
      AI: {
        run: async (id, params) => ({
          response: "Test response",
          tokens_used: 42,
          latency: 150
        })
      },
      CLOUDFLARE_API_TOKEN: "dummy-token"
    };

    const response = await worker.fetch(new Request('http://localhost', {
      method: 'POST',
      body: JSON.stringify({
        model: 'mistral',
        messages: [{ role: 'user', content: 'Hello' }]
      })
    }), env);

    expect(response.status).toBe(200);
    expect(await response.json()).toHaveProperty('response');
  });
});
```

#### CI/CD налаштування

Створіть файл `.github/workflows/deploy.yml`:

```yaml
name: Deploy Worker

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18
      - name: Install dependencies
        run: npm install
      - name: Publish Worker
        uses: cloudflare/wrangler-action@3.0.0
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          command: publish
```

#### Розгортання

1. Налаштуйте секрети:

   ```bash
   wrangler secret put CLOUDFLARE_API_TOKEN
   ```

2. Запустіть локальний сервер для тестування:

   ```bash
   wrangler dev --remote
   ```

3. Розгорніть на продакшен:

   ```bash
   wrangler deploy
   ```

4. Перевірте роботу:

   ```bash
   curl -X POST https://your-worker.url/ \
     -H "Content-Type: application/json" \
     -d '{"model": "mistral", "messages": [{"role": "user", "content": "Hello"}]}'
   ```
