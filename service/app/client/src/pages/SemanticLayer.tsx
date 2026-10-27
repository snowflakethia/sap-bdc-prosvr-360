import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { useQuery } from '@/hooks/useQuery';
import { fetchSemanticModel, type SemanticModel } from '@/lib/api';

// "Semantic Layer = Ontology" tab on the Supply Chain Ontology page.
// Content mirrors the deployed semantic view ANALYTICS.SAP_SUPPLY_CHAIN_360.

const MAPPING = [
  ['Entity / class', 'Logical table', 'SUPPLIER_QUALITY, PRODUCTION_ORDER, BOM_EXPLOSION, INVENTORY_OVERVIEW …'],
  ['Property / attribute', 'Dimension', 'plant_name, supplier_name, material_desc, period_date'],
  ['Quantitative property', 'Fact', 'planned_qty, scrap_qty, quality_score, days_of_cover'],
  ['Relationship', 'Relationship (join keys)', 'SUPPLIER_QUALITY(SUPPLIER) → SUPPLIER(SUPPLIER); BOM_EXPLOSION(COMPONENT_MATERIAL) → MATERIAL'],
  ['Measure / KPI', 'Metric', 'yield %, scrap rate, OTIF — define once as metrics so every consumer computes them identically'],
  ['Business vocabulary', 'Synonyms + descriptions', '"vendor" = supplier, "fab" = plant, "on time" = OTD'],
  ['Validated knowledge', 'Verified queries', 'Curated question → SQL pairs that anchor AI answers'],
];

const ENTITIES = [
  ['PRODUCTION_ORDER', 'DT_PRODUCTION_ORDER_360', 'Orders, confirmations, yield, scrap, cycle time'],
  ['BOM_EXPLOSION', 'DT_BOM_EXPLOSION', 'Parent → component structure, qty, cost'],
  ['INVENTORY_OVERVIEW', 'DT_INVENTORY_OVERVIEW', 'Stock by material/plant, turnover, obsolescence'],
  ['SUPPLIER_QUALITY', 'DT_SUPPLIER_QUALITY', 'Quarterly defect %, OTD %, quality score per material'],
  ['SUPPLY_CHAIN_GEO', 'DT_SUPPLY_CHAIN_GEO', 'Nodes and flows with coordinates and value'],
  ['DELIVERY_PERFORMANCE', 'DT_DELIVERY_PERFORMANCE', 'Outbound deliveries, on-time, delay'],
  ['MANUFACTURING_KPI', 'DT_MANUFACTURING_KPI', 'Monthly OEE, throughput, scrap, OTD, turnover'],
  ['COMPONENT_COVER', 'DT_COMPONENT_COVER', 'Days of cover vs supplier lead time'],
  ['ORDER_FULFILLMENT', 'DT_ORDER_FULFILLMENT', 'OTIF, late cause, late cost'],
  ['MATERIAL · SUPPLIER · PLANT', 'ENT_MATERIAL · ENT_SUPPLIER · ENT_PLANT', 'Ontology entities: one row per key, every fact links to them'],
  ['… 6 more', 'Equipment, outages, operating rate, work centers, projects', ''],
];

// How SAP CDS metadata maps onto the semantic view. In this repo the view is
// hand-authored (sql/04_semantic_view.sql); this is the mapping a generator
// over the data products' CSN metadata would apply.
const CDS_MAP = [
  ['CDS view entity (e.g. a supplier-evaluation view)', 'Logical table', 'SUPPLIER_QUALITY'],
  ['key elements', 'primary key', 'SUPPLIER primary key (SUPPLIER)'],
  ['association [0..1] to I_Supplier on …Supplier', 'relationship', 'SUPPLIER_SUPPLIES: (SUPPLIER) references SUPPLIER'],
  ['@Analytics.dataCategory: #DIMENSION / #CUBE', 'entity table vs fact table', 'ENT_SUPPLIER vs DT_SUPPLIER_QUALITY'],
  ['@Semantics.quantity / @Semantics.amount, @DefaultAggregation', 'fact / metric', 'DEFECT_QTY, STOCK_VALUE'],
  ['@ObjectModel.text.element, @EndUserText.label', 'description dimension, comment, synonyms', 'SUPPLIER_NAME for SUPPLIER'],
];

const PATH = ['Supplier (Festo AG)', 'supplies → Material', 'used in → BOM', 'built at → Plant', 'ships → Customer order'];

const WHY = [
  { title: 'One definition, three consumers', body: 'Dashboards, SQL users and AI all read the same entity and metric definitions — no drift between the report and the answer.' },
  { title: 'AI needs meaning, not just tables', body: 'LLMs cannot guess that MATNR is a material or that OTD excludes partials. The semantic layer supplies that meaning explicitly.' },
  { title: 'Governed like data', body: 'The semantic view is a Snowflake schema object: RBAC-controlled, auditable, and shareable through listings and Native Apps.' },
  { title: 'Keeps SAP context', body: 'SAP BDC data products arrive with business semantics; the semantic view carries them forward instead of flattening them.' },
];

export default function SemanticLayer() {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-violet-200 bg-gradient-to-br from-violet-50 via-white to-sky-50 p-6">
        <h3 className="text-lg font-bold text-sf-dark">Why the semantic layer is the ontology</h3>
        <p className="mt-1 max-w-4xl text-sm text-gray-700">
          An ontology names the things in a business, their properties and how they relate. In Snowflake that model
          lives in a <b>semantic view</b> — <code className="text-xs">ANALYTICS.SAP_SUPPLY_CHAIN_360</code> — sitting on
          the gold Dynamic Tables built from SAP BDC data products. The graph, the dashboards and Cortex Analyst all
          read from it.
        </p>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          {WHY.map((w) => (
            <div key={w.title} className="rounded-lg border border-violet-200 bg-white p-4">
              <p className="text-sm font-semibold text-violet-800">{w.title}</p>
              <p className="mt-1 text-xs text-gray-700">{w.body}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="border-b px-5 py-3"><h3 className="font-bold text-sf-dark">Ontology concept → semantic view element</h3></div>
          <table className="w-full text-xs">
            <thead className="bg-gray-50 text-left uppercase tracking-wider text-gray-500">
              <tr><th className="px-4 py-2">Ontology</th><th className="px-4 py-2">Semantic view</th><th className="px-4 py-2">Example</th></tr>
            </thead>
            <tbody>
              {MAPPING.map(([o, s, e]) => (
                <tr key={o} className="border-t border-gray-100">
                  <td className="px-4 py-2 font-semibold text-sf-dark">{o}</td>
                  <td className="px-4 py-2 text-violet-700">{s}</td>
                  <td className="px-4 py-2 text-gray-600">{e}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div data-tour="semantic-entities" className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="border-b px-5 py-3"><h3 className="font-bold text-sf-dark">Entities defined in SAP_SUPPLY_CHAIN_360 (15)</h3></div>
          <table className="w-full text-xs">
            <tbody>
              {ENTITIES.map(([e, t, d]) => (
                <tr key={e} className="border-t border-gray-100 first:border-0">
                  <td className="px-4 py-2 font-mono font-semibold text-sf-dark">{e}</td>
                  <td className="px-4 py-2 font-mono text-gray-500">{t}</td>
                  <td className="px-4 py-2 text-gray-600">{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="font-bold text-sf-dark">From question to ontology path to SQL</h3>
        <p className="mt-1 text-sm text-gray-600">“If Festo AG became unavailable, which materials are affected and who else can supply them?”</p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {PATH.map((p, i) => (
            <span key={p} className="flex items-center gap-2">
              <span className="rounded-full border border-violet-300 bg-violet-50 px-3 py-1 text-xs font-medium text-violet-800">{p}</span>
              {i < PATH.length - 1 && <ArrowRight className="h-4 w-4 text-gray-300" />}
            </span>
          ))}
        </div>
        <pre className="mt-4 overflow-x-auto rounded-lg bg-gray-900 p-4 text-[11px] leading-relaxed text-gray-100">{`-- Generated by Cortex Analyst over SAP_SUPPLY_CHAIN_360
WITH festo_materials AS (
  SELECT DISTINCT material, material_desc
  FROM DT_SUPPLIER_QUALITY WHERE supplier_name = 'Festo AG'
)
SELECT fm.material, fm.material_desc, sq.supplier_name,
       ROUND(AVG(sq.quality_score), 1) AS avg_quality_score
FROM festo_materials fm
LEFT JOIN DT_SUPPLIER_QUALITY sq
  ON sq.material = fm.material AND sq.supplier_name <> 'Festo AG'
GROUP BY 1, 2, 3 ORDER BY 1, 4 DESC;
-- Result in this demo: 4 materials, 3 alternate suppliers`}</pre>
        <p className="mt-3 text-xs text-gray-500">
          Cortex Analyst generated this traversal by joining through the declared relationships and the MATERIAL entity
          (live list below). Ask “If Festo AG stops delivering, which parent assemblies are affected and at which plants
          are those components below lead time?” — 4 assemblies across 5 plants in this demo.
        </p>
      </div>

      <DeclaredRelationships />
      <FromCds />
    </div>
  );
}

function DeclaredRelationships() {
  const { data, loading, error } = useQuery<SemanticModel>(fetchSemanticModel, []);
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h4 className="text-sm font-semibold text-sf-dark">Relationships declared in the semantic view (live)</h4>
      <p className="mt-1 text-xs text-gray-500">
        Read from <code>DESCRIBE SEMANTIC VIEW APP_DATA.SAP_SUPPLY_CHAIN_360</code>. These are the only joins Cortex
        Analyst treats as valid, and they define the edge types in the entity graph.
      </p>
      {loading && <p className="mt-3 text-xs text-gray-400">Loading…</p>}
      {error && <p className="mt-3 text-xs text-red-500">Could not read the semantic view: {String(error)}</p>}
      {data && (
        <>
          <p className="mt-2 text-xs text-gray-600">
            {data.tables.length} logical tables · {data.relationships.length} relationships
          </p>
          <table className="mt-3 w-full text-left text-xs">
            <thead className="text-gray-500">
              <tr><th className="py-1 pr-3">Relationship</th><th className="py-1 pr-3">From (many)</th><th className="py-1">To (one)</th></tr>
            </thead>
            <tbody>
              {data.relationships.map((r) => (
                <tr key={r.name} className="border-t border-gray-100">
                  <td className="py-1 pr-3 font-mono text-violet-700"><CheckCircle2 className="mr-1 inline h-3 w-3 text-emerald-500" />{r.name}</td>
                  <td className="py-1 pr-3 font-mono">{r.from}({r.fromKeys.join(', ')})</td>
                  <td className="py-1 font-mono">{r.to}({r.toKeys.join(', ')})</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

function FromCds() {
  return (
    <div className="rounded-xl border border-sky-200 bg-sky-50/40 p-5">
      <h4 className="text-sm font-semibold text-sf-dark">From SAP CDS to the semantic view</h4>
      <p className="mt-1 max-w-4xl text-xs text-gray-700">
        SAP BDC data products are modelled in SAP with CDS (Core Data Services) and described by CSN metadata: entities,
        key fields, associations and semantic annotations. Zero-copy sharing brings the data into Snowflake as
        catalog-linked tables. <b>In this demo the semantic view is authored by hand</b> in{' '}
        <code>sql/04_semantic_view.sql</code> over the gold Dynamic Tables — it is not generated from CDS. The table shows
        the mapping a generator would use: CDS already holds most of the ontology, so it can be carried forward rather
        than re-invented.
      </p>
      <table className="mt-3 w-full text-left text-xs">
        <thead className="text-gray-500">
          <tr><th className="py-1 pr-3">SAP CDS / CSN</th><th className="py-1 pr-3">Semantic view</th><th className="py-1">Example here</th></tr>
        </thead>
        <tbody>
          {CDS_MAP.map(([a, b, c]) => (
            <tr key={a} className="border-t border-sky-100">
              <td className="py-1 pr-3 font-mono text-sky-800">{a}</td>
              <td className="py-1 pr-3">{b}</td>
              <td className="py-1 font-mono text-gray-600">{c}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-[11px] text-gray-500">
        Caveat: the gold tables join, rename and aggregate the data products, so CDS metadata maps directly only to the
        bronze tables. Generating gold-layer relationships needs lineage from each gold column back to its CDS element.
      </p>
    </div>
  );
}
