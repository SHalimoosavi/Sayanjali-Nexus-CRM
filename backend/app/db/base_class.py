"""
Base model + shared mixins used by every table in the schema.

Design decisions (apply across the whole DB):
- UUID primary keys (stored as CHAR(36) string for SQLite compatibility,
  native UUID when running on Postgres) so records can be created offline,
  merged across machines, and safely synced to a future cloud backend
  without primary-key collisions.
- Soft delete everywhere via `is_deleted` + `deleted_at` instead of hard
  DELETE, so audit history and reporting never lose data.
- created_at / updated_at / created_by / updated_by on every table for
  full audit trail.
- No vertical-specific tables. Every business-vertical entity (Lead,
  Client, Project, etc.) has a `vertical_id` FK into `business_verticals`.
  Adding a new vertical is a row insert, never a schema migration.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Boolean, String, ForeignKey
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()


def gen_uuid() -> str:
    return str(uuid.uuid4())


class UUIDMixin:
    id = Column(String(36), primary_key=True, default=gen_uuid)


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AuditMixin:
    @declared_attr
    def created_by(cls):
        return Column(String(36), ForeignKey("users.id"), nullable=True)

    @declared_attr
    def updated_by(cls):
        return Column(String(36), ForeignKey("users.id"), nullable=True)


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class BaseModel(Base, UUIDMixin, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Every business table should inherit this. Marked abstract so it
    doesn't create its own table."""
    __abstract__ = True
