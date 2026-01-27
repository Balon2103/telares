import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()

    with open("init.sql", "r", encoding="utf-8") as f:
        sql = f.read()

    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()