from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.identity import User
from app.schemas.lead import LeadCreate, LeadUpdate, LeadOut, PaginatedLeads, LeadNoteCreate
from app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post("", response_model=LeadOut, dependencies=[Depends(require_permission("leads.create"))])
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = LeadService(db)
    return service.create_lead(payload.model_dump(), created_by=current_user.id)


@router.get("", response_model=PaginatedLeads)
def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    vertical_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    stage: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeadService(db)
    items, total = service.list_leads(page, page_size, vertical_id, owner_id, stage)
    return PaginatedLeads(total=total, page=page, page_size=page_size, items=items)


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return LeadService(db).get_lead(lead_id)


@router.patch("/{lead_id}", response_model=LeadOut, dependencies=[Depends(require_permission("leads.update"))])
def update_lead(lead_id: str, payload: LeadUpdate, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    service = LeadService(db)
    return service.update_lead(lead_id, payload.model_dump(exclude_unset=True), updated_by=current_user.id)


@router.delete("/{lead_id}", status_code=204, dependencies=[Depends(require_permission("leads.delete"))])
def delete_lead(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    LeadService(db).delete_lead(lead_id)


@router.post("/{lead_id}/notes", status_code=201, dependencies=[Depends(require_permission("leads.update"))])
def add_lead_note(lead_id: str, payload: LeadNoteCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    from app.models.lead import LeadNote
    note = LeadNote(lead_id=lead_id, note=payload.note, created_by=current_user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "note": note.note, "created_at": note.created_at}
