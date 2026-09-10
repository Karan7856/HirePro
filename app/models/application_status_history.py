import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApplicationStatusHistory(Base):
    """Append-only audit trail for every application status transition.

    Records are never updated or deleted (§5.11, §6.3).
    Both FKs use ON DELETE RESTRICT to preserve audit integrity.
    old_status is NULL for the initial 'pending' record (§5.11).
    """

    __tablename__ = "application_status_history"

    __table_args__ = (
        # INDEX(changed_at DESC) — supports chronological history queries.
        Index("ix_application_status_history_changed_at", "changed_at", postgresql_ops={"changed_at": "DESC"}),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # FK to Application — RESTRICT: audit trail must outlive any deletion
    # attempt (applications themselves are also RESTRICT-protected).
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # NULL allowed for the initial 'pending' record — no prior status exists.
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # The status being transitioned to — always required.
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)

    # FK to User — RESTRICT: cannot delete a user who has made status changes.
    # Deactivate the user instead.
    changed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Many-to-one: many history records belong to one application.
    application: Mapped["Application"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Application",
        foreign_keys=[application_id],
        lazy="select",
    )

    # Many-to-one: many history records reference the user who made the change.
    changed_by_user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        foreign_keys=[changed_by],
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<ApplicationStatusHistory id={self.id} "
            f"application_id={self.application_id} "
            f"old_status={self.old_status!r} new_status={self.new_status!r}>"
        )
