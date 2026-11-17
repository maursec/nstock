-- =====================================================
-- NStock seed refresh (run AFTER nstock_seed.sql)
--
-- 1) Moves every date in the demo data forward so the most recent
--    stock movement is today. The original seed is dated Sept-Oct
--    2026, so without this, a "last 30 days" report on demo day
--    would show almost no sales and every product would look like
--    a slow mover. Run it again right before the demo.
--
-- 2) Adds one product that clearly sells slowly, so the
--    slow-mover report always has something to show.
--
-- Safe to re-run with the seed: reload nstock_seed.sql, then this.
-- =====================================================

USE nstock;

-- -----------------------------------------------------
-- 1) Shift dates so the newest movement lands on today
-- -----------------------------------------------------
SET @shift_days = (
    SELECT DATEDIFF(CURDATE(), MAX(DATE(created_at))) FROM stock_movements
);

UPDATE stock_movements
SET created_at = created_at + INTERVAL @shift_days DAY;

UPDATE purchase_orders
SET order_date    = order_date    + INTERVAL @shift_days DAY,
    expected_date = expected_date + INTERVAL @shift_days DAY;

-- -----------------------------------------------------
-- 2) A slow mover: 24 received two months ago, 1 sold since
-- -----------------------------------------------------
INSERT INTO products (sku, name, category_id, supplier_id, unit_cost, unit_price, reorder_point)
VALUES ('HOM-901', 'Scented Candle (Pumpkin Spice)',
        (SELECT MIN(category_id) FROM categories),
        (SELECT MIN(supplier_id) FROM suppliers),
        4.50, 12.99, 4);

SET @candle = LAST_INSERT_ID();

INSERT INTO stock_movements (product_id, movement_type, quantity, note, created_at) VALUES
  (@candle, 'receive', 24, 'Seasonal order', NOW() - INTERVAL 60 DAY),
  (@candle, 'sale',    -1, NULL,             NOW() - INTERVAL 41 DAY);

-- Quick check: the date range should end today
SELECT MIN(created_at) AS first_movement, MAX(created_at) AS last_movement
FROM stock_movements;
