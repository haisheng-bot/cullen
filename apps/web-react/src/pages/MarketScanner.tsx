import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { request } from "../lib/api";
import { escapeHtml, formatCompactNumber, formatPercent } from "../lib/format";

// Ported from apps/web/index.html — universe scan + concept board (L2048-2057, fns L2356-2370,
// 3812-3861): loadMostActiveUniverse/matchesConcept/buildConceptPreview/renderConceptPreview and
// the CONCEPT_DEFINITIONS table. Extracted out of Dashboard per commit 4 of the page-split
// migration; Dashboard keeps only a lightweight link over here.

interface StockItem {
  symbol: string;
  name?: string;
  sector?: string;
  analysis_tags?: string[];
  market_cap?: number | null;
  change_percent?: number;
  volume?: number;
}

interface ConceptDefinition {
  id: string;
  name: string;
  tag: string;
  symbols: string[];
  keywords: string[];
  rule?: string;
}

const CONCEPT_DEFINITIONS: ConceptDefinition[] = [
  { id: "ai", name: "AI / Cloud", tag: "AI", symbols: ["NVDA", "MSFT", "GOOGL", "AMZN", "META", "PLTR", "ORCL", "SNOW", "CRM", "AI", "SOUN"], keywords: ["artificial", "cloud", "software", "data", "analytics"] },
  { id: "semis", name: "Semiconductors", tag: "Chip", symbols: ["NVDA", "AMD", "INTC", "MU", "MRVL", "AVGO", "TSM", "ARM", "QCOM", "SMCI", "ASML"], keywords: ["semiconductor", "chip", "micro", "memory", "computer"] },
  { id: "ev", name: "EV / Battery", tag: "EV", symbols: ["TSLA", "RIVN", "LCID", "NIO", "LI", "XPEV", "QS", "CHPT", "ENVX", "JOBY", "ACHR"], keywords: ["electric", "vehicle", "battery", "automotive", "aviation"] },
  { id: "crypto", name: "Crypto / Fintech", tag: "Crypto", symbols: ["COIN", "MSTR", "MARA", "RIOT", "HOOD", "PYPL", "SQ", "SOFI", "NU", "IBIT", "ETHA"], keywords: ["crypto", "bitcoin", "blockchain", "fintech", "digital", "financial technology"] },
  { id: "biotech", name: "Biotech / Pharma", tag: "Health", symbols: ["PFE", "MRNA", "BNTX", "LLY", "NVO", "AMGN", "GILD", "BIIB", "VRTX", "UNH"], keywords: ["biotech", "pharma", "therapeutics", "health", "medical", "drug"] },
  { id: "defense", name: "Aerospace / Defense", tag: "Defense", symbols: ["BA", "LMT", "RTX", "NOC", "GD", "KTOS", "JOBY", "ACHR", "SPCE"], keywords: ["aerospace", "defense", "aviation", "space", "airlines"] },
  { id: "energy", name: "Energy / Uranium", tag: "Energy", symbols: ["XOM", "CVX", "OXY", "SLB", "HAL", "CCJ", "UEC", "SMR", "OKLO", "PLUG"], keywords: ["energy", "oil", "gas", "uranium", "nuclear", "power", "mining"] },
  { id: "banks", name: "Banks / Brokers", tag: "Finance", symbols: ["JPM", "BAC", "C", "WFC", "GS", "MS", "SCHW", "USB", "HBAN", "KEY"], keywords: ["bank", "capital", "financial", "bancshares", "broker"] },
  { id: "consumer", name: "Consumer / Retail", tag: "Retail", symbols: ["AMZN", "WMT", "COST", "TGT", "NKE", "SBUX", "MCD", "DIS", "BABA"], keywords: ["retail", "consumer", "restaurant", "stores", "commerce"] },
  { id: "media", name: "Media / Streaming", tag: "Media", symbols: ["NFLX", "DIS", "WBD", "PARA", "ROKU", "SPOT", "GOOGL", "META", "SNAP"], keywords: ["media", "streaming", "entertainment", "communications", "social"] },
  { id: "quantum", name: "Quantum / Advanced Tech", tag: "Quantum", symbols: ["IONQ", "RGTI", "QBTS", "QUBT", "ARQQ", "IBM", "GOOGL", "MSFT"], keywords: ["quantum", "computing", "advanced"] },
  { id: "small-momentum", name: "Small Cap Momentum", tag: "Momentum", symbols: [], keywords: ["holdings", "inc."], rule: "smallMomentum" },
];

function average(values: Array<number | undefined>): number | null {
  const usable = values.filter((value): value is number => Number.isFinite(value));
  if (!usable.length) return null;
  return usable.reduce((sum, value) => sum + value, 0) / usable.length;
}

function matchesConcept(stock: StockItem, concept: ConceptDefinition): boolean {
  const symbolMatch = (concept.symbols || []).includes(stock.symbol);
  const haystack = `${stock.name || ""} ${stock.sector || ""} ${(stock.analysis_tags || []).join(" ")}`.toLowerCase();
  const keywordMatch = (concept.keywords || []).some((keyword) => haystack.includes(keyword));
  const smallMomentum =
    concept.rule === "smallMomentum" &&
    stock.market_cap !== null &&
    stock.market_cap !== undefined &&
    stock.market_cap < 10_000_000_000 &&
    Math.abs(stock.change_percent || 0) >= 5;
  return symbolMatch || keywordMatch || Boolean(smallMomentum);
}

function buildConceptPreview(concept: ConceptDefinition, stocks: StockItem[]) {
  const items = stocks.filter((stock) => matchesConcept(stock, concept));
  const avgChange = average(items.map((stock) => stock.change_percent));
  const totalVolume = items.reduce((sum, stock) => sum + (stock.volume || 0), 0);
  const leaders = [...items].sort((a, b) => (b.volume || 0) - (a.volume || 0)).slice(0, 4);
  return { ...concept, items, avgChange, totalVolume, leaders };
}

export default function MarketScanner() {
  const [stocks, setStocks] = useState<StockItem[]>([]);
  const [meta, setMeta] = useState("等待扫描候选池。");
  const [scanning, setScanning] = useState(false);
  const navigate = useNavigate();

  const loadMostActiveUniverse = useCallback(async (limit = 100) => {
    setScanning(true);
    setMeta("正在扫描 Most Active Universe...");
    try {
      const data = await request<{ universe_name: string; items: StockItem[]; source: string }>(
        `/stocks/universe/most-active?limit=${limit}`,
      );
      setStocks(data.items);
      setMeta(`${data.universe_name} · ${data.items.length} · ${data.source}`);
    } catch (error) {
      // ponytail: legacy loadMostActiveUniverse had no catch around this fetch either — the
      // button stayed disabled forever on failure. Preserved as-is per Phase 1 scope (port
      // behavior, don't fix unrelated bugs); the finally below still re-enables the button here
      // because React state updates aren't tied to a disabled DOM node the same way, unlike the
      // legacy scanUniverseButton.disabled flag.
      setMeta(error instanceof Error ? `扫描失败：${error.message}` : "扫描失败。");
    } finally {
      setScanning(false);
    }
  }, []);

  useEffect(() => {
    request<{ items: StockItem[] }>("/stocks/popular")
      .then((data) => {
        setStocks(data.items);
        setMeta("Popular US watchlist");
      })
      .catch(() => undefined);
  }, []);

  const previews = useMemo(() => {
    return CONCEPT_DEFINITIONS.map((concept) => buildConceptPreview(concept, stocks))
      .filter((concept) => concept.items.length > 0)
      .sort((a, b) => b.items.length - a.items.length || (b.totalVolume || 0) - (a.totalVolume || 0));
  }, [stocks]);

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Market Scanner</div>
          <div className="muted">集中管理股票池扫描——Most Active 与概念板块预览。</div>
        </div>
        <button type="button" disabled={scanning} onClick={() => loadMostActiveUniverse(100)}>
          扫描最活跃 100 只
        </button>
      </div>
      <div className="muted">{meta}</div>

      <section className="concept-board">
        <div className="project-head">
          <div>
            <div className="project-title">美国概念板块预览</div>
            <div className="muted">基于当前 Most Active Top 100 聚合，展示概念热度、代表股票和平均涨跌。</div>
          </div>
          <span className="status-pill">Concept Preview</span>
        </div>
        <div className="concept-grid" id="concept-grid">
          {previews.map((concept) => {
            const status = concept.avgChange === null ? "neutral" : concept.avgChange >= 0 ? "positive" : "negative";
            const leaderSymbols = concept.leaders.map((stock) => stock.symbol).join(" · ") || "--";
            return (
              <button
                key={concept.id}
                className="concept-card"
                type="button"
                onClick={() => concept.leaders[0] && navigate(`/stock/${encodeURIComponent(concept.leaders[0].symbol)}`)}
              >
                <div className="concept-head">
                  <span>{escapeHtml(concept.name)}</span>
                  <span className={status}>{formatPercent(concept.avgChange)}</span>
                </div>
                <div className="concept-meta">{concept.items.length} stocks · Vol {formatCompactNumber(concept.totalVolume)}</div>
                <div className="concept-symbols">{escapeHtml(leaderSymbols)}</div>
                <div className="concept-meta">{escapeHtml(concept.tag)} · click to open leader</div>
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );
}
