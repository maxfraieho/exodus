---
{"title":"Використання n8n для створення RAG-систем","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/vikoristannya-n8n-dlya-stvorennya-rag-sistem/","dgPassFrontmatter":true,"noteIcon":""}
---



## Вступ

Системи Retrieval-Augmented Generation (RAG) поєднують точність пошуку даних зі здатністю генерації відповідей великих мовних моделей (LLM). Одним із зручних low-code інструментів для автоматизації створення таких систем є платформа n8n.

У цьому матеріалі розглядаються доступні open-source компоненти та проєкти, які можна використовувати як основу для створення власної RAG-системи на базі n8n із інтеграцією векторних баз даних, API мовних моделей та сховищ документів.

## Компоненти для створення RAG із використанням n8n

### 1. n8n-nodes-openrouter

**Опис**: Community-нода, що дозволяє інтегрувати OpenRouter API для взаємодії з різними LLM через єдиний інтерфейс.

**Посилання**: [GitHub — MatthewSabia1/n8n-nodes-openrouter](https://github.com/MatthewSabia1/n8n-nodes-openrouter)

**Ключові технології**: n8n, OpenRouter API

**Приклад workflow**: Відсутній у документації

**Інтеграція**:
- LLM: ✅ OpenRouter
- MinIO/S3: ❌
- Cloudflare AI: ❌

Ця нода підходить для побудови гнучких RAG-систем, дозволяючи легко змінювати моделі через OpenRouter.

### 2. Chat with GitHub API Documentation: RAG-Powered Chatbot

**Опис**: Готовий шаблон workflow для створення RAG-чатбота, який взаємодіє з документацією GitHub API.

**Посилання**: [n8n.io workflow](https://n8n.io)

**Ключові технології**: n8n, Pinecone (векторна БД), OpenAI (gpt-4o-mini)

**Приклад workflow**: ✅ (готовий шаблон)

**Інтеграція**:
- LLM: ✅ OpenAI
- MinIO/S3: ❌ (замість цього Pinecone)
- Cloudflare AI: ❌

Шаблон легко адаптувати для інших задач, що вимагають RAG із використанням векторної БД Pinecone.

### 3. Retrieval-Augmented Generation з n8n, PostgreSQL та Supabase

**Опис**: Покроковий посібник зі створення production-ready RAG агента на базі n8n з використанням Supabase як векторного сховища.

**Посилання**: [Geeky Gadgets](https://www.geekygadgets.com)

**Ключові технології**: n8n, PostgreSQL (Supabase), OpenAI

**Приклад workflow**: ✅ (згадується в гайді)

**Інтеграція**:
- LLM: ✅ OpenAI
- MinIO/S3: ❌ PostgreSQL/Supabase
- Cloudflare AI: ❌

Підходить для швидкого розгортання якісної системи з векторним пошуком.

### 4. OpenRouter для старих версій n8n (<1.78)

**Опис**: Шаблон для інтеграції OpenRouter у старіших версіях n8n через ноду OpenAI.

**Посилання**: [n8n.io workflow](https://n8n.io)

**Ключові технології**: n8n, OpenRouter, OpenAI API

**Приклад workflow**: ✅ (демонстраційний шаблон)

**Інтеграція**:
- LLM: ✅ OpenRouter через OpenAI node
- MinIO/S3: ❌
- Cloudflare AI: ❌ (опосередковано через OpenRouter можливо)

Рекомендовано для ситуацій, коли потрібно підтримувати сумісність із застарілими версіями n8n.

### 5. Інтеграція n8n з S3-сумісними сховищами (MinIO)

**Опис**: Документація щодо налаштування інтеграції n8n зі сховищами, сумісними з S3 (наприклад, MinIO).

**Посилання**: [n8n.io — S3 integration](https://n8n.io)

**Ключові технології**: n8n, S3-сумісні сховища (MinIO)

**Приклад workflow**: ❌ (описана лише інтеграція)

**Інтеграція**:
- LLM: ❌
- MinIO/S3: ✅ повна підтримка
- Cloudflare AI: ❌

Ідеальний компонент для RAG, що потребує надійного зберігання документів на self-hosted сховищі MinIO.

## Готові open-source рішення для RAG на базі n8n

### 1. Self-Hosted AI Starter Kit (від команди n8n)

**Опис**: Офіційний open-source шаблон від n8n для швидкого розгортання локального AI-середовища з підтримкою RAG. Система базується на Docker Compose та включає Ollama (для локальних моделей типу Llama-2), векторну БД Qdrant та PostgreSQL.

**Посилання**: [n8n-io/self-hosted-ai-starter-kit](https://github.com/n8n-io/self-hosted-ai-starter-kit)

**Ключові технології**: n8n, Ollama, Qdrant, PostgreSQL

**Приклад workflow**: ✅ (готові шаблони workflow)

**Інтеграції**:
- LLM: ✅ Ollama (локально); можлива інтеграція OpenRouter
- MinIO/S3: ❌ (зберігання документів у Qdrant/Postgres)
- Cloudflare AI: ❌ (можливо налаштувати вручну)

Рішення підходить для повністю self-hosted сценаріїв з низькими витратами.

### 2. Knowledge Base API (n8n RAG Sample)

**Опис**: Приклад повної реалізації RAG-системи за допомогою n8n з REST API, який дозволяє завантажувати документи, створювати ембеддинги, зберігати їх у PostgreSQL + PGVector та MinIO (self-hosted S3) і взаємодіяти через OpenAI API.

**Посилання**: [je4ngomes/knowledge-base-api](https://github.com/je4ngomes/knowledge-base-api)

**Ключові технології**: n8n, MinIO, PostgreSQL + PGVector, OpenAI

**Приклад workflow**: ✅ (workflow JSON та архітектура)

**Інтеграції**:
- LLM: ✅ OpenAI API
- MinIO/S3: ✅ MinIO
- Cloudflare AI: ❌ (можлива заміна на OpenRouter API)

Готовий до запуску приклад, який максимально відповідає критеріям інтеграції MinIO як сховища документів.

### 3. AI-Powered RAG Agent (Google Drive + Supabase)

**Опис**: Просунутий RAG-чатбот з веб-інтерфейсом, автоматизованим через n8n. Документи синхронізуються з Google Drive, векторні вбудовування зберігаються в Supabase (pgvector), а відповіді генеруються через OpenAI API.

**Посилання**: [josematosworks/n8n-ai-powered-rag-agent](https://github.com/josematosworks/n8n-ai-powered-rag-agent)

**Ключові технології**: n8n, Supabase (pgvector), Google Drive, OpenAI

**Приклад workflow**: ✅ (описано в документації)

**Інтеграції**:
- LLM: ✅ OpenAI API
- MinIO/S3: ❌ (використовує Google Drive та Supabase)
- Cloudflare AI: ❌ (можлива інтеграція OpenRouter)

Ідеально підійде тим, хто використовує Supabase для векторних сховищ.

### 4. Logos IFT RAG Chatbot

**Опис**: RAG-чатбот від Institute of Free Technology на базі n8n з використанням open-source веб-сервера для LLM (Open-WebUI) та моделей Anthropic Claude через зовнішній API. Векторні дані інтегруються з різних джерел.

**Посилання**: [logos-co/logos-rag](https://github.com/logos-co/logos-rag)

**Ключові технології**: n8n, Open-WebUI, Anthropic Claude, векторні БД (імовірно Qdrant або Chroma)

**Приклад workflow**: 🔄 (у процесі публікації)

**Інтеграції**:
- LLM: ✅ Claude API (через OpenRouter можливі альтернативи)
- MinIO/S3: ❌ (не зазначено)
- Cloudflare AI: ❌ (не зазначено)

Підходить для внутрішнього використання з акцентом на приватність і локальні ресурси.

### 5. Ultimate Agentic RAG AI Template (oTTomator)

**Опис**: Комплексний шаблон workflow для побудови інтелектуальних RAG-агентів в n8n, які здатні динамічно вибирати спосіб отримання інформації (векторний пошук, SQL-запити, отримання документів).

**Посилання**: [coleam00/ottomator-agents – n8n-agentic-rag-agent](https://github.com/coleam00/ottomator-agents)

**Ключові технології**: n8n, Supabase (pgvector), Google Drive, OpenAI API (з можливістю заміни на OpenRouter)

**Приклад workflow**: ✅ (повний шаблон JSON)

**Інтеграції**:
- LLM: ✅ OpenAI API (можливість OpenRouter/HuggingFace)
- MinIO/S3: ❌ (використовується Google Drive)
- Cloudflare AI: ❌ (не зазначено)

Рекомендується для створення агентських RAG-систем з мінімальними витратами та високою гнучкістю.

## Висновки та рекомендації

Жоден із наявних проєктів не покриває абсолютно всі критерії одразу. Проте, комбінуючи ці open-source шаблони з описаними вище компонентами, можна швидко створити власну ефективну RAG-систему, що відповідає конкретним потребам і наявним ресурсам.

### Рекомендований набір компонентів:

1. **Knowledge Base API** як базова архітектура (найкраща інтеграція з MinIO)
2. **n8n-nodes-openrouter** для доступу до різних LLM через єдиний API
3. **Self-Hosted AI Starter Kit** як альтернатива для повністю локального розгортання

Такий стек дозволить побудувати ефективну RAG-систему з мінімальними витратами і з максимальною гнучкістю щодо вибору LLM моделей та способу зберігання даних.

---

**Теги**: #RAG #n8n #OpenSource #LLM #MinIO #AI #Automation #SelfHosted #SemanticSearch #VectorDB #OpenRouter