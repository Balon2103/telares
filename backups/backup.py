import os
import time
import subprocess
from datetime import datetime

# 🔑 pg_dump correcto en Render (PostgreSQL 18)
PG_DUMP = "/usr/lib/postgresql/18/bin/pg_dump"

# 🔗 URL de conexión (Render la provee)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definida en las variables de entorno")

# 📁 Carpeta de respaldo (RELATIVA al proyecto)
BACKUP_DIR = "backups"
LOG_FILE = os.path.join(BACKUP_DIR, "backup_log.txt")


def create_backup():
    """Genera un respaldo de la base de datos PostgreSQL."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(BACKUP_DIR, f"respaldo_{timestamp}.sql")

    command = [
        PG_DUMP,
        "--dbname",
        DATABASE_URL,
        "-f",
        filename,
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
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


if __name__ == "__main__":
    import sys

    mode = "auto"
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        mode = "once"

    print("Respaldo realizado en la base de datos")

    if mode == "once":
        create_backup()
    else:
        while True:
            create_backup()
            time.sleep(3600)  # cada 1 hora
