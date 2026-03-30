import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


class DatabaseManager:
    """Handles all MySQL connection, schema creation, and raw queries."""

    # DDL
    _CREATE_DB_SQL = "CREATE DATABASE IF NOT EXISTS stock_mgmt_db;"

    _CREATE_PRODUCTS_SQL = """
        CREATE TABLE IF NOT EXISTS products (
            product_id  INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(120)   NOT NULL,
            category    VARCHAR(80)    NOT NULL,
            price       DECIMAL(12,2)  NOT NULL CHECK (price >= 0),
            quantity    INT            NOT NULL DEFAULT 0 CHECK (quantity >= 0),
            min_stock   INT            NOT NULL DEFAULT 10,
            created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                        ON UPDATE CURRENT_TIMESTAMP
        );
    """

    _CREATE_TRANSACTIONS_SQL = """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id   INT AUTO_INCREMENT PRIMARY KEY,
            product_id       INT          NOT NULL,
            transaction_type ENUM('IN','OUT','ADJUSTMENT') NOT NULL,
            quantity         INT          NOT NULL CHECK (quantity > 0),
            note             VARCHAR(255) DEFAULT '',
            timestamp        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
                ON DELETE CASCADE
        );
    """

    def __init__(self, config: dict = None):
        self._config = config or DB_CONFIG
        self._connection = None

    # connection management
    def connect(self) -> None:
        """Open connection and ensure the schema exists."""
        try:
            # First connect without specifying the database so we can create it
            init_cfg = {k: v for k, v in self._config.items() if k != "database"}
            conn = mysql.connector.connect(**init_cfg)
            cursor = conn.cursor()
            cursor.execute(self._CREATE_DB_SQL)
            cursor.close()
            conn.close()

            # Now connect with the target database
            self._connection = mysql.connector.connect(**self._config)
            self._create_tables()
        except Error as exc:
            raise ConnectionError(f"MySQL connection failed: {exc}") from exc

    def disconnect(self) -> None:
        if self._connection and self._connection.is_connected():
            self._connection.close()

    def is_connected(self) -> bool:
        return self._connection is not None and self._connection.is_connected()

    # internal helpers
    def _create_tables(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute(self._CREATE_PRODUCTS_SQL)
        cursor.execute(self._CREATE_TRANSACTIONS_SQL)
        self._connection.commit()
        cursor.close()

    def execute_query(self, sql: str, params: tuple = ()) -> int:
        """Run INSERT / UPDATE / DELETE; returns lastrowid or rowcount."""
        cursor = self._connection.cursor()
        cursor.execute(sql, params)
        self._connection.commit()
        row_id = cursor.lastrowid or cursor.rowcount
        cursor.close()
        return row_id

    def fetch_all(self, sql: str, params: tuple = ()) -> list:
        """Run SELECT and return all rows as list-of-dicts."""
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def fetch_one(self, sql: str, params: tuple = ()) -> dict | None:
        """Run SELECT and return a single row as dict (or None)."""
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        row = cursor.fetchone()
        cursor.close()
        return row

    # context-manager support
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
