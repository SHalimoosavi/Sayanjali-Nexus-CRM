from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.identity import User
from app.schemas.opportunity import (
    OpportunityCreate, OpportunityUpdate, OpportunityOut, PaginatedOpportunities,
)
from app.services.opportunity_service import OpportunityService

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


@router.post("", response_model=OpportunityOut, dependencies=[Depends(require_permission("opportunities.create"))])
def create_opportunity(payload: OpportunityCreate, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    return OpportunityService(db).create_opportunity(payload.model_dump(), created_by=current_user.id)


@router.get("", response_model=PaginatedOpportunities,
            dependencies=[Depends(require_permission("opportunities.read"))])
def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    vertical_id: Optional[str] = None,
    client_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = OpportunityService(db)
    items, total, open_value_total = service.list_opportunities(page, page_size, vertical_id, client_id, owner_id)
    return PaginatedOpportunities(total=total, page=page, page_size=page_size, items=items,
                                   open_value_total=open_value_total)


@router.get("/{opportunity_id}", response_model=OpportunityOut,
            dependencies=[Depends(require_permission("opportunities.read"))])
def get_opportunity(opportunity_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return OpportunityService(db).get_opportunity(opportunity_id)


@router.patch("/{opportunity_id}", response_model=OpportunityOut,
              dependencies=[Depends(require_permission("opportunities.update"))])
def update_opportunity(opportunity_id: str, payload: OpportunityUpdate, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    service = OpportunityService(db)
    return service.update_opportunity(opportunity_id, payload.model_dump(exclude_unset=True),
                                       updated_by=current_user.id)


@router.delete("/{opportunity_id}", status_code=204,
                dependencies=[Depends(require_permission("opportunities.delete"))])
def delete_opportunity(opportunity_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    OpportunityService(db).delete_opportunity(opportunity_id)


@router.post("/{opportunity_id}/mark-won", response_model=OpportunityOut,
             dependencies=[Depends(require_permission("opportunities.update"))])
def mark_won(opportunity_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Closes the opportunity as Won and, if it's linked to a Client, auto-creates
    a starter Project so delivery can begin without a separate manual step."""
    return OpportunityService(db).mark_won(opportunity_id, updated_by=current_user.id)


@router.post("/{opportunity_id}/mark-lost", response_model=OpportunityOut,
             dependencies=[Depends(require_permission("opportunities.update"))])
def mark_lost(opportunity_id: str, reason: Optional[str] = None, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    return OpportunityService(db).mark_lost(opportunity_id, reason, updated_by=current_user.id)
