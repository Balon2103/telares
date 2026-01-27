import os
import time
import subprocess
from datetime import datetime

# Configuración de conexión
DB_NAME = os.getenv("POSTGRES_DB", "telares_db")
DB_USER = os.getenv("POSTGRES_USER", "telares_db_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "r2850sFLGCVPhlTf9LwecNsn2K6kPnl0")
DB_HOST = os.getenv("POSTGRES_HOST", "dpg-d5sj20fpm1nc73cds5j0-a")

# Carpeta de respaldo y log
BACKUP_DIR = "/backups"
LOG_FILE = os.path.join(BACKUP_DIR, "backup_log.txt")


def create_backup():
    """Genera un respaldo completo de la base de datos PostgreSQL."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(BACKUP_DIR, f"respaldo_{timestamp}.sql")

    command = [
        "pg_dump",
        f"--dbname=postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
        "-f",
        filename,
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        msg = f"[{datetime.now()}] Respaldo exitoso"
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

    print(f"Respaldo realizado en la base de datos")

    if mode == "once":
        create_backup()
    else:
        while True:
            create_backup()
            time.sleep(3600)
