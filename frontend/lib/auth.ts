import type { Account } from "./api";

const ACCESS_TOKEN_KEY = "mts_access_token";
const REFRESH_TOKEN_KEY = "mts_refresh_token";

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setTokens(tokens: TokenResponse): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  window.sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw new Error((await response.text()) || "Login failed");
  const tokens = (await response.json()) as TokenResponse;
  setTokens(tokens);
  return tokens;
}

export async function refreshSession(): Promise<TokenResponse | null> {
  if (typeof window === "undefined") return null;
  const refreshToken = window.sessionStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) return null;
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { Authorization: `Bearer ${refreshToken}` },
  });
  if (!response.ok) {
    clearTokens();
    return null;
  }
  const tokens = (await response.json()) as TokenResponse;
  setTokens(tokens);
  return tokens;
}

export async function logout(): Promise<void> {
  const accessToken = getAccessToken();
  if (accessToken) {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/auth/logout`, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
    }).catch(() => undefined);
  }
  clearTokens();
}

export type DashboardAccount = Account;
