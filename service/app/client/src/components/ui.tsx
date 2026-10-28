import type { ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import Chart from '@/components/Chart';
import AskCortex from '@/components/AskCortex';
import { useFilters } from '@/hooks/useFilters';
import { useQuery } from '@/hooks/useQuery';
import { getPage, type PageData, type Rows } from '@/lib/api';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------
const n = (v: any) => (v === null || v === undefined || v === '' ? NaN : Number(v));
export const fmt = {
  usd: (v: any) => {
    const x = n(v);
    if (Number.isNaN(x)) return '-';
    const a = Math.abs(x);
    return `${x < 0 ? '-' : ''}$${a >= 1e9 ? (a / 1e9).toFixed(2) + 'B' : a >= 1e6 ? (a / 1e6).toFixed(1) + 'M' : a >= 1e3 ? (a / 1e3).toFixed(0) + 'K' : a.toFixed(0)}`;
  },
  pct: (v: any) => (Number.isNaN(n(v)) ? '-' : `${n(v).toFixed(1)} %`),
  ratio: (v: any) => (Number.isNaN(n(v)) ? '-' : n(v).toFixed(2)),
  num: (v: any) => (Number.isNaN(n(v)) ? '-' : n(v).toLocaleString('en-US', { maximumFractionDigits: 1 })),
  signedPct: (v: any) => (Number.isNaN(n(v)) ? '-' : `${n(v) >= 0 ? '+' : ''}${(100 * n(v)).toFixed(1)} %`),
  date: (v: any) => (v ? String(v).slice(0, 10) : '-'),
  bool: (v: any) => (v === true || v === 'true' ? 'Yes' : v === false || v === 'false' ? 'No' : '-'),
  fy: (v: any) => `FY${String(v).slice(-2)}`,
  text: (v: any) => (v === null || v === undefined ? '-' : String(v)),
};
export const num = n;
export const COLORS = ['#29B5E8', '#11567F', '#FF9F36', '#7D44CF', '#D45B90', '#71D3F7', '#5B8C5A', '#8A8D91'];
export const TIME_COLORS: Record<string, string> = {
  Delivery: '#11567F', Bid: '#29B5E8', Learning: '#7D44CF', Admin: '#FF9F36', Bench: '#D45B90',
};

// ---------------------------------------------------------------------------
// Page data
// ---------------------------------------------------------------------------
/** Fetch a page's registry results for the current filters (refetches when filters change). */
export function usePage(path: string, extra: Record<string, string> = {}) {
  const { filters } = useFilters();
  return useQuery<PageData>(() => getPage(path, filters, extra), [path, filters.group, filters.fy0, filters.fy1, filters.size, JSON.stringify(extra)]);
}

export function scopeLabel(group: string, groups: Rows) {
  if (group === 'ALL') return 'Firm-wide';
  return String(groups.find((g) => g.md_group_id === group)?.md_group_name ?? group);
}

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------
export function PageFrame({ id, title, subtitle, ask, askArgs, suggestions, children }: {
  id: string; title: string; subtitle?: ReactNode; ask?: string; askArgs?: Record<string, string>;
  suggestions?: string[]; children: ReactNode;
}) {
  const { filters, groups } = useFilters();
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-sf-primary">{id}</p>
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          {subtitle && <p className="mt-1 max-w-4xl text-sm text-gray-500">{subtitle}</p>}
          <p className="mt-1 text-xs text-gray-400">
            {scopeLabel(filters.group, groups)} - FY{filters.fy0 % 100}-FY{filters.fy1 % 100} - as of 1 Oct 2026
          </p>
        </div>
      </div>
      {ask && (
        <AskCortex topic={ask} args={{ group: filters.group, fy0: String(filters.fy0), fy1: String(filters.fy1), size: filters.size, ...askArgs }}
          suggestions={suggestions ?? []} />
      )}
      {children}
    </div>
  );
}

export function Loading({ what = 'Loading live data from Snowflake' }: { what?: string }) {
  return <p className="flex items-center gap-2 py-10 text-sm text-gray-500"><Loader2 className="h-4 w-4 animate-spin" /> {what}…</p>;
}

export function ErrorBox({ error }: { error: string }) {
  return <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</p>;
}

/** Render children once the page data has arrived. */
export function WithData({ q, children }: { q: { data: PageData | null; loading: boolean; error: string | null }; children: (d: PageData) => ReactNode }) {
  if (q.error) return <ErrorBox error={q.error} />;
  if (q.loading || !q.data) return <Loading />;
  return <>{children(q.data)}</>;
}

export function Grid({ cols = 3, children }: { cols?: number; children: ReactNode }) {
  const c = { 1: 'lg:grid-cols-1', 2: 'lg:grid-cols-2', 3: 'lg:grid-cols-3', 4: 'lg:grid-cols-4', 5: 'lg:grid-cols-5' }[cols] ?? 'lg:grid-cols-3';
  return <div className={cn('grid grid-cols-1 gap-4 md:grid-cols-2', c)}>{children}</div>;
}

export function Card({ title, subtitle, children, className, right }: {
  title: string; subtitle?: ReactNode; children: ReactNode; className?: string; right?: ReactNode;
}) {
  return (
    <div className={cn('rounded-xl border border-gray-200 bg-white p-5 shadow-sm', className)}>
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <h3 className="text-base font-bold text-gray-900">{title}</h3>
          {subtitle && <p className="mt-0.5 text-xs text-gray-500">{subtitle}</p>}
        </div>
        {right}
      </div>
      {children}
    </div>
  );
}

export type Tone = 'good' | 'bad' | 'neutral';
export function Kpi({ label, value, sub, tone = 'neutral' }: { label: string; value: string; sub?: ReactNode; tone?: Tone }) {
  return (
    <div className={cn('rounded-xl border p-4 shadow-sm',
      tone === 'good' ? 'border-emerald-200 bg-emerald-50/60' : tone === 'bad' ? 'border-rose-200 bg-rose-50/60' : 'border-sf-primary/30 bg-gradient-to-br from-blue-50 to-sky-50')}>
      <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">{label}</p>
      <p className="mt-1.5 text-2xl font-extrabold text-gray-900">{value}</p>
      {sub && <p className="mt-1 text-xs text-gray-500">{sub}</p>}
    </div>
  );
}

/** "FY26 vs FY25" delta line; higherIsBetter decides the tone. */
export function delta(cur: any, prev: any, kind: 'pct' | 'usd' | 'ratio' | 'pts' | 'num', higherIsBetter = true): { sub: string; tone: Tone } {
  const c = n(cur), p = n(prev);
  if (Number.isNaN(c) || Number.isNaN(p)) return { sub: '', tone: 'neutral' };
  const d = c - p;
  const txt = kind === 'usd' ? fmt.usd(d) : kind === 'num' ? fmt.num(d) : kind === 'ratio' ? d.toFixed(3) : `${d.toFixed(1)} pts`;
  const tone: Tone = Math.abs(d) < 1e-9 ? 'neutral' : (d > 0) === higherIsBetter ? 'good' : 'bad';
  return { sub: `${d >= 0 ? '+' : ''}${txt} vs prior year`, tone };
}

// ---------------------------------------------------------------------------
// Tables
// ---------------------------------------------------------------------------
export interface Col { key: string; label: string; format?: (v: any, row: Record<string, any>) => ReactNode; align?: 'right' }

export function Table({ cols, rows, onRow, max = 400, highlight }: {
  cols: Col[]; rows: Rows; onRow?: (r: Record<string, any>) => void; max?: number; highlight?: (r: Record<string, any>) => boolean;
}) {
  if (!rows?.length) return <p className="py-4 text-center text-sm text-gray-400">No rows</p>;
  return (
    <div className="overflow-auto rounded-lg border border-gray-200" style={{ maxHeight: max }}>
      <table className="min-w-full text-xs">
        <thead className="sticky top-0">
          <tr className="bg-sf-dark text-white">
            {cols.map((c) => <th key={c.key} className={cn('whitespace-nowrap px-3 py-2 font-medium', c.align === 'right' ? 'text-right' : 'text-left')}>{c.label}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} onClick={onRow ? () => onRow(r) : undefined}
              className={cn(i % 2 ? 'bg-sky-50/50' : 'bg-white', onRow && 'cursor-pointer hover:bg-sky-100', highlight?.(r) && 'font-semibold text-rose-700')}>
              {cols.map((c) => (
                <td key={c.key} className={cn('px-3 py-1.5 text-gray-700', c.align === 'right' && 'text-right tabular-nums')}>
                  {c.format ? c.format(r[c.key], r) : fmt.text(r[c.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Charts (ECharts option builders; category order is always the data order)
// ---------------------------------------------------------------------------
export function EChart({ option, height = 300, onClick }: { option: any; height?: number; onClick?: (p: any) => void }) {
  // No animation: options carry fresh formatter functions on every render, and a restarted grow-in animation
  // would leave bars invisible while a page re-renders (seen on P5).
  return <Chart option={{ animation: false, ...option }} keepOrder noPieConversion style={{ height }} onEvents={onClick ? { click: onClick } : undefined} />;
}

const axisPct = { type: 'value', axisLabel: { formatter: '{value} %' } };
const axisUsd = { type: 'value', axisLabel: { formatter: (v: number) => fmt.usd(v) } };

export function bars(categories: any[], series: { name: string; data: any[]; color?: string; stack?: string }[],
  opts: { unit?: 'pct' | 'usd' | 'num'; horizontal?: boolean; markLine?: { name: string; value: number }[] } = {}) {
  const valAxis = opts.unit === 'pct' ? axisPct : opts.unit === 'usd' ? axisUsd : { type: 'value' };
  const catAxis = { type: 'category', data: categories, axisLabel: { interval: 0, rotate: categories.length > 8 && !opts.horizontal ? 30 : 0 } };
  return {
    tooltip: { trigger: 'axis', valueFormatter: (v: any) => (opts.unit === 'pct' ? fmt.pct(v) : opts.unit === 'usd' ? fmt.usd(v) : fmt.num(v)) },
    legend: { top: 0 },
    grid: { left: 10, right: 20, top: 36, bottom: 10, containLabel: true },
    xAxis: opts.horizontal ? valAxis : catAxis,
    yAxis: opts.horizontal ? { ...catAxis, inverse: true } : valAxis,
    series: series.map((s, i) => ({
      type: 'bar', name: s.name, data: s.data.map(n), stack: s.stack, itemStyle: { color: s.color ?? COLORS[i % COLORS.length] },
      ...(i === 0 && opts.markLine ? { markLine: { symbol: 'none', data: opts.markLine.map((m) => ({ name: m.name, yAxis: m.value })), label: { formatter: '{b}' } } } : {}),
    })),
  };
}

export function lines(categories: any[], series: { name: string; data: any[]; color?: string; dashed?: boolean; area?: boolean; yAxisIndex?: number }[],
  opts: { unit?: 'pct' | 'usd' | 'num'; unit2?: 'pct' | 'usd' | 'num'; markX?: { label: string; at: any } } = {}) {
  const ax = (u?: string) => (u === 'pct' ? axisPct : u === 'usd' ? axisUsd : { type: 'value' });
  return {
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 10, right: 20, top: 36, bottom: 10, containLabel: true },
    xAxis: { type: 'category', data: categories, boundaryGap: false },
    yAxis: opts.unit2 ? [ax(opts.unit), { ...ax(opts.unit2), splitLine: { show: false } }] : ax(opts.unit),
    series: series.map((s, i) => ({
      type: 'line', name: s.name, data: s.data.map(n), smooth: true, showSymbol: false, yAxisIndex: s.yAxisIndex ?? 0,
      lineStyle: { type: s.dashed ? 'dashed' : 'solid', color: s.color ?? COLORS[i % COLORS.length] },
      itemStyle: { color: s.color ?? COLORS[i % COLORS.length] },
      areaStyle: s.area ? { opacity: 0.12 } : undefined,
      ...(i === 0 && opts.markX ? { markLine: { symbol: 'none', data: [{ xAxis: opts.markX.at, name: opts.markX.label }], label: { formatter: '{b}' }, lineStyle: { color: '#888' } } } : {}),
    })),
  };
}

/** Point estimate with its 90 % confidence interval, one row per stratum. */
export function ciChart(labels: string[], est: any[], lo: any[], hi: any[], unitPct = true) {
  const k = unitPct ? 100 : 1;
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (ps: any[]) => {
        const i = ps[0].dataIndex;
        return `${labels[i]}<br/>estimate ${(k * n(est[i])).toFixed(1)} %<br/>90 % CI [${(k * n(lo[i])).toFixed(1)}, ${(k * n(hi[i])).toFixed(1)}]`;
      },
    },
    grid: { left: 10, right: 30, top: 10, bottom: 10, containLabel: true },
    yAxis: { type: 'category', data: labels, inverse: true },
    xAxis: { type: 'value', axisLabel: { formatter: '{value} %' } },
    series: [
      {
        // The interval [lo, hi] as a rectangle (stacked bars cannot span zero).
        type: 'custom',
        renderItem: (_p: any, api: any) => {
          const a = api.coord([api.value(0), api.value(2)]);
          const b = api.coord([api.value(1), api.value(2)]);
          return { type: 'rect', shape: { x: a[0], y: a[1] - 7, width: Math.max(2, b[0] - a[0]), height: 14 }, style: { fill: 'rgba(41,181,232,0.35)' } };
        },
        encode: { x: [0, 1], y: 2 },
        data: lo.map((v, i) => [k * n(v), k * n(hi[i]), i]),
        silent: true,
      },
      { type: 'scatter', data: est.map((v, i) => [k * n(v), i]), itemStyle: { color: '#11567F' }, symbolSize: 10,
        markLine: { symbol: 'none', data: [{ xAxis: 0 }], lineStyle: { color: '#D45B90' }, label: { show: false } } },
    ],
  };
}
