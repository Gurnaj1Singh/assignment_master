# Assignment Master

> An academic assignment management platform with semantic plagiarism detection, LLM-powered question generation, and collusion analytics — built for NIT Jalandhar.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
  - [Backend](#backend)
  - [Frontend](#frontend)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Key Design Decisions](#key-design-decisions)
- [Plagiarism Detection Pipeline](#plagiarism-detection-pipeline)

---

## Overview

Assignment Master is a full-stack web application that gives professors tools to create and manage assignments, detect plagiarism using semantic vector similarity, generate questions from reference material using a RAG (Retrieval-Augmented Generation) pipeline, and identify collusion rings through graph analysis. Students submit PDF assignments, receive plagiarism feedback, and are served individually assigned questions.

The system is purpose-built for institutional use. Authentication is restricted to `@nitj.ac.in` email addresses, and all core operations — submission comparison, question generation, collusion detection — run server-side with no client-side trust.

---

## Features

### For Professors
- Create classrooms with auto-generated invite codes
- Create and publish assignment tasks with PDF question papers
- Upload reference corpus PDFs per task (used for source exclusion and RAG)
- Generate up to 100 questions from reference material via OpenAI GPT-4o-mini
- Select and randomly distribute questions to enrolled students
- View plagiarism scores, pairwise similarity matrices, and heatmaps
- Detect collusion rings using NetworkX graph connected-component analysis
- Inspect flagged sentence matches side-by-side in a diff viewer
- Track per-student submission status across the class

### For Students
- Join classrooms using professor-issued codes
- View published tasks and assigned questions (difficulty + Bloom's level)
- Submit PDF assignments before deadline (5-minute grace period)
- View own plagiarism score and flagged matches post-evaluation

### Platform
- OTP-based email verification for signup and password reset
- JWT authentication with silent access-token refresh via refresh tokens
- Rate limiting per authenticated user (or IP for unauthenticated routes)
- Soft-delete pattern across all core entities with full audit trail
- ASGI-native request ID middleware for distributed tracing

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│   React 19 + Vite  ·  React Query  ·  Zustand  ·  shadcn  │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS / REST
┌───────────────────────────▼─────────────────────────────────┐
│                     FastAPI (ASGI)                          │
│  Auth  ·  Classrooms  ·  Assignments  ·  Questions  ·  Refs │
│                                                             │
│  ┌──────────────────┐   ┌──────────────────────────────┐   │
│  │   NLP Service    │   │       LLM Service            │   │
│  │  SBERT 768D      │   │  OpenAI GPT-4o-mini (RAG)    │   │
│  │  all-mpnet-base  │   │  100 question generation     │   │
│  └────────┬─────────┘   └──────────────────────────────┘   │
│           │ embeddings                                      │
│  ┌────────▼──────────────────────────────────────────────┐  │
│  │               PostgreSQL 14+  +  pgvector             │  │
│  │  Users · Classrooms · Submissions · TextVectors       │  │
│  │  Questions · References · OTPRecords                  │  │
│  │  HNSW index on Vector(768) — cosine ANN search        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Data flow for a student submission:**

```
Student PDF upload
      │
      ▼
PyMuPDF text extraction
      │
      ▼
NLTK sentence tokenization
      │
      ▼
SBERT batch embedding (768D vectors)
      │
      ├──▶ TextVector rows (PostgreSQL + pgvector HNSW)
      │
      ▼
pgvector cosine similarity search (threshold: 0.85)
      │
      ├──▶ Cross-student matches
      │
      └──▶ Reference corpus cross-check (source exclusion)
                  │
                  ▼
         Plagiarism score + verbatim flag stored on Submission
```

---

## Tech Stack

### Backend

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.104+, Uvicorn (ASGI) |
| Database | PostgreSQL 14+ with pgvector extension |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Auth | python-jose (JWT, HS256), passlib (bcrypt) |
| NLP | sentence-transformers (all-mpnet-base-v2), NLTK, PyMuPDF |
| LLM | OpenAI Python SDK (GPT-4o-mini) |
| Graph | NetworkX (collusion ring detection) |
| Email | fastapi-mail over Gmail SMTP |
| Rate Limiting | slowapi |
| Validation | Pydantic v2, pydantic-settings |

### Frontend

| Layer | Technology |
|---|---|
| Framework | React 19, Vite 7 |
| Routing | react-router-dom 7 (lazy-loaded routes) |
| Server State | TanStack React Query 5 |
| Client State | Zustand 5 |
| Forms | react-hook-form 7 + Zod 4 |
| HTTP | Axios 1.13 (interceptors for silent refresh) |
| UI | shadcn/ui (Radix UI primitives), Tailwind CSS 4 |
| Charts | Recharts 3 (heatmaps, similarity matrices) |
| Toasts | Sonner 2 |
| Icons | Lucide React |
| Date Utilities | date-fns + date-fns-tz |

---

## Prerequisites

- Python 3.10+
- Node.js 20+ and npm 10+
- PostgreSQL 14+ with the `pgvector` extension installed
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833) enabled for SMTP
- An OpenAI API key (GPT-4o-mini access required for question generation)

**Install the pgvector extension on your PostgreSQL instance:**

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Local Setup

### Backend

```bash
# 1. Clone the repository
git clone <repository-url>
cd assignment_master

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate          # Linux / macOS
# venv\Scripts\activate           # Windows

# 3. Install Python dependencies
pip install -r backend/requirements.txt

# 4. Create the PostgreSQL database
createdb assignment_master

# 5. Configure environment variables
cp .env.example .env              # then edit .env with your values

# 6. Apply all database migrations
cd backend
alembic upgrade head

# 7. Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive documentation is served at `http://localhost:8000/docs`.

### Frontend

```bash
# From the project root
cd frontend

# Install dependencies
npm install

# Start the Vite development server (HMR enabled)
npm run dev
```

The UI will be available at `http://localhost:5173`.

**Production build:**

```bash
npm run build      # outputs to frontend/dist/
npm run preview    # serve the production build locally
```

---

## Environment Variables

Create a `.env` file in the project root. All variables below are required unless marked optional.

```env
# ── Database ────────────────────────────────────────────────────────────────
SQLALCHEMY_DATABASE_URL=postgresql://user:password@localhost:5432/assignment_master

# ── JWT Security ────────────────────────────────────────────────────────────
SECRET_KEY=<random-256-bit-hex>       # openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── Email (Gmail SMTP with App Password) ────────────────────────────────────
MAIL_USERNAME=your-address@gmail.com
MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx    # App Password, not account password
MAIL_FROM=your-address@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
USE_CREDENTIALS=true

# ── CORS ────────────────────────────────────────────────────────────────────
FRONTEND_URL=http://localhost:5173
CORS_ALLOW_ALL=false                  # Set to true only in development

# ── NLP (SBERT) ─────────────────────────────────────────────────────────────
SBERT_MODEL_NAME=all-mpnet-base-v2
SIMILARITY_THRESHOLD=0.85

# ── LLM (OpenAI) ────────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
```

> **Note:** The SBERT model (~420 MB) is downloaded automatically from Hugging Face on first startup and cached locally. Ensure outbound internet access from the server during the first run.

---

## Database Migrations

Migrations are managed with Alembic. All migration files live in `backend/alembic/versions/`.

| Revision | Description |
|---|---|
| `001` | Initial schema — Users, Classrooms, Memberships, Tasks, Submissions, TextVectors |
| `002` | HNSW vector index on `TextVector.embedding` for approximate nearest-neighbor search |
| `003` | Production hardening — CheckConstraints, partial unique indexes, soft-delete indexes |
| `004` | Reference corpus — `ReferenceDocument` and `ReferenceVector` tables |
| `005` | Question generation — `GeneratedQuestion` and `StudentQuestionAssignment` tables |
| `006` | OTP persistence — `OTPRecord` table with TTL-based expiry |

```bash
# Apply all pending migrations
alembic upgrade head

# Roll back the last migration
alembic downgrade -1

# View current database revision
alembic current

# View full migration history
alembic history --verbose
```

---

## API Reference

All endpoints are prefixed with `/api/v1`. Protected routes require an `Authorization: Bearer <access_token>` header.

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/auth/signup` | Initiate signup — validates email domain, sends OTP | — |
| `POST` | `/auth/verify-otp` | Verify OTP, create user account | — |
| `POST` | `/auth/login` | Password login, returns access + refresh tokens | — |
| `POST` | `/auth/refresh` | Exchange refresh token for new access token | — |
| `POST` | `/auth/forgot-password` | Request password-reset OTP | — |
| `POST` | `/auth/reset-password` | Verify reset OTP and set new password | — |

Rate-limited at **5 requests / minute** per IP for all auth endpoints.

### Classrooms

| Method | Endpoint | Description | Role |
|---|---|---|---|
| `POST` | `/classrooms/create` | Create a new classroom | Professor |
| `POST` | `/classrooms/join/{class_code}` | Enrol in a classroom by code | Student |
| `GET` | `/classrooms/my` | List classrooms the user belongs to | Any |
| `GET` | `/classrooms/{id}/members` | List enrolled students | Professor |
| `GET` | `/classrooms/{id}/tasks` | List tasks (students see published only) | Any |
| `POST` | `/classrooms/{id}/tasks` | Create a new assignment task | Professor |

### Assignments

| Method | Endpoint | Description | Role |
|---|---|---|---|
| `POST` | `/assignments/submit/{task_id}` | Submit assignment PDF (3/min rate limit) | Student |
| `POST` | `/assignments/task-pdf/{task_id}` | Upload task question-paper PDF | Professor |
| `GET` | `/assignments/task/{task_id}` | Task detail (view differs by role) | Any |
| `PATCH` | `/assignments/task/{task_id}/publish` | Toggle task published state | Professor |
| `GET` | `/assignments/status/{task_id}` | Submission status for all enrolled students | Professor |
| `GET` | `/assignments/report/{task_id}` | Sorted plagiarism score report | Professor |
| `GET` | `/assignments/matrix/{task_id}` | Pairwise student similarity matrix | Professor |
| `GET` | `/assignments/heatmap/{task_id}` | All-pairs heatmap data | Professor |
| `GET` | `/assignments/collusion-groups/{task_id}` | Collusion ring clusters (NetworkX) | Professor |
| `GET` | `/assignments/submission-detail/{submission_id}` | Flagged match details for a submission | Professor |
| `GET` | `/assignments/my-submissions` | Authenticated student's submission history | Student |

### References

| Method | Endpoint | Description | Role |
|---|---|---|---|
| `POST` | `/references/upload/{task_id}` | Upload reference PDF, chunk and embed | Professor |
| `GET` | `/references/list/{task_id}` | List reference documents for a task | Professor |
| `DELETE` | `/references/{id}` | Soft-delete a reference document | Professor |

### Questions

| Method | Endpoint | Description | Role |
|---|---|---|---|
| `POST` | `/questions/generate/{task_id}` | Generate 100 questions via GPT RAG | Professor |
| `GET` | `/questions/list/{task_id}` | List all generated questions | Professor |
| `POST` | `/questions/select/{task_id}` | Mark questions as selected for distribution | Professor |
| `POST` | `/questions/distribute/{task_id}` | Randomly assign questions to students | Professor |
| `GET` | `/questions/my-questions/{task_id}` | Get student's assigned questions | Student |

---

## Project Structure

```
assignment_master/
├── backend/
│   ├── main.py                        # App factory, middleware, lifespan, router mount
│   ├── config.py                      # Pydantic settings (reads from .env)
│   ├── database.py                    # SQLAlchemy engine, session factory, get_db()
│   ├── requirements.txt
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/                  # 001 – 006 migration files
│   │
│   ├── models/
│   │   ├── base.py                    # Base, TimestampMixin, SoftDeleteMixin
│   │   ├── user.py
│   │   ├── classroom.py               # Classroom, ClassroomMembership
│   │   ├── submission.py              # AssignmentTask, Submission
│   │   ├── text_vector.py             # TextVector (Vector(768))
│   │   ├── question.py                # GeneratedQuestion, StudentQuestionAssignment
│   │   ├── reference.py               # ReferenceDocument, ReferenceVector
│   │   └── otp.py                     # OTPRecord
│   │
│   ├── repositories/
│   │   ├── base.py                    # Generic BaseRepository[T] with soft-delete filter
│   │   ├── user_repo.py
│   │   ├── classroom_repo.py
│   │   ├── submission_repo.py
│   │   ├── vector_repo.py             # pgvector cosine search queries
│   │   ├── question_repo.py
│   │   ├── reference_repo.py
│   │   └── otp_repo.py
│   │
│   ├── schemas/                       # Pydantic request/response models
│   │   ├── auth.py
│   │   ├── classroom.py
│   │   ├── submission.py
│   │   ├── question.py
│   │   └── reference.py
│   │
│   ├── services/
│   │   ├── auth_service.py            # OTP lifecycle, JWT issuance, password reset
│   │   ├── plagiarism_service.py      # Embedding pipeline, scoring, source exclusion
│   │   ├── nlp_service.py             # SBERT singleton (lazy-loaded, thread-safe)
│   │   ├── llm_service.py             # OpenAI GPT-4o-mini question generation
│   │   ├── pdf_service.py             # PyMuPDF text extraction
│   │   ├── reference_service.py       # Reference corpus ingestion
│   │   ├── graph_service.py           # NetworkX collusion ring detection
│   │   ├── question_distribution_service.py
│   │   ├── classroom_service.py
│   │   └── text_utils.py              # Verbatim detection helpers
│   │
│   ├── api/
│   │   ├── deps.py                    # get_current_user, require_role, oauth2_scheme
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── classrooms.py
│   │       ├── assignments.py
│   │       ├── references.py
│   │       └── questions.py
│   │
│   ├── middleware/
│   │   ├── exception_handler.py       # ASGI RequestIDMiddleware, global error handlers
│   │   └── rate_limiter.py            # slowapi config, user-ID key function
│   │
│   └── core/
│       ├── security.py                # bcrypt hashing, JWT create/decode
│       └── email.py                   # FastMail SMTP, OTP email templates
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js                 # Vite + React plugin + Tailwind CSS, @ alias
│   ├── package.json
│   │
│   └── src/
│       ├── main.jsx                   # React 19 root, QueryClientProvider, Sonner
│       ├── App.jsx                    # Route renderer with Suspense
│       ├── routes.jsx                 # Declarative route tree (lazy-loaded)
│       │
│       ├── api/
│       │   ├── client.js              # Axios instance, token injection, silent refresh
│       │   ├── auth.js
│       │   ├── assignments.js
│       │   ├── classrooms.js
│       │   ├── questions.js
│       │   └── references.js
│       │
│       ├── stores/
│       │   ├── authStore.js           # Zustand — user, isAuthenticated, login/logout
│       │   └── themeStore.js          # Zustand — dark/light, localStorage persist
│       │
│       ├── pages/
│       │   ├── auth/                  # Login, Signup, VerifyOtp, ForgotPassword, ResetPassword
│       │   ├── dashboard/             # ProfessorDashboard, StudentDashboard, StudentSubmissions
│       │   ├── classroom/             # ClassroomDetailPage
│       │   ├── task/                  # TaskDetailPage
│       │   └── NotFoundPage.jsx
│       │
│       ├── components/
│       │   ├── layout/                # AppShell (sidebar + topbar), ProtectedRoute
│       │   ├── analytics/             # PlagiarismReport, SimilarityMatrix, CollusionHeatmap, CollusionGroups
│       │   ├── submission/            # MatchViewer (side-by-side diff)
│       │   ├── shared/                # DeadlineCountdown, ErrorBoundary, QueryError
│       │   └── ui/                    # Full shadcn/ui primitive set (20+ components)
│       │
│       └── lib/
│           ├── utils.js               # cn() — clsx + tailwind-merge
│           └── validators.js          # Zod schemas for all forms
│
├── uploads/
│   ├── assignments/                   # Student PDF submissions
│   ├── tasks/                         # Professor question-paper PDFs
│   └── references/                    # Reference corpus PDFs
│
├── Assignment_Master_ERD.svg          # Entity-relationship diagram
├── diagram.puml                       # PlantUML source
└── .env                               # Environment configuration (not committed)
```

---

## Key Design Decisions

### Pure ASGI Middleware (not BaseHTTPMiddleware)

`RequestIDMiddleware` is implemented as a raw ASGI middleware rather than extending `BaseHTTPMiddleware`. This avoids a known Starlette behaviour where `BaseHTTPMiddleware` consumes the entire response body before forwarding it, silently dropping `Access-Control-*` headers from error responses. The pure ASGI approach attaches an `X-Request-ID` UUID to every response without interfering with CORS headers.

### Vector Search with pgvector and HNSW

Submission embeddings (768D SBERT vectors) are stored in PostgreSQL using the pgvector extension. An HNSW (Hierarchical Navigable Small World) index provides sub-linear approximate nearest-neighbor search for cosine similarity comparisons. The similarity threshold of `0.85` is deliberately conservative to reduce false positives — nearly identical sentences are flagged, not merely topic-adjacent ones.

### Soft Delete Across All Core Models

Every major entity (`User`, `Classroom`, `ClassroomMembership`, `AssignmentTask`, `Submission`, etc.) inherits from `SoftDeleteMixin`, which adds `is_deleted`, `deleted_at`, and `deleted_by` columns. Repository base classes automatically filter `is_deleted = false` in every query. A **partial unique index** on `ClassroomMembership(classroom_id, student_id) WHERE is_deleted = false` allows a student who left to re-enrol without violating uniqueness constraints.

### Stateless JWT with Refresh Token Pattern

Access tokens expire in 60 minutes. A 7-day refresh token is issued alongside and stored client-side. The Axios request interceptor queues requests that receive a 401, silently calls `/auth/refresh`, updates the stored token, and replays the queued requests — transparent to the user. Both token types include a `"type"` claim (`"access"` / `"refresh"`) to prevent substitution attacks.

### Thread-Safe SBERT Singleton

The SBERT model (~420 MB) is loaded once at startup via a double-checked locking singleton in `NLPService`. FastAPI route handlers that call `get_nlp_service()` receive the same instance across all requests. CPU-bound inference functions are declared as regular `def` (not `async def`), so Uvicorn dispatches them to a thread-pool executor, keeping the async event loop free for concurrent I/O.

### Cryptographically Secure OTP Generation

OTPs are generated with `secrets.randbelow(1_000_000)` (CSPRNG) rather than `random.randint`, and compared using `hmac.compare_digest` to prevent timing side-channel attacks. OTPs are persisted in the `OTPRecord` table with a 5-minute TTL, making them resilient to server restarts and compatible with horizontally scaled deployments.

### Source Exclusion in Plagiarism Scoring

When a student sentence matches another student's submission above the threshold, the system also queries the reference corpus vectors. If the match is also found in a reference document, the sentence is tagged for display but **excluded from the final plagiarism score**. This prevents penalising students for citing source material, while still surfacing verbatim copies in the professor's report.

### Constraint-Based Uniqueness (Not Application Logic)

Uniqueness invariants are enforced at the database level:
- `UNIQUE (task_id, student_id)` on `Submission` — one submission per student per task
- `UNIQUE (student_id, question_id)` on `StudentQuestionAssignment` — no duplicate question assignments
- `CHECK (0.0 <= overall_similarity_score <= 100.0)` on `Submission` — score bounds

This prevents TOCTOU race conditions that application-level checks cannot guard against under concurrent load.

---

## Plagiarism Detection Pipeline

```
1. Receive student PDF via multipart upload
       │
2. PyMuPDF: extract raw text (handles multi-column, headers, footers)
       │
3. NLTK sent_tokenize: split into discrete sentences
       │
4. SBERT (all-mpnet-base-v2):
   batch encode sentences → float32[768] embeddings
       │
5. Bulk INSERT TextVector rows
   (submission_id, content_chunk, embedding, type='sentence', seq_order)
       │
6. pgvector ANN query (HNSW, cosine distance):
   for each sentence vector → find closest vectors in other submissions
   where cosine_similarity >= SIMILARITY_THRESHOLD (default 0.85)
       │
7. Reference corpus cross-check:
   for each flagged sentence → query ReferenceVector table
   ├── similarity >= threshold + verbatim match → flag, display, exclude from score
   └── similarity >= threshold + paraphrase → exclude from score silently
       │
8. Score calculation:
   plagiarism_score = (flagged - excluded) / total_sentences * 100
       │
9. Persist score + verbatim_flag on Submission row
   Submission.status → 'completed' (or 'failed' on exception)
```

**Collusion ring detection** runs separately on-demand:

```
GET /assignments/collusion-groups/{task_id}
       │
Build similarity graph G:
  nodes = students with completed submissions
  edges = pairs where matrix[i][j] > 0.30 (30% overlap)
       │
NetworkX connected_components(G)
       │
Return clusters of ≥2 students as collusion groups
```

---

*Assignment Master is built for academic use at NIT Jalandhar. All authentication is restricted to `@nitj.ac.in` email addresses.*
