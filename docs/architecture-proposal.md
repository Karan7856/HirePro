# HirePro AI — Architecture Proposal

> **Status**: **APPROVED**  
> **Author**: Senior Software Architect  
> **Date**: 2026-08-15  
> **Version**: 0.2.0

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Actors & Permissions](#2-actors--permissions)
3. [Complete Feature Breakdown](#3-complete-feature-breakdown)
4. [Domain Model](#4-domain-model)
5. [Database Entities](#5-database-entities)
6. [Database Relationships](#6-database-relationships)
7. [API Module Structure](#7-api-module-structure)
8. [Authentication Architecture](#8-authentication-architecture)
9. [Authorization Model](#9-authorization-model)
10. [AI Service Architecture](#10-ai-service-architecture)
11. [Error Handling Strategy](#11-error-handling-strategy)
12. [Testing Strategy](#12-testing-strategy)
13. [Docker Strategy](#13-docker-strategy)
14. [CI/CD Strategy](#14-cicd-strategy)
15. [Deployment Architecture](#15-deployment-architecture)
16. [Recommended Folder Structure](#16-recommended-folder-structure)
17. [Development Phases](#17-development-phases)
18. [Architectural Risks](#18-architectural-risks)
19. [Questions & Ambiguities Requiring Approval](#19-questions--ambiguities-requiring-approval)

---

## 1. Product Overview

**HirePro AI** is a monolithic FastAPI backend that manages the full lifecycle of campus/placement recruitment:

```
Student registers → builds profile → browses jobs → checks eligibility → applies
Recruiter registers → creates company → posts jobs → reviews applicants → updates status
Admin oversees all entities and platform health
AI layer provides optional intelligence (resume analysis, matching, interview prep, etc.)
```

The system is designed as a **modular monolith** — a single deployable unit with clear internal module boundaries. This is the correct architecture for a project of this scope: it avoids the operational overhead of microservices while maintaining clean separation of concerns.

---

## 2. Actors & Permissions

### 2.1 Permission Matrix

| Resource / Action | Student (own) | Student (other) | Recruiter (own) | Recruiter (other) | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| View own profile | ✅ | ❌ | ✅ | ❌ | ✅ |
| Edit own profile | ✅ | ❌ | ✅ | ❌ | ✅ |
| View public job listings | ✅ | — | ✅ | — | ✅ |
| Apply to job | ✅ | ❌ | ❌ | ❌ | ❌ |
| View own applications | ✅ | ❌ | — | — | ✅ |
| Create job | ❌ | ❌ | ✅ | ❌ | ✅ |
| Edit own job | ❌ | ❌ | ✅ | ❌ | ✅ |
| View applicants for company's jobs | ❌ | ❌ | ✅ | ❌ | ✅ |
| Change application status | ❌ | ❌ | ✅ (company's jobs) | ❌ | ✅ |
| Manage users | ❌ | ❌ | ❌ | ❌ | ✅ |
| Use AI features | ✅ (student AI) | ❌ | ✅ (recruiter AI) | ❌ | ✅ |

### 2.2 Role Hierarchy

```
ADMIN  →  full platform access (superuser)
RECRUITER  →  company/job/application management for own resources
STUDENT  →  profile/resume/application management for own resources
```

Roles are **mutually exclusive** — a user has exactly one role. This avoids multi-role complexity. If a person is both a student and a recruiter, they create separate accounts.

---

## 3. Complete Feature Breakdown

### 3.1 Authentication & Account Management
- User registration (student or recruiter; admin created via seed/CLI)
- Login with email + password → JWT access token
- Token refresh (optional, see Q19.1)
- Password change (authenticated)
- Profile retrieval and update

### 3.2 Student Features
- **Profile**: Name, email, phone, date of birth, bio
- **Education**: Multiple entries (institution, degree, field of study, start/end dates, GPA/percentage)
- **Skills**: Tag-like list of skills associated with the student
- **Resume**: Structured resume data (stored as text/JSON, not file upload initially — see Q19.4)
- **Job browsing**: List open jobs with search (by title, company, skills) and filters (by location, job type, salary range, eligibility)
- **Eligibility check**: Compare student profile against job requirements before applying
- **Apply**: Submit application to a job (one application per student per job)
- **Track applications**: View own applications and their full status transition history

### 3.3 Recruiter Features
- **Profile**: Name, email, phone, designation
- **Company management**: Create company; edit company profile (creator only); other recruiters at the same company cannot edit company profile
- **Job management**: Create, update, close jobs under their company (any recruiter at the company)
- **Eligibility criteria**: Min GPA, required skills, allowed branches/degrees, graduation year range
- **View applicants**: List and review applications for their company's jobs
- **Application status**: Move applications through a defined workflow (see §3.5) for their company's jobs

### 3.4 Admin Features
- **User management**: List, view, deactivate/reactivate users (no role escalation via API — see §9.4)
- **Company management**: View/edit/deactivate any company (soft-delete only — see §6.4)
- **Job management**: View/edit/close any job (soft-close only — see §6.4)
- **Application management**: View any application, override status if needed
- **Platform monitoring**: Basic stats (user count, job count, application count by status)

### 3.5 Application Status Workflow

```
PENDING → REVIEWING → SHORTLISTED → INTERVIEW → SELECTED → REJECTED
                  ↘                           ↗
                    ────────── REJECTED ──────
```

Valid transitions:
| From | Allowed To |
|---|---|
| `PENDING` | `REVIEWING`, `REJECTED` |
| `REVIEWING` | `SHORTLISTED`, `REJECTED` |
| `SHORTLISTED` | `INTERVIEW`, `REJECTED` |
| `INTERVIEW` | `SELECTED`, `REJECTED` |
| `SELECTED` | (terminal) |
| `REJECTED` | (terminal) |

`WITHDRAWN` — student-initiated cancellation, allowed from any non-terminal state.

**Every status transition must create an `ApplicationStatusHistory` record** capturing the old status, new status, who made the change, and when. This enables full audit trail and allows students to see their application journey.

### 3.6 AI Features (see §10 for architecture)
- Resume analysis (student)
- Job matching (student)
- Resume improvement (student)
- Interview preparation (student)
- Job description generation (recruiter)

---

## 4. Domain Model

After analyzing the requirements, the following **9 core entities** emerge. I rejected several potential entities and explain why below.

### 4.1 Final Entity List

| Entity | Justification |
|---|---|
| **User** | Central identity for auth. Holds role, credentials, common fields. |
| **StudentProfile** | Student-specific data (including `current_gpa` and `graduation_year` for eligibility). 1:1 with User where role=STUDENT. |
| **RecruiterProfile** | Recruiter-specific data. 1:1 with User where role=RECRUITER. |
| **Company** | Organizational entity that recruiter belongs to and jobs are posted under. |
| **Job** | A position posted by a recruiter under a company. |
| **Application** | A student's application to a specific job. |
| **ApplicationStatusHistory** | Audit trail for every application status transition. Captures old/new status, who changed it, and when. |
| **Education** | A student's education entry (degree, institution, dates, GPA). Historical academic record — NOT used for eligibility. |
| **Skill** | A normalized skill tag. Shared across students and jobs via junction tables. |

### 4.2 Rejected / Deferred Entities

| Considered | Decision | Reasoning |
|---|---|---|
| **Resume** (separate table) | ❌ Rejected | Resume content is a text field on `StudentProfile`. No need for a separate table unless we support multiple resume versions — deferred. |
| **AIAnalysisResult** (persisted) | ❌ Rejected for now | AI results are returned synchronously and not stored. Persisting them adds storage cost with unclear retrieval value. Can be added later if users want history. |
| **Notification** | ❌ Deferred | Not in requirements. Can be added in a later phase. |

### 4.3 Student Eligibility Design

**Problem**: The original design had ambiguity between `StudentProfile.graduation_year` and `Education.gpa` for eligibility checks.

**Resolution**: Eligibility fields live on `StudentProfile`:

| Field | Location | Purpose |
|---|---|---|
| `current_gpa` | `StudentProfile` | Student's current cumulative GPA for placement eligibility |
| `graduation_year` | `StudentProfile` | Expected graduation year for placement eligibility |
| `gpa` | `Education` | GPA for a specific degree/institution — historical academic record |

**Rule**: Job eligibility checks (`min_gpa`, `allowed_graduation_years`) compare against `StudentProfile.current_gpa` and `StudentProfile.graduation_year`, NOT against individual `Education` entries.

### 4.4 Domain Model Diagram

```mermaid
erDiagram
    USER ||--o| STUDENT_PROFILE : "has (if student)"
    USER ||--o| RECRUITER_PROFILE : "has (if recruiter)"
    RECRUITER_PROFILE }o--|| COMPANY : "belongs to"
    COMPANY ||--o{ JOB : "has"
    JOB }o--|| RECRUITER_PROFILE : "posted by"
    JOB }o--o{ SKILL : "requires (job_skills)"
    STUDENT_PROFILE }o--o{ SKILL : "possesses (student_skills)"
    STUDENT_PROFILE ||--o{ EDUCATION : "has"
    STUDENT_PROFILE ||--o{ APPLICATION : "submits"
    JOB ||--o{ APPLICATION : "receives"
    APPLICATION ||--o{ APPLICATION_STATUS_HISTORY : "has"
```

---

## 5. Database Entities

### 5.1 `users`

The central identity table. Holds authentication credentials and the role discriminator.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Avoids sequential ID enumeration |
| `email` | `VARCHAR(255)` | NOT NULL, UNIQUE | Login identifier |
| `hashed_password` | `VARCHAR(255)` | NOT NULL | bcrypt hash |
| `full_name` | `VARCHAR(150)` | NOT NULL | Display name |
| `role` | `VARCHAR(20)` | NOT NULL, CHECK IN (`student`, `recruiter`, `admin`) | Role discriminator |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `true` | Soft-disable account |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | Auto-updated via trigger or app |

**Indexes**: `UNIQUE(email)`, `INDEX(role)`, `INDEX(is_active)`

---

### 5.2 `student_profiles`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK | |
| `user_id` | `UUID` | FK → `users.id`, UNIQUE, NOT NULL, ON DELETE RESTRICT | 1:1 with user. RESTRICT prevents accidental user deletion that would orphan audit data. |
| `phone` | `VARCHAR(20)` | | Optional |
| `date_of_birth` | `DATE` | | Optional |
| `bio` | `TEXT` | | Short bio / summary |
| `resume_content` | `TEXT` | | Plaintext or markdown resume |
| `current_gpa` | `NUMERIC(4,2)` | CHECK `current_gpa >= 0 AND current_gpa <= 10.0` | Current cumulative GPA for placement eligibility |
| `graduation_year` | `INTEGER` | | Expected graduation year for placement eligibility |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |

**Indexes**: `UNIQUE(user_id)`

> **Eligibility note**: `current_gpa` and `graduation_year` on this table are the **authoritative fields** for job eligibility checks. The `Education` table stores historical academic records per-institution and is NOT used for eligibility comparisons.

---

### 5.3 `recruiter_profiles`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK | |
| `user_id` | `UUID` | FK → `users.id`, UNIQUE, NOT NULL, ON DELETE RESTRICT | 1:1 with user. RESTRICT prevents accidental user deletion. |
| `phone` | `VARCHAR(20)` | | Optional |
| `designation` | `VARCHAR(100)` | | Job title at company |
| `company_id` | `UUID` | FK → `companies.id`, ON DELETE SET NULL | Nullable — recruiter may not have a company yet |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |

**Indexes**: `UNIQUE(user_id)`, `INDEX(company_id)`

---

### 5.4 `companies`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK | |
| `name` | `VARCHAR(200)` | NOT NULL, UNIQUE | Company names must be unique |
| `description` | `TEXT` | | |
| `website` | `VARCHAR(500)` | | |
| `industry` | `VARCHAR(100)` | | |
| `location` | `VARCHAR(200)` | | HQ or primary location |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `true` | Admin can deactivate |
| `created_by` | `UUID` | FK → `users.id` | Tracks who created it |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |

**Indexes**: `UNIQUE(name)`, `INDEX(is_active)`

---

### 5.5 `jobs`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK | |
| `title` | `VARCHAR(200)` | NOT NULL | |
| `description` | `TEXT` | NOT NULL | Full job description |
| `company_id` | `UUID` | FK → `companies.id`, NOT NULL, ON DELETE RESTRICT | RESTRICT — cannot delete a company that has jobs. Deactivate instead. |
| `recruiter_id` | `UUID` | FK → `recruiter_profiles.id`, NOT NULL, ON DELETE RESTRICT | RESTRICT — cannot delete recruiter profile with posted jobs. |
| `location` | `VARCHAR(200)` | | |
| `job_type` | `VARCHAR(30)` | CHECK IN (`full_time`, `part_time`, `internship`, `contract`) | |
| `salary_min` | `NUMERIC(12,2)` | | |
| `salary_max` | `NUMERIC(12,2)` | CHECK `salary_max >= salary_min` | |
| `min_gpa` | `NUMERIC(4,2)` | | Eligibility: minimum GPA. Compared against `student_profiles.current_gpa`. |
| `allowed_graduation_years` | `INTEGER[]` | | PostgreSQL native array. Intentional PG-specific design (approved). |
| `status` | `VARCHAR(20)` | NOT NULL, DEFAULT `open`, CHECK IN (`open`, `closed`) | `closed` = soft-close, job data retained |
| `application_deadline` | `TIMESTAMPTZ` | | |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |

**Indexes**: `INDEX(company_id)`, `INDEX(recruiter_id)`, `INDEX(status)`, `INDEX(job_type)`, `INDEX(created_at DESC)`

> **Eligibility matching**: `min_gpa` is compared against `student_profiles.current_gpa`. `allowed_graduation_years` is checked against `student_profiles.graduation_year` using PostgreSQL's `ANY()` operator.

---

### 5.6 `skills`

A **normalized skill lookup table**. Skills are shared entities — the same skill (e.g., "Python") can be referenced by many students and many jobs.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK | |
| `name` | `VARCHAR(100)` | NOT NULL, UNIQUE | Lowercase, normalized |

**Indexes**: `UNIQUE(name)`

---

### 5.7 `student_skills` (Junction Table)

| Column | Type | Constraints |
|---|---|---|
| `student_profile_id` | `UUID` | FK → `student_profiles.id`, ON DELETE CASCADE |
| `skill_id` | `UUID` | FK → `skills.id`, ON DELETE RESTRICT |
| **PK** | | `(student_profile_id, skill_id)` |

> Skill FK uses RESTRICT — a skill cannot be deleted if any student references it. Remove associations first.

---

### 5.8 `job_skills` (Junction Table)

| Column | Type | Constraints |
|---|---|---|
| `job_id` | `UUID` | FK → `jobs.id`, ON DELETE CASCADE |
| `skill_id` | `UUID` | FK → `skills.id`, ON DELETE RESTRICT |
| **PK** | | `(job_id, skill_id)` |

> Skill FK uses RESTRICT — a skill cannot be deleted if any job references it.

---

### 5.9 `education`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK | |
| `student_profile_id` | `UUID` | FK → `student_profiles.id`, NOT NULL, ON DELETE CASCADE | |
| `institution` | `VARCHAR(200)` | NOT NULL | |
| `degree` | `VARCHAR(100)` | NOT NULL | e.g., "B.Tech", "M.Sc" |
| `field_of_study` | `VARCHAR(150)` | | e.g., "Computer Science" |
| `start_date` | `DATE` | | |
| `end_date` | `DATE` | | Null = currently pursuing |
| `gpa` | `NUMERIC(4,2)` | CHECK `gpa >= 0 AND gpa <= 10.0` | |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |

**Indexes**: `INDEX(student_profile_id)`

---

### 5.10 `applications`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK | |
| `student_profile_id` | `UUID` | FK → `student_profiles.id`, NOT NULL, ON DELETE RESTRICT | RESTRICT — applications are recruitment records and must be retained. |
| `job_id` | `UUID` | FK → `jobs.id`, NOT NULL, ON DELETE RESTRICT | RESTRICT — cannot delete a job that has applications. Close it instead. |
| `status` | `VARCHAR(20)` | NOT NULL, DEFAULT `pending`, CHECK IN (`pending`, `reviewing`, `shortlisted`, `interview`, `selected`, `rejected`, `withdrawn`) | |
| `cover_letter` | `TEXT` | | Optional cover message |
| `applied_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |

**Constraints**: `UNIQUE(student_profile_id, job_id)` — a student can apply to a job only once.

**Indexes**: `UNIQUE(student_profile_id, job_id)`, `INDEX(job_id)`, `INDEX(status)`, `INDEX(applied_at DESC)`

---

### 5.11 `application_status_history`

Audit trail for every application status transition.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK | |
| `application_id` | `UUID` | FK → `applications.id`, NOT NULL, ON DELETE RESTRICT | RESTRICT — history must survive even if application deletion is attempted (which is itself restricted). |
| `old_status` | `VARCHAR(20)` | | NULL for the initial `pending` record |
| `new_status` | `VARCHAR(20)` | NOT NULL | The status being transitioned to |
| `changed_by` | `UUID` | FK → `users.id`, NOT NULL, ON DELETE RESTRICT | The user who made the change (student for withdraw, recruiter for status updates) |
| `changed_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `now()` | |

**Indexes**: `INDEX(application_id)`, `INDEX(changed_at DESC)`

> **Data retention**: This table is append-only. Records are never updated or deleted. ON DELETE RESTRICT on all FKs ensures audit integrity.

---

## 6. Database Relationships

### 6.1 Relationship Summary

| Relationship | Type | Implementation |
|---|---|---|
| User ↔ StudentProfile | One-to-One | `student_profiles.user_id` FK UNIQUE to `users.id` |
| User ↔ RecruiterProfile | One-to-One | `recruiter_profiles.user_id` FK UNIQUE to `users.id` |
| RecruiterProfile → Company | Many-to-One | `recruiter_profiles.company_id` FK to `companies.id` |
| Company → Jobs | One-to-Many | `jobs.company_id` FK to `companies.id` |
| RecruiterProfile → Jobs | One-to-Many | `jobs.recruiter_id` FK to `recruiter_profiles.id` |
| StudentProfile ↔ Skills | Many-to-Many | `student_skills` junction table |
| Job ↔ Skills | Many-to-Many | `job_skills` junction table |
| StudentProfile → Education | One-to-Many | `education.student_profile_id` FK |
| StudentProfile → Applications | One-to-Many | `applications.student_profile_id` FK |
| Job → Applications | One-to-Many | `applications.job_id` FK |
| Application → ApplicationStatusHistory | One-to-Many | `application_status_history.application_id` FK |

### 6.2 Ownership Rules

| Entity | Owner | Rule |
|---|---|---|
| StudentProfile | The user (role=student) | `student_profiles.user_id == current_user.id` |
| RecruiterProfile | The user (role=recruiter) | `recruiter_profiles.user_id == current_user.id` |
| Company (profile edit) | The creating recruiter only (and admin) | `companies.created_by == current_user.id` |
| Company (job management) | Any recruiter belonging to the company | `recruiter_profiles.company_id == company.id` |
| Job | Any recruiter at the same company (and admin) | `job.company_id == current_user.recruiter_profile.company_id` |
| Application (student access) | The applying student | `applications.student_profile_id == current_user.student_profile.id` |
| Application (recruiter access) | Any recruiter at the job's company (and admin) | `job.company_id == current_user.recruiter_profile.company_id` |
| Education | The student | `education.student_profile_id == current_user.student_profile.id` |

> **Company/Recruiter ownership distinction (approved)**:
> - A recruiter belongs to **one company** (`recruiter_profiles.company_id`).
> - **Company profile editing** (name, description, website, etc.) is restricted to the **creator** (`companies.created_by`) and admins.
> - **Job management** (create, update, close jobs under the company) is allowed for **any recruiter belonging to that company**.
> - **Application access** (view applicants, review applications, change application status) is allowed for **any recruiter belonging to the job's company**.
> - Other recruiters at the same company **cannot** edit company profile information unless explicitly authorized in a future phase.
>
> **Recruiter company switching (approved)**:
> - A recruiter **cannot** switch companies while they have active (open) jobs or unresolved (non-terminal) applications associated with their current company.
> - Historical recruitment records (closed jobs, resolved applications, status history) remain associated with their original company.
> - Once all recruitment responsibilities are resolved (jobs closed, applications in terminal state), the recruiter's `company_id` may be updated.
> - This is enforced at the application/service layer, not via database constraints.

### 6.3 Cascade / Retention Rules

The cascade strategy is designed to **protect recruitment and audit data**. Destructive cascades are replaced with RESTRICT or soft-deletion where important records would be lost.

| FK Relationship | ON DELETE | Rationale |
|---|---|---|
| `student_profiles.user_id` → `users.id` | **RESTRICT** | Cannot delete a user that has a student profile (which may have applications). Deactivate instead. |
| `recruiter_profiles.user_id` → `users.id` | **RESTRICT** | Cannot delete a user that has a recruiter profile (which may have posted jobs). Deactivate instead. |
| `recruiter_profiles.company_id` → `companies.id` | **SET NULL** | Company deactivated/removed → recruiter loses company association but profile survives. |
| `jobs.company_id` → `companies.id` | **RESTRICT** | Cannot delete a company that has jobs. Deactivate the company instead. |
| `jobs.recruiter_id` → `recruiter_profiles.id` | **RESTRICT** | Cannot delete a recruiter profile that has posted jobs. |
| `applications.student_profile_id` → `student_profiles.id` | **RESTRICT** | Applications are recruitment records. Cannot delete student profile with applications. Deactivate user instead. |
| `applications.job_id` → `jobs.id` | **RESTRICT** | Cannot delete a job that has applications. Close the job instead. |
| `application_status_history.application_id` → `applications.id` | **RESTRICT** | Audit trail must be preserved. Applications themselves are also RESTRICT-protected. |
| `application_status_history.changed_by` → `users.id` | **RESTRICT** | Cannot delete a user who has made status changes. Deactivate instead. |
| `education.student_profile_id` → `student_profiles.id` | **CASCADE** | If a student profile is somehow removed (admin override), education history has no standalone value. |
| `student_skills.student_profile_id` → `student_profiles.id` | **CASCADE** | Skill associations are lightweight and have no audit value. |
| `student_skills.skill_id` → `skills.id` | **RESTRICT** | Cannot delete a skill referenced by students. |
| `job_skills.job_id` → `jobs.id` | **CASCADE** | If a job is somehow removed, its skill requirements go with it. |
| `job_skills.skill_id` → `skills.id` | **RESTRICT** | Cannot delete a skill referenced by jobs. |

### 6.4 Soft-Deletion / Deactivation Strategy

Instead of hard-deleting important entities, use soft-deactivation:

| Entity | Mechanism | Effect |
|---|---|---|
| **User** | `users.is_active = false` | User cannot login. Profile and associated data retained. |
| **Company** | `companies.is_active = false` | Company hidden from listings. Jobs under it should be closed. Data retained. |
| **Job** | `jobs.status = 'closed'` | Job no longer accepts applications. Existing applications and history retained. |
| **Application** | No soft-delete | Applications are never deleted. Status workflow handles lifecycle. |

---

## 7. API Module Structure

### 7.1 Module Overview

| Module | Prefix | Responsibility |
|---|---|---|
| `auth` | `/api/v1/auth` | Registration, login, token management |
| `users` | `/api/v1/users` | User account management (admin-focused) |
| `students` | `/api/v1/students` | Student profile, education, skills, resume |
| `recruiters` | `/api/v1/recruiters` | Recruiter profile management |
| `companies` | `/api/v1/companies` | Company CRUD |
| `jobs` | `/api/v1/jobs` | Job CRUD, search, eligibility |
| `applications` | `/api/v1/applications` | Apply, track, review, status changes |
| `ai` | `/api/v1/ai` | All AI feature endpoints |

All endpoints are versioned under `/api/v1/` to allow future evolution.

### 7.2 Endpoint Catalog

#### Auth (`/api/v1/auth`)

| Method | Path | Purpose | Auth | Role |
|---|---|---|---|---|
| POST | `/register` | Register new student or recruiter | ❌ | — |
| POST | `/login` | Authenticate, return JWT | ❌ | — |
| GET | `/me` | Get current user info | ✅ | any |
| PUT | `/me/password` | Change own password | ✅ | any |

#### Users (`/api/v1/users`) — Admin only

| Method | Path | Purpose | Auth | Role |
|---|---|---|---|---|
| GET | `/` | List all users (paginated, filterable) | ✅ | admin |
| GET | `/stats` | Platform statistics | ✅ | admin |
| GET | `/{user_id}` | Get user details | ✅ | admin |
| PATCH | `/{user_id}` | Update user (deactivate/reactivate only — no role changes) | ✅ | admin |

> **⚠️ Route ordering (approved)**: Static routes like `GET /stats` **must be registered before** parameterized routes like `GET /{user_id}` in FastAPI router code. Otherwise, FastAPI will try to parse `"stats"` as a `user_id` UUID and return a 422 validation error. This applies to any router with both static and parameterized paths.

> **⚠️ Admin privilege control (approved)**: The `PATCH /{user_id}` endpoint allows deactivation/reactivation of users only. It does **NOT** allow role changes (e.g., promoting a user to admin). Admin users are created exclusively via the seed/CLI mechanism (`python -m app.seed_admin`). This prevents accidental or malicious privilege escalation through the API.

#### Students (`/api/v1/students`)

| Method | Path | Purpose | Auth | Role |
|---|---|---|---|---|
| GET | `/me/profile` | Get own student profile | ✅ | student |
| PUT | `/me/profile` | Update own student profile | ✅ | student |
| GET | `/me/education` | List own education entries | ✅ | student |
| POST | `/me/education` | Add education entry | ✅ | student |
| PUT | `/me/education/{id}` | Update education entry | ✅ | student |
| DELETE | `/me/education/{id}` | Delete education entry | ✅ | student |
| GET | `/me/skills` | List own skills | ✅ | student |
| PUT | `/me/skills` | Set/replace skill list | ✅ | student |
| GET | `/me/resume` | Get resume content | ✅ | student |
| PUT | `/me/resume` | Update resume content | ✅ | student |
| GET | `/me/applications` | List own applications (with status history) | ✅ | student |

> **Design decision**: Student endpoints use `/me/` prefix instead of `/{student_id}/` because students only access their own resources. This makes ownership implicit and simplifies authorization. Admin access to student data goes through `/users/{id}` or dedicated admin endpoints.

#### Recruiters (`/api/v1/recruiters`)

| Method | Path | Purpose | Auth | Role |
|---|---|---|---|---|
| GET | `/me/profile` | Get own recruiter profile | ✅ | recruiter |
| PUT | `/me/profile` | Update own recruiter profile | ✅ | recruiter |
| GET | `/me/jobs` | List own posted jobs | ✅ | recruiter |

#### Companies (`/api/v1/companies`)

| Method | Path | Purpose | Auth | Role |
|---|---|---|---|---|
| POST | `/` | Create company | ✅ | recruiter |
| GET | `/` | List companies | ✅ | any |
| GET | `/{company_id}` | Get company details | ✅ | any |
| PUT | `/{company_id}` | Update company profile | ✅ | recruiter (creator) / admin |
| PATCH | `/{company_id}/deactivate` | Deactivate company (soft-delete) | ✅ | admin |

#### Jobs (`/api/v1/jobs`)

| Method | Path | Purpose | Auth | Role |
|---|---|---|---|---|
| POST | `/` | Create job | ✅ | recruiter |
| GET | `/` | List/search/filter jobs | ✅ | any |
| GET | `/{job_id}` | Get job details | ✅ | any |
| PUT | `/{job_id}` | Update job | ✅ | recruiter (same company) / admin |
| PATCH | `/{job_id}/close` | Close job | ✅ | recruiter (same company) / admin |
| GET | `/{job_id}/eligibility` | Check own eligibility | ✅ | student |
| GET | `/{job_id}/applicants` | List applicants for job | ✅ | recruiter (same company) / admin |

#### Applications (`/api/v1/applications`)

| Method | Path | Purpose | Auth | Role |
|---|---|---|---|---|
| POST | `/` | Apply to job | ✅ | student |
| GET | `/{application_id}` | Get application details (includes status history) | ✅ | student (owner) / recruiter (same company) / admin |
| GET | `/{application_id}/history` | Get full status transition history | ✅ | student (owner) / recruiter (same company) / admin |
| PATCH | `/{application_id}/status` | Change application status (creates history record) | ✅ | recruiter (same company) / admin |
| PATCH | `/{application_id}/withdraw` | Withdraw application (creates history record) | ✅ | student (owner) |

#### AI (`/api/v1/ai`)

| Method | Path | Purpose | Auth | Role |
|---|---|---|---|---|
| POST | `/resume/analyze` | Analyze resume | ✅ | student |
| POST | `/resume/improve` | Get improvement suggestions | ✅ | student |
| POST | `/job-match` | Match student to job | ✅ | student |
| POST | `/interview-prep` | Generate interview questions | ✅ | student |
| POST | `/job-description/generate` | Generate job description | ✅ | recruiter |

---

## 8. Authentication Architecture

### 8.1 Flow

```
1. Registration
   Client → POST /auth/register { email, password, full_name, role }
   Server → validate → hash password (bcrypt) → insert user + profile → return user info

2. Login
   Client → POST /auth/login { email, password } (form data, OAuth2 spec)
   Server → find user → verify bcrypt hash → generate JWT → return { access_token, token_type }

3. Authenticated Request
   Client → GET /students/me/profile
            Authorization: Bearer <jwt_token>
   Server → decode JWT → extract user_id + role → load user → inject as dependency

4. Authorization
   Route dependency checks:
   - Is user authenticated? (401 if not)
   - Does user have required role? (403 if not)
   - Does user own the resource? (403 if not)
```

### 8.2 JWT Payload

```json
{
  "sub": "user-uuid-here",
  "role": "student",
  "exp": 1692000000,
  "iat": 1691990000
}
```

- `sub`: User ID (UUID string)
- `role`: User role (avoids a DB query on every request to check role)
- `exp`: Expiration timestamp
- `iat`: Issued-at timestamp

### 8.3 Security Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Password hashing | bcrypt via `passlib[bcrypt]` | Industry standard, work-factor tunable |
| Token algorithm | HS256 | Sufficient for monolith (single signing + verifying party). RS256 only needed for distributed verification. |
| Token expiry | 30 minutes (configurable via env) | Reasonable default; no refresh token in Phase 1 |
| Token storage | Client-side (header) | Stateless; no server-side session store needed |
| Secret key | Loaded from `SECRET_KEY` env var | Never hardcoded |

### 8.4 FastAPI Integration

```python
# Dependency chain (conceptual)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Decode JWT, load user from DB, return User model."""

async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Ensure user.is_active == True."""

def require_role(*roles: str):
    """Return a dependency that checks current_user.role in roles."""

def require_ownership(resource_owner_id_extractor):
    """Return a dependency that checks current_user owns the resource."""
```

---

## 9. Authorization Model

### 9.1 Three Layers of Access Control

```
Layer 1: Authentication  →  Is the user logged in?  (401 Unauthorized)
Layer 2: Role Check      →  Does the user's role permit this action?  (403 Forbidden)
Layer 3: Ownership Check →  Does the user own this specific resource?  (403 Forbidden)
```

### 9.2 Implementation Strategy

Authorization is implemented via **FastAPI dependencies**, not decorators or middleware. This is idiomatic FastAPI and makes the authorization requirements visible in each route's function signature.

```python
# Example: Any recruiter at the job's company (or admin) can see applicants
@router.get("/{job_id}/applicants")
async def get_applicants(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    job = await job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if current_user.role == "admin":
        pass  # admin can see all
    elif current_user.role == "recruiter":
        if job.company_id != current_user.recruiter_profile.company_id:
            raise HTTPException(403, "Not your company's job")
    else:
        raise HTTPException(403, "Students cannot view applicants")
    # ... proceed
```

### 9.3 Ownership Patterns

| Pattern | Example |
|---|---|
| Direct ownership | Student viewing own profile: `profile.user_id == current_user.id` |
| Company-scoped ownership | Recruiter viewing applicants for a job: `job.company_id == current_user.recruiter_profile.company_id` |
| Admin bypass | Admin can access/modify any resource regardless of ownership |

### 9.4 Admin Privilege Control

Admin role assignment is **explicitly controlled** and never exposed through regular APIs:

| Action | Mechanism | Allowed Via |
|---|---|---|
| Create initial admin | Seed script: `python -m app.seed_admin` | CLI only (credentials from env vars) |
| Promote user to admin | Not implemented in Phase 1 | Manual DB operation or future admin-only CLI |
| Admin via registration API | **Blocked** | Registration endpoint rejects `role=admin` |
| Admin via user update API | **Blocked** | `PATCH /users/{id}` does not accept role changes |

> **Rationale**: Unrestricted admin promotion through the API is a privilege escalation vulnerability. Admin creation is an infrastructure operation, not a user-facing feature.

---

## 10. AI Service Architecture

### 10.1 Design Principles

1. **Isolation**: AI logic lives in a dedicated service layer (`app/services/ai/`). No AI imports or LLM calls in routes or core services.
2. **Graceful degradation**: If the AI provider is down, all non-AI features continue working. AI endpoints return 503 with a clear message.
3. **Provider abstraction**: An `AIProvider` interface (protocol) abstracts the LLM API. Swapping providers requires changing only the provider implementation. **Only one concrete provider is implemented initially** — selected via configuration (`AI_PROVIDER` env var).
4. **Strongly typed I/O (approved)**: All AI features use **strongly typed Pydantic request and response schemas**. Raw LLM JSON is never returned directly to API clients. The AI service must validate and parse the provider response into the appropriate Pydantic response model before returning it.
5. **No persistence of AI results** in Phase 1. Results are computed and returned synchronously.
6. **Single provider initially (approved)**: The architecture is provider-agnostic at the protocol level, but only **one concrete provider** (chosen based on developer access — OpenAI or Gemini) is implemented in Phase 4. Additional providers can be added later without architectural changes.

### 10.2 Architecture Diagram

```
Route Layer (ai_router.py)
    │  - Receives typed Pydantic request model
    │  - Returns typed Pydantic response model
    ▼
AI Service Layer (ai_service.py)
    │  - Validates input (Pydantic request schema)
    │  - Constructs prompt from templates
    │  - Calls provider
    │  - Parses raw LLM response into Pydantic response schema
    │  - NEVER returns raw LLM JSON to the caller
    ▼
AI Provider (providers/<configured_provider>.py)
    │  - Implements AIProvider protocol
    │  - Handles HTTP call to external API
    │  - Handles retries, timeouts, errors
    ▼
External LLM API (configured via AI_PROVIDER + AI_API_KEY env vars)
```

### 10.3 Provider Protocol

```python
class AIProvider(Protocol):
    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Send prompt to LLM and return raw text response."""
        ...
```

> **Note**: The provider returns raw text. It is the **AI service layer's** responsibility to parse this into a Pydantic model. The provider is intentionally simple.

### 10.4 Prompt Management

Prompts are stored as **string templates** in `app/services/ai/prompts/`. Each AI feature has its own prompt template file:

```
app/services/ai/prompts/
├── resume_analysis.py
├── resume_improvement.py
├── job_matching.py
├── interview_prep.py
└── job_description.py
```

Each module exports a function: `build_prompt(input_data: PydanticModel) -> str`

All prompts instruct the LLM to respond in **structured JSON format** matching the expected Pydantic response schema.

### 10.5 Response Parsing & Contracts (Approved)

This is a critical architectural rule:

1. The LLM is instructed (via system prompt) to return JSON matching a specific structure.
2. The AI service layer parses the raw JSON string using `PydanticModel.model_validate_json()`.
3. If parsing succeeds, the typed Pydantic response model is returned to the route layer.
4. If parsing fails, the service raises a structured error (502 — bad upstream response).
5. **Raw LLM output is NEVER returned directly to API clients.** The response contract is always the Pydantic schema.

Example flow:
```
LLM returns: '{"score": 85, "strengths": ["Python", "FastAPI"], ...}'
             ↓
AI service:  ResumeAnalysisResponse.model_validate_json(raw_response)
             ↓
Route layer: Returns validated ResumeAnalysisResponse (200 OK)
```

### 10.6 Error Handling for AI

| Scenario | HTTP Status | Behavior |
|---|---|---|
| AI provider unreachable | 503 | "AI service temporarily unavailable" |
| AI provider returns error | 502 | "AI service returned an error" |
| AI response unparseable (contract violation) | 502 | "Could not parse AI response" |
| AI feature disabled (no API key) | 503 | "AI features are not configured" |
| Rate limit exceeded | 429 | "AI rate limit exceeded, try again later" |

---

## 11. Error Handling Strategy

### 11.1 Consistent Error Response Format

All errors return the same JSON structure:

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "status_code": 422
}
```

For validation errors (Pydantic), FastAPI's default 422 format is preserved as it's well-understood by API consumers.

### 11.2 Error Categories & Status Codes

| Category | Status Code | `error_code` Example |
|---|---|---|
| Validation error | 422 | `VALIDATION_ERROR` |
| Invalid credentials | 401 | `INVALID_CREDENTIALS` |
| Token expired / invalid | 401 | `TOKEN_EXPIRED`, `INVALID_TOKEN` |
| Insufficient permissions | 403 | `FORBIDDEN` |
| Resource not found | 404 | `NOT_FOUND` |
| Duplicate / conflict | 409 | `ALREADY_EXISTS`, `DUPLICATE_APPLICATION` |
| Invalid state transition | 409 | `INVALID_STATUS_TRANSITION` |
| AI service unavailable | 503 | `AI_UNAVAILABLE` |
| AI response error | 502 | `AI_RESPONSE_ERROR` |
| Unexpected server error | 500 | `INTERNAL_ERROR` |

### 11.3 Implementation

- Custom exception classes inheriting from a base `AppException`.
- A global exception handler registered on the FastAPI app that catches `AppException` subclasses and returns the consistent JSON format.
- Unhandled exceptions caught by a catch-all handler returning 500 with a generic message (no stack trace in response body; stack trace logged server-side).

---

## 12. Testing Strategy

### 12.1 Test Structure

```
tests/
├── conftest.py              # Shared fixtures: test DB, client, auth helpers
├── test_auth.py             # Registration, login, token validation
├── test_students.py         # Student profile, education, skills, resume
├── test_recruiters.py       # Recruiter profile
├── test_companies.py        # Company CRUD
├── test_jobs.py             # Job CRUD, search, eligibility
├── test_applications.py     # Apply, status transitions, withdraw
├── test_ai.py               # AI endpoint behavior (mocked provider)
└── test_authorization.py    # Cross-cutting RBAC and ownership tests
```

### 12.2 Test Database Strategy

- Tests run against a **separate PostgreSQL database** spun up via Docker Compose (or the same Docker Compose with a test DB).
- Each test function gets a **fresh transaction that is rolled back** after the test — fast isolation without full DB recreation.
- Alternative: SQLite in-memory for faster unit tests. However, PostgreSQL-specific features (arrays, JSON) may not work. Recommend PostgreSQL for integration tests.

### 12.3 Fixtures

```python
# conftest.py — conceptual
@pytest.fixture
async def db_session():
    """Provide a transactional DB session that rolls back after each test."""

@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden DB dependency."""

@pytest.fixture
def student_token(client):
    """Register + login a student, return JWT token."""

@pytest.fixture
def recruiter_token(client):
    """Register + login a recruiter, return JWT token."""

@pytest.fixture
def admin_token(client):
    """Login as seeded admin, return JWT token."""
```

### 12.4 Coverage Areas

| Area | What to Test |
|---|---|
| Auth | Register (success, duplicate email), login (success, wrong password), token decode |
| RBAC | Student can't create job, recruiter can't apply, admin can do everything |
| Ownership | Student A can't see Student B's applications |
| CRUD | Create, read, update, delete for each entity |
| Business rules | Eligibility check, application uniqueness, status transitions |
| AI | Mock LLM provider; test prompt construction, response parsing, error handling |
| Validation | Missing fields, invalid types, out-of-range values |

### 12.5 AI Testing

AI tests **mock the AI provider** — they do not call real LLM APIs. The mock returns predefined JSON strings. Tests verify:
- Correct prompt construction
- Successful response parsing
- Error handling when provider fails
- Error handling when response is malformed

---

## 13. Docker Strategy

### 13.1 Development — Docker Compose

```yaml
# docker-compose.yml (conceptual)
services:
  app:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [db]
    volumes: ["./app:/app/app"]  # Hot reload in dev

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: hirepro
      POSTGRES_USER: hirepro_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

volumes:
  pgdata:
```

### 13.2 Dockerfile

```dockerfile
# Multi-stage build (conceptual)
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Production variant uses Gunicorn with uvicorn workers instead of bare uvicorn.

### 13.3 Environment Files

- `.env` — actual secrets (git-ignored)
- `.env.example` — template with placeholder values (committed)
- `docker-compose.yml` reads from `.env`

---

## 14. CI/CD Strategy

### 14.1 GitHub Actions Pipeline

```yaml
# .github/workflows/ci.yml (conceptual)
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: hirepro_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest --tb=short -q
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/hirepro_test
          SECRET_KEY: test-secret-key
          AI_API_KEY: fake-key  # AI tests use mocks

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install ruff
      - run: ruff check app/ tests/

  build:
    needs: [test, lint]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t hirepro-ai .
```

### 14.2 Pipeline Stages

```
Push / PR → Lint → Test (with PostgreSQL service) → Build Docker Image (main only)
```

---

## 15. Deployment Architecture

### 15.1 Production Topology

```
                    ┌─────────────┐
    Internet ──────►│   NGINX     │
                    │  (TLS/SSL)  │
                    └──────┬──────┘
                           │ proxy_pass :8000
                    ┌──────▼──────┐
                    │  Gunicorn   │
                    │  (4 uvicorn │
                    │   workers)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐         ┌──────────────┐
                    │   FastAPI   │────────►│ External LLM │
                    │   App       │         │ API          │
                    └──────┬──────┘         └──────────────┘
                           │
                    ┌──────▼──────┐
                    │ PostgreSQL  │
                    └─────────────┘
```

### 15.2 Component Configuration

| Component | Configuration |
|---|---|
| NGINX | Reverse proxy, TLS termination (Let's Encrypt / certbot), static file serving if needed, rate limiting |
| Gunicorn | `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000` |
| systemd | Service unit file for Gunicorn auto-start and restart on failure |
| PostgreSQL | Local or managed instance, connection via `DATABASE_URL` env var |

### 15.3 NGINX Configuration (Conceptual)

```nginx
server {
    listen 443 ssl;
    server_name api.hirepro.example.com;

    ssl_certificate /etc/letsencrypt/live/.../fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/.../privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 16. Recommended Folder Structure

```
hirepro-ai/
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory, middleware, exception handlers
│   ├── config.py                  # Settings class (pydantic-settings)
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── session.py             # Engine, SessionLocal, get_db dependency
│   │   └── base.py                # Declarative base for models
│   │
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── student_profile.py
│   │   ├── recruiter_profile.py
│   │   ├── company.py
│   │   ├── job.py
│   │   ├── application.py
│   │   ├── application_status_history.py
│   │   ├── education.py
│   │   └── skill.py
│   │
│   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── student.py
│   │   ├── recruiter.py
│   │   ├── company.py
│   │   ├── job.py
│   │   ├── application.py
│   │   ├── application_status_history.py
│   │   ├── education.py
│   │   ├── skill.py
│   │   └── ai.py
│   │
│   ├── api/                       # Route handlers (thin layer)
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Aggregates all v1 routers
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── students.py
│   │   │   ├── recruiters.py
│   │   │   ├── companies.py
│   │   │   ├── jobs.py
│   │   │   ├── applications.py
│   │   │   └── ai.py
│   │
│   ├── services/                  # Business logic (called by routes)
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── student_service.py
│   │   ├── recruiter_service.py
│   │   ├── company_service.py
│   │   ├── job_service.py
│   │   ├── application_service.py
│   │   └── ai/                    # AI-specific service layer
│   │       ├── __init__.py
│   │       ├── ai_service.py      # Orchestrator: builds prompt, calls provider, parses
│   │       ├── providers/
│   │       │   ├── __init__.py
│   │       │   ├── base.py        # AIProvider protocol
│   │       │   └── openai_provider.py
│   │       └── prompts/
│   │           ├── __init__.py
│   │           ├── resume_analysis.py
│   │           ├── resume_improvement.py
│   │           ├── job_matching.py
│   │           ├── interview_prep.py
│   │           └── job_description.py
│   │
│   ├── auth/                      # Auth utilities & dependencies
│   │   ├── __init__.py
│   │   ├── security.py            # Password hashing, JWT create/decode
│   │   └── dependencies.py        # get_current_user, require_role, etc.
│   │
│   ├── exceptions/                # Custom exception classes
│   │   ├── __init__.py
│   │   └── handlers.py            # Global exception handlers
│   │
│   └── utils/                     # Shared utilities
│       ├── __init__.py
│       └── pagination.py          # Pagination helpers
│
├── alembic/                       # Database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_students.py
│   ├── test_recruiters.py
│   ├── test_companies.py
│   ├── test_jobs.py
│   ├── test_applications.py
│   ├── test_ai.py
│   └── test_authorization.py
│
├── docs/
│   ├── requirements.md
│   ├── architecture-proposal.md   # This document
│   ├── database-design.md         # Detailed DB design (future)
│   ├── api-design.md              # Detailed API design (future)
│   └── development-roadmap.md     # Phase plan (future)
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
```

### 16.1 Design Rationale

| Decision | Why |
|---|---|
| `models/` separate from `schemas/` | SQLAlchemy models ≠ Pydantic schemas. Mixing them causes circular imports and tight coupling. |
| `services/` separate from `api/` | Business logic is testable independently of HTTP. Routes stay thin. |
| `services/ai/` as a sub-package | AI is complex enough to deserve its own namespace, but it's still part of the monolith. |
| `auth/` separate from `services/` | Auth concerns (hashing, JWT, dependencies) are cross-cutting infrastructure, not business logic per se. |
| `api/v1/` versioned | Allows adding `v2/` later without breaking existing clients. |
| No `repositories/` layer | For this project size, services calling SQLAlchemy directly is simpler. A repository layer adds abstraction without clear payoff. Can be introduced later if needed. |

---

## 17. Development Phases

### Phase 1: Foundation (Weeks 1–2)
- [ ] Project scaffolding (folder structure, config, `.env.example`)
- [ ] Database setup (SQLAlchemy models, Alembic initial migration)
- [ ] Docker Compose (app + PostgreSQL)
- [ ] User model + Auth (register, login, JWT, password hashing)
- [ ] Auth dependencies (`get_current_user`, `require_role`)
- [ ] Basic error handling framework
- [ ] Tests: auth flows

### Phase 2: Core Entities (Weeks 3–4)
- [ ] Student profile CRUD + education + skills
- [ ] Recruiter profile CRUD
- [ ] Company CRUD
- [ ] Ownership checks for all entities
- [ ] Tests: CRUD, ownership, RBAC

### Phase 3: Jobs & Applications (Weeks 5–6)
- [ ] Job CRUD (create, update, close, list/search/filter)
- [ ] Eligibility criteria and checking
- [ ] Application workflow (apply, track, status transitions, withdraw)
- [ ] Recruiter: view applicants, change status
- [ ] Admin: manage all entities
- [ ] Tests: job search, eligibility, application workflow, status transitions

### Phase 4: AI Integration (Week 7)
- [ ] AI provider abstraction + ONE concrete provider (OpenAI initially)
- [ ] Prompt templates for all 5 features
- [ ] AI service orchestrator
- [ ] AI endpoints
- [ ] Graceful degradation when AI unavailable
- [ ] Tests: AI service with mocked provider

### Phase 5: Admin, Polish & Documentation (Week 8)
- [ ] Admin endpoints (user management, stats)
- [ ] Pagination across all list endpoints
- [ ] API documentation review (FastAPI auto-docs)
- [ ] README.md, database-design.md, api-design.md, development-roadmap.md
- [ ] CI/CD pipeline (GitHub Actions)

### Phase 6: Production Deployment (Week 9+)
- [ ] Production Dockerfile (Gunicorn + uvicorn workers)
- [ ] NGINX configuration
- [ ] systemd service file
- [ ] TLS/SSL setup
- [ ] Deployment documentation

---

## 18. Architectural Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **LLM API instability** | Medium | Medium | AI isolation pattern; graceful 503 responses; timeout + retry with backoff |
| **LLM response format unpredictable** | High | Medium | Strict Pydantic parsing; fallback error messages; prompt engineering to request JSON |
| **JWT token theft** | Low | High | Short expiry (30 min); HTTPS only; no sensitive data in token payload |
| **N+1 query performance** | Medium | Medium | SQLAlchemy `selectinload` / `joinedload` for relationships; query review in code review |
| **Database migration conflicts** | Low | Medium | One developer working at a time; linear Alembic history; test migrations in CI |
| **Scope creep** | High | High | Strict phase boundaries; no implementing future features prematurely |
| **Over-engineering** | Medium | Medium | Follow principle #9 — avoid unnecessary abstractions; review architecture decisions |

---

## 19. Previously Open Questions — Approved Decisions

The following questions from v0.1.0 have been reviewed and resolved. Decisions are now incorporated into the architecture.

### Q19.1 — Refresh Tokens

**Decision**: ✅ **No refresh tokens in Phase 1.** Access tokens expire after 30 minutes. User must re-login. Refresh tokens may be added in a later phase.

---

### Q19.2 — PostgreSQL Arrays for `allowed_graduation_years`

**Decision**: ✅ **Use PostgreSQL `INTEGER[]`.** This is an intentional PostgreSQL-specific design choice. Queryable with `ANY()` operator. Already reflected in §5.5.

---

### Q19.3 — Admin Seeding

**Decision**: ✅ **Seed script** via `python -m app.seed_admin`. Credentials loaded from environment variables. Registration API rejects `role=admin`. See §9.4.

---

### Q19.4 — Resume Storage

**Decision**: ✅ **Text field on `student_profiles`** for Phase 1. Sufficient for AI analysis. File upload deferred.

---

### Q19.5 — Multiple Companies per Recruiter

**Decision**: ✅ **One company per recruiter.** `recruiter_profiles.company_id` FK.

A recruiter cannot switch companies while they have active (open) jobs or unresolved (non-terminal) applications associated with their current company.

Once all recruitment responsibilities are resolved (jobs closed, applications in terminal state), the recruiter's `company_id` may be updated.

Historical recruitment records remain associated with their original company.

This rule is enforced at the application/service layer. See §6.2.

---

### Q19.6 — Company Ownership Model

**Decision**: ✅ **Creator-only editing rights** for company profile. Other recruiters at the same company can manage jobs but cannot edit company profile. See §6.2.

---

### Q19.7 — AI Provider Selection

**Decision**: ✅ **Provider-agnostic architecture, single concrete provider initially.** The provider is selected via `AI_PROVIDER` env var. Only one provider is implemented in Phase 4. See §10.1.

---

### Q19.8 — Application Status: `OFFERED` vs `SELECTED`

**Decision**: ✅ **`SELECTED`** — placement platform terminology.

---

### Q19.9 — Sync vs Async SQLAlchemy

**Decision**: ✅ **Async** (`AsyncSession`, `asyncpg`). FastAPI is async-first, and AI service makes external HTTP calls that benefit from async.

---

## 20. Remaining Ambiguities

All major architectural questions have been resolved. The following minor items may need clarification during implementation but do not block the start:

| Item | Notes |
|---|---|
| Exact GPA scale (4.0 vs 10.0) | Currently using 10.0 scale (`CHECK gpa <= 10.0`). May need adjustment if platform serves international students. |
| Password complexity rules | Not specified. Recommend minimum 8 characters for Phase 1, configurable. |
| Rate limiting for AI endpoints | Architecture mentions 429 responses but does not specify rate limit values. Define during Phase 4 implementation. |

---

*End of architecture proposal v0.2.0. Awaiting human approval before proceeding with implementation.*
