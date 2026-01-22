export type HighestBid = {
  amount: string | null;
  bidder_id: number | null;
};

export type ItemDetail = {
  id: number;
  title: string;
  description: string;
  starting_price: string;
  images: { id: number; url: string; order: number }[];
  ends_at: string;
  owner_id: number;
  owner_username?: string;
  owner_avatar_url?: string;
  is_following_owner?: boolean;
  highest_bid?: HighestBid;
  time_remaining_seconds?: number;
};

export type Answer = {
  content: string;
  created_at: string;
  author_avatar_url?: string;
};

export type Question = {
  id: number;
  content: string;
  author: string;
  author_id: number;
  author_avatar_url?: string;
  created_at: string;
  answer: Answer | null;
};

export type QuestionListResponse = {
  questions: Question[];
};

export type BidResponse = {
  id: number;
  bidder: string;
  amount: string;
  created_at: string;
};

// ... existing helper functions ...
async function handleResponse(response: Response) {
  if (!response.ok) {
    const text = await response.text();
    // Try to parse error Json from the text
    try {
      const errorData = JSON.parse(text);
      if (errorData.errors) {
        // Return the errors object directly if present
        throw errorData.errors; 
      }
      if (errorData.detail) {
        throw new Error(errorData.detail);
      }
    } catch (e) {
      // Re-throw if it's not a JSON parsing error (e.g. it's our structured error object we just threw)
      if (!(e instanceof SyntaxError)) throw e; 
    }
    throw new Error(text || `Request failed (${response.status})`);
  }
  return response.json();
}

export async function apiFetch<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  // Get CSRF token if needed - Django usually uses cookies for this in SPA if session based
  // But for simple fetch we might need X-CSRFToken header if we rely on cookies
  const headers: HeadersInit = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    ...(init.headers ?? {}),
  };

  // Basic CSRF handling for Django
  const csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
  if (csrfMatch) {
    (headers as any)["X-CSRFToken"] = csrfMatch[1];
  }

  const response = await fetch(path, {
    credentials: "include",
    headers: headers,
    ...init,
  });
  return handleResponse(response) as Promise<T>;
}

export async function fetchItemDetail(id: number): Promise<ItemDetail> {
  return apiFetch<ItemDetail>(`/api/items/${id}/`);
}

export async function fetchItemQuestions(itemId: number): Promise<QuestionListResponse> {
  return apiFetch<QuestionListResponse>(`/api/items/${itemId}/questions/`);
}

export async function postQuestion(itemId: number, content: string): Promise<Question> {
  return apiFetch<Question>(`/api/items/${itemId}/questions/`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function placeBid(itemId: number, amount: string): Promise<BidResponse> {
  return apiFetch<BidResponse>(`/api/items/${itemId}/bid/`, {
    method: "POST",
    body: JSON.stringify({ amount }),
  });
}

export async function postAnswer(questionId: number, content: string): Promise<Answer> {
  return apiFetch<Answer>(`/api/questions/${questionId}/answer/`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function followUser(userId: number): Promise<void> {
  await apiFetch(`/api/users/${userId}/follow/`, { method: "POST" });
}

export async function unfollowUser(userId: number): Promise<void> {
  await apiFetch(`/api/users/${userId}/follow/`, { method: "DELETE" });
}

export async function deleteItem(itemId: number): Promise<void> {
  await apiFetch(`/api/items/${itemId}/`, { method: "DELETE" });
}
