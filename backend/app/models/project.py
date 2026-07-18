"""
Project & Task management — vertical-aware, so "Website Redesign" (Web Dev
vertical) and "Farmhouse Construction Phase 1" (Construction vertical) live
in the same tables with the same UI, just filtered/themed by vertical.
"""
from sqlalchemy import Column, String, ForeignKey, Text, Numeric, Integer, DateTime, Boolean, Table
from sqlalchemy.orm import relationship

from app.db.base_class import Base, BaseModel

project_team_members = Table(
    "project_team_members",
    Base.metadata,
    Column("project_id", String(36), ForeignKey("projects.id"), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
)


class Project(BaseModel):
    __tablename__ = "projects"
    vertical_id = Column(String(36), ForeignKey("business_verticals.id"), nullable=False)
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=True)
    project_manager_id = Column(String(36), ForeignKey("users.id"))

    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(30), default="planning")  # planning, active, on_hold, completed, cancelled
    budget = Column(Numeric(14, 2))
    start_date = Column(DateTime)
    due_date = Column(DateTime)
    progress_percent = Column(Integer, default=0)

    client = relationship("Client", back_populates="projects")
    stages = relationship("ProjectStage", back_populates="project", order_by="ProjectStage.sort_order")
    tasks = relationship("ProjectTask", back_populates="project")
    team_members = relationship("User", secondary=project_team_members)


class ProjectStage(BaseModel):
    """Milestones / Kanban columns for a project, e.g. Discovery -> Design
    -> Development -> QA -> Deployment."""
    __tablename__ = "project_stages"
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(120), nullable=False)
    sort_order = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    due_date = Column(DateTime)

    project = relationship("Project", back_populates="stages")


class ProjectTask(BaseModel):
    __tablename__ = "project_tasks"
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)  # nullable: supports personal tasks
    stage_id = Column(String(36), ForeignKey("project_stages.id"), nullable=True)
    parent_task_id = Column(String(36), ForeignKey("project_tasks.id"), nullable=True)  # subtasks

    title = Column(String(255), nullable=False)
    description = Column(Text)
    assignee_id = Column(String(36), ForeignKey("users.id"))
    status = Column(String(30), default="todo")  # todo, in_progress, in_review, done, blocked
    priority = Column(String(20), default="medium")
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(100))  # e.g. RRULE string for recurring tasks
    due_date = Column(DateTime)

    project = relationship("Project", back_populates="tasks")
    comments = relationship("TaskComment", back_populates="task")
    subtasks = relationship("ProjectTask", remote_side="ProjectTask.id")


class TaskComment(BaseModel):
    __tablename__ = "task_comments"
    task_id = Column(String(36), ForeignKey("project_tasks.id"), nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=False)

    task = relationship("ProjectTask", back_populates="comments")
