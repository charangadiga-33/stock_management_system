CREATE DATABASE IF NOT EXISTS stock_mgmt_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE stock_mgmt_db;

-- products
CREATE TABLE IF NOT EXISTS products (
    product_id  INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(120)   NOT NULL,
    category    VARCHAR(80)    NOT NULL,
    price       DECIMAL(12,2)  NOT NULL,
    quantity    INT            NOT NULL DEFAULT 0,
    min_stock   INT            NOT NULL DEFAULT 10,
    created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_price    CHECK (price    >= 0),
    CONSTRAINT chk_quantity CHECK (quantity >= 0),
    CONSTRAINT chk_min      CHECK (min_stock >= 0)
);

-- transactions
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   INT AUTO_INCREMENT PRIMARY KEY,
    product_id       INT          NOT NULL,
    transaction_type ENUM('IN','OUT','ADJUSTMENT') NOT NULL,
    quantity         INT          NOT NULL,
    note             VARCHAR(255) DEFAULT '',
    timestamp        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_txn_qty CHECK (quantity > 0),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE CASCADE
);

-- seed data (optional)
INSERT INTO products (name, category, price, quantity, min_stock) VALUES
    ('USB-C Hub',         'Electronics',   1299.00, 45,  10),
    ('Wireless Mouse',    'Electronics',    799.00, 30,   8),
    ('A4 Paper Ream',     'Stationery',     180.00, 100, 20),
    ('Ball Pen Box',      'Stationery',      75.00,  60, 15),
    ('Office Chair',      'Furniture',     5999.00,   8,  3),
    ('Standing Desk',     'Furniture',    12999.00,   4,  2),
    ('Hand Sanitizer',    'Hygiene',        120.00,  75, 20),
    ('Laptop Stand',      'Electronics',   1499.00,  12,  5);

INSERT INTO transactions (product_id, transaction_type, quantity, note)
SELECT product_id, 'IN', quantity, 'Seed data – initial stock'
FROM   products;
