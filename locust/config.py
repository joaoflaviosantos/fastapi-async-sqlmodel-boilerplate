# Built-in Dependencies
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
backend_env_path = Path(__file__).parent.parent / "backend" / ".env"
if backend_env_path.exists():
    load_dotenv(backend_env_path)

# API Host
HOST: str = os.environ.get("LOCUST_HOST", "http://127.0.0.1:8000")

# Admin credentials for authentication (read from backend/.env)
USER_FIRST_ADMIN_EMAIL: str = os.environ.get("USER_FIRST_ADMIN_EMAIL", "admin@system.com")
USER_FIRST_ADMIN_PASSWORD: str = os.environ.get("USER_FIRST_ADMIN_PASSWORD", "!Ch4ng3Th1sP4ssW0rd!")

# API base path
API_V1_PREFIX: str = "/api/v1"
