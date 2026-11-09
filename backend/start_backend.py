import os
import re
import subprocess
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_dir = backend_dir.parent
config_text = (project_dir / "api" / "config.php").read_text(encoding="utf-8")

def php_string(key: str) -> str:
    pattern = rf"['\"]{re.escape(key)}['\"]\s*=>\s*'((?:\\\\.|[^'\\\\])*)'"
    match = re.search(pattern, config_text)
    if not match:
        raise RuntimeError(f"Missing {key} in api/config.php")
    return match.group(1).replace("\\'", "'").replace("\\\\", "\\")

for env_key, config_key in {
    "DB_HOST": "db_host",
    "DB_NAME": "db_name",
    "DB_USER": "db_user",
    "DB_PASS": "db_password",
    "DB_PORT": "db_port",
}.items():
    if config_key == "db_port":
        match = re.search(r"[\'\"]db_port[\'\"]\s*=>\s*(\d+)", config_text)
        if not match:
            raise RuntimeError("Missing db_port in api/config.php")
        value = match.group(1)
    else:
        value = php_string(config_key)
    os.environ.setdefault(env_key, value)

python = backend_dir / "venv" / "Scripts" / "python.exe"
if not python.is_file():
    raise RuntimeError("Backend venv is missing. Run backend\\start_backend.bat once to install requirements.")
command = [str(python), "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]
raise SystemExit(subprocess.call(command, cwd=backend_dir))
