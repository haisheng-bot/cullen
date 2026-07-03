import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { request, postJson, friendlyBacktestError } from "../lib/api";
import { escapeHtml, formatRunTime } from "../lib/format";

// Ported from apps/web/index.html — researchHistoryQuery/renderResearchRunList/loadResearchRuns/
// loadResearchRunDetail (L3631-3694) and reportArchiveQuery/renderReportList/renderReportDetail/
// loadReports/loadReportDetail/createReportFromSelectedTrace (L3696-3776).

interface ResearchRunItem {
  trace_id: string;
  portfolio_name?: string;
  strategy_library_name?: string;
  summary_text?: string;
  started_at?: string;
  symbols?: string[];
  state: string;
}

interface ReportItem {
  trace_id: string;
  title?: string;
  portfolio_name?: string;
  risk_disclaimer?: string;
  generated_at?: string;
}

interface ReportDetail extends ReportItem {
  html?: string;
  markdown?: string;
}

export default function Reports() {
  const [portfolioFilter, setPortfolioFilter] = useState("");
  const [strategyFilter, setStrategyFilter] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [dateFilter, setDateFilter] = useState("");

  const [runs, setRuns] = useState<ResearchRunItem[]>([]);
  const [runStatus, setRunStatus] = useState("等待加载历史研究记录。");
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [selectedRunResult, setSelectedRunResult] = useState<Record<string, unknown> | null>(null);

  const [reports, setReports] = useState<ReportItem[]>([]);
  const [reportStatus, setReportStatus] = useState("请选择一条 Research Run 后生成报告。");
  const [reportDetail, setReportDetail] = useState<ReportDetail | null>(null);

  const loadResearchRuns = useCallback(async () => {
    setRunStatus("正在加载历史研究记录...");
    const params = new URLSearchParams({ limit: "20", offset: "0" });
    if (portfolioFilter.trim()) params.set("portfolio_name", portfolioFilter.trim());
    if (strategyFilter.trim()) params.set("strategy_library_name", strategyFilter.trim());
    if (stateFilter) params.set("state", stateFilter);
    if (dateFilter) {
      params.set("start_date", dateFilter);
      params.set("end_date", dateFilter);
    }
    try {
      const payload = (await request(`/research-runs?${params.toString()}`)) as {
        items: ResearchRunItem[];
        total_count: number;
      };
      const items = payload.items || [];
      setRuns(items);
      setRunStatus(items.length ? `已加载 ${items.length}/${payload.total_count || 0} 条历史研究记录。` : "暂无匹配的历史研究记录。");
    } catch (error) {
      setRuns([]);
      setRunStatus(friendlyBacktestError(error));
    }
  }, [portfolioFilter, strategyFilter, stateFilter, dateFilter]);

  const loadReports = useCallback(async () => {
    setReportStatus("正在加载报告归档...");
    const params = new URLSearchParams({ limit: "20", offset: "0" });
    if (portfolioFilter.trim()) params.set("portfolio_name", portfolioFilter.trim());
    try {
      const payload = (await request(`/reports?${params.toString()}`)) as { items: ReportItem[]; total_count: number };
      const items = payload.items || [];
      setReports(items);
      setReportStatus(items.length ? `已加载 ${items.length}/${payload.total_count || 0} 份报告。` : "暂无匹配的报告归档。");
    } catch (error) {
      setReports([]);
      setReportStatus(friendlyBacktestError(error));
    }
  }, [portfolioFilter]);

  useEffect(() => {
    loadResearchRuns();
    loadReports();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Named loadResearchRunDetail/loadReportDetail (not openRunDetail/openReportDetail) to match the
  // legacy app's identifiers verbatim — see plan's "Governance test retargeting" note on preserving
  // literal identifiers so retargeted tests still validate real intent.
  async function loadResearchRunDetail(traceId: string) {
    setSelectedTraceId(traceId);
    setRunStatus(`正在复盘 trace_id ${traceId}...`);
    try {
      // ponytail: full workflow/backtest/risk/AI-summary rendering (renderPortfolioResearchResult
      // in the legacy app) lives with the Portfolio Research page (commit 7 of this migration) since
      // it reuses the same result renderers as a live run. Until then, show the raw result summary;
      // upgrade this to route into PortfolioResearch's shared result view once that page exists.
      const result = (await request(`/portfolio-research/${encodeURIComponent(traceId)}`)) as Record<string, unknown>;
      setSelectedRunResult(result);
      setRunStatus(`已打开 trace_id ${traceId}。`);
    } catch (error) {
      setRunStatus(friendlyBacktestError(error));
    }
  }

  async function loadReportDetail(traceId: string) {
    setReportStatus(`正在打开报告 ${traceId}...`);
    try {
      const report = await request<ReportDetail>(`/reports/${encodeURIComponent(traceId)}`);
      setReportDetail(report);
      setReportStatus(`已打开报告 ${traceId}。`);
    } catch (error) {
      setReportStatus(friendlyBacktestError(error));
    }
  }

  async function createReportFromSelectedTrace() {
    if (!selectedTraceId) {
      setReportStatus("请先在 Research Run 复盘中选择一条 trace_id。");
      return;
    }
    const traceId = selectedTraceId;
    setReportStatus(`正在生成报告 ${traceId}...`);
    try {
      const report = (await postJson(`/reports/from-trace/${encodeURIComponent(traceId)}`, {})) as ReportDetail;
      setReportDetail(report);
      await loadReports();
      setReportStatus(`已生成并归档报告 ${traceId}。`);
    } catch (error) {
      setReportStatus(friendlyBacktestError(error));
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Reports 研究报告</div>
          <div className="muted">Research Run 复盘与 Report Archive——沉淀系统生成的研究结果。</div>
        </div>
      </div>

      <div className="research-history">
        <div className="research-history-head">
          <div>
            <div className="research-history-title">Research Run 复盘</div>
            <div className="workflow-note">按组合、策略和状态查看历史研究运行，点击任一记录复盘 trace_id。</div>
          </div>
          <span className="status-pill">P3</span>
        </div>
        <div className="research-history-filters">
          <input placeholder="组合名" value={portfolioFilter} onChange={(e) => setPortfolioFilter(e.target.value)} />
          <input placeholder="策略库存档名" value={strategyFilter} onChange={(e) => setStrategyFilter(e.target.value)} />
          <select value={stateFilter} onChange={(e) => setStateFilter(e.target.value)}>
            <option value="">全部状态</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
            <option value="Recommendation Ready">Recommendation Ready</option>
            <option value="Failed">Failed</option>
          </select>
          <input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} />
          <button type="button" onClick={loadResearchRuns}>刷新历史</button>
        </div>
        <div className="workflow-note">{runStatus}</div>
        <div className="research-run-list">
          {runs.map((item) => (
            <button
              key={item.trace_id}
              type="button"
              className={`research-run-item${item.trace_id === selectedTraceId ? " active" : ""}`}
              onClick={() => loadResearchRunDetail(item.trace_id)}
            >
              <span className="research-run-main">
                <span className="research-run-name">
                  {escapeHtml(item.portfolio_name || "未命名组合")} · {escapeHtml(item.strategy_library_name || "未绑定策略")}
                </span>
                <span className="research-run-summary">{escapeHtml(item.summary_text || "暂无摘要")}</span>
                <span className="research-run-meta">
                  {formatRunTime(item.started_at)} · {(item.symbols || []).join(", ") || "--"} · {item.trace_id}
                </span>
              </span>
              <span className="research-run-state">{item.state}</span>
            </button>
          ))}
        </div>
        {selectedRunResult && (
          <div className="report-detail">
            <div className="research-run-name">trace_id: {selectedTraceId}</div>
            <pre style={{ whiteSpace: "pre-wrap", margin: "6px 0 0" }}>
              {JSON.stringify(selectedRunResult, null, 2).slice(0, 4000)}
            </pre>
            <Link to={`/portfolio?trace=${encodeURIComponent(selectedTraceId || "")}`}>
              在 Portfolio Research 中查看完整结果 →
            </Link>
          </div>
        )}
      </div>

      <div className="research-history">
        <div className="research-history-head">
          <div>
            <div className="research-history-title">Report Archive</div>
            <div className="workflow-note">从已完成的 trace_id 生成 Markdown/HTML 报告，并保留报告归档。</div>
          </div>
          <span className="status-pill">P4</span>
        </div>
        <div className="report-archive-actions">
          <button className="primary" type="button" onClick={createReportFromSelectedTrace}>生成当前报告</button>
          <button type="button" onClick={loadReports}>刷新报告</button>
        </div>
        <div className="workflow-note">{reportStatus}</div>
        <div className="research-run-list" id="report-archive-list">
          {reports.map((item) => (
            <button
              key={item.trace_id}
              type="button"
              className="research-run-item"
              onClick={() => loadReportDetail(item.trace_id)}
            >
              <span className="research-run-main">
                <span className="research-run-name">{escapeHtml(item.title || "Research Report")}</span>
                <span className="research-run-summary">
                  {escapeHtml(item.portfolio_name || "未命名组合")} · {escapeHtml(item.risk_disclaimer || "")}
                </span>
                <span className="research-run-meta">{formatRunTime(item.generated_at)} · {item.trace_id}</span>
              </span>
              <span className="research-run-state">HTML</span>
            </button>
          ))}
        </div>
        {reportDetail && (
          <div className="report-detail">
            <div className="research-run-name">{escapeHtml(reportDetail.title || "Research Report")}</div>
            <div className="research-run-meta">
              {escapeHtml(reportDetail.portfolio_name || "未命名组合")} · {formatRunTime(reportDetail.generated_at)} · {reportDetail.trace_id}
            </div>
            {reportDetail.html ? (
              <div dangerouslySetInnerHTML={{ __html: reportDetail.html }} />
            ) : (
              <pre>{escapeHtml(reportDetail.markdown || "")}</pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
