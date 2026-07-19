# Merge Changelog — Sayanjali Nexus CRM (zip 1 → zip 4)

Paste this whole file to ChatGPT along with zip 4. Tell it: **"Apply section 'ZIP 4 DELTA' only. Everything in zip 1–3 is already merged. Don't re-explain the project, just diff and apply."**

---

## ZIP 4 DELTA — this is the only thing that needs merging right now

7 files touched. 2 new, 5 modified. No backend schema changes, no new dependencies.

### New files (copy as-is)
```
frontend/src/features/tasks/TasksPage.tsx
frontend/src/api/opportunities.ts
```

### Modified files (replace with zip 4's version — small, targeted diffs)
```
frontend/src/App.tsx                              → import TasksPage, replace the /tasks placeholder route
frontend/src/api/projects.ts                       → added deleteTask() export, nothing else changed
frontend/src/features/dashboard/DashboardPage.tsx   → Pipeline Value KPI now calls /opportunities instead of hardcoded ₹0
docs/SDD.md                                         → 2 status-table rows updated (Tasks, Dashboard) — cosmetic only
README.md                                           → not changed this round
```

### What it does
- `/tasks` route now renders a real page instead of the "scaffold it next" placeholder: lists every task across all projects **plus personal tasks** (task with no `project_id`), filterable by status and project, with a checkbox to toggle done, priority tag, due date, delete-on-hover, and a "New task" modal where leaving Project blank creates a personal task.
- Dashboard's "Pipeline Value" KPI card is no longer hardcoded `₹0` — it now calls `GET /api/v1/opportunities` and reads the `open_value_total` field the backend already returns. "Follow-ups Due" was changed from a fake `0` to an honest `—` with a "not wired yet" hint (Reminders module doesn't have an endpoint yet).

### Merge conflict risk
Low. `App.tsx` is the only file likely to have local edits colliding — it's a route-table file, so a manual 3-line resolve (import + one `<Route>` line) is all that's needed if GPT's merge tool flags it.

### Verify after merging
```bash
cd frontend && npx tsc -b && npm run build
```
Both must exit clean. No backend changes in this delta, so no `alembic` or `pytest` step needed for zip 4 specifically — but see the full-stack verification block at the bottom of this doc if you want to sanity-check the whole repo end to end.

---

## Full history, for context if GPT needs to double check zip 1–3 were merged correctly

### ZIP 1 — initial scaffold
Everything was new: full backend (`app/core`, `app/db`, `app/models`, `app/api/v1/{auth,leads,verticals}`), full frontend (`Login`, `Dashboard`, `Leads`), Electron shell, Alembic migration (35 tables), seed script, docs.

### ZIP 2 — Clients, Projects, Tasks modules + one architecture fix
**New:**
```
backend/app/schemas/client.py
backend/app/schemas/project.py
backend/app/services/client_service.py
backend/app/services/project_service.py
backend/app/services/task_service.py
backend/app/api/v1/clients.py
backend/app/api/v1/projects.py
backend/app/api/v1/tasks.py
frontend/src/api/clients.ts
frontend/src/api/projects.ts
frontend/src/features/clients/ClientsPage.tsx
frontend/src/features/projects/ProjectsPage.tsx
```
**Modified:**
```
backend/app/api/v1/__init__.py       → registered clients/projects/tasks routers
backend/app/db/base_class.py         → AuditMixin FKs got use_alter=True (fixed a circular-FK
                                        warning between roles<->users at table-creation time)
backend/alembic/versions/*.py        → regenerated (still 35 tables, just the FK constraint fix)
frontend/src/App.tsx                 → wired /clients and /projects routes
frontend/src/api/leads.ts            → added convertLeadToClient()
frontend/src/features/leads/LeadsPage.tsx → added "Convert to client" button per row
```
**Business rules added:** Lead→Client conversion (carries contact + vertical across, preserves the Lead row). Project.progress_percent auto-recalculates from task completion.

### ZIP 3 — Phase 1–2 audit (8 findings fixed) + Opportunities & Documents modules
**Bug fixes (modified files):**
```
backend/app/models/project.py        → fixed INVERTED self-referential subtasks relationship
                                        (parent.subtasks was returning None; child.subtasks was
                                        returning the parent object)
backend/app/models/lead.py           → custom_fields: Text -> JSON (consistency with BusinessVertical)
backend/app/api/v1/verticals.py      → permission code fixed: settings.manage -> settings.update
                                        (the old code was never seeded, so only Founder/Director
                                        could ever pass the check)
backend/app/services/project_service.py → progress_percent now resets to 0 if a project's last
                                        task is deleted (was leaving a stale value)
backend/app/api/v1/leads.py          → added .read permission gates to list/get endpoints
backend/app/api/v1/clients.py        → same
backend/app/api/v1/projects.py       → same
backend/app/api/v1/tasks.py          → same
                                        (previously ANY authenticated user could read everything
                                        regardless of role — write endpoints were gated, reads weren't)
backend/scripts/seed.py              → full permission matrix for all 11 roles (previously only
                                        Founder/Director/Sales had any permissions at all; the
                                        other 8 roles were empty shells)
backend/alembic/env.py               → auto-creates backend/data/ before connecting (fresh clone +
                                        `alembic upgrade head` as the first command was failing
                                        because git doesn't track empty directories)
backend/alembic/versions/*.py        → regenerated (still 35 tables — custom_fields type change only)
backend/app/api/v1/__init__.py       → registered opportunities/documents routers
backend/app/core/config.py           → added STORAGE_DIR, MAX_UPLOAD_SIZE_MB settings
.gitignore                           → ignore backend/storage/* except .gitkeep
```
**New (Opportunities + Documents modules):**
```
backend/app/schemas/opportunity.py
backend/app/schemas/document.py
backend/app/services/opportunity_service.py
backend/app/services/document_service.py
backend/app/api/v1/opportunities.py
backend/app/api/v1/documents.py
backend/storage/.gitkeep
backend/tests/__init__.py
backend/tests/conftest.py
backend/tests/test_core_workflow.py    → 9 tests, including regression tests for the two bugs above
```
**Business rules added:** Opportunity mark-won/mark-lost as explicit actions (not generic PATCH). Winning a client-linked opportunity auto-creates a starter Project with the deal value as budget. Documents support polymorphic attachment to any entity with automatic versioning on re-upload (same filename → version 2, not an overwrite).

---

## Full-stack verification (run this once everything is merged, not just for zip 4)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python scripts/seed.py
python -m pytest tests/ -v          # expect: 9 passed
uvicorn app.main:app --reload       # leave running

# Frontend (separate terminal)
cd frontend
npm install
npx tsc -b && npm run build         # expect: clean build, no errors
npm run dev
```

Then open `http://localhost:5173`, log in with `syed@sayanjalinexus.com` / `ChangeMe123!` (seeded — change this password for anything beyond local testing), and confirm:
- `/tasks` shows a real page, not "scaffold it next"
- Dashboard's Pipeline Value shows `₹0` with "0 open opportunities" (correct — you haven't created any opportunities yet, this isn't a bug)
- Creating a lead and hitting "Convert to client" on the Leads page produces a Client with the contact carried over

If `python -m pytest tests/` doesn't show `9 passed`, something didn't merge cleanly — stop and diff before going further.
