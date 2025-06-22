import mysql.connector
from mysql.connector import Error, pooling
from contextlib import contextmanager
import logging
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.config = Config.DB_CONFIG
        self.pool = None
        self._create_connection_pool()
    
    def _create_connection_pool(self):
        """Create a connection pool for better performance"""
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="lovenest_pool",
                pool_size=10,
                pool_reset_session=True,
                **self.config
            )
            logger.info("Database connection pool created successfully")
        except Error as e:
            logger.error(f"Error creating connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        try:
            connection = self.pool.get_connection()
            yield connection
        except Error as e:
            logger.error(f"Database error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    @contextmanager
    def get_cursor(self, dictionary=False):
        """Context manager for database cursors"""
        with self.get_connection() as connection:
            cursor = None
            try:
                cursor = connection.cursor(dictionary=dictionary)
                yield cursor, connection
            except Error as e:
                logger.error(f"Cursor error: {e}")
                connection.rollback()
                raise
            finally:
                if cursor:
                    cursor.close()
    
    def execute_query(self, query, params=None, fetch=False, dictionary=False):
        """Execute a single query"""
        with self.get_cursor(dictionary=dictionary) as (cursor, connection):
            cursor.execute(query, params or ())
            
            if fetch:
                if fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'all':
                    return cursor.fetchall()
            
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    
    def execute_many(self, query, params_list):
        """Execute multiple queries with different parameters"""
        with self.get_cursor() as (cursor, connection):
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_connection() as connection:
                if connection.is_connected():
                    logger.info("Database connection test successful")
                    return True
        except Error as e:
            logger.error(f"Database connection test failed: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions
def get_db_connection():
    """Get a database connection (for backward compatibility)"""
    return db_manager.pool.get_connection()

def execute_query(query, params=None, fetch=False, dictionary=False):
    """Execute a query using the database manager"""
    return db_manager.execute_query(query, params, fetch, dictionary)

def test_database_connection():
    """Test the database connection"""
    return db_manager.test_connection()
