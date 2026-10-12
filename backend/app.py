import os
import psycopg2
import psycopg2.errors
import psycopg2.extras
from flask import Flask, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Sessions: the login cookie is signed with this secret key
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SESSION_COOKIE_HTTPONLY"] = True   # JavaScript can't read the cookie
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # other websites can't send it for you


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


# ---------- Accounts ----------

# Create an account
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or len(password) < 8:
        return jsonify(error="Name, email and a password of at least 8 characters are required"), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (name, email, generate_password_hash(password)),
        )
        user_id = cur.fetchone()[0]
        conn.commit()
    except psycopg2.errors.UniqueViolation:     # the email is already in the users table
        conn.close()
        return jsonify(error="An account with this email already exists"), 409
    conn.close()

    # Log them in straight away
    session.clear()
    session["user_id"] = user_id
    session["name"] = name
    return jsonify(id=user_id, name=name), 201


# Log in
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, password_hash FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    conn.close()

    # Same message whether the email or the password is wrong
    if row is None or not check_password_hash(row[2], password):
        return jsonify(error="Wrong email or password"), 401

    session.clear()
    session["user_id"] = row[0]
    session["name"] = row[1]
    return jsonify(id=row[0], name=row[1])


# Log out
@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify(ok=True)


# Who is logged in? (the frontend asks this when a page loads)
@app.route("/api/me")
def me():
    if "user_id" not in session:
        return jsonify(error="not logged in"), 401
    return jsonify(id=session["user_id"], name=session["name"])


# ---------- Products ----------

# Get all products
@app.route("/api/products")
def products():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, name, description, price::float AS price, image_url FROM products ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)


# ---------- Orders ----------

PAYMENT_METHODS = {"cod", "upi"}   # Cash on delivery, UPI (pretend; no real payment)


# Place an order (logged-in users only)
@app.route("/api/orders", methods=["POST"])
def create_order():
    # 1. Who is ordering? Taken from the signed session cookie, not from the request
    if "user_id" not in session:
        return jsonify(error="Please log in to place an order"), 401

    data = request.get_json() or {}
    items = data.get("items") or []
    address = (data.get("address") or "").strip()
    city = (data.get("city") or "").strip()
    pincode = (data.get("pincode") or "").strip()
    phone = (data.get("phone") or "").strip()
    payment_method = data.get("payment_method")

    # 2. Check the shipping details
    if not address or not city:
        return jsonify(error="Address and city are required"), 400
    if not (pincode.isdigit() and len(pincode) == 6):
        return jsonify(error="Pincode must be 6 digits"), 400
    if not (phone.isdigit() and len(phone) == 10):
        return jsonify(error="Phone number must be 10 digits"), 400
    if payment_method not in PAYMENT_METHODS:
        return jsonify(error="Please choose a payment method"), 400

    # 3. Check the items
    if not isinstance(items, list) or not items:
        return jsonify(error="Your cart is empty"), 400
    for item in items:
        qty = item.get("quantity")
        if not isinstance(qty, int) or not 1 <= qty <= 10:
            return jsonify(error="Quantity must be between 1 and 10"), 400

    conn = get_db()
    cur = conn.cursor()

    # 4. Look up the REAL price of each product and add up the total
    total = 0
    for item in items:
        cur.execute("SELECT price FROM products WHERE id = %s", (item.get("product_id"),))
        row = cur.fetchone()
        if row is None:
            conn.close()
            return jsonify(error="Product not found"), 400
        item["price"] = row[0]
        total += row[0] * item["quantity"]

    # 5. Save the order, linked to the user
    cur.execute(
        """INSERT INTO orders (user_id, customer_name, total, address, city, pincode, phone, payment_method)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (session["user_id"], session["name"], total, address, city, pincode, phone, payment_method),
    )
    order_id = cur.fetchone()[0]

    # 6. Save each product in the order
    for item in items:
        cur.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, item["product_id"], item["quantity"], item["price"]),
        )

    conn.commit()      # all or nothing: nothing is saved until this line
    conn.close()
    return jsonify(order_id=order_id, total=float(total)), 201


# My orders: only the logged-in user's own orders
@app.route("/api/orders")
def my_orders():
    if "user_id" not in session:
        return jsonify(error="Please log in"), 401

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT id, total::float AS total, status, address, city, pincode, payment_method, created_at
           FROM orders WHERE user_id = %s ORDER BY id DESC""",
        (session["user_id"],),
    )
    orders = cur.fetchall()

    # Add the products in each order
    for order in orders:
        cur.execute(
            """SELECT p.name, oi.quantity, oi.price::float AS price
               FROM order_items oi JOIN products p ON p.id = oi.product_id
               WHERE oi.order_id = %s""",
            (order["id"],),
        )
        order["items"] = cur.fetchall()

    conn.close()
    return jsonify(orders)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    