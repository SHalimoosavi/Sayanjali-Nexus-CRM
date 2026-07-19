"""
Document service layer. Files are stored on local disk under
`STORAGE_DIR/<entity_type>/<entity_id>/`, with the DB row (`Attachment`)
holding metadata and the polymorphic (entity_type, entity_id) link -- the
same pattern already used for Tags (Section 6.1 of the SDD), so Documents
work identically on Leads, Clients, Projects, Tasks, and Invoices without
a join table per entity.

Versioning: uploading a file with the same name against the same entity
doesn't overwrite -- it increments `version` and keeps the prior file on
disk, consistent with the project's "never destroy history" soft-delete
philosophy.
"""
import shutil
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.common import Attachment

ALLOWED_ENTITY_TYPES = {"lead", "client", "project", "task", "invoice", "meeting", "contact"}


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def upload(self, entity_type: str, entity_id: str, file: UploadFile, category: Optional[str],
               uploaded_by: str) -> Attachment:
        if entity_type not in ALLOWED_ENTITY_TYPES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                 f"Unknown entity_type '{entity_type}'. Must be one of {sorted(ALLOWED_ENTITY_TYPES)}")

        existing_count = (
            self.db.query(Attachment)
            .filter(Attachment.entity_type == entity_type, Attachment.entity_id == entity_id,
                    Attachment.file_name == file.filename, Attachment.is_deleted.is_(False))
            .count()
        )
        version = existing_count + 1

        entity_dir = Path(settings.STORAGE_DIR) / entity_type / entity_id
        entity_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"v{version}__{file.filename}"
        dest_path = entity_dir / stored_name

        with dest_path.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        size_bytes = dest_path.stat().st_size

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if size_bytes > max_bytes:
            dest_path.unlink(missing_ok=True)
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                 f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit")

        attachment = Attachment(
            entity_type=entity_type,
            entity_id=entity_id,
            file_name=file.filename,
            file_path=str(dest_path),
            file_type=file.content_type,
            file_size_bytes=size_bytes,
            category=category,
            version=version,
            uploaded_by=uploaded_by,
            created_by=uploaded_by,
        )
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    def list_for_entity(self, entity_type: str, entity_id: str):
        items = (
            self.db.query(Attachment)
            .filter(Attachment.entity_type == entity_type, Attachment.entity_id == entity_id,
                    Attachment.is_deleted.is_(False))
            .order_by(Attachment.created_at.desc())
            .all()
        )
        return items, len(items)

    def get(self, attachment_id: str) -> Attachment:
        attachment = (
            self.db.query(Attachment)
            .filter(Attachment.id == attachment_id, Attachment.is_deleted.is_(False))
            .first()
        )
        if not attachment:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        return attachment

    def delete(self, attachment_id: str) -> None:
        """Soft-deletes the DB row; the physical file is kept on disk so a
        restore is always possible (same philosophy as every other module)."""
        attachment = self.get(attachment_id)
        from datetime import datetime
        attachment.is_deleted = True
        attachment.deleted_at = datetime.utcnow()
        self.db.commit()
