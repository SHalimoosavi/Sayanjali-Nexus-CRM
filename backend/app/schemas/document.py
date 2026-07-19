from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    entity_type: str
    entity_id: str
    file_name: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    category: Optional[str] = None
    version: int
    uploaded_by: Optional[str] = None
    created_at: datetime


class PaginatedAttachments(BaseModel):
    total: int
    items: list[AttachmentOut]
