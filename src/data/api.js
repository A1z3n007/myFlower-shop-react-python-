export const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api";

async function handle(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

function authHeaders() {
  const token = localStorage.getItem("jwt");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const Api = {
  // products
  getProducts: () => fetch(`${API_BASE}/products/`).then(handle),
  getProduct: (id) => fetch(`${API_BASE}/products/${id}/`).then(handle),
  getSimilarProducts: (id) =>
    fetch(`${API_BASE}/products/${id}/similar/`).then(handle),
  getBundleSuggestions: (id) =>
    fetch(`${API_BASE}/products/${id}/bundles/`).then(handle),

  // orders
  createOrder: (data) =>
    fetch(`${API_BASE}/orders/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(data),
    }).then(handle),

  getOrders: ({ mine = false, email = null } = {}) => {
    const q = mine ? "?mine=1" : email ? `?email=${encodeURIComponent(email)}` : "";
    return fetch(`${API_BASE}/orders/${q}`, { headers: { ...authHeaders() } }).then(handle);
  },

  getOrder: (id) =>
    fetch(`${API_BASE}/orders/${id}/`, { headers: { ...authHeaders() } }).then(handle),

  requestDelivery: (id, payload) =>
    fetch(`${API_BASE}/orders/${id}/request_delivery/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload || {}),
    }).then(handle),

  setOrderStatus: (id, status) =>
    fetch(`${API_BASE}/orders/${id}/set_status/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ status }),
    }).then(handle),

  setDeliveryStatus: (id, delivery_status) =>
    fetch(`${API_BASE}/orders/${id}/set_delivery_status/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ delivery_status }),
    }).then(handle),
  uploadDeliveryPhoto: (token, file) => {
    const form = new FormData();
    form.append("photo", file);
    return fetch(`${API_BASE}/orders/photo/${token}/`, {
      method: "POST",
      body: form,
    }).then(handle);
  },

  // auth (JWT)
  async login({ email, password }) {
    const res = await fetch(`${API_BASE}/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // SimpleJWT ждёт поле "username"
      body: JSON.stringify({ username: email, password }),
    }).then(handle);
    localStorage.setItem("jwt", res.access);
    localStorage.setItem("refresh", res.refresh || "");
    localStorage.setItem("user_email", email);
    return res;
  },

  register: ({ name, email, password }) =>
    fetch(`${API_BASE}/auth/register/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    }).then(handle),

  logout() {
    localStorage.removeItem("jwt");
    localStorage.removeItem("refresh");
    localStorage.removeItem("user_email");
  },

  // account
  getProfile: ({ mine = true, email = null } = {}) => {
    const q = mine ? "" : email ? `?email=${encodeURIComponent(email)}` : "";
    return fetch(`${API_BASE}/account/profile/${q}`, { headers: { ...authHeaders() } }).then(handle);
  },

  getFavorites: ({ mine = true, email = null } = {}) => {
    const q = mine ? "" : email ? `?email=${encodeURIComponent(email)}` : "";
    return fetch(`${API_BASE}/account/favorites/${q}`, { headers: { ...authHeaders() } }).then(handle);
  },
  toggleFavorite: (product_id, action = "toggle") =>
    fetch(`${API_BASE}/account/favorites/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ product_id, action }),
    }).then(handle),

  validateCoupon: (code, subtotal) =>
    fetch(`${API_BASE}/coupons/validate/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, subtotal }),
    }).then(handle),

  getDeliverySlots: () => fetch(`${API_BASE}/delivery/slots/`).then(handle),
  autocompleteAddress: (q) =>
    fetch(`${API_BASE}/delivery/autocomplete/?q=${encodeURIComponent(q)}`).then(handle),

  getSavedAddresses: () =>
    fetch(`${API_BASE}/account/addresses/`, {
      headers: { ...authHeaders() },
    }).then(handle),
  createAddress: (payload) =>
    fetch(`${API_BASE}/account/addresses/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handle),
  deleteAddress: (id) =>
    fetch(`${API_BASE}/account/addresses/`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ id }),
    }).then(handle),

  quickOrder: (payload) =>
    fetch(`${API_BASE}/orders/quick/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(handle),

  getProductReviews: (productId) =>
    fetch(`${API_BASE}/product-reviews/?product=${productId}`).then(handle),
  addProductReview: (payload) =>
    fetch(`${API_BASE}/product-reviews/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handle),

  fireAnalytics: (name, payload = {}) =>
    fetch(`${API_BASE}/analytics/events/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        payload,
        session_id: localStorage.getItem("session_id") || "",
        email: localStorage.getItem("user_email") || "",
      }),
    }).then(handle),

  createStripeIntent: ({ amount, currency = "kzt" }) =>
    fetch(`${API_BASE}/payments/stripe/intent/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount, currency }),
    }).then(handle),
};
