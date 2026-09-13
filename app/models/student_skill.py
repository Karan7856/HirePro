import uuid

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudentSkill(Base):
    """Junction table connecting StudentProfile and Skill (many-to-many).

    Composite primary key (student_profile_id, skill_id) prevents a student
    from having the same skill twice.

    ON DELETE behavior (§5.7 / §6.3):
    - student_profile_id → CASCADE: skill associations are lightweight and
      have no audit value; they are removed when the student profile is removed.
    - skill_id → RESTRICT: a skill cannot be deleted while any student
      references it — remove the association first.
    """

    __tablename__ = "student_skills"

    __table_args__ = (
        PrimaryKeyConstraint(
            "student_profile_id",
            "skill_id",
            name="pk_student_skills",
        ),
    )

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<StudentSkill student_profile_id={self.student_profile_id} "
            f"skill_id={self.skill_id}>"
        )
