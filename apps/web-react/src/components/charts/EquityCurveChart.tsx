import { useEffect, useRef } from "react";
import { drawRoundedRect } from "../../lib/canvas";
import { formatMoney } from "../../lib/format";

// Ported verbatim from apps/web/index.html drawEquityCurve (lines 3337-3417), wrapped in
// useRef+useEffect per plan Decision #6 (same pattern proven by OhlcChart in commit 5). Reuses
// drawRoundedRect from lib/canvas.ts for the legend swatches.

export interface EquityCurvePoint {
  portfolio_value: number;
  benchmark_value?: number;
}

interface EquityCurveChartProps {
  equityCurve: EquityCurvePoint[] | null | undefined;
}

export default function EquityCurveChart({ equityCurve }: EquityCurveChartProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  function drawEquityCurve(curve: EquityCurvePoint[] | null | undefined, canvasEl: HTMLCanvasElement) {
    const points = (curve || []).filter((p) => p && typeof p.portfolio_value === "number");
    const ratio = window.devicePixelRatio || 1;
    const rect = canvasEl.getBoundingClientRect();
    canvasEl.width = Math.max(1, Math.floor(rect.width * ratio));
    canvasEl.height = Math.max(1, Math.floor(rect.height * ratio));
    const context = canvasEl.getContext("2d");
    if (!context) return;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    const w = rect.width;
    const h = rect.height;
    context.clearRect(0, 0, w, h);
    if (!points.length) return;

    const pad = { top: 14, right: 14, bottom: 26, left: 60 };
    const plotWidth = w - pad.left - pad.right;
    const plotHeight = h - pad.top - pad.bottom;
    const hasBenchmark = points.some((p) => typeof p.benchmark_value === "number");
    const benchmarkValues = points.map((p) => p.benchmark_value).filter((v): v is number => typeof v === "number");
    const allValues = points.map((p) => p.portfolio_value).concat(benchmarkValues);
    const min = Math.min(...allValues);
    const max = Math.max(...allValues);
    const span = max - min || 1;
    const x = (index: number) => pad.left + (plotWidth * index) / Math.max(points.length - 1, 1);
    const y = (value: number) => pad.top + plotHeight - ((value - min) / span) * plotHeight;

    context.strokeStyle = "#e4eaf2";
    context.lineWidth = 1;
    context.beginPath();
    for (let i = 0; i <= 4; i++) {
      const gridY = pad.top + (plotHeight / 4) * i;
      context.moveTo(pad.left, gridY);
      context.lineTo(w - pad.right, gridY);
    }
    context.stroke();

    context.fillStyle = "#607086";
    context.font = "11px system-ui";
    for (let i = 0; i <= 4; i++) {
      const value = max - (span / 4) * i;
      context.fillText(formatMoney(value), 2, pad.top + (plotHeight / 4) * i + 4);
    }

    const drawLine = (values: Array<number | undefined>, color: string) => {
      context.strokeStyle = color;
      context.lineWidth = 2;
      context.beginPath();
      let started = false;
      values.forEach((value, index) => {
        if (typeof value !== "number") return;
        const px = x(index);
        const py = y(value);
        if (!started) {
          context.moveTo(px, py);
          started = true;
        } else {
          context.lineTo(px, py);
        }
      });
      context.stroke();
    };

    drawLine(points.map((p) => p.portfolio_value), "#0f766e");
    if (hasBenchmark) drawLine(points.map((p) => p.benchmark_value), "#9aa3b2");

    const legendY = h - 10;
    context.fillStyle = "#0f766e";
    context.beginPath();
    drawRoundedRect(context, pad.left, legendY - 8, 10, 10, 2);
    context.fill();
    context.fillStyle = "#34404a";
    context.font = "11px system-ui";
    context.fillText("组合净值", pad.left + 14, legendY);
    if (hasBenchmark) {
      context.fillStyle = "#9aa3b2";
      context.beginPath();
      drawRoundedRect(context, pad.left + 78, legendY - 8, 10, 10, 2);
      context.fill();
      context.fillStyle = "#34404a";
      context.fillText("基准净值", pad.left + 92, legendY);
    }
  }

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    drawEquityCurve(equityCurve, canvas);
  }, [equityCurve]);

  return (
    <div className="card chart-card equity-chart-card" id="equity-chart-card">
      <canvas id="equity-chart" ref={canvasRef} />
    </div>
  );
}
