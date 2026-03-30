import sys
from database import DatabaseManager
from stock_manager import StockManager
from models import Product

# colour helpers (ANSI)
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'═'*55}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'═'*55}{RESET}\n")

def success(msg: str) -> None: print(f"{GREEN}✔  {msg}{RESET}")
def error(msg: str)   -> None: print(f"{RED}✘  {msg}{RESET}")
def warn(msg: str)    -> None: print(f"{YELLOW}⚠  {msg}{RESET}")
def info(msg: str)    -> None: print(f"   {msg}")

# input helpers
def prompt(label: str, default: str = "") -> str:
    val = input(f"  {label}: ").strip()
    return val if val else default

def prompt_int(label: str) -> int:
    while True:
        try:
            return int(input(f"  {label}: ").strip())
        except ValueError:
            error("Please enter a whole number.")

def prompt_float(label: str) -> float:
    while True:
        try:
            return float(input(f"  {label}: ").strip())
        except ValueError:
            error("Please enter a number.")

#  MENU HANDLERS
def list_all_products(sm: StockManager) -> None:
    header("All Products")
    products = sm.get_all_products()
    if not products:
        warn("No products in catalogue.")
        return
    for p in products:
        print(f"  {p}")

def add_product(sm: StockManager) -> None:
    header("Add New Product")
    try:
        name      = prompt("Product name")
        category  = prompt("Category")
        price     = prompt_float("Price (₹)")
        quantity  = prompt_int("Initial quantity")
        min_stock = prompt_int("Minimum stock alert level")
        p = Product(name, category, price, quantity, min_stock)
        pid = sm.add_product(p)
        success(f"Product '{name}' added with ID {pid}.")
    except (ValueError, RuntimeError) as exc:
        error(str(exc))

def restock_product(sm: StockManager) -> None:
    header("Restock Product")
    try:
        pid    = prompt_int("Product ID")
        amount = prompt_int("Units to add")
        note   = prompt("Note (optional)", "Restock")
        product = sm.restock(pid, amount, note)
        success(f"New quantity for '{product.name}': {product.quantity}")
    except (ValueError, RuntimeError) as exc:
        error(str(exc))

def sell_product(sm: StockManager) -> None:
    header("Sell / Dispatch Stock")
    try:
        pid    = prompt_int("Product ID")
        amount = prompt_int("Units to sell")
        note   = prompt("Note (optional)", "Sale")
        product = sm.sell(pid, amount, note)
        success(f"New quantity for '{product.name}': {product.quantity}")
        if product.is_low_stock:
            warn(f"Low stock alert! Only {product.quantity} units remaining.")
    except (ValueError, RuntimeError) as exc:
        error(str(exc))

def adjust_stock(sm: StockManager) -> None:
    header("Adjust Stock (Physical Count)")
    try:
        pid      = prompt_int("Product ID")
        new_qty  = prompt_int("Actual quantity (new value)")
        note     = prompt("Note (optional)", "Physical count adjustment")
        product  = sm.adjust_stock(pid, new_qty, note)
        success(f"Stock for '{product.name}' set to {product.quantity}.")
    except (ValueError, RuntimeError) as exc:
        error(str(exc))

def search_products(sm: StockManager) -> None:
    header("Search Products")
    kw = prompt("Enter keyword")
    results = sm.search_products(kw)
    if not results:
        warn("No matching products found.")
    for p in results:
        print(f"  {p}")

def update_product(sm: StockManager) -> None:
    header("Update Product Details")
    try:
        pid = prompt_int("Product ID")
        p   = sm.get_product(pid)
        if p is None:
            error(f"No product with ID {pid}.")
            return
        info(f"Current: {p}")
        p.name      = prompt(f"New name       [{p.name}]",      p.name)
        p.category  = prompt(f"New category   [{p.category}]",  p.category)
        p.price     = float(prompt(f"New price      [{p.price}]",    str(p.price)))
        p.min_stock = int(prompt(f"New min stock  [{p.min_stock}]", str(p.min_stock)))
        sm.update_product(p)
        success("Product updated.")
    except (ValueError, RuntimeError) as exc:
        error(str(exc))

def delete_product(sm: StockManager) -> None:
    header("Delete Product")
    try:
        pid = prompt_int("Product ID to delete")
        p   = sm.get_product(pid)
        if p is None:
            error(f"No product with ID {pid}.")
            return
        confirm = prompt(f"Delete '{p.name}'? (yes/no)", "no")
        if confirm.lower() == "yes":
            sm.delete_product(pid)
            success(f"Product '{p.name}' deleted.")
        else:
            info("Deletion cancelled.")
    except (ValueError, RuntimeError) as exc:
        error(str(exc))

def show_low_stock(sm: StockManager) -> None:
    header("Low Stock Alert")
    products = sm.get_low_stock_products()
    if not products:
        success("All products are well-stocked!")
        return
    warn(f"{len(products)} product(s) need attention:")
    for p in products:
        print(f"  {p}")

def show_summary(sm: StockManager) -> None:
    header("Inventory Summary")
    s = sm.get_inventory_summary()
    print(f"  Total Products  : {s['total_products']}")
    print(f"  Total Units     : {s['total_units']}")
    print(f"  Total Value     : ₹{s['total_value']:.2f}")
    print(f"  Out of Stock    : {s['out_of_stock']}")

def show_transactions(sm: StockManager) -> None:
    header("Transaction History")
    choice = prompt("  1) All products  2) Single product", "1")
    if choice == "2":
        pid = prompt_int("Product ID")
        txns = sm.get_transaction_history(pid)
    else:
        txns = sm.get_all_transactions()
    if not txns:
        warn("No transactions found.")
        return
    for t in txns[:50]:   # cap display at 50 rows
        print(f"  {t}")

def show_categories(sm: StockManager) -> None:
    header("Product Categories")
    cats = sm.get_categories()
    if not cats:
        warn("No categories yet.")
        return
    for i, cat in enumerate(cats, 1):
        products = sm.get_products_by_category(cat)
        print(f"  {i}. {cat}  ({len(products)} products)")

#  MAIN LOOP
MENU = """
  ┌──────────────────────────────────────┐
  │      STOCK MANAGEMENT SYSTEM         │
  ├──────────────────────────────────────┤
  │  1.  List all products               │
  │  2.  Add new product                 │
  │  3.  Restock product                 │
  │  4.  Sell / dispatch stock           │
  │  5.  Adjust stock (physical count)   │
  │  6.  Search products                 │
  │  7.  Update product details          │
  │  8.  Delete product                  │
  │  9.  Low stock alerts                │
  │  10. Inventory summary               │
  │  11. Transaction history             │
  │  12. Browse by category              │
  │  0.  Exit                            │
  └──────────────────────────────────────┘
"""

ACTIONS = {
    "1":  list_all_products,
    "2":  add_product,
    "3":  restock_product,
    "4":  sell_product,
    "5":  adjust_stock,
    "6":  search_products,
    "7":  update_product,
    "8":  delete_product,
    "9":  show_low_stock,
    "10": show_summary,
    "11": show_transactions,
    "12": show_categories,
}


def main() -> None:
    print(f"\n{BOLD}Connecting to database…{RESET}")
    try:
        db = DatabaseManager()
        db.connect()
        success("Connected to MySQL.")
    except ConnectionError as exc:
        error(str(exc))
        info("Make sure MySQL is running and config.py has the correct credentials.")
        sys.exit(1)

    sm = StockManager(db)

    try:
        while True:
            print(MENU)
            choice = input("  Enter choice: ").strip()
            if choice == "0":
                success("Goodbye!")
                break
            action = ACTIONS.get(choice)
            if action:
                action(sm)
            else:
                error("Invalid choice. Please enter 0–12.")
    finally:
        db.disconnect()


if __name__ == "__main__":
    main()
