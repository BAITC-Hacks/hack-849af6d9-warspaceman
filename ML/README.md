# ML service

This FastAPI service generates clarifying questions and forms a task card. It supports English and Russian prompts and answers. Card values come from the draft or the answer associated with a matching question; unsupported values are `null`.

## Setup

From this directory, create a virtual environment and install the development dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

The service works without an API key using its labelled rule-based fallback. To enable AI extraction, set `OPENAI_API_KEY`. You can optionally set `OPENAI_MODEL`; the default is `gpt-4o-mini`.

## Launch

From `ML/`:

```sh
uvicorn service.main:app --reload --port 8001
```

The API is available at `http://localhost:8001`; interactive API docs are at `http://localhost:8001/docs`. Responses include `X-Generation-Mode: openai` or `X-Generation-Mode: rule-based-stub`. Stub responses also include `X-Generation-Notice`.

## Tests

From `ML/`, run:

```sh
python -m pytest
```

The tests use a mocked provider and do not make paid API calls.

## Demo requests

Generate questions:

```sh
curl -i http://localhost:8001/generate-questions \
  -H 'Content-Type: application/json' \
  -d '{"draft_text":"Нужен инструмент для подготовки отчетов","topic":"Отчеты"}'
```

Form a card by answering generated questions. Use each exact question string as the key for its answer:

```sh
curl -i http://localhost:8001/form-card \
  -H 'Content-Type: application/json' \
  -d '{"draft_text":"Нужен инструмент для подготовки отчетов","questions":["Кто будет пользоваться решением?"],"answers":{"Кто будет пользоваться решением?":"Финансовые аналитики"}}'
```

The card response contains exactly `context`, `need`, `users`, `data_materials`, `constraints`, `expected_result`, and `success_criteria`.
