import os
import psycopg2
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definida")

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"respaldo_{timestamp}.sql")

    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cur = conn.cursor()

        # Obtener tablas del schema public
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE';
        """)
        tables = [row[0] for row in cur.fetchall()]

        with open(backup_file, "w", encoding="utf-8") as f:
            f.write("-- Backup generado sin pg_dump\n\n")

            for table in tables:
                f.write(f"-- Tabla: {table}\n")
                f.write(f"TRUNCATE TABLE {table} CASCADE;\n")

                # Exportar datos con COPY
                f.write(f"COPY {table} FROM stdin WITH CSV;\n")
                cur.copy_expert(
                    f"COPY {table} TO STDOUT WITH CSV",
                    f
                )
                f.write("\\.\n\n")

        cur.close()
        conn.close()

        return f"[{datetime.now()}] Respaldo exitoso: {backup_file}"

    except Exception as e:
        return f"[{datetime.now()}] Error al generar respaldo: {e}"