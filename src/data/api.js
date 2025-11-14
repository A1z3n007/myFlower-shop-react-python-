const LOCAL_API_BASE = "http://127.0.0.1:8000/api";
const API_OVERRIDE_KEY = "api_base_override";

function readStoredOverride() {
  try {
    return localStorage.getItem(API_OVERRIDE_KEY);
  } catch {
    return null;
  }
}

function writeStoredOverride(value) {
  try {
    localStorage.setItem(API_OVERRIDE_KEY, value);
  } catch {
    // storage might be unavailable (private mode) — ignore
  }
}

function normalizeBase(raw) {
  if (!raw) return "";
  let base = raw.trim();
  if (!base) return "";

  // ensure protocol for URL parsing
  if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(base)) {
    base = `https://${base}`;
  }

  try {
    const url = new URL(base);
    // If no path specified, default to /api for convenience.
    if (url.pathname === "/" || url.pathname === "") {
      url.pathname = "/api";
    }
    // Remove trailing slash while keeping potential nested paths (/api/v1)
    const normalized = `${url.origin}${url.pathname}`.replace(/\/+$/, "");
    return normalized;
  } catch (err) {
    console.warn("Invalid API base, falling back to local:", raw, err);
    return LOCAL_API_BASE;
  }
}

function detectApiBase() {
  if (typeof window === "undefined") {
    return normalizeBase(import.meta.env.VITE_API_BASE || LOCAL_API_BASE);
  }

  const params = new URLSearchParams(window.location.search);
  const queryOverride = params.get("apiBase") || params.get("api") || "";
  const globalOverride = window.__FLOWER_API_BASE__;
  const storedOverride = readStoredOverride();

  let candidate =
    queryOverride ||
    globalOverride ||
    storedOverride ||
    import.meta.env.VITE_API_BASE ||
    "";

  if (!candidate) {
    const host = window.location.hostname;
    const isLocal =
      !host ||
      host === "localhost" ||
      host.startsWith("127.") ||
      host.startsWith("192.168.") ||
      host.startsWith("10.");
    candidate = isLocal
      ? LOCAL_API_BASE
      : `${window.location.origin.replace(/\/$/, "")}/api`;
  }

  const normalized = normalizeBase(candidate);

  if (queryOverride) {
    writeStoredOverride(normalized);
  }

  return normalized;
}

export const API_BASE = detectApiBase();
const EXTRA_HEADERS = API_BASE.includes("ngrok")
  ? { "ngrok-skip-browser-warning": "1" }
  : {};

function apiFetch(url, options = {}) {
  if (options.headers instanceof Headers) {
    Object.entries(EXTRA_HEADERS).forEach(([key, value]) => {
      if (!options.headers.has(key)) {
        options.headers.set(key, value);
      }
    });
    return fetch(url, options);
  }

  if (Object.keys(EXTRA_HEADERS).length) {
    const merged = { ...EXTRA_HEADERS, ...(options.headers || {}) };
    return fetch(url, { ...options, headers: merged });
  }

  return fetch(url, options);
}

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
  getProducts: () => apiFetch(`${API_BASE}/products/`).then(handle),
  getProduct: (id) => apiFetch(`${API_BASE}/products/${id}/`).then(handle),
  getSimilarProducts: (id) =>
    apiFetch(`${API_BASE}/products/${id}/similar/`).then(handle),
  getBundleSuggestions: (id) =>
    apiFetch(`${API_BASE}/products/${id}/bundles/`).then(handle),

  // orders
  createOrder: (data) =>
    apiFetch(`${API_BASE}/orders/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(data),
    }).then(handle),

  getOrders: ({ mine = false, email = null } = {}) => {
    const q = mine ? "?mine=1" : email ? `?email=${encodeURIComponent(email)}` : "";
    return apiFetch(`${API_BASE}/orders/${q}`, { headers: { ...authHeaders() } }).then(handle);
  },

  getOrder: (id) =>
    apiFetch(`${API_BASE}/orders/${id}/`, { headers: { ...authHeaders() } }).then(handle),

  requestDelivery: (id, payload) =>
    apiFetch(`${API_BASE}/orders/${id}/request_delivery/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload || {}),
    }).then(handle),

  setOrderStatus: (id, status) =>
    apiFetch(`${API_BASE}/orders/${id}/set_status/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ status }),
    }).then(handle),

  setDeliveryStatus: (id, delivery_status) =>
    apiFetch(`${API_BASE}/orders/${id}/set_delivery_status/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ delivery_status }),
    }).then(handle),
  uploadDeliveryPhoto: (token, file) => {
    const form = new FormData();
    form.append("photo", file);
    return apiFetch(`${API_BASE}/orders/photo/${token}/`, {
      method: "POST",
      body: form,
    }).then(handle);
  },

  // auth (JWT)
  async login({ email, password }) {
    const res = await apiFetch(`${API_BASE}/auth/login/`, {
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
    apiFetch(`${API_BASE}/auth/register/`, {
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
    return apiFetch(`${API_BASE}/account/profile/${q}`, { headers: { ...authHeaders() } }).then(handle);
  },

  getFavorites: ({ mine = true, email = null } = {}) => {
    const q = mine ? "" : email ? `?email=${encodeURIComponent(email)}` : "";
    return apiFetch(`${API_BASE}/account/favorites/${q}`, { headers: { ...authHeaders() } }).then(handle);
  },
  toggleFavorite: (product_id, action = "toggle") =>
    apiFetch(`${API_BASE}/account/favorites/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ product_id, action }),
    }).then(handle),

  validateCoupon: (code, subtotal) =>
    apiFetch(`${API_BASE}/coupons/validate/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, subtotal }),
    }).then(handle),

  getDeliverySlots: () => apiFetch(`${API_BASE}/delivery/slots/`).then(handle),
  autocompleteAddress: (q) =>
    apiFetch(`${API_BASE}/delivery/autocomplete/?q=${encodeURIComponent(q)}`).then(handle),

  getSavedAddresses: () =>
    apiFetch(`${API_BASE}/account/addresses/`, {
      headers: { ...authHeaders() },
    }).then(handle),
  createAddress: (payload) =>
    apiFetch(`${API_BASE}/account/addresses/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handle),
  deleteAddress: (id) =>
    apiFetch(`${API_BASE}/account/addresses/`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ id }),
    }).then(handle),

  quickOrder: (payload) =>
    apiFetch(`${API_BASE}/orders/quick/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(handle),

  getProductReviews: (productId) =>
    apiFetch(`${API_BASE}/product-reviews/?product=${productId}`).then(handle),
  addProductReview: (payload) =>
    apiFetch(`${API_BASE}/product-reviews/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handle),

  fireAnalytics: (name, payload = {}) =>
    apiFetch(`${API_BASE}/analytics/events/`, {
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
    apiFetch(`${API_BASE}/payments/stripe/intent/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount, currency }),
    }).then(handle),
};
