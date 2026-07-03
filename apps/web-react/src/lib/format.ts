// Ported verbatim from apps/web/index.html (lines 2260-2294) — formatting helpers shared across all pages.

export const fmt = (value: number | string | null | undefined): string =>
  value === null || value === undefined ? "--" : Number(value).toFixed(2);

export const formatCompactNumber = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(Number(value));
};

export const formatMoney = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `$${formatCompactNumber(value)}`;
};

export const formatPercent = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const sign = Number(value) > 0 ? "+" : "";
  return `${sign}${Number(value).toFixed(2)}%`;
};

export const formatRatio = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${Number(value).toFixed(2)}x`;
};

export const formatChartTime = (timestamp: string | number | null | undefined): string => {
  if (!timestamp) return "--";
  const date = new Date(timestamp);
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
};

export const formatRunTime = (timestamp: string | number | null | undefined): string => {
  if (!timestamp) return "--";
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return String(timestamp);
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
};

export const escapeHtml = (value: unknown): string =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

export function settledValue<T>(result: PromiseSettledResult<T>): T | null {
  return result.status === "fulfilled" ? result.value : null;
}

export function downloadTextFile(filename: string, content: string, mimeType = "text/plain"): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
