-- =====================================================
-- NStock seed data (MySQL 8+)
-- Run AFTER nstock_schema.sql.
-- Safe to re-run: it wipes the tables and reloads them,
-- so IDs always come out the same (1, 2, 3...).
--
-- Story: a small neighborhood market, September-October 2026.
-- After loading, the low-stock report should show 5 items:
--   Sparkling Water, Orange Juice, Trail Mix,
--   Dark Chocolate Bar, Dish Soap
-- =====================================================

USE nstock;

-- -----------------------------------------------------
-- 1) Clear everything
-- Foreign key checks are paused so tables can be emptied
-- in any order. TRUNCATE also resets AUTO_INCREMENT to 1.
-- -----------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE stock_movements;
TRUNCATE TABLE purchase_order_items;
TRUNCATE TABLE purchase_orders;
TRUNCATE TABLE products;
TRUNCATE TABLE suppliers;
TRUNCATE TABLE categories;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------
-- 2) Load "parent" tables first (nothing depends on others)
-- -----------------------------------------------------

-- user_id: 1 = owner, 2-3 = staff
INSERT INTO users (full_name, email, password_hash, role) VALUES
  ('Maria Lopez', 'maria@nstock.test', 'not-a-real-hash', 'owner'),
  ('Devon Price', 'devon@nstock.test', 'not-a-real-hash', 'staff'),
  ('Aisha Khan',  'aisha@nstock.test', 'not-a-real-hash', 'staff');

-- category_id: 1 Beverages, 2 Snacks, 3 Household, 4 Personal Care
INSERT INTO categories (name) VALUES
  ('Beverages'), ('Snacks'), ('Household'), ('Personal Care');

-- supplier_id: 1 Acme, 2 Coastal, 3 Harbor, 4 CleanPro
INSERT INTO suppliers (name, contact_name, email, phone) VALUES
  ('Acme Distributing',   'Pat Lee',      'pat@acme.test',     '562-555-0101'),
  ('Coastal Beverage Co.', 'Sam Ortiz',   'sam@coastal.test',  '562-555-0102'),
  ('Harbor Snack Supply', 'Jordan Wu',    'jordan@harbor.test','562-555-0103'),
  ('CleanPro Wholesale',  'Riley Brooks', 'riley@cleanpro.test','562-555-0104');

-- -----------------------------------------------------
-- 3) Products (need categories + suppliers to exist)
-- product_id is the row number, 1-15
-- -----------------------------------------------------
INSERT INTO products
  (sku, name, category_id, supplier_id, unit_cost, unit_price, reorder_point, is_active)
VALUES
  ('BEV-001', 'Sparkling Water 12oz',  1, 2, 0.40, 1.25, 24, TRUE),   -- 1
  ('BEV-002', 'Cold Brew Coffee 11oz', 1, 2, 1.80, 4.50, 12, TRUE),   -- 2
  ('BEV-003', 'Orange Juice 16oz',     1, 2, 1.50, 3.75, 12, TRUE),   -- 3
  ('BEV-004', 'Green Tea 16oz',        1, 2, 0.90, 2.50, 18, TRUE),   -- 4
  ('SNK-001', 'Trail Mix 6oz',         2, 3, 1.10, 3.00, 10, TRUE),   -- 5
  ('SNK-002', 'Kettle Chips 2oz',      2, 3, 0.55, 1.75, 24, TRUE),   -- 6
  ('SNK-003', 'Protein Bar',           2, 3, 1.20, 2.99, 15, TRUE),   -- 7
  ('SNK-004', 'Dark Chocolate Bar',    2, 3, 1.00, 2.75, 12, TRUE),   -- 8
  ('HSE-001', 'Paper Towels 2pk',      3, 4, 2.10, 4.99,  8, TRUE),   -- 9
  ('HSE-002', 'Dish Soap 16oz',        3, 4, 1.40, 3.49,  6, TRUE),   -- 10
  ('HSE-003', 'Trash Bags 20ct',       3, 4, 3.00, 6.99,  6, TRUE),   -- 11
  ('PRC-001', 'Hand Sanitizer 8oz',    4, 1, 1.25, 3.99, 10, TRUE),   -- 12
  ('PRC-002', 'Toothpaste 4oz',        4, 1, 1.60, 3.79,  8, TRUE),   -- 13
  ('PRC-003', 'Lip Balm',              4, 1, 0.60, 1.99, 12, TRUE),   -- 14
  ('SNK-005', 'Summer Fruit Gummies',  2, 3, 0.80, 2.25,  0, FALSE);  -- 15 (discontinued)

-- -----------------------------------------------------
-- 4) Purchase orders (need suppliers + users)
-- Mix of statuses so every app screen has something to show
-- -----------------------------------------------------
INSERT INTO purchase_orders (supplier_id, created_by, status, order_date, expected_date) VALUES
  (2, 1, 'received', '2026-09-01', '2026-09-03'),  -- PO 1: Coastal
  (3, 1, 'received', '2026-09-02', '2026-09-04'),  -- PO 2: Harbor
  (4, 1, 'received', '2026-09-05', '2026-09-08'),  -- PO 3: CleanPro
  (1, 2, 'received', '2026-09-08', '2026-09-10'),  -- PO 4: Acme
  (2, 1, 'ordered',  '2026-10-08', '2026-10-14'),  -- PO 5: on the way
  (3, 2, 'draft',    NULL,         NULL);          -- PO 6: not sent yet

INSERT INTO purchase_order_items (po_id, product_id, quantity, unit_cost) VALUES
  (1, 1, 96, 0.40), (1, 2, 36, 1.80), (1, 3, 36, 1.50), (1, 4, 48, 0.90),
  (2, 5, 30, 1.10), (2, 6, 72, 0.55), (2, 7, 45, 1.20), (2, 8, 36, 1.00), (2, 15, 24, 0.80),
  (3, 9, 24, 2.10), (3, 10, 18, 1.40), (3, 11, 18, 3.00),
  (4, 12, 30, 1.25), (4, 13, 24, 1.60), (4, 14, 36, 0.60),
  (5, 1, 48, 0.40), (5, 2, 24, 1.80),
  (6, 6, 48, 0.55), (6, 8, 24, 1.00);

-- -----------------------------------------------------
-- 5) Stock movements (need products, users, POs)
-- Receipts only for POs marked 'received' (1-4).
-- Positive = in, negative = out.
-- -----------------------------------------------------

-- Receipts, matching the PO lines above
INSERT INTO stock_movements (product_id, user_id, movement_type, quantity, po_id, note, created_at) VALUES
  (1, 2, 'receive', 96, 1, 'PO #1', '2026-09-03 09:15:00'),
  (2, 2, 'receive', 36, 1, 'PO #1', '2026-09-03 09:15:00'),
  (3, 2, 'receive', 36, 1, 'PO #1', '2026-09-03 09:15:00'),
  (4, 2, 'receive', 48, 1, 'PO #1', '2026-09-03 09:15:00'),
  (5, 3, 'receive', 30, 2, 'PO #2', '2026-09-04 10:00:00'),
  (6, 3, 'receive', 72, 2, 'PO #2', '2026-09-04 10:00:00'),
  (7, 3, 'receive', 45, 2, 'PO #2', '2026-09-04 10:00:00'),
  (8, 3, 'receive', 36, 2, 'PO #2', '2026-09-04 10:00:00'),
  (15, 3, 'receive', 24, 2, 'PO #2', '2026-09-04 10:00:00'),
  (9, 2, 'receive', 24, 3, 'PO #3', '2026-09-08 14:30:00'),
  (10, 2, 'receive', 18, 3, 'PO #3', '2026-09-08 14:30:00'),
  (11, 2, 'receive', 18, 3, 'PO #3', '2026-09-08 14:30:00'),
  (12, 1, 'receive', 30, 4, 'PO #4', '2026-09-10 11:45:00'),
  (13, 1, 'receive', 24, 4, 'PO #4', '2026-09-10 11:45:00'),
  (14, 1, 'receive', 36, 4, 'PO #4', '2026-09-10 11:45:00');

-- Sales (grouped as a few batches per product to keep this readable)
INSERT INTO stock_movements (product_id, user_id, movement_type, quantity, note, created_at) VALUES
  (1, 2, 'sale', -45, NULL, '2026-09-15 17:00:00'),
  (1, 3, 'sale', -35, NULL, '2026-10-01 17:00:00'),
  (2, 2, 'sale', -20, NULL, '2026-09-20 17:00:00'),
  (3, 3, 'sale', -30, NULL, '2026-09-25 17:00:00'),
  (4, 2, 'sale', -25, NULL, '2026-09-28 17:00:00'),
  (5, 3, 'sale', -22, NULL, '2026-10-02 17:00:00'),
  (6, 2, 'sale', -40, NULL, '2026-09-30 17:00:00'),
  (7, 3, 'sale', -18, NULL, '2026-09-29 17:00:00'),
  (8, 2, 'sale', -26, NULL, '2026-10-03 17:00:00'),
  (9, 3, 'sale', -10, NULL, '2026-09-27 17:00:00'),
  (10, 2, 'sale', -13, NULL, '2026-10-04 17:00:00'),
  (11, 3, 'sale',  -5, NULL, '2026-10-05 17:00:00'),
  (12, 2, 'sale', -12, NULL, '2026-10-06 17:00:00'),
  (13, 3, 'sale',  -9, NULL, '2026-10-06 17:00:00'),
  (14, 2, 'sale', -20, NULL, '2026-10-07 17:00:00'),
  (15, 3, 'sale', -24, 'Sold out before discontinuing', '2026-09-30 17:00:00');

-- Adjustments and returns (the messy real-world stuff)
INSERT INTO stock_movements (product_id, user_id, movement_type, quantity, note, created_at) VALUES
  (3, 1, 'adjustment', -2, 'Expired, discarded',          '2026-10-05 08:30:00'),
  (6, 1, 'adjustment', -3, 'Damaged bags found in stock', '2026-10-02 08:30:00'),
  (7, 3, 'return',      1, 'Customer return, unopened',   '2026-10-01 12:10:00');

-- -----------------------------------------------------
-- 6) Quick checks: run these to confirm the load
-- -----------------------------------------------------

-- Row counts (expect 3, 4, 4, 15, 6, 19, 34)
SELECT 'users' AS tbl, COUNT(*) AS row_count FROM users
UNION ALL SELECT 'categories', COUNT(*) FROM categories
UNION ALL SELECT 'suppliers', COUNT(*) FROM suppliers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'purchase_orders', COUNT(*) FROM purchase_orders
UNION ALL SELECT 'purchase_order_items', COUNT(*) FROM purchase_order_items
UNION ALL SELECT 'stock_movements', COUNT(*) FROM stock_movements;

-- Low-stock report (expect 5 rows)
SELECT p.sku, p.name, p.reorder_point, COALESCE(SUM(m.quantity), 0) AS on_hand
FROM products p
LEFT JOIN stock_movements m ON m.product_id = p.product_id
WHERE p.is_active = TRUE
GROUP BY p.product_id, p.sku, p.name, p.reorder_point
HAVING on_hand <= p.reorder_point
ORDER BY on_hand;
