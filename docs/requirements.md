# HirePro AI — Approved Requirements

> **Status**: Approved  
> **Last Updated**: 2026-08-15  
> **Version**: 0.2.0

---

## 1. Product Overview

**HirePro AI** is an AI-powered placement and recruitment management platform that connects students/candidates, recruiters, companies, jobs, and applications.

The backend must be maintainable, secure, testable, and deployable. It must be built using technologies from the developer's backend learning path — no unnecessary technologies for resume keywords.

---

## 2. Approved Technology Stack

### Backend
| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| API Style | REST |
| Validation / Schemas | Pydantic v2 |

### Database
| Layer | Technology |
|---|---|
| RDBMS | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.x (async-compatible) |
| Migrations | Alembic |

### Authentication & Security
| Concern | Approach |
|---|---|
| Token Format | JWT (HS256 or RS256) |
| Auth Flow | OAuth2 Password Bearer (FastAPI native) |
| Password Storage | bcrypt via `passlib` |
| Authorization | Role-based access control (RBAC) |
| Ownership | Per-resource ownership checks |

### Testing
| Tool | Purpose |
|---|---|
| pytest | Test runner and assertions |
| FastAPI `TestClient` | HTTP-level integration tests |
| Factory fixtures | Repeatable test data |

### Configuration
| Item | Purpose |
|---|---|
| `.env` | Local secrets (git-ignored) |
| `.env.example` | Template for required variables |
| `pydantic-settings` | Typed, validated config loading |

### Development & Version Control
| Tool | Purpose |
|---|---|
| Git | Version control |
| GitHub | Remote repository, PRs, Actions |

### Containerization
| Tool | Purpose |
|---|---|
| Docker | Application container |
| Docker Compose | Local multi-service orchestration (app + db) |

### CI/CD
| Tool | Purpose |
|---|---|
| GitHub Actions | Automated test, lint, build pipeline |

### Production Deployment
| Component | Purpose |
|---|---|
| Ubuntu/Linux | Server OS |
| Gunicorn (w/ uvicorn workers) | ASGI process manager |
| systemd | Service management |
| NGINX | Reverse proxy, TLS termination |
| HTTPS/SSL (Let's Encrypt) | Transport security |

### AI
| Component | Purpose |
|---|---|
| External LLM API (e.g. OpenAI, Gemini) | AI inference |
| Internal AI service layer | Prompt construction, response parsing, isolation |

### Explicitly Excluded Technologies
Redis, Kafka, Kubernetes, microservices, GraphQL, Celery, Elasticsearch, LangChain, LangGraph, vector databases, RAG — none of these may be introduced unless explicitly approved.

---

## 3. User Roles & Permissions

### 3.1 Student
| Category | Capabilities |
|---|---|
| Account | Register, login, manage profile |
| Education | Add/edit/delete education entries |
| Skills | Add/remove skills |
| Resume | Manage resume information |
| Jobs | Browse, search, filter, check eligibility |
| Applications | Apply to jobs, track application status and full transition history |
| AI | Resume analysis, resume improvement suggestions, job matching, interview prep generation |

### 3.2 Recruiter
| Category | Capabilities |
|---|---|
| Account | Register, login, manage recruiter profile |
| Company | Create company. Edit company profile (creator only). Other recruiters at the same company cannot edit company profile. Admin can edit/deactivate any company. |
| Company membership | A recruiter belongs to one company. Cannot switch companies while they have active jobs or unresolved applications. Historical records remain with the original company. |
| Jobs | Create, update, close jobs under their company (any recruiter at the company) |
| Applications | View applicants, review applications, change application status for their company's jobs |
| AI | Generate job descriptions |

### 3.3 Admin
| Category | Capabilities |
|---|---|
| Users | Manage all users (view, deactivate/reactivate). No role escalation via API. Admin created via seed/CLI only. |
| Companies | Manage all companies (view, edit, deactivate — soft-delete only) |
| Jobs | Manage all jobs (view, edit, close — soft-close only) |
| Applications | Manage all applications |
| Platform | Monitor activity, perform administrative actions |

---

## 4. AI Feature Requirements

All AI features must be **isolated** from core business logic. The core application must continue to function if the AI provider is unavailable.

### 4.1 Resume Analysis
- **Input**: Resume content, optional target job
- **Output**: Overall score, strengths, weaknesses, missing skills, keyword suggestions, improvement recommendations

### 4.2 Job Matching
- **Input**: Student profile/resume, job description/requirements
- **Output**: Match score, matching skills, missing skills, explanation, recommendation

### 4.3 Resume Improvement
- **Input**: Resume, target job
- **Output**: Improvement suggestions, relevant keywords, suggested changes

### 4.4 Interview Preparation
- **Input**: Job description
- **Output**: Technical questions, conceptual questions, coding questions, backend-related questions, preparation recommendations

### 4.5 Job Description Generation
- **Input**: Recruiter's job information (title, skills, requirements, etc.)
- **Output**: Professional, structured job description text

---

## 5. Non-Functional Requirements

### 5.1 Security
- All secrets loaded from environment variables; never committed to source control.
- Passwords hashed with bcrypt; never stored or logged in plaintext.
- JWT tokens with configurable expiration.
- RBAC enforced at the API layer.
- Resource ownership validated before mutation or access to private data.
- Admin role creation restricted to seed/CLI mechanism; registration API blocks `role=admin`.
- CORS configured explicitly.
- Input validated via Pydantic before reaching business logic.

### 5.2 Data Retention
- Applications and application status history are never hard-deleted.
- Users, companies, and jobs use soft-deactivation instead of deletion.
- ON DELETE RESTRICT protects recruitment records from accidental destruction.
- Application status transitions are recorded in an append-only audit trail.

### 5.3 Error Handling
Consistent JSON error responses for:
- Validation errors (422)
- Authentication errors (401)
- Authorization / forbidden errors (403)
- Not found (404)
- Conflict / duplicate (409)
- External service failures — AI (503 / 502)
- Unexpected server errors (500)

### 5.4 AI Response Contracts
- All AI features use strongly typed Pydantic request and response schemas.
- Raw LLM JSON is never returned directly to API clients.
- The AI service validates and parses provider responses before returning them.
- Only one concrete AI provider is implemented initially; selected via configuration.

### 5.5 Testing
- Unit tests for services and utilities.
- Integration tests for API endpoints via `TestClient`.
- Coverage targets: auth flows, RBAC, ownership, CRUD, application workflows, status transition history, AI service behavior.
- Tests must run against an isolated test database (Docker or SQLite for speed).

### 5.6 Documentation
The following documents are required:
| Document | Purpose |
|---|---|
| `README.md` | Project overview, quickstart, tech stack |
| `docs/requirements.md` | This document |
| `docs/architecture-proposal.md` | Detailed architecture and design |
| `docs/database-design.md` | Entity details, relationships, constraints |
| `docs/api-design.md` | Endpoint catalog with schemas |
| `docs/development-roadmap.md` | Phased delivery plan |

---

## 6. Development Principles

1. **Security first.** Every feature starts with auth/authz considerations.
2. **Keep secrets out of source code.** Use `.env` and environment variables.
3. **Keep business logic out of route handlers.** Routes delegate to service functions.
4. **Use database constraints** (unique, foreign key, check) instead of relying only on application logic.
5. **Validate external input.** Pydantic schemas for every request body and query.
6. **Use meaningful HTTP status codes.** No generic 200 for errors.
7. **Keep AI integration isolated.** AI service layer with clean interfaces.
8. **Write testable code.** Dependency injection, no global mutable state.
9. **Avoid unnecessary abstractions.** No abstract base classes or patterns without clear payoff.
10. **Avoid unnecessary technologies.** Only introduce what is approved.
11. **Do not implement future phases prematurely.** Build incrementally.
12. **Do not silently make major architectural decisions.** Flag and get approval.
13. **Prefer simple solutions** that are easy to maintain.
14. **Every feature must have a clear business purpose.**

---

## 7. Deployment Requirements

### Development
```
Docker Compose → FastAPI (uvicorn) + PostgreSQL
```

### Production
```
Internet → NGINX (TLS) → Gunicorn (uvicorn workers) → FastAPI → PostgreSQL
                                                      → External LLM API
```

### CI/CD Pipeline (GitHub Actions)
1. Install dependencies
2. Lint / format check
3. Run test suite
4. Build Docker image (on main branch)
