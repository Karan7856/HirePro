import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecruiterProfile(Base):
    """Recruiter-specific profile data.

    One-to-one with User (role=recruiter).
    Belongs to one Company (nullable — a recruiter may not yet have a company).
    Company FK uses SET NULL so deactivating a company does not destroy
    the recruiter profile.
    """

    __tablename__ = "recruiter_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    # One-to-one with User. UNIQUE enforces the 1:1 at the DB level.
    # RESTRICT prevents deleting a user that has a recruiter profile.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Nullable: recruiter may not belong to a company yet.
    # SET NULL: company deactivation/removal leaves the recruiter profile intact.
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
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

    # Relationship back to User.
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        foreign_keys=[user_id],
        lazy="select",
    )
    # Relationship to Company (many-to-one — many recruiters can belong to one company).
    company: Mapped["Company"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Company",
        foreign_keys=[company_id],
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<RecruiterProfile id={self.id} user_id={self.user_id} company_id={self.company_id}>"
