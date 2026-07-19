from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.identity import User
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectOut, PaginatedProjects,
    ProjectStageCreate, ProjectStageOut,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectOut, dependencies=[Depends(require_permission("projects.create"))])
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ProjectService(db).create_project(payload.model_dump(), created_by=current_user.id)


@router.get("", response_model=PaginatedProjects, dependencies=[Depends(require_permission("projects.read"))])
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    vertical_id: Optional[str] = None,
    client_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    items, total = service.list_projects(page, page_size, vertical_id, client_id, status_filter)
    return PaginatedProjects(total=total, page=page, page_size=page_size, items=items)


@router.get("/{project_id}", response_model=ProjectOut, dependencies=[Depends(require_permission("projects.read"))])
def get_project(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ProjectService(db).get_project(project_id)


@router.patch("/{project_id}", response_model=ProjectOut, dependencies=[Depends(require_permission("projects.update"))])
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    service = ProjectService(db)
    return service.update_project(project_id, payload.model_dump(exclude_unset=True), updated_by=current_user.id)


@router.delete("/{project_id}", status_code=204, dependencies=[Depends(require_permission("projects.delete"))])
def delete_project(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ProjectService(db).delete_project(project_id)


@router.post("/{project_id}/stages", response_model=ProjectStageOut, status_code=201,
             dependencies=[Depends(require_permission("projects.update"))])
def add_stage(project_id: str, payload: ProjectStageCreate, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    return ProjectService(db).add_stage(project_id, payload.model_dump(), created_by=current_user.id)
