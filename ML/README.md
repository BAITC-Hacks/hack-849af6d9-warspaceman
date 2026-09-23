# ML service

This FastAPI service generates clarifying questions and forms a task card. It supports English and Russian prompts and answers. Card values must be grounded in the draft or submitted answers; unknown fields are `null`. The AI path receives the original question-answer pairs so it can interpret unfamiliar wording. Its text check confirms a returned value appears in submitted evidence, but that check alone cannot prove the value was assigned to the semantically correct field.

## Setup

From this directory, create a virtual environment and install the development dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

The service works without an API key using its labelled rule-based fallback. That fallback recognizes explicitly labelled fields, the service's generated question templates, and unambiguous question wording; unfamiliar or ambiguous answer questions are left unmapped. Whole-answer placeholders such as `TBD`, `not sure`, `не знаю`, `пока неизвестно`, and `уточним позже` count as unknown. This is deliberately conservative: a substantive answer containing one of those phrases is retained, and meaningful negatives such as “No personal data may be used” remain data. To enable AI extraction, set `OPENAI_API_KEY` in your shell environment or environment manager; never put a real key in a repository file. Leave it unset to use the fallback. You can optionally set `OPENAI_MODEL`; the default is `gpt-4o-mini`. The question endpoint returns the language of the draft or topic. Answers in `/form-card` must be keyed by their question text.

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

The tests use a mocked provider and do not make paid API calls. A mocked AI test checks provider request/response behavior and is not evidence of live model quality. For repeatable deterministic fallback quality evaluation, run:

```sh
python evaluation/run_evaluation.py
```

The offline evaluator loads 13 synthetic cases from `evaluation/cases.json`, exercises `/generate-questions` and then `/form-card` in-process, reports exact field matches, missing expected values, and unexpectedly populated fields, and exits nonzero on failures. It clears the API key for these calls and does not contact a provider. Its results measure the rule-based fallback only.

## Demo requests

Five synthetic examples with different levels of completeness are in `examples/demo_drafts.json`. With the service running, call both endpoints for all five examples with:

```sh
python examples/run_demos.py
```

The demo script sends each draft to `/generate-questions`, then submits the generated questions and its sample answers to `/form-card`. It prints each question list, card, and generation mode.

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

## Russian clarification example

Start with a weak draft and topic:

```json
{"draft_text":"Нужен сервис для записи к школьному психологу. Пользователи: пока неизвестно.","topic":"Запись к школьному психологу"}
```

`POST /generate-questions` asks in Russian about missing details, including users because `пока неизвестно` is a placeholder. Suppose the returned list contains `Кто будет пользоваться решением для темы «Запись к школьному психологу»?`, `Какие данные или материалы и в каких форматах будут доступны для темы «Запись к школьному психологу»?`, and `Какой конкретный результат или готовый материал нужно подготовить для темы «Запись к школьному психологу»?`. Submit the exact returned strings as keys and only include facts the user supplied:

```json
{
  "draft_text":"Нужен сервис для записи к школьному психологу. Пользователи: пока неизвестно.",
  "questions":["Кто будет пользоваться решением для темы «Запись к школьному психологу»?","Какие данные или материалы и в каких форматах будут доступны для темы «Запись к школьному психологу»?","Какой конкретный результат или готовый материал нужно подготовить для темы «Запись к школьному психологу»?"],
  "answers":{
    "Кто будет пользоваться решением для темы «Запись к школьному психологу»?":"Ученики и их родители",
    "Какие данные или материалы и в каких форматах будут доступны для темы «Запись к школьному психологу»?":"Расписание специалистов в CSV",
    "Какой конкретный результат или готовый материал нужно подготовить для темы «Запись к школьному психологу»?":"Форма записи на консультацию"
  }
}
```

`POST /form-card` can then fill `users`, `data_materials`, and `expected_result` with those exact answers. The placeholder in the draft does not overwrite the clarified user value; other unsupported fields remain `null`.
