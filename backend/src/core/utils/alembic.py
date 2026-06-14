# src/core/utils/alembic.py

# Built-in Dependencies
import subprocess
import asyncio
import os
from pathlib import Path

# Third-Party Dependencies
from alembic.script import ScriptDirectory
from alembic.config import Config


# --------------------------------------
# ----------- PATH UTILITIES -----------
# --------------------------------------
def _get_backend_dir() -> Path:
    """
    Get the backend directory path.

    Returns the path to the backend directory by navigating up from this file's location.
    Structure: src/core/utils/alembic.py -> backend/
    """
    return Path(__file__).resolve().parent.parent.parent.parent


# --------------------------------------
# -------- MIGRATION UTILITIES ---------
# --------------------------------------
def get_latest_migration_version(alembic_cfg_path: str = "alembic.ini") -> str | None:
    """
    Retrieve the latest migration version from Alembic.

    Args:
        alembic_cfg_path (str): Path to the Alembic configuration file.
                                Defaults to "alembic.ini" (relative to backend dir).

    Returns:
        str | None: The latest migration version identifier, or None if no migrations exist.
    """
    # Resolve path relative to backend directory
    backend_dir = _get_backend_dir()
    full_path = backend_dir / alembic_cfg_path

    alembic_cfg = Config(str(full_path))
    script_directory = ScriptDirectory.from_config(alembic_cfg)
    return script_directory.get_current_head()


def run_alembic_migration_sync(
    alembic_cfg_path: str = "alembic.ini",
    target: str = "head",
) -> dict:
    """
    Runs an Alembic migration synchronously.

    Parameters
    ----------
    alembic_cfg_path : str, optional
        Path to alembic.ini (relative to backend dir). Default is "alembic.ini".
    target : str, optional
        The target revision to migrate to. Default is "head".

    Returns
    -------
    dict
        A dictionary with "stdout" and "stderr" from the migration command.

    Raises
    ------
    RuntimeError
        If the command fails with a non-zero exit code.
    """
    backend_dir = _get_backend_dir()

    env = os.environ.copy()
    env["ENVIRONMENT"] = "migration"

    command = [
        "poetry",
        "run",
        "alembic",
        "--config",
        alembic_cfg_path,
        "upgrade",
        target,
    ]

    result = subprocess.run(
        command,
        cwd=str(backend_dir),  # Automatically resolved!
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Alembic migration failed:\n{result.stderr}")

    return {"stdout": result.stdout, "stderr": result.stderr}


async def run_alembic_migration_async(
    alembic_cfg_path: str = "alembic.ini",
    target: str = "head",
) -> dict:
    """
    Runs an Alembic migration asynchronously.

    Parameters
    ----------
    alembic_cfg_path : str, optional
        Path to alembic.ini (relative to backend dir). Default is "alembic.ini".
    target : str, optional
        The target revision to migrate to. Default is "head".

    Returns
    -------
    dict
        A dictionary with "stdout" and "stderr" from the migration command.

    Raises
    ------
    RuntimeError
        If the command fails with a non-zero exit code.
    """
    backend_dir = _get_backend_dir()

    env = os.environ.copy()
    env["ENVIRONMENT"] = "migration"

    command = [
        "poetry",
        "run",
        "alembic",
        "--config",
        alembic_cfg_path,
        "upgrade",
        target,
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(backend_dir),  # Automatically resolved!
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"Alembic migration failed:\n{stderr.decode()}")

    return {"stdout": stdout.decode(), "stderr": stderr.decode()}
