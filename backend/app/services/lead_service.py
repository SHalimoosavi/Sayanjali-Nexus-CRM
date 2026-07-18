"""
Lead service layer — business rules for the lead pipeline live here, not
in the router or the repository. e.g. validating a stage transition
against the owning vertical's configured pipeline_stages, logging an
activity row on every stage change, etc.
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadActivity
from app.models.vertical import BusinessVertical
from app.repositories.base import BaseRepository


class LeadService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BaseRepository(Lead, db)

    def create_lead(self, data: dict, created_by: str) -> Lead:
        vertical = self.db.query(BusinessVertical).filter(BusinessVertical.id == data["vertical_id"]).first()
        if not vertical:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid business vertical")
        data["created_by"] = created_by
        lead = self.repo.create(data)
        self._log_activity(lead.id, "created", f"Lead created in stage '{lead.stage}'")
        return lead

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

    def _log_activity(self, lead_id: str, activity_type: str, description: str) -> None:
        self.db.add(LeadActivity(lead_id=lead_id, activity_type=activity_type, description=description))
        self.db.commit()
