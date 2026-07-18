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

- Full database schema (35 tables) — Users/Roles/Permissions, Business Verticals, Clients/Contacts/Companies, Lead pipeline, Projects/Tasks, Meetings, Invoices/Payments, Tags, Attachments, Notifications, Audit Log
- Working Alembic migrations (`backend/alembic/versions/`)
- JWT auth with refresh tokens + granular RBAC (`require_permission("leads.create")` style)
- Fully working **Leads module** end-to-end (API + repository/service layers + React UI) — this is the reference pattern for every other module
- Business Verticals module — add a new vertical as a data row, zero migrations
- React + TypeScript + Tailwind frontend shell with sidebar nav, auth flow, dashboard
- Seed script with the company's 29 verticals, 11 roles, and granular permissions pre-loaded

## What's next (see roadmap in the SDD)

Clients, Projects, Tasks, Communication Center, Documents, Reporting, and the AI module all follow the exact same backend pattern already proven by Leads (`model → schema → repository → service → router`) and the exact same frontend pattern (`api/*.ts → feature page`). See `CONTRIBUTING.md`.

## Structure

```
backend/    FastAPI + SQLAlchemy + Alembic (SQLite now, Postgres-ready)
frontend/   React + TypeScript + Vite + Tailwind
electron/   Desktop shell wrapping the frontend + spawning the backend
docs/       Software Design Document, ER diagram, roadmap
scripts/    Setup scripts, DB seed
```
