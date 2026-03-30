from datetime import datetime

class Product:
    """Represents a product/item stored in the warehouse."""

    def __init__(
        self,
        name: str,
        category: str,
        price: float,
        quantity: int,
        min_stock: int = 10,
        product_id: int = None,
    ):
        if not name or not name.strip():
            raise ValueError("Product name cannot be empty.")
        if price < 0:
            raise ValueError("Price cannot be negative.")
        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        if min_stock < 0:
            raise ValueError("Minimum stock level cannot be negative.")

        self.product_id = product_id
        self.name = name.strip()
        self.category = category.strip()
        self.price = round(float(price), 2)
        self.quantity = int(quantity)
        self.min_stock = int(min_stock)

    # derived properties
    @property
    def total_value(self) -> float:
        """Total monetary value of current stock."""
        return round(self.price * self.quantity, 2)

    @property
    def is_low_stock(self) -> bool:
        """True when quantity has fallen at or below the minimum threshold."""
        return self.quantity <= self.min_stock

    # stock mutation
    def add_stock(self, amount: int) -> None:
        """Add units to inventory."""
        if amount <= 0:
            raise ValueError("Amount to add must be positive.")
        self.quantity += amount

    def remove_stock(self, amount: int) -> None:
        """Remove units from inventory."""
        if amount <= 0:
            raise ValueError("Amount to remove must be positive.")
        if amount > self.quantity:
            raise ValueError(
                f"Insufficient stock: requested {amount}, available {self.quantity}."
            )
        self.quantity -= amount

    # serialisation
    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "quantity": self.quantity,
            "min_stock": self.min_stock,
            "total_value": self.total_value,
            "is_low_stock": self.is_low_stock,
        }

    def __repr__(self) -> str:
        return (
            f"Product(id={self.product_id}, name='{self.name}', "
            f"category='{self.category}', price={self.price}, qty={self.quantity})"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Product):
            return False
        return self.product_id == other.product_id

    def __str__(self) -> str:
        low = " ⚠ LOW STOCK" if self.is_low_stock else ""
        return (
            f"[{self.product_id}] {self.name} | {self.category} | "
            f"₹{self.price:.2f} | Qty: {self.quantity}{low}"
        )


class Transaction:
    """Records every stock movement (IN / OUT / ADJUSTMENT)."""

    TYPES = ("IN", "OUT", "ADJUSTMENT")

    def __init__(
        self,
        product_id: int,
        transaction_type: str,
        quantity: int,
        note: str = "",
        transaction_id: int = None,
        timestamp: datetime = None,
    ):
        if transaction_type not in self.TYPES:
            raise ValueError(
                f"Invalid transaction type '{transaction_type}'. "
                f"Must be one of {self.TYPES}."
            )
        if quantity <= 0:
            raise ValueError("Transaction quantity must be positive.")

        self.transaction_id = transaction_id
        self.product_id = product_id
        self.transaction_type = transaction_type
        self.quantity = int(quantity)
        self.note = note.strip()
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "product_id": self.product_id,
            "transaction_type": self.transaction_type,
            "quantity": self.quantity,
            "note": self.note,
            "timestamp": str(self.timestamp),
        }

    def __repr__(self) -> str:
        return (
            f"Transaction(id={self.transaction_id}, product_id={self.product_id}, "
            f"type={self.transaction_type}, qty={self.quantity}, "
            f"at={self.timestamp:%Y-%m-%d %H:%M:%S})"
        )

    def __str__(self) -> str:
        return (
            f"[{self.transaction_id}] {self.timestamp:%Y-%m-%d %H:%M} | "
            f"Product #{self.product_id} | {self.transaction_type} | "
            f"Qty: {self.quantity} | {self.note}"
        )
