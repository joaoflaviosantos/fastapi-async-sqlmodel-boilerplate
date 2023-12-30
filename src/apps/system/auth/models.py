# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

# Local Dependencies
from src.core.common.models import Base

# Define a TokenBlacklist class that represents the 'token_blacklist' table
class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id: Mapped[int] = mapped_column(
        "id", autoincrement=True, nullable=False, unique=True, primary_key=True, init=False
    )
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
