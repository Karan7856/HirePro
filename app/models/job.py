import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Valid job_type values.
JOB_TYPES = ("full_time", "part_time", "internship", "contract")

# Valid job status values.
JOB_STATUSES = ("open", "closed")


class Job(Base):
    """A position posted by a recruiter under a company.

    Soft-closed via status='closed' — jobs are never hard-deleted.
    Eligibility criteria (min_gpa, allowed_graduation_years) are compared
    against StudentProfile.current_gpa and StudentProfile.graduation_year.
    """

    __tablename__ = "jobs"

    __table_args__ = (
        CheckConstraint(
            f"job_type IN {JOB_TYPES}",
            name="ck_jobs_job_type",
        ),
        CheckConstraint(
            f"status IN {JOB_STATUSES}",
            name="ck_jobs_status",
        ),
        # salary_max >= salary_min only when both values are present.
        CheckConstraint(
            "salary_max IS NULL OR salary_min IS NULL OR salary_max >= salary_min",
            name="ck_jobs_salary_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # FK to Company — RESTRICT: cannot delete a company that has jobs.
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # FK to RecruiterProfile — RESTRICT: cannot delete a recruiter profile
    # that has posted jobs.
    recruiter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recruiter_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    job_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Eligibility: compared against StudentProfile.current_gpa.
    min_gpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)

    # PostgreSQL-native INTEGER array.
    # Eligibility: checked against StudentProfile.graduation_year via ANY().
    allowed_graduation_years: Mapped[list[int] | None] = mapped_column(
        ARRAY(INTEGER()),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        server_default="open",
        index=True,
    )
    application_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    # Many-to-one: many jobs belong to one company.
    company: Mapped["Company"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Company",
        foreign_keys=[company_id],
        lazy="select",
    )
    # Many-to-one: many jobs are posted by one recruiter profile.
    recruiter: Mapped["RecruiterProfile"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "RecruiterProfile",
        foreign_keys=[recruiter_id],
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Job id={self.id} title={self.title!r} "
            f"status={self.status!r} company_id={self.company_id}>"
        )
