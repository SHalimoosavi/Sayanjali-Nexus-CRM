from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


# --- Project ---

class ProjectBase(BaseModel):
    vertical_id: str
    client_id: Optional[str] = None
    project_manager_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    status: str = "planning"
    budget: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    project_manager_id: Optional[str] = None
    budget: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    progress_percent: Optional[int] = None


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    progress_percent: int
    created_at: datetime
    updated_at: datetime


class PaginatedProjects(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProjectOut]


# --- Project Stage ---

class ProjectStageCreate(BaseModel):
    name: str
    sort_order: int = 0
    due_date: Optional[datetime] = None


class ProjectStageOut(ProjectStageCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    is_completed: bool


# --- Project Task ---

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    stage_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    assignee_id: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    stage_id: Optional[str] = None
    assignee_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskOut(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime


class PaginatedTasks(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TaskOut]


class TaskCommentCreate(BaseModel):
    comment: str
