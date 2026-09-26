-- Schema + seed data for SQL-layer tests. Mirrors the Sauce Demo domain so
-- UI / API / SQL tests talk about the same entities.
PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    email       TEXT    NOT NULL UNIQUE CHECK (email LIKE '%_@_%._%'),
    is_locked   INTEGER NOT NULL DEFAULT 0 CHECK (is_locked IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE products (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT    NOT NULL UNIQUE,
    price  REAL    NOT NULL CHECK (price > 0)
);

CREATE TABLE orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status      TEXT    NOT NULL CHECK (status IN ('PENDING', 'PAID', 'SHIPPED', 'CANCELLED')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE order_items (
    order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    unit_price  REAL    NOT NULL,
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE bookings (
    id            INTEGER PRIMARY KEY,           -- id from the Restful Booker API
    firstname     TEXT    NOT NULL,
    lastname      TEXT    NOT NULL,
    totalprice    INTEGER NOT NULL,
    depositpaid   INTEGER NOT NULL,
    checkin       TEXT    NOT NULL,
    checkout      TEXT    NOT NULL,
    CHECK (checkout >= checkin)
);

INSERT INTO users (username, email, is_locked) VALUES
    ('standard_user',   'standard@example.com', 0),
    ('locked_out_user', 'locked@example.com',   1),
    ('problem_user',    'problem@example.com',  0);

INSERT INTO products (name, price) VALUES
    ('Sauce Labs Backpack',      29.99),
    ('Sauce Labs Bike Light',     9.99),
    ('Sauce Labs Bolt T-Shirt',  15.99),
    ('Sauce Labs Fleece Jacket', 49.99),
    ('Sauce Labs Onesie',         7.99),
    ('Test.allTheThings() T-Shirt (Red)', 15.99);

INSERT INTO orders (user_id, status) VALUES (1, 'PAID'), (1, 'PENDING'), (3, 'SHIPPED');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 29.99),
    (1, 2, 2,  9.99),
    (2, 4, 1, 49.99),
    (3, 5, 3,  7.99);
