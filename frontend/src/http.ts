export async function apiFetch(url: string, options: RequestInit = {}) {
  const resp = await fetch(url, {
    ...options,
    credentials: "include",
  });

  return resp;
}
