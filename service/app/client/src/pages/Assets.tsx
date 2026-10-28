import { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { useFilters } from '@/hooks/useFilters';
import { Card, EChart, Grid, PageFrame, Table, WithData, bars, fmt, lines, usePage } from '@/components/ui';
import { searchAssets, type Rows } from '@/lib/api';

export default function Assets({ openProject }: { openProject: (id: string) => void }) {
  const { project } = useFilters();
  const q = usePage('assets', { project });
  const [text, setText] = useState('');
  const [hits, setHits] = useState<Rows | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setBusy(true); setErr(null);
    try { setHits(await searchAssets(text)); } catch (x: any) { setErr(String(x.message ?? x)); } finally { setBusy(false); }
  }

  return (
    <PageFrame id="P11" title="Asset Library" ask="assets" askArgs={{ project }}
      subtitle="Do we harvest our work and reuse it? Harvest and reuse rates, the most reused assets, CPI with vs without reuse, a search over the library, and the assets that fit the selected project."
      suggestions={['What does reuse save us?', 'Which assets should the at-risk project use now?']}>
      <WithData q={q}>
        {(d) => (
          <>
            <Grid cols={2}>
              <Card title="Harvest and reuse rate" subtitle="Harvest = closed projects that contributed an asset; reuse = projects that used one">
                <EChart height={280} option={lines(d.as_fy.map((r) => fmt.fy(r.fiscal_year)), [
                  { name: 'Harvest rate %', data: d.as_fy.map((r) => r.harvest_rate_pct), color: '#11567F' },
                  { name: 'Reuse rate %', data: d.as_fy.map((r) => r.reuse_rate_pct), color: '#29B5E8' },
                ], { unit: 'pct' })} />
              </Card>
              <Card title="Median CPI with vs without reuse" subtitle="Projects by fiscal year of (forecast) end">
                <EChart height={280} option={bars(d.as_fy.map((r) => fmt.fy(r.fiscal_year)), [
                  { name: 'With reuse', data: d.as_fy.map((r) => r.cpi_with_reuse), color: '#11567F' },
                  { name: 'Without reuse', data: d.as_fy.map((r) => r.cpi_without_reuse), color: '#8A8D91' },
                ])} />
              </Card>
            </Grid>
            <Grid cols={2}>
              <Card title="Top reused assets" subtitle="Recorded uses and hours saved (ESTIMATED)">
                <Table max={340} rows={d.as_top} onRow={(r) => openProject(r.source_project_id)} cols={[
                  { key: 'asset_title', label: 'Asset' }, { key: 'asset_type', label: 'Type' }, { key: 'work_type', label: 'Work type' },
                  { key: 'uses', label: 'Uses', align: 'right' }, { key: 'hours_saved_estimated', label: 'Est. hours saved', format: fmt.num, align: 'right' },
                  { key: 'source_project_id', label: 'Harvested from' },
                ]} />
              </Card>
              <Card title="Reuse by contract type" subtitle="From SV_PROJECT_DELIVERY; missed reuse = hours the best-matching unused asset would have saved (ESTIMATED)">
                <Table rows={d.as_reuse_value} cols={[
                  { key: 'contract_type', label: 'Contract' }, { key: 'project_count', label: 'Projects', align: 'right' },
                  { key: 'asset_reuse_rate_pct', label: 'Reuse rate', format: fmt.pct, align: 'right' },
                  { key: 'total_hours_saved_estimated', label: 'Est. hours saved', format: fmt.num, align: 'right' },
                  { key: 'missed_reuse_hours', label: 'Est. hours missed', format: fmt.num, align: 'right' },
                ]} />
              </Card>
            </Grid>
            <Card title="Search the library" subtitle="Cortex Search (CSS_ASSET_LIBRARY) over titles, descriptions and skill tags">
              <form onSubmit={search} className="mb-3 flex gap-2">
                <input value={text} onChange={(e) => setText(e.target.value)} placeholder="e.g. data migration reconciliation accelerator"
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none" />
                <button type="submit" className="flex items-center gap-1 rounded-lg bg-sf-dark px-4 text-sm font-semibold text-white">
                  {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />} Search
                </button>
              </form>
              {err && <p className="text-sm text-red-600">{err}</p>}
              {hits && <Table rows={hits} cols={[
                { key: 'asset_title', label: 'Asset' }, { key: 'asset_type', label: 'Type' }, { key: 'work_type', label: 'Work type' },
                { key: 'effort_saving_hours', label: 'Est. hours saved', format: fmt.num, align: 'right' }, { key: 'source_project_id', label: 'Harvested from' },
              ]} />}
            </Card>
            <Card title={`Assets matching ${project}'s work packages`} subtitle="Top 3 per work package by embedding similarity; status shows whether the project used it">
              <Table rows={d.as_match} cols={[
                { key: 'wbs_id', label: 'WBS' }, { key: 'work_type', label: 'Work type' }, { key: 'asset_title', label: 'Asset' },
                { key: 'similarity', label: 'Similarity', format: fmt.ratio, align: 'right' },
                { key: 'effort_saving_hours', label: 'Est. hours saved', format: fmt.num, align: 'right' }, { key: 'reuse_status', label: 'Status' },
              ]} />
            </Card>
          </>
        )}
      </WithData>
    </PageFrame>
  );
}
