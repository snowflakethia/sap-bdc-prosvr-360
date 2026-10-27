import { ArrowDown, ShieldCheck } from 'lucide-react';

// Technology Architecture — the ideal zero-copy path from SAP BDC to the app.
// Each layer lists the real objects this demo builds (sql/00–07b).

interface Layer {
  name: string;
  tag: string;
  tone: string;
  what: string;
  objects: string[];
}

const LAYERS: Layer[] = [
  { name: 'SAP S/4HANA → SAP Business Data Cloud', tag: 'SAP', tone: 'border-blue-300 bg-blue-50',
    what: 'SAP curates Standard Data Products with business semantics (CSN metadata, keys, units, statuses).',
    objects: ['Production orders', 'BOM', 'Stock', 'Deliveries', 'Suppliers', 'Projects / WBS'] },
  { name: 'BDC Connect → Catalog-Linked Database (L0 bronze)', tag: 'Zero-copy', tone: 'border-cyan-300 bg-cyan-50',
    what: 'Data products are shared into Snowflake as a catalog-linked database — no extraction, no pipeline, no copy to reconcile.',
    objects: ['SAP_SUPPLY_CHAIN.<data product schemas> (21 A_* tables)', 'Tag-based PII masking (UNMASK_PII)'] },
  { name: 'Dynamic Tables (L2 gold)', tag: 'Declarative', tone: 'border-emerald-300 bg-emerald-50',
    what: 'Business-ready facts built declaratively; Snowflake manages incremental refresh to a target lag.',
    objects: ['ANALYTICS.DT_PRODUCTION_ORDER_360', 'DT_MANUFACTURING_KPI', 'DT_SUPPLIER_QUALITY', 'DT_SUPPLY_CHAIN_GEO', '…15 dynamic tables'] },
  { name: 'Serving views', tag: 'App contract', tone: 'border-teal-300 bg-teal-50',
    what: 'A stable interface for the application, decoupled from refinement logic.',
    objects: ['APP_REF.* serving views'] },
  { name: 'Semantic view — the ontology', tag: 'Semantics', tone: 'border-violet-300 bg-violet-50',
    what: 'Entities, relationships, dimensions, facts, synonyms and descriptions in one governed schema object.',
    objects: ['ANALYTICS.SAP_SUPPLY_CHAIN_360 (15 logical tables)'] },
  { name: 'Cortex AI', tag: 'AI', tone: 'border-fuchsia-300 bg-fuchsia-50',
    what: 'Cortex Analyst turns questions into SQL over the semantic view; the Cortex Agent orchestrates multi-step reasoning.',
    objects: ['Cortex Analyst', 'ANALYTICS.SAP_SC360_ANALYST_AGENT', 'SNOWFLAKE.CORTEX.COMPLETE (Ask Cortex)'] },
  { name: 'Snowflake Native App on SPCS', tag: 'Delivery', tone: 'border-sky-300 bg-sky-50',
    what: 'React + Express in a container, packaged with its data and semantic view; installable by any account or region.',
    objects: ['SUPPLY_CHAIN_360_PKG', 'SUPPLY_CHAIN_360_APP / SC360_SERVICE'] },
];

const COMPARE = [
  ['Data movement', 'Copies plus pipelines to build and run', 'Shared in place — nothing to extract or reconcile'],
  ['SAP business semantics', 'Lost in flat tables, re-derived by hand', 'Preserved in curated data products'],
  ['Freshness', 'Batch windows; stale between loads', 'As current as the data product SAP publishes'],
  ['Change handling', 'Schema change breaks pipelines', 'Changes arrive as data product versions'],
  ['Governance', 'Re-implemented in each target system', 'SAP-curated products + Snowflake Horizon policies'],
  ['Cost of ownership', 'Integration tooling, storage of copies, ops effort', 'No pipeline layer to own'],
];

const WHY = [
  { title: 'Semantics as a first-class object', body: 'The semantic view is a governed schema object — versioned, access-controlled, shareable through listings — not a BI-tool layer.' },
  { title: 'AI on the same definitions', body: 'Cortex Analyst and Agents use that semantic view directly, so AI answers and dashboards agree by construction.' },
  { title: 'Declarative pipelines', body: 'Dynamic Tables replace hand-built orchestration for the medallion layers.' },
  { title: 'One governance plane', body: 'Horizon masking, tags, lineage and RBAC apply from the CLD to the app.' },
  { title: 'Ship it as a product', body: 'The whole solution packages as a Native App and distributes across accounts and regions.' },
];

export default function Architecture() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_380px]">
        <div data-tour="architecture-flow" className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-bold text-sf-dark">SAP BDC → CLD → medallion → ontology → AI → app</h3>
          <p className="mt-1 text-xs text-gray-500">Target state: SAP BDC data products shared zero-copy into a catalog-linked database.</p>
          <div className="mt-5 flex gap-4">
            <div className="flex-1 space-y-1">
              {LAYERS.map((l, i) => (
                <div key={l.name}>
                  <div className={`group relative rounded-lg border-l-4 ${l.tone} px-4 py-3`}>
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-sf-dark">{l.name}</p>
                      <span className="rounded-full bg-white/80 px-2 py-0.5 text-[10px] font-bold uppercase text-gray-600">{l.tag}</span>
                    </div>
                    <p className="mt-1 text-xs text-gray-700">{l.what}</p>
                    <p className="mt-1.5 hidden font-mono text-[11px] text-gray-500 group-hover:block">{l.objects.join(' · ')}</p>
                  </div>
                  {i < LAYERS.length - 1 && <ArrowDown className="mx-auto my-0.5 h-4 w-4 text-gray-300" />}
                </div>
              ))}
            </div>
            <div className="flex w-10 flex-col items-center justify-center rounded-lg bg-gradient-to-b from-amber-100 to-amber-50 py-4">
              <ShieldCheck className="h-5 w-5 text-amber-700" />
              <span className="mt-2 text-[11px] font-bold uppercase tracking-widest text-amber-800 [writing-mode:vertical-rl]">
                Horizon governance · masking · lineage · RBAC
              </span>
            </div>
          </div>
          <p className="mt-3 text-[11px] text-gray-400">Hover a layer to see the objects this demo creates.</p>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-bold text-sf-dark">Why Snowflake for SAP BDC</h3>
          {WHY.map((w) => (
            <div key={w.title} className="rounded-xl border border-sf-primary/25 bg-white p-4 shadow-sm">
              <p className="text-sm font-semibold text-sf-primary">{w.title}</p>
              <p className="mt-1 text-xs text-gray-700">{w.body}</p>
            </div>
          ))}
          <p className="text-[11px] text-gray-400">
            Other platforms also integrate with SAP BDC. Compare on semantics, AI on governed definitions, and
            packaging — verify current competitor capabilities before positioning.
          </p>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-bold text-sf-dark">Why SAP BDC zero-copy instead of ETL</h3>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase tracking-wider text-gray-500">
            <tr><th className="px-6 py-3"></th><th className="px-6 py-3">ETL extract into Snowflake</th><th className="px-6 py-3 text-sf-primary">SAP BDC zero-copy → CLD</th></tr>
          </thead>
          <tbody>
            {COMPARE.map(([k, etl, bdc]) => (
              <tr key={k} className="border-t border-gray-100">
                <td className="px-6 py-3 font-semibold text-sf-dark">{k}</td>
                <td className="px-6 py-3 text-gray-600">{etl}</td>
                <td className="px-6 py-3 text-gray-800">{bdc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3 text-xs text-gray-500">
        This demo build: L0 is bootstrapped from the internal SAP BDC listing (sql/00) and extended with a
        labelled synthetic SUPPLIER_EXT schema (sql/07a). The diagram shows the target zero-copy state.
      </p>
    </div>
  );
}
