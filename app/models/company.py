import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Company(Base):
    """Organisational entity that recruiters belong to and jobs are posted under.

    Company profile editing is restricted to the creator (and admins).
    Job management under the company is open to any recruiter belonging to it.
    Soft-deactivation via is_active — companies are never hard-deleted.
    """

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
    # Ownership: tracks which user (recruiter) created this company.
    # Used to enforce "creator-only" profile editing rule.
    # Nullable: allows the creator's account to be deactivated without
    # breaking the company record (no ON DELETE behaviour — FK only).
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationship to the creator User — lazy loaded, read-only reference.
    # Back-populates not added on User to avoid coupling User to Company
    # before RecruiterProfile and Job models exist.
    creator: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        foreign_keys=[created_by],
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name!r} active={self.is_active}>"
