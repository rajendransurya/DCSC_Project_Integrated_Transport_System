# db/db_utils.py
import os

from psycopg2.pool import ThreadedConnectionPool
import logging
from contextlib import contextmanager
from dotenv import load_dotenv

# get environment variables
load_dotenv()

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


pg_hostname=os.getenv('PG_HOSTNAME')
pg_dbname=os.getenv('PG_DBNAME')
pg_username=os.getenv('PG_USERNAME')
pg_pwd= os.getenv('PG_PWD')
pg_port=os.getenv('PG_PORT')

print(f"{pg_hostname},{pg_dbname},{pg_username},{pg_pwd},{pg_port}")


class DBUtil:
    def __init__(self):
        self.db_pool = ThreadedConnectionPool(1, 10, host=pg_hostname, dbname=pg_dbname, user=pg_username,
                                              password=pg_pwd, port=pg_port)

    @contextmanager
    def get_db_cursor(self):
        conn = self.db_pool.getconn()
        cursor = conn.cursor()
        logger.info("Connection retrieved and cursor created")
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            logger.error(f"Database error: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            logger.info("Cursor closed")
            self.db_pool.putconn(conn)

    def close_all_connections(self):
        self.db_pool.closeall()
        logger.info("All database connections closed")