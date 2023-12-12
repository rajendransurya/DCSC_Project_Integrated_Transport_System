# db/db_utils.py
import os
import logging
from contextlib import contextmanager
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

# get environment variables
load_dotenv()

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pg_hostname=os.getenv('PG_HOSTNAME') or 'localhost'
pg_dbname=os.getenv('PG_DBNAME') or 'integrated_transport_system'
pg_username=os.getenv('PG_USERNAME') or  'postgres'
pg_pwd= os.getenv('PG_PWD') or 'admin'
pg_port=os.getenv('PG_PORT') or '5432'

print(f"{pg_hostname},{pg_dbname},{pg_username},{pg_pwd},{pg_port}")


class DBUtil:

    def __init__(self):
        self.db_pool = ConnectionPool(conninfo=f"""
        dbname={pg_dbname}
        user={pg_username}
        password={pg_pwd}
        host={pg_hostname}
        port={pg_port}
        """, min_size=4, max_size=20, timeout=60, open=True)

    @contextmanager
    def get_db_cursor(self):
        with self.db_pool.connection(timeout=60) as conn:
            with conn.cursor() as cur:
                logger.info("Connection retrieved and cursor created")
                try:
                    yield cur
                    conn.commit()
                except Exception as e:
                    logger.error(f"Database error: {e}")
                    conn.rollback()
                    raise
                finally:
                    cur.close()
                    logger.info("Cursor closed")

    def close_all_connections(self):
        self.db_pool.closeall()
        logger.info("All database connections closed")