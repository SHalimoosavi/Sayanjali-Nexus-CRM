from fastapi import APIRouter

from app.api.v1 import auth, leads, verticals, clients, projects, tasks

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(verticals.router)
api_router.include_router(clients.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)

# NEXT MODULES TO ADD HERE (following the exact same pattern as leads.py):
# opportunities, meetings, documents, invoices, notifications, reports,
# users, roles, dashboard, communications (email/call/whatsapp/sms logs)
