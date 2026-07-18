"""
Generic repository: encapsulates raw SQLAlchemy queries so services never
touch the ORM directly. Every entity-specific repository subclasses this.
"""
from typing import Generic, TypeVar, Type, Optional, List

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: str) -> Optional[ModelType]:
        return (
            self.db.query(self.model)
            .filter(self.model.id == id, self.model.is_deleted.is_(False))
            .first()
        )

    def list(self, skip: int = 0, limit: int = 25, **filters) -> List[ModelType]:
        query = self.db.query(self.model).filter(self.model.is_deleted.is_(False))
        for field, value in filters.items():
            if value is not None:
                query = query.filter(getattr(self.model, field) == value)
        return query.offset(skip).limit(limit).all()

    def count(self, **filters) -> int:
        query = self.db.query(self.model).filter(self.model.is_deleted.is_(False))
        for field, value in filters.items():
            if value is not None:
                query = query.filter(getattr(self.model, field) == value)
        return query.count()

    def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, updates: dict) -> ModelType:
        for field, value in updates.items():
            if value is not None:
                setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def soft_delete(self, db_obj: ModelType) -> None:
        from datetime import datetime

        db_obj.is_deleted = True
        db_obj.deleted_at = datetime.utcnow()
        self.db.commit()
