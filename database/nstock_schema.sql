-- =====================================================
-- NStock schema (MySQL 8+)
-- Small-business inventory tool
-- Run this whole file in MySQL Workbench or the mysql CLI,
-- then run nstock_seed.sql.
--
-- Change log
--   v1 (Oct 2026)  First version: 7 tables, stock kept as a ledger.
--   v2 (Nov 2026)  Matched to the FastAPI backend:
--     - purchase_orders.created_by and stock_movements.user_id are
--       now optional, since login is out of scope for the prototype
--     - suppliers get is_active, so deleting one that's in use can be
--       a "deactivate" instead of a foreign key error
--     - stock_movements.po_id is set to NULL if its PO is deleted
--     - indexes on stock_movements for the history and report queries
--     - new view product_stock: on-hand quantity per product
--     - sample rows moved out; nstock_seed.sql loads the demo data
--   Column names did not change, so nstock_seed.sql still runs as is.
-- =====================================================

DROP DATABASE IF EXISTS nstock;
CREATE DATABASE nstock;
USE nstock;

-- -----------------------------------------------------
-- Who can log in to the app
-- (Login is future work; kept so records can say who did what later.)
-- -----------------------------------------------------
CREATE TABLE users (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    full_name      VARCHAR(100) NOT NULL,
    email          VARCHAR(255) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,          -- never store plain passwords
    role           ENUM('owner','staff') NOT NULL DEFAULT 'staff',
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------
-- Product groupings (e.g., "Beverages", "Cleaning")
-- -----------------------------------------------------
CREATE TABLE categories (
    category_id    INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(100) NOT NULL UNIQUE
);

-- -----------------------------------------------------
-- Vendors the business buys from
-- API: Supplier {name, email, phone}
-- -----------------------------------------------------
CREATE TABLE suppliers (
    supplier_id    INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(150) NOT NULL,
    contact_name   VARCHAR(100),
    email          VARCHAR(255),
    phone          VARCHAR(30),
    is_active      BOOLEAN NOT NULL DEFAULT TRUE   -- "delete" by deactivating
);

-- -----------------------------------------------------
-- The items being tracked
-- API: Product {sku, name, price, quantity}
--   price    -> unit_price
--   quantity -> NOT stored here. It's the sum of stock_movements
--               (see the product_stock view). Setting a quantity
--               through the API means inserting an 'adjustment' row.
-- -----------------------------------------------------
CREATE TABLE products (
    product_id     INT AUTO_INCREMENT PRIMARY KEY,
    sku            VARCHAR(50)  NOT NULL UNIQUE,
    name           VARCHAR(150) NOT NULL,
    category_id    INT,
    supplier_id    INT,                            -- preferred supplier
    unit_cost      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    unit_price     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    reorder_point  INT NOT NULL DEFAULT 0,         -- alert when stock falls to this
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,  -- "delete" by deactivating
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- -----------------------------------------------------
-- Purchase orders (header) and their lines
-- One PO has many lines -> two tables.
-- API: PurchaseOrder {product_id, supplier_id, quantity, status}
--   The API sends one product per PO for now, so the backend writes
--   one header row + one line row. Status values must be one of the
--   ENUM values below.
-- -----------------------------------------------------
CREATE TABLE purchase_orders (
    po_id          INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id    INT NOT NULL,
    created_by     INT NULL,                       -- optional until login exists
    status         ENUM('draft','ordered','received','cancelled') NOT NULL DEFAULT 'draft',
    order_date     DATE,
    expected_date  DATE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (created_by)  REFERENCES users(user_id)
);

CREATE TABLE purchase_order_items (
    po_item_id     INT AUTO_INCREMENT PRIMARY KEY,
    po_id          INT NOT NULL,
    product_id     INT NOT NULL,
    quantity       INT NOT NULL CHECK (quantity > 0),
    unit_cost      DECIMAL(10,2) NOT NULL,         -- cost at time of order
    FOREIGN KEY (po_id)      REFERENCES purchase_orders(po_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- -----------------------------------------------------
-- Every change to stock is a row here (a ledger).
-- Positive quantity = stock in, negative = stock out.
-- API: StockTransaction {product_id, quantity, transaction_type}
--   IN  -> movement_type 'receive', quantity stored as positive
--   OUT -> movement_type 'sale',    quantity stored as negative
-- The backend blocks an OUT that would take stock below zero.
-- -----------------------------------------------------
CREATE TABLE stock_movements (
    movement_id    INT AUTO_INCREMENT PRIMARY KEY,
    product_id     INT NOT NULL,
    user_id        INT NULL,                       -- optional until login exists
    movement_type  ENUM('receive','sale','adjustment','return') NOT NULL,
    quantity       INT NOT NULL CHECK (quantity <> 0),
    po_id          INT NULL,                       -- filled when type = 'receive'
    note           VARCHAR(255),
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (user_id)    REFERENCES users(user_id),
    FOREIGN KEY (po_id)      REFERENCES purchase_orders(po_id) ON DELETE SET NULL,
    INDEX idx_movements_product_date (product_id, created_at),
    INDEX idx_movements_date (created_at)
);

-- -----------------------------------------------------
-- On-hand quantity per product.
-- The backend reads "quantity" from here instead of storing it.
-- -----------------------------------------------------
CREATE VIEW product_stock AS
SELECT p.product_id,
       COALESCE(SUM(m.quantity), 0) AS on_hand
FROM products p
LEFT JOIN stock_movements m ON m.product_id = p.product_id
GROUP BY p.product_id;


-- =====================================================
-- Queries the backend needs (copy into the API code)
-- =====================================================

-- 1) Products with their on-hand quantity
-- SELECT p.*, s.on_hand
-- FROM products p JOIN product_stock s ON s.product_id = p.product_id
-- WHERE p.is_active = TRUE;

-- 2) Low stock (at or below reorder point)
-- SELECT p.product_id, p.sku, p.name, p.reorder_point, s.on_hand
-- FROM products p JOIN product_stock s ON s.product_id = p.product_id
-- WHERE p.is_active = TRUE AND s.on_hand <= p.reorder_point
-- ORDER BY s.on_hand - p.reorder_point;

-- 3) Slow movers: in stock, but 2 or fewer units sold in the last 30 days
-- SELECT p.product_id, p.sku, p.name, s.on_hand,
--        COALESCE(SUM(CASE WHEN m.created_at >= CURDATE() - INTERVAL 30 DAY
--                          THEN -m.quantity END), 0) AS sold_30d,
--        MAX(m.created_at) AS last_sale
-- FROM products p
-- JOIN product_stock s ON s.product_id = p.product_id
-- LEFT JOIN stock_movements m
--        ON m.product_id = p.product_id AND m.movement_type = 'sale'
-- WHERE p.is_active = TRUE AND s.on_hand > 0
-- GROUP BY p.product_id, p.sku, p.name, s.on_hand
-- HAVING sold_30d <= 2
-- ORDER BY sold_30d, last_sale;

-- 4) Turnover over the last 90 days
--    turnover = units sold / average on hand
--    average on hand = (on hand 90 days ago + on hand now) / 2
-- SELECT p.product_id, p.sku, p.name,
--        COALESCE(SUM(CASE WHEN m.movement_type = 'sale'
--                           AND m.created_at >= CURDATE() - INTERVAL 90 DAY
--                          THEN -m.quantity END), 0) AS sold_90d,
--        COALESCE(SUM(CASE WHEN m.created_at < CURDATE() - INTERVAL 90 DAY
--                          THEN m.quantity END), 0) AS on_hand_start,
--        COALESCE(SUM(m.quantity), 0) AS on_hand_now,
--        ROUND(
--          COALESCE(SUM(CASE WHEN m.movement_type = 'sale'
--                             AND m.created_at >= CURDATE() - INTERVAL 90 DAY
--                            THEN -m.quantity END), 0)
--          / NULLIF((COALESCE(SUM(CASE WHEN m.created_at < CURDATE() - INTERVAL 90 DAY
--                                      THEN m.quantity END), 0)
--                    + COALESCE(SUM(m.quantity), 0)) / 2, 0)
--        , 2) AS turnover_90d
-- FROM products p
-- LEFT JOIN stock_movements m ON m.product_id = p.product_id
-- WHERE p.is_active = TRUE
-- GROUP BY p.product_id, p.sku, p.name
-- ORDER BY turnover_90d DESC;

-- 5) Movement history for one product
-- SELECT created_at, movement_type, quantity, note
-- FROM stock_movements WHERE product_id = 1
-- ORDER BY created_at DESC;
