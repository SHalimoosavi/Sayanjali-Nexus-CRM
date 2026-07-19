from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LeadBase(BaseModel):
    vertical_id: str
    source_id: Optional[str] = None
    owner_id: Optional[str] = None
    full_name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    stage: str = "New"
    priority: str = "medium"
    expected_value: Optional[Decimal] = None
    expected_close_date: Optional[datetime] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    stage: Optional[str] = None
    priority: Optional[str] = None
    owner_id: Optional[str] = None
    expected_value: Optional[Decimal] = None
    expected_close_date: Optional[datetime] = None
    score: Optional[int] = None


class LeadOut(LeadBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    score: int
    is_converted: bool
    created_at: datetime
    updated_at: datetime


class LeadNoteCreate(BaseModel):
    note: str


class PaginatedLeads(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[LeadOut]
