"""Generic CRUD base repository with automatic soft-delete filtering."""

from datetime import datetime, timezone  # Fix: Import both class and objectfrom time import timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session
from uuid import UUID  # Fix: Need this for type hinting
from ..models.base import Base, SoftDeleteMixin

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def _base_query(self):
        """Returns a query that auto-filters soft-deleted records."""
        q = self.db.query(self.model)
        if issubclass(self.model, SoftDeleteMixin):
            q = q.filter(self.model.is_deleted == False)  # noqa: E712
        return q

    def get_by_id(self, id: Any) -> ModelType | None:
        return self._base_query().filter(self.model.id == id).first()

    def get_all(self) -> list[ModelType]:
        return self._base_query().all()

    def create(self, **kwargs: Any) -> ModelType:
        obj = self.model(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def soft_delete(self, id: Any, deleted_by: UUID | None = None) -> ModelType | None:
        obj = self.get_by_id(id)
        if obj and isinstance(obj, SoftDeleteMixin):
            obj.is_deleted = True
            obj.deleted_at = datetime.now(timezone.utc)  # Python-side, not server_default
            obj.deleted_by = deleted_by
            self.db.flush()
        return obj

