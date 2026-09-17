const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Account = {
  id: string;
  name: string;
  currency: string;
  initial_balance: string;
  cash_balance: string;
  realized_pnl: string;
};

export type Position = {
  id: string;
  account_id: string;
  symbol: string;
  quantity: string;
  average_price: string;
  market_price: string | null;
  unrealized_pnl: string;
};

export type Order = {
  id: string;
  account_id: string;
  client_order_id: string;
  symbol: string;
  side: "BUY" | "SELL";
  order_type: "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT";
  time_in_force: "DAY" | "GTC" | "IOC" | "FOK";
  quantity: string;
  limit_price: string | null;
  stop_price: string | null;
  filled_quantity: string;
  average_fill_price: string | null;
  status: string;
  rejection_reason: string | null;
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    cache: "no-store",
  });
  if (!response.ok) throw new Error((await response.text()) || `API request failed with ${response.status}`);
  return response.json() as Promise<T>;
}

export function listAccounts(accessToken?: string): Promise<Account[]> {
  return request<Account[]>("/api/v1/accounts", { headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined });
}

export function listOrders(accountId?: string, accessToken?: string): Promise<Order[]> {
  const query = accountId ? `?account_id=${encodeURIComponent(accountId)}` : "";
  return request<Order[]>(`/api/v1/orders${query}`, { headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined });
}

export function createOrder(payload: {
  account_id: string;
  client_order_id: string;
  symbol: string;
  side: Order["side"];
  order_type: Order["order_type"];
  time_in_force: Order["time_in_force"];
  quantity: string;
  limit_price?: string;
  stop_price?: string;
}, accessToken?: string): Promise<Order> {
  return request<Order>("/api/v1/orders", {
    method: "POST",
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
    body: JSON.stringify(payload),
  });
}
