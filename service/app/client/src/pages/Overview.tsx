import type { Navigate } from '@/App';
import { Card, EChart, Grid, Kpi, PageFrame, TIME_COLORS, Table, WithData, bars, delta, fmt, lines, num, usePage } from '@/components/ui';

const CATS = ['Delivery', 'Bid', 'Learning', 'Admin', 'Bench'] as const;
const key = (c: string) => c.toLowerCase();

export default function Overview({ nav, openProject }: { nav: Navigate; openProject: (id: string) => void }) {
  const q = usePage('overview');
  return (
    <PageFrame id="P0" title="ProServe360 Overview" ask="overview"
      subtitle="The three pillars FY-over-FY, how the group's time is used against the target by level, and the top cross-pillar risks."
      suggestions={['What are the top three risks and what do I do first?', 'Is our time mix on target by level?']}>
      <WithData q={q}>
        {(d) => {
          const sc = d.ov_scorecard;
          const cur = sc[sc.length - 1] ?? {};
          const prev = sc[sc.length - 2] ?? {};
          const fy = fmt.fy(cur.fiscal_year), pfy = fmt.fy(prev.fiscal_year);
          const ot = d.ov_on_time[0] ?? {};
          const ai = d.ov_ai_uplift.find((r) => r.ai_band === 'AI_ACTIVE');
          const k = (label: string, f: string, kind: 'pct' | 'usd' | 'ratio' | 'pts' | 'num', hib: boolean, show: (v: any) => string) => {
            const dl = delta(cur[f], prev[f], kind, hib);
            return <Kpi label={`${label} ${fy}`} value={show(cur[f])} sub={dl.sub ? `${dl.sub.replace('prior year', pfy)}` : undefined} tone={dl.tone} />;
          };
          const tm = d.ov_time_mix;
          return (
            <>
              <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
                <Card title="Operational Excellence" subtitle="Deliver what was sold at the sold margin">
                  <div className="grid grid-cols-2 gap-3">
                    {k('Margin', 'margin_pct', 'pts', true, fmt.pct)}
                    <Kpi label="On-time (active)" value={fmt.pct(ot.on_time_pct)} sub={`${ot.active_projects} active projects, no forecast slip`} />
                    {k('Asset reuse rate', 'reuse_rate_pct', 'pts', true, fmt.pct)}
                    {k('Revenue', 'revenue', 'usd', true, fmt.usd)}
                  </div>
                </Card>
                <Card title="Value Creation" subtitle="Win the right work">
                  <div className="grid grid-cols-2 gap-3">
                    {k('Win-rate', 'win_rate_pct', 'pts', true, fmt.pct)}
                    {k('Pursuit cost / won USD', 'pursuit_cost_per_won_usd', 'ratio', false, (v) => `$${num(v).toFixed(3)}`)}
                    <Kpi label={`Book-to-bill ${fy}`} value={fmt.ratio(num(cur.won_value) / num(cur.revenue))} sub={`won ${fmt.usd(cur.won_value)}`} />
                    {k('Won value', 'won_value', 'usd', true, fmt.usd)}
                  </div>
                </Card>
                <Card title="People Development" subtitle="The right people, skills and time mix">
                  <div className="grid grid-cols-2 gap-3">
                    {k('Delivery share', 'delivery_pct', 'pts', true, fmt.pct)}
                    {k('Bench cost', 'bench_cost', 'usd', false, fmt.usd)}
                    {k('Admin share', 'admin_pct', 'pts', false, fmt.pct)}
                    {k('Voluntary attrition', 'attrition_pct', 'pts', false, fmt.pct)}
                    <Kpi label={`AI productivity uplift ${fy}`} value={ai ? fmt.signedPct(ai.uplift) : '-'}
                      sub={ai ? `90 % CI [${fmt.signedPct(ai.ci_low)}, ${fmt.signedPct(ai.ci_high)}] - ${ai.significant ? 'significant' : 'no significant effect'}` : undefined}
                      tone={ai?.significant ? 'good' : 'neutral'} />
                    {k('People (end of year)', 'headcount_end', 'num', true, fmt.num)}
                  </div>
                </Card>
              </div>

              <Grid cols={2}>
                <Card title={`Time mix by level, ${fy} - actual vs target`} subtitle="Share of available hours; each level's second bar is its target mix (PRD 2.1)">
                  <EChart height={340} option={{
                    ...bars(tm.flatMap((r) => [r.level, `${r.level} target`]),
                      CATS.map((c) => ({ name: c, stack: 'mix', color: TIME_COLORS[c],
                        data: tm.flatMap((r) => [r[`${key(c)}_pct`], r[`${key(c)}_target_pct`]]) })),
                      { unit: 'pct', horizontal: true }),
                  }} />
                </Card>
                <Card title="Revenue and margin, 60 months" subtitle="Monthly, from SV_PORTFOLIO_360; the rule marks the as-of date">
                  <EChart height={340} option={lines(d.ov_trend.map((r) => String(r.month_start).slice(0, 7)), [
                    { name: 'Revenue', data: d.ov_trend.map((r) => r.total_revenue), area: true },
                    { name: 'Margin %', data: d.ov_trend.map((r) => r.margin_pct), yAxisIndex: 1, color: '#FF9F36' },
                  ], { unit: 'usd', unit2: 'pct', markX: { label: 'As of 1 Oct 2026', at: String(d.ov_trend[d.ov_trend.length - 1]?.month_start ?? '').slice(0, 7) } })} />
                </Card>
              </Grid>

              <Card title="Top 5 cross-pillar risks" subtitle="From the risk register, by USD at stake; click a project risk to drill into P2">
                <Table rows={d.ov_risks} onRow={(r) => (r.object_entity === 'project' ? openProject(r.object_id) : r.object_entity === 'opportunity' ? nav('p5') : nav('p3'))} cols={[
                  { key: 'pillar', label: 'Pillar' }, { key: 'risk_type', label: 'Risk' }, { key: 'object_id', label: 'Object' },
                  { key: 'detail', label: 'Detail' }, { key: 'usd_at_stake', label: 'USD at stake', format: fmt.usd, align: 'right' },
                ]} />
              </Card>
              <TimeMixLegend />
            </>
          );
        }}
      </WithData>
    </PageFrame>
  );
}

function TimeMixLegend() {
  return (
    <p className="text-xs text-gray-400">
      Objectives: Delivery - maximise; Bid - raise the win-rate, not the hours; Learning - shorten future delivery; Admin - below 5 %; Bench - towards the ~2 % structural transition.
    </p>
  );
}
