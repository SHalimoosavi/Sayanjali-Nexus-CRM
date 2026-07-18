from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.vertical import BusinessVertical

router = APIRouter(prefix="/verticals", tags=["Business Verticals"])


@router.get("")
def list_verticals(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(BusinessVertical).filter(
        BusinessVertical.is_deleted.is_(False)
    ).order_by(BusinessVertical.display_order).all()


@router.post("", dependencies=[Depends(require_permission("settings.manage"))])
def create_vertical(
    name: str, slug: str, description: str = "", icon: str = "briefcase", color: str = "#6366F1",
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    """Onboard a brand-new business vertical -- a row insert, never a migration."""
    vertical = BusinessVertical(name=name, slug=slug, description=description, icon=icon, color=color)
    db.add(vertical)
    db.commit()
    db.refresh(vertical)
    return vertical
