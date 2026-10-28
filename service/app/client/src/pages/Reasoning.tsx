import { Card, EChart, Grid, PageFrame, Table, WithData, bars, fmt, lines, usePage } from '@/components/ui';

export default function Reasoning({ openProject }: { openProject: (id: string) => void }) {
  const q = usePage('reasoning');
  return (
    <PageFrame id="P7" title="Context & Reasoning" ask="reasoning"
      subtitle="What Snowflake adds as a System of Context and Reasoning (PRD 9): live tiles from the REASONING layer, served through SERVING views."
      suggestions={['Who on the bench should I put on which bid?', 'Where is margin leaking?']}>
      <WithData q={q}>
        {(d) => {
          const fc = d.rs_forecast;
          const months = [...new Set(fc.map((r) => String(r.month_start).slice(0, 7)))].sort();
          const fams = [...new Set(fc.map((r) => r.skill_family))];
          return (
            <>
              <Grid cols={2}>
                <Card title="Bench-to-pipeline match" info="bench_match" subtitle="AI_EMBED + VECTOR_COSINE_SIMILARITY of people's skills vs bid requirements, weighted by coverage and AI level">
                  <Table rows={d.rs_bench} cols={[
                    { key: 'display_name', label: 'Person' }, { key: 'level', label: 'Level' }, { key: 'roll_off_date', label: 'Free from', format: fmt.date },
                    { key: 'opportunity_id', label: 'Best bid' }, { key: 'work_type', label: 'Work type' },
                    { key: 'match_score', label: 'Match', format: fmt.ratio, align: 'right' }, { key: 'meets_ai_level', label: 'AI level met', format: fmt.bool },
                  ]} />
                </Card>
                <Card title="Demand forecast by skill family" info="demand_forecast" subtitle="SNOWFLAKE.ML.FORECAST over pipeline-weighted skill hours">
                  <EChart height={300} option={lines(months, fams.flatMap((f, i) => (['ACTUAL', 'FORECAST'] as const).map((t) => ({
                    name: t === 'ACTUAL' ? f : `${f} forecast`, dashed: t === 'FORECAST', color: ['#7D44CF', '#11567F', '#FF9F36'][i % 3],
                    data: months.map((m) => fc.find((r) => r.skill_family === f && r.series_type === t && String(r.month_start).startsWith(m))?.demand_hours ?? null),
                  }))), { unit: 'num' })} />
                </Card>
              </Grid>
              <Grid cols={2}>
                <Card title="Margin-leak detector" info="margin_leak" subtitle="Projects whose forecast ends in a loss; click to drill into P2">
                  <Table rows={d.rs_margin_leak} onRow={(r) => openProject(r.project_id)} cols={[
                    { key: 'project_id', label: 'Project' }, { key: 'md_group_id', label: 'Business Group' }, { key: 'detail', label: 'Detail' },
                    { key: 'usd_at_stake', label: 'USD at stake', format: fmt.usd, align: 'right' },
                  ]} />
                </Card>
                <Card title="Attrition risk by decile" info="attrition_decile" subtitle="SNOWFLAKE.ML.CLASSIFICATION scores, active people">
                  <EChart height={260} option={bars(d.rs_attrition.map((r) => `D${r.risk_decile}`), [
                    { name: 'Average risk %', data: d.rs_attrition.map((r) => 100 * Number(r.avg_risk)), color: '#D45B90' },
                  ], { unit: 'pct' })} />
                </Card>
              </Grid>
            </>
          );
        }}
      </WithData>
    </PageFrame>
  );
}
