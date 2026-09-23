# Hack Alem AI 2026 — Business Task Catalog

> **From a vague business request to a clear student-ready challenge.**

Hack Alem AI is a hackathon MVP that helps a business turn a short problem description into a structured task card, measure how ready that task is for student teams, publish it to a shared catalog, receive proposals, and manually choose a team.

---

## ✨ What the product does

### For business

1. Write a short description of a real business problem.
2. Receive clarifying questions.
3. Get an editable task card.
4. See a **readiness score from 0 to 100**.
5. Improve missing fields and recalculate the score.
6. Publish the task to the catalog.
7. Review team proposals.
8. **Accept or reject proposals manually.**

### For student teams

1. Browse published business tasks.
2. Filter by topic and readiness level.
3. Open the full task brief.
4. Create or select a team.
5. Submit:
   - solution idea;
   - implementation plan;
   - deadline;
   - prototype link.
6. Wait for the business decision.

The frontend uses a simple **Business / Student** demo role switch instead of full authentication.

---

## 🎯 Why it matters

Business tasks are often too vague for students to start working immediately.

Typical missing details:

- who will use the solution;
- what data or materials are available;
- what result is expected;
- what constraints exist;
- how success will be measured;
- how the team can communicate with the business.

The platform makes these gaps visible and turns task quality into a transparent readiness score.

---

## 🧠 Readiness score

The backend calculates the score. The frontend only displays the result.

| Category | Points |
|---|---:|
| Context + business need | 20 |
| Data and materials | 20 |
| Expected result | 15 |
| Success criteria | 15 |
| Constraints | 10 |
| Users | 10 |
| Contact + interaction format | 10 |
| **Maximum** | **100** |

Readiness levels:

| Score | Level |
|---:|---|
| 0–39 | Draft |
| 40–69 | Working |
| 70–89 | Ready |
| 90–100 | Priority |

A low score **does not hide a confirmed task**. It only shows how much clarification is still needed.

---

## 🏗 Architecture

```text
Browser
  │
  │  HTTP / JSON
  ▼
Frontend — React + Vite + Nginx
  │
  │  /api/*
  ▼
Backend — FastAPI + SQLAlchemy + SQLite
  │
  │  HTTP / JSON
  ▼
ML service — FastAPI
  │
  ├─ OpenAI API when configured
  └─ rule-based fallback without a key
```

### Repository structure

```text
.
├── frontend/             React/Vite UI
├── backend/              FastAPI API, rating, DB, proposals
├── ML/                   clarification + card extraction service
├── docs/
│   └── API_CONTRACT.md   source of truth for API shapes
├── docker-compose.yml
└── README.md
```

---

## 🧰 Tech stack

### Frontend
- React
- Vite
- JavaScript
- CSS
- Fetch API
- Nginx in Docker

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- aiosqlite
- Pydantic
- HTTPX

### ML / AI
- Python
- FastAPI
- OpenAI API support
- structured output
- rule-based fallback when no API key is configured

---

# 🚀 Quick start with Docker

This is the easiest way to run the whole project.

### Requirements

- Docker Desktop
- Git

### 1. Clone the repository

```powershell
git clone https://github.com/BAITC-Hacks/hack-849af6d9-warspaceman.git
cd hack-849af6d9-warspaceman
```

### 2. Start Docker Desktop

Wait until Docker is fully running.

### 3. Build and start the project

```powershell
docker compose up --build -d
```

### 4. Open the app

**http://localhost:8080**

### 5. Check container status

```powershell
docker compose ps
```

Expected services:

```text
frontend
backend
ml
```

### 6. View logs

```powershell
docker compose logs -f
```

Or per service:

```powershell
docker compose logs -f frontend
docker compose logs -f backend
docker compose logs -f ml
```

### 7. Stop the project

```powershell
docker compose down
```

The SQLite demo database is stored in a Docker volume and survives a normal `docker compose down`.

> Do not use `docker compose down -v` unless you intentionally want to delete demo data.

---

## 🔑 OpenAI API key — optional

The project can run **without an OpenAI API key** using the local rule-based fallback.

To enable the provider-backed AI path, copy the example environment file:

```powershell
Copy-Item .env.example .env.local
```

Then edit `.env.local`:

```env
FRONTEND_PORT=8080
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

Start with:

```powershell
docker compose --env-file .env.local up --build -d
```

Do not commit real API keys.

---

# 🧪 How the jury can verify the solution

The complete MVP can be checked in one end-to-end scenario.

## 1. Business creates a task

Switch to **Business** and click **Create task**.

Example:

```text
We need a service that helps employees prepare monthly reports faster.
```

Optional topic:

```text
Reporting
```

Submit the draft.

---

## 2. Answer clarification questions

The system returns targeted questions about missing information.

Answer them and continue to the editable task card.

---

## 3. Review the task card and rating

The task card contains fields such as:

- title;
- context;
- business need;
- users;
- data and materials;
- constraints;
- expected result;
- success criteria;
- contact;
- interaction format;
- topic.

The UI also shows:

- readiness score;
- readiness level;
- score breakdown;
- missing fields;
- improvement suggestions.

---

## 4. Demonstrate rating growth

Add missing information and press:

```text
Save & recalculate
```

The backend recalculates the score.

This demonstrates the core gamification mechanic:

```text
weak task
   ↓
clarification
   ↓
better task
   ↓
higher readiness score
```

---

## 5. Publish the task

Press:

```text
Publish task
```

The confirmed task appears in the catalog.

The catalog supports:

- topic filtering;
- readiness filtering;
- rating sorting.

---

## 6. Student submits a proposal

Switch to **Student**.

Open the published task.

Create or select a team and submit:

- idea;
- plan;
- deadline;
- prototype link.

---

## 7. Business makes the decision

Switch back to **Business** on the same task.

The proposal list is shown with team names and status.

The business can manually:

```text
Accept proposal
Reject
```

There is **no automatic team assignment**.

---

## ✅ Demo flow in one line

```text
Draft
→ Clarification
→ Editable Card
→ Readiness Score
→ Improvement
→ Publish
→ Catalog
→ Team Proposal
→ Business Decision
```

---

## 🔌 Main backend API

### Tasks

```text
POST  /tasks
PATCH /tasks/{id}/answers
PATCH /tasks/{id}
POST  /tasks/{id}/confirm
GET   /tasks/{id}/rating
GET   /tasks
```

### Teams

```text
POST /teams
GET  /teams
```

### Proposals

```text
POST  /tasks/{id}/proposals
GET   /tasks/{id}/proposals
PATCH /proposals/{id}
```

Full request and response shapes are documented in:

**[docs/API_CONTRACT.md](docs/API_CONTRACT.md)**

---

# 💻 Local development without Docker

Use three terminals.

## Backend

```powershell
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend:

**http://localhost:8000**

Swagger:

**http://localhost:8000/docs**

---

## ML service

```powershell
cd ML
python -m pip install -r requirements-dev.txt
uvicorn service.main:app --reload --port 8001
```

Health endpoint:

**http://localhost:8001/health**

---

## Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Frontend:

**http://localhost:5173**

The frontend API client supports `VITE_API_BASE_URL` for explicit local API configuration. In Docker, the frontend uses `/api` through Nginx.

---

## 🔍 Useful Docker commands

Rebuild everything:

```powershell
docker compose up --build -d
```

Rebuild only frontend:

```powershell
docker compose up --build -d frontend
```

Check running services:

```powershell
docker compose ps
```

Tail logs:

```powershell
docker compose logs -f frontend backend ml
```

Stop:

```powershell
docker compose down
```

---

## 📌 MVP scope

Intentionally not included:

- full registration and password recovery;
- complex role management;
- chat;
- notifications;
- calendar;
- file storage;
- payment;
- automatic team assignment;
- full project tracking.

The goal is to demonstrate one reliable end-to-end workflow from a raw business need to a real student proposal and a manual business decision.

---

## 📄 API contract

The API contract between services is maintained in:

**[docs/API_CONTRACT.md](docs/API_CONTRACT.md)**

It is the source of truth for endpoint paths and request/response structures.
