import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Skill(Base):
    """Normalized skill lookup table.

    Skills are shared entities — the same skill (e.g., "Python") can be
    referenced by many students and many jobs via junction tables
    (student_skills, job_skills), implemented in a later module.
    Names are stored lowercase and normalized (§5.6).
    """

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Lowercase, normalized skill name — must be unique across the table.
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<Skill id={self.id} name={self.name!r}>"
