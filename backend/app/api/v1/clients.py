from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.identity import User
from app.schemas.client import (
    ClientCreate, ClientUpdate, ClientOut, ClientDetailOut, PaginatedClients,
    ContactCreate, ContactUpdate, ContactOut,
)
from app.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("", response_model=ClientOut, dependencies=[Depends(require_permission("clients.create"))])
def create_client(payload: ClientCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ClientService(db).create_client(payload.model_dump(), created_by=current_user.id)


@router.get("", response_model=PaginatedClients)
def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    account_owner_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClientService(db)
    items, total = service.list_clients(page, page_size, status_filter, account_owner_id)
    return PaginatedClients(total=total, page=page, page_size=page_size, items=items)


@router.get("/{client_id}", response_model=ClientDetailOut)
def get_client(client_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    client = ClientService(db).get_client(client_id)
    return ClientDetailOut(
        **ClientOut.model_validate(client).model_dump(),
        contacts=[ContactOut.model_validate(c) for c in client.contacts if not c.is_deleted],
        vertical_ids=[v.id for v in client.verticals],
    )


@router.patch("/{client_id}", response_model=ClientOut, dependencies=[Depends(require_permission("clients.update"))])
def update_client(client_id: str, payload: ClientUpdate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    service = ClientService(db)
    return service.update_client(client_id, payload.model_dump(exclude_unset=True), updated_by=current_user.id)


@router.delete("/{client_id}", status_code=204, dependencies=[Depends(require_permission("clients.delete"))])
def delete_client(client_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ClientService(db).delete_client(client_id)


# --- Contacts (nested under client) ---

@router.post("/{client_id}/contacts", response_model=ContactOut, status_code=201,
             dependencies=[Depends(require_permission("clients.update"))])
def add_contact(client_id: str, payload: ContactCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    return ClientService(db).add_contact(client_id, payload.model_dump(), created_by=current_user.id)


@router.patch("/{client_id}/contacts/{contact_id}", response_model=ContactOut,
              dependencies=[Depends(require_permission("clients.update"))])
def update_contact(client_id: str, contact_id: str, payload: ContactUpdate, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    service = ClientService(db)
    return service.update_contact(client_id, contact_id, payload.model_dump(exclude_unset=True),
                                    updated_by=current_user.id)


# --- Lead conversion ---

@router.post("/convert-lead/{lead_id}", response_model=ClientOut, status_code=201,
             dependencies=[Depends(require_permission("clients.create"))])
def convert_lead_to_client(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Converts a qualified Lead into a Client, carrying its primary contact
    across and preserving the Lead record (soft-delete pattern -- see SDD Section 5)."""
    return ClientService(db).convert_lead(lead_id, created_by=current_user.id)
