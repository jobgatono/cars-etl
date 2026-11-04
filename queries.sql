-- 1. Row counts per table
SELECT 'customers' AS tbl, COUNT(*) AS n FROM customers UNION ALL
SELECT 'orders', COUNT(*) FROM orders UNION ALL
SELECT 'shipments', COUNT(*) FROM shipments UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews;

-- 2. Average shipping time by origin country (delivered orders)
SELECT origin_country,
       COUNT(*)                          AS orders,
       ROUND(AVG(transit_days), 1)       AS avg_transit_days,
       ROUND(AVG(clearance_days), 1)     AS avg_clearance_days,
       ROUND(AVG(order_to_delivery_days),1) AS avg_order_to_delivery
FROM v_order_shipping
WHERE order_status = 'Delivered'
GROUP BY origin_country
ORDER BY avg_order_to_delivery DESC;

-- 3. Do delays hurt ratings?
SELECT CASE WHEN s.delay_reason IS NULL THEN 'No delay' ELSE 'Delayed' END AS shipment,
       COUNT(*)                   AS reviews,
       ROUND(AVG(r.rating), 2)    AS avg_rating
FROM reviews r
JOIN shipments s ON s.order_id = r.order_id
GROUP BY shipment;

-- 4. Most common delay reasons and their average extra clearance time
SELECT delay_reason,
       COUNT(*)                      AS shipments,
       ROUND(AVG(transit_days), 1)   AS avg_transit_days,
       ROUND(AVG(clearance_days), 1) AS avg_clearance_days
FROM v_order_shipping
WHERE delay_reason IS NOT NULL
GROUP BY delay_reason
ORDER BY shipments DESC;

-- 5. Revenue (KES) and order count by make, excluding cancelled orders
SELECT m.make,
       COUNT(*)                              AS orders,
       ROUND(SUM(o.total_price_kes)/1e6, 1)  AS revenue_kes_millions,
       ROUND(AVG(o.total_price_kes))         AS avg_order_value_kes
FROM orders o
JOIN car_models m USING (model_id)
WHERE o.order_status <> 'Cancelled'
GROUP BY m.make
ORDER BY revenue_kes_millions DESC
LIMIT 10;

-- 6. Monthly orders and revenue (window function: running total)
WITH monthly AS (
    SELECT strftime('%Y-%m', order_date) AS month,
           COUNT(*)                      AS orders,
           SUM(total_price_kes)          AS revenue
    FROM orders
    WHERE order_status <> 'Cancelled'
    GROUP BY month
)
SELECT month, orders, ROUND(revenue/1e6, 1) AS revenue_m,
       ROUND(SUM(revenue) OVER (ORDER BY month)/1e6, 1) AS cumulative_revenue_m
FROM monthly
ORDER BY month DESC
LIMIT 12;

-- 7. Top supplier by average rating they earn from customers
SELECT sp.supplier_name, sp.country,
       COUNT(r.review_id)       AS reviews,
       ROUND(AVG(r.rating), 2)  AS avg_customer_rating
FROM suppliers sp
JOIN orders  o ON o.supplier_id = sp.supplier_id
JOIN reviews r ON r.order_id = o.order_id
GROUP BY sp.supplier_id
HAVING reviews >= 30
ORDER BY avg_customer_rating DESC;

-- 8. Repeat customers: share of customers with 2+ orders
SELECT ROUND(100.0 * SUM(n >= 2) / COUNT(*), 1) AS pct_repeat_customers
FROM (SELECT customer_id, COUNT(*) AS n FROM orders GROUP BY customer_id);

-- 9. Order status funnel
SELECT order_status, COUNT(*) AS orders
FROM orders GROUP BY order_status ORDER BY orders DESC;

-- 10. Best-selling model in each origin country (RANK window function)
SELECT origin_country, make, model, units FROM (
    SELECT m.origin_country, m.make, m.model, COUNT(*) AS units,
           RANK() OVER (PARTITION BY m.origin_country ORDER BY COUNT(*) DESC) AS rnk
    FROM orders o JOIN car_models m USING (model_id)
    GROUP BY m.model_id
)
WHERE rnk = 1;
