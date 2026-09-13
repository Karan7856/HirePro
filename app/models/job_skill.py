import uuid

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobSkill(Base):
    """Junction table connecting Job and Skill (many-to-many).

    Composite primary key (job_id, skill_id) prevents a job from listing
    the same skill requirement twice.

    ON DELETE behavior (§5.8 / §6.3):
    - job_id → CASCADE: if a job is somehow removed, its skill requirements
      go with it.
    - skill_id → RESTRICT: a skill cannot be deleted while any job references
      it — remove the association first.
    """

    __tablename__ = "job_skills"

    __table_args__ = (
        PrimaryKeyConstraint(
            "job_id",
            "skill_id",
            name="pk_job_skills",
        ),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<JobSkill job_id={self.job_id} "
            f"skill_id={self.skill_id}>"
        )
