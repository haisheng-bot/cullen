import { useEffect, useRef, useState } from "react";
import { chartLayout, drawRoundedRect, pointX, resizeCanvas } from "../../lib/canvas";
import { fmt, formatChartTime, formatCompactNumber, formatMoney, formatPercent } from "../../lib/format";

// Ported verbatim from apps/web/index.html drawChart/updateChartHover/
// updateChartHoverFromClientPoint/estimateTradeFlow/estimatedSharesOutstanding/renderInspector
// (lines 4157-4389), wrapped in useRef+useEffect per plan Decision #6. First canvas chart ported
// (proves the pattern before EquityCurveChart in commit 7).

export interface TrendPoint {
  timestamp: string | number;
  close: number;
  volume?: number;
}

interface TradeFlow {
  buyVolume: number | null;
  sellVolume: number | null;
  cumulativeVolume: number | null;
  turnoverRate: number | null;
  direction: "buy" | "sell" | "flat";
}

function estimatedSharesOutstanding(marketCap: number | null | undefined, price: number | null): number | null {
  if (!marketCap || !price) return null;
  return marketCap / price;
}

function estimateTradeFlow(points: TrendPoint[], index: number, marketCap: number | null | undefined): TradeFlow {
  const point = points[index];
  if (!point) {
    return { buyVolume: null, sellVolume: null, cumulativeVolume: null, turnoverRate: null, direction: "flat" };
  }
  const previous = points[Math.max(index - 1, 0)];
  const volume = point.volume || 0;
  let buyVolume = 0;
  let sellVolume = 0;
  let direction: TradeFlow["direction"] = "flat";
  if (point.close > previous.close) {
    buyVolume = volume;
    direction = "buy";
  } else if (point.close < previous.close) {
    sellVolume = volume;
    direction = "sell";
  } else {
    buyVolume = volume / 2;
    sellVolume = volume / 2;
  }
  const cumulativeVolume = points.slice(0, index + 1).reduce((sum, item) => sum + (item.volume || 0), 0);
  const sharesOutstanding = estimatedSharesOutstanding(marketCap, point.close);
  const turnoverRate = sharesOutstanding ? (cumulativeVolume / sharesOutstanding) * 100 : null;
  return { buyVolume, sellVolume, cumulativeVolume, turnoverRate, direction };
}

interface OhlcChartProps {
  points: TrendPoint[];
  previousClose?: number | null;
  marketCap?: number | null;
}

export default function OhlcChart({ points, previousClose, marketCap }: OhlcChartProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const chartSizeKey = useRef("");
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  function drawChart(hoverIdx: number | null) {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    resizeCanvas(canvas, ctx, chartSizeKey);
    const rect = canvas.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height;
    ctx.clearRect(0, 0, w, h);
    if (!points.length) return;

    const layout = chartLayout(w, h);
    const values = points.map((p) => p.close);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const volumes = points.map((p) => p.volume || 0);
    const maxVolume = Math.max(...volumes, 1);
    const first = points[0];
    const last = points[points.length - 1];
    const lineColor = last.close >= first.close ? "#0f8b57" : "#c43b38";

    ctx.strokeStyle = "#e4eaf2";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i <= 4; i++) {
      const y = layout.priceTop + (layout.priceHeight / 4) * i;
      ctx.moveTo(layout.pad.left, y);
      ctx.lineTo(layout.right, y);
    }
    ctx.moveTo(layout.pad.left, layout.volumeTop);
    ctx.lineTo(layout.right, layout.volumeTop);
    ctx.moveTo(layout.pad.left, layout.bottom);
    ctx.lineTo(layout.right, layout.bottom);
    ctx.stroke();

    ctx.fillStyle = "#607086";
    ctx.font = "12px system-ui";
    for (let i = 0; i <= 4; i++) {
      const value = max - (span / 4) * i;
      const y = layout.priceTop + (layout.priceHeight / 4) * i + 4;
      ctx.fillText(value.toFixed(2), 10, y);
      ctx.fillText(value.toFixed(2), layout.right + 8, y);
    }
    ctx.fillText(formatCompactNumber(maxVolume), 10, layout.volumeTop + 12);
    ctx.fillText("VOL", layout.right + 8, layout.volumeTop + 12);

    const barWidth = Math.max(2, (layout.width / Math.max(points.length, 1)) * 0.62);
    points.forEach((point, index) => {
      const x = pointX(index, points, layout);
      const volumeHeight = ((point.volume || 0) / maxVolume) * layout.volumeHeight;
      const prior = points[Math.max(index - 1, 0)];
      ctx.fillStyle = point.close >= prior.close ? "rgba(15, 139, 87, 0.34)" : "rgba(196, 59, 56, 0.34)";
      ctx.fillRect(x - barWidth / 2, layout.bottom - volumeHeight, barWidth, volumeHeight);
    });

    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;
    ctx.beginPath();
    points.forEach((point, index) => {
      const x = pointX(index, points, layout);
      const y = layout.priceTop + layout.priceHeight - ((point.close - min) / span) * layout.priceHeight;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    const selectedIndex = Number.isInteger(hoverIdx) ? Math.max(0, Math.min(hoverIdx as number, points.length - 1)) : points.length - 1;
    const selected = points[selectedIndex];
    const selectedX = pointX(selectedIndex, points, layout);
    const selectedY = layout.priceTop + layout.priceHeight - ((selected.close - min) / span) * layout.priceHeight;

    ctx.save();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "rgba(23, 32, 51, 0.45)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(selectedX, layout.priceTop);
    ctx.lineTo(selectedX, layout.bottom);
    ctx.moveTo(layout.pad.left, selectedY);
    ctx.lineTo(layout.right, selectedY);
    ctx.stroke();
    ctx.restore();

    ctx.fillStyle = lineColor;
    ctx.beginPath();
    ctx.arc(selectedX, selectedY, 4, 0, Math.PI * 2);
    ctx.fill();

    const base = previousClose || first.close;
    const change = selected.close - base;
    const sign = change >= 0 ? "+" : "";
    const turnover = selected.volume ? selected.close * selected.volume : null;
    const flow = estimateTradeFlow(points, selectedIndex, marketCap);
    const tooltipLines = [
      formatChartTime(selected.timestamp),
      `Price ${fmt(selected.close)}`,
      `Change ${sign}${fmt(change)}`,
      `Vol ${formatCompactNumber(selected.volume)}`,
      `Amount ${formatMoney(turnover)}`,
      `T/O Rate ${formatPercent(flow.turnoverRate)}`,
      `Buy ${formatCompactNumber(flow.buyVolume)} / Sell ${formatCompactNumber(flow.sellVolume)}`,
    ];
    const tooltipWidth = 168;
    const tooltipHeight = 138;
    const tooltipX = selectedX + tooltipWidth + 18 > layout.right ? selectedX - tooltipWidth - 14 : selectedX + 14;
    const tooltipY = Math.max(layout.priceTop + 4, Math.min(selectedY - 18, layout.bottom - tooltipHeight));
    ctx.fillStyle = "rgba(17, 24, 39, 0.92)";
    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    drawRoundedRect(ctx, tooltipX, tooltipY, tooltipWidth, tooltipHeight, 7);
    ctx.fill();
    ctx.stroke();
    tooltipLines.forEach((line, index) => {
      ctx.fillStyle = index === 2 ? (change >= 0 ? "#6ee7b7" : "#fca5a5") : "#f8fafc";
      ctx.font = index === 1 ? "700 12px system-ui" : "12px system-ui";
      ctx.fillText(line, tooltipX + 10, tooltipY + 20 + index * 17);
    });
  }

  function updateChartHover(event: { offsetX?: number; clientX?: number; touches?: { clientX: number }[] }) {
    if (!points.length) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const layout = chartLayout(rect.width, rect.height);
    const touchX = event.touches?.[0]?.clientX;
    const rawX = Number.isFinite(event.offsetX) ? (event.offsetX as number) : (touchX ?? event.clientX ?? rect.left) - rect.left;
    const boundedX = Math.max(layout.pad.left, Math.min(rawX, layout.right));
    const ratio = (boundedX - layout.pad.left) / Math.max(layout.width, 1);
    const index = Math.round(ratio * (points.length - 1));
    setHoverIndex(index);
  }

  function updateChartHoverFromClientPoint(clientX: number, clientY: number) {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const insideChart = clientX >= rect.left && clientX <= rect.right && clientY >= rect.top && clientY <= rect.bottom;
    if (!insideChart) return;
    updateChartHover({ clientX });
  }

  useEffect(() => {
    drawChart(hoverIndex);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points, hoverIndex, previousClose, marketCap]);

  useEffect(() => {
    function onResize() {
      if (points.length) drawChart(hoverIndex);
    }
    window.addEventListener("resize", onResize);
    // document-level pointermove mirrors the legacy app's global listener so the crosshair keeps
    // tracking even if the pointer briefly leaves the canvas element mid-drag.
    function onDocumentPointerMove(event: PointerEvent) {
      updateChartHoverFromClientPoint(event.clientX, event.clientY);
    }
    document.addEventListener("pointermove", onDocumentPointerMove);
    return () => {
      window.removeEventListener("resize", onResize);
      document.removeEventListener("pointermove", onDocumentPointerMove);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points, hoverIndex]);

  const selectedIndex = Number.isInteger(hoverIndex) ? Math.max(0, Math.min(hoverIndex as number, points.length - 1)) : points.length - 1;
  const selected = points[selectedIndex];
  const first = points[0];
  const base = previousClose || first?.close || 0;
  const change = selected ? selected.close - base : 0;
  const changePercent = base ? (change / base) * 100 : 0;
  const changeSign = change >= 0 ? "+" : "";
  const changeClass = change >= 0 ? "positive" : "negative";
  const turnover = selected?.volume ? selected.close * selected.volume : null;
  const flow = selected ? estimateTradeFlow(points, selectedIndex, marketCap) : null;

  return (
    <>
      <canvas
        ref={canvasRef}
        id="chart"
        onPointerMove={(e) => updateChartHover({ offsetX: e.nativeEvent.offsetX, clientX: e.clientX })}
        onPointerDown={(e) => updateChartHover({ offsetX: e.nativeEvent.offsetX, clientX: e.clientX })}
        onPointerLeave={() => setHoverIndex(null)}
        onTouchMove={(e) => {
          e.preventDefault();
          updateChartHover({ touches: [{ clientX: e.touches[0].clientX }] });
        }}
      />
      <div className="chart-inspector">
        <div className="metric"><div className="label">Time</div><div className="value" id="inspect-time">{selected ? formatChartTime(selected.timestamp) : "--"}</div></div>
        <div className="metric"><div className="label">Price</div><div className="value" id="inspect-price">{selected ? fmt(selected.close) : "--"}</div></div>
        <div className="metric"><div className="label">Change</div><div className={`value ${changeClass}`} id="inspect-change">{selected ? `${changeSign}${fmt(change)} (${changeSign}${fmt(changePercent)}%)` : "--"}</div></div>
        <div className="metric"><div className="label">Volume</div><div className="value" id="inspect-volume">{formatCompactNumber(selected?.volume)}</div></div>
        <div className="metric"><div className="label">Amount</div><div className="value" id="inspect-turnover">{formatMoney(turnover)}</div></div>
        <div className="metric"><div className="label">Turnover Rate</div><div className="value" id="inspect-turnover-rate">{formatPercent(flow?.turnoverRate ?? null)}</div></div>
        <div className="metric"><div className="label">Buy Vol</div><div className="value positive" id="inspect-buy-volume">{formatCompactNumber(flow?.buyVolume ?? null)}</div></div>
        <div className="metric"><div className="label">Sell Vol</div><div className="value negative" id="inspect-sell-volume">{formatCompactNumber(flow?.sellVolume ?? null)}</div></div>
      </div>
    </>
  );
}
