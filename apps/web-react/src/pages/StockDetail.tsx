import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { request, requestOptional } from "../lib/api";
import { escapeHtml, fmt, formatCompactNumber, formatMoney, formatPercent, formatRatio } from "../lib/format";
import OhlcChart, { type TrendPoint } from "../components/charts/OhlcChart";

// Ported from apps/web/index.html — quote/chart/metrics/score/news (fns L3863-4141):
// selectSymbol, loadMarket, renderQuote, renderMetrics, renderRecommendation, calculateRSI,
// renderScreenerGuide, renderNews, renderInspector, plus the 60s auto-refresh
// (window.setInterval(loadMarket, 60000), L4460). Canvas chart lives in
// components/charts/OhlcChart.tsx (commit 5 also proves the useRef+useEffect canvas-porting
// pattern used again by EquityCurveChart in commit 7).
//
// ponytail deviation (plan Decisions #5/#7): renderScreenerGuide's "行业强弱" factor and the
// chart's turnover-rate estimate both read `state.stocks`/`currentUniverseStock()`, i.e. the full
// Most Active universe list owned by Dashboard/MarketScanner (not this page, no global store per
// Decision #5). This port fetches the single stock's own record via the existing
// GET /stocks/search endpoint instead of reaching into another page's state; the
// universe-wide sector-average comparison (only available when a full stock list is in memory)
// is left as "数据不足" when unavailable, matching the legacy fallback for symbols outside the
// loaded stock list. "加入到组合"/"模拟回测" actions are deferred to PortfolioResearch (commit 7)
// for the same page-ownership reason (they mutate portfolio state, not stock-detail state).

interface Quote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  exchange_name?: string;
  currency?: string;
  source?: string;
  data_quality?: { source?: string; freshness?: string };
}

interface Trend {
  source: string;
  points: TrendPoint[];
  previous_close?: number;
  analysis_time: string;
}

interface HistoryPoint {
  close: number;
  high?: number;
  low?: number;
}

interface History {
  points?: HistoryPoint[];
}

interface Factor {
  name: string;
  score: number;
  explanation: string;
  weight: number;
}

interface Recommendation {
  symbol: string;
  total_score: number;
  recommendation: string;
  algorithm_version: string;
  source: string;
  factors?: Factor[];
  reasons?: string[];
  risks?: string[];
}

interface NewsItem {
  url: string;
  title: string;
  category: string;
  source: string;
  published_at?: string;
  summary?: string;
}

interface NewsPayload {
  items?: NewsItem[];
  coverage_note?: string;
}

interface UniverseStock {
  symbol: string;
  sector?: string;
  market_cap?: number;
  pe_ratio?: number;
  relative_volume?: number;
  change_percent?: number;
  volume?: number;
  price?: number;
}

function average(values: Array<number | null | undefined>): number | null {
  const usable = values.filter((value): value is number => Number.isFinite(value as number));
  if (!usable.length) return null;
  return usable.reduce((sum, value) => sum + value, 0) / usable.length;
}

export function calculateRSI(closes: number[], period = 14): number | null {
  if (closes.length <= period) return null;
  let gains = 0;
  let losses = 0;
  const slice = closes.slice(-period - 1);
  for (let index = 1; index < slice.length; index += 1) {
    const change = slice[index] - slice[index - 1];
    if (change >= 0) gains += change;
    else losses += Math.abs(change);
  }
  const averageGain = gains / period;
  const averageLoss = losses / period;
  if (averageLoss === 0) return 100;
  const rs = averageGain / averageLoss;
  return 100 - 100 / (1 + rs);
}

function statusClass(status: string): string {
  if (["活跃", "强势", "高位", "站上均线", "行业偏强", "估值可观察"].includes(status)) return "positive";
  if (["异常活跃", "波动较高", "跌破均线", "弱势", "行业偏弱", "高估值"].includes(status)) return "negative";
  return "neutral";
}

interface GuideMetric {
  name: string;
  tag: string;
  value: string;
  status: string;
  text: string;
}

export default function StockDetail() {
  const { symbol: routeSymbol = "AAPL" } = useParams();
  const symbol = routeSymbol.toUpperCase();

  const [range, setRange] = useState("1d");
  const [interval, setInterval_] = useState("1m");
  const [status, setStatus] = useState("准备读取行情...");
  const [refreshing, setRefreshing] = useState(false);

  const [quote, setQuote] = useState<Quote | null>(null);
  const [trend, setTrend] = useState<Trend | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [guideMetrics, setGuideMetrics] = useState<GuideMetric[]>([]);
  const [news, setNews] = useState<NewsPayload | null>(null);

  const [reportStatus, setReportStatus] = useState('点击「生成研究报告」，由 Report Agent 综合五因子评分与近期资讯生成一段研究结论。');
  const [reportConclusion, setReportConclusion] = useState<{ symbol: string; model: string; conclusion: string; data_source: string[]; risk_disclaimer: string } | null>(null);

  const universeStockRef = useRef<UniverseStock | null>(null);

  function normalizeInterval(nextRange: string, currentInterval: string): string {
    if (nextRange !== "1d" && currentInterval === "1m") return "5m";
    return currentInterval;
  }

  const loadMarket = useCallback(async () => {
    const effectiveInterval = normalizeInterval(range, interval);
    if (effectiveInterval !== interval) setInterval_(effectiveInterval);
    setRefreshing(true);
    setStatus(`正在读取 ${symbol} 美股行情...`);
    try {
      const [quoteData, trendData] = await Promise.all([
        request<Quote>(`/stocks/${symbol}/quote`),
        request<Trend>(`/stocks/${symbol}/trend?range=${range}&interval=${effectiveInterval}`),
      ]);
      const [recommendationData, historyData, newsData, universeData] = await Promise.all([
        request<Recommendation>(`/stocks/${symbol}/recommendation`),
        requestOptional<History>(`/stocks/${symbol}/history?range=1y&interval=1d`),
        request<NewsPayload>(`/stocks/${symbol}/news?years=3&limit=60`),
        requestOptional<{ items: UniverseStock[] }>(`/stocks/search?q=${encodeURIComponent(symbol)}`),
      ]);
      const stock = universeData?.items?.find((item) => item.symbol === symbol) || null;
      universeStockRef.current = stock;

      setQuote(quoteData);
      setTrend(trendData);
      setRecommendation(recommendationData);
      setNews(newsData);
      setGuideMetrics(renderScreenerGuide(quoteData, trendData, historyData, recommendationData, stock));
      setStatus(`${symbol} 行情已更新 · 买/卖量为分钟线方向估算`);
    } catch (error) {
      setStatus(`读取失败：${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setRefreshing(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, range, interval]);

  useEffect(() => {
    loadMarket();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol]);

  useEffect(() => {
    const timer = window.setInterval(loadMarket, 60000);
    return () => window.clearInterval(timer);
  }, [loadMarket]);

  function renderScreenerGuide(
    quoteData: Quote,
    trendData: Trend,
    historyData: History | null,
    recommendationData: Recommendation,
    stock: UniverseStock | null,
  ): GuideMetric[] {
    const trendPoints = trendData.points || [];
    const historyPoints = historyData?.points || [];
    const closes = historyPoints.map((point) => point.close).filter((value) => Number.isFinite(value));
    const trendVolumes = trendPoints.map((point) => point.volume || 0).filter((value) => value > 0);
    const latestPoint = trendPoints[trendPoints.length - 1];
    const latestVolumePoint = [...trendPoints].reverse().find((point) => point.volume && point.volume > 0);
    const latestPrice = quoteData.price || latestPoint?.close || stock?.price || null;
    const totalIntradayVolume = trendVolumes.reduce((sum, value) => sum + value, 0);
    const displayVolume = stock?.volume || totalIntradayVolume || latestPoint?.volume || null;
    const averageIntradayVolume = average(trendVolumes);
    const latestVolumeRatio = averageIntradayVolume && latestVolumePoint?.volume ? latestVolumePoint.volume / averageIntradayVolume : stock?.relative_volume ?? null;
    const changePercent = quoteData.change_percent ?? stock?.change_percent ?? null;
    const marketCap = stock?.market_cap ?? null;
    const peRatio = stock?.pe_ratio ?? null;
    const rsi = calculateRSI(closes);
    const ma20 = average(closes.slice(-20));
    const ma50 = average(closes.slice(-50));
    const high52 = historyPoints.length ? Math.max(...historyPoints.map((point) => point.high || point.close)) : null;
    const low52 = historyPoints.length ? Math.min(...historyPoints.map((point) => point.low || point.close)) : null;
    const rangePosition = high52 && low52 && high52 !== low52 && latestPrice ? ((latestPrice - low52) / (high52 - low52)) * 100 : null;
    const volatility = closes.length ? ((Math.max(...closes.slice(-30)) - Math.min(...closes.slice(-30))) / (average(closes.slice(-30)) || 1)) * 100 : null;
    // ponytail: sector-peer average change needs the full Most Active universe list (owned by
    // Dashboard/MarketScanner, not fetched here) — left as "数据不足" like the legacy fallback for
    // symbols outside the loaded stock list.
    const sectorAverageChange: number | null = null;
    const maStatus = latestPrice && ma20 && ma50 ? (latestPrice >= ma20 && latestPrice >= ma50 ? "站上均线" : "跌破均线") : "数据不足";
    const rsiStatus = rsi === null ? "数据不足" : rsi >= 70 ? "偏热" : rsi <= 30 ? "弱势" : "中性";
    const relVolStatus = latestVolumeRatio === null || latestVolumeRatio === undefined ? "数据不足" : latestVolumeRatio >= 2 ? "异常活跃" : latestVolumeRatio >= 1 ? "活跃" : "平稳";
    const changeStatus = changePercent === null || changePercent === undefined ? "数据不足" : changePercent >= 2 ? "强势" : changePercent <= -2 ? "弱势" : "中性";
    return [
      {
        name: "成交量",
        tag: "Volume",
        value: formatCompactNumber(displayVolume),
        status: displayVolume ? (displayVolume >= 10_000_000 ? "活跃" : "平稳") : "数据不足",
        text: `候选池成交量用于判断流动性；当前估算成交额 ${formatMoney(displayVolume && latestPrice ? displayVolume * latestPrice : null)}。`,
      },
      {
        name: "相对成交量",
        tag: "Rel Vol",
        value: formatRatio(latestVolumeRatio),
        status: relVolStatus,
        text: "用最新分钟成交量相对当日分钟均量估算，后续可接入历史日均量作为正式 Rel Vol。",
      },
      {
        name: "涨跌幅",
        tag: "% Change",
        value: formatPercent(changePercent),
        status: changeStatus,
        text: "衡量当日价格冲击，只代表研究关注强弱，不构成买卖建议。",
      },
      {
        name: "市值",
        tag: "Market Cap",
        value: formatMoney(marketCap),
        status: marketCap ? (marketCap >= 200_000_000_000 ? "大盘股" : "中小盘") : "数据不足",
        text: "来自候选池报价数据，用于区分稳定性和波动弹性。",
      },
      {
        name: "P/E",
        tag: "Valuation",
        value: peRatio ? peRatio.toFixed(2) : "--",
        status: peRatio ? (peRatio > 60 ? "高估值" : peRatio > 0 && peRatio < 20 ? "估值可观察" : "中性") : "数据不足",
        text: "估值需要结合增长、行业和利润质量；低 P/E 或高 P/E 都不能单独判断好坏。",
      },
      {
        name: "RSI",
        tag: "Momentum",
        value: rsi === null ? "--" : rsi.toFixed(1),
        status: rsiStatus,
        text: "基于 1 年日线最近 14 个交易日估算，70 以上偏热，30 以下偏弱。",
      },
      {
        name: "均线位置",
        tag: "MA",
        value: ma20 && ma50 ? `20D ${fmt(ma20)} / 50D ${fmt(ma50)}` : "--",
        status: maStatus,
        text: `当前价 ${fmt(latestPrice)}，用于判断是否处于短中期趋势线上方。`,
      },
      {
        name: "波动率",
        tag: "Risk",
        value: formatPercent(volatility),
        status: volatility === null ? "数据不足" : volatility >= 12 ? "波动较高" : "中性",
        text: "用最近 30 个交易日高低区间相对均价估算，数值越高仓位管理要求越高。",
      },
      {
        name: "52 周位置",
        tag: "Range",
        value: rangePosition === null ? "--" : `${rangePosition.toFixed(0)}%`,
        status: rangePosition === null ? "数据不足" : rangePosition >= 80 ? "高位" : rangePosition <= 20 ? "弱势" : "中性",
        text: high52 && low52 ? `52 周低 ${fmt(low52)} / 高 ${fmt(high52)}。接近高位代表强势，也要观察过热。` : "需要 1 年历史数据。",
      },
      {
        name: "Beta",
        tag: "Market Risk",
        value: "--",
        status: "待接入",
        text: "第一阶段尚未接入指数回归或数据商 Beta，后续用 SPY 回归或基本面数据源补齐。",
      },
      {
        name: "收入 / EPS 增长",
        tag: "Growth",
        value: recommendationData?.total_score ? `${recommendationData.total_score}/100` : "--",
        status: "待接入",
        text: "当前先显示算法综合分；正式收入和 EPS 增长需接入财报标准化数据。",
      },
      {
        name: "行业强弱",
        tag: "Sector",
        value: stock?.sector || "--",
        status: sectorAverageChange === null ? "数据不足" : sectorAverageChange >= 1 ? "行业偏强" : sectorAverageChange <= -1 ? "行业偏弱" : "中性",
        text: sectorAverageChange === null ? "搜索股票不在当前候选池时，行业相对强弱暂不可用。" : `当前 Top 100 中同板块平均涨跌 ${formatPercent(sectorAverageChange)}。`,
      },
    ];
  }

  async function generateResearchReport() {
    setReportConclusion(null);
    setReportStatus(`正在为 ${symbol} 生成研究报告…`);
    try {
      const payload = await request<{ symbol: string; model: string; conclusion: string; data_source: string[]; risk_disclaimer: string }>(`/stocks/${symbol}/report`);
      setReportConclusion(payload);
    } catch (error) {
      setReportStatus(`生成研究报告失败：${error instanceof Error ? error.message : String(error)}`);
    }
  }

  const changeClass = (quote?.change ?? 0) >= 0 ? "positive" : "negative";
  const changeSign = (quote?.change ?? 0) >= 0 ? "+" : "";

  const marketCap = useMemo(() => universeStockRef.current?.market_cap ?? null, [trend]);

  return (
    <div>
      <section className="quote-row">
        <div>
          <div className="quote-symbol" id="quote-symbol">{quote?.symbol || symbol}</div>
          <div className="muted" id="quote-meta">
            {quote ? `${quote.exchange_name || "US"} · ${quote.currency || "USD"} · ${quote.data_quality?.source || quote.source || "--"} · ${quote.data_quality?.freshness || "unknown"}` : "NASDAQ · USD"}
          </div>
        </div>
        <div>
          <div className="quote-price" id="quote-price">{quote ? fmt(quote.price) : "--"}</div>
          <div id="quote-change" className={changeClass}>
            {quote ? `${changeSign}${fmt(quote.change)} (${changeSign}${fmt(quote.change_percent)}%)` : "--"}
          </div>
        </div>
      </section>

      <section className="toolbar">
        <label>
          范围
          <select id="range" value={range} onChange={(e) => setRange(e.target.value)}>
            <option value="1d">1日</option>
            <option value="5d">5日</option>
            <option value="1mo">1月</option>
            <option value="3mo">3月</option>
            <option value="6mo">6月</option>
            <option value="1y">1年</option>
          </select>
        </label>
        <label>
          间隔
          <select id="interval" value={interval} onChange={(e) => setInterval_(e.target.value)}>
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="60m">60m</option>
            <option value="1d">1d</option>
          </select>
        </label>
        <button id="refresh-button" disabled={refreshing} onClick={loadMarket}>刷新走势</button>
      </section>

      <section className="card chart-card">
        <OhlcChart points={trend?.points || []} previousClose={trend?.previous_close} marketCap={marketCap} />
        <div className="status" id="status">{status}</div>
      </section>

      <section className="metrics">
        <div className="metric"><div className="label">数据源</div><div className="value" id="metric-source">{trend?.source || "--"}</div></div>
        <div className="metric"><div className="label">最新点数</div><div className="value" id="metric-points">{trend?.points?.length ?? "--"}</div></div>
        <div className="metric"><div className="label">前收盘</div><div className="value" id="metric-prev">{trend ? fmt(trend.previous_close) : "--"}</div></div>
        <div className="metric"><div className="label">更新时间</div><div className="value" id="metric-time">{trend?.analysis_time ? new Date(trend.analysis_time).toLocaleTimeString() : "--"}</div></div>
      </section>

      <section className="analysis-guide">
        <div className="project-head">
          <div>
            <div className="project-title">常用分析维度解读</div>
            <div className="muted">用于每日候选池、推荐算法和人工复核。</div>
          </div>
          <span className="status-pill">Screener Guide</span>
        </div>
        <div className="guide-grid" id="screener-guide-grid">
          {guideMetrics.map((metric) => (
            <div className="guide-item" key={metric.name}>
              <div className="guide-name"><span>{escapeHtml(metric.name)}</span><span className="guide-tag">{escapeHtml(metric.tag)}</span></div>
              <div className="guide-value">{escapeHtml(metric.value)}</div>
              <div className={`guide-status ${statusClass(metric.status)}`}>{escapeHtml(metric.status)}</div>
              <div className="guide-text">{escapeHtml(metric.text)}</div>
            </div>
          ))}
        </div>
      </section>

      <div className="section-title">AI 研究报告</div>
      <div className="analysis" id="report-panel">
        {reportConclusion ? (
          <div className="note" id="report-conclusion">
            <div><strong>{reportConclusion.symbol}</strong> · {reportConclusion.model}</div>
            <div style={{ marginTop: 6 }}>{reportConclusion.conclusion}</div>
            <div className="muted" style={{ marginTop: 6 }}>数据来源：{reportConclusion.data_source.join(", ")}</div>
            <div className="muted">{reportConclusion.risk_disclaimer}</div>
          </div>
        ) : (
          <div className="note" id="report-status">{reportStatus}</div>
        )}
        <button type="button" id="action-report" onClick={generateResearchReport}>生成研究报告</button>
      </div>

      <div className="section-title">AI 研究评分</div>
      <div className="analysis">
        <div className="score">
          <div className="score-number" id="score-number">{recommendation?.total_score ?? "--"}</div>
          <div>
            <div className="symbol" id="score-label">{recommendation?.recommendation || "等待数据"}</div>
            <div className="muted" id="algorithm-version">
              {recommendation ? `${recommendation.algorithm_version} · ${recommendation.source}` : "等待算法层返回结果。"}
            </div>
          </div>
        </div>
        <div className="factor-list" id="factor-list">
          {(recommendation?.factors || []).map((factor) => (
            <div className="factor" key={factor.name}>
              <div className="factor-head"><span>{factor.name}</span><span>{factor.score}</span></div>
              <div className="factor-bar"><span style={{ width: `${factor.score}%` }} /></div>
              <div className="muted">{factor.explanation} · 权重 {(factor.weight * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
        <ul className="bullets" id="reason-list">
          {(recommendation?.reasons || []).map((reason, index) => (
            <li key={index}>{reason}</li>
          ))}
        </ul>
        <div className="note" id="research-note">
          {recommendation ? `${recommendation.symbol} 算法推荐等级：${recommendation.recommendation}。${(recommendation.risks || []).join(" ")}` : "请选择美股并刷新走势。当前页面只做研究辅助，不下单、不承诺收益。"}
        </div>
        <div className="note">本系统仅用于投资研究辅助，不构成任何投资建议。</div>
      </div>

      <div className="section-title">Policy & News · 3Y Archive</div>
      <div className="news-list" id="news-list">
        {(news?.items || []).map((item) => (
          <div className="news-item" key={item.url}>
            <a className="news-title" href={item.url} target="_blank" rel="noreferrer">{escapeHtml(item.title)}</a>
            <div className="news-meta">{escapeHtml(item.category)} · {escapeHtml(item.source)} · {item.published_at ? new Date(item.published_at).toLocaleDateString() : ""}</div>
            {item.summary && <div className="news-summary">{escapeHtml(item.summary)}</div>}
          </div>
        ))}
      </div>
      <div className="note" id="news-coverage-note">{news?.coverage_note || "Recent news and 3-year SEC disclosure traces will appear here."}</div>
    </div>
  );
}
