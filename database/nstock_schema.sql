-- =====================================================
-- NStock starter schema (MySQL 8+)
-- Small-business inventory tool
-- Run this whole file in MySQL Workbench or the mysql CLI.
-- =====================================================

DROP DATABASE IF EXISTS nstock;
CREATE DATABASE nstock;
USE nstock;

-- -----------------------------------------------------
-- Who can log in to the app
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
-- -----------------------------------------------------
CREATE TABLE suppliers (
    supplier_id    INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(150) NOT NULL,
    contact_name   VARCHAR(100),
    email          VARCHAR(255),
    phone          VARCHAR(30)
);

-- -----------------------------------------------------
-- The items being tracked
-- Note: there is NO quantity column here on purpose.
-- On-hand quantity is calculated from stock_movements.
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
-- One PO has many lines -> two tables
-- -----------------------------------------------------
CREATE TABLE purchase_orders (
    po_id          INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id    INT NOT NULL,
    created_by     INT NOT NULL,
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
-- -----------------------------------------------------
CREATE TABLE stock_movements (
    movement_id    INT AUTO_INCREMENT PRIMARY KEY,
    product_id     INT NOT NULL,
    user_id        INT NOT NULL,
    movement_type  ENUM('receive','sale','adjustment','return') NOT NULL,
    quantity       INT NOT NULL,
    po_id          INT NULL,                       -- filled when type = 'receive'
    note           VARCHAR(255),
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (user_id)    REFERENCES users(user_id),
    FOREIGN KEY (po_id)      REFERENCES purchase_orders(po_id)
);

-- =====================================================
-- Sample data so you can test
-- =====================================================
INSERT INTO users (full_name, email, password_hash, role) VALUES
  ('Test Owner', 'owner@example.com', 'hash-goes-here', 'owner'),
  ('Test Staff', 'staff@example.com', 'hash-goes-here', 'staff');

INSERT INTO categories (name) VALUES ('Beverages'), ('Snacks');

INSERT INTO suppliers (name, contact_name, email) VALUES
  ('Acme Distributing', 'Pat Lee', 'pat@acme.example');

INSERT INTO products (sku, name, category_id, supplier_id, unit_cost, unit_price, reorder_point) VALUES
  ('BEV-001', 'Sparkling Water 12oz', 1, 1, 0.40, 1.25, 24),
  ('SNK-001', 'Trail Mix 6oz',        2, 1, 1.10, 3.00, 10);

INSERT INTO purchase_orders (supplier_id, created_by, status, order_date) VALUES
  (1, 1, 'received', CURDATE());

INSERT INTO purchase_order_items (po_id, product_id, quantity, unit_cost) VALUES
  (1, 1, 48, 0.40),
  (1, 2, 20, 1.10);

INSERT INTO stock_movements (product_id, user_id, movement_type, quantity, po_id, note) VALUES
  (1, 1, 'receive', 48, 1, 'PO #1'),
  (2, 1, 'receive', 20, 1, 'PO #1'),
  (1, 2, 'sale',   -30, NULL, NULL),
  (2, 2, 'sale',   -12, NULL, NULL);

-- =====================================================
-- Queries your app will actually need
-- =====================================================

-- 1) Current on-hand quantity for every product
SELECT p.sku, p.name, COALESCE(SUM(m.quantity), 0) AS on_hand
FROM products p
LEFT JOIN stock_movements m ON m.product_id = p.product_id
GROUP BY p.product_id, p.sku, p.name;

-- 2) Low-stock report (at or below reorder point)
SELECT p.sku, p.name, p.reorder_point, COALESCE(SUM(m.quantity), 0) AS on_hand
FROM products p
LEFT JOIN stock_movements m ON m.product_id = p.product_id
WHERE p.is_active = TRUE
GROUP BY p.product_id, p.sku, p.name, p.reorder_point
HAVING on_hand <= p.reorder_point;

-- 3) Movement history for one product
SELECT m.created_at, m.movement_type, m.quantity, u.full_name, m.note
FROM stock_movements m
JOIN users u ON u.user_id = m.user_id
WHERE m.product_id = 1
ORDER BY m.created_at DESC;
