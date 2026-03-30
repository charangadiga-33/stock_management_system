
from models import Product, Transaction
from database import DatabaseManager


class StockManager:
    """
    High-level API that glues the OOP models to the MySQL database.
    All public methods raise ValueError for bad input and
    RuntimeError for DB-level problems.
    """

    def __init__(self, db: DatabaseManager):
        self.db = db

    #  PRODUCT CRUD
    def add_product(self, product: Product) -> int:
        """Insert a new product; returns the auto-assigned product_id."""
        if self._product_name_exists(product.name):
            raise ValueError(f"Product '{product.name}' already exists.")
        sql = """
            INSERT INTO products (name, category, price, quantity, min_stock)
            VALUES (%s, %s, %s, %s, %s)
        """
        product_id = self.db.execute_query(
            sql,
            (product.name, product.category, product.price,
             product.quantity, product.min_stock),
        )
        product.product_id = product_id

        # Record initial stock as an IN transaction
        if product.quantity > 0:
            self._record_transaction(
                Transaction(product_id, "IN", product.quantity, "Initial stock")
            )
        return product_id

    def get_product(self, product_id: int) -> Product | None:
        """Fetch a single product by ID."""
        row = self.db.fetch_one(
            "SELECT * FROM products WHERE product_id = %s", (product_id,)
        )
        return self._row_to_product(row) if row else None

    def get_all_products(self) -> list[Product]:
        """Return every product in the catalogue."""
        rows = self.db.fetch_all("SELECT * FROM products ORDER BY name")
        return [self._row_to_product(r) for r in rows]

    def update_product(self, product: Product) -> bool:
        """Update name / category / price / min_stock (not quantity directly)."""
        if product.product_id is None:
            raise ValueError("Cannot update a product without product_id.")
        rows_affected = self.db.execute_query(
            """
            UPDATE products
               SET name=%s, category=%s, price=%s, min_stock=%s
             WHERE product_id=%s
            """,
            (product.name, product.category, product.price,
             product.min_stock, product.product_id),
        )
        return rows_affected > 0

    def delete_product(self, product_id: int) -> bool:
        """Remove a product and its transaction history (CASCADE)."""
        rows_affected = self.db.execute_query(
            "DELETE FROM products WHERE product_id = %s", (product_id,)
        )
        return rows_affected > 0

    def search_products(self, keyword: str) -> list[Product]:
        """Case-insensitive search across name and category."""
        pattern = f"%{keyword.strip()}%"
        rows = self.db.fetch_all(
            "SELECT * FROM products WHERE name LIKE %s OR category LIKE %s "
            "ORDER BY name",
            (pattern, pattern),
        )
        return [self._row_to_product(r) for r in rows]

    def get_products_by_category(self, category: str) -> list[Product]:
        rows = self.db.fetch_all(
            "SELECT * FROM products WHERE category = %s ORDER BY name",
            (category,),
        )
        return [self._row_to_product(r) for r in rows]

    #  STOCK OPERATIONS
    def restock(self, product_id: int, amount: int, note: str = "") -> Product:
        """Add stock units to a product."""
        product = self._require_product(product_id)
        product.add_stock(amount)          # validates amount > 0
        self._update_quantity(product)
        self._record_transaction(
            Transaction(product_id, "IN", amount, note or "Restock")
        )
        return product

    def sell(self, product_id: int, amount: int, note: str = "") -> Product:
        """Remove stock units from a product (sale / dispatch)."""
        product = self._require_product(product_id)
        product.remove_stock(amount)       # validates amount & sufficiency
        self._update_quantity(product)
        self._record_transaction(
            Transaction(product_id, "OUT", amount, note or "Sale")
        )
        return product

    def adjust_stock(self, product_id: int, new_quantity: int, note: str = "") -> Product:
        """Forcibly set stock to an exact value (e.g., after physical count)."""
        if new_quantity < 0:
            raise ValueError("Adjusted quantity cannot be negative.")
        product = self._require_product(product_id)
        diff = abs(new_quantity - product.quantity)
        old_qty = product.quantity
        product.quantity = new_quantity
        self._update_quantity(product)
        if diff > 0:
            self._record_transaction(
                Transaction(
                    product_id, "ADJUSTMENT", diff,
                    note or f"Adjusted from {old_qty} to {new_quantity}",
                )
            )
        return product

    #  REPORTS
    def get_low_stock_products(self) -> list[Product]:
        """Products whose quantity ≤ min_stock."""
        rows = self.db.fetch_all(
            "SELECT * FROM products WHERE quantity <= min_stock ORDER BY quantity"
        )
        return [self._row_to_product(r) for r in rows]

    def get_inventory_summary(self) -> dict:
        """Aggregate stats across the whole catalogue."""
        row = self.db.fetch_one(
            """
            SELECT
                COUNT(*)                        AS total_products,
                SUM(quantity)                   AS total_units,
                SUM(price * quantity)           AS total_value,
                COUNT(CASE WHEN quantity = 0
                           THEN 1 END)          AS out_of_stock
            FROM products
            """
        )
        return {
            "total_products": row["total_products"] or 0,
            "total_units":    int(row["total_units"] or 0),
            "total_value":    float(row["total_value"] or 0),
            "out_of_stock":   row["out_of_stock"] or 0,
        }

    def get_transaction_history(self, product_id: int) -> list[Transaction]:
        """All transactions for a specific product, newest first."""
        rows = self.db.fetch_all(
            "SELECT * FROM transactions WHERE product_id = %s "
            "ORDER BY timestamp DESC",
            (product_id,),
        )
        return [self._row_to_transaction(r) for r in rows]

    def get_all_transactions(self) -> list[Transaction]:
        """Every transaction in the system, newest first."""
        rows = self.db.fetch_all(
            "SELECT * FROM transactions ORDER BY timestamp DESC"
        )
        return [self._row_to_transaction(r) for r in rows]

    def get_categories(self) -> list[str]:
        """Distinct categories present in the catalogue."""
        rows = self.db.fetch_all(
            "SELECT DISTINCT category FROM products ORDER BY category"
        )
        return [r["category"] for r in rows]

    #  PRIVATE HELPERS
    def _require_product(self, product_id: int) -> Product:
        product = self.get_product(product_id)
        if product is None:
            raise ValueError(f"No product found with ID {product_id}.")
        return product

    def _product_name_exists(self, name: str) -> bool:
        row = self.db.fetch_one(
            "SELECT product_id FROM products WHERE name = %s", (name,)
        )
        return row is not None

    def _update_quantity(self, product: Product) -> None:
        self.db.execute_query(
            "UPDATE products SET quantity = %s WHERE product_id = %s",
            (product.quantity, product.product_id),
        )

    def _record_transaction(self, txn: Transaction) -> int:
        txn_id = self.db.execute_query(
            """
            INSERT INTO transactions
                (product_id, transaction_type, quantity, note)
            VALUES (%s, %s, %s, %s)
            """,
            (txn.product_id, txn.transaction_type, txn.quantity, txn.note),
        )
        txn.transaction_id = txn_id
        return txn_id

    @staticmethod
    def _row_to_product(row: dict) -> Product:
        return Product(
            name=row["name"],
            category=row["category"],
            price=float(row["price"]),
            quantity=int(row["quantity"]),
            min_stock=int(row["min_stock"]),
            product_id=row["product_id"],
        )

    @staticmethod
    def _row_to_transaction(row: dict) -> Transaction:
        return Transaction(
            product_id=row["product_id"],
            transaction_type=row["transaction_type"],
            quantity=int(row["quantity"]),
            note=row["note"] or "",
            transaction_id=row["transaction_id"],
            timestamp=row["timestamp"],
        )
