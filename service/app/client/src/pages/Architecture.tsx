import { useMemo, useState, type ReactNode } from 'react';
import { Card, EChart, Grid, PageFrame, Table, WithData, fmt, usePage } from '@/components/ui';
import type { Rows } from '@/lib/api';

/** Owning-system class for colouring (PRD 5.3): S/4HANA, People Intelligence, or non-SAP / derived. */
function systemClass(owning: string): { key: string; color: string } {
  if (/People Intelligence/i.test(owning)) return { key: 'SAP People Intelligence', color: '#7D44CF' };
  if (/S\/4HANA/i.test(owning)) return { key: 'SAP S/4HANA', color: '#11567F' };
  return { key: 'Non-SAP / derived', color: '#FF9F36' };
}

const LAYERS = [
  { id: 'L0', name: 'Sources (L0)', text: 'SAP BDC catalog-linked databases (zero copy, read only) plus ACOCO_SIM for data products not yet shared.' },
  { id: 'L1', name: 'Domains (L1)', text: 'ACOCO_L1: nine domain schemas of views; one business object per source shape, SOURCE_SYSTEM on every row.' },
  { id: 'L2', name: 'Assets (L2)', text: 'ACOCO_L2: CORE, ONTOLOGY (ENT_* / REL_* / ONT_*), five marts of dynamic tables, REASONING (ML, embeddings, search).' },
  { id: 'SEM', name: 'Semantic layer', text: 'Five Semantic Views (one per pillar + portfolio) built on the shared ontology entities.' },
  { id: 'APP', name: 'Experience', text: 'This Command Center (SERVING / SEMANTIC / ONTOLOGY only) and the Cortex Agent ACOCO_ADVISOR.' },
];

function Graph({ rows, onPick, picked }: { rows: Rows; onPick: (e: string) => void; picked: string | null }) {
  const option = useMemo(() => {
    const nodes = rows.filter((r) => r.item === 'NODE');
    const edges = rows.filter((r) => r.item === 'EDGE');
    const classes = ['SAP S/4HANA', 'SAP People Intelligence', 'Non-SAP / derived'];
    const maxRows = Math.max(...nodes.map((n) => Number(n.row_count) || 1));
    return {
      tooltip: { formatter: (p: any) => (p.dataType === 'edge' ? `${p.data.source} <b>${p.data.verb}</b> ${p.data.target}` : `<b>${p.data.name}</b><br/>${p.data.owning}<br/>${fmt.num(p.data.rows)} rows`) },
      legend: { data: classes, top: 0 },
      series: [{
        type: 'graph', layout: 'force', roam: true, draggable: true,
        force: { repulsion: 520, edgeLength: [90, 170], gravity: 0.08 },
        categories: classes.map((c) => ({ name: c, itemStyle: { color: systemClass(c === 'SAP S/4HANA' ? 'S/4HANA' : c).color } })),
        label: { show: true, position: 'bottom', fontSize: 11 },
        edgeSymbol: ['none', 'arrow'], edgeSymbolSize: 7,
        edgeLabel: { show: true, formatter: (p: any) => p.data.verb, fontSize: 9, color: '#666' },
        lineStyle: { color: '#9ca3af', curveness: 0.15 },
        emphasis: { focus: 'adjacency' },
        data: nodes.map((n) => ({
          name: n.from_entity, owning: n.owning_system, rows: n.row_count,
          category: classes.indexOf(systemClass(String(n.owning_system)).key),
          symbolSize: 22 + 26 * Math.sqrt((Number(n.row_count) || 1) / maxRows),
          itemStyle: picked === n.from_entity ? { borderColor: '#111', borderWidth: 3 } : undefined,
        })),
        links: edges.map((e) => ({ source: e.from_entity, target: e.to_entity, verb: e.verb })),
      }],
    };
  }, [rows, picked]);
  return <EChart option={option} height={520} onClick={(p) => p.dataType === 'node' && onPick(p.data.name)} />;
}

function EntityDetail({ rows, entity }: { rows: Rows; entity: string }) {
  const n = rows.find((r) => r.item === 'NODE' && r.from_entity === entity);
  if (!n) return null;
  const rels = rows.filter((r) => r.item === 'EDGE' && (r.from_entity === entity || r.to_entity === entity));
  const l0 = String(n.l0_sources ?? '').split('; ').filter(Boolean);
  const cls = systemClass(String(n.owning_system));
  const step = (label: string, body: ReactNode, color: string) => (
    <div className="rounded-lg border p-3" style={{ borderColor: color }}>
      <p className="text-[10px] font-bold uppercase tracking-wider" style={{ color }}>{label}</p>
      <div className="mt-1 break-all font-mono text-xs text-gray-800">{body}</div>
    </div>
  );
  return (
    <div className="space-y-3">
      <div>
        <p className="text-lg font-bold text-gray-900">{entity}</p>
        <p className="text-xs text-gray-500">{n.definition}</p>
        <p className="mt-1 text-xs"><span className="rounded px-1.5 py-0.5 text-white" style={{ background: cls.color }}>{n.owning_system}</span></p>
      </div>
      {step('L0 - SAP data product / source', l0.map((s) => <div key={s}>{s}</div>), '#8A8D91')}
      <p className="text-center text-gray-400">↓</p>
      {step('L1 - domain object', n.l1_source, '#29B5E8')}
      <p className="text-center text-gray-400">↓</p>
      {step('L2 - ontology entity', <>{n.l2_table}<div className="mt-1 font-sans text-gray-500">key {n.primary_key} - {fmt.num(n.row_count)} rows - {fmt.pct(n.bdc_cld_share_pct)} from BDC CLDs</div></>, '#11567F')}
      <p className="text-center text-gray-400">↓</p>
      {step('Semantic Views', n.semantic_views || '-', '#7D44CF')}
      <Table max={220} rows={rels} cols={[
        { key: 'from_entity', label: 'From' }, { key: 'verb', label: 'Relationship' }, { key: 'to_entity', label: 'To' }, { key: 'definition', label: 'Cardinality' },
      ]} />
    </div>
  );
}

export default function Architecture() {
  const q = usePage('ontology');
  const [picked, setPicked] = useState<string | null>('project');
  return (
    <PageFrame id="C4" title="Platform Architecture" subtitle="SAP is the system of record; Snowflake adds context and reasoning. Five layers, one ontology, zero-copy sources and a fee boundary the app never crosses.">
      <div className="grid grid-cols-1 gap-2 md:grid-cols-5">
        {LAYERS.map((l, i) => (
          <div key={l.id} className="rounded-xl border border-sf-primary/30 bg-gradient-to-b from-sky-50 to-white p-3">
            <p className="text-[10px] font-bold uppercase text-sf-primary">{i + 1}. {l.id}</p>
            <p className="text-sm font-bold text-gray-900">{l.name}</p>
            <p className="mt-1 text-xs text-gray-600">{l.text}</p>
          </div>
        ))}
      </div>
      <WithData q={q}>
        {(d) => (
          <>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card className="lg:col-span-2" title="Ontology graph" info="ontology" subtitle="13 entities and 18 relationships from ACOCO_L2.ONTOLOGY (via SERVING.VW_ONTOLOGY_GRAPH); size = rows. Click an entity.">
                <Graph rows={d.on_graph} picked={picked} onPick={setPicked} />
              </Card>
              <Card title="Entity lineage" info="entity_lineage" subtitle="L0 -> L1 -> L2 -> Semantic Views">
                {picked ? <EntityDetail rows={d.on_graph} entity={picked} /> : <p className="text-sm text-gray-400">Click an entity in the graph.</p>}
              </Card>
            </div>
            <Grid cols={2}>
              <Card title="Medallion contract and fee boundary">
                <ul className="list-disc space-y-1 pl-5 text-sm text-gray-600">
                  <li><b>L0</b> is read only: CLDs are shared by SAP BDC with zero copy; nothing is altered on them or on the connector.</li>
                  <li><b>L1</b> views are the only readers of L0; each domain may read only its declared sources (linted).</li>
                  <li><b>L2</b> reads only L1; the marts are dynamic tables refreshed hourly.</li>
                  <li>The <b>app</b> reads only <code>ACOCO_L2.SERVING</code>, <code>SEMANTIC</code> and <code>ONTOLOGY</code> - enforced by <code>tools/lint_app.py</code> and evidenced by <code>ACCESS_HISTORY</code> on P9.</li>
                </ul>
              </Card>
              <Card title="Object inventory" subtitle="Latest lineage snapshot">
                <Table rows={Object.values(d.on_lineage.reduce((acc: Record<string, any>, r) => {
                  const k = `${r.layer} ${r.object_kind}`;
                  acc[k] = acc[k] ?? { layer: r.layer, kind: r.object_kind, objects: 0, rows: 0 };
                  acc[k].objects += 1; acc[k].rows += Number(r.row_count) || 0;
                  return acc;
                }, {}))} cols={[
                  { key: 'layer', label: 'Layer' }, { key: 'kind', label: 'Kind' },
                  { key: 'objects', label: 'Objects', align: 'right' }, { key: 'rows', label: 'Rows', format: fmt.num, align: 'right' },
                ]} />
              </Card>
            </Grid>
          </>
        )}
      </WithData>
    </PageFrame>
  );
}
