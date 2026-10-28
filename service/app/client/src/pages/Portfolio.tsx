import { useFilters } from '@/hooks/useFilters';
import { Card, EChart, Grid, PageFrame, Table, WithData, bars, fmt, usePage } from '@/components/ui';

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
                <Card title="Revenue by size class" subtitle="Per fiscal year, from SV_PROJECT_DELIVERY">
                  <EChart height={320} option={bars(years.map(fmt.fy), sizes.map((s) => ({
                    name: s, stack: 'rev', data: years.map((y) => d.pf_size.find((r) => r.fiscal_year === y && r.size_class === s)?.total_revenue ?? 0),
                  })), { unit: 'usd' })} />
                </Card>
                <Card title={`Pareto of project revenue, ${fmt.fy(filters.fy1)}`}
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
              <Card title="Fixed-price projects below 10 % forecast margin" subtitle="Active projects; click a row to open Project Health (P2)">
                <Table rows={d.pf_fp_watch} onRow={(r) => openProject(r.project_id)} highlight={(r) => r.is_story_project} cols={[
                  { key: 'project_id', label: 'Project' }, { key: 'customer_name', label: 'Customer' }, { key: 'md_group_id', label: 'Group' },
                  { key: 'size_class', label: 'Size' }, { key: 'contract_value', label: 'Contract', format: fmt.usd, align: 'right' },
                  { key: 'cpi', label: 'CPI', format: fmt.ratio, align: 'right' }, { key: 'spi', label: 'SPI', format: fmt.ratio, align: 'right' },
                  { key: 'eac', label: 'EAC', format: fmt.usd, align: 'right' },
                  { key: 'forecast_margin_pct', label: 'Forecast margin', format: fmt.pct, align: 'right' },
                  { key: 'ld_exposure', label: 'LD exposure', format: fmt.usd, align: 'right' },
                ]} />
              </Card>
            </>
          );
        }}
      </WithData>
    </PageFrame>
  );
}
