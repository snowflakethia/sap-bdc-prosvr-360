import { AlertTriangle, ArrowRight, Factory, Network, Bot, Database, Layers, Target, Boxes } from 'lucide-react';

// Business Scenario — the context of the dashboard and the program it is built for.
// Outcomes are framed as aspirations, not measured results.

const PROBLEMS = [
  { title: 'Fragmented SAP data', body: 'Production, procurement, quality and logistics live in separate SAP modules and plants. Nobody sees the whole network at once.' },
  { title: 'Extracts lose meaning', body: 'Classic ETL copies tables but drops SAP business context — keys, units, statuses — so every team re-derives it differently.' },
  { title: 'Slow, unexplained answers', body: '"Why did OTIF drop?" takes days of joins across systems, and the answer is a spreadsheet nobody can audit.' },
];

const PROGRAM = [
  { icon: Database, title: 'SAP BDC data products', body: '21 standard data products: orders, BOM, stock, deliveries, suppliers.' },
  { icon: Layers, title: 'Zero-copy CLD + medallion', body: 'Mounted in Snowflake, refined by Dynamic Tables into gold KPIs.' },
  { icon: Network, title: 'Semantic view = ontology', body: 'Suppliers, materials, plants, flows and KPIs defined once.' },
  { icon: Bot, title: 'Cortex Analyst & Agent', body: 'Natural-language What / Why / What-if over the ontology.' },
  { icon: Boxes, title: 'Native App', body: 'Packaged, governed, deployable to any account or region.' },
];

const STORY = [
  { step: 'Signal', text: 'Festo AG quality score falls ~11 points in Q3', page: 'SC Forecasting' },
  { step: 'Exposure', text: 'Which materials, BOMs and plants depend on Festo AG?', page: 'Supply Chain Ontology' },
  { step: 'Impact', text: 'Component cover vs lead time — shortages locked in', page: 'Fulfillment & Constraints' },
  { step: 'Options', text: 'Alternate qualified suppliers and their scores', page: 'Cortex Analyst' },
  { step: 'Decision', text: 'Re-allocate sourcing; quantify value at stake', page: 'SC Optimization' },
];

const OUTCOMES = [
  'Minutes from question to governed answer, not days',
  'No extraction pipelines to build or maintain',
  'One definition per KPI — shared by dashboards, SQL and AI',
  'Every number traceable to an SAP BDC data product',
];

export default function Scenario() {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-sf-deeper to-sf-primary p-8 text-white shadow-lg">
        <p className="text-xs font-semibold uppercase tracking-widest text-white/70">The company</p>
        <h2 className="mt-2 text-2xl font-bold leading-snug">
          A semiconductor-equipment maker running SAP S/4HANA — 5 plants, 15 suppliers, 28 network nodes.
        </h2>
        <p className="mt-3 max-w-3xl text-white/85">
          It needs one trusted, explainable view of supply risk across plants, suppliers and customers — and it
          needs to ask that view questions in plain language.
        </p>
        <div className="mt-5 flex flex-wrap gap-6 text-sm">
          {['Austin Fab', 'Dresden Fab', 'Penang Assembly', 'San Jose HQ', 'Singapore Hub'].map((p) => (
            <span key={p} className="inline-flex items-center gap-1.5"><Factory className="h-4 w-4" />{p}</span>
          ))}
        </div>
      </div>

      <section>
        <h3 className="mb-3 flex items-center gap-2 text-lg font-bold text-sf-dark"><AlertTriangle className="h-5 w-5 text-amber-500" />The problem</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {PROBLEMS.map((p) => (
            <div key={p.title} className="rounded-xl border border-amber-200 bg-amber-50/50 p-5">
              <p className="font-semibold text-amber-900">{p.title}</p>
              <p className="mt-1.5 text-sm text-gray-700">{p.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h3 className="mb-3 text-lg font-bold text-sf-dark">The program we built</h3>
        <div className="flex flex-wrap items-stretch gap-2">
          {PROGRAM.map((p, i) => (
            <div key={p.title} className="flex items-center gap-2">
              <div className="w-52 rounded-xl border border-sf-primary/30 bg-white p-4 shadow-sm">
                <p.icon className="h-5 w-5 text-sf-primary" />
                <p className="mt-2 text-sm font-semibold text-sf-dark">{p.title}</p>
                <p className="mt-1 text-xs text-gray-600">{p.body}</p>
              </div>
              {i < PROGRAM.length - 1 && <ArrowRight className="h-5 w-5 shrink-0 text-sf-primary/50" />}
            </div>
          ))}
        </div>
      </section>

      <section data-tour="scenario-storyline" className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-bold text-sf-dark">The storyline — a supplier quality shock</h3>
        <p className="mt-1 text-sm text-gray-500">Follow it through the app; each step names the page that shows it.</p>
        <ol className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-5">
          {STORY.map((s, i) => (
            <li key={s.step} className="rounded-lg border border-sf-primary/20 bg-sky-50/40 p-4">
              <p className="text-[11px] font-bold uppercase tracking-wider text-sf-primary">{i + 1}. {s.step}</p>
              <p className="mt-1 text-sm text-sf-dark">{s.text}</p>
              <p className="mt-2 text-[11px] text-gray-500">→ {s.page}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-6">
        <h3 className="flex items-center gap-2 text-lg font-bold text-emerald-900"><Target className="h-5 w-5" />Target outcomes</h3>
        <ul className="mt-3 grid grid-cols-1 gap-2 text-sm text-gray-700 md:grid-cols-2">
          {OUTCOMES.map((o) => <li key={o} className="flex gap-2"><span className="text-emerald-600">✓</span>{o}</li>)}
        </ul>
        <p className="mt-4 text-xs text-gray-500">
          Demo data: SAP BDC data products from the internal listing, plus a clearly labelled synthetic supplier
          extension (SUPPLIER_EXT). Outcomes are program aspirations, not measured results.
        </p>
      </section>
    </div>
  );
}
