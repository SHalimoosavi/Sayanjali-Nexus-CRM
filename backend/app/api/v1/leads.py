from typing import Optional
import io

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.identity import User
from app.schemas.lead import (
    LeadCreate, LeadUpdate, LeadOut, PaginatedLeads, LeadNoteCreate, LeadNoteOut, LeadActivityOut,
    DuplicateMatch, BulkLeadUpdate, BulkLeadDelete, BulkActionResult, CSVImportResult,
)
from app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["Leads"])


# --- Create / list (static paths) ---

@router.post("", response_model=LeadOut, dependencies=[Depends(require_permission("leads.create"))])
def create_lead(payload: LeadCreate, force: bool = Query(False, description="Bypass duplicate detection"),
                 db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = LeadService(db)
    return service.create_lead(payload.model_dump(), created_by=current_user.id, force=force)


@router.get("", response_model=PaginatedLeads, dependencies=[Depends(require_permission("leads.read"))])
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


# --- Duplicate detection, import/export, bulk ops --------------------------
# IMPORTANT: these static-path routes must stay registered BEFORE the
# GET/PATCH/DELETE "/{lead_id}" routes below, or FastAPI/Starlette will
# match e.g. "/leads/export" against "/{lead_id}" first and treat "export"
# as a lead ID. Route order = registration order, not specificity.

@router.get("/check-duplicate", response_model=list[DuplicateMatch],
            dependencies=[Depends(require_permission("leads.read"))])
def check_duplicate(phone: Optional[str] = None, email: Optional[str] = None,
                     db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dupes = LeadService(db).find_duplicates(phone, email)
    return [
        DuplicateMatch(id=d.id, full_name=d.full_name, phone=d.phone, email=d.email,
                        matched_on="phone" if phone and d.phone == phone else "email")
        for d in dupes
    ]


@router.post("/import", response_model=CSVImportResult,
             dependencies=[Depends(require_permission("leads.create"))])
def import_leads_csv(vertical_id: str = Form(...), file: UploadFile = File(...),
                      db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """CSV columns expected: full_name, company_name, email, phone, whatsapp_number, stage, priority.
    Only full_name is required; rows matching an existing lead's phone/email are skipped, not overwritten."""
    result = LeadService(db).import_csv(file, vertical_id, created_by=current_user.id)
    return CSVImportResult(**result)


@router.get("/export", dependencies=[Depends(require_permission("leads.read"))])
def export_leads_csv(vertical_id: Optional[str] = None, stage: Optional[str] = None,
                      db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    csv_text = LeadService(db).export_csv(vertical_id, stage)
    return StreamingResponse(
        io.BytesIO(csv_text.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


@router.patch("/bulk", response_model=BulkActionResult,
              dependencies=[Depends(require_permission("leads.update"))])
def bulk_update_leads(payload: BulkLeadUpdate, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    """Applies the same field updates (e.g. {"owner_id": "..."} for bulk-assign,
    or {"stage": "Contacted"} for bulk stage moves) to every lead ID given."""
    affected, not_found = LeadService(db).bulk_update(
        payload.ids, payload.updates.model_dump(exclude_unset=True), updated_by=current_user.id
    )
    return BulkActionResult(affected=affected, not_found=not_found)


@router.post("/bulk-delete", response_model=BulkActionResult,
             dependencies=[Depends(require_permission("leads.delete"))])
def bulk_delete_leads(payload: BulkLeadDelete, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    affected, not_found = LeadService(db).bulk_delete(payload.ids)
    return BulkActionResult(affected=affected, not_found=not_found)


# --- Single-lead routes (parameterized -- must come after the static paths above) ---

@router.get("/{lead_id}", response_model=LeadOut, dependencies=[Depends(require_permission("leads.read"))])
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


@router.get("/{lead_id}/notes", response_model=list[LeadNoteOut],
            dependencies=[Depends(require_permission("leads.read"))])
def list_lead_notes(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return LeadService(db).list_notes(lead_id)


@router.post("/{lead_id}/notes", response_model=LeadNoteOut, status_code=201,
             dependencies=[Depends(require_permission("leads.update"))])
def add_lead_note(lead_id: str, payload: LeadNoteCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    from app.models.lead import LeadNote
    note = LeadNote(lead_id=lead_id, note=payload.note, created_by=current_user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/{lead_id}/timeline", response_model=list[LeadActivityOut],
            dependencies=[Depends(require_permission("leads.read"))])
def list_lead_timeline(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return LeadService(db).list_timeline(lead_id)
