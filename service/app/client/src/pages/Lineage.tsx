import { useMemo } from 'react';
import { Card, EChart, Grid, Kpi, PageFrame, Table, WithData, fmt, usePage } from '@/components/ui';
import type { Rows } from '@/lib/api';

const SOURCE_LABEL: Record<string, string> = {
  BDC_CLD: 'SAP BDC CLDs (zero copy)', SIMULATED: 'Simulated (ACOCO_SIM)', ACOCO_CONFIG: 'ACoCo configuration',
};

/**
 * Medallion flow as a Sankey: L0 source system -> L1 domain (rows of its views from that source)
 * -> ACOCO_L2 -> L2 schema (rows of its dynamic tables). Flow widths are row counts (log-damped so small
 * domains stay visible); the tooltip shows the true rows.
 */
function lineageSankey(objs: Rows) {
  const nodes = new Map<string, { name: string }>();
  const links = new Map<string, { source: string; target: string; rows: number }>();
  const add = (name: string) => { if (!nodes.has(name)) nodes.set(name, { name }); };
  const link = (a: string, b: string, rows: number) => {
    add(a); add(b);
    const k = `${a}|${b}`;
    links.set(k, { source: a, target: b, rows: (links.get(k)?.rows ?? 0) + (Number(rows) || 0) });
  };
  const l1Domains = new Set<string>();
  for (const o of objs) {
    const parts = String(o.object_name).split('.');
    if (o.layer === 'L1') {
      const domain = `L1 ${parts[1]}`;
      l1Domains.add(domain);
      link(SOURCE_LABEL[o.source_system] ?? String(o.source_system), domain, o.row_count);
      link(domain, 'ACOCO_L2', o.row_count);
    } else if (o.layer === 'L2') {
      link('ACOCO_L2', `L2 ${parts[1] ?? 'CORE'}`, o.row_count);
    }
  }
  const data = [...links.values()].map((l) => ({ ...l, value: Math.max(1, Math.log10(1 + l.rows)) }));
  return {
    tooltip: { trigger: 'item', formatter: (p: any) => (p.dataType === 'edge' ? `${p.data.source} -> ${p.data.target}<br/>${fmt.num(p.data.rows)} rows` : p.name) },
    series: [{ type: 'sankey', left: 10, right: 130, nodeGap: 8, emphasis: { focus: 'adjacency' }, data: [...nodes.values()], links: data,
      lineStyle: { color: 'gradient', opacity: 0.35 }, label: { fontSize: 11 } }],
    _domains: l1Domains.size,
  };
}

export default function Lineage() {
  const q = usePage('lineage');
  return (
    <PageFrame id="P8" title="BDC Sources & Lineage" subtitle="Which data is real SAP BDC (catalog-linked, zero copy) and which is simulated, and how it flows L0 -> L1 -> L2 into the Semantic Views and this app.">
      <WithData q={q}>
        {(d) => <LineageBody objs={d.ln_objects} layers={d.ln_layers} />}
      </WithData>
    </PageFrame>
  );
}

function LineageBody({ objs, layers }: { objs: Rows; layers: Rows }) {
  const sankey = useMemo(() => lineageSankey(objs), [objs]);
  const l0 = objs.filter((o) => o.layer === 'L0');
  const cldRows = l0.filter((o) => o.source_system === 'BDC_CLD').reduce((s, o) => s + Number(o.row_count), 0);
  const allRows = l0.reduce((s, o) => s + Number(o.row_count), 0);
  return (
    <>
      <Grid cols={4}>
        <Kpi label="CLD tables read (L0)" info="cld_tables" value={String(l0.filter((o) => o.source_system === 'BDC_CLD').length)} sub="via connector SNOWFLAKE_APJ, read only" />
        <Kpi label="Simulated tables (L0)" info="sim_tables" value={String(l0.filter((o) => o.source_system !== 'BDC_CLD').length)} sub="ACOCO_SIM, shaped like the BDC products" />
        <Kpi label="Rows from BDC CLDs" info="cld_rows" value={fmt.pct((100 * cldRows) / (allRows || 1))} sub={`${fmt.num(cldRows)} of ${fmt.num(allRows)} L0 rows`} />
        <Kpi label="L1 views / L2 tables" info="l1_l2" value={`${objs.filter((o) => o.layer === 'L1').length} / ${objs.filter((o) => o.layer === 'L2').length}`} sub={`${sankey._domains} L1 domains`} />
      </Grid>
      <Card title="Lineage in medallion order" info="lineage_sankey" subtitle="L0 source -> L1 domain views -> L2 schemas (rows); the app reads only SERVING, SEMANTIC and ONTOLOGY">
        <EChart height={420} option={sankey} />
      </Card>
      <Grid cols={2}>
        <Card title="Summary by layer and source">
          <Table rows={layers} cols={[
            { key: 'layer', label: 'Layer' }, { key: 'object_kind', label: 'Kind' }, { key: 'source_system', label: 'Source' },
            { key: 'objects', label: 'Objects', align: 'right' }, { key: 'row_count', label: 'Rows', format: fmt.num, align: 'right' },
          ]} />
        </Card>
        <Card title="Object inventory">
          <Table max={420} rows={objs} cols={[
            { key: 'layer', label: 'Layer' }, { key: 'object_name', label: 'Object' }, { key: 'source_system', label: 'Source' },
            { key: 'row_count', label: 'Rows', format: fmt.num, align: 'right' },
          ]} />
        </Card>
      </Grid>
    </>
  );
}
