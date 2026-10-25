import uuid
from datetime import date, datetime

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, created_at, uuid_pk


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    company_name: Mapped[str] = mapped_column(Text)
    form: Mapped[str] = mapped_column(String(16))
    fiscal_year: Mapped[int] = mapped_column(index=True)
    report_date: Mapped[date] = mapped_column(Date)
    filing_date: Mapped[date] = mapped_column(Date)
    accession_number: Mapped[str] = mapped_column(String(32), unique=True)
    source_url: Mapped[str] = mapped_column(Text)
    content_markdown: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at()
