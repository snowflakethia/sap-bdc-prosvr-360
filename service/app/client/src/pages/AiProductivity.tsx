import { Card, EChart, Grid, Kpi, PageFrame, Table, WithData, bars, ciChart, fmt, usePage, type Tone } from '@/components/ui';

/** Green only for a significant positive effect, red for a significant negative one. */
const effectTone = (r: any, k = 'uplift'): Tone => (!r?.significant ? 'neutral' : Number(r[k]) > 0 ? 'good' : 'bad');

export default function AiProductivity() {
  const q = usePage('ai');
  return (
    <PageFrame id="P6" title="AI Productivity & Learning Payback" ask="ai"
      subtitle="Does AI skill and actual AI use make people faster at the same level and work type? Does learning pay back? Every effect is shown with its 90 % confidence interval."
      suggestions={['Is the AI productivity effect real?', 'Should I keep funding the AI curriculum?']}>
      <WithData q={q}>
        {(d) => {
          const t = d.ai_test;
          const active = t.filter((r) => r.ai_band === 'AI_ACTIVE');
          const inactive = t.filter((r) => r.ai_band === 'SKILLED_INACTIVE');
          const allA = active.find((r) => r.stratum === 'ALL LEVELS');
          const allI = inactive.find((r) => r.stratum === 'ALL LEVELS');
          const sig = (r: any) => (r ? (r.significant ? 'significant' : 'no significant effect (CI spans zero)') : '');
          const tools = [...new Set(d.ai_cost.map((r) => r.ai_tool_id))];
          const years = [...new Set(d.ai_cost.map((r) => r.fiscal_year))].sort();
          return (
            <>
              <Grid cols={4}>
                <Kpi label="AI-active uplift" value={allA ? fmt.signedPct(allA.uplift) : '-'} tone={effectTone(allA)}
                  sub={allA ? `CI [${fmt.signedPct(allA.ci_low)}, ${fmt.signedPct(allA.ci_high)}] - ${sig(allA)}` : undefined} />
                <Kpi label="AI-skilled but inactive" value={allI ? fmt.signedPct(allI.uplift) : '-'} tone={effectTone(allI)}
                  sub={allI ? `CI [${fmt.signedPct(allI.ci_low)}, ${fmt.signedPct(allI.ci_high)}] - ${sig(allI)}` : undefined} />
                {d.ai_payback.map((r) => (
                  <Kpi key={r.curriculum} label={`Learning payback - ${r.curriculum}`} value={fmt.signedPct(r.payback)} tone={effectTone(r, 'payback')}
                    sub={`CI [${fmt.signedPct(r.ci_low)}, ${fmt.signedPct(r.ci_high)}] - ${r.episodes} episodes - ${sig(r)}`} />
                ))}
              </Grid>
              <Grid cols={2}>
                <Card title="Productivity uplift vs not AI-active, by level" subtitle="Same level and work type; point = estimate, band = bootstrap 90 % CI; the red line is zero">
                  <EChart height={Math.max(220, 34 * t.length)} option={ciChart(
                    t.map((r) => `${r.stratum} - ${r.ai_band === 'AI_ACTIVE' ? 'AI-active' : 'skilled, inactive'}`),
                    t.map((r) => r.uplift), t.map((r) => r.ci_low), t.map((r) => r.ci_high))} />
                </Card>
                <Card title="Learning payback by curriculum" subtitle="Productivity after vs before the course, against a matched group">
                  <EChart height={220} option={ciChart(d.ai_payback.map((r) => r.curriculum), d.ai_payback.map((r) => r.payback), d.ai_payback.map((r) => r.ci_low), d.ai_payback.map((r) => r.ci_high))} />
                  <p className="mt-2 text-xs text-gray-500">Hours saved by learning (ESTIMATED): {d.ai_payback.map((r) => `${r.curriculum} ${fmt.num(r.hours_saved)}`).join(' - ')}</p>
                </Card>
              </Grid>
              <Grid cols={2}>
                <Card title="Adoption S-curve" subtitle="Share of delivery people active on AI tools">
                  <EChart height={260} option={bars(d.ai_adoption.map((r) => fmt.fy(r.fiscal_year)), [
                    { name: 'AI-active %', data: d.ai_adoption.map((r) => r.ai_active_pct) },
                  ], { unit: 'pct' })} />
                </Card>
                <Card title="AI cost by vendor / agent" subtitle="Assistant spend plus agent cost charged to projects">
                  <EChart height={260} option={bars(years.map(fmt.fy), tools.map((tl) => ({
                    name: tl, stack: 'cost', data: years.map((y) => d.ai_cost.filter((r) => r.fiscal_year === y && r.ai_tool_id === tl).reduce((s, r) => s + Number(r.cost_usd), 0)),
                  })), { unit: 'usd' })} />
                </Card>
              </Grid>
              <Grid cols={2}>
                <Card title="Margin and CPI by delivery model" subtitle="Projects active in the last year of the range">
                  <Table rows={d.ai_delivery_model} cols={[
                    { key: 'delivery_model', label: 'Delivery model' }, { key: 'projects', label: 'Projects', align: 'right' },
                    { key: 'revenue', label: 'Revenue', format: fmt.usd, align: 'right' }, { key: 'margin_pct', label: 'Margin', format: fmt.pct, align: 'right' },
                    { key: 'median_cpi', label: 'Median CPI', format: fmt.ratio, align: 'right' },
                  ]} />
                </Card>
                <Card title="AI-skilled but inactive (latest quarter)" subtitle="AI-skill 3+ and no AI tool use - the cheapest uplift to unlock">
                  <Table max={300} rows={d.ai_inactive} cols={[
                    { key: 'display_name', label: 'Person' }, { key: 'level', label: 'Level' }, { key: 'ai_skill_level', label: 'AI skill', align: 'right' },
                    { key: 'delivery_hours', label: 'Delivery h', format: fmt.num, align: 'right' },
                    { key: 'productivity_index', label: 'Productivity', format: fmt.ratio, align: 'right' },
                  ]} />
                </Card>
              </Grid>
            </>
          );
        }}
      </WithData>
    </PageFrame>
  );
}
