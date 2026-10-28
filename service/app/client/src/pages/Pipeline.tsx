import { Card, EChart, Grid, PageFrame, Table, WithData, bars, fmt, lines, usePage } from '@/components/ui';

export default function Pipeline() {
  const q = usePage('pipeline');
  return (
    <PageFrame id="P5" title="Pipeline & Pursuit" ask="pipeline"
      subtitle="Open pipeline by size, win-rate by pursuit intensity and by team skill fit within size, pursuit cost per won USD, open bids with suggested bench additions, and bookings."
      suggestions={['Does more pursuit effort win more?', 'Which open bid should I strengthen, and with whom?']}>
      <WithData q={q}>
        {(d) => {
          const wr = d.pi_win_rate;
          const sizes = [...new Set(wr.map((r) => r.size_class))];
          const seg = (filter: (r: any) => boolean) => sizes.map((s) => {
            const rows = wr.filter((r) => r.size_class === s && filter(r));
            const bids = rows.reduce((a, r) => a + Number(r.bids), 0), won = rows.reduce((a, r) => a + Number(r.won), 0);
            return bids ? (100 * won) / bids : null;
          });
          const bandRank = (b: string) => (/^LOW/.test(b) ? 0 : /^MEDIUM/.test(b) ? 1 : 2);
          const bands = [...new Set(wr.map((r) => String(r.skill_fit_band)))].sort((x, y) => bandRank(x) - bandRank(y));
          const b = d.pi_bookings;
          return (
            <>
              <Grid cols={2}>
                <Card title="Win-rate by pursuit intensity, within size" subtitle="Decided bids in the range: above vs below the size class's median pursuit hours per USD">
                  <EChart height={300} option={bars(sizes, [
                    { name: 'Above median intensity', data: seg((r) => r.intensity_band === 'Above median'), color: '#11567F' },
                    { name: 'Below median intensity', data: seg((r) => r.intensity_band === 'Below median'), color: '#71D3F7' },
                  ], { unit: 'pct' })} />
                </Card>
                <Card title="Win-rate by team skill fit, within size" subtitle="Share of the bid's required skills the pursuit team holds">
                  <EChart height={300} option={bars(sizes, bands.map((band, i) => ({
                    name: `Fit ${band}`, data: seg((r) => r.skill_fit_band === band), color: ['#D45B90', '#71D3F7', '#11567F'][i % 3],
                  })), { unit: 'pct' })} />
                </Card>
              </Grid>
              <Grid cols={2}>
                <Card title="Open pipeline by size" subtitle="From SV_PIPELINE_PRESALES">
                  <EChart height={260} option={bars(d.pi_size.map((r) => r.opportunity_size), [{ name: 'Open pipeline value', data: d.pi_size.map((r) => r.open_pipeline_value) }], { unit: 'usd', horizontal: true })} />
                </Card>
                <Card title="Bookings, book-to-bill and pursuit cost" subtitle="Won value vs revenue; pursuit cost per won USD">
                  <EChart height={260} option={{
                    ...lines(b.map((r) => fmt.fy(r.fiscal_year)), [
                      { name: 'Book-to-bill', data: b.map((r) => r.book_to_bill), color: '#11567F' },
                      { name: 'Pursuit cost / won USD', data: b.map((r) => r.pursuit_cost_per_won_usd), color: '#D45B90', yAxisIndex: 1 },
                    ], { unit: 'num', unit2: 'num' }),
                  }} />
                </Card>
              </Grid>
              <Card title={`Open bids (${d.pi_open.length})`} subtitle="Team skill fit, AI-skill requirement and the best-matched bench / roll-off people (embedding match, VW_BENCH_TO_PIPELINE)">
                <Table rows={d.pi_open} highlight={(r) => Number(r.skill_fit) < 0.6} cols={[
                  { key: 'opportunity_id', label: 'Bid' }, { key: 'customer_name', label: 'Customer' }, { key: 'size_class', label: 'Size' },
                  { key: 'work_type', label: 'Work type' }, { key: 'estimated_value', label: 'Value', format: fmt.usd, align: 'right' },
                  { key: 'expected_start_date', label: 'Start', format: fmt.date }, { key: 'skill_fit', label: 'Skill fit', format: fmt.ratio, align: 'right' },
                  { key: 'required_ai_skill_level', label: 'AI level', align: 'right' }, { key: 'team_size', label: 'Team', align: 'right' },
                  { key: 'suggested_bench', label: 'Suggested bench additions' },
                ]} />
              </Card>
            </>
          );
        }}
      </WithData>
    </PageFrame>
  );
}
