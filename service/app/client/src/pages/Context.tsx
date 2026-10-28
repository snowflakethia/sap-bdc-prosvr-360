import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Navigate } from '@/App';
import type { PageId } from '@/components/Sidebar';
import { NAV_ITEMS } from '@/components/Sidebar';
import { Card, Grid, Kpi, PageFrame, Table, WithData, fmt, usePage } from '@/components/ui';
import business from '@/content/business.md?raw';
import demo from '@/content/demo.md?raw';

function Md({ text }: { text: string }) {
  return <div className="cortex-md max-w-none"><ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown></div>;
}

// ---------------------------------------------------------------------------
// C1 Business Overview
// ---------------------------------------------------------------------------
export function BusinessOverview({ nav }: { nav: Navigate }) {
  const q = usePage('context/c1');
  return (
    <PageFrame id="C1" title="Business Overview" subtitle="The business ACoCo runs, the five uses of time, the three pillars, and the Partner MD's situation on 1 October 2026.">
      <WithData q={q}>
        {(d) => {
          const f = d.cx_firm[0] ?? {};
          return (
            <>
              <Grid cols={5}>
                <Kpi label="FY26 revenue (firm)" value={fmt.usd(f.revenue)} sub={`margin ${fmt.pct(f.margin_pct)}`} />
                <Kpi label="People (end FY26)" value={fmt.num(f.headcount_end)} sub={`voluntary attrition ${fmt.pct(f.attrition_pct)}`} />
                <Kpi label="Delivery share" value={fmt.pct(f.delivery_pct)} sub="target ~70 % (headcount mix)" />
                <Kpi label="Win-rate FY26" value={fmt.pct(f.win_rate_pct)} sub="decided bids" />
                <Kpi label="MD groups" value={String(d.cx_groups.length)} sub="each led by a Partner MD" />
              </Grid>
              <Card title="The six MD groups (FY26)" subtitle="Live from ACOCO_L2.SERVING.VW_SCORECARD_FY">
                <Table rows={d.cx_groups} cols={[
                  { key: 'md_group_name', label: 'Group' },
                  { key: 'managing_director_name', label: 'Partner MD' },
                  { key: 'revenue', label: 'Revenue', format: fmt.usd, align: 'right' },
                  { key: 'margin_pct', label: 'Margin', format: fmt.pct, align: 'right' },
                  { key: 'headcount_end', label: 'People', format: fmt.num, align: 'right' },
                ]} />
              </Card>
            </>
          );
        }}
      </WithData>
      <Card title="How the business works"><Md text={business} /></Card>
      <div className="flex gap-3">
        <button onClick={() => nav('c4')} className="rounded-lg bg-sf-dark px-4 py-2 text-sm font-semibold text-white">Next: Platform Architecture</button>
        <button onClick={() => nav('p0')} className="rounded-lg border border-sf-dark px-4 py-2 text-sm font-semibold text-sf-dark">Go to ProServe360 Overview</button>
      </div>
    </PageFrame>
  );
}

// ---------------------------------------------------------------------------
// C2 Dashboard Overview
// ---------------------------------------------------------------------------
const PAGE_GUIDE: { id: PageId; question: string; stories: string }[] = [
  { id: 'p0', question: 'How is my group doing on all three pillars, and what are the top risks?', stories: 'PMD-0' },
  { id: 'p1', question: 'Where does revenue come from, and which fixed-price projects are below 10 % margin?', stories: 'PMD-1' },
  { id: 'p2', question: 'Why is this project off plan, and which asset would have helped?', stories: 'PMD-2, PMD-8' },
  { id: 'p11', question: 'Do we harvest and reuse our work, and what does reuse save?', stories: 'PMD-9' },
  { id: 'p5', question: 'Which bids do we win, at what pursuit cost, and who would raise the odds?', stories: 'PMD-6, PMD-10' },
  { id: 'p3', question: 'Is the five-way time mix right by level, and who rolls off soon?', stories: 'PMD-3' },
  { id: 'p4', question: 'Who may leave, and do our skills match the pipeline?', stories: 'PMD-4, PMD-5' },
  { id: 'p6', question: 'Does AI skill and AI use make people faster, and does learning pay back?', stories: 'PMD-7, PMD-12' },
  { id: 'p7', question: 'What can context and reasoning add (matching, forecasting, leak detection)?', stories: 'section 9' },
  { id: 'p10', question: 'Ask anything across the five Semantic Views', stories: 'PMD-0..12' },
  { id: 'p8', question: 'Where does each number come from (L0 -> L1 -> L2)?', stories: '-' },
  { id: 'p9', question: 'Can I trust it (freshness, completeness, fee boundary)?', stories: '-' },
];

export function DashboardOverview({ nav }: { nav: Navigate }) {
  const q = usePage('context/c2');
  return (
    <PageFrame id="C2" title="Dashboard Overview" subtitle="How to read the Command Center: the question each page answers, its metrics and filters, and the honesty markers.">
      <Card title="Site map">
        <Table rows={PAGE_GUIDE.map((p) => ({ ...p, code: NAV_ITEMS.find((n) => n.id === p.id)?.code, label: NAV_ITEMS.find((n) => n.id === p.id)?.label }))}
          onRow={(r) => nav(r.id)} cols={[
            { key: 'code', label: 'Page' }, { key: 'label', label: 'Name' }, { key: 'question', label: 'Question it answers' }, { key: 'stories', label: 'Stories' },
          ]} />
      </Card>
      <Grid cols={3}>
        <Card title="Filters">
          <p className="text-sm text-gray-600">MD group (default Financial Services, or Firm-wide), fiscal-year range and size class sit in the left rail. They are bound into the SQL on the server (WHERE clauses on <code>SEMANTIC_VIEW()</code> and SERVING views) - never filtered in the browser.</p>
        </Card>
        <Card title="Ask Cortex and the Advisor">
          <p className="text-sm text-gray-600"><b>Ask Cortex</b> re-runs the page's registry statements and asks <code>AI_COMPLETE</code> to explain exactly those figures. The <b>Advisor</b> (P10) is the Cortex Agent <code>ACOCO_ADVISOR</code> over five Semantic Views, two Cortex Search services and the reasoning views.</p>
        </Card>
        <Card title="Honesty markers">
          <p className="text-sm text-gray-600"><code>SOURCE_SYSTEM</code> shows real BDC rows vs simulated ones; hours saved are labelled <b>ESTIMATED</b>; statistical effects show a 90 % confidence interval and "no significant effect" when it spans zero.</p>
        </Card>
      </Grid>
      <WithData q={q}>
        {(d) => (
          <Card title={`Metric glossary (${d.cx_metrics.length} metrics)`} subtitle="Live from ACOCO_L2.ONTOLOGY.ONT_METRIC via SERVING.VW_METRIC_GLOSSARY">
            <Table rows={d.cx_metrics} max={480} cols={[
              { key: 'pillar', label: 'Pillar' }, { key: 'metric', label: 'Metric' }, { key: 'semantic_view', label: 'Semantic View' }, { key: 'definition', label: 'Definition' },
            ]} />
          </Card>
        )}
      </WithData>
    </PageFrame>
  );
}

// ---------------------------------------------------------------------------
// C3 Demo Overview
// ---------------------------------------------------------------------------
const STORYBOARD: { min: string; beat: string; page: PageId; claim: string }[] = [
  { min: '0-3', beat: 'Framing', page: 'c1', claim: 'Bill codes, five uses of time and their targets, three pillars; the five-layer platform and the ontology graph (C4).' },
  { min: '3-5', beat: 'Where the data comes from', page: 'p8', claim: 'Real CLDs from connector SNOWFLAKE_APJ incl. four People Intelligence products; which rows are simulated and why.' },
  { min: '5-8', beat: 'ProServe360', page: 'p0', claim: 'FY26 vs FY25 per pillar; time mix by level vs target; top cross-pillar risks.' },
  { min: '8-14', beat: 'Operational Excellence', page: 'p2', claim: 'Pareto tail (P1); the FS project in loss, critical work package, pyramid drift, "why" from PM notes; assets it did not reuse (P11).' },
  { min: '14-18', beat: 'Value Creation', page: 'p5', claim: 'Win-rate by pursuit intensity and team fit; open bids with weak fit and the bench people who would raise it.' },
  { min: '18-24', beat: 'People Development', page: 'p3', claim: 'Time mix vs target; roll-off before 30 Dec; skills vs pipeline and attrition risk (P4); AI-skilled but inactive and the AI productivity test (P6).' },
  { min: '24-28', beat: 'What-if', page: 'p10', claim: 'Bench-to-pipeline match (P7); ask the Advisor the what-if and one free question.' },
  { min: '28-30', beat: 'Close', page: 'p9', claim: 'Fee-boundary evidence; what goes back to SAP for each pillar.' },
];

export function DemoOverview({ nav }: { nav: Navigate }) {
  const q = usePage('context/c3');
  return (
    <PageFrame id="C3" title="Demo Overview" subtitle="The 30-minute flow as a clickable storyboard, which data is real and which is simulated, and what goes back to SAP.">
      <Card title="Storyboard (click a beat to open its page)">
        <Table rows={STORYBOARD.map((s) => ({ ...s, code: NAV_ITEMS.find((n) => n.id === s.page)?.code }))} onRow={(r) => nav(r.page)} cols={[
          { key: 'min', label: 'Min' }, { key: 'beat', label: 'Beat' }, { key: 'code', label: 'Page' }, { key: 'claim', label: 'Claim' },
        ]} />
      </Card>
      <WithData q={q}>
        {(d) => {
          const s = d.cx_story[0];
          return s ? (
            <Card title={`The story project: ${s.project_id} - ${s.customer_name}`} subtitle="Seeded at-risk FS fixed-price project (live figures)">
              <Grid cols={4}>
                <Kpi label="Contract" value={fmt.usd(s.contract_value)} sub={`${s.size_class} - ${s.contract_type}`} />
                <Kpi label="CPI / SPI" value={`${fmt.ratio(s.cpi)} / ${fmt.ratio(s.spi)}`} tone="bad" />
                <Kpi label="Forecast margin" value={fmt.pct(s.forecast_margin_pct)} tone="bad" />
                <Kpi label="LD exposure" value={fmt.usd(s.ld_exposure)} />
              </Grid>
            </Card>
          ) : null;
        }}
      </WithData>
      <Card title="The demo, explained"><Md text={demo} /></Card>
    </PageFrame>
  );
}
