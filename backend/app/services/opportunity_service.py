"""
Opportunity service layer.

Two pieces of real business logic beyond CRUD, matching the pattern set by
Leads (pipeline validation) and Clients (lead conversion):

1. `mark_won` / `mark_lost` are explicit actions, not a generic PATCH of
   `is_won`, so the state transition always carries the right side-effects
   and can't be set into an inconsistent state (e.g. is_won=True with a
   lost_reason still attached).
2. Winning an opportunity tied to a Client auto-creates a starter Project
   for that client/vertical, so delivery can begin immediately without a
   separate manual step -- the same "don't make the user re-type what the
   system already knows" principle behind Lead-to-Client conversion.
"""
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.lead import SalesOpportunity
from app.models.vertical import BusinessVertical
from app.models.project import Project
from app.repositories.base import BaseRepository


class OpportunityService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BaseRepository(SalesOpportunity, db)

    def create_opportunity(self, data: dict, created_by: str) -> SalesOpportunity:
        vertical = self.db.query(BusinessVertical).filter(BusinessVertical.id == data["vertical_id"]).first()
        if not vertical:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid business vertical")
        data["created_by"] = created_by
        return self.repo.create(data)

    def list_opportunities(self, page: int, page_size: int, vertical_id: Optional[str] = None,
                            client_id: Optional[str] = None, owner_id: Optional[str] = None):
        skip = (page - 1) * page_size
        items = self.repo.list(skip=skip, limit=page_size, vertical_id=vertical_id,
                                client_id=client_id, owner_id=owner_id)
        total = self.repo.count(vertical_id=vertical_id, client_id=client_id, owner_id=owner_id)

        # Open pipeline value -- sum of `value` across still-open (is_won IS NULL)
        # opportunities matching the same filters, used for the dashboard KPI.
        query = self.db.query(SalesOpportunity).filter(
            SalesOpportunity.is_deleted.is_(False), SalesOpportunity.is_won.is_(None)
        )
        if vertical_id:
            query = query.filter(SalesOpportunity.vertical_id == vertical_id)
        if client_id:
            query = query.filter(SalesOpportunity.client_id == client_id)
        if owner_id:
            query = query.filter(SalesOpportunity.owner_id == owner_id)
        open_value_total = sum((o.value or Decimal("0")) for o in query.all())

        return items, total, open_value_total

    def get_opportunity(self, opportunity_id: str) -> SalesOpportunity:
        opp = self.repo.get(opportunity_id)
        if not opp:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found")
        return opp

    def update_opportunity(self, opportunity_id: str, updates: dict, updated_by: str) -> SalesOpportunity:
        opp = self.get_opportunity(opportunity_id)
        updates["updated_by"] = updated_by
        return self.repo.update(opp, updates)

    def delete_opportunity(self, opportunity_id: str) -> None:
        self.repo.soft_delete(self.get_opportunity(opportunity_id))

    # --- Explicit win/loss actions ---

    def mark_won(self, opportunity_id: str, updated_by: str) -> SalesOpportunity:
        opp = self.get_opportunity(opportunity_id)
        if opp.is_won is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Opportunity is already closed")
        opp.is_won = True
        opp.stage = "Won"
        opp.probability_percent = 100
        opp.updated_by = updated_by
        self.db.commit()
        self.db.refresh(opp)

        if opp.client_id:
            self._create_starter_project(opp, created_by=updated_by)

        return opp

    def mark_lost(self, opportunity_id: str, reason: Optional[str], updated_by: str) -> SalesOpportunity:
        opp = self.get_opportunity(opportunity_id)
        if opp.is_won is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Opportunity is already closed")
        opp.is_won = False
        opp.stage = "Lost"
        opp.probability_percent = 0
        opp.lost_reason = reason
        opp.updated_by = updated_by
        self.db.commit()
        self.db.refresh(opp)
        return opp

    def _create_starter_project(self, opp: SalesOpportunity, created_by: str) -> Project:
        project = Project(
            vertical_id=opp.vertical_id,
            client_id=opp.client_id,
            name=f"{opp.title} — Delivery",
            description=f"Auto-created when opportunity '{opp.title}' was marked Won.",
            status="planning",
            budget=opp.value,
            created_by=created_by,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
