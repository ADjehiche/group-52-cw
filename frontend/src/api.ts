export type HighestBid = {
  amount: string | null;
  bidder_id: number | null;
};

export type ItemDetail = {
  id: number;
  title: string;
  description: string;
  starting_price: string;
  image_url: string;
  ends_at: string;
  owner_id: number;
  highest_bid: HighestBid;
  time_remaining_seconds: number;
};

async function handleResponse(response: Response) {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }
  return response.json();
}

export async function apiFetch<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    credentials: "include",
    headers: {
      "Accept": "application/json",
      ...init.headers,
    },
    ...init,
  });
  return handleResponse(response) as Promise<T>;
}

export async function fetchItemDetail(id: number): Promise<ItemDetail> {
  return apiFetch<ItemDetail>(`/api/items/${id}/`);
}
