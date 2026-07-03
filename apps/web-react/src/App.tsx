import { useCallback, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { request } from "./lib/api";

// Persistent shell: top nav + left sidebar (Search + Most Active quick list only, per the
// requirements doc's nav design). Ported from apps/web/index.html's loadStocks/
// loadMostActiveUniverse/renderStockList (L2348-2383) — the "quick switch stock" behavior only;
// the full Market Scanner (multi-scanner-type tables) is its own routed page (commit 4).

interface StockListItem {
  symbol: string;
  name: string;
  sector?: string;
  rank?: number;
  analysis_tags?: string[];
}

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/scanner", label: "Scanner" },
  { to: "/stock/AAPL", label: "Stock" },
  { to: "/portfolio", label: "Portfolio" },
  { to: "/strategy", label: "Strategy" },
  { to: "/reports", label: "Reports" },
  { to: "/settings", label: "Settings" },
];

export default function App() {
  const [stocks, setStocks] = useState<StockListItem[]>([]);
  const [meta, setMeta] = useState("Most Active · US");
  const [searchInput, setSearchInput] = useState("");
  const [scanning, setScanning] = useState(false);
  const navigate = useNavigate();

  const loadStocks = useCallback(async (query = "") => {
    const data = await request<{ items: StockListItem[] }>(
      query ? `/stocks/search?q=${encodeURIComponent(query)}` : "/stocks/popular",
    );
    setStocks(data.items);
    setMeta(query ? `Search · ${query}` : "Popular US watchlist");
  }, []);

  const scanUniverse = useCallback(async (limit = 100) => {
    setScanning(true);
    setMeta("正在扫描 Most Active Universe...");
    try {
      const data = await request<{ universe_name: string; items: StockListItem[]; source: string }>(
        `/stocks/universe/most-active?limit=${limit}`,
      );
      setStocks(data.items);
      setMeta(`${data.universe_name} · ${data.items.length} · ${data.source}`);
    } catch (error) {
      // ponytail: the legacy app had no catch here either, leaving the UI stuck on "扫描中"
      // forever on failure (found during the earlier UX review) — preserved as-is per Phase 1
      // scope (port behavior, don't fix unrelated bugs); fix is a one-line follow-up.
      setMeta(error instanceof Error ? `扫描失败：${error.message}` : "扫描失败。");
    } finally {
      setScanning(false);
    }
  }, []);

  function onSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    loadStocks(searchInput.trim());
  }

  function onSelectStock(symbol: string) {
    navigate(`/stock/${encodeURIComponent(symbol)}`);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">OpenStock AI</div>
        <nav className="top-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <form className="search" onSubmit={onSearchSubmit}>
          <input
            placeholder="搜索美股代码：AAPL / NVDA / TSLA"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <button type="submit">Search</button>
        </form>
      </header>

      <aside className="app-sidebar">
        <div className="section-title">每日美股候选池</div>
        <div className="side-actions">
          <button type="button" disabled={scanning} onClick={() => scanUniverse(100)}>
            扫描最活跃 100 只
          </button>
        </div>
        <div className="muted">{meta}</div>
        <div className="stock-list">
          {stocks.map((stock) => (
            <button key={stock.symbol} type="button" className="stock-item" onClick={() => onSelectStock(stock.symbol)}>
              <span className="stock-main">
                <span className="symbol">{stock.symbol}</span>
                <span className="name">{stock.name}</span>
                <span className="sector">{(stock.analysis_tags || []).slice(0, 2).join(", ") || stock.sector}</span>
              </span>
              <span className="sector">{stock.rank ? `#${stock.rank}` : stock.sector}</span>
            </button>
          ))}
        </div>
      </aside>

      <main className="app-content">
        <Outlet />
      </main>

      <footer className="project-board">
        <div className="project-head">
          <div>
            <div className="project-title">项目开发界面</div>
            <div className="muted">OpenStock AI · v0.1.0 · 即开发即使用</div>
          </div>
          <span className="status-pill">MVP 可用</span>
        </div>
        <div className="layer-grid">
          <div className="layer">
            <div className="layer-name">Application</div>
            <div className="layer-status">美股操作界面、报价、走势、推荐展示已接入。</div>
          </div>
          <div className="layer">
            <div className="layer-name">Universe Layer</div>
            <div className="layer-status">每日扫描美股最活跃 Top 100，作为候选池。</div>
          </div>
          <div className="layer">
            <div className="layer-name">Algorithm Layer</div>
            <div className="layer-status">algorithm-v0.1，趋势型推荐算法，可单独测试。</div>
          </div>
          <div className="layer">
            <div className="layer-name">Model Layer</div>
            <div className="layer-status">LiteLLM-compatible provider 已建立，真实模型待配置。</div>
          </div>
          <div className="layer">
            <div className="layer-name">Data Layer</div>
            <div className="layer-status">Yahoo Finance chart API 已接入，美股为主。</div>
          </div>
          <div className="layer">
            <div className="layer-name">Workflow / Agent</div>
            <div className="layer-status">标准已定义，后续接入 LangGraph 与 Agent SDK。</div>
          </div>
          <div className="layer">
            <div className="layer-name">Governance</div>
            <div className="layer-status">GitHub、版本、AI 工具协作、敏捷迭代标准已建立。</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
