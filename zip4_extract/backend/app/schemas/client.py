from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# --- Company ---

class CompanyBase(BaseModel):
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    gst_number: Optional[str] = None
    billing_address: Optional[str] = None
    notes: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


# --- Contact ---

class ContactBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


class ContactOut(ContactBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    client_id: Optional[str] = None
    created_at: datetime


# --- Client ---

class ClientBase(BaseModel):
    display_name: str
    company_id: Optional[str] = None
    client_code: Optional[str] = None
    status: str = "active"
    account_owner_id: Optional[str] = None
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    vertical_ids: list[str] = []


class ClientUpdate(BaseModel):
    display_name: Optional[str] = None
    status: Optional[str] = None
    account_owner_id: Optional[str] = None
    notes: Optional[str] = None
    vertical_ids: Optional[list[str]] = None


class ClientOut(ClientBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime


class ClientDetailOut(ClientOut):
    contacts: list[ContactOut] = []
    vertical_ids: list[str] = []


class PaginatedClients(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ClientOut]
