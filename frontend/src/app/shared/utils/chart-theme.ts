import { ApexChart } from 'ng-apexcharts';

/** Common ApexCharts settings for the dark theme. */
export const DARK_CHART: Partial<ApexChart> = {
  foreColor: '#94a3b8',
  toolbar: { show: false },
  background: 'transparent',
  fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
  width: '100%', // follows the container (sidebar collapse / expand)
};

export const GRID = { borderColor: '#223047', strokeDashArray: 4 };

export const PALETTE = ['#38bdf8', '#818cf8', '#2dd4bf', '#f472b6', '#facc15', '#fb923c', '#a78bfa', '#4ade80', '#f87171', '#22d3ee'];

/** 120000 -> "120k", 850 -> "850" */
export const compactNumber = (v: number): string =>
  Math.abs(v) >= 1000 ? `${Math.round(v / 1000)}k` : `${Math.round(v)}`;

