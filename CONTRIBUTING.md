# Contributing to Sayanjali Nexus CRM

## Setup
1. Clone the repo
2. Backend: `cd backend && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`
3. Copy `.env.example` to `.env` in `backend/`
4. `alembic upgrade head` then `python scripts/seed.py`
5. `uvicorn app.main:app --reload`
6. Frontend: `cd frontend && npm install && npm run dev`

## Branching
- `main` — always deployable
- `feature/<module-name>` — one branch per module (e.g. `feature/invoices`)
- `fix/<short-description>` — bug fixes

## Commit style
Conventional commits: `feat(leads): add bulk CSV import`, `fix(auth): refresh token expiry`

## Adding a new module (backend)
Follow the pattern in `app/api/v1/leads.py`:
model -> schema -> repository (reuse BaseRepository) -> service -> router -> register in `app/api/v1/__init__.py`
