import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Valid application status values (§3.5, §5.10).
APPLICATION_STATUSES = (
    "pending",
    "reviewing",
    "shortlisted",
    "interview",
    "selected",
    "rejected",
    "withdrawn",
)


class Application(Base):
    """A student's application to a specific job.

    One application per student per job — enforced by UNIQUE(student_profile_id, job_id).
    Applications are never hard-deleted; status workflow handles lifecycle (§6.4).
    Both FKs use ON DELETE RESTRICT to protect recruitment records (§6.3).
    """

    __tablename__ = "applications"

    __table_args__ = (
        # Prevent duplicate applications from the same student to the same job.
        UniqueConstraint(
            "student_profile_id",
            "job_id",
            name="uq_applications_student_job",
        ),
        CheckConstraint(
            f"status IN {APPLICATION_STATUSES}",
            name="ck_applications_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # FK to StudentProfile — RESTRICT: applications are recruitment records
    # and must be retained even if student profile deletion is attempted.
    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # FK to Job — RESTRICT: cannot delete a job that has applications.
    # Close the job instead.
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)

    applied_at: Mapped[datetime] = mapped_column(
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

    # Many-to-one: many applications are submitted by one student profile.
    student_profile: Mapped["StudentProfile"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "StudentProfile",
        foreign_keys=[student_profile_id],
        lazy="select",
    )

    # Many-to-one: many applications are received by one job.
    job: Mapped["Job"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Job",
        foreign_keys=[job_id],
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Application id={self.id} "
            f"student_profile_id={self.student_profile_id} "
            f"job_id={self.job_id} status={self.status!r}>"
        )
