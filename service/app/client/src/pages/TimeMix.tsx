import { Card, EChart, Grid, PageFrame, TIME_COLORS, Table, WithData, bars, fmt, lines, usePage } from '@/components/ui';

const CATS = ['Delivery', 'Bid', 'Learning', 'Admin', 'Bench'] as const;

export default function TimeMix() {
  const q = usePage('workforce');
  return (
    <PageFrame id="P3" title="Time Mix & Bench" ask="workforce"
      subtitle="The five uses of time by level against target, excess bench (above the 2 % allowance) cost, admin against its 5 % ceiling, and who rolls off in the next 90 days."
      suggestions={['Which level is furthest from its time target?', 'Who rolls off below the AI level the pipeline needs?']}>
      <WithData q={q}>
        {(d) => {
          const tm = d.wf_time_mix;
          const bm = d.wf_bench_month;
          const months = bm.map((r) => String(r.month_start).slice(0, 7));
          return (
            <>
              <Grid cols={2}>
                <Card title="Time mix by level vs target" subtitle="Actual (bars) vs target (markers), share of available hours, last year in the range">
                  <EChart height={340} option={{
                    ...bars(tm.map((r) => r.level), CATS.map((c) => ({ name: c, color: TIME_COLORS[c], data: tm.map((r) => r[`${c.toLowerCase()}_pct`]) })), { unit: 'pct' }),
                    series: [
                      ...CATS.map((c) => ({ type: 'bar', name: c, data: tm.map((r) => Number(r[`${c.toLowerCase()}_pct`])), itemStyle: { color: TIME_COLORS[c] } })),
                      ...CATS.map((c) => ({ type: 'scatter', name: `${c} target`, symbol: 'rect', symbolSize: [16, 3], data: tm.map((r) => Number(r[`${c.toLowerCase()}_target_pct`])), itemStyle: { color: '#111' }, tooltip: { valueFormatter: (v: any) => fmt.pct(v) } })),
                    ],
                    legend: { top: 0, data: [...CATS] },
                  }} />
                </Card>
                <Card title="Five-way mix over the years" subtitle="Share of available hours">
                  <EChart height={340} option={bars(d.wf_mix_trend.map((r) => fmt.fy(r.fiscal_year)),
                    CATS.map((c) => ({ name: c, stack: 'mix', color: TIME_COLORS[c], data: d.wf_mix_trend.map((r) => r[`${c.toLowerCase()}_pct`]) })), { unit: 'pct' })} />
                </Card>
              </Grid>
              <Grid cols={2}>
                <Card title="Excess bench cost by month" subtitle="Cost of bench hours above the ~2 % structural allowance">
                  <EChart height={280} option={bars(months, [
                    { name: 'Excess bench cost', data: bm.map((r) => r.excess_bench_cost), color: '#D45B90' },
                    { name: 'Total bench cost', data: bm.map((r) => r.bench_cost), color: '#F4B8CF' },
                  ], { unit: 'usd' })} />
                </Card>
                <Card title="Bench and admin share by month" subtitle="Admin ceiling 5 %, bench allowance 2 %">
                  <EChart height={280} option={{
                    ...lines(months, [
                      { name: 'Admin %', data: bm.map((r) => r.admin_pct), color: '#FF9F36' },
                      { name: 'Bench %', data: bm.map((r) => r.bench_pct), color: '#D45B90' },
                    ], { unit: 'pct' }),
                    series: [
                      { type: 'line', name: 'Admin %', data: bm.map((r) => Number(r.admin_pct)), showSymbol: false, itemStyle: { color: '#FF9F36' },
                        markLine: { symbol: 'none', data: [{ yAxis: 5, name: 'Admin ceiling 5 %' }, { yAxis: 2, name: 'Bench allowance 2 %' }], label: { formatter: '{b}' }, lineStyle: { type: 'dashed' } } },
                      { type: 'line', name: 'Bench %', data: bm.map((r) => Number(r.bench_pct)), showSymbol: false, itemStyle: { color: '#D45B90' } },
                    ],
                  }} />
                </Card>
              </Grid>
              <Card title={`Rolling off in the next 90 days (${d.wf_roll_off.length})`} subtitle="Bold red = below the AI-skill level the open pipeline needs; SOURCE_SYSTEM shows real People Intelligence rows">
                <Table rows={d.wf_roll_off} highlight={(r) => r.below_pipeline_ai_level} cols={[
                  { key: 'display_name', label: 'Person' }, { key: 'level', label: 'Level' }, { key: 'project_id', label: 'Project' },
                  { key: 'roll_off_date', label: 'Roll-off', format: fmt.date }, { key: 'days_to_roll_off', label: 'Days', align: 'right' },
                  { key: 'ai_skill_level', label: 'AI skill', align: 'right' }, { key: 'pipeline_required_ai_level', label: 'Pipeline needs', align: 'right' },
                  { key: 'source_system', label: 'Source' },
                ]} />
              </Card>
            </>
          );
        }}
      </WithData>
    </PageFrame>
  );
}
