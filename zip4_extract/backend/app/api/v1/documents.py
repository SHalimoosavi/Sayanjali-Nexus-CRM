from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.identity import User
from app.schemas.document import AttachmentOut, PaginatedAttachments
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=AttachmentOut, status_code=201,
             dependencies=[Depends(require_permission("documents.create"))])
def upload_document(
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    category: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a file against any entity (lead, client, project, task, invoice...).
    Re-uploading the same filename against the same entity creates a new
    version rather than overwriting -- nothing is ever silently replaced."""
    return DocumentService(db).upload(entity_type, entity_id, file, category, uploaded_by=current_user.id)


@router.get("", response_model=PaginatedAttachments,
            dependencies=[Depends(require_permission("documents.read"))])
def list_documents(entity_type: str, entity_id: str, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    items, total = DocumentService(db).list_for_entity(entity_type, entity_id)
    return PaginatedAttachments(total=total, items=items)


@router.get("/{attachment_id}/download", dependencies=[Depends(require_permission("documents.read"))])
def download_document(attachment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    attachment = DocumentService(db).get(attachment_id)
    return FileResponse(path=attachment.file_path, filename=attachment.file_name,
                         media_type=attachment.file_type or "application/octet-stream")


@router.delete("/{attachment_id}", status_code=204,
                dependencies=[Depends(require_permission("documents.delete"))])
def delete_document(attachment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    DocumentService(db).delete(attachment_id)
