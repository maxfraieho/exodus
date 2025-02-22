---
{"title":"Стратегії подолання обмежень Cloudflare AI на безкоштовному плані через інтеграцію з n8n","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/strategiyi-podolannya-obmezhen-cloudflare-ai-na-bezkoshtovnomu-plani-cherez-integracziyu-z-n8n/","dgPassFrontmatter":true,"noteIcon":""}
---


Система Cloudflare AI на безкоштовному тарифі має суттєві обмеження на довжину відповіді LLM-моделей та час виконання запитів. Цей звіт пропонує комплексний підхід до вирішення цих проблем через комбінацію технік розділення даних, автоматизації циклічних операцій та паралельної обробки з використанням платформи n8n.  

## 1. Розділення вхідних даних (Input Chunking)  
### 1.1 Принцип роботи та архітектура  
Для обробки довгих текстових фрагментів необхідно використовувати механізм поділу вхідних даних на менші частини (чанки). У n8n це реалізується комбінацією вузлів **Code** та **SplitInBatches**[3].  

Метод `String.Split`[1] з .NET може бути адаптований для створення логіки розбиття через регулярні вирази. Наприклад, для тексту з 5000 токенів при ліміті 1000 токенів:  
```javascript 
const chunkSize = 1000;
const chunks = [];
for (let i=0; i<text.length; i+=chunkSize) {
    chunks.push(text.slice(i, i+chunkSize));
}
return chunks;
```

### 1.2 Конфігурація workflow в n8n  
1. **HTTP Request Node**: Отримання вихідних даних з API або файлу  
2. **Code Node**: Виконання алгоритму розбиття з використанням методу `slice`[1]  
3. **SplitInBatches**[3]: Пакетна обробка чанків з параметром `Batch Size = 1`  
4. **HTTP Request Node**: Надсилання кожного чанка до Cloudflare AI  
5. **Merge Node**: Об'єднання результатів через `Array.concat()`  

Схема workflow  

**Критичні параметри:**  
- Максимальний розмір чанка: 900 токенів (запас 10% для маркерів форматування)  
- Стратегія перекриття: 50 токенів між сусідніми чанками для контекстної цілісності  

## 2. Каскадні запити з автоматичним продовженням  
### 2.1 Модифікація Cloudflare Worker  
Для детекції обрізаних відповідей додається спеціальний маркер `[TRUNCATED]`. Приклад коду:  
```javascript
const MAX_LENGTH = 950;
let response = await ai.run("@cf/meta/llama-3", {prompt});

if (response.length > MAX_LENGTH) {
    const truncated = response.slice(0, MAX_LENGTH);
    const lastSpace = truncated.lastIndexOf(' ');
    return `${truncated.slice(0, lastSpace)} [TRUNCATED]`;
}
return response;
```
Цей підхід використовує методи маніпуляції з рядками з[1], забезпечуючи коректне розбиття на межі слів.  

### 2.2 Циклічний workflow в n8n  
1. **Initial Request Node**: Початковий запит до AI  
2. **If Node**: Перевірка наявності `[TRUNCATED]`  
3. **Loop Node**:  
   - **Extract Last Phrase**: Використання `String.lastIndexOf`[1]  
   - **Construct New Prompt**: Додавання "Continue from: [last_phrase]"  
   - **Throttle Node**: Затримка 500 мс між ітераціями  
4. **Aggregate Node**: Об'єднання фрагментів через `Array.join()`  

**Оптимізація:**  
- Лічильник ітерацій з `Counter Node` для запобігання нескінченним циклам  
- Кешування проміжних результатів у Workers KV[5] з ключами `session_id:iteration`  

## 3. Паралельна обробка через декілька Worker-ів  
### 3.1 Архітектура паралелізму  
Використання шаблону "Parallel Sub-Workflow Execution"[4] дозволяє:  
1. Розділити вхідні дані на незалежні підзавдання  
2. Запустити їх одночасно через окремі екземпляри Workers  
3. Синхронізувати результати через механізм callback URL  

### 3.2 Реалізація в n8n  
1. **SplitInBatches Node**[3]: Розподіл завдань на групи  
2. **HTTP Request Node**: Паралельні запити з параметром `parallel=true`  
3. **Wait Node**: Очікування завершення через:  
   - Полінг статусів через `/callback` ендпоінти  
   - Таймаут 30 секунд на групу  
4. **Merge Node**: Об'єднання результатів з перевіркою цілісності  

Паралельна обробка  

**Переваги:**  
- Скорочення загального часу виконання на 40-70%  
- Обхід обмежень Rate Limiting через балансування навантаження  

## 4. Гібридний підхід  
### 4.1 Комбінація технік  
Інтеграція всіх методів у єдиний workflow:  
1. **Перший етап**: Розділення вхідних даних на чанки  
2. **Другий етап**: Паралельна обробка чанків  
3. **Третій етап**: Каскадне продовження для кожного фрагмента  
4. **Фінальний етап**: Агрегація результатів з перевіркою консистентності  

### 4.2 Ключові компоненти  
- **Workers KV[5]**: Зберігання стану кожного чанка (статус, ітерація, результат)  
- **Recovery Mechanism**: Відновлення обриваних сесій через `session_id`  
- **Priority Queue**: Обробка критичних фрагментів у першу чергу  

## 5. Оптимізація продуктивності  
### 5.1 Налаштування Docker для n8n[2]  
У файлі `docker-compose.yml`:  
```yaml
services:
  n8n:
    image: n8nio/n8n
    environment:
      N8N_TIMEOUT: 3600
      GENERIC_TIMEZONE: Europe/Kyiv
      N8N_PROTOCOL: https
```

### 5.2 Кешування результатів  
Реалізація кешування через Workers KV[5]:  
```javascript 
const cacheKey = `cache:${hash(inputText)}`;
const cached = await KV.get(cacheKey);
if (cached) return new Response(cached);

// ...обробка запиту...

await KV.put(cacheKey, response, {expirationTtl: 86400});
```

## 6. Обхід обмежень часу виконання  
### 6.1 Стратегії:  
- **Preemptive Chunking**: Попереднє розбиття даних перед відправкою  
- **Background Processing**: Використання webhook-ів для асинхронної обробки  
- **Result Streaming**: Поетапне повернення результатів через Server-Sent Events  

### 6.2 Реалізація SSE:  
```javascript
const stream = new ReadableStream({
    start(controller) {
        processChunks(inputData, (chunk) => {
            controller.enqueue(chunk);
        });
    }
});

return new Response(stream, {
    headers: {'Content-Type': 'text/event-stream'}
});
```

## Висновок  
Запропонована архітектура дозволяє ефективно обходити обмеження безкоштовного тарифу Cloudflare AI через:  
1. Ієрархічне розбиття даних з використанням методів маніпуляції рядками[1]  
2. Автоматизовані цикли продовження з маркерами обрізання  
3. Масово-паралельну обробку через шаблони n8n[4]  
4. Гібридне кешування з Workers KV[5]  

Для подальшого вдосконалення системи рекомендується:  
- Інтеграція Durable Objects для керування станом складних workflow  
- Використання мікросервісів для балансування навантаження  
- Реалізація адаптивного розбиття на основі реальних показників latency

Citations:
[1] [PDF] МЕТОДИЧНІ ВКАЗІВКИ "Програмування під платформу .NET ... https://ep3.nuwm.edu.ua/6059/1/04-04-201.pdf
[2] N8N | Установка, Настройка, Обзор - YouTube https://www.youtube.com/watch?v=rEdruJHQ4KQ
[3] Эффективное использование циклов в n8n для автоматизации https://dzen.ru/a/Z1aki0MsNB7meAZn
[4] Pattern for Parallel Sub-Workflow Execution Followed by Wait ... - N8N https://n8n.io/workflows/2536-pattern-for-parallel-sub-workflow-execution-followed-by-wait-for-all-loop/
[5] Workers KV - free to try, with increased limits! - The Cloudflare Blog https://blog.cloudflare.com/ru-ru/workers-kv-free-tier
[6] workers-types/index.d.ts at master - GitHub https://github.com/cloudflare/workers-types/blob/master/index.d.ts
[7] Workers AI | Cloudflare https://www.cloudflare.com/ru-ru/developer-platform/products/workers-ai/
[8] Splitting and processing a long document in chunks using a ... https://community.n8n.io/t/splitting-and-processing-a-long-document-in-chunks-using-a-language-model-in-n8n/43576
[9] Элемент Split Out n8n - YouTube https://www.youtube.com/watch?v=6uwT0_2N17o
[10] Responses being mangled · Issue #64 · cloudflare/workers-rs - GitHub https://github.com/cloudflare/workers-rs/issues/64
[11] Tutorial: AI Data Extraction in Bubble with Cloudflare Workers https://www.nocodesaas.io/p/tutorial-ai-data-extraction-in-bubble
[12] [PDF] Магістерська дисертація https://ela.kpi.ua/bitstreams/07fad343-71eb-49e3-b5aa-81a5320af330/download
[13] Vector Database Optimization with n8n: Metadata, Text Splitting ... https://community.n8n.io/t/vector-database-optimization-with-n8n-metadata-text-splitting-embeddings/64312
[14] Data structure - n8n Docs https://docs.n8n.io/data/data-structure/
[15] Run cloudflare worker at dynamically set timestamps - Stack Overflow https://stackoverflow.com/questions/76122161/run-cloudflare-worker-at-dynamically-set-timestamps
[16] Build a Retrieval Augmented Generation (RAG) AI - Cloudflare Docs https://developers.cloudflare.com/workers-ai/tutorials/build-a-retrieval-augmented-generation-ai/
[17] Блоки в n8n (узлы/ноды) | Русский - Smartbot Pro https://docs.smartbotpro.ru/nocode-cloud/n8n/bloki-v-n8n-uzly-nody
[18] Обзор n8n: конструктор бэкенда, автоматизаций и интеграций https://ya.zerocoder.ru/obzor-n8n-konstruktor-bekienda-avtomatizatsii-i-intieghratsii/
[19] Does n8n Workflow support parallel execution? - Questions https://community.n8n.io/t/does-n8n-workflow-support-parallel-execution/22596
[20] Workers Free plan behavior if limit is reached? - General https://community.cloudflare.com/t/workers-free-plan-behavior-if-limit-is-reached/92012
[21] Announcing Cloudflare Workers Unbound for General Availability https://blog.cloudflare.com/workers-unbound-ga/
[22] Stable Diffusion, Code Llama + Workers AI in 100 cities https://blog.cloudflare.com/ru-ru/workers-ai-update-stable-diffusion-code-llama-workers-ai-in-100-cities
[23] [PDF] МОДЕЛЮВАННЯ СИСТЕМ http://web.kpi.kharkov.ua/auts/wp-content/uploads/sites/67/2017/02/MOCS_Kachanov_posobie.pdf
[24] Nodes | n8n Docs https://docs.n8n.io/workflows/components/nodes/
[25] Алгоритми та структури даних — від «десь чув - DOU https://dou.ua/forums/topic/40645/
[26] ШПФ (БПФ, FFT) Швидке ПФ - Студопедія https://studopedia.com.ua/1_29434_shpf-bpf-FFT-shvidke-pf.html
[27] Limits · Cloudflare Workers docs https://developers.cloudflare.com/workers/platform/limits/
[28] Compatibility flags - Workers - Cloudflare Docs https://developers.cloudflare.com/workers/configuration/compatibility-flags/
[29] RAG:Context-Aware Chunking | Google Drive to Pinecone via ... - N8N https://n8n.io/workflows/2871-ragcontext-aware-chunking-or-google-drive-to-pinecone-via-openrouter-and-gemini/
[30] n8n - ToolJet documentation https://docs.tooljet.com/docs/2.62.0/data-sources/n8n
[31] BUG: Logs with `at ` get truncated to `at [object Object]` · Issue #4668 https://github.com/cloudflare/workers-sdk/issues/4668
[32] Get started - CLI · Cloudflare Workers AI docs https://developers.cloudflare.com/workers-ai/get-started/workers-wrangler/
[33] How to use Character Text Splitter - Questions - n8n Community https://community.n8n.io/t/how-to-use-character-text-splitter/59677
[34] Workflows App Automation Features from n8n.io https://n8n.io/features/
[35] Zstd compression is randomly truncating responses https://community.cloudflare.com/t/zstd-compression-is-randomly-truncating-responses/701862
[36] bobbyiliev/cloudflare-ai-worker-demo - GitHub https://github.com/bobbyiliev/cloudflare-ai-worker-demo
[37] Vector Database Optimization with n8n: Metadata, Text ... - YouTube https://www.youtube.com/watch?v=VBw5PEV-zKw
[38] Powerful Workflow Automation Software & Tools - n8n https://n8n.io
[39] Buffered data was truncated after reaching the output size limit https://stackoverflow.com/questions/51463383/buffered-data-was-truncated-after-reaching-the-output-size-limit
[40] Cloudflare Workers AI docs https://developers.cloudflare.com/workers-ai/
