# Import all models here so Alembic's autogenerate can discover them.
from app.models.application import Application  # noqa: F401
from app.models.application_status_history import ApplicationStatusHistory  # noqa: F401
from app.models.company import Company  # noqa: F401
from app.models.education import Education  # noqa: F401
from app.models.job import Job  # noqa: F401
from app.models.recruiter_profile import RecruiterProfile  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.student_profile import StudentProfile  # noqa: F401
from app.models.user import User  # noqa: F401
