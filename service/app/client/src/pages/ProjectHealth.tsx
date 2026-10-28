import { useState } from 'react';
import type { Navigate } from '@/App';
import { useFilters } from '@/hooks/useFilters';
import { Card, EChart, Grid, Kpi, PageFrame, Table, WithData, bars, fmt, lines, num, usePage } from '@/components/ui';

export default function ProjectHealth({ nav }: { nav: Navigate }) {
  const { project, setProject } = useFilters();
  const q = usePage(`project/${project}`);
  const [why, setWhy] = useState(false);
  return (
    <PageFrame id="P2" title="Project Health" ask="project" askArgs={{ project }}
      subtitle="One project: contract, cost and schedule performance, plan vs actual, the critical path, the sold vs actual pyramid, why it is off plan, and the assets that fit."
      suggestions={['Why is this project losing margin?', 'What would recover the margin?']}>
      <WithData q={q}>
        {(d) => {
          const h = d.pj_header[0];
          if (!h) return <p className="text-sm text-gray-500">Project not found.</p>;
          const rag = String(h.rag);
          const m = d.pj_months;
          return (
            <>
              <div className="flex flex-wrap items-center gap-3">
                <select value={project} onChange={(e) => setProject(e.target.value)} className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm">
                  {[...d.pj_list, ...(d.pj_list.some((r) => r.project_id === project) ? [] : [{ project_id: project, customer_name: h.customer_name }])].map((r) => (
                    <option key={r.project_id} value={r.project_id}>{r.project_id} - {r.customer_name}{r.is_story_project ? ' (story)' : ''}</option>
                  ))}
                </select>
                <span className={`rounded-full px-3 py-1 text-xs font-bold text-white ${rag === 'RED' ? 'bg-rose-600' : rag === 'AMBER' ? 'bg-amber-500' : 'bg-emerald-600'}`}>{rag}</span>
                <span className="text-sm text-gray-600">{h.customer_name} - {h.md_group} - {h.size_class} {h.work_type} - {h.contract_type} - {h.delivery_model}</span>
              </div>
              <Grid cols={5}>
                <Kpi label="Contract value" info="contract_value" value={fmt.usd(h.contract_value)} sub={`sold margin ${fmt.pct(h.sold_margin_pct)}`} />
                <Kpi label="CPI" info="cpi" value={fmt.ratio(h.cpi)} tone={num(h.cpi) < 0.95 ? 'bad' : 'good'} sub="earned value / actual cost" />
                <Kpi label="SPI" info="spi" value={fmt.ratio(h.spi)} tone={num(h.spi) < 0.95 ? 'bad' : 'good'} sub={`forecast end ${fmt.date(h.forecast_end)} (${h.forecast_slip_weeks} wk slip)`} />
                <Kpi label="Estimate at completion" info="eac" value={fmt.usd(h.eac)} sub={`forecast margin ${fmt.pct(h.forecast_margin_pct)}`} tone={num(h.forecast_margin_pct) < 0 ? 'bad' : 'neutral'} />
                <Kpi label="LD exposure" info="ld_exposure" value={fmt.usd(h.ld_exposure)} sub="liquidated damages if the slip holds" />
              </Grid>
              <Grid cols={2}>
                <Card title="Plan vs actual (cumulative)" info="plan_vs_actual" subtitle="Planned value, earned value and actual cost by month">
                  <EChart height={300} option={lines(m.map((r) => String(r.month_start).slice(0, 7)), [
                    { name: 'Planned value', data: m.map((r) => r.cum_planned_value), dashed: true, color: '#8A8D91' },
                    { name: 'Earned value', data: m.map((r) => r.cum_earned_value), color: '#29B5E8' },
                    { name: 'Actual cost', data: m.map((r) => r.cum_actual_cost), color: '#D45B90' },
                  ], { unit: 'usd' })} />
                </Card>
                <Card title="Sold vs actual pyramid" info="pyramid" subtitle="Share of hours by level; drift moves margin">
                  <EChart height={300} option={bars(d.pj_pyramid.map((r) => r.level), [
                    { name: 'Sold', data: d.pj_pyramid.map((r) => r.sold_share_pct), color: '#8A8D91' },
                    { name: 'Actual', data: d.pj_pyramid.map((r) => r.actual_share_pct), color: '#11567F' },
                  ], { unit: 'pct' })} />
                </Card>
              </Grid>
              <Card title="Work packages" info="work_packages" subtitle="Bold red = on the critical path">
                <Table rows={d.pj_work_packages} highlight={(r) => r.is_critical_path} cols={[
                  { key: 'wbs_id', label: 'WBS' }, { key: 'wbs_name', label: 'Work package' }, { key: 'work_type', label: 'Work type' },
                  { key: 'planned_hours', label: 'Planned h', format: fmt.num, align: 'right' },
                  { key: 'planned_end', label: 'Planned end', format: fmt.date }, { key: 'forecast_end', label: 'Forecast end', format: fmt.date },
                  { key: 'forecast_slip_weeks', label: 'Slip (wk)', align: 'right' },
                  { key: 'team_productivity', label: 'Productivity', format: fmt.ratio, align: 'right' },
                  { key: 'is_critical_path', label: 'Critical', format: fmt.bool }, { key: 'reused_asset_id', label: 'Reused asset' },
                ]} />
              </Card>
              <Grid cols={2}>
                <Card title="Why? - from the PM status notes" info="why_notes" subtitle="Cortex Search over project commentary (CSS_PROJECT_COMMENTARY)"
                  right={<button onClick={() => setWhy(!why)} className="rounded-lg bg-sf-dark px-3 py-1 text-xs font-semibold text-white">{why ? 'Hide' : 'Why?'}</button>}>
                  {why ? (
                    <div className="space-y-2">
                      {d.pj_why.length ? d.pj_why.map((r, i) => (
                        <div key={i} className="rounded-lg border border-gray-200 p-3 text-sm">
                          <p className="text-xs text-gray-400">{fmt.date(r.note_date)} - {r.rag_status}</p>
                          <p className="text-gray-700">{r.note}</p>
                        </div>
                      )) : <p className="text-sm text-gray-400">No notes found.</p>}
                    </div>
                  ) : <p className="text-sm text-gray-400">Press "Why?" to retrieve the most relevant status notes.</p>}
                </Card>
                <Card title="Assets that fit" info="assets_fit" subtitle="Top library matches per work package (embedding similarity); hours saved are ESTIMATED"
                  right={<button onClick={() => nav('p11')} className="text-xs font-semibold text-sf-dark underline">Asset Library</button>}>
                  <Table max={300} rows={d.pj_assets} cols={[
                    { key: 'wbs_id', label: 'WBS' }, { key: 'asset_title', label: 'Asset' }, { key: 'asset_type', label: 'Type' },
                    { key: 'similarity', label: 'Similarity', format: fmt.ratio, align: 'right' },
                    { key: 'effort_saving_hours', label: 'Est. hours saved', format: fmt.num, align: 'right' }, { key: 'reuse_status', label: 'Status' },
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
