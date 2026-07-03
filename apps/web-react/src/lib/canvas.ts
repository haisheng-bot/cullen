// Ported verbatim from apps/web/index.html (lines 4143-4249) — canvas sizing/layout primitives
// shared by both hand-rolled charts (OhlcChart here, EquityCurveChart in commit 7). Kept as plain
// functions per plan Decision #6: no charting library introduced in Phase 1.
// ponytail: hand-rolled canvas ported as-is, swap for recharts/lightweight-charts if perf or
// feature needs justify it later.

export interface ChartPad {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export interface ChartLayout {
  pad: ChartPad;
  priceTop: number;
  priceHeight: number;
  volumeTop: number;
  volumeHeight: number;
  width: number;
  right: number;
  bottom: number;
}

export function resizeCanvas(
  canvas: HTMLCanvasElement,
  ctx: CanvasRenderingContext2D,
  sizeKeyRef: { current: string },
): void {
  const ratio = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const width = Math.floor(rect.width * ratio);
  const height = Math.floor(rect.height * ratio);
  const sizeKey = `${width}x${height}`;
  if (sizeKeyRef.current !== sizeKey) {
    canvas.width = width;
    canvas.height = height;
    sizeKeyRef.current = sizeKey;
  }
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
}

export function chartLayout(width: number, height: number): ChartLayout {
  const pad: ChartPad = { top: 24, right: 56, bottom: 30, left: 58 };
  const priceHeight = Math.max(210, Math.floor((height - pad.top - pad.bottom) * 0.72));
  const volumeTop = pad.top + priceHeight + 22;
  const volumeHeight = Math.max(58, height - volumeTop - pad.bottom);
  return {
    pad,
    priceTop: pad.top,
    priceHeight,
    volumeTop,
    volumeHeight,
    width: width - pad.left - pad.right,
    right: width - pad.right,
    bottom: height - pad.bottom,
  };
}

export function pointX(index: number, points: unknown[], layout: ChartLayout): number {
  return layout.pad.left + (layout.width * index) / Math.max(points.length - 1, 1);
}

export function drawRoundedRect(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
): void {
  if (context.roundRect) {
    context.roundRect(x, y, width, height, radius);
    return;
  }
  context.moveTo(x + radius, y);
  context.lineTo(x + width - radius, y);
  context.quadraticCurveTo(x + width, y, x + width, y + radius);
  context.lineTo(x + width, y + height - radius);
  context.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  context.lineTo(x + radius, y + height);
  context.quadraticCurveTo(x, y + height, x, y + height - radius);
  context.lineTo(x, y + radius);
  context.quadraticCurveTo(x, y, x + radius, y);
}
