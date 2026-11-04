-- Car Import Dealer: relational schema (SQLite)
PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS v_order_shipping;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS car_models;
DROP TABLE IF EXISTS etl_rejects;

CREATE TABLE car_models (
    model_id            TEXT PRIMARY KEY,
    make                TEXT NOT NULL,
    model               TEXT NOT NULL,
    body_type           TEXT,
    fuel_type           TEXT,
    engine_cc           INTEGER,
    transmission        TEXT,
    origin_country      TEXT NOT NULL,
    base_fob_price_usd  REAL
);

CREATE TABLE suppliers (
    supplier_id    TEXT PRIMARY KEY,
    supplier_name  TEXT NOT NULL,
    country        TEXT NOT NULL,
    supplier_type  TEXT,
    rating         REAL CHECK (rating BETWEEN 0 AND 5),
    payment_terms  TEXT
);

CREATE TABLE customers (
    customer_id        TEXT PRIMARY KEY,
    full_name          TEXT NOT NULL,
    email              TEXT,
    phone              TEXT,
    county             TEXT,
    customer_type      TEXT CHECK (customer_type IN ('Individual','Corporate','Government')),
    registration_date  DATE
);

CREATE TABLE orders (
    order_id          TEXT PRIMARY KEY,
    customer_id       TEXT NOT NULL REFERENCES customers(customer_id),
    model_id          TEXT NOT NULL REFERENCES car_models(model_id),
    supplier_id       TEXT NOT NULL REFERENCES suppliers(supplier_id),
    order_date        DATE NOT NULL,
    manufacture_year  INTEGER,
    mileage_km        INTEGER,
    color             TEXT,
    fob_price_usd     REAL,
    freight_usd       REAL,
    insurance_usd     REAL,
    usd_kes_rate      REAL,
    import_duty_kes   REAL,
    excise_duty_kes   REAL,
    vat_kes           REAL,
    total_price_kes   REAL,
    payment_method    TEXT,
    order_status      TEXT NOT NULL CHECK (order_status IN
        ('Pending Shipment','In Transit','At Port - Mombasa','Cleared','Delivered','Cancelled')),
    salesperson       TEXT
);

CREATE TABLE shipments (
    shipment_id             TEXT PRIMARY KEY,
    order_id                TEXT NOT NULL UNIQUE REFERENCES orders(order_id),
    vessel_name             TEXT,
    origin_port             TEXT,
    destination_port        TEXT,
    departure_date          DATE,
    arrival_date            DATE,
    customs_clearance_date  DATE,
    delivery_date           DATE,
    shipping_method         TEXT,
    delay_reason            TEXT,
    bill_of_lading_no       TEXT
);

CREATE TABLE reviews (
    review_id     TEXT PRIMARY KEY,
    order_id      TEXT NOT NULL REFERENCES orders(order_id),
    customer_id   TEXT NOT NULL REFERENCES customers(customer_id),
    review_date   DATE,
    rating        INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text   TEXT,
    source        TEXT
);

-- Audit table: every row the pipeline refuses to load, and why
CREATE TABLE etl_rejects (
    reject_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT,
    record_key  TEXT,
    reason      TEXT,
    loaded_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_model    ON orders(model_id);
CREATE INDEX idx_orders_supplier ON orders(supplier_id);
CREATE INDEX idx_orders_date     ON orders(order_date);
CREATE INDEX idx_reviews_order   ON reviews(order_id);

-- Convenience view: one row per shipped order with derived durations (days)
CREATE VIEW v_order_shipping AS
SELECT  o.order_id, o.order_date, o.order_status,
        m.make, m.model, m.origin_country,
        s.origin_port, s.shipping_method, s.delay_reason,
        s.departure_date, s.arrival_date, s.customs_clearance_date, s.delivery_date,
        CAST(julianday(s.arrival_date)          - julianday(s.departure_date)         AS INTEGER) AS transit_days,
        CAST(julianday(s.customs_clearance_date) - julianday(s.arrival_date)          AS INTEGER) AS clearance_days,
        CAST(julianday(s.delivery_date)          - julianday(s.customs_clearance_date) AS INTEGER) AS last_mile_days,
        CAST(julianday(s.delivery_date)          - julianday(o.order_date)            AS INTEGER) AS order_to_delivery_days
FROM orders o
JOIN car_models m ON m.model_id = o.model_id
JOIN shipments  s ON s.order_id = o.order_id;
