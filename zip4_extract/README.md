# Sayanjali Nexus CRM

A local-first, multi-vertical CRM built for **Sayanjali Nexus Private Limited** — one platform for AI Solutions, Custom Software, Real Estate, Hospitality, Agriculture, Import/Export, and every other vertical the company runs, without needing a schema change per business line.

Founder & Managing Director: **Syed Ali Hasan Moosavi**

Full design rationale, ERD, module specs, and roadmap: see [`docs/SDD.md`](docs/SDD.md).

## Quick start (local)

**Requirements:** Python 3.11+, Node.js 18+

```bash
# one-time setup
bash scripts/dev-setup.sh      # or scripts\dev-setup.ps1 on Windows

# run backend (terminal 1)
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# run frontend (terminal 2)
cd frontend && npm run dev
```

Open **http://localhost:5173**. Log in with the seeded Founder account:
`syed@sayanjalinexus.com` / `ChangeMe123!` — **change this password immediately.**

API docs (Swagger): **http://localhost:8000/docs**

## Desktop app (Electron)

```bash
cd frontend && npm run build   # builds dist/ that electron loads
cd ../electron && npm install && npm start
```

## What's implemented right now

- Full database schema (35 tables) — Users/Roles/Permissions, Business Verticals, Clients/Contacts/Companies, Lead pipeline, Projects/Tasks, Opportunities, Meetings, Invoices/Payments, Tags, Attachments, Notifications, Audit Log
- Working Alembic migrations (`backend/alembic/versions/`)
- JWT auth with refresh tokens + **granular RBAC that's actually enforced** — every list/get/create/update/delete endpoint checks a real permission, verified live: a zero-permission role gets 403 on everything, Founder/Director bypass cleanly, and each of the 11 roles gets a deliberate, module-scoped slice of access (see `scripts/seed.py`)
- **Leads, Clients, Projects/Tasks, Opportunities, and Documents — fully working end-to-end** (API + repository/service layers + React UI where applicable), including real business rules, not just CRUD:
  - **Convert Lead → Client** in one click: carries the contact across, links the vertical, preserves the original lead's history
  - **Project progress auto-recalculates** from task completion — never hand-edited, can't drift out of sync
  - **Winning an Opportunity auto-creates a starter Project** with the deal value carried over as budget
  - **Documents** support polymorphic attachment to any entity with automatic versioning on re-upload
- Automated test suite (`backend/tests/`, 9 passing tests) covering auth, RBAC at every tier, and the full Lead→Client→Project→Task lifecycle
- Business Verticals module — add a new vertical as a data row, zero migrations
- React + TypeScript + Tailwind frontend shell with sidebar nav, auth flow, dashboard, and an inline expandable task checklist on each project
- Seed script with the company's 29 verticals, 11 fully-permissioned roles, and 40 granular permissions pre-loaded

A full audit of Phases 1–2 was conducted before Phase 3 began — 8 findings (2 real bugs, an incomplete RBAC implementation, and a few consistency/onboarding issues) were found and fixed, each with a regression test. Full details in `docs/SDD.md` Section 5A.

## What's next (see roadmap in the SDD)

Communications, Reports, Team/Employee management, and the Finance API all follow the exact same backend pattern already proven five times over (`model → schema → repository → service → router`) and the exact same frontend pattern (`api/*.ts → feature page`). See `CONTRIBUTING.md`.

## Structure

```
backend/    FastAPI + SQLAlchemy + Alembic (SQLite now, Postgres-ready)
frontend/   React + TypeScript + Vite + Tailwind
electron/   Desktop shell wrapping the frontend + spawning the backend
docs/       Software Design Document, ER diagram, roadmap
scripts/    Setup scripts, DB seed
```
