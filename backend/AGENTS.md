# Backend (FastAPI)

Run: uvicorn app.main:app --reload --port 8000

Structure:
- app/main.py — entrypoint, routers included here
- app/api/routes/ — один файл на ресурс
- app/schemas/ — Pydantic модели request/response
- app/services/ — бизнес-логика
- app/core/ — config, db session

Rules:
- Every route must match /docs/API_CONTRACT.md
- Async def for all routes
- Don't touch /frontend or /ml
