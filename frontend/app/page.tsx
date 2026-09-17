"use client";

import { useState } from "react";

const positions = [
  { symbol: "NIFTY", qty: "50", avg: "22,410.20", ltp: "22,486.10", pnl: "+₹3,795" },
  { symbol: "RELIANCE", qty: "25", avg: "2,921.40", ltp: "2,908.70", pnl: "−₹318" },
  { symbol: "TCS", qty: "10", avg: "4,182.00", ltp: "4,246.50", pnl: "+₹645" },
];

const orders = [
  { id: "ORD-1048", symbol: "NIFTY", side: "BUY", qty: "50", price: "22,410.20", status: "FILLED" },
  { id: "ORD-1047", symbol: "RELIANCE", side: "SELL", qty: "25", price: "2,910.00", status: "PARTIALLY_FILLED" },
  { id: "ORD-1046", symbol: "TCS", side: "BUY", qty: "10", price: "4,182.00", status: "FILLED" },
];

export default function Dashboard() {
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [symbol, setSymbol] = useState("NIFTY");

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">MyTrading<span>System</span></div>
        <nav className="nav">
          <button className="active">▦ &nbsp; Dashboard</button>
          <button>◫ &nbsp; Positions</button>
          <button>↕ &nbsp; Orders</button>
          <button>◒ &nbsp; Risk</button>
          <button>⌁ &nbsp; Strategies</button>
          <button>◌ &nbsp; Backtests</button>
          <button>⚙ &nbsp; Settings</button>
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <div className="eyebrow">Trading workspace</div>
            <h1>Portfolio overview</h1>
          </div>
          <div className="account">
            <span className="badge">PAPER</span>
            <select aria-label="Trading account">
              <option>Primary Account · ₹10,00,000</option>
            </select>
          </div>
        </header>

        <section className="metrics">
          <Metric label="Net liquidation" value="₹10,42,680" detail="+4.27%" positive />
          <Metric label="Available cash" value="₹7,84,220" detail="76.4% of equity" />
          <Metric label="Unrealized P&L" value="+₹4,122" detail="Today" positive />
          <Metric label="Realized P&L" value="+₹18,558" detail="Today" positive />
        </section>

        <section className="workspace">
          <div>
            <div className="card">
              <div className="panel-title"><h2>Equity curve</h2><span className="badge">1D · PAPER</span></div>
              <div className="chart" aria-label="Portfolio equity curve">
                {[25, 50, 75].map((top) => <div key={top} className="gridline" style={{ top: `${top}%` }} />)}
                <svg viewBox="0 0 900 330" preserveAspectRatio="none" role="img">
                  <polyline fill="none" stroke="var(--green)" strokeWidth="3" points="0,260 65,248 125,255 190,220 255,232 325,186 390,195 455,150 520,165 590,120 655,138 720,92 785,110 845,62 900,76" />
                </svg>
              </div>
            </div>

            <div className="card section">
              <div className="panel-title"><h2>Open positions</h2><span className="badge">3 positions</span></div>
              <table><thead><tr><th>Symbol</th><th>Qty</th><th>Avg</th><th>LTP</th><th>P&L</th></tr></thead><tbody>
                {positions.map((p) => <tr key={p.symbol}><td className="symbol">{p.symbol}</td><td>{p.qty}</td><td>{p.avg}</td><td>{p.ltp}</td><td className={p.pnl.startsWith("+") ? "positive" : "negative"}>{p.pnl}</td></tr>)}
              </tbody></table>
            </div>

            <div className="card section">
              <div className="panel-title"><h2>Recent orders</h2><span className="badge">Latest 3</span></div>
              <table><thead><tr><th>Order</th><th>Symbol</th><th>Side</th><th>Qty</th><th>Price</th><th>Status</th></tr></thead><tbody>
                {orders.map((o) => <tr key={o.id}><td>{o.id}</td><td className="symbol">{o.symbol}</td><td className={o.side === "BUY" ? "positive" : "negative"}>{o.side}</td><td>{o.qty}</td><td>{o.price}</td><td><span className="badge">{o.status}</span></td></tr>)}
              </tbody></table>
            </div>
          </div>

          <aside className="card order-card">
            <div className="panel-title"><h2>Place order</h2><span className="badge">Risk checked</span></div>
            <div className="side-toggle">
              <button className={side === "BUY" ? "selected-buy" : ""} onClick={() => setSide("BUY")}>BUY</button>
              <button className={side === "SELL" ? "selected-sell" : ""} onClick={() => setSide("SELL")}>SELL</button>
            </div>
            <div className="form">
              <div className="field"><label>SYMBOL</label><input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} /></div>
              <div className="field"><label>ORDER TYPE</label><select><option>LIMIT</option><option>MARKET</option><option>STOP</option><option>STOP LIMIT</option></select></div>
              <div className="field"><label>QUANTITY</label><input type="number" defaultValue="50" min="1" /></div>
              <div className="field"><label>LIMIT PRICE</label><input type="number" defaultValue="22410.20" step="0.05" /></div>
              <div className="field"><label>TIME IN FORCE</label><select><option>DAY</option><option>GTC</option><option>IOC</option><option>FOK</option></select></div>
              <button className={`submit ${side === "SELL" ? "sell" : ""}`}>{side} {symbol}</button>
            </div>
            <div className="note">Orders will enter the risk engine before execution. This workspace is paper-only; no live broker connection is enabled.</div>
          </aside>
        </section>
      </main>
    </div>
  );
}

function Metric({ label, value, detail, positive = false }: { label: string; value: string; detail: string; positive?: boolean }) {
  return <div className="card"><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className={positive ? "positive" : "metric-label"}>{detail}</div></div>;
}
