"""
Lead service layer — business rules for the lead pipeline live here, not
in the router or the repository. e.g. validating a stage transition
against the owning vertical's configured pipeline_stages, logging an
activity row on every stage change, etc.
"""
import csv
import io
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadActivity, LeadNote
from app.models.vertical import BusinessVertical
from app.repositories.base import BaseRepository

CSV_COLUMNS = ["full_name", "company_name", "email", "phone", "whatsapp_number", "stage", "priority"]


class LeadService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BaseRepository(Lead, db)

    def create_lead(self, data: dict, created_by: str, force: bool = False) -> Lead:
        vertical = self.db.query(BusinessVertical).filter(BusinessVertical.id == data["vertical_id"]).first()
        if not vertical:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid business vertical")

        if not force:
            dupes = self.find_duplicates(data.get("phone"), data.get("email"))
            if dupes:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail={
                        "message": "A lead with this phone or email already exists. "
                                   "Retry with force=true to create anyway.",
                        "matches": [
                            {"id": d.id, "full_name": d.full_name, "phone": d.phone, "email": d.email,
                             "matched_on": "phone" if d.phone == data.get("phone") and data.get("phone") else "email"}
                            for d in dupes
                        ],
                    },
                )

        data["created_by"] = created_by
        lead = self.repo.create(data)
        self._log_activity(lead.id, "created", f"Lead created in stage '{lead.stage}'")
        return lead

    def find_duplicates(self, phone: Optional[str], email: Optional[str]) -> list[Lead]:
        """Matches on phone OR email, case-insensitive for email, ignoring
        blank values so two leads with no phone don't false-positive."""
        conditions = []
        if phone:
            conditions.append(Lead.phone == phone)
        if email:
            conditions.append(Lead.email.ilike(email))
        if not conditions:
            return []
        return (
            self.db.query(Lead)
            .filter(Lead.is_deleted.is_(False), or_(*conditions))
            .all()
        )

    def list_leads(self, page: int, page_size: int, vertical_id: Optional[str] = None,
                    owner_id: Optional[str] = None, stage: Optional[str] = None):
        skip = (page - 1) * page_size
        items = self.repo.list(skip=skip, limit=page_size, vertical_id=vertical_id,
                                owner_id=owner_id, stage=stage)
        total = self.repo.count(vertical_id=vertical_id, owner_id=owner_id, stage=stage)
        return items, total

    def get_lead(self, lead_id: str) -> Lead:
        lead = self.repo.get(lead_id)
        if not lead:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
        return lead

    def update_lead(self, lead_id: str, updates: dict, updated_by: str) -> Lead:
        lead = self.get_lead(lead_id)
        old_stage = lead.stage
        updates["updated_by"] = updated_by
        lead = self.repo.update(lead, updates)
        if updates.get("stage") and updates["stage"] != old_stage:
            self._log_activity(lead.id, "stage_change", f"Stage changed: {old_stage} -> {lead.stage}")
        return lead

    def delete_lead(self, lead_id: str) -> None:
        lead = self.get_lead(lead_id)
        self.repo.soft_delete(lead)

    # --- Notes & timeline ---

    def list_notes(self, lead_id: str) -> list[LeadNote]:
        self.get_lead(lead_id)
        return (
            self.db.query(LeadNote)
            .filter(LeadNote.lead_id == lead_id, LeadNote.is_deleted.is_(False))
            .order_by(LeadNote.created_at.desc())
            .all()
        )

    def list_timeline(self, lead_id: str) -> list[LeadActivity]:
        self.get_lead(lead_id)
        return (
            self.db.query(LeadActivity)
            .filter(LeadActivity.lead_id == lead_id)
            .order_by(LeadActivity.created_at.desc())
            .all()
        )

    # --- Bulk operations ---

    def bulk_update(self, ids: list[str], updates: dict, updated_by: str) -> tuple[int, list[str]]:
        found = self.db.query(Lead).filter(Lead.id.in_(ids), Lead.is_deleted.is_(False)).all()
        found_ids = {l.id for l in found}
        not_found = [i for i in ids if i not in found_ids]
        clean_updates = {k: v for k, v in updates.items() if v is not None}
        for lead in found:
            for field, value in clean_updates.items():
                setattr(lead, field, value)
            lead.updated_by = updated_by
        self.db.commit()
        return len(found), not_found

    def bulk_delete(self, ids: list[str]) -> tuple[int, list[str]]:
        from datetime import datetime
        found = self.db.query(Lead).filter(Lead.id.in_(ids), Lead.is_deleted.is_(False)).all()
        found_ids = {l.id for l in found}
        not_found = [i for i in ids if i not in found_ids]
        for lead in found:
            lead.is_deleted = True
            lead.deleted_at = datetime.utcnow()
        self.db.commit()
        return len(found), not_found

    # --- CSV import / export ---

    def import_csv(self, file: UploadFile, vertical_id: str, created_by: str) -> dict:
        vertical = self.db.query(BusinessVertical).filter(BusinessVertical.id == vertical_id).first()
        if not vertical:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid business vertical")

        raw = file.file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(raw))

        created, skipped, errors = 0, 0, []
        for i, row in enumerate(reader, start=2):  # row 1 is the header
            full_name = (row.get("full_name") or "").strip()
            if not full_name:
                errors.append(f"Row {i}: missing full_name, skipped")
                continue

            phone = (row.get("phone") or "").strip() or None
            email = (row.get("email") or "").strip() or None
            if self.find_duplicates(phone, email):
                skipped += 1
                continue

            try:
                lead = Lead(
                    vertical_id=vertical_id,
                    full_name=full_name,
                    company_name=(row.get("company_name") or "").strip() or None,
                    email=email,
                    phone=phone,
                    whatsapp_number=(row.get("whatsapp_number") or "").strip() or None,
                    stage=(row.get("stage") or "New").strip(),
                    priority=(row.get("priority") or "medium").strip().lower(),
                    created_by=created_by,
                )
                self.db.add(lead)
                self.db.flush()
                self._log_activity(lead.id, "created", "Lead created via CSV import")
                created += 1
            except Exception as exc:  # noqa: BLE001 -- row-level errors shouldn't abort the whole import
                errors.append(f"Row {i}: {exc}")
                self.db.rollback()

        self.db.commit()
        return {"created": created, "skipped_duplicates": skipped, "errors": errors}

    def export_csv(self, vertical_id: Optional[str], stage: Optional[str]) -> str:
        items = self.repo.list(skip=0, limit=100000, vertical_id=vertical_id, stage=stage)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for lead in items:
            writer.writerow({col: getattr(lead, col, "") or "" for col in CSV_COLUMNS})
        return buffer.getvalue()

    def _log_activity(self, lead_id: str, activity_type: str, description: str) -> None:
        self.db.add(LeadActivity(lead_id=lead_id, activity_type=activity_type, description=description))
        self.db.commit()
