import { ChartSpec } from '../../core/models/ai.model';
import { DARK_CHART, GRID, PALETTE, compactNumber } from './chart-theme';

type Row = Record<string, unknown>;

const pretty = (col: string) => col.replace(/_/g, ' ');

function formatter(format: ChartSpec['y_format']): (v: number) => string {
  switch (format) {
    case 'money': return v => `$${compactNumber(v)}`;
    case 'percent': return v => `${Number(v).toFixed(1)}%`;
    default: return v => (Math.abs(v) >= 1000 ? compactNumber(v) : `${Math.round(v * 100) / 100}`);
  }
}

/** A category / date value for the axis: ISO dates are shortened to the day. */
function label(v: unknown): string {
  const s = v === null || v === undefined ? '—' : String(v);
  return /^\d{4}-\d{2}-\d{2}T/.test(s) ? s.slice(0, 10) : s;
}

const num = (v: unknown) => (v === null || v === undefined || v === '' ? 0 : Number(v));

/** ChartSpec + rows -> ApexCharts options (the same builder for the chat and the dashboard). */
export function buildChart(spec: ChartSpec, rows: Row[], height = 260): any {
  const fmt = formatter(spec.y_format);
  const base = {
    chart: {
      ...DARK_CHART,
      height,
      toolbar: { show: true, tools: { download: true, selection: false, zoom: false, zoomin: false, zoomout: false, pan: false, reset: false } },
    },
    colors: PALETTE,
    dataLabels: { enabled: false },
    grid: GRID,
    legend: { show: true, position: 'top' as const, labels: { colors: '#94a3b8' } },
    tooltip: { theme: 'dark', y: { formatter: fmt } },
  };

  // ---- pie / donut: one value per category
  if (spec.type === 'pie' || spec.type === 'donut') {
    return {
      ...base,
      chart: { ...base.chart, type: spec.type },
      series: rows.map(r => num(r[spec.y[0]])),
      labels: rows.map(r => label(r[spec.x])),
      legend: { ...base.legend, position: 'bottom' as const },
      stroke: { show: false },
    };
  }

  // ---- scatter: x and y are both numbers
  if (spec.type === 'scatter') {
    return {
      ...base,
      chart: { ...base.chart, type: 'scatter', zoom: { enabled: false } },
      series: spec.y.map(y => ({ name: pretty(y), data: rows.map(r => [num(r[spec.x]), num(r[y])]) })),
      xaxis: { type: 'numeric', title: { text: pretty(spec.x), style: { color: '#64748b' } }, labels: { formatter: (v: string) => compactNumber(Number(v)) } },
      yaxis: { labels: { formatter: fmt } },
      markers: { size: 5 },
    };
  }

  // ---- bars and lines: categories on x
  // with a series the x values repeat on purpose (one row per group); without one,
  // every row is its own bar, even when two rows share a label (e.g. the same job title)
  const categories = spec.series ? [...new Set(rows.map(r => label(r[spec.x])))] : rows.map(r => label(r[spec.x]));
  let series: { name: string; data: number[] }[];
  if (spec.series) {
    // long format (department, gender, value) -> one series per gender
    const groups = [...new Set(rows.map(r => label(r[spec.series!])))];
    series = groups.map(g => ({
      name: g,
      data: categories.map(c => {
        const row = rows.find(r => label(r[spec.x]) === c && label(r[spec.series!]) === g);
        return row ? num(row[spec.y[0]]) : 0;
      }),
    }));
  } else {
    series = spec.y.map(y => ({ name: pretty(y), data: rows.map(r => num(r[y])) }));
  }

  const horizontal = spec.type === 'horizontal-bar';
  const isLine = spec.type === 'line';
  const manyLabels = categories.length > 8;
  return {
    ...base,
    chart: {
      ...base.chart,
      type: isLine ? 'line' : 'bar',
      stacked: spec.type === 'stacked-bar',
      height: horizontal ? Math.max(height, categories.length * 26) : height,
      zoom: { enabled: false },
    },
    series,
    legend: { ...base.legend, show: series.length > 1 },
    xaxis: {
      categories,
      // long time series: about 12 evenly spaced labels instead of all of them
      tickAmount: isLine && categories.length > 16 ? 12 : undefined,
      labels: horizontal
        ? { formatter: (v: string) => fmt(Number(v)) }
        : { rotate: manyLabels && !isLine ? -45 : 0, hideOverlappingLabels: true, trim: !isLine, maxHeight: 90, style: { fontSize: '10px' } },
    },
    yaxis: horizontal ? { labels: { maxWidth: 160 } } : { labels: { formatter: fmt } },
    plotOptions: { bar: { horizontal, borderRadius: 3, columnWidth: '55%', barHeight: '65%' } },
    stroke: { width: isLine ? 2.5 : 0, curve: 'smooth' },
    markers: { size: isLine && categories.length <= 24 ? 4 : 0 },
  };
}
