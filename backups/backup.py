import os
import time
import subprocess
from datetime import datetime

# 🔗 URL de conexión (Render la provee)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definida")

# Carpeta de respaldo
BACKUP_DIR = "backups"
LOG_FILE = os.path.join(BACKUP_DIR, "backup_log.txt")


def create_backup():
    """Genera un respaldo de la base de datos PostgreSQL."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(BACKUP_DIR, f"respaldo_{timestamp}.sql")

    command = [
        "pg_dump",           # ✔ llamar directo al binario en PATH
        "--dbname", DATABASE_URL,
        "-f", filename
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        msg = f"[{datetime.now()}] Respaldo exitoso: {filename}\n"

    except subprocess.CalledProcessError as e:
        msg = (
            f"[{datetime.now()}] Error al generar respaldo:\n"
            f"Comando: {' '.join(command)}\n"
            f"Error: {e.stderr.strip() if e.stderr else str(e)}\n"
        )

    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(msg)

    return msg