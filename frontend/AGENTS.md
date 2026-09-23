# Frontend (React)

Run: npm install && npm run dev

Structure:
- src/api/ — по файлу на ресурс, base URL из .env
- src/components/ — переиспользуемые компоненты
- src/pages/ — экраны

Rules:
- Requests must match /docs/API_CONTRACT.md
- Don't touch /backend or /ml

## API sync
Before writing or changing any code that talks to the backend, always read
/docs/API_CONTRACT.md first — it's the source of truth for endpoints.
If contract has no relevant entry, stop and ask instead of guessing the shape.
