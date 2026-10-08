// Talk to the backend using "/api/...".
// Nginx (next step) will forward these requests to the backend container.
const API = "/api";
const cart = {}; // what's in the cart: { productId: { product, quantity } }

// 1. Get products from the backend and show them as cards
async function loadProducts() {
  const box = document.getElementById("products");
  try {
    const res = await fetch(`${API}/products`);
    const products = await res.json();
    box.innerHTML = products.map(p => `
      <div class="card">
        <img src="${p.image_url}" alt="${p.name}">
        <div class="body">
          <h3>${p.name}</h3>
          <p>${p.description}</p>
          <div class="row">
            <strong>₹${p.price}</strong>
            <button data-id="${p.id}">Add to cart</button>
          </div>
        </div>
      </div>`).join("");
    box.querySelectorAll("button").forEach(btn => {
      btn.onclick = () => addToCart(products.find(p => p.id == btn.dataset.id));
    });
  } catch (err) {
    box.innerHTML = "<p>Could not load products. Is the backend running?</p>";
  }
}

// 2. Add a product to the cart
function addToCart(product) {
  cart[product.id] = cart[product.id] || { product, quantity: 0 };
  cart[product.id].quantity++;
  renderCart();
  document.getElementById("cart").classList.remove("hidden");
}

// 3. Show what's in the cart and the total
function renderCart() {
  const entries = Object.values(cart);
  document.getElementById("cart-count").textContent = entries.reduce((n, e) => n + e.quantity, 0);
  document.getElementById("cart-items").innerHTML = entries
    .map(e => `<li><span>${e.product.name} × ${e.quantity}</span><span>₹${e.product.price * e.quantity}</span></li>`)
    .join("");
  document.getElementById("cart-total").textContent = entries.reduce((s, e) => s + e.product.price * e.quantity, 0);
}

// 4. Send the order to the backend (the same POST you did with curl!)
async function checkout() {
  const msg = document.getElementById("message");
  const name = document.getElementById("customer-name").value.trim();
  const items = Object.values(cart).map(e => ({ product_id: e.product.id, quantity: e.quantity }));
  if (!name || items.length === 0) { msg.textContent = "Add items and enter your name."; return; }

  const res = await fetch(`${API}/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customer_name: name, items }),
  });
  const data = await res.json();
  if (res.ok) {
    msg.textContent = `Order #${data.order_id} placed! Total ₹${data.total}`;
    Object.keys(cart).forEach(k => delete cart[k]);
    renderCart();
  } else {
    msg.textContent = data.error || "Something went wrong.";
  }
}

// Connect the buttons, and load products when the page opens
document.getElementById("cart-btn").onclick = () => document.getElementById("cart").classList.toggle("hidden");
document.getElementById("checkout-btn").onclick = checkout;
loadProducts();
