from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.identity import User
from app.schemas.project import TaskCreate, TaskUpdate, TaskOut, PaginatedTasks, TaskCommentCreate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskOut, dependencies=[Depends(require_permission("tasks.create"))])
def create_task(payload: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return TaskService(db).create_task(payload.model_dump(), created_by=current_user.id)


@router.get("", response_model=PaginatedTasks, dependencies=[Depends(require_permission("tasks.read"))])
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    project_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(db)
    items, total = service.list_tasks(page, page_size, project_id, assignee_id, status_filter)
    return PaginatedTasks(total=total, page=page, page_size=page_size, items=items)


@router.get("/{task_id}", response_model=TaskOut, dependencies=[Depends(require_permission("tasks.read"))])
def get_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return TaskService(db).get_task(task_id)


@router.patch("/{task_id}", response_model=TaskOut, dependencies=[Depends(require_permission("tasks.update"))])
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    service = TaskService(db)
    return service.update_task(task_id, payload.model_dump(exclude_unset=True), updated_by=current_user.id)


@router.delete("/{task_id}", status_code=204, dependencies=[Depends(require_permission("tasks.delete"))])
def delete_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    TaskService(db).delete_task(task_id)


@router.post("/{task_id}/comments", status_code=201, dependencies=[Depends(require_permission("tasks.update"))])
def add_comment(task_id: str, payload: TaskCommentCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    comment = TaskService(db).add_comment(task_id, payload.comment, author_id=current_user.id)
    return {"id": comment.id, "comment": comment.comment, "created_at": comment.created_at}
