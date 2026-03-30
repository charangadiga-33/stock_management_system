#  tests/test_stock_management.py
#
#  25+ automated test cases  –  target ≈ 90% coverage
#  Run:  python -m pytest tests/ -v --tb=short
#        python -m pytest tests/ --cov=.. --cov-report=term-missing

import sys
import os
import unittest
from unittest.mock import MagicMock, call, patch
from datetime import datetime

# make parent package importable 
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import Product, Transaction
from stock_manager import StockManager

#  HELPER  –  build a pre-configured mock DatabaseManager
def _make_db(**kwargs) -> MagicMock:
    db = MagicMock()
    db.execute_query.return_value = kwargs.get("execute_query", 1)
    db.fetch_one.return_value     = kwargs.get("fetch_one", None)
    db.fetch_all.return_value     = kwargs.get("fetch_all", [])
    return db

def _product_row(
    pid=1, name="Widget", category="Electronics",
    price=99.99, quantity=50, min_stock=10
) -> dict:
    return dict(product_id=pid, name=name, category=category,
                price=price, quantity=quantity, min_stock=min_stock)


#  TEST SUITE 1 – Product model
class TestProductModel(unittest.TestCase):

    # TC-01
    def test_product_creation_valid(self):
        p = Product("Widget", "Electronics", 99.99, 50, 10)
        self.assertEqual(p.name, "Widget")
        self.assertEqual(p.price, 99.99)
        self.assertEqual(p.quantity, 50)
        self.assertIsNone(p.product_id)

    # TC-02
    def test_product_total_value(self):
        p = Product("Widget", "Electronics", 10.0, 5)
        self.assertAlmostEqual(p.total_value, 50.0)

    # TC-03
    def test_product_is_low_stock_true(self):
        p = Product("Widget", "Electronics", 10.0, 5, min_stock=10)
        self.assertTrue(p.is_low_stock)

    # TC-04
    def test_product_is_low_stock_false(self):
        p = Product("Widget", "Electronics", 10.0, 50, min_stock=10)
        self.assertFalse(p.is_low_stock)

    # TC-05
    def test_product_is_low_stock_at_boundary(self):
        p = Product("Widget", "Electronics", 10.0, 10, min_stock=10)
        self.assertTrue(p.is_low_stock)   # exactly at threshold → low stock

    # TC-06
    def test_add_stock_increases_quantity(self):
        p = Product("Widget", "Electronics", 10.0, 20)
        p.add_stock(5)
        self.assertEqual(p.quantity, 25)

    # TC-07
    def test_remove_stock_decreases_quantity(self):
        p = Product("Widget", "Electronics", 10.0, 20)
        p.remove_stock(5)
        self.assertEqual(p.quantity, 15)

    # TC-08
    def test_remove_stock_insufficient_raises(self):
        p = Product("Widget", "Electronics", 10.0, 3)
        with self.assertRaises(ValueError):
            p.remove_stock(10)

    # TC-09
    def test_product_empty_name_raises(self):
        with self.assertRaises(ValueError):
            Product("", "Electronics", 10.0, 5)

    # TC-10
    def test_product_negative_price_raises(self):
        with self.assertRaises(ValueError):
            Product("Widget", "Electronics", -1.0, 5)

    # TC-11
    def test_product_negative_quantity_raises(self):
        with self.assertRaises(ValueError):
            Product("Widget", "Electronics", 10.0, -1)

    # TC-12
    def test_product_to_dict(self):
        p = Product("Widget", "Electronics", 10.0, 5, product_id=7)
        d = p.to_dict()
        self.assertEqual(d["product_id"], 7)
        self.assertEqual(d["name"], "Widget")
        self.assertIn("total_value", d)
        self.assertIn("is_low_stock", d)

    # TC-13
    def test_product_equality_same_id(self):
        p1 = Product("Widget", "Electronics", 10.0, 5, product_id=1)
        p2 = Product("Gadget", "Tools",       20.0, 3, product_id=1)
        self.assertEqual(p1, p2)

    # TC-14
    def test_product_equality_diff_id(self):
        p1 = Product("Widget", "Electronics", 10.0, 5, product_id=1)
        p2 = Product("Widget", "Electronics", 10.0, 5, product_id=2)
        self.assertNotEqual(p1, p2)

    # TC-15
    def test_add_stock_zero_raises(self):
        p = Product("Widget", "Electronics", 10.0, 20)
        with self.assertRaises(ValueError):
            p.add_stock(0)

    # TC-16
    def test_remove_stock_zero_raises(self):
        p = Product("Widget", "Electronics", 10.0, 20)
        with self.assertRaises(ValueError):
            p.remove_stock(0)

#  TEST SUITE 2 – Transaction model
class TestTransactionModel(unittest.TestCase):

    # TC-17
    def test_transaction_creation_valid(self):
        t = Transaction(1, "IN", 10, "Test")
        self.assertEqual(t.product_id, 1)
        self.assertEqual(t.transaction_type, "IN")
        self.assertEqual(t.quantity, 10)

    # TC-18
    def test_transaction_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            Transaction(1, "WRONG", 10)

    # TC-19
    def test_transaction_zero_quantity_raises(self):
        with self.assertRaises(ValueError):
            Transaction(1, "IN", 0)

    # TC-20
    def test_transaction_to_dict(self):
        t = Transaction(1, "OUT", 5, "Sale", transaction_id=99)
        d = t.to_dict()
        self.assertEqual(d["transaction_id"], 99)
        self.assertEqual(d["transaction_type"], "OUT")

    # TC-21
    def test_transaction_default_timestamp(self):
        before = datetime.now()
        t = Transaction(1, "IN", 1)
        after = datetime.now()
        self.assertGreaterEqual(t.timestamp, before)
        self.assertLessEqual(t.timestamp, after)


#  TEST SUITE 3 – StockManager (DB mocked)
class TestStockManager(unittest.TestCase):

    # TC-22  add_product – happy path
    def test_add_product_success(self):
        db = _make_db(fetch_one=None, execute_query=42)
        sm = StockManager(db)
        p  = Product("Widget", "Electronics", 99.99, 20, 5)
        pid = sm.add_product(p)
        self.assertEqual(pid, 42)
        self.assertEqual(p.product_id, 42)

    # TC-23  add_product – duplicate name raises
    def test_add_product_duplicate_name(self):
        db = _make_db(fetch_one={"product_id": 1})
        sm = StockManager(db)
        p  = Product("Widget", "Electronics", 99.99, 20)
        with self.assertRaises(ValueError):
            sm.add_product(p)

    # TC-24  get_product – found
    def test_get_product_found(self):
        row = _product_row()
        db  = _make_db(fetch_one=row)
        sm  = StockManager(db)
        p   = sm.get_product(1)
        self.assertIsNotNone(p)
        self.assertEqual(p.name, "Widget")

    # TC-25  get_product – not found
    def test_get_product_not_found(self):
        db = _make_db(fetch_one=None)
        sm = StockManager(db)
        self.assertIsNone(sm.get_product(999))

    # TC-26  get_all_products
    def test_get_all_products(self):
        rows = [_product_row(pid=1, name="A"), _product_row(pid=2, name="B")]
        db   = _make_db(fetch_all=rows)
        sm   = StockManager(db)
        products = sm.get_all_products()
        self.assertEqual(len(products), 2)

    # TC-27  restock – increases quantity
    def test_restock_success(self):
        row = _product_row(quantity=10)
        db  = _make_db(fetch_one=row)
        sm  = StockManager(db)
        p   = sm.restock(1, 5, "Top-up")
        self.assertEqual(p.quantity, 15)

    # TC-28  restock – invalid product raises
    def test_restock_invalid_product(self):
        db = _make_db(fetch_one=None)
        sm = StockManager(db)
        with self.assertRaises(ValueError):
            sm.restock(999, 5)

    # TC-29  sell – decreases quantity
    def test_sell_success(self):
        row = _product_row(quantity=20)
        db  = _make_db(fetch_one=row)
        sm  = StockManager(db)
        p   = sm.sell(1, 8, "Order #100")
        self.assertEqual(p.quantity, 12)

    # TC-30  sell – insufficient stock raises
    def test_sell_insufficient_stock(self):
        row = _product_row(quantity=2)
        db  = _make_db(fetch_one=row)
        sm  = StockManager(db)
        with self.assertRaises(ValueError):
            sm.sell(1, 10)

    # TC-31  adjust_stock – sets exact value
    def test_adjust_stock_exact(self):
        row = _product_row(quantity=30)
        db  = _make_db(fetch_one=row)
        sm  = StockManager(db)
        p   = sm.adjust_stock(1, 15, "Count result")
        self.assertEqual(p.quantity, 15)

    # TC-32  adjust_stock – negative raises
    def test_adjust_stock_negative_raises(self):
        row = _product_row(quantity=10)
        db  = _make_db(fetch_one=row)
        sm  = StockManager(db)
        with self.assertRaises(ValueError):
            sm.adjust_stock(1, -5)

    # TC-33  delete_product – calls DB
    def test_delete_product(self):
        db = _make_db(execute_query=1)
        sm = StockManager(db)
        result = sm.delete_product(1)
        self.assertTrue(result)
        db.execute_query.assert_called_once()

    # TC-34  update_product – no ID raises
    def test_update_product_no_id_raises(self):
        db = _make_db()
        sm = StockManager(db)
        p  = Product("Widget", "Electronics", 10.0, 5)  # no product_id
        with self.assertRaises(ValueError):
            sm.update_product(p)

    # TC-35  search_products – delegates to DB
    def test_search_products(self):
        rows = [_product_row(name="Widget A"), _product_row(pid=2, name="Widget B")]
        db   = _make_db(fetch_all=rows)
        sm   = StockManager(db)
        results = sm.search_products("Widget")
        self.assertEqual(len(results), 2)

    # TC-36  get_low_stock_products
    def test_get_low_stock_products(self):
        row = _product_row(quantity=3, min_stock=10)
        db  = _make_db(fetch_all=[row])
        sm  = StockManager(db)
        low = sm.get_low_stock_products()
        self.assertEqual(len(low), 1)
        self.assertTrue(low[0].is_low_stock)

    # TC-37  get_inventory_summary
    def test_get_inventory_summary(self):
        summary_row = {
            "total_products": 5,
            "total_units": 120,
            "total_value": 4500.0,
            "out_of_stock": 1,
        }
        db = _make_db(fetch_one=summary_row)
        sm = StockManager(db)
        s  = sm.get_inventory_summary()
        self.assertEqual(s["total_products"], 5)
        self.assertAlmostEqual(s["total_value"], 4500.0)

    # TC-38  get_transaction_history
    def test_get_transaction_history(self):
        txn_rows = [
            dict(transaction_id=1, product_id=1, transaction_type="IN",
                 quantity=20, note="Initial", timestamp=datetime.now()),
            dict(transaction_id=2, product_id=1, transaction_type="OUT",
                 quantity=5,  note="Sale",    timestamp=datetime.now()),
        ]
        db   = _make_db(fetch_all=txn_rows)
        sm   = StockManager(db)
        txns = sm.get_transaction_history(1)
        self.assertEqual(len(txns), 2)
        self.assertIsInstance(txns[0], Transaction)

    # TC-39  get_categories
    def test_get_categories(self):
        db = _make_db(fetch_all=[{"category": "Electronics"}, {"category": "Tools"}])
        sm = StockManager(db)
        cats = sm.get_categories()
        self.assertEqual(cats, ["Electronics", "Tools"])

    # TC-40  restock with zero amount raises via Product model
    def test_restock_zero_amount_raises(self):
        row = _product_row(quantity=10)
        db  = _make_db(fetch_one=row)
        sm  = StockManager(db)
        with self.assertRaises(ValueError):
            sm.restock(1, 0)

    # TC-41  add_product with zero initial quantity (no IN transaction)
    def test_add_product_zero_quantity_no_transaction(self):
        db = _make_db(fetch_one=None, execute_query=5)
        sm = StockManager(db)
        p  = Product("Bolt", "Hardware", 0.50, 0)
        sm.add_product(p)
        # execute_query should be called only once (INSERT product, no txn)
        self.assertEqual(db.execute_query.call_count, 1)

    # TC-42  adjust_stock with same quantity (no transaction recorded)
    def test_adjust_stock_same_quantity_no_transaction(self):
        row = _product_row(quantity=20)
        db  = _make_db(fetch_one=row)
        sm  = StockManager(db)
        sm.adjust_stock(1, 20)
        # Only the UPDATE query fires; no transaction INSERT
        for c in db.execute_query.call_args_list:
            args = c[0][0].strip().upper()
            self.assertFalse(args.startswith("INSERT INTO TRANSACTIONS"),
                             "Should not insert a transaction for no-change adjustment")

    # TC-43  Product __str__ contains LOW STOCK warning when applicable
    def test_product_str_low_stock_indicator(self):
        p = Product("Widget", "Electronics", 10.0, 3, min_stock=10, product_id=1)
        self.assertIn("LOW STOCK", str(p))

    # TC-44  get_products_by_category
    def test_get_products_by_category(self):
        rows = [_product_row(category="Tools"), _product_row(pid=2, name="Hammer", category="Tools")]
        db   = _make_db(fetch_all=rows)
        sm   = StockManager(db)
        result = sm.get_products_by_category("Tools")
        self.assertEqual(len(result), 2)

    # TC-45  get_all_transactions
    def test_get_all_transactions(self):
        txn_rows = [
            dict(transaction_id=i, product_id=1, transaction_type="IN",
                 quantity=10, note="", timestamp=datetime.now())
            for i in range(3)
        ]
        db   = _make_db(fetch_all=txn_rows)
        sm   = StockManager(db)
        txns = sm.get_all_transactions()
        self.assertEqual(len(txns), 3)


#  ENTRY POINT
if __name__ == "__main__":
    unittest.main(verbosity=2)
