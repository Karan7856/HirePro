import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StudentProfile(Base):
    """Student-specific profile data.

    One-to-one with User (role=student). Holds eligibility fields
    (current_gpa, graduation_year) that are used for job matching.
    Education entries are stored separately in the Education table.
    """

    __tablename__ = "student_profiles"

    __table_args__ = (
        CheckConstraint(
            "current_gpa >= 0 AND current_gpa <= 10.0",
            name="ck_student_profiles_current_gpa",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    # One-to-one with User. UNIQUE enforces the 1:1 at the DB level.
    # RESTRICT prevents deleting a user that has a student profile.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Placement eligibility fields — authoritative for job matching.
    # Individual Education entries store per-institution GPA separately.
    current_gpa: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
    )
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
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

    def __repr__(self) -> str:
        return f"<StudentProfile id={self.id} user_id={self.user_id}>"
