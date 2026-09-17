"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { createOrder, listAccounts, listOrders, listPositions, type Account, type Order, type Position } from "../lib/api";
import { getAccessToken, login, logout } from "../lib/auth";

export default function Dashboard() {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [accountId, setAccountId] = useState("");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [symbol, setSymbol] = useState("NIFTY");
  const [orderType, setOrderType] = useState<Order["order_type"]>("LIMIT");
  const [quantity, setQuantity] = useState("50");
  const [limitPrice, setLimitPrice] = useState("22410.20");
  const [tif, setTif] = useState<Order["time_in_force"]>("DAY");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => setToken(getAccessToken()), []);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    setLoading(true);
    setError("");
    Promise.all([listAccounts(token), listOrders(undefined, token)])
      .then(async ([nextAccounts, nextOrders]) => {
        if (cancelled) return;
        setAccounts(nextAccounts);
        setOrders(nextOrders);
        const selected = accountId && nextAccounts.some((a) => a.id === accountId) ? accountId : nextAccounts[0]?.id ?? "";
        setAccountId(selected);
        if (selected) setPositions(await listPositions(selected, token));
      })
      .catch((err: Error) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [token]);

  useEffect(() => {
    if (!token || !accountId) return;
    listPositions(accountId, token).then(setPositions).catch((err: Error) => setError(err.message));
  }, [accountId, token]);

  const account = accounts.find((item) => item.id === accountId);
  const unrealized = positions.reduce((sum, p) => sum + Number(p.unrealized_pnl), 0);
  const netLiquidation = Number(account?.cash_balance ?? 0) + positions.reduce((sum, p) => sum + Number(p.quantity) * Number(p.market_price ?? p.average_price), 0);
  const accountOrders = useMemo(() => orders.filter((o) => !accountId || o.account_id === accountId), [orders, accountId]);

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setLoading(true); setError("");
    try { const tokens = await login(email, password); setToken(tokens.access_token); }
    catch (err) { setError(err instanceof Error ? err.message : "Login failed"); }
    finally { setLoading(false); }
  }

  async function handleOrder(event: FormEvent) {
    event.preventDefault();
    if (!token || !accountId) return;
    setLoading(true); setError(""); setMessage("");
    try {
      const created = await createOrder({
        account_id: accountId,
        client_order_id: `WEB-${Date.now()}`,
        symbol: symbol.trim(), side, order_type: orderType, time_in_force: tif,
        quantity, ...(orderType === "LIMIT" || orderType === "STOP_LIMIT" ? { limit_price: limitPrice } : {}),
      }, token);
      setOrders((current) => [created, ...current]);
      setMessage(created.status === "REJECTED" ? `Order rejected: ${created.rejection_reason ?? "risk check failed"}` : `Order ${created.status.toLowerCase()}`);
    } catch (err) { setError(err instanceof Error ? err.message : "Order submission failed"); }
    finally { setLoading(false); }
  }

  if (!token) return <main className="login-shell"><form className="card login-card" onSubmit={handleLogin}><div className="brand">MyTrading<span>System</span></div><div className="eyebrow">Paper trading workspace</div><h1>Sign in</h1><div className="form"><div className="field"><label>EMAIL</label><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div><div className="field"><label>PASSWORD</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div><button className="submit" disabled={loading}>{loading ? "SIGNING IN…" : "SIGN IN"}</button></div>{error && <div className="error">{error}</div>}</form></main>;

  return (
    <div className="shell">
      <aside className="sidebar"><div className="brand">MyTrading<span>System</span></div><nav className="nav"><button className="active">▦ &nbsp; Dashboard</button><button>◫ &nbsp; Positions</button><button>↕ &nbsp; Orders</button><button>◒ &nbsp; Risk</button><button>⌁ &nbsp; Strategies</button><button>◌ &nbsp; Backtests</button><button>⚙ &nbsp; Settings</button></nav><button className="nav-logout" onClick={() => { void logout(); setToken(null); }}>↪ &nbsp; Sign out</button></aside>
      <main className="main">
        <header className="topbar"><div><div className="eyebrow">Trading workspace</div><h1>Portfolio overview</h1></div><div className="account"><span className="badge">PAPER</span><select aria-label="Trading account" value={accountId} onChange={(e) => setAccountId(e.target.value)}>{accounts.length ? accounts.map((a) => <option key={a.id} value={a.id}>{a.name} · {a.currency} {Number(a.cash_balance).toLocaleString()}</option>) : <option value="">No accounts</option>}</select></div></header>
        {error && <div className="error banner">{error}</div>}{message && <div className="notice banner">{message}</div>}
        <section className="metrics"><Metric label="Net liquidation" value={money(netLiquidation, account?.currency)} detail={loading ? "Loading…" : "Live account data"} /><Metric label="Available cash" value={money(Number(account?.cash_balance ?? 0), account?.currency)} detail="Account cash" /><Metric label="Unrealized P&L" value={money(unrealized, account?.currency)} detail="Open positions" positive={unrealized >= 0} /><Metric label="Realized P&L" value={money(Number(account?.realized_pnl ?? 0), account?.currency)} detail="Account realized" positive={Number(account?.realized_pnl ?? 0) >= 0} /></section>
        <section className="workspace"><div><div className="card"><div className="panel-title"><h2>Equity curve</h2><span className="badge">PAPER</span></div><div className="chart empty-chart">Live historical equity series will appear here as portfolio snapshots are recorded.</div></div>
          <div className="card section"><div className="panel-title"><h2>Open positions</h2><span className="badge">{positions.length} positions</span></div><table><thead><tr><th>Symbol</th><th>Qty</th><th>Avg</th><th>Market</th><th>P&L</th></tr></thead><tbody>{positions.map((p) => <tr key={p.id}><td className="symbol">{p.symbol}</td><td>{p.quantity}</td><td>{money(Number(p.average_price), account?.currency)}</td><td>{p.market_price ? money(Number(p.market_price), account?.currency) : "—"}</td><td className={Number(p.unrealized_pnl) >= 0 ? "positive" : "negative"}>{money(Number(p.unrealized_pnl), account?.currency)}</td></tr>)}{!positions.length && <tr><td colSpan={5}>No open positions.</td></tr>}</tbody></table></div>
          <div className="card section"><div className="panel-title"><h2>Recent orders</h2><span className="badge">{accountOrders.length}</span></div><table><thead><tr><th>Order</th><th>Symbol</th><th>Side</th><th>Qty</th><th>Price</th><th>Status</th></tr></thead><tbody>{accountOrders.slice(0, 10).map((o) => <tr key={o.id}><td>{o.client_order_id}</td><td className="symbol">{o.symbol}</td><td className={o.side === "BUY" ? "positive" : "negative"}>{o.side}</td><td>{o.quantity}</td><td>{o.average_fill_price ?? o.limit_price ?? o.stop_price ?? "Market"}</td><td><span className="badge">{o.status}</span></td></tr>)}{!accountOrders.length && <tr><td colSpan={6}>No orders for this account.</td></tr>}</tbody></table></div></div>
          <aside className="card order-card"><div className="panel-title"><h2>Place order</h2><span className="badge">Risk checked</span></div><form onSubmit={handleOrder}><div className="side-toggle"><button type="button" className={side === "BUY" ? "selected-buy" : ""} onClick={() => setSide("BUY")}>BUY</button><button type="button" className={side === "SELL" ? "selected-sell" : ""} onClick={() => setSide("SELL")}>SELL</button></div><div className="form"><div className="field"><label>SYMBOL</label><input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} required /></div><div className="field"><label>ORDER TYPE</label><select value={orderType} onChange={(e) => setOrderType(e.target.value as Order["order_type"])}><option>LIMIT</option><option>MARKET</option><option>STOP</option><option>STOP_LIMIT</option></select></div><div className="field"><label>QUANTITY</label><input type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} min="0.00000001" step="any" required /></div><div className="field"><label>LIMIT PRICE</label><input type="number" value={limitPrice} onChange={(e) => setLimitPrice(e.target.value)} min="0.00000001" step="0.05" disabled={orderType === "MARKET" || orderType === "STOP"} /></div><div className="field"><label>TIME IN FORCE</label><select value={tif} onChange={(e) => setTif(e.target.value as Order["time_in_force"])}><option>DAY</option><option>GTC</option><option>IOC</option><option>FOK</option></select></div><button className={`submit ${side === "SELL" ? "sell" : ""}`} disabled={loading || !accountId}>{loading ? "SUBMITTING…" : `${side} ${symbol}`}</button></div></form><div className="note">Every order is submitted to the backend risk engine. The current workspace is paper-only; market orders remain subject to backend market-data requirements.</div></aside>
        </section>
      </main>
    </div>
  );
}

function money(value: number, currency = "INR") { return new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 2 }).format(value); }
function Metric({ label, value, detail, positive = false }: { label: string; value: string; detail: string; positive?: boolean }) { return <div className="card"><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className={positive ? "positive" : "metric-label"}>{detail}</div></div>; }
