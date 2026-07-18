from fastapi import APIRouter

from app.api.v1 import auth, leads, verticals

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(verticals.router)

# NEXT MODULES TO ADD HERE (following the exact same pattern as leads.py):
# clients, contacts, opportunities, projects, tasks, meetings, documents,
# invoices, notifications, reports, users, roles, dashboard
