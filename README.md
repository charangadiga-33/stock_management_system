# Stock Management System
**Python · OOP · MySQL · 25+ Automated Tests (~90% coverage)**

---

## Project Structure

```
stock_management_system/
├── config.py           # DB credentials (edit this first)
├── models.py           # OOP classes: Product, Transaction
├── database.py         # DatabaseManager (MySQL layer)
├── stock_manager.py    # StockManager (business logic)
├── main.py             # CLI menu application
├── setup.sql           # One-time MySQL schema + seed data
├── requirements.txt
└── tests/
    └── test_stock_management.py   # 45 test cases
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure MySQL
Edit `config.py`:
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",   # change pass here
    "database": "stock_mgmt_db",
}
```

### 3. Create the database schema
```bash
mysql -u root -p < setup.sql
```

### 4. Run the application
```bash
python main.py
```

---

## Features

| # | Feature |
|---|---------|
| 1 | Add / Update / Delete products |
| 2 | Restock (IN) and Sell / Dispatch (OUT) |
| 3 | Manual stock adjustment (physical count) |
| 4 | Search by name or category |
| 5 | Low-stock alerts (per product threshold) |
| 6 | Inventory summary (total units, total value) |
| 7 | Full transaction history (IN / OUT / ADJUSTMENT) |
| 8 | Browse by category |

---

## Running Tests

```bash
# Basic run
python -m pytest tests/ -v

# With coverage report
pip install pytest-cov
python -m pytest tests/ --cov=.. --cov-report=term-missing
```

### Test breakdown (45 cases)

| Suite | Cases | What is tested |
|-------|-------|----------------|
| `TestProductModel` | TC-01 – TC-16 | Product creation, validation, stock mutation, equality |
| `TestTransactionModel` | TC-17 – TC-21 | Transaction creation, validation, serialisation |
| `TestStockManager` | TC-22 – TC-45 | All business operations with mocked DB |

---

## OOP Design

```
Product            ← domain entity; owns stock mutation logic
Transaction        ← immutable record of every stock movement
DatabaseManager    ← wraps mysql.connector; executes raw SQL
StockManager       ← orchestrates Product + DB; all business rules live here
```

---

## Technologies
- **Language**: Python 3.11+
- **Database**: MySQL 8.x via `mysql-connector-python`
- **Testing**: `unittest` + `unittest.mock` + `pytest` + `pytest-cov`
