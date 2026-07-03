import { useCallback, useEffect, useState } from "react";
import { request, friendlyBacktestError } from "../lib/api";
import { escapeHtml, formatRunTime } from "../lib/format";

// Ported verbatim from apps/web/index.html renderDataSourceHealth/loadDataSourceHealth
// (L2481-2510) — moved off Dashboard onto Settings per commit 2 of the Phase 1 migration.

interface DataSourceHealthItem {
  name: string;
  status: string;
  configured?: boolean;
  available?: boolean;
  capabilities?: string[];
  last_error?: string;
  fallback?: string;
}

interface DataSourceHealthPayload {
  overall_status: string;
  available_count: number;
  total_count: number;
  checked_at?: string;
  items: DataSourceHealthItem[];
}

export default function DataSourceHealth() {
  const [status, setStatus] = useState("展示数据源配置、可用性、最近错误和 fallback 状态。");
  const [items, setItems] = useState<DataSourceHealthItem[]>([]);

  const loadDataSourceHealth = useCallback(async () => {
    setStatus("正在检查数据源健康状态...");
    try {
      const payload = await request<DataSourceHealthPayload>("/data-sources/health");
      const payloadItems = payload?.items || [];
      setStatus(
        payload
          ? `${payload.overall_status} · ${payload.available_count}/${payload.total_count} available · ${formatRunTime(payload.checked_at)}`
          : "数据源健康检查暂不可用。",
      );
      setItems(payloadItems);
    } catch (error) {
      setStatus(friendlyBacktestError(error));
      setItems([]);
    }
  }, []);

  useEffect(() => {
    loadDataSourceHealth();
  }, [loadDataSourceHealth]);

  return (
    <section className="daily-home">
      <div className="daily-home-head">
        <div>
          <div className="daily-home-title">Data Source Health</div>
          <div className="muted" id="data-source-health-status">{status}</div>
        </div>
        <span className="status-pill">P6</span>
      </div>
      <div className="data-health-list" id="data-source-health-list">
        {items.length ? (
          items.map((item) => (
            <div className="data-health-item" key={item.name}>
              <div className="data-health-head">
                <span className="data-health-name">{escapeHtml(item.name)}</span>
                <span className={`data-health-status ${escapeHtml(item.status)}`}>{escapeHtml(item.status)}</span>
              </div>
              <div className="daily-card-note">configured: {escapeHtml(item.configured ? "yes" : "no")} · available: {escapeHtml(item.available ? "yes" : "no")}</div>
              <div className="daily-card-note">capabilities: {escapeHtml((item.capabilities || []).join(", ") || "--")}</div>
              <div className="daily-card-note">last_error: {escapeHtml(item.last_error || "none")}</div>
              <div className="daily-card-note">fallback: {escapeHtml(item.fallback || "--")}</div>
            </div>
          ))
        ) : (
          <div className="workflow-note">暂无数据源健康信息。</div>
        )}
      </div>
    </section>
  );
}
