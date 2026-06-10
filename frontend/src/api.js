const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function getToken() {
  return localStorage.getItem("rag_token");
}

export function setSession(token, user) {
  localStorage.setItem("rag_token", token);
  localStorage.setItem("rag_user", JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem("rag_token");
  localStorage.removeItem("rag_user");
}

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem("rag_user") || "null");
  } catch {
    return null;
  }
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();

  if (token) headers.Authorization = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message = typeof data === "object" ? data.detail || JSON.stringify(data) : data;
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return data;
}

export const api = {
  baseUrl: API_BASE_URL,
  register: (email, password) => request("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email, password) => request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  listDocuments: () => request("/documents/list"),
  uploadDocuments: (files) => {
    const form = new FormData();
    Array.from(files).forEach((file) => form.append("files", file));
    return request("/documents/upload", { method: "POST", body: form });
  },
  deleteDocument: (id) => request(`/documents/delete/${id}`, { method: "DELETE" }),
  ask: (question, topK = 5) => request("/chat/ask", { method: "POST", body: JSON.stringify({ question, top_k: topK }) }),
  history: () => request("/chat/history"),
  deleteHistoryItem: (id) => request(`/chat/history/${id}`, { method: "DELETE" }),
  clearHistory: () => request("/chat/history", { method: "DELETE" }),
  adminDashboard: () => request("/admin/dashboard"),
  health: () => request("/health"),
};
