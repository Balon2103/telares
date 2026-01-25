FROM python:3.10-slim

RUN apt-get update && apt-get install -y postgresql-client

WORKDIR /backups
COPY . .

RUN pip install --no-cache-dir psycopg2-binary

CMD ["python", "backup.py"]
