-- ShopEase database (v2)
-- Safe to run many times: it only creates or adds what is missing.

-- Sheet 1: products we sell
CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    price       NUMERIC(10, 2) NOT NULL,
    image_url   TEXT
);

-- NEW Sheet: customer accounts
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,  -- UNIQUE: one account per email
    password_hash TEXT NOT NULL,                 -- never the real password
    created_at    TIMESTAMP DEFAULT NOW()
);

-- Sheet 2: orders (who bought, total amount)
CREATE TABLE IF NOT EXISTS orders (
    id            SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    total         NUMERIC(10, 2) NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);

-- NEW columns on orders (added only if missing)
ALTER TABLE orders ADD COLUMN IF NOT EXISTS user_id        INTEGER REFERENCES users(id);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS address        TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS city           VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS pincode        VARCHAR(10);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS phone          VARCHAR(20);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(30);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS status         VARCHAR(20) DEFAULT 'placed';

-- Sheet 3: which products are in which order
CREATE TABLE IF NOT EXISTS order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity   INTEGER NOT NULL,
    price      NUMERIC(10, 2) NOT NULL
);

-- Sample products: only added when the products table is empty
INSERT INTO products (name, description, price, image_url)
SELECT * FROM (VALUES
 ('Wireless Headphones', 'Over-ear, 30-hour battery',   2499.00, 'https://picsum.photos/seed/headphones/400/300'),
 ('Smart Watch',         'Tracks steps and heart rate', 3999.00, 'https://picsum.photos/seed/watch/400/300'),
 ('Backpack',            'Fits a 15 inch laptop',       1799.00, 'https://picsum.photos/seed/backpack/400/300'),
 ('Coffee Mug',          'Ceramic, 350 ml',              399.00, 'https://picsum.photos/seed/mug/400/300')
) AS sample(name, description, price, image_url)
WHERE NOT EXISTS (SELECT 1 FROM products);
