---
{"title":"Шаблони та ресурси для налаштування Cloudflare AI Workers","dg-publish":true,"dg-metatags":null,"dg-home":null,"permalink":"/dokumentacziya-do-proektu-exodus-pp-ua/shabloni-ta-resursi-dlya-nalashtuvannya-cloudflare-ai-workers/","dgPassFrontmatter":true,"noteIcon":""}
---



#### 1. **GitHub - chand1012/openai-cf-workers-ai**
- **Опис**: Цей репозиторій пропонує шаблон для заміни API OpenAI на Cloudflare AI. Він дозволяє використовувати SDK OpenAI із моделями Cloudflare AI без необхідності переписувати код. Включає інструкції з налаштування Worker’а, розгортання через Wrangler та інтеграції з API OpenAI.
- **Посилання**: [github.com/chand1012/openai-cf-workers-ai](https://github.com/chand1012/openai-cf-workers-ai)

#### 2. **GitHub - jackculpan/openai-to-cloudflare-ai**
- **Опис**: Цей шаблон демонструє використання Workers AI для створення базового URL для викликів AI моделі `@cf/meta/llama-3-8b-instruct` через клієнт OpenAI. Він схожий на приклад, який ви надали, і показує інтеграцію Cloudflare AI з OpenAI-сумісними клієнтами.
- **Посилання**: [github.com/jackculpan/openai-to-cloudflare-ai](https://github.com/jackculpan/openai-to-cloudflare-ai)

#### 3. **GitHub - SchrodingerFish/cloudflare-AI-workers**
- **Опис**: Репозиторій містить посібник із використання Workers AI на Cloudflare. Включає приклади, такі як імітація запитів DALL-E-3 із моделлю Stable Diffusion від Cloudflare та налаштування проксі для API ChatGPT.
- **Посилання**: [github.com/SchrodingerFish/cloudflare-AI-workers](https://github.com/SchrodingerFish/cloudflare-AI-workers)

#### 4. **GitHub - tsunrise/salieri**
- **Опис**: API-шлюз для OpenAI Chat Completion на базі Cloudflare Workers. Шаблон включає інструкції з налаштування Worker’а як проксі для Chat API OpenAI, конфігурацію змінних середовища та розгортання через Wrangler.
- **Посилання**: [github.com/tsunrise/salieri](https://github.com/tsunrise/salieri)

#### 5. **GitHub - bobbyiliev/cloudflare-ai-worker-demo**
- **Опис**: Демо-проєкт, який показує, як розгорнути Cloudflare Worker для генерації історій та зображень за допомогою AI. Включає кроки з налаштування проєкту, розгортання через Wrangler та локального тестування.
- **Посилання**: [github.com/bobbyiliev/cloudflare-ai-worker-demo](https://github.com/bobbyiliev/cloudflare-ai-worker-demo)

#### 6. **GitHub - janlay/openai-cloudflare**
- **Опис**: Проксі для API OpenAI на базі Cloudflare Workers. Шаблон пропонує докладні інструкції з створення сервісу, налаштування DNS і розгортання через Wrangler.
- **Посилання**: [github.com/janlay/openai-cloudflare](https://github.com/janlay/openai-cloudflare)

#### 7. **Офіційна документація Cloudflare Workers AI**
- **Опис**: Офіційна документація Cloudflare містить посібники та приклади для налаштування AI Workers із використанням Wrangler. Включає інструкції з конфігурації AI-моделей, розгортання Worker’ів та інтеграції з іншими сервісами, такими як Vectorize.
- **Посилання**: [developers.cloudflare.com/workers-ai](https://developers.cloudflare.com/workers-ai)

#### 8. **GitHub - cloudflare/workers-for-platforms-example**
- **Опис**: Хоча цей репозиторій не зосереджений виключно на AI, він пропонує базовий шаблон для платформ, які використовують Cloudflare Workers. Включає приклади налаштування просторів імен (dispatch namespaces) і розгортання через Wrangler, які можна адаптувати для AI-задач.
- **Посилання**: [github.com/cloudflare/workers-for-platforms-example](https://github.com/cloudflare/workers-for-platforms-example)

---

### Додаткові зауваження
- Ці шаблони охоплюють різні сценарії використання: від інтеграції з OpenAI до роботи з власними AI-моделями Cloudflare. Кожен із них містить інструкції з налаштування та розгортання через Wrangler, що робить їх корисними для ваших потреб.
- Якщо вам потрібні специфічніші шаблони (наприклад, для певних AI-моделей), ви можете додатково пошукати на GitHub чи GitLab за ключовими словами, такими як "Cloudflare AI Workers template" або "Wrangler AI example".
- Також рекомендую переглянути офіційні ресурси Cloudflare, такі як їхня організація на GitHub ([github.com/cloudflare](https://github.com/cloudflare)) або форум Cloudflare Community, де розробники діляться власними конфігураціями.

Сподіваюся, ці ресурси будуть вам корисними для налаштування Cloudflare AI Workers!