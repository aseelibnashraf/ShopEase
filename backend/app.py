import os
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

app = Flask(__name__)


# Connect to the database (settings come from environment variables)
def get_db():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


# Health check
@app.route("/api/health")
def health():
    return jsonify(status="ok")


# Get all products
@app.route("/api/products")
def products():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, name, description, price::float AS price, image_url FROM products ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)


# NEW: place an order
@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    name = data.get("customer_name")
    items = data.get("items")          # example: [{"product_id": 1, "quantity": 2}]

    if not name or not items:
        return jsonify(error="customer_name and items are required"), 400

    conn = get_db()
    cur = conn.cursor()

    # 1. Look up the REAL price of each product and add up the total
    total = 0
    for item in items:
        cur.execute("SELECT price FROM products WHERE id = %s", (item["product_id"],))
        row = cur.fetchone()
        if row is None:
            conn.close()
            return jsonify(error="product not found"), 400
        item["price"] = row[0]
        total += row[0] * item["quantity"]

    # 2. Save the order and get its new id
    cur.execute("INSERT INTO orders (customer_name, total) VALUES (%s, %s) RETURNING id", (name, total))
    order_id = cur.fetchone()[0]

    # 3. Save each product in the order
    for item in items:
        cur.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, item["product_id"], item["quantity"], item["price"]),
        )

    conn.commit()      # make the changes permanent
    conn.close()
    return jsonify(order_id=order_id, total=float(total)), 201


# NEW: see recent orders
@app.route("/api/orders")
def list_orders():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, customer_name, total::float AS total, created_at FROM orders ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    