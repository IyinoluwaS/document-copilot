import uuid
from datetime import datetime

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, created_at


class User(Base):
    __tablename__ = "users"

    # Same value as auth.users.id. The FK to auth.users lives in the migration,
    # since the auth schema is owned by Supabase and not part of this metadata.
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = created_at()
