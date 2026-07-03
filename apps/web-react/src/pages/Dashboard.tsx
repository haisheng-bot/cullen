import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { request, postJson } from "../lib/api";
import { escapeHtml, formatPercent, formatRatio, formatRunTime, settledValue } from "../lib/format";

// Ported from apps/web/index.html's "每日研究首页" widget grid (L1645-1689, fns L2387-2479):
// renderDailyUniverse/renderDailyRecommendations/renderDailyRuns/renderDailyPortfolioRisk/
// loadDailyResearchHome. Data Source Health tile intentionally NOT ported here — it moved to
// Settings alone in commit 2.
//
// ponytail deviation (see plan Decisions #5/#7 + Sequencing commit 3): the legacy
// renderDailyPortfolioRisk/loadDailyResearchHome read `state.portfolios`/`activePortfolioSymbols`/
// `benchmarkSymbolInput`, all of which Decision #5 assigns to PortfolioResearch (not built until
// commit 7). Rather than reaching into a page that doesn't exist yet, this port fetches
// GET /portfolios directly (already an existing endpoint) and uses the first portfolio + the
// legacy's own "SPY" default-benchmark fallback, which matches legacy behavior whenever the user
// hasn't touched the benchmark input yet. addCurrentSymbolToPortfolio (mutates portfolio state) is
// deferred to PortfolioResearch (commit 7) instead of Dashboard for the same reason.

interface StockItem {
  symbol: string;
  name: string;
  sector?: string;
}

interface UniversePayload {
  universe_name?: string;
  source?: string;
  items?: StockItem[];
}

interface ScreeningCandidate {
  rank: number;
  symbol: string;
  recommendation: string;
  total_score: number;
}

interface ScreeningPayload {
  scoring_profile?: string;
  source?: string;
  candidates?: ScreeningCandidate[];
}

interface RunItem {
  state?: string;
  portfolio_name?: string;
  started_at?: string;
}

interface RunsPayload {
  items?: RunItem[];
}

interface RiskPayload {
  volatility_percent: number;
  beta: number;
  max_drawdown_percent: number;
  concentration_percent: number;
}

interface PortfolioItem {
  name: string;
  symbols: string[];
}

export default function Dashboard() {
  const [status, setStatus] = useState("汇总今日候选池、推荐、最近研究和当前组合风险。");

  const [universeCount, setUniverseCount] = useState("--");
  const [universeNote, setUniverseNote] = useState("等待加载候选池。");

  const [recommendationCount, setRecommendationCount] = useState("--");
  const [recommendationNote, setRecommendationNote] = useState("等待评分筛选。");
  const [recommendations, setRecommendations] = useState<ScreeningCandidate[]>([]);

  const [runCount, setRunCount] = useState("--");
  const [runNote, setRunNote] = useState("等待复盘历史。");
  const [runs, setRuns] = useState<RunItem[]>([]);

  const [riskValue, setRiskValue] = useState("--");
  const [riskNote, setRiskNote] = useState("请选择至少 2 只股票的组合。");
  const [activePortfolio, setActivePortfolio] = useState<PortfolioItem | null>(null);

  const loadDailyResearchHome = useCallback(async () => {
    setStatus("正在刷新每日研究首页...");

    const portfolios = await request<{ items: PortfolioItem[] }>("/portfolios").catch(() => ({ items: [] }));
    const portfolio = portfolios.items?.[0] || null;
    setActivePortfolio(portfolio);
    const symbols = portfolio?.symbols || [];

    const riskRequest =
      symbols.length >= 2
        ? postJson<RiskPayload>("/risk/portfolio", {
            symbols,
            weights: null,
            benchmark_symbol: "SPY",
            sector_map: {},
          })
        : Promise.resolve(null);

    const [universeResult, screeningResult, runsResult, riskResult] = await Promise.allSettled([
      request<UniversePayload>("/stocks/universe/most-active?limit=100"),
      request<ScreeningPayload>("/stocks/screening?limit=20"),
      request<RunsPayload>("/research-runs?limit=5&offset=0"),
      riskRequest,
    ]);

    const universe = settledValue(universeResult);
    const items = universe?.items || [];
    setUniverseCount(String(items.length || "--"));
    setUniverseNote(universe ? `${universe.universe_name || "Most Active"} · ${universe.source || "source unknown"}` : "候选池暂不可用。");

    const screening = settledValue(screeningResult);
    const candidates = (screening?.candidates || []).filter((_, index) => index < 20);
    setRecommendationCount(String(candidates.length || "--"));
    setRecommendationNote(screening ? `${screening.scoring_profile || "balanced"} · ${screening.source || "algorithm"}` : "评分筛选暂不可用。");
    setRecommendations(candidates.slice(0, 6));

    const runsPayload = settledValue(runsResult);
    const runItems = (runsPayload?.items || []).slice(0, 5);
    setRunCount(String(runItems.length || "--"));
    setRunNote(runsPayload ? "最近 Portfolio Research 复盘记录。" : "历史研究暂不可用。");
    setRuns(runItems);

    if (!symbols.length) {
      setRiskValue("--");
      setRiskNote("当前组合没有股票。");
    } else {
      const risk = settledValue(riskResult);
      if (!risk) {
        setRiskValue(symbols.length >= 2 ? "--" : "1 stock");
        setRiskNote(symbols.length >= 2 ? "组合风险暂不可用。" : "至少 2 只股票后计算组合风险。");
      } else {
        setRiskValue(formatPercent(risk.volatility_percent));
        setRiskNote(
          `Beta ${formatRatio(risk.beta)} · Max DD ${formatPercent(risk.max_drawdown_percent)} · Concentration ${formatPercent(risk.concentration_percent)}`,
        );
      }
    }

    setStatus("每日研究首页已刷新。本系统仅用于投资研究辅助，不构成任何投资建议。");
  }, []);

  useEffect(() => {
    loadDailyResearchHome();
  }, [loadDailyResearchHome]);

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Dashboard</div>
          <div className="muted">每日研究首页——今天市场发生了什么，哪些股票值得关注。</div>
        </div>
      </div>

      <section className="daily-home">
        <div className="daily-home-head">
          <div>
            <div className="daily-home-title">每日研究首页</div>
            <div className="muted" id="daily-home-status">{status}</div>
          </div>
          <span className="status-pill">P5</span>
        </div>
        <div className="daily-home-grid">
          <div className="daily-card">
            <div className="daily-card-title">Most Active Universe</div>
            <div className="daily-card-value" id="daily-universe-count">{universeCount}</div>
            <div className="daily-card-note" id="daily-universe-note">{universeNote}</div>
          </div>
          <div className="daily-card">
            <div className="daily-card-title">Top Recommendations</div>
            <div className="daily-card-value" id="daily-recommendation-count">{recommendationCount}</div>
            <div className="daily-card-note" id="daily-recommendation-note">{recommendationNote}</div>
          </div>
          <div className="daily-card">
            <div className="daily-card-title">Recent Research Runs</div>
            <div className="daily-card-value" id="daily-run-count">{runCount}</div>
            <div className="daily-card-note" id="daily-run-note">{runNote}</div>
          </div>
          <div className="daily-card">
            <div className="daily-card-title">Active Portfolio Risk</div>
            <div className="daily-card-value" id="daily-risk-value">{riskValue}</div>
            <div className="daily-card-note" id="daily-risk-note">{riskNote}</div>
          </div>
        </div>
        <div className="daily-lists">
          <div className="daily-card">
            <div className="daily-card-title">Top 20 推荐</div>
            <div className="daily-list" id="daily-recommendation-list">
              {recommendations.length ? (
                recommendations.map((item, index) => (
                  <div className="daily-row" key={`${item.symbol}-${index}`}>
                    <span className="daily-rank">#{escapeHtml(item.rank)}</span>
                    <span className="daily-symbol">{escapeHtml(item.symbol)} · {escapeHtml(item.recommendation)}</span>
                    <span className="daily-meta">{escapeHtml(item.total_score)}/100</span>
                  </div>
                ))
              ) : (
                <div className="workflow-note">暂无推荐候选。</div>
              )}
            </div>
          </div>
          <div className="daily-card">
            <div className="daily-card-title">最近 5 次研究</div>
            <div className="daily-list" id="daily-run-list">
              {runs.length ? (
                runs.map((item, index) => (
                  <div className="daily-row" key={index}>
                    <span className="daily-rank">{escapeHtml(item.state || "--")}</span>
                    <span className="daily-symbol">{escapeHtml(item.portfolio_name || "未命名组合")}</span>
                    <span className="daily-meta">{escapeHtml(formatRunTime(item.started_at))}</span>
                  </div>
                ))
              ) : (
                <div className="workflow-note">暂无最近研究运行。</div>
              )}
            </div>
          </div>
          <div className="daily-card">
            <div className="daily-card-title">当前组合摘要</div>
            <div className="daily-list" id="daily-portfolio-list">
              {activePortfolio && activePortfolio.symbols?.length ? (
                <div className="daily-row">
                  <span className="daily-rank">{escapeHtml(activePortfolio.name)}</span>
                  <span className="daily-symbol">{escapeHtml(activePortfolio.symbols.join(", "))}</span>
                  <span className="daily-meta">{activePortfolio.symbols.length} stocks</span>
                </div>
              ) : (
                <div className="workflow-note">请先向组合加入股票。</div>
              )}
            </div>
          </div>
        </div>
      </section>

      <div className="muted" style={{ marginTop: 8 }}>
        Market Scanner 与 Data Source Health 已迁移到独立页面：<Link to="/scanner">Scanner</Link> · <Link to="/settings">Settings</Link>
      </div>
    </div>
  );
}
