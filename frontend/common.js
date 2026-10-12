// Shared code used by every page

const API = "/api";

// ---------- Cart (kept in the browser's localStorage) ----------

function getCart() {
  try {
    return JSON.parse(localStorage.getItem("cart")) || {};
  } catch {
    return {};      // if the saved cart is broken, start with an empty one
  }
}

function saveCart(cart) {
  localStorage.setItem("cart", JSON.stringify(cart));
  updateCartCount();
}

function addToCart(product, qty = 1) {
  const cart = getCart();
  const current = cart[product.id] ? cart[product.id].quantity : 0;
  cart[product.id] = {
    id: product.id,
    name: product.name,
    price: product.price,
    image_url: product.image_url,
    quantity: Math.min(current + qty, 10),   // same limit as the backend
  };
  saveCart(cart);
}

function cartCount() {
  return Object.values(getCart()).reduce((sum, item) => sum + item.quantity, 0);
}

function updateCartCount() {
  const el = document.getElementById("cart-count");
  if (el) el.textContent = cartCount();
}

// ---------- Logged-in user ----------

async function getMe() {
  const res = await fetch(`${API}/me`);
  return res.ok ? res.json() : null;   // null means "not logged in"
}

async function logout() {
  await fetch(`${API}/logout`, { method: "POST" });
  location.href = "index.html";
}

// ---------- Header (the same on every page) ----------

async function renderHeader() {
  document.querySelector("header").innerHTML = `
    <a href="index.html" class="logo">ShopEase</a>
    <nav>
      <a href="cart.html">Cart (<span id="cart-count">0</span>)</a>
      <span id="user-area"></span>
    </nav>`;
  updateCartCount();

  const me = await getMe();
  const area = document.getElementById("user-area");
  if (me) {
    area.innerHTML = `<a href="orders.html">My orders</a>
                      <span class="hello"></span>
                      <button id="logout-btn" class="link">Log out</button>`;
    area.querySelector(".hello").textContent = `Hi, ${me.name}`;   // textContent: always plain text
    document.getElementById("logout-btn").onclick = logout;
  } else {
    area.innerHTML = `<a href="login.html">Log in</a>`;
  }
  return me;
}

// ---------- Small helpers ----------

// Turn text into safe HTML, so names like "<script>" show as text instead of running
function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

// 4998 -> "₹4,998" (Indian number format)
function rupees(amount) {
  return "₹" + Number(amount).toLocaleString("en-IN");
}

// A small message that pops up for 2 seconds
function showToast(text) {
  const toast = document.getElementById("toast");
  toast.textContent = text;
  toast.classList.remove("hidden");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => toast.classList.add("hidden"), 2000);
}