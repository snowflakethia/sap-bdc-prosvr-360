import { Card, EChart, Grid, PageFrame, Table, WithData, bars, fmt, lines, usePage } from '@/components/ui';

const FAMILIES = ['AGENTIC_AI', 'TECHNICAL', 'INDUSTRY'];

export default function People() {
  const q = usePage('people');
  return (
    <PageFrame id="P4" title="People Intelligence" ask="people"
      subtitle="Headcount and attrition, who may leave next (Manager and above) and why, skills supply against forecast pipeline demand, and the AI curriculum that closes the gap."
      suggestions={['Which Managers are most at risk, and why?', 'Where is skills demand outrunning supply?']}>
      <WithData q={q}>
        {(d) => {
          const fc = d.pe_demand;
          const months = [...new Set(fc.map((r) => String(r.month_start).slice(0, 7)))].sort();
          const fam = FAMILIES.filter((f) => fc.some((r) => r.skill_family === f));
          const firstFc = fc.find((r) => r.series_type === 'FORECAST');
          return (
            <>
              <Grid cols={2}>
                <Card title="Headcount and voluntary attrition" subtitle="End-of-year headcount (bars) and attrition % (line)">
                  <EChart height={300} option={{
                    tooltip: { trigger: 'axis' }, legend: { top: 0 },
                    grid: { left: 10, right: 20, top: 36, bottom: 10, containLabel: true },
                    xAxis: { type: 'category', data: d.pe_headcount.map((r) => fmt.fy(r.fiscal_year)) },
                    yAxis: [{ type: 'value' }, { type: 'value', axisLabel: { formatter: '{value} %' }, splitLine: { show: false } }],
                    series: [
                      { type: 'bar', name: 'Headcount', data: d.pe_headcount.map((r) => Number(r.headcount_end)), itemStyle: { color: '#29B5E8' } },
                      { type: 'line', name: 'Attrition %', yAxisIndex: 1, data: d.pe_headcount.map((r) => Number(r.attrition_pct)), itemStyle: { color: '#D45B90' } },
                    ],
                  }} />
                </Card>
                <Card title="Pipeline demand by skill family" subtitle="Actual and SNOWFLAKE.ML.FORECAST hours per month (dashed = forecast)">
                  <EChart height={300} option={lines(months, fam.flatMap((f, i) => [
                    { name: `${f}`, data: months.map((m) => fc.find((r) => r.skill_family === f && String(r.month_start).startsWith(m) && r.series_type === 'ACTUAL')?.demand_hours ?? null), color: ['#7D44CF', '#11567F', '#FF9F36'][i] },
                    { name: `${f} forecast`, dashed: true, data: months.map((m) => fc.find((r) => r.skill_family === f && String(r.month_start).startsWith(m) && r.series_type === 'FORECAST')?.demand_hours ?? null), color: ['#7D44CF', '#11567F', '#FF9F36'][i] },
                  ]), { unit: 'num', markX: firstFc ? { label: 'forecast', at: String(firstFc.month_start).slice(0, 7) } : undefined })} />
                </Card>
              </Grid>
              <Grid cols={2}>
                <Card title="Skills supply" subtitle="Active people at proficiency 3 or more, by skill family">
                  <EChart height={240} option={bars(d.pe_supply.map((r) => r.skill_family), [{ name: 'People at 3+', data: d.pe_supply.map((r) => r.people_at_3_plus) }], { horizontal: true })} />
                </Card>
                <Card title="AI curriculum for the gap" subtitle="Learning items in the Agentic-AI curriculum">
                  <Table max={260} rows={d.pe_curriculum} cols={[
                    { key: 'learning_item_title', label: 'Course' }, { key: 'target_skill_id', label: 'Skill' },
                    { key: 'target_proficiency_level', label: 'Target level', align: 'right' }, { key: 'learning_hours', label: 'Hours', align: 'right' },
                  ]} />
                </Card>
              </Grid>
              <Card title="Attrition risk - Manager and above (top 25)" subtitle="SNOWFLAKE.ML.CLASSIFICATION; drivers are the features furthest from the group norm. Within the simulated pool the model separates weakly (AUC ~0.57) - treat as a ranking, not a prediction.">
                <Table rows={d.pe_risk} cols={[
                  { key: 'display_name', label: 'Person' }, { key: 'level', label: 'Level' }, { key: 'md_group_id', label: 'Group' },
                  { key: 'attrition_risk', label: 'Risk', format: (v) => fmt.pct(100 * Number(v)), align: 'right' }, { key: 'risk_decile', label: 'Decile', align: 'right' },
                  { key: 'tenure_months', label: 'Tenure (mo)', align: 'right' }, { key: 'performance_rating', label: 'Rating', align: 'right' },
                  { key: 'compa_ratio', label: 'Compa-ratio', format: fmt.ratio, align: 'right' }, { key: 'top_drivers', label: 'Top drivers' },
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
