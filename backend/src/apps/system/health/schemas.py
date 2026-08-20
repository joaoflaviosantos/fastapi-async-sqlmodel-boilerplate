# Built-in Dependencies
from typing import Literal

# Third-Party Dependencies
from pydantic import BaseModel, ConfigDict


class HealthRead(BaseModel):
    """Liveness probe: the process is up. No dependency checks."""

    status: Literal["ok"]

    model_config = ConfigDict(extra="forbid")


class ReadyRead(BaseModel):
    """Readiness probe: this instance can take traffic."""

    status: Literal["ok"]
    database: Literal["ok"]
    redis: Literal["ok"]

    model_config = ConfigDict(extra="forbid")
