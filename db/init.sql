-- Sheet 1: products we sell
CREATE TABLE products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    price       NUMERIC(10, 2) NOT NULL,
    image_url   TEXT
);

-- Sheet 2: orders (who bought, total amount)
CREATE TABLE orders (
    id            SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    total         NUMERIC(10, 2) NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);

-- Sheet 3: which products are in which order
CREATE TABLE order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity   INTEGER NOT NULL,
    price      NUMERIC(10, 2) NOT NULL
);

-- Add some sample products to the shop
INSERT INTO products (name, description, price, image_url) VALUES
 ('Wireless Headphones', 'Over-ear, 30-hour battery', 2499.00, 'https://picsum.photos/seed/headphones/400/300'),
 ('Smart Watch',         'Tracks steps and heart rate', 3999.00, 'https://picsum.photos/seed/watch/400/300'),
 ('Backpack',            'Fits a 15 inch laptop',       1799.00, 'https://picsum.photos/seed/backpack/400/300'),
 ('Coffee Mug',          'Ceramic, 350 ml',              399.00, 'https://picsum.photos/seed/mug/400/300');