const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:5000/api/v1";

function getToken() {
  return localStorage.getItem("access_token");
}

export async function apiFetch(path, { method = "GET", body, headers } = {}) {
  const token = getToken();
  const isFormData = body instanceof FormData;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(headers || {}),
    },
    body: body ? (isFormData ? body : JSON.stringify(body)) : undefined,
  });

  let data = null;
  try {
    const text = await res.text();
    data = text ? JSON.parse(text) : null;
  } catch {}

  if (!res.ok) {
    const msg =
      data?.message || data?.error || `Request failed with status ${res.status}`;
    throw new Error(msg);
  }

  return data;
}