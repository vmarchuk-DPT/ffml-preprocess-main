from psycopg2.pool import SimpleConnectionPool
import os


POOL = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=os.environ.get("POSTGRES_HOST"),
    dbname='decipher',
    user=os.environ.get("POSTGRES_USERNAME"),
    password=os.environ.get("POSTGRES_PASSWORD")
)