# Hack Alem AI 2026 — Business Task Catalog

An MVP for turning a business need into an editable, rated task card, publishing confirmed tasks to a catalog, and letting student teams submit proposals for a manual business decision.

## Architecture

```text
Browser
  │ HTTP/JSON on /api
  ▼
Frontend: React + Vite build, served by Nginx (:80 in Docker)
  │ /api/* is proxied to backend:8000 with the prefix removed
  ▼
Backend: FastAPI (:8000) ──HTTP/JSON──▶ ML service: FastAPI (:8001)
  │                                     └─ rule-based fallback without a key
  └─ SQLite database at /data/app.db (persistent Docker volume)
```

The service contract is documented in [docs/API_CONTRACT.md](docs/API_CONTRACT.md). The backend keeps the public API paths unchanged. In Docker, the browser calls `/api`; Nginx removes that prefix before forwarding requests to FastAPI.
Inside Compose the backend calls `http://ml:8001`; local backend development defaults to `http://localhost:8001`.

## Problem and solution

Business requests often start as short descriptions that leave student teams unsure about users, available data, expected outcomes, constraints, and success measures. The platform guides a business user through clarification, presents an editable task card, rates its readiness, and publishes confirmed tasks for student proposals. The business user keeps the final team decision.

### MVP capabilities

- Business user creates a task and receives at least three clarification questions.
- The submitted answers are saved with their questions and used to produce an editable card.
- The card receives a deterministic readiness score and field-level improvement guidance.
- Confirmed tasks appear in the shared catalog, including low-rated tasks; catalog filters support topic and readiness, with rating sort.
- Student teams submit an idea, plan, duration/deadline, and prototype link.
- Business users review proposals and manually accept or reject them. There is no automatic team assignment.

The MVP uses a demonstration role switch in the frontend. Authentication and advanced access control are outside its scope.

### Technologies and repository layout

- **Frontend:** React, Vite, Fetch API, CSS.
- **Backend:** FastAPI, SQLAlchemy async, SQLite, aiosqlite, Pydantic, HTTPX.
- **ML service:** FastAPI, OpenAI structured output when configured, and a rule-based fallback without a key.

```text
.
├── docker-compose.yml
├── docs/API_CONTRACT.md
├── frontend/       React/Vite app and Nginx packaging
├── backend/        FastAPI routes, models, rating, and ML adapter
└── ML/             FastAPI question and card service (uppercase path)
```

The frontend talks only to the backend API. The backend calls the ML service; if it is unavailable, the backend's deterministic fallback keeps the main flow usable.

## Run the complete application with Docker

Use Docker Desktop in **Linux-container mode** and run from the repository root:

```sh
docker compose up --build -d
```

Open [http://localhost:8080](http://localhost:8080). This builds a static frontend image and starts `frontend`, `backend`, and `ml`. It is not a hot-reload development setup: rebuild after source changes with the same command.

| Service | Container port | Host access | Health check |
|---|---:|---|---|
| frontend (Nginx) | 80 | `127.0.0.1:8080` | Static HTTP response |
| backend (FastAPI) | 8000 | Compose network only | `GET /teams` checks app and database |
| ml (FastAPI) | 8001 | Compose network only | `GET /health` |

Only the frontend is published to the host. Set `FRONTEND_PORT` in the environment or `.env.local` to use another host port. Ports 8000 and 8001 are not published, so local development servers may use them.

The first build needs network access to download the official base images and the dependencies listed in the existing backend, ML, and frontend lock files. Containers use Linux Python and Node images; they do not use host Python, Node, virtual environments, `node_modules`, or a committed `dist` directory.

### Optional local configuration

The stack works without an API key and does not require an environment file. To set optional values, copy the secret-free example and edit the ignored local file:

```powershell
Copy-Item .env.example .env.local
```

Then launch with:

```sh
docker compose --env-file .env.local up --build -d
```

`OPENAI_API_KEY` is passed only to the ML container at runtime. Leave it empty to use the ML service's labelled rule-based mode. `OPENAI_MODEL` is optional and defaults to `gpt-4o-mini`. Do not put a real key in the tracked root `.env`, frontend variables, image build arguments, or source files. The root `.env` is currently tracked and empty; use `.env.local` for private values.

Startup and health checks do not make paid provider requests. To opt into a separate provider-backed check, put your key in `.env.local`, start or recreate the ML service with `docker compose --env-file .env.local up -d --force-recreate ml`, then create a task through the UI or call `POST /api/tasks`. That request invokes the provider when the key is configured and may incur provider charges.

### Check status, logs, and stop

```sh
docker compose ps
docker compose logs -f frontend backend ml
docker compose down
```

`docker compose ps` reports service health. The checks make local HTTP calls only: frontend static content, backend `GET /teams`, and ML `GET /health`. Healthy containers show that processes and local dependencies respond; they do not prove real AI quality or that a paid provider was used.

The backend SQLite database is stored in the named `backend-data` volume at `/data/app.db`. The image prepares a writable `/data` directory for its non-root user. The data remains available across container recreation and ordinary `docker compose down` followed by `up`. Normal shutdown does not remove the volume. Do not remove the volume unless you intend to permanently erase the demo database.

If port 8080 is occupied, set `FRONTEND_PORT` to a free port. If Docker reports it cannot connect to the engine, start Docker Desktop, switch it to Linux containers, wait for the engine to become ready, then retry the Compose command.

### Rebuild and run backend regression tests

Rebuild after changing frontend, backend, or ML source:

```sh
docker compose up --build -d
```

The backend image includes the regression tests. Run them in the Linux Python image with:

```sh
docker compose run --rm --no-deps backend python -m unittest discover -s tests -v
```

The suite uses a temporary SQLite database and mocked outbound ML HTTP; it does not modify the persistent demo database or make paid calls. A separate no-key smoke test against the real running ML container is needed to verify service-to-service connectivity and rule-based responses.

## Local development without Docker

Run each service from its own directory. The ML directory is uppercase `ML/`.

Backend, from `backend/`:

```sh
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

ML, from `ML/`:

```sh
python -m pip install -r requirements-dev.txt
uvicorn service.main:app --reload --port 8001
```

Frontend, from `frontend/`:

```sh
npm ci
npm run dev
```

The Vite development server is available at [http://localhost:5173](http://localhost:5173). For local cross-origin API calls, set `VITE_API_BASE_URL=http://localhost:8000` in the frontend's local Vite environment. The Docker build sets `VITE_API_BASE_URL=/api` at build time.

## Rating model

The task rating is deterministic and ranges from 0 to 100. Points are awarded only when the corresponding information is present:

| Card information | Points |
|---|---:|
| Context and need | 20 |
| Data and materials | 20 |
| Expected result | 15 |
| Success criteria | 15 |
| Constraints | 10 |
| Users | 10 |
| Business contact and interaction format | 10 |

Readiness levels are `draft` (0–39), `working` (40–69), `ready` (70–89), and `priority` (90–100). Confirmed tasks remain visible in the catalog regardless of rating; catalog filters include topic and readiness, with optional rating sort. Business users make proposal decisions manually; the backend never automatically assigns a team.

## Demo flow

1. Create a task from a short business description and answer the clarification questions.
2. Review and edit the task card, then confirm it and inspect its rating.
3. Find the confirmed task in the catalog and submit a team proposal.
4. Review proposals and accept or reject them manually as the business user.

Use synthetic demo data. The rating, catalog, and proposal flow does not require provider-backed AI.

### Walkthrough details

1. Choose the business role and create a task from a short request such as “We need a service to help employees prepare monthly reports faster.” A topic such as `Reporting` is optional.
2. Answer the returned clarification questions. Review the generated card and edit fields directly; the business user controls the final card contents.
3. Confirm the card and inspect the 0–100 score, readiness level, breakdown, missing fields, and suggestions. Fill missing information and save changes; edits to a confirmed task recalculate its rating.
4. Publish by confirming the task. Open the catalog and try topic filtering, readiness filtering, or rating sort. Low scores do not hide confirmed tasks.
5. Create/select a student team, open the published task, and send a proposal with an idea, plan, estimated duration/deadline, and prototype link.
6. Return to the business role, review the proposals, and manually accept or reject one. The API never selects a team automatically.

For a focused API demo, the backend endpoints are:

```text
POST  /tasks
PATCH /tasks/{id}/answers
PATCH /tasks/{id}
POST  /tasks/{id}/confirm
GET   /tasks/{id}/rating
GET   /tasks
POST  /teams
GET   /teams
POST  /tasks/{id}/proposals
GET   /tasks/{id}/proposals
PATCH /proposals/{id}
```

The full request/response shapes and nullable fields are in the [API contract](docs/API_CONTRACT.md). To prepare for proposal submission, first ensure at least one team exists; teams can be created from the UI or with `POST /teams` through the API. Proposal decisions use the documented `pending`, `accepted`, and `rejected` statuses and remain a business action.

### Rating and readiness reference

| Category | Points |
|---|---:|
| Context and need | 20 |
| Data and materials | 20 |
| Expected result | 15 |
| Success criteria | 15 |
| Constraints | 10 |
| Users | 10 |
| Business contact and interaction format | 10 |
| **Maximum** | **100** |

| Score | Readiness |
|---:|---|
| 0–39 | Draft |
| 40–69 | Working |
| 70–89 | Ready |
| 90–100 | Priority |

The backend owns this formula; the frontend displays the response and does not calculate its own score. Points count when the required card information is present.

### ML behavior

The ML service exposes `POST /generate-questions` and `POST /form-card`. Without `OPENAI_API_KEY`, it uses a labelled rule-based response and makes no provider request. With a key, task creation and answer submission may invoke the configured provider. Container health checks call only local health routes and do not indicate whether provider-backed AI ran or whether its output is high quality.

## Scope of the MVP

The demo focuses on the task-to-proposal flow. User registration, password recovery, complex role management, chat, notifications, file storage, payment, and automatic team assignment are not included.
