"""
Project service layer. Owns the one non-trivial rule: `progress_percent`
is derived from completed tasks rather than hand-edited, so the dashboard
KPI stays trustworthy as tasks move through the board.
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStage, ProjectTask
from app.models.vertical import BusinessVertical
from app.repositories.base import BaseRepository


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BaseRepository(Project, db)

    def create_project(self, data: dict, created_by: str) -> Project:
        vertical = self.db.query(BusinessVertical).filter(BusinessVertical.id == data["vertical_id"]).first()
        if not vertical:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid business vertical")
        data["created_by"] = created_by
        return self.repo.create(data)

    def list_projects(self, page: int, page_size: int, vertical_id: Optional[str] = None,
                       client_id: Optional[str] = None, status_filter: Optional[str] = None):
        skip = (page - 1) * page_size
        items = self.repo.list(skip=skip, limit=page_size, vertical_id=vertical_id,
                                client_id=client_id, status=status_filter)
        total = self.repo.count(vertical_id=vertical_id, client_id=client_id, status=status_filter)
        return items, total

    def get_project(self, project_id: str) -> Project:
        project = self.repo.get(project_id)
        if not project:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
        return project

    def update_project(self, project_id: str, updates: dict, updated_by: str) -> Project:
        project = self.get_project(project_id)
        updates["updated_by"] = updated_by
        return self.repo.update(project, updates)

    def delete_project(self, project_id: str) -> None:
        self.repo.soft_delete(self.get_project(project_id))

    # --- Stages ---

    def add_stage(self, project_id: str, data: dict, created_by: str) -> ProjectStage:
        self.get_project(project_id)
        data["project_id"] = project_id
        data["created_by"] = created_by
        stage = ProjectStage(**data)
        self.db.add(stage)
        self.db.commit()
        self.db.refresh(stage)
        return stage

    # --- Progress recalculation, called by TaskService on status change ---

    def recalculate_progress(self, project_id: str) -> None:
        tasks = self.db.query(ProjectTask).filter(
            ProjectTask.project_id == project_id, ProjectTask.is_deleted.is_(False)
        ).all()
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        if not tasks:
            project.progress_percent = 0
            self.db.commit()
            return
        done = sum(1 for t in tasks if t.status == "done")
        project.progress_percent = round((done / len(tasks)) * 100)
        self.db.commit()
