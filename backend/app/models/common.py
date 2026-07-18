"""
Cross-cutting entities used by many modules: generic tagging, attachments,
notifications, the global audit log, meetings, and finance (invoices/payments).

Tag & Attachment use a polymorphic (entity_type, entity_id) pair instead of
one FK column per table, so tagging/attaching works uniformly on Leads,
Clients, Projects, Tasks, etc. without new join tables per entity.
"""
from sqlalchemy import Column, String, ForeignKey, Text, Numeric, DateTime, Boolean, Integer

from app.db.base_class import BaseModel


class Tag(BaseModel):
    __tablename__ = "tags"
    name = Column(String(80), nullable=False, unique=True)
    color = Column(String(20), default="#6366F1")


class EntityTag(BaseModel):
    """Polymorphic tag assignment: tag X applied to entity_type='lead', entity_id=<uuid>."""
    __tablename__ = "entity_tags"
    tag_id = Column(String(36), ForeignKey("tags.id"), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)


class Attachment(BaseModel):
    __tablename__ = "attachments"
    entity_type = Column(String(50), nullable=False)  # lead, client, project, task, invoice...
    entity_id = Column(String(36), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)   # local path under /storage
    file_type = Column(String(80))
    file_size_bytes = Column(Integer)
    uploaded_by = Column(String(36), ForeignKey("users.id"))
    version = Column(Integer, default=1)
    category = Column(String(60))  # contract, proposal, invoice, nda, quotation...


class Notification(BaseModel):
    __tablename__ = "notifications"
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text)
    link = Column(String(500))
    is_read = Column(Boolean, default=False)
    notification_type = Column(String(50))  # task_due, lead_followup, meeting_reminder, mention...


class Reminder(BaseModel):
    __tablename__ = "reminders"
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(String(36))
    remind_at = Column(DateTime, nullable=False)
    message = Column(String(500))
    is_sent = Column(Boolean, default=False)


class AuditLog(BaseModel):
    """System-wide immutable audit trail (never soft-deleted in practice,
    though it inherits the mixin for consistency)."""
    __tablename__ = "audit_logs"
    user_id = Column(String(36), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)   # create, update, delete, login, export...
    entity_type = Column(String(50))
    entity_id = Column(String(36))
    changes = Column(Text)  # JSON diff
    ip_address = Column(String(60))


class Meeting(BaseModel):
    __tablename__ = "meetings"
    title = Column(String(200), nullable=False)
    description = Column(Text)
    entity_type = Column(String(50))  # lead, client, project (what the meeting relates to)
    entity_id = Column(String(36))
    organizer_id = Column(String(36), ForeignKey("users.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    location = Column(String(255))  # or video link
    status = Column(String(30), default="scheduled")  # scheduled, completed, cancelled


class MeetingNote(BaseModel):
    __tablename__ = "meeting_notes"
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False)
    note = Column(Text, nullable=False)
    ai_summary = Column(Text)  # reserved for AI-generated meeting summaries


class Invoice(BaseModel):
    __tablename__ = "invoices"
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    invoice_number = Column(String(60), unique=True, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    tax_amount = Column(Numeric(14, 2), default=0)
    status = Column(String(30), default="draft")  # draft, sent, paid, overdue, cancelled
    issue_date = Column(DateTime)
    due_date = Column(DateTime)


class Payment(BaseModel):
    __tablename__ = "payments"
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    payment_date = Column(DateTime)
    method = Column(String(50))  # bank_transfer, upi, cash, cheque
    reference_number = Column(String(120))
