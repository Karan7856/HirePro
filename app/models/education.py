import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Education(Base):
    """A student's historical academic record entry.

    NOT used for placement eligibility — eligibility uses
    StudentProfile.current_gpa and StudentProfile.graduation_year.
    One StudentProfile can have many Education entries (§6.1).
    ON DELETE CASCADE: education has no standalone value if the
    student profile is removed (§6.3).
    """

    __tablename__ = "education"

    __table_args__ = (
        CheckConstraint(
            "gpa IS NULL OR (gpa >= 0 AND gpa <= 10.0)",
            name="ck_education_gpa",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # FK to StudentProfile — CASCADE: education history has no standalone value.
    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    degree: Mapped[str] = mapped_column(String(100), nullable=False)
    field_of_study: Mapped[str | None] = mapped_column(String(150), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Null means currently pursuing.
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Per-institution GPA — historical record only, not used for eligibility.
    gpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)

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

    # Many-to-one: many education entries belong to one student profile.
    student_profile: Mapped["StudentProfile"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "StudentProfile",
        foreign_keys=[student_profile_id],
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Education id={self.id} "
            f"institution={self.institution!r} degree={self.degree!r} "
            f"student_profile_id={self.student_profile_id}>"
        )
