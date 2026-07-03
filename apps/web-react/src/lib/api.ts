// Ported verbatim from apps/web/index.html (lines 2296-2346, 3306-3335) — fetch wrappers and
// error-message mappers shared across all pages. Behavior unchanged from the vanilla-JS version.

const API = window.location.origin;

async function unwrapError(response: Response): Promise<never> {
  const err = await response.json().catch(() => ({}) as { detail?: string });
  throw new Error(err.detail || `HTTP ${response.status}`);
}

export async function request<T = unknown>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`);
  if (!response.ok) return unwrapError(response);
  return response.json();
}

export async function postJson<T = unknown>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) return unwrapError(response);
  return response.json();
}

export async function putJson<T = unknown>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) return unwrapError(response);
  return response.json();
}

export async function deleteJson<T = unknown>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`, { method: "DELETE" });
  if (!response.ok) return unwrapError(response);
  return response.json();
}

export async function requestOptional<T = unknown>(path: string): Promise<T | null> {
  try {
    return await request<T>(path);
  } catch {
    return null;
  }
}

// ponytail: preserved verbatim from the legacy app, including the "Backtest" framing that now
// reads oddly on non-backtest pages (e.g. Reports) — a shared rename to friendlyApiError is a
// good Phase-2 cleanup once every call site is ported, not a Phase-1 page-split concern.
export function friendlyBacktestError(error: unknown): string {
  const message = error instanceof Error ? error.message : "";
  if (/Failed to fetch|NetworkError|network/i.test(message)) {
    return `网络连接失败，请检查本地服务是否在运行。（${message}）`;
  }
  if (/422|400/.test(message)) {
    return `请求参数有误，请检查约束和高级设置后重试。（${message}）`;
  }
  if (/500|502|503/.test(message)) {
    return `服务端处理回测时出错，可能是外部数据源暂时不可用，请稍后重试。（${message}）`;
  }
  return `回测失败：${message}`;
}

const NODE_LABELS_ZH: Record<string, string> = {
  "Universe Builder": "股票池构建",
  "Portfolio Builder": "组合构建",
  "Strategy Selector": "策略选择",
  "Constraint Config": "约束配置",
  "Backtest Runner": "回测执行",
  "AI Summary": "AI 分析",
  "Portfolio Recommendation": "组合建议生成",
};

interface WorkflowNodeResult {
  name: string;
  state: string;
  error?: string;
}

export function friendlyWorkflowError(result: { node_results?: WorkflowNodeResult[] }): string {
  const failedNode = (result.node_results || []).find((node) => node.state === "Failed");
  if (!failedNode) return "工作流执行失败，请稍后重试。";
  const label = NODE_LABELS_ZH[failedNode.name] || failedNode.name;
  return `在「${label}」阶段失败：${failedNode.error || "未知错误"}`;
}
