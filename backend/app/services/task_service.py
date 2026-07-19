"""
Task service layer. Supports both project-linked tasks and standalone
personal tasks (`project_id` nullable per the schema). Any status change
on a project-linked task triggers the owning project's progress
recalculation, keeping Project.progress_percent trustworthy without the
frontend having to compute it.
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import ProjectTask, TaskComment
from app.repositories.base import BaseRepository
from app.services.project_service import ProjectService


class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BaseRepository(ProjectTask, db)

    def create_task(self, data: dict, created_by: str) -> ProjectTask:
        data["created_by"] = created_by
        task = self.repo.create(data)
        if task.project_id:
            ProjectService(self.db).recalculate_progress(task.project_id)
        return task

    def list_tasks(self, page: int, page_size: int, project_id: Optional[str] = None,
                    assignee_id: Optional[str] = None, status_filter: Optional[str] = None):
        skip = (page - 1) * page_size
        items = self.repo.list(skip=skip, limit=page_size, project_id=project_id,
                                assignee_id=assignee_id, status=status_filter)
        total = self.repo.count(project_id=project_id, assignee_id=assignee_id, status=status_filter)
        return items, total

    def get_task(self, task_id: str) -> ProjectTask:
        task = self.repo.get(task_id)
        if not task:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
        return task

    def update_task(self, task_id: str, updates: dict, updated_by: str) -> ProjectTask:
        task = self.get_task(task_id)
        updates["updated_by"] = updated_by
        task = self.repo.update(task, updates)
        if task.project_id and "status" in updates:
            ProjectService(self.db).recalculate_progress(task.project_id)
        return task

    def delete_task(self, task_id: str) -> None:
        task = self.get_task(task_id)
        project_id = task.project_id
        self.repo.soft_delete(task)
        if project_id:
            ProjectService(self.db).recalculate_progress(project_id)

    def add_comment(self, task_id: str, comment: str, author_id: str) -> TaskComment:
        self.get_task(task_id)
        c = TaskComment(task_id=task_id, comment=comment, author_id=author_id, created_by=author_id)
        self.db.add(c)
        self.db.commit()
        self.db.refresh(c)
        return c
