import { useState } from 'react';
import { useFilters } from '@/hooks/useFilters';
import { Card, EChart, Grid, PageFrame, Table, WithData, bars, fmt, num, usePage, type Col } from '@/components/ui';
import type { Rows } from '@/lib/api';

const SIZES = ['XX-Small', 'X-Small', 'Small', 'Medium', 'Large'];

export default function Portfolio({ openProject }: { openProject: (id: string) => void }) {
  const q = usePage('portfolio');
  const { filters } = useFilters();
  return (
    <PageFrame id="P1" title="Portfolio & Pareto" ask="portfolio"
      subtitle="Where revenue comes from by project size, how concentrated it is, and which fixed-price projects are below 10 % forecast margin."
      suggestions={['How concentrated is our revenue?', 'Which fixed-price project needs attention first?']}>
      <WithData q={q}>
        {(d) => {
          const years = [...new Set(d.pf_size.map((r) => r.fiscal_year))].sort();
          const sizes = SIZES.filter((s) => d.pf_size.some((r) => r.size_class === s));
          const pareto = d.pf_pareto;
          const top20 = pareto[Math.max(0, Math.ceil(pareto.length * 0.2) - 1)];
          return (
            <>
              <Grid cols={2}>
                <Card title="Revenue by size class" info="revenue_by_size" subtitle="Per fiscal year, from SV_PROJECT_DELIVERY">
                  <EChart height={320} option={bars(years.map(fmt.fy), sizes.map((s) => ({
                    name: s, stack: 'rev', data: years.map((y) => d.pf_size.find((r) => r.fiscal_year === y && r.size_class === s)?.total_revenue ?? 0),
                  })), { unit: 'usd' })} />
                </Card>
                <Card title={`Pareto of project revenue, ${fmt.fy(filters.fy1)}`} info="pareto"
                  subtitle={top20 ? `The top 20 % of projects (${top20.rank_no}) earn ${fmt.pct(top20.cum_revenue_pct)} of revenue` : undefined}>
                  <EChart height={320} option={{
                    tooltip: { trigger: 'axis' }, legend: { top: 0 },
                    grid: { left: 10, right: 20, top: 36, bottom: 10, containLabel: true },
                    xAxis: { type: 'category', data: pareto.map((r) => r.project_id), axisLabel: { show: false } },
                    yAxis: [{ type: 'value', axisLabel: { formatter: (v: number) => fmt.usd(v) } }, { type: 'value', max: 100, axisLabel: { formatter: '{value} %' }, splitLine: { show: false } }],
                    series: [
                      { type: 'bar', name: 'Revenue', data: pareto.map((r) => Number(r.revenue)), itemStyle: { color: '#29B5E8' } },
                      { type: 'line', name: 'Cumulative %', yAxisIndex: 1, data: pareto.map((r) => Number(r.cum_revenue_pct)), showSymbol: false, itemStyle: { color: '#11567F' } },
                    ],
                  }} onClick={(p) => p.name && openProject(p.name)} />
                </Card>
              </Grid>
              <Card title="Fixed-price projects below 10 % forecast margin" info="fp_watch" subtitle="Active projects; click a row to open Project Health (P2)">
                <Table rows={d.pf_fp_watch} onRow={(r) => openProject(r.project_id)} highlight={(r) => r.is_story_project} cols={[
                  { key: 'project_id', label: 'Project' }, { key: 'customer_name', label: 'Customer' }, { key: 'md_group_id', label: 'Business Group' },
                  { key: 'size_class', label: 'Size' }, { key: 'contract_value', label: 'Contract', format: fmt.usd, align: 'right' },
                  { key: 'cpi', label: 'CPI', format: fmt.ratio, align: 'right' }, { key: 'spi', label: 'SPI', format: fmt.ratio, align: 'right' },
                  { key: 'eac', label: 'EAC', format: fmt.usd, align: 'right' },
                  { key: 'forecast_margin_pct', label: 'Forecast margin', format: fmt.pct, align: 'right' },
                  { key: 'ld_exposure', label: 'LD exposure', format: fmt.usd, align: 'right' },
                ]} />
              </Card>
              <PortfolioGroups rows={d.pf_portfolio} openProject={openProject} />
            </>
          );
        }}
      </WithData>
    </PageFrame>
  );
}

const RAG_STYLE: Record<string, string> = {
  RED: 'bg-rose-600 text-white', AMBER: 'bg-amber-500 text-white', GREEN: 'bg-emerald-600 text-white',
};
const rag = (v: any) => (
  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${RAG_STYLE[String(v)] ?? 'bg-gray-200 text-gray-600'}`}>
    {String(v ?? '-').replace('_', ' ')}
  </span>
);

const PROJECT_COLS: Col[] = [
  { key: 'project_id', label: 'Project' }, { key: 'customer_name', label: 'Customer' },
  { key: 'size_class', label: 'Size' }, { key: 'contract_type', label: 'Contract type' },
  { key: 'contract_value', label: 'Contract', format: fmt.usd, align: 'right' },
  { key: 'revenue', label: 'Revenue', format: fmt.usd, align: 'right' },
  { key: 'margin_pct', label: 'Margin', format: fmt.pct, align: 'right' },
  { key: 'cpi', label: 'CPI', format: fmt.ratio, align: 'right' }, { key: 'spi', label: 'SPI', format: fmt.ratio, align: 'right' },
  { key: 'forecast_margin_pct', label: 'Forecast margin', format: fmt.pct, align: 'right' },
  { key: 'rag', label: 'Status', format: rag },
];

/** Firm-wide portfolio: one row per Business Group, expandable to its projects (click a project for P2). */
function PortfolioGroups({ rows, openProject }: { rows: Rows; openProject: (id: string) => void }) {
  const { filters, groups } = useFilters();
  const [open, setOpen] = useState<Set<string>>(() => new Set(filters.group === 'ALL' ? [] : [filters.group]));
  const toggle = (g: string) => setOpen((o) => { const x = new Set(o); x.has(g) ? x.delete(g) : x.add(g); return x; });
  const projects: Rows = rows.map((r) => ({ ...r, margin_pct: num(r.revenue) ? (100 * num(r.margin)) / num(r.revenue) : null }));
  const byGroup = groups.map((g: Record<string, any>) => {
    const ps = projects.filter((r) => r.md_group_id === g.md_group_id);
    const revenue = ps.reduce((a, r) => a + num(r.revenue), 0);
    const margin = ps.reduce((a, r) => a + num(r.margin), 0);
    const count = (k: string) => ps.filter((r) => r.rag === k).length;
    return { ...g, md_group_id: g.md_group_id, md_group_name: g.md_group_name, managing_director_name: g.managing_director_name, ps, revenue, margin, active: ps.filter((r) => r.status_as_of === 'ACTIVE').length,
      red: count('RED'), amber: count('AMBER'), green: count('GREEN') };
  }).filter((g) => g.ps.length);
  const total = byGroup.reduce((a, g) => a + g.revenue, 0);
  const years = filters.fy0 === filters.fy1 ? fmt.fy(filters.fy1) : `${fmt.fy(filters.fy0)}-${fmt.fy(filters.fy1)}`;
  const th = 'whitespace-nowrap px-3 py-2 font-medium';
  return (
    <Card title="Portfolio by Business Group" info="portfolio_groups"
      subtitle={`All Business Groups, ${years}${filters.size === 'ALL' ? '' : `, ${filters.size}`}; expand a group, click a project to open Project Health (P2)`}>
      <div className="overflow-auto rounded-lg border border-gray-200">
        <table className="min-w-full text-xs">
          <thead><tr className="bg-sf-dark text-white">
            <th className={`${th} text-left`}>Business Group</th><th className={`${th} text-left`}>Managing Director</th>
            <th className={`${th} text-right`}>Projects</th><th className={`${th} text-right`}>Active</th>
            <th className={`${th} text-right`}>Revenue</th><th className={`${th} text-right`}>Share</th>
            <th className={`${th} text-right`}>Margin</th><th className={`${th} text-left`}>Active health</th>
          </tr></thead>
          <tbody>
            {byGroup.map((g) => {
              const isOpen = open.has(String(g.md_group_id));
              return [
                <tr key={String(g.md_group_id)} onClick={() => toggle(String(g.md_group_id))}
                  className={`cursor-pointer border-t border-gray-200 hover:bg-sky-100 ${g.md_group_id === filters.group ? 'bg-sky-50' : 'bg-white'}`}>
                  <td className="px-3 py-2 font-semibold text-gray-800">
                    <span className="mr-2 inline-block w-3 text-gray-400">{isOpen ? '\u25BE' : '\u25B8'}</span>{String(g.md_group_name)}
                  </td>
                  <td className="px-3 py-2 text-gray-600">{fmt.text(g.managing_director_name)}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{g.ps.length}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{g.active}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{fmt.usd(g.revenue)}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{fmt.pct(total ? (100 * g.revenue) / total : NaN)}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{fmt.pct(g.revenue ? (100 * g.margin) / g.revenue : NaN)}</td>
                  <td className="space-x-1 px-3 py-2">
                    {g.red > 0 && <span className="rounded bg-rose-100 px-1.5 text-rose-700">{g.red} red</span>}
                    {g.amber > 0 && <span className="rounded bg-amber-100 px-1.5 text-amber-700">{g.amber} amber</span>}
                    {g.green > 0 && <span className="rounded bg-emerald-100 px-1.5 text-emerald-700">{g.green} green</span>}
                  </td>
                </tr>,
                isOpen && (
                  <tr key={`${g.md_group_id}-projects`}><td colSpan={8} className="bg-gray-50 px-3 py-2">
                    <Table rows={g.ps} cols={PROJECT_COLS} onRow={(r) => openProject(r.project_id)} highlight={(r) => r.is_story_project} max={360} />
                  </td></tr>
                ),
              ];
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
