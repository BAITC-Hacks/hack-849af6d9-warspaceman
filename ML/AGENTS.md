# ML/AI

Structure:
- src/ — модель, инференс
- notebooks/ — эксперименты
- service/ — если бэку нужен доступ к модели по HTTP, поднять здесь свой мини-сервис

Rules:
- Contract-first: если отдаёшь функциональность бэку, сначала опиши эндпоинт в /docs/API_CONTRACT.md
- Don't touch /backend or /frontend
- Веса моделей — в .gitignore, не в git

## API sync
Before writing or changing any code that talks to the backend, always read
/docs/API_CONTRACT.md first — it's the source of truth for endpoints.
If contract has no relevant entry, stop and ask instead of guessing the shape.