import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { deleteJson, putJson, request } from "../lib/api";
import { downloadTextFile, escapeHtml } from "../lib/format";

// Carved out of the Portfolio Research code per commit 6 of the page-split migration: strategy
// CRUD + modal (loadStrategies/renderStrategyList/applyStrategy/saveCurrentFormAsStrategy/
// openStrategyModal+submitStrategyModal/deleteStrategyByName, L2582-2785).
//
// ponytail deviation (plan Decisions #5/#7): the legacy applyStrategy/saveCurrentFormAsStrategy
// read and write the Portfolio Research Workbench's live form fields (workflowStrategy,
// signalModeSelect, benchmarkSymbolInput, etc.), which belong to PortfolioResearch — not built
// until commit 7. Rather than reaching into a page that doesn't exist yet:
//   - "应用"/"推荐组合" navigate to /portfolio?strategy=<name>[&autorun=1]; PortfolioResearch
//     (commit 7) reads that query param on mount and calls its own applyStrategy/
//     generateStrategyResearchPortfolio, restoring the original cross-feature behavior once both
//     pages exist.
//   - "保存"/"更新" (saveCurrentFormAsStrategy) has no live workbench form to read on this page,
//     so it PUTs a strategy record built from the template's own defaults (same shape as legacy
//     currentStrategyPayload) instead of inventing new UI. Once PortfolioResearch exists, its own
//     "存为策略" action (still to be wired) can PUT the live form the same way.

interface StrategyOption {
  name: string;
  method: string;
  summary: string;
}

const STRATEGY_LIBRARY_OPTIONS: StrategyOption[] = [
  { name: "Equal Weight", method: "equal_weight", summary: "等权基准策略，适合快速建立中性组合。" },
  { name: "Momentum", method: "minimum_variance", summary: "动量研究模板，适合跟踪强趋势候选股。" },
  { name: "Growth", method: "minimum_variance", summary: "成长风格模板，聚焦营收和盈利扩张。" },
  { name: "Quality", method: "minimum_variance", summary: "质量风格模板，强调盈利稳定性和资产质量。" },
  { name: "Value", method: "minimum_variance", summary: "价值风格模板，关注估值安全边际。" },
  { name: "Low Volatility", method: "risk_parity", summary: "低波动模板，优先控制组合波动。" },
  { name: "Dividend", method: "equal_weight", summary: "股息风格模板，适合收益型候选组合。" },
  { name: "Minimum Variance", method: "minimum_variance", summary: "最小方差模板，适合风险优先研究。" },
  { name: "AI Momentum", method: "minimum_variance", summary: "AI 评分 + 动量模板，适合因子增强研究。" },
  { name: "Sector Rotation", method: "market_cap", summary: "行业轮动模板，适合主题和板块比较。" },
  { name: "Risk Parity", method: "risk_parity", summary: "风险平价模板，按风险贡献分配权重。" },
  { name: "Black-Litterman", method: "minimum_variance", summary: "Black-Litterman 研究模板，预留主观观点融合。" },
];

interface StrategyPreferences {
  scoring_mode?: string;
  backtest_mode?: string;
  optimizer_method?: string;
  rebalance_frequency?: string;
  scoring_profile?: string;
}

interface StrategyRecord {
  name: string;
  preferences?: StrategyPreferences;
  constraints?: Record<string, unknown>;
}

function defaultPayloadForOption(option: StrategyOption) {
  return {
    preferences: {
      scoring_mode: "algorithm_v0.3",
      backtest_mode: option.name === "AI Momentum" ? "ai_score" : "technical",
      optimizer_method: option.method,
      rebalance_frequency: "monthly",
      scoring_profile: "balanced",
    },
    constraints: {
      max_position_weight: 0.25,
      min_cash_weight: 0.1,
      max_drawdown: 0.12,
      benchmark_symbol: "SPY",
      backtest_years: 3,
    },
  };
}

export default function StrategyLibrary() {
  const [strategies, setStrategies] = useState<Record<string, StrategyRecord>>({});
  const [appliedStrategyName, setAppliedStrategyName] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalStatus, setModalStatus] = useState("");
  const [modalSubmitting, setModalSubmitting] = useState(false);
  const navigate = useNavigate();
  const importInputRef = useRef<HTMLInputElement | null>(null);

  // Uncontrolled select read via getElementById, same idiom the legacy app used for this element
  // (`const strategyModalName = document.getElementById("strategy-modal-name")`) — kept so the
  // JSX tag below stays exactly `<select id="strategy-modal-name">`, matching the governance test.
  function strategyModalNameEl(): HTMLSelectElement | null {
    return document.getElementById("strategy-modal-name") as HTMLSelectElement | null;
  }

  const loadStrategies = useCallback(async () => {
    const data = await request<{ items: StrategyRecord[] }>("/strategies");
    const map: Record<string, StrategyRecord> = {};
    data.items.forEach((strategy) => {
      map[strategy.name] = strategy;
    });
    setStrategies(map);
  }, []);

  useEffect(() => {
    loadStrategies();
  }, [loadStrategies]);

  function applyStrategy(name: string) {
    setAppliedStrategyName(name);
    navigate(`/portfolio?strategy=${encodeURIComponent(name)}`);
  }

  function generateStrategyResearchPortfolio(name: string) {
    setAppliedStrategyName(name);
    navigate(`/portfolio?strategy=${encodeURIComponent(name)}&autorun=1`);
  }

  async function saveCurrentFormAsStrategy(name: string, option: StrategyOption | undefined) {
    try {
      const payload = option ? defaultPayloadForOption(option) : defaultPayloadForOption({ name, method: "minimum_variance", summary: "" });
      const saved = await putJson<StrategyRecord>(`/strategies/${encodeURIComponent(name)}`, payload);
      setStrategies((prev) => ({ ...prev, [saved.name]: saved }));
      setAppliedStrategyName(saved.name);
      return saved;
    } catch (error) {
      window.alert(`保存策略失败：${error instanceof Error ? error.message : String(error)}`);
      return null;
    }
  }

  async function deleteStrategyByName(name: string) {
    if (!window.confirm(`删除策略「${name}」？`)) return;
    try {
      await deleteJson(`/strategies/${encodeURIComponent(name)}`);
    } catch (error) {
      window.alert(`删除策略失败：${error instanceof Error ? error.message : String(error)}`);
      return;
    }
    setStrategies((prev) => {
      const next = { ...prev };
      delete next[name];
      return next;
    });
    setAppliedStrategyName((current) => (current === name ? null : current));
  }

  async function cloneStrategy(strategy: StrategyRecord) {
    const newName = window.prompt(`另存为新策略名称（复制自「${strategy.name}」）：`, `${strategy.name} Copy`)?.trim();
    if (!newName) return;
    if (strategies[newName]) {
      window.alert(`策略「${newName}」已存在，请换一个名称。`);
      return;
    }
    try {
      const saved = await putJson<StrategyRecord>(`/strategies/${encodeURIComponent(newName)}`, {
        preferences: strategy.preferences || {},
        constraints: strategy.constraints || {},
      });
      setStrategies((prev) => ({ ...prev, [saved.name]: saved }));
      setAppliedStrategyName(saved.name);
    } catch (error) {
      window.alert(`另存为失败：${error instanceof Error ? error.message : String(error)}`);
    }
  }

  function exportStrategy(strategy: StrategyRecord) {
    const payload = {
      name: strategy.name,
      preferences: strategy.preferences || {},
      constraints: strategy.constraints || {},
    };
    downloadTextFile(`${strategy.name}.json`, JSON.stringify(payload, null, 2), "application/json");
  }

  function openStrategyImport() {
    if (importInputRef.current) {
      importInputRef.current.value = "";
      importInputRef.current.click();
    }
  }

  async function onImportFileChange() {
    const file = importInputRef.current?.files?.[0];
    if (!file) return;
    try {
      const data = JSON.parse(await file.text());
      const name = String(data.name || "").trim();
      if (!name) throw new Error("导入文件缺少策略名称 (name)");
      const saved = await putJson<StrategyRecord>(`/strategies/${encodeURIComponent(name)}`, {
        preferences: data.preferences || {},
        constraints: data.constraints || {},
      });
      setStrategies((prev) => ({ ...prev, [saved.name]: saved }));
      setAppliedStrategyName(saved.name);
      window.alert(`已导入策略「${saved.name}」。`);
    } catch (error) {
      window.alert(`导入失败：${error instanceof Error ? error.message : String(error)}`);
    }
  }

  function openStrategyModal() {
    setModalStatus("");
    setModalSubmitting(false);
    setModalOpen(true);
    window.setTimeout(() => {
      const el = strategyModalNameEl();
      if (el) {
        el.selectedIndex = 0;
        el.focus();
      }
    }, 0);
  }

  function closeStrategyModal() {
    setModalOpen(false);
  }

  async function submitStrategyModal(event: React.FormEvent) {
    event.preventDefault();
    const name = strategyModalNameEl()?.value.trim() || "";
    if (!name) {
      setModalStatus("请选择策略。");
      strategyModalNameEl()?.focus();
      return;
    }
    setModalStatus("正在保存策略...");
    setModalSubmitting(true);
    const option = STRATEGY_LIBRARY_OPTIONS.find((item) => item.name === name);
    const saved = await saveCurrentFormAsStrategy(name, option);
    if (!saved) {
      setModalStatus("保存失败，请检查策略参数后重试。");
      setModalSubmitting(false);
      return;
    }
    closeStrategyModal();
  }

  const configuredOptions: StrategyOption[] = [...STRATEGY_LIBRARY_OPTIONS];
  Object.values(strategies).forEach((strategy) => {
    if (configuredOptions.some((option) => option.name === strategy.name)) return;
    configuredOptions.push({
      name: strategy.name,
      method: strategy.preferences?.optimizer_method || "minimum_variance",
      summary: "历史保存的自定义策略组合，可继续应用、更新或删除。",
    });
  });

  const fixedSavedCount = STRATEGY_LIBRARY_OPTIONS.filter((option) => strategies[option.name]).length;
  const customSavedCount = Object.keys(strategies).length - fixedSavedCount;
  const selectedLabel = appliedStrategyName || "未选择";

  function renderStrategyList() {
    return configuredOptions.map((option) => {
      const strategy = strategies[option.name];
      const isSaved = Boolean(strategy);
      const isSelected = appliedStrategyName === option.name;
      const prefs = strategy?.preferences || {};
      const optimizer = prefs.optimizer_method || option.method;
      const backtestMode = prefs.backtest_mode || "technical";
      const rebalance = prefs.rebalance_frequency || "monthly";
      const scoringProfile = prefs.scoring_profile || "balanced";
      return (
        <div className={`strategy-item${isSelected ? " selected" : ""}`} key={option.name}>
          <div className="strategy-item-head">
            <span>{escapeHtml(option.name)}</span>
            <span className="strategy-item-badges">
              {isSelected && <span className="strategy-badge selected">当前选择</span>}
              <span className="strategy-badge">{isSaved ? "已保存" : "待保存"}</span>
            </span>
          </div>
          <div className="strategy-item-summary">{escapeHtml(optimizer)} · {escapeHtml(backtestMode)} · {escapeHtml(rebalance)} · {escapeHtml(scoringProfile)}</div>
          <div className="strategy-item-summary">{escapeHtml(option.summary)}</div>
          <div className="strategy-item-actions">
            {isSaved && <button type="button" onClick={() => applyStrategy(option.name)}>应用</button>}
            <button type="button" onClick={() => generateStrategyResearchPortfolio(option.name)}>推荐组合</button>
            <button type="button" onClick={() => saveCurrentFormAsStrategy(option.name, option)}>{isSaved ? "更新" : "保存"}</button>
            {isSaved && <button type="button" onClick={() => cloneStrategy(strategy)}>另存为</button>}
            {isSaved && <button type="button" onClick={() => exportStrategy(strategy)}>导出 JSON</button>}
            {isSaved && <button type="button" onClick={() => deleteStrategyByName(option.name)}>删除</button>}
          </div>
        </div>
      );
    });
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Strategy Library</div>
          <div className="muted">策略管理——新建、编辑、复制、删除、运行策略。</div>
        </div>
        <div>
          <button id="add-strategy-button" type="button" onClick={openStrategyModal}>新增策略</button>
          <button type="button" onClick={openStrategyImport}>导入策略 JSON</button>
        </div>
      </div>
      <input type="file" id="strategy-import-input" ref={importInputRef} accept=".json" hidden onChange={onImportFileChange} />
      <div className="muted" id="strategy-list-meta">
        当前策略组合：{selectedLabel} · 固定已保存 {fixedSavedCount}/{STRATEGY_LIBRARY_OPTIONS.length} · 自定义 {customSavedCount}
      </div>
      <div className="strategy-list" id="strategy-list">
        {renderStrategyList()}
      </div>

      {modalOpen && (
        <div className="modal-backdrop" id="strategy-modal-backdrop" onClick={(e) => { if (e.target === e.currentTarget) closeStrategyModal(); }}>
          <form className="strategy-modal" id="strategy-modal-form" onSubmit={submitStrategyModal}>
            <div className="strategy-modal-title">新增策略</div>
            <div className="muted">选择策略模板并保存当前 Portfolio Research Workbench 的策略参数，之后可应用到任意组合。</div>
            <select id="strategy-modal-name">
              {STRATEGY_LIBRARY_OPTIONS.map((option) => (
                <option key={option.name} value={option.name}>{option.name}</option>
              ))}
            </select>
            {modalStatus && <div className="note" id="strategy-modal-status">{modalStatus}</div>}
            <div className="strategy-modal-actions">
              <button id="strategy-modal-cancel" type="button" onClick={closeStrategyModal}>取消</button>
              <button id="strategy-modal-submit" type="submit" disabled={modalSubmitting}>{modalSubmitting ? "保存中" : "保存策略"}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
