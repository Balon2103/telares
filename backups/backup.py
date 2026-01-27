import os
import psycopg2
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"respaldo_{timestamp}.sql")

    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cur = conn.cursor()

        # Obtener todas las tablas del schema public
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type='BASE TABLE';
        """)
        tables = [row[0] for row in cur.fetchall()]

        with open(backup_file, "w", encoding="utf-8") as f:
            for table in tables:
                # Escribimos un DROP TABLE para no duplicar
                f.write(f"DROP TABLE IF EXISTS {table} CASCADE;\n")

                # Obtener el CREATE TABLE
                cur.execute(f"SELECT 'CREATE TABLE ' || relname || E' (\n' || "
                            f"array_to_string(array_agg(column_defs.column_def), E',\n') || E'\n);' "
                            f"FROM (SELECT c.relname, "
                            f"c.attname || ' ' || pg_catalog.format_type(c.atttypid, c.atttypmod) || "
                            f"CASE WHEN c.attnotnull THEN ' NOT NULL' ELSE '' END as column_def "
                            f"FROM pg_class c "
                            f"JOIN pg_attribute a ON a.attrelid = c.oid "
                            f"WHERE c.relkind = 'r' AND a.attnum > 0 AND c.relname = '{table}') column_defs "
                            f"GROUP BY relname;")
                create_table_sql = cur.fetchone()[0]
                f.write(create_table_sql + "\n\n")

                # Exportar datos
                cur.execute(f"SELECT * FROM {table};")
                rows = cur.fetchall()
                if rows:
                    for row in rows:
                        values = []
                        for val in row:
                            if val is None:
                                values.append("NULL")
                            else:
                                values.append("'" + str(val).replace("'", "''") + "'")
                        f.write(f"INSERT INTO {table} VALUES ({', '.join(values)});\n")
                f.write("\n")

        cur.close()
        conn.close()

        return f"[{datetime.now()}] Respaldo exitoso: {backup_file}"

    except Exception as e:
        return f"[{datetime.now()}] Error al generar respaldo: {e}"