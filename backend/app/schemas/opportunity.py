from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OpportunityBase(BaseModel):
    vertical_id: str
    lead_id: Optional[str] = None
    client_id: Optional[str] = None
    owner_id: Optional[str] = None
    title: str
    stage: str = "Qualification"
    value: Optional[Decimal] = None
    probability_percent: int = 10
    expected_close_date: Optional[datetime] = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    stage: Optional[str] = None
    owner_id: Optional[str] = None
    value: Optional[Decimal] = None
    probability_percent: Optional[int] = None
    expected_close_date: Optional[datetime] = None
    is_won: Optional[bool] = None
    lost_reason: Optional[str] = None


class OpportunityOut(OpportunityBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    is_won: Optional[bool] = None
    lost_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaginatedOpportunities(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[OpportunityOut]
    open_value_total: Decimal
