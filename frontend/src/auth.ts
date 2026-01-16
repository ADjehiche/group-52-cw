import { apiFetch } from "@/http";

export type AuthStatus = {
  authenticated: boolean;
  user: null | {
    id: number;
    username: string;
    is_staff: boolean;
  };
};

let cachedStatus: AuthStatus | null = null;
let inFlight: Promise<AuthStatus> | null = null;

export async function fetchAuthStatus(force = false): Promise<AuthStatus> {
  if (!force && cachedStatus) return cachedStatus;
  if (!force && inFlight) return inFlight;

  inFlight = (async () => {
    try {
      const resp = await apiFetch("/api/auth/status/");
      let data: AuthStatus = { authenticated: false, user: null };
      if (resp.ok) {
        data = (await resp.json()) as AuthStatus;
      }
      cachedStatus = data;
      return data;
    } catch (err) {
      throw err;
    } finally {
      inFlight = null;
    }
  })();

  return inFlight;
}

export function getCachedAuthStatus(): AuthStatus | null {
  return cachedStatus;
}
