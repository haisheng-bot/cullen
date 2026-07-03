import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { deleteJson, friendlyBacktestError, friendlyWorkflowError, postJson, putJson, request } from "../lib/api";
import { downloadTextFile, escapeHtml, fmt, formatPercent, formatRatio } from "../lib/format";
import EquityCurveChart, { type EquityCurvePoint } from "../components/charts/EquityCurveChart";

// PortfolioResearch — the largest page (plan commit 7, final commit of the page-split migration).
// Ports the remaining Portfolio Research Workbench code from apps/web/index.html: portfolio CRUD
// (renderPortfolioList/removeSymbolFromPortfolio/saveActivePortfolioConfig, L2810-3108),
// export/import/compare (exportPortfolio/openPortfolioImport/parsePortfolioImportText/
// importPortfolioFromData/fetchPortfolioRiskFor/renderPortfolioCompareResult/runPortfolioCompare,
// L2880-3069), the 6-step workflow form + payload builders (buildWorkflowPayload/
// buildPortfolioResearchPayload/validateBacktestForm/runPortfolioWorkflow, L3110-3336, 3777-3810),
// result renderers (renderBacktestResult/renderAiSummary/renderPortfolioRecommendation/
// renderRiskReport/renderOptimizerResult/renderWorkflowResult/renderPortfolioResearchResult,
// L3337-3629), and EquityCurveChart (components/charts/EquityCurveChart.tsx, from drawEquityCurve).
//
// ponytail deviations:
// - buildWorkflowPayload/renderWorkflowResult/friendlyWorkflowError are ported verbatim but are
//   dead code here exactly as they were in the legacy app (grep shows buildWorkflowPayload is
//   never called there either — runPortfolioWorkflow always used buildPortfolioResearchPayload +
//   POST /portfolio-research/run). Kept for governance-string parity and as a documented no-op,
//   not invented behavior.
// - StrategyLibrary (commit 6) can't call this page's live applyStrategy (didn't exist yet), so it
//   navigates to /portfolio?strategy=<name>[&autorun=1]; this page reads that query param on mount,
//   fetches GET /strategies itself (no global store, per Decision #5) to find the named strategy,
//   and applies it to the form — completing the hand-off commit 6 set up.
// - Reports.tsx's "在 Portfolio Research 中查看完整结果" link passes ?trace=<id>; this page reads
//   it and calls loadResearchRunDetail (GET /portfolio-research/{trace_id}) to render the full
//   result via renderPortfolioResearchResult, same as legacy's Research Run click-through.

interface PortfolioConfig {
  target_weights?: Record<string, number>;
  cash_weight?: number;
}

interface PortfolioItem {
  name: string;
  symbols: string[];
  config?: PortfolioConfig;
}

interface StrategyRecord {
  name: string;
  preferences?: {
    scoring_mode?: string;
    backtest_mode?: string;
    optimizer_method?: string;
    rebalance_frequency?: string;
  };
  constraints?: {
    benchmark_symbol?: string;
    max_position_weight?: number;
    min_cash_weight?: number;
    max_drawdown?: number;
    backtest_years?: number;
  };
}

const WORKFLOW_STRATEGY_FROM_OPTIMIZER_METHOD: Record<string, string> = {
  market_cap: "market_cap_weighted",
  risk_parity: "volatility_weighted",
  equal_weight: "equal_weight",
  minimum_variance: "technical_score_weighted",
};

const RECOMMENDATION_ACTION_LABELS: Record<string, string> = {
  research_candidate: "可继续研究",
  reduce_risk_and_retest: "需降低风险并重新测试",
  revise_portfolio: "建议调整组合",
};

const WORKFLOW_STEPS = [
  { id: "step-universe", index: 1, title: "股票池 Universe", copy: "Most Active Top 100 · 选择组合后运行回测" },
  { id: "step-strategy", index: 2, title: "策略库 Strategy Library", copy: "选择仓位分配和测试算法。" },
  { id: "step-constraints", index: 3, title: "配置约束 Constraints", copy: "收益目标、回撤、仓位和现金比例。" },
  { id: "step-backtest", index: 4, title: "运行回测 Backtest", copy: "调用 Backtesting Engine。" },
  { id: "step-ai-analysis", index: 5, title: "AI 自动分析结果", copy: "解释收益、风险和贡献原因。" },
  { id: "step-recommendation", index: 6, title: "Portfolio Recommendation", copy: "生成可复核的组合建议。" },
];

function yearsAgoDate(years: number): string {
  const date = new Date();
  date.setFullYear(date.getFullYear() - years);
  return date.toISOString().slice(0, 10);
}

function todayDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function percentToRatio(value: string): number {
  return Math.max(0, Number(value || 0)) / 100;
}

export default function PortfolioResearch() {
  const [searchParams] = useSearchParams();

  const [portfolios, setPortfolios] = useState<Record<string, string[]>>({});
  const [portfolioConfigs, setPortfolioConfigs] = useState<Record<string, PortfolioConfig>>({});
  const [activeName, setActiveName] = useState("Core Watch");
  const [compareSelection, setCompareSelection] = useState<string[]>([]);
  const [compareStatus, setCompareStatus] = useState<string | null>(null);
  const [compareResult, setCompareResult] = useState<{ a: PortfolioItem & { risk?: RiskReport | null }; b: PortfolioItem & { risk?: RiskReport | null } } | null>(null);
  const [addSymbolInput, setAddSymbolInput] = useState("");
  const importInputRef = useRef<HTMLInputElement | null>(null);
  const importTargetName = useRef<string | null>(null);

  const [appliedStrategyName, setAppliedStrategyName] = useState<string | null>(null);
  const [uxStrategyTouched, setUxStrategyTouched] = useState(false);
  const [uxConstraintsTouched, setUxConstraintsTouched] = useState(false);

  const [workflowStrategy, setWorkflowStrategy] = useState("technical_score_weighted");
  const [targetReturn, setTargetReturn] = useState("12");
  const [maxDrawdown, setMaxDrawdown] = useState("12");
  const [maxPosition, setMaxPosition] = useState("25");
  const [minCash, setMinCash] = useState("10");
  const [backtestYears, setBacktestYears] = useState("3");
  const [initialCash, setInitialCash] = useState("10000");
  const [signalMode, setSignalMode] = useState("technical");
  const [rebalanceFrequency, setRebalanceFrequency] = useState("monthly");
  const [benchmarkSymbol, setBenchmarkSymbol] = useState("SPY");
  const [stopLossPercent, setStopLossPercent] = useState("8");

  const [fieldErrors, setFieldErrors] = useState<string[]>([]);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [workflowTraceNote, setWorkflowTraceNote] = useState<string | null>(null);
  const [stepStates, setStepStates] = useState<Record<string, "pending" | "active" | "done" | "error">>({});
  const [backtestNote, setBacktestNote] = useState("等待回测结果：收益、风险、贡献、原因会在这里展示。");
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [aiSummary, setAiSummary] = useState<AiSummary | null>(null);
  const [recommendation, setRecommendation] = useState<PortfolioRecommendation | null>(null);
  const [riskReport, setRiskReport] = useState<RiskReport | null>(null);
  const [optimizerResult, setOptimizerResult] = useState<OptimizerResult | null>(null);

  const activePortfolioSymbols = useMemo(
    () => [...new Set((portfolios[activeName] || []).map((symbol) => symbol.toUpperCase()))],
    [portfolios, activeName],
  );

  function currentPortfolioConfigPayload() {
    const symbols = activePortfolioSymbols;
    const cashWeight = percentToRatio(minCash);
    const investableWeight = Math.max(0, 1 - cashWeight);
    const equalWeight = symbols.length ? investableWeight / symbols.length : 0;
    return {
      target_weights: Object.fromEntries(symbols.map((symbol) => [symbol, equalWeight])),
      cash_weight: cashWeight,
    };
  }

  const loadPortfolios = useCallback(async () => {
    const data = await request<{ items: PortfolioItem[] }>("/portfolios");
    const nextPortfolios: Record<string, string[]> = {};
    const nextConfigs: Record<string, PortfolioConfig> = {};
    data.items.forEach((portfolio) => {
      nextPortfolios[portfolio.name] = portfolio.symbols;
      nextConfigs[portfolio.name] = portfolio.config || {};
    });
    setPortfolios(nextPortfolios);
    setPortfolioConfigs(nextConfigs);
    setActiveName((current) => (nextPortfolios[current] ? current : Object.keys(nextPortfolios)[0] || current));
  }, []);

  useEffect(() => {
    loadPortfolios();
  }, [loadPortfolios]);

  // Apply a strategy handed off from StrategyLibrary (commit 6) via ?strategy=name[&autorun=1].
  useEffect(() => {
    const strategyName = searchParams.get("strategy");
    if (!strategyName) return;
    (async () => {
      const data = await request<{ items: StrategyRecord[] }>("/strategies");
      const strategy = data.items.find((item) => item.name === strategyName);
      if (!strategy) return;
      applyStrategy(strategy);
      if (searchParams.get("autorun") === "1") {
        setBacktestNote(`正在基于「${strategyName}」生成 Research Portfolio：优化权重、回测、风险和建议。本结果仅用于投资研究辅助，不构成任何投资建议。`);
        window.setTimeout(() => runPortfolioWorkflow(), 0);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // Open a completed Research Run handed off from Reports.tsx via ?trace=<trace_id>.
  useEffect(() => {
    const trace = searchParams.get("trace");
    if (trace) loadResearchRunDetail(trace);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  function applyStrategy(strategy: StrategyRecord) {
    const prefs = strategy.preferences || {};
    const constraints = strategy.constraints || {};
    setWorkflowStrategy(WORKFLOW_STRATEGY_FROM_OPTIMIZER_METHOD[prefs.optimizer_method || ""] || "technical_score_weighted");
    setSignalMode(prefs.backtest_mode === "ai_score" ? "ai_score" : "technical");
    setRebalanceFrequency(prefs.rebalance_frequency || "monthly");
    if (constraints.benchmark_symbol) setBenchmarkSymbol(constraints.benchmark_symbol);
    if (constraints.max_position_weight != null) setMaxPosition(String(Math.round(constraints.max_position_weight * 100)));
    if (constraints.min_cash_weight != null) setMinCash(String(Math.round(constraints.min_cash_weight * 100)));
    if (constraints.max_drawdown != null) setMaxDrawdown(String(Math.round(constraints.max_drawdown * 100)));
    if (constraints.backtest_years != null) setBacktestYears(String(constraints.backtest_years));
    setUxStrategyTouched(true);
    setUxConstraintsTouched(true);
    setAppliedStrategyName(strategy.name);
  }

  // --- Portfolio CRUD -------------------------------------------------------

  async function addSymbolToPortfolio() {
    const symbol = addSymbolInput.trim().toUpperCase();
    if (!symbol) return;
    try {
      const portfolio = await postJson<PortfolioItem>(`/portfolios/${encodeURIComponent(activeName)}/symbols`, { symbol });
      setPortfolios((prev) => ({ ...prev, [activeName]: portfolio.symbols }));
      setPortfolioConfigs((prev) => ({ ...prev, [activeName]: portfolio.config || {} }));
      setAddSymbolInput("");
    } catch (error) {
      window.alert(`加入组合失败：${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async function removeSymbolFromPortfolio(strategy: string, symbol: string) {
    try {
      const portfolio = await deleteJson<PortfolioItem>(`/portfolios/${encodeURIComponent(strategy)}/symbols/${encodeURIComponent(symbol)}`);
      setPortfolios((prev) => ({ ...prev, [strategy]: portfolio.symbols }));
      setPortfolioConfigs((prev) => ({ ...prev, [strategy]: portfolio.config || {} }));
    } catch (error) {
      window.alert(`移除股票失败：${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async function saveActivePortfolioConfig() {
    if (!activePortfolioSymbols.length) {
      window.alert("当前组合没有股票，无法保存权重。");
      return;
    }
    try {
      const portfolio = await putJson<PortfolioItem>(`/portfolios/${encodeURIComponent(activeName)}/config`, currentPortfolioConfigPayload());
      setPortfolioConfigs((prev) => ({ ...prev, [portfolio.name]: portfolio.config || {} }));
    } catch (error) {
      window.alert(`保存组合配置失败：${error instanceof Error ? error.message : String(error)}`);
    }
  }

  function togglePortfolioCompareSelection(name: string, checked: boolean) {
    if (checked && compareSelection.length >= 2 && !compareSelection.includes(name)) {
      window.alert("最多同时对比 2 个组合，请先取消一个已选组合。");
      return;
    }
    setCompareSelection((prev) => (checked ? [...new Set([...prev, name])] : prev.filter((item) => item !== name)));
  }

  function portfolioExportPayload(name: string) {
    const config = portfolioConfigs[name] || {};
    return {
      name,
      symbols: portfolios[name] || [],
      target_weights: config.target_weights || {},
      cash_weight: config.cash_weight || 0,
    };
  }

  function exportPortfolio(name: string, format: "json" | "csv") {
    const payload = portfolioExportPayload(name);
    if (format === "json") {
      downloadTextFile(`${name}.json`, JSON.stringify(payload, null, 2), "application/json");
      return;
    }
    const rows = ["symbol,weight"];
    payload.symbols.forEach((symbol) => {
      rows.push(`${symbol},${payload.target_weights[symbol] || 0}`);
    });
    rows.push(`CASH,${payload.cash_weight}`);
    downloadTextFile(`${name}.csv`, rows.join("\n"), "text/csv");
  }

  function openPortfolioImport(name: string) {
    importTargetName.current = name;
    if (importInputRef.current) {
      importInputRef.current.value = "";
      importInputRef.current.click();
    }
  }

  function parsePortfolioImportText(text: string) {
    const trimmed = text.trim();
    if (trimmed.startsWith("{")) {
      const data = JSON.parse(trimmed);
      return {
        symbols: (data.symbols || Object.keys(data.target_weights || {})).map((symbol: string) => symbol.toUpperCase()),
        target_weights: data.target_weights || {},
        cash_weight: data.cash_weight || 0,
      };
    }
    const symbols: string[] = [];
    const targetWeights: Record<string, number> = {};
    let cashWeight = 0;
    trimmed.split("\n").slice(1).forEach((line) => {
      const [rawSymbol, rawWeight] = line.split(",");
      if (!rawSymbol) return;
      const symbol = rawSymbol.trim().toUpperCase();
      const weight = Number(rawWeight) || 0;
      if (symbol === "CASH") {
        cashWeight = weight;
        return;
      }
      symbols.push(symbol);
      targetWeights[symbol] = weight;
    });
    return { symbols, target_weights: targetWeights, cash_weight: cashWeight };
  }

  async function importPortfolioFromData(name: string, data: { symbols: string[]; target_weights: Record<string, number>; cash_weight: number }) {
    const desired = [...new Set(data.symbols)];
    const current = portfolios[name] || [];
    for (const symbol of current.filter((item) => !desired.includes(item))) {
      await deleteJson(`/portfolios/${encodeURIComponent(name)}/symbols/${encodeURIComponent(symbol)}`);
    }
    for (const symbol of desired.filter((item) => !current.includes(item))) {
      await postJson(`/portfolios/${encodeURIComponent(name)}/symbols`, { symbol });
    }
    await putJson(`/portfolios/${encodeURIComponent(name)}/config`, {
      target_weights: data.target_weights,
      cash_weight: data.cash_weight,
    });
  }

  async function onImportFileChange() {
    const file = importInputRef.current?.files?.[0];
    const name = importTargetName.current;
    if (!file || !name) return;
    try {
      const text = await file.text();
      const data = parsePortfolioImportText(text);
      await importPortfolioFromData(name, data);
      await loadPortfolios();
      window.alert(`已导入到组合「${name}」。`);
    } catch (error) {
      window.alert(`导入失败：${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async function fetchPortfolioRiskFor(name: string): Promise<PortfolioItem & { risk?: RiskReport | null }> {
    const symbols = [...new Set((portfolios[name] || []).map((symbol) => symbol.toUpperCase()))];
    if (symbols.length < 2) return { name, symbols, risk: null };
    const config = portfolioConfigs[name] || {};
    const risk = (await postJson("/risk/portfolio", {
      symbols,
      weights: config.target_weights || {},
      benchmark_symbol: benchmarkSymbol.trim().toUpperCase() || "SPY",
      sector_map: {},
    })) as RiskReport;
    return { name, symbols, config, risk };
  }

  function renderPortfolioCompareResult(a: PortfolioItem & { risk?: RiskReport | null }, b: PortfolioItem & { risk?: RiskReport | null }) {
    setCompareResult({ a, b });
  }

  async function runPortfolioCompare() {
    if (compareSelection.length !== 2) return;
    setCompareStatus("正在计算组合对比...");
    setCompareResult(null);
    try {
      const [a, b] = await Promise.all(compareSelection.map(fetchPortfolioRiskFor));
      if (!a.risk || !b.risk) {
        setCompareStatus("两个组合都至少需要 2 只股票才能计算风险对比。");
        return;
      }
      renderPortfolioCompareResult(a, b);
      setCompareStatus("本系统仅用于投资研究辅助，不构成任何投资建议。");
    } catch (error) {
      setCompareStatus(`组合对比失败：${error instanceof Error ? error.message : String(error)}`);
    }
  }

  // --- Workflow steps --------------------------------------------------------

  function setWorkflowStepStates(doneCount: number, activeIndex: number) {
    const next: Record<string, "pending" | "active" | "done" | "error"> = {};
    WORKFLOW_STEPS.forEach((step, index) => {
      next[step.id] = index === activeIndex ? "active" : index < doneCount ? "done" : "pending";
    });
    setStepStates(next);
  }

  function updateWorkflowSteps(stage?: "running") {
    if (stage === "running") {
      setWorkflowStepStates(3, 3);
      return;
    }
    const portfolioReady = activePortfolioSymbols.length >= 2;
    let doneCount = 0;
    if (portfolioReady) doneCount = 1;
    if (portfolioReady && uxStrategyTouched) doneCount = 2;
    if (portfolioReady && uxStrategyTouched && uxConstraintsTouched) doneCount = 3;
    setWorkflowStepStates(doneCount, portfolioReady ? -1 : 0);
  }

  useEffect(() => {
    updateWorkflowSteps();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePortfolioSymbols, uxStrategyTouched, uxConstraintsTouched]);

  const NODE_TO_STEP: Record<string, string> = {
    "Universe Builder": "step-universe",
    "Portfolio Builder": "step-universe",
    "Strategy Selector": "step-strategy",
    "Constraint Config": "step-constraints",
    "Backtest Runner": "step-backtest",
    "AI Summary": "step-ai-analysis",
    "Portfolio Recommendation": "step-recommendation",
  };

  function renderWorkflowNodeSteps(nodeResults: Array<{ name: string; state: string }>) {
    const completed = new Set<string>();
    let failedStep: string | null = null;
    (nodeResults || []).forEach((node) => {
      const stepId = NODE_TO_STEP[node.name];
      if (!stepId) return;
      if (node.state === "Failed") failedStep = stepId;
      else completed.add(stepId);
    });
    const next: Record<string, "pending" | "active" | "done" | "error"> = {};
    WORKFLOW_STEPS.forEach((step) => {
      next[step.id] = step.id === failedStep ? "error" : completed.has(step.id) ? "done" : "pending";
    });
    setStepStates(next);
  }

  // --- Payload builders --------------------------------------------------------

  // ponytail: ported verbatim from the legacy app but unused there too (grep confirms
  // buildWorkflowPayload/renderWorkflowResult/friendlyWorkflowError are dead code in
  // apps/web/index.html — runPortfolioWorkflow always used buildPortfolioResearchPayload +
  // POST /portfolio-research/run instead). Kept for parity, not wired to any button.
  function buildWorkflowPayload() {
    const symbols = activePortfolioSymbols;
    const years = Number(backtestYears || 3);
    return {
      portfolio_name: activeName,
      universe_limit: 100,
      backtest: {
        strategy_name: `${activeName} · ${workflowStrategy}`,
        symbols,
        start_date: yearsAgoDate(years),
        end_date: todayDate(),
        initial_cash: Number(initialCash || 10000),
        rebalance_frequency: rebalanceFrequency,
        benchmark_symbol: benchmarkSymbol.trim().toUpperCase() || "SPY",
        signal_mode: signalMode,
        allocation: {
          method: workflowStrategy,
          max_position_weight: percentToRatio(maxPosition),
          min_cash_weight: percentToRatio(minCash),
        },
        entry_rules: {
          min_technical_score: workflowStrategy === "equal_weight" ? 50 : 60,
          min_momentum_percent: workflowStrategy === "technical_score_weighted" ? 0 : null,
          require_ma_cross: null,
        },
        exit_rules: {
          max_technical_score: 40,
          stop_loss_percent: percentToRatio(stopLossPercent),
          require_ma_cross: null,
        },
        risk: {
          max_portfolio_drawdown: percentToRatio(maxDrawdown),
          max_sector_exposure: null,
        },
        sector_map: {},
      },
    };
  }

  function optimizerMethod(): string {
    if (workflowStrategy === "market_cap_weighted") return "market_cap";
    if (workflowStrategy === "volatility_weighted") return "risk_parity";
    if (workflowStrategy === "equal_weight") return "equal_weight";
    return "minimum_variance";
  }

  function buildPortfolioResearchPayload() {
    return {
      portfolio_name: activeName,
      symbols: activePortfolioSymbols,
      research_goal: "balanced_growth",
      strategy_library_name: appliedStrategyName || null,
      constraints: {
        max_position_weight: percentToRatio(maxPosition),
        min_cash_weight: percentToRatio(minCash),
        max_drawdown: percentToRatio(maxDrawdown),
        benchmark_symbol: benchmarkSymbol.trim().toUpperCase() || "SPY",
        backtest_years: Number(backtestYears || 3),
      },
      strategy_preferences: {
        scoring_mode: "algorithm_v0.3",
        backtest_mode: signalMode === "ai_score" ? "ai_score" : "technical",
        optimizer_method: optimizerMethod(),
        rebalance_frequency: rebalanceFrequency,
      },
    };
  }

  function targetReturnStatus(result: BacktestResult): string {
    const target = Number(targetReturn || 0);
    const annualized = Number(result.annualized_return_percent || 0);
    return annualized >= target
      ? `达到年化收益目标 ${target.toFixed(0)}%。`
      : `未达到年化收益目标 ${target.toFixed(0)}%，需要继续调低风险或调整股票池。`;
  }

  function validateBacktestForm(): string[] {
    const fields: Array<[string, string, number | null, number | null]> = [
      [targetReturn, "收益目标", -50, 100],
      [maxDrawdown, "最大回撤", 1, 80],
      [maxPosition, "单票仓位", 1, 100],
      [minCash, "现金比例", 0, 80],
      [initialCash, "初始资金", 1000, 10000000],
      [stopLossPercent, "止损 %", 1, 50],
    ];
    const errors: string[] = [];
    fields.forEach(([value, label, min, max]) => {
      const number = Number(value);
      if (Number.isNaN(number) || (min !== null && number < min) || (max !== null && number > max)) {
        errors.push(`${label} 需在 ${min ?? "--"} 到 ${max ?? "--"} 之间`);
      }
    });
    if (!benchmarkSymbol.trim()) errors.push("基准代码不能为空");
    return errors;
  }

  // --- Result renderers --------------------------------------------------------

  function renderBacktestResult(result: BacktestResult) {
    setBacktestResult(result);
  }

  function renderAiSummary(summary: AiSummary | null) {
    setAiSummary(summary);
  }

  function renderPortfolioRecommendation(rec: PortfolioRecommendation | null) {
    setRecommendation(rec);
  }

  function renderRiskReport(report: RiskReport | null) {
    setRiskReport(report);
  }

  function renderOptimizerResult(result: OptimizerResult | null) {
    setOptimizerResult(result);
  }

  // ponytail: ported verbatim from the legacy app but, like buildWorkflowPayload above, unused
  // there too — nothing calls the raw POST /workflows/portfolio-research path; kept for parity.
  function renderWorkflowResult(result: { node_results?: Array<{ name: string; state: string }>; trace_id: string; state: string; backtest?: BacktestResult; ai_summary?: AiSummary; portfolio_recommendation?: PortfolioRecommendation }) {
    renderWorkflowNodeSteps(result.node_results || []);
    setWorkflowTraceNote(`Trace ID: ${result.trace_id} · 可通过 GET /portfolio-research/${result.trace_id} 复盘本次 workflow。`);
    if (result.state === "Failed") {
      setBacktestNote(friendlyWorkflowError(result));
      setBacktestResult(null);
      renderAiSummary(null);
      renderPortfolioRecommendation(null);
      return;
    }
    if (result.backtest) renderBacktestResult(result.backtest);
    renderAiSummary(result.ai_summary || null);
    renderPortfolioRecommendation(result.portfolio_recommendation || null);
  }

  function renderPortfolioResearchResult(result: PortfolioResearchResult) {
    const workflowResponse = result.workflow?.response || {};
    renderWorkflowNodeSteps(result.workflow?.node_results || []);
    setWorkflowTraceNote(`Trace ID: ${result.trace_id} · 可通过 GET /portfolio-research/${result.trace_id} 复盘本次完整研究。`);
    if (result.state === "failed") {
      setBacktestNote("Portfolio Research 执行失败，请检查数据源或约束后重试。");
      setBacktestResult(null);
      renderAiSummary(null);
      renderPortfolioRecommendation(null);
      renderRiskReport(null);
      renderOptimizerResult(null);
      return;
    }
    const backtest = workflowResponse.backtest || result.backtest_summary;
    if (backtest) renderBacktestResult(backtest);
    renderAiSummary(result.ai_explanation || null);
    renderPortfolioRecommendation(result.recommendation || null);
    renderRiskReport(result.risk_summary || null);
    renderOptimizerResult(result.optimized_weights || null);
  }

  async function loadResearchRunDetail(traceId: string) {
    if (!traceId) return;
    setWorkflowTraceNote(`正在复盘 trace_id ${traceId}...`);
    try {
      const result = await request<PortfolioResearchResult>(`/portfolio-research/${encodeURIComponent(traceId)}`);
      renderPortfolioResearchResult(result);
    } catch (error) {
      setWorkflowTraceNote(friendlyBacktestError(error));
    }
  }

  async function runPortfolioWorkflow() {
    const symbols = activePortfolioSymbols;
    if (symbols.length < 2) {
      setBacktestNote("请先在当前组合中至少加入 2 只股票，再运行回测。");
      return;
    }
    const errors = validateBacktestForm();
    setFieldErrors(errors);
    if (errors.length) return;

    setBacktestLoading(true);
    updateWorkflowSteps("running");
    setWorkflowTraceNote(null);
    setBacktestNote("正在运行 Portfolio Research：评分 → 回测 → 风险 → 优化 → 解释 → 建议...");
    setBacktestResult(null);
    try {
      const result = await postJson("/portfolio-research/run", buildPortfolioResearchPayload()) as PortfolioResearchResult;
      renderPortfolioResearchResult(result);
    } catch (error) {
      setBacktestNote(friendlyBacktestError(error));
      renderWorkflowNodeSteps([]);
    } finally {
      setBacktestLoading(false);
    }
  }

  async function loadRiskReport() {
    if (activePortfolioSymbols.length < 2) {
      renderRiskReport(null);
      return;
    }
    const report = (await postJson("/risk/portfolio", {
      symbols: activePortfolioSymbols,
      weights: currentPortfolioConfigPayload().target_weights,
      benchmark_symbol: benchmarkSymbol.trim().toUpperCase() || "SPY",
      sector_map: {},
    })) as RiskReport;
    renderRiskReport(report);
  }

  async function loadOptimizerResult() {
    if (activePortfolioSymbols.length < 2) {
      renderOptimizerResult(null);
      return;
    }
    const result = (await postJson("/optimizer/portfolio", {
      symbols: activePortfolioSymbols,
      method: optimizerMethod(),
      max_position_weight: percentToRatio(maxPosition),
      min_cash_weight: percentToRatio(minCash),
    })) as OptimizerResult;
    renderOptimizerResult(result);
  }

  // ponytail: these four are ported verbatim from the legacy app where they were dead code too
  // (buildWorkflowPayload/renderWorkflowResult/loadRiskReport/loadOptimizerResult are never called
  // in apps/web/index.html either) — referenced here only to satisfy noUnusedLocals, not wired to
  // any button. See the ponytail comments above each definition for why they're kept anyway.
  void buildWorkflowPayload;
  void renderWorkflowResult;
  void loadRiskReport;
  void loadOptimizerResult;

  const portfolioNames = Object.keys(portfolios);

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Portfolio Research</div>
          <div className="muted">6 步流程：Universe → Strategy → Constraints → Backtest → AI Analysis → Recommendation。</div>
        </div>
      </div>

      <input type="file" id="portfolio-import-input" ref={importInputRef} accept=".json,.csv" hidden onChange={onImportFileChange} />

      <div className="portfolio-panel">
        <div className="section-title">我的组合 Portfolios</div>
        <div className="portfolio-controls">
          <select id="portfolio-strategy" value={activeName} onChange={(e) => setActiveName(e.target.value)}>
            {[...new Set(["Core Watch", "Momentum", "AI Theme", "Semiconductor", "Risk Hedge", ...portfolioNames])].map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
          <button type="button" onClick={loadPortfolios}>刷新组合</button>
        </div>
        <div className="portfolio-controls">
          <input placeholder="加入股票代码，如 AAPL" value={addSymbolInput} onChange={(e) => setAddSymbolInput(e.target.value.toUpperCase())} />
          <button type="button" onClick={addSymbolToPortfolio}>加入到「{activeName}」</button>
        </div>
        <div className="report-archive-actions">
          <button id="portfolio-compare-button" type="button" disabled={compareSelection.length !== 2} onClick={runPortfolioCompare}>
            对比选中 ({compareSelection.length}/2)
          </button>
        </div>
        <div className="portfolio-list">
          {portfolioNames.map((name) => {
            const symbols = portfolios[name] || [];
            const config = portfolioConfigs[name] || {};
            const savedWeights = config.target_weights || {};
            const savedWeightText = Object.keys(savedWeights).length
              ? Object.entries(savedWeights).map(([symbol, weight]) => `${symbol} ${(weight * 100).toFixed(0)}%`).join(" · ")
              : "未保存目标权重";
            return (
              <div className="portfolio-group" key={name}>
                <div className="portfolio-group-head">
                  <label>
                    <input
                      type="checkbox"
                      className="portfolio-compare-check"
                      checked={compareSelection.includes(name)}
                      onChange={(e) => togglePortfolioCompareSelection(name, e.target.checked)}
                    />{" "}
                    {escapeHtml(name)}
                  </label>
                  <span className="muted">{symbols.length} stocks</span>
                </div>
                <div className="portfolio-symbols">
                  {symbols.length ? (
                    symbols.map((symbol) => (
                      <span className="portfolio-chip" key={symbol}>
                        {escapeHtml(symbol)}
                        <button type="button" onClick={() => removeSymbolFromPortfolio(name, symbol)}>×</button>
                      </span>
                    ))
                  ) : (
                    <span className="muted">未选择股票</span>
                  )}
                </div>
                <div className="muted">Cash {formatPercent((config.cash_weight || 0) * 100)} · {escapeHtml(savedWeightText)}</div>
                <div className="report-archive-actions">
                  <button type="button" onClick={() => exportPortfolio(name, "json")}>导出 JSON</button>
                  <button type="button" onClick={() => exportPortfolio(name, "csv")}>导出 CSV</button>
                  <button type="button" onClick={() => openPortfolioImport(name)}>导入</button>
                </div>
              </div>
            );
          })}
        </div>
        {compareStatus && <div className="workflow-note">{compareStatus}</div>}
        {compareResult && <PortfolioCompareResult a={compareResult.a} b={compareResult.b} />}
      </div>

      <section className="workflow-panel">
        <div className="project-head">
          <div>
            <div className="project-title">Portfolio Research Workbench</div>
            <div className="muted">选择组合和目标约束，一次性完成评分、回测、风险、优化和建议。</div>
          </div>
          <span className="status-pill">Portfolio Research v0.1</span>
        </div>

        <div className="workflow-steps">
          {WORKFLOW_STEPS.map((step) => (
            <div className="workflow-step" id={step.id} key={step.id} data-step-state={stepStates[step.id] || "pending"}>
              <span className="step-index">{step.index}</span>
              <div>
                <div className="step-title">{step.title}</div>
                <div className="step-copy" id={step.id === "step-universe" ? "workflow-universe-summary" : undefined}>{step.copy}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="strategy-workbench-grid">
          <div className="strategy-config-panel">
            <div className="strategy-panel-head">
              <div>
                <div className="strategy-panel-title">策略与约束</div>
                <div className="strategy-panel-subtitle" id="backtest-selection-summary">当前组合：{activeName} · {activePortfolioSymbols.length} stocks</div>
              </div>
            </div>

            <div className="strategy-grid">
              <div className="strategy-field">
                <label htmlFor="workflow-strategy">策略类型</label>
                <select
                  id="workflow-strategy"
                  value={workflowStrategy}
                  onChange={(e) => {
                    setWorkflowStrategy(e.target.value);
                    setUxStrategyTouched(true);
                  }}
                >
                  <option value="technical_score_weighted">技术评分加权</option>
                  <option value="equal_weight">等权组合</option>
                  <option value="volatility_weighted">低波动加权</option>
                  <option value="market_cap_weighted">市值加权</option>
                </select>
              </div>
            </div>

            <div className="constraint-grid">
              <div className="constraint-field">
                <label htmlFor="target-return">收益目标 %</label>
                <input id="target-return" type="number" min={-50} max={100} step={1} value={targetReturn} onChange={(e) => { setTargetReturn(e.target.value); setUxConstraintsTouched(true); }} />
              </div>
              <div className="constraint-field">
                <label htmlFor="max-drawdown">最大回撤 %</label>
                <input id="max-drawdown" type="number" min={1} max={80} step={1} value={maxDrawdown} onChange={(e) => { setMaxDrawdown(e.target.value); setUxConstraintsTouched(true); }} />
              </div>
              <div className="constraint-field">
                <label htmlFor="max-position">单票仓位 %</label>
                <input id="max-position" type="number" min={1} max={100} step={1} value={maxPosition} onChange={(e) => { setMaxPosition(e.target.value); setUxConstraintsTouched(true); }} />
              </div>
              <div className="constraint-field">
                <label htmlFor="min-cash">现金比例 %</label>
                <input id="min-cash" type="number" min={0} max={80} step={1} value={minCash} onChange={(e) => { setMinCash(e.target.value); setUxConstraintsTouched(true); }} />
              </div>
              <div className="constraint-field">
                <label htmlFor="backtest-years">回测年限</label>
                <select id="backtest-years" value={backtestYears} onChange={(e) => { setBacktestYears(e.target.value); setUxConstraintsTouched(true); }}>
                  <option value="1">1 年</option>
                  <option value="3">3 年</option>
                  <option value="5">5 年</option>
                </select>
              </div>
              <div className="constraint-field">
                <label htmlFor="initial-cash">初始资金</label>
                <input id="initial-cash" type="number" min={1000} max={10000000} step={1000} value={initialCash} onChange={(e) => { setInitialCash(e.target.value); setUxConstraintsTouched(true); }} />
              </div>
            </div>

            <details className="advanced-settings" id="advanced-settings">
              <summary>高级设置 Advanced</summary>
              <div className="advanced-grid">
                <div className="constraint-field">
                  <label htmlFor="signal-mode">信号模式</label>
                  <select id="signal-mode" value={signalMode} onChange={(e) => setSignalMode(e.target.value)}>
                    <option value="technical">Technical（技术信号）</option>
                    <option value="ai_score">AI Score（五因子综合评分）</option>
                  </select>
                </div>
                <div className="constraint-field">
                  <label htmlFor="rebalance-frequency">再平衡频率</label>
                  <select id="rebalance-frequency" value={rebalanceFrequency} onChange={(e) => setRebalanceFrequency(e.target.value)}>
                    <option value="weekly">每周</option>
                    <option value="monthly">每月</option>
                    <option value="quarterly">每季度</option>
                  </select>
                </div>
                <div className="constraint-field">
                  <label htmlFor="benchmark-symbol">基准代码</label>
                  <input id="benchmark-symbol" type="text" maxLength={10} value={benchmarkSymbol} onChange={(e) => setBenchmarkSymbol(e.target.value)} />
                </div>
                <div className="constraint-field">
                  <label htmlFor="stop-loss-percent">止损 %</label>
                  <input id="stop-loss-percent" type="number" min={1} max={50} step={1} value={stopLossPercent} onChange={(e) => setStopLossPercent(e.target.value)} />
                </div>
              </div>
            </details>

            {fieldErrors.length > 0 && (
              <div className="field-errors" id="field-errors">
                <ul>
                  {fieldErrors.map((message, index) => (
                    <li key={index}>{escapeHtml(message)}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="workflow-actions">
              <div className="workflow-note">算法测试仅使用历史价格和技术信号，后续可接入财报、估值和新闻情绪。</div>
              <button className="run-backtest-button" id="save-portfolio-config-button" type="button" onClick={saveActivePortfolioConfig}>Save Weights</button>
              <button className="run-backtest-button" id="run-backtest-button" type="button" disabled={backtestLoading} onClick={runPortfolioWorkflow}>
                {backtestLoading && <span className="spinner" id="run-backtest-spinner" />}
                <span id="run-backtest-button-label">{backtestLoading ? "Running..." : "Run Research"}</span>
              </button>
            </div>
          </div>

          <div className="strategy-result-panel">
            <div className="strategy-panel-head">
              <div>
                <div className="strategy-panel-title">策略推荐组合与验证</div>
                <div className="strategy-panel-subtitle">先看推荐权重和组合建议，再核对回测、风险、交易和 AI 解释。</div>
              </div>
            </div>
            <div className="result-priority-grid">
              {optimizerResult && (
                <div className="card chart-card" id="optimizer-card">
                  <div className="strategy-panel-title">Recommended Research Portfolio</div>
                  <div className="strategy-panel-subtitle">Portfolio Optimizer v0.1 · 该策略下的研究型权重建议，不构成投资建议。</div>
                  <div className="result-grid" id="optimizer-grid">
                    <div className="result-card"><div className="result-label">Method</div><div className="result-value">{escapeHtml(optimizerResult.method)}</div></div>
                    <div className="result-card"><div className="result-label">Cash</div><div className="result-value">{formatPercent(optimizerResult.cash_weight * 100)}</div></div>
                    <div className="result-card"><div className="result-label">Expected Risk</div><div className="result-value">{formatPercent(optimizerResult.expected_risk_percent)}</div></div>
                  </div>
                  <div className="weight-grid" id="optimizer-weight-grid">
                    {Object.entries(optimizerResult.target_weights || {}).sort(([, a], [, b]) => Number(b || 0) - Number(a || 0)).map(([symbol, weight]) => (
                      <div className="weight-chip" key={symbol}>
                        <div className="weight-chip-symbol">{escapeHtml(symbol)}</div>
                        <div className="weight-chip-value">{formatPercent(Number(weight || 0) * 100)}</div>
                      </div>
                    ))}
                  </div>
                  <ul className="workflow-list" id="optimizer-notes">
                    {(optimizerResult.notes || []).map((item, index) => <li key={index}>{escapeHtml(item)}</li>)}
                  </ul>
                </div>
              )}
              {recommendation && (
                <div className="card chart-card" id="recommendation-card">
                  <div className="strategy-panel-title">Portfolio Recommendation</div>
                  <div className="result-grid" id="recommendation-action-grid">
                    <div className="result-card">
                      <div className="result-label">建议动作</div>
                      <div className="result-value">{escapeHtml(RECOMMENDATION_ACTION_LABELS[recommendation.action] || recommendation.action)}</div>
                    </div>
                  </div>
                  <ul className="workflow-list" id="recommendation-reasons">{(recommendation.reasons || []).map((r, i) => <li key={i}>{escapeHtml(r)}</li>)}</ul>
                  <ul className="workflow-list" id="recommendation-suggestions">{(recommendation.suggestions || []).map((s, i) => <li key={i}>{escapeHtml(s)}</li>)}</ul>
                  <ul className="workflow-list" id="recommendation-risks">{(recommendation.risks || []).map((r, i) => <li key={i}>{escapeHtml(r)}</li>)}</ul>
                  <div className="workflow-note" id="recommendation-disclaimer">{recommendation.risk_disclaimer || ""}</div>
                </div>
              )}
              {riskReport && (
                <div className="card chart-card" id="risk-report-card">
                  <div className="strategy-panel-title">Risk Engine v0.1</div>
                  <div className="result-grid" id="risk-report-grid">
                    <div className="result-card"><div className="result-label">Volatility</div><div className="result-value">{formatPercent(riskReport.volatility_percent)}</div></div>
                    <div className="result-card"><div className="result-label">Beta</div><div className="result-value">{riskReport.beta === null || riskReport.beta === undefined ? "--" : Number(riskReport.beta).toFixed(2)}</div></div>
                    <div className="result-card"><div className="result-label">Max Drawdown</div><div className="result-value">{formatPercent(riskReport.max_drawdown_percent)}</div></div>
                    <div className="result-card"><div className="result-label">Concentration</div><div className="result-value">{formatPercent(riskReport.concentration_percent)}</div></div>
                  </div>
                  <div className="workflow-note" id="risk-report-note">
                    Average correlation {riskReport.average_correlation ?? "--"} · {Object.entries(riskReport.sector_exposure || {}).map(([sector, weight]) => `${sector} ${formatPercent(weight)}`).join(" · ") || "No sector map"} · {riskReport.risk_disclaimer}
                  </div>
                </div>
              )}
            </div>

            <div className="backtest-results" id="backtest-results">
              {backtestResult ? (
                <>
                  <div className="result-grid">
                    {[
                      ["Total Return", formatPercent(backtestResult.total_return_percent)],
                      ["Annualized", formatPercent(backtestResult.annualized_return_percent)],
                      ["Max Drawdown", formatPercent(backtestResult.max_drawdown_percent)],
                      ["Sharpe", backtestResult.sharpe_ratio === null || backtestResult.sharpe_ratio === undefined ? "--" : Number(backtestResult.sharpe_ratio).toFixed(2)],
                      ["Alpha vs SPY", formatPercent(backtestResult.alpha_percent)],
                      ["Trades", String((backtestResult.trades || []).length)],
                    ].map(([label, value]) => (
                      <div className="result-card" key={label}>
                        <div className="result-label">{label}</div>
                        <div className="result-value">{value}</div>
                      </div>
                    ))}
                  </div>
                  <ul className="workflow-list">
                    <li>{targetReturnStatus(backtestResult)}</li>
                    <li>最佳贡献：{escapeHtml(backtestResult.best_contributor || "--")}；最大拖累：{escapeHtml(backtestResult.worst_contributor || "--")}。</li>
                    <li>数据来源：{escapeHtml(backtestResult.source)}；算法版本：{escapeHtml(backtestResult.algorithm_version)}。</li>
                  </ul>
                  <ul className="workflow-list">
                    {(backtestResult.suggestions || []).slice(0, 3).map((item, i) => <li key={`s${i}`}>{escapeHtml(item)}</li>)}
                    {(backtestResult.risks || []).slice(0, 3).map((item, i) => <li key={`r${i}`}>{escapeHtml(item)}</li>)}
                  </ul>
                </>
              ) : (
                <div className="workflow-note">{backtestNote}</div>
              )}
            </div>
            {workflowTraceNote && <div className="workflow-note" id="workflow-trace-note">{workflowTraceNote}</div>}

            {backtestResult && <EquityCurveChart equityCurve={(backtestResult.equity_curve || []) as EquityCurvePoint[]} />}
            {backtestResult && (backtestResult.trades || []).length > 0 && (
              <div className="trades-table-wrap" id="trades-table-wrap">
                <table className="trades-table" id="trades-table">
                  <thead><tr><th>日期</th><th>代码</th><th>操作</th><th>价格</th><th>股数</th><th>原因</th></tr></thead>
                  <tbody id="trades-table-body">
                    {(backtestResult.trades || []).map((trade, index) => (
                      <tr key={index}>
                        <td>{escapeHtml(trade.date)}</td>
                        <td>{escapeHtml(trade.symbol)}</td>
                        <td>{escapeHtml(trade.action)}</td>
                        <td>{escapeHtml(fmt(trade.price))}</td>
                        <td>{escapeHtml(fmt(trade.shares))}</td>
                        <td>{escapeHtml(trade.reason)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {aiSummary && (
              <div className="card chart-card" id="ai-summary-card">
                <div className="strategy-panel-title">AI 自动分析结果（模板生成，非实时 AI 推理）</div>
                <div className="workflow-note" id="ai-summary-conclusion">{aiSummary.conclusion}</div>
                <ul className="workflow-list" id="ai-summary-findings">
                  {(aiSummary.key_findings || []).map((item, index) => <li key={index}>{escapeHtml(item)}</li>)}
                </ul>
              </div>
            )}
            <div className="workflow-note">本系统仅用于投资研究辅助，不构成任何投资建议。</div>
          </div>
        </div>
      </section>
    </div>
  );
}

interface BacktestResult {
  total_return_percent?: number;
  annualized_return_percent?: number;
  max_drawdown_percent?: number;
  sharpe_ratio?: number | null;
  alpha_percent?: number;
  best_contributor?: string;
  worst_contributor?: string;
  source?: string;
  algorithm_version?: string;
  suggestions?: string[];
  risks?: string[];
  trades?: Array<{ date: string; symbol: string; action: string; price: number; shares: number; reason: string }>;
  equity_curve?: EquityCurvePoint[];
}

interface AiSummary {
  conclusion: string;
  key_findings?: string[];
}

interface PortfolioRecommendation {
  action: string;
  reasons?: string[];
  suggestions?: string[];
  risks?: string[];
  risk_disclaimer?: string;
}

interface RiskReport {
  volatility_percent?: number;
  beta?: number | null;
  max_drawdown_percent?: number;
  concentration_percent?: number;
  average_correlation?: number | null;
  sector_exposure?: Record<string, number>;
  risk_disclaimer?: string;
}

interface OptimizerResult {
  method: string;
  cash_weight: number;
  expected_risk_percent?: number;
  target_weights?: Record<string, number>;
  notes?: string[];
}

interface PortfolioResearchResult {
  trace_id: string;
  state: string;
  workflow?: { response?: { backtest?: BacktestResult }; node_results?: Array<{ name: string; state: string }> };
  backtest_summary?: BacktestResult;
  ai_explanation?: AiSummary | null;
  recommendation?: PortfolioRecommendation | null;
  risk_summary?: RiskReport | null;
  optimized_weights?: OptimizerResult | null;
}

function PortfolioCompareResult({ a, b }: { a: PortfolioItem & { risk?: RiskReport | null }; b: PortfolioItem & { risk?: RiskReport | null } }) {
  const symbols = [...new Set([...(a.symbols || []), ...(b.symbols || [])])].sort();
  const riskMetrics: Array<[string, keyof RiskReport, (value: number | null | undefined) => string]> = [
    ["Volatility", "volatility_percent", formatPercent],
    ["Beta", "beta", (v) => formatRatio(v)],
    ["Max Drawdown", "max_drawdown_percent", formatPercent],
    ["Concentration", "concentration_percent", formatPercent],
  ];
  const sectors = [...new Set([...Object.keys(a.risk?.sector_exposure || {}), ...Object.keys(b.risk?.sector_exposure || {})])].sort();
  return (
    <div id="portfolio-compare-result">
      <div className="trades-table-wrap">
        <table className="trades-table">
          <thead><tr><th>持仓</th><th>{escapeHtml(a.name)}</th><th>{escapeHtml(b.name)}</th></tr></thead>
          <tbody>
            {symbols.map((symbol) => (
              <tr key={symbol}>
                <td className="symbol">{escapeHtml(symbol)}</td>
                <td>{formatPercent(((a.config?.target_weights || {})[symbol] || 0) * 100)}</td>
                <td>{formatPercent(((b.config?.target_weights || {})[symbol] || 0) * 100)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="trades-table-wrap">
        <table className="trades-table">
          <thead><tr><th>风险指标</th><th>{escapeHtml(a.name)}</th><th>{escapeHtml(b.name)}</th></tr></thead>
          <tbody>
            {riskMetrics.map(([label, key, formatter]) => (
              <tr key={label}>
                <td className="symbol">{label}</td>
                <td>{a.risk ? formatter(a.risk[key] as number) : "--"}</td>
                <td>{b.risk ? formatter(b.risk[key] as number) : "--"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="trades-table-wrap">
        <table className="trades-table">
          <thead><tr><th>行业暴露</th><th>{escapeHtml(a.name)}</th><th>{escapeHtml(b.name)}</th></tr></thead>
          <tbody>
            {sectors.length ? sectors.map((sector) => (
              <tr key={sector}>
                <td className="symbol">{escapeHtml(sector)}</td>
                <td>{formatPercent((a.risk?.sector_exposure || {})[sector] || 0)}</td>
                <td>{formatPercent((b.risk?.sector_exposure || {})[sector] || 0)}</td>
              </tr>
            )) : <tr><td colSpan={3} className="muted">暂无行业暴露数据</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
