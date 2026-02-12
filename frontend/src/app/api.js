const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api/v1";


function getToken() {
  return localStorage.getItem("access_token");
}

export async function apiFetch(endpoint, options = {}) {
  const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "http://localhost:5000/api/v1";

  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // Add Authorization if token exists
  const token = localStorage.getItem("access_token");
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  let data;
  try {
    data = await res.json();
  } catch {
    data = {};
  }

  if (!res.ok) {
    console.error('API Error:', { status: res.status, endpoint, data });
    throw new Error(data.message || "API request failed");
  }

  return data;
}
