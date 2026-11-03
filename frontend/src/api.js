export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

const TOKEN_KEY = "site_shelf_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export function previewSrc(path) {
  return path.startsWith("http") ? path : `${API_URL}${path}`;
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = tokenStore.get();
  if (auth && token) headers["Authorization"] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Can't reach the server. Check that the backend is running.");
  }

  if (res.status === 401 && auth && token) {
    tokenStore.clear();
    window.dispatchEvent(new Event("auth:expired"));
  }
  if (res.status === 204) return null;

  let data = null;
  try {
    data = await res.json();
  } catch {
    /* no body */
  }
  if (!res.ok) {
    let message = "Something went wrong. Please try again.";
    if (typeof data?.detail === "string") message = data.detail;
    else if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
      const field = data.detail[0].loc?.slice(-1)[0];
      message = `${field ? field + ": " : ""}${data.detail[0].msg}`;
    }
    throw new Error(message);
  }
  return data;
}

export const api = {
  signup: (name, email, password) =>
    request("/api/auth/signup", { method: "POST", body: { name, email, password }, auth: false }),
  login: (email, password) =>
    request("/api/auth/login", { method: "POST", body: { email, password }, auth: false }),
  me: () => request("/api/auth/me"),
  listSites: () => request("/api/sites"),
  addSite: (url) => request("/api/sites", { method: "POST", body: { url } }),
  deleteSite: (id) => request(`/api/sites/${id}`, { method: "DELETE" }),
};
