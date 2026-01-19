const CSRF_SAFE_METHODS = ["GET", "HEAD", "OPTIONS", "TRACE"];

function getCookie(name: string): string | null {
  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (const cookie of cookies) {
    const [rawName, ...rest] = cookie.trim().split("=");
    if (rawName === name) {
      return decodeURIComponent(rest.join("="));
    }
  }
  return null;
}

export async function apiFetch(url: string, options: RequestInit = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});

  // Attach CSRF token for unsafe methods when available.
  if (!CSRF_SAFE_METHODS.includes(method)) {
    const token = getCookie("csrftoken");
    if (token && !headers.has("X-CSRF-Token")) {
      headers.set("X-CSRF-Token", token);
    }
  }

  const resp = await fetch(url, {
    ...options,
    method,
    headers,
    credentials: "include",
  });

  return resp;
}
