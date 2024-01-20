# Local Dependencies
from src.core.common.models import Base


class Job(Base):
    """
    API Schema

    Description:
    ----------
    'Job' response schema.

    Fields:
    ----------
    - 'id' (str): Unique identifier for the job.
    """

    id: str
