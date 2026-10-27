import { useMemo, useState } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import ReactECharts from '@/components/Chart';
import { useQuery } from '@/hooks/useQuery';
import { fetchOntology, fetchSemanticModel, type SemanticModel } from '@/lib/api';
import MetricCard, { Factory, CheckCircle2, Timer, TrendingUp } from '@/components/MetricCard';
import ChartCard from '@/components/ChartCard';
import DataTable from '@/components/DataTable';
import { ExternalLink, Network } from 'lucide-react';
import SemanticLayer from '@/pages/SemanticLayer';

// Line legend for the entity graph (ECharts' legend only covers node colours).
// Every edge points from source to target: the arrowhead is on the target end.
// `rels` names the semantic-view relationships that back an edge type; those
// edge types are drawn only when the live semantic view declares them.
const EDGE_LEGEND = [
  { color: '#10b981', dash: '', label: 'Inbound flow', meaning: 'Supplier → plant: material arriving', src: 'DT_SUPPLY_CHAIN_GEO row (SOURCE_NAME → TARGET_NAME)', rels: [] as string[] },
  { color: '#ef4444', dash: '', label: 'Outbound flow', meaning: 'Plant → customer: product shipped', src: 'DT_SUPPLY_CHAIN_GEO row', rels: [] as string[] },
  { color: '#3b82f6', dash: '', label: 'Inter-plant flow', meaning: 'Plant → plant transfer', src: 'DT_SUPPLY_CHAIN_GEO row', rels: [] as string[] },
  { color: '#8b5cf6', dash: '6 4', label: 'Supplies (dashed)', meaning: 'Supplier → material it supplies; hover for quality score', src: 'DT_SUPPLIER_QUALITY', rels: ['SUPPLIER_SUPPLIES', 'SUPPLIED_MATERIAL'] },
  { color: '#f59e0b', dash: '', label: 'BOM structure', meaning: 'Assembly → component it contains; hover for quantity', src: 'DT_BOM_EXPLOSION', rels: ['BOM_COMPONENT'] },
  { color: '#3b82f6', dash: '2 3', label: 'Produces (dotted)', meaning: 'Plant → material it manufactures (SAP production orders)', src: 'DT_PRODUCTION_ORDER_360', rels: ['PRODUCED_MATERIAL', 'PRODUCED_AT_PLANT'] },
  { color: '#0e7c86', dash: '1 3', label: 'Ordered as', meaning: 'Customer order → material ordered and plant that ships it (legend only; orders are not drawn as nodes)', src: 'DT_ORDER_FULFILLMENT', rels: ['ORDERED_MATERIAL', 'ORDERED_AT_PLANT'] },
];

type Rel = SemanticModel['relationships'][number];
const relText = (r: Rel) => `${r.from}(${r.fromKeys.join(',')}) → ${r.to}(${r.toKeys.join(',')})`;

function EdgeLegend({ rels }: { rels: Map<string, Rel> | null }) {
  return (
    <div className="mt-3 border-t border-gray-100 pt-3">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
        How to read the lines — arrows point from source to target · flow line width = monthly volume
      </p>
      <div className="grid grid-cols-1 gap-x-6 gap-y-1.5 sm:grid-cols-1 xl:grid-cols-2">
        {EDGE_LEGEND.map((e, i) => (
          <div key={e.label} className="flex items-center gap-2 text-xs">
            <svg width="44" height="10" className="shrink-0">
              <defs>
                <marker id={`edge-arr-${i}`} markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 z" fill={e.color} />
                </marker>
              </defs>
              <line x1="2" y1="5" x2="38" y2="5" stroke={e.color} strokeWidth="2" strokeDasharray={e.dash} markerEnd={`url(#edge-arr-${i})`} />
            </svg>
            <span className="font-semibold text-sf-dark">{e.label}</span>
            <span className="text-gray-500">— {e.meaning}</span>
            <span className="font-mono text-[10px] text-violet-500">[{e.src}]</span>
            {e.rels.length === 0 ? (
              <span className="text-[10px] text-gray-400">fact lane · not a relationship</span>
            ) : (
              e.rels.map((n) => {
                const r = rels?.get(n);
                return (
                  <span key={n} title={r ? relText(r) : 'not declared'} className={`rounded px-1 font-mono text-[10px] ${r ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-400'}`}>
                    {r ? '✓' : '✗'} {n}
                  </span>
                );
              })
            )}
          </div>
        ))}
      </div>
      <p className="mt-2 text-[11px] text-gray-400">
        Node colours: blue plant · green supplier · red customer · amber material/component (large = assembly).
        Hover a node to highlight its neighbours; drag to rearrange; scroll to zoom.
      </p>
      <p className="mt-1 text-[11px] text-gray-400">
        Where edges live: the edge <i>types</i> are relationships declared in the semantic view
        APP_DATA.SAP_SUPPLY_CHAIN_360 (read live via DESCRIBE SEMANTIC VIEW — ✓ = declared, hover for join keys).
        The edge <i>instances</i> are the rows of the tables in [brackets]. Flow lanes are facts in
        DT_SUPPLY_CHAIN_GEO, not relationships. Nodes come from A_SUPPLY_CHAIN_NODES plus BOM materials.
      </p>
    </div>
  );
}

const PALETTE = ['#06b6d4', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444', '#3b82f6', '#ec4899'];

// ---------------------------------------------------------------------------
// Link out to the companion Supply Chain Ontology app
//
// That app is a separate React app over the same network, and goes deeper than
// this page does: BDC ontology coverage, graph traversal, and the disruption
// scenario modelling (ripple propagation and AI mitigation planning).
//
// It keeps its current page in the URL hash, so these links land directly on the
// page named rather than dropping you on its Overview.
// Override the base with VITE_ONTOLOGY_APP_URL if you host it elsewhere.
// ---------------------------------------------------------------------------
const ONTOLOGY_APP_PUBLIC =
  import.meta.env.VITE_ONTOLOGY_APP_URL ??
  'https://sfc-gh-dfreriks.github.io/supply-chain-ontology/';
const ONTOLOGY_APP_LOCAL = 'http://localhost:5179/';
// The :5179 link only works on a laptop running the companion app's dev server,
// so show it only when this app is itself served from localhost.
const IS_LOCAL_DEV = ['localhost', '127.0.0.1'].includes(window.location.hostname);

const DEEP_LINKS = [
  { hash: 'scenario',   label: 'Scenario Studio',
    blurb: 'Pick a disruption — hurricane, supplier failure, lane closure' },
  { hash: 'ripple',     label: 'Ripple Map',
    blurb: 'Watch the impact propagate hop by hop across the network' },
  { hash: 'mitigation', label: 'Mitigation Plan',
    blurb: 'Reroutes, spare capacity, and what cannot be saved' },
  { hash: 'demo',       label: 'Guided Demo',
    blurb: 'Seven annotated steps showing which control to click' },
];

function OntologyAppLink() {
  return (
    <div className="rounded-xl border border-sf-primary/30 bg-gradient-to-br from-sky-50 via-white to-cyan-50 p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <div className="flex items-center gap-2">
            <Network className="h-5 w-5 text-sf-primary" />
            <h3 className="text-base font-bold text-sf-dark">
              Supply Chain Ontology app
            </h3>
            <span className="rounded-full bg-sf-primary/10 px-2 py-0.5 text-[11px] font-medium text-sf-primary">
              companion app
            </span>
          </div>
          <p className="mt-1.5 text-sm leading-relaxed text-sf-dark/70">
            This page shows the entity graph and BOM structure. The companion app goes
            further on the same network — SAP BDC ontology coverage, graph traversal,
            and disruption scenario modelling that propagates a shock through the
            network and plans the reroutes around it.
          </p>
        </div>
        <div className="flex shrink-0 flex-col gap-2">
          <a
            href={ONTOLOGY_APP_PUBLIC}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-sf-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:brightness-110"
          >
            Open the ontology app
            <ExternalLink className="h-4 w-4" />
          </a>
          {import.meta.env.VITE_STATIC !== '1' && IS_LOCAL_DEV && (
          <a
            href={ONTOLOGY_APP_LOCAL}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center justify-center gap-1.5 text-xs text-sf-dark/60 underline decoration-dotted transition hover:text-sf-primary"
            title="Needs the ontology app running locally on port 5179"
          >
            or open the local build on :5179
          </a>
          )}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-2 border-t border-sf-primary/15 pt-4 sm:grid-cols-2 lg:grid-cols-4">
        {DEEP_LINKS.map((d) => (
          <a
            key={d.hash}
            href={`${ONTOLOGY_APP_PUBLIC.replace(/\/$/, '')}/#${d.hash}`}
            target="_blank"
            rel="noreferrer"
            className="group rounded-lg border border-gray-200 bg-white/70 px-3 py-2.5 transition hover:border-sf-primary/50 hover:bg-white hover:shadow-sm"
          >
            <div className="flex items-center gap-1.5 text-sm font-semibold text-sf-dark group-hover:text-sf-primary">
              {d.label}
              <ExternalLink className="h-3 w-3 opacity-0 transition group-hover:opacity-60" />
            </div>
            <div className="mt-0.5 text-[11px] leading-snug text-sf-dark/55">{d.blurb}</div>
          </a>
        ))}
      </div>
    </div>
  );
}

const tabClass =
  'px-4 py-2 text-sm font-medium text-sf-dark/60 data-[state=active]:text-sf-primary data-[state=active]:border-b-2 data-[state=active]:border-sf-primary';

interface OntologyNode {
  node_id: string;
  node_name: string;
  node_type: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  plant: string;
}

interface Flow {
  flow_id: string;
  flow_type: string;
  material_category: string;
  monthly_volume: number;
  monthly_value: number;
  source_name: string;
  source_type: string;
  target_name: string;
  target_type: string;
}

interface BomRow {
  parent_material: string;
  parent_desc: string;
  bom_level: number;
  component_material: string;
  component_desc: string;
  component_qty: number;
  component_cost: number;
}

interface Supplier {
  supplier_name: string;
  material_desc: string;
  defect_rate_pct: number;
  on_time_delivery_pct: number;
  quality_score: number;
}

interface Production {
  plant_name: string;
  material_desc: string;
}

interface OntologyData {
  nodes: OntologyNode[];
  flows: Flow[];
  bom: BomRow[];
  suppliers: Supplier[];
  production: Production[];
}

const NODE_CATEGORIES = [
  { name: 'Plant', itemStyle: { color: '#3b82f6' } },
  { name: 'Supplier', itemStyle: { color: '#10b981' } },
  { name: 'Customer', itemStyle: { color: '#ef4444' } },
  { name: 'Material', itemStyle: { color: '#f59e0b' } },
  { name: 'Work Center', itemStyle: { color: '#8b5cf6' } },
];

export default function Ontology() {
  const { data, loading, error } = useQuery<OntologyData>(fetchOntology, []);
  const { data: model } = useQuery<SemanticModel>(fetchSemanticModel, []);
  const rels = useMemo(
    () => (model?.relationships ? new Map(model.relationships.map((r) => [r.name, r])) : null),
    [model],
  );

  const graphData = useMemo(() => {
    if (!data) return null;
    // Until the model loads (or if it can't be read) fall back to drawing every edge type.
    const declared = (label: string) => {
      const names = EDGE_LEGEND.find((e) => e.label === label)?.rels ?? [];
      return !rels || names.some((n) => rels.has(n));
    };

    // Build graph nodes from supply chain nodes
    const graphNodes: any[] = [];
    const nodeNames = new Set<string>();

    for (const n of data.nodes) {
      const catIdx = NODE_CATEGORIES.findIndex((c) => c.name === n.node_type);
      graphNodes.push({
        name: n.node_name,
        category: catIdx >= 0 ? catIdx : 0,
        symbolSize: n.node_type === 'Plant' ? 50 : 35,
        value: `${n.node_type} | ${n.city}, ${n.country}`,
      });
      nodeNames.add(n.node_name);
    }

    // Add material nodes from BOM
    const materials = new Set<string>();
    for (const b of data.bom) {
      if (!materials.has(b.parent_desc)) {
        materials.add(b.parent_desc);
        if (!nodeNames.has(b.parent_desc)) {
          graphNodes.push({
            name: b.parent_desc,
            category: 3,
            symbolSize: 40,
            value: `Material | ${b.parent_material}`,
          });
          nodeNames.add(b.parent_desc);
        }
      }
      if (!materials.has(b.component_desc)) {
        materials.add(b.component_desc);
        if (!nodeNames.has(b.component_desc)) {
          graphNodes.push({
            name: b.component_desc,
            category: 3,
            symbolSize: 25,
            value: `Component | ${b.component_material}`,
          });
          nodeNames.add(b.component_desc);
        }
      }
    }

    // Build edges from flows
    const graphEdges: any[] = [];
    for (const f of data.flows) {
      if (nodeNames.has(f.source_name) && nodeNames.has(f.target_name)) {
        graphEdges.push({
          source: f.source_name,
          target: f.target_name,
          value: `${f.flow_type} flow · ${f.material_category}`,
          lineStyle: {
            width: Math.max(1, Math.min(6, f.monthly_volume / 10)),
            color: f.flow_type === 'Inbound' ? '#10b981' : f.flow_type === 'Outbound' ? '#ef4444' : '#3b82f6',
          },
        });
      }
    }

    // Add supplier → material edges
    for (const s of declared('Supplies (dashed)') ? data.suppliers : []) {
      if (nodeNames.has(s.supplier_name) && nodeNames.has(s.material_desc)) {
        graphEdges.push({
          source: s.supplier_name,
          target: s.material_desc,
          value: `Supplies · quality score ${s.quality_score}`,
          lineStyle: { width: 2, color: '#8b5cf6', type: 'dashed' },
        });
      }
    }

    // Add BOM hierarchy edges (parent → component)
    const bomEdgeSet = new Set<string>();
    for (const b of declared('BOM structure') ? data.bom : []) {
      const key = `${b.parent_desc}→${b.component_desc}`;
      if (!bomEdgeSet.has(key) && nodeNames.has(b.parent_desc) && nodeNames.has(b.component_desc)) {
        bomEdgeSet.add(key);
        graphEdges.push({
          source: b.parent_desc,
          target: b.component_desc,
          value: `BOM: contains component ×${b.component_qty}`,
          lineStyle: { width: 1.5, color: '#f59e0b', type: 'solid' },
        });
      }
    }

    // Add material → plant edges using actual production order data
    for (const p of declared('Produces (dotted)') ? data.production : []) {
      if (nodeNames.has(p.plant_name) && nodeNames.has(p.material_desc)) {
        const mkey = `${p.plant_name}→${p.material_desc}`;
        if (!bomEdgeSet.has(mkey)) {
          bomEdgeSet.add(mkey);
          graphEdges.push({
            source: p.plant_name,
            target: p.material_desc,
            value: 'Produces (from SAP production orders)',
            lineStyle: { width: 2, color: '#3b82f6', type: 'dotted' },
          });
        }
      }
    }

    return { nodes: graphNodes, edges: graphEdges };
  }, [data, rels]);

  // Build list of top-level products for BOM selector
  const bomProducts = useMemo(() => {
    if (!data) return [];
    const topLevel = new Set<string>();
    for (const b of data.bom) {
      if (b.bom_level === 0) {
        topLevel.add(b.parent_desc);
      }
    }
    return [...topLevel].sort();
  }, [data]);

  const [selectedBomProduct, setSelectedBomProduct] = useState<string>('');

  // Build recursive tree for the selected product
  const bomTreeData = useMemo(() => {
    if (!data || !selectedBomProduct) return null;

    // Build a map: parent_desc → children[]
    const childrenMap = new Map<string, { desc: string; material: string; qty: number; cost: number }[]>();
    for (const b of data.bom) {
      if (!childrenMap.has(b.parent_desc)) {
        childrenMap.set(b.parent_desc, []);
      }
      childrenMap.get(b.parent_desc)!.push({
        desc: b.component_desc,
        material: b.component_material,
        qty: b.component_qty,
        cost: b.component_cost,
      });
    }

    // Recursively build tree
    function buildNode(name: string, qty?: number, cost?: number): any {
      const children = childrenMap.get(name);
      const label = qty ? `${name} (x${qty})` : name;
      const node: any = {
        name: label,
        value: cost ? `$${Number(cost).toLocaleString()}` : '',
        children: [],
      };
      if (children) {
        node.children = children.map((c) => buildNode(c.desc, c.qty, c.cost));
      }
      return node;
    }

    return buildNode(selectedBomProduct);
  }, [data, selectedBomProduct]);

  if (loading) {
    return (
      <div className="space-y-6">
        <OntologyAppLink />
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-32 animate-pulse rounded-xl bg-sky-100/60" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <OntologyAppLink />
        <div className="rounded-xl bg-red-50 p-4 text-red-700">Error: {error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <OntologyAppLink />
        <p className="py-4 text-center text-sm text-gray-400">No data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <OntologyAppLink />
      <Tabs.Root defaultValue="semantic">
      <Tabs.List className="mb-6 flex gap-1 border-b border-gray-200">
        <Tabs.Trigger value="semantic" data-tour="ontology-tab-semantic" className={tabClass}>Semantic Layer = Ontology</Tabs.Trigger>
        <Tabs.Trigger value="graph" data-tour="ontology-tab-graph" className={tabClass}>Entity Graph</Tabs.Trigger>
        <Tabs.Trigger value="bom" className={tabClass}>BOM Hierarchy</Tabs.Trigger>
        <Tabs.Trigger value="datamodel" className={tabClass}>Data Model</Tabs.Trigger>
      </Tabs.List>

      <Tabs.Content value="semantic" className="space-y-6">
        <SemanticLayer />
      </Tabs.Content>

      <Tabs.Content value="graph" className="space-y-6">
        <div className="grid grid-cols-4 gap-5">
          <MetricCard title="Network Nodes" value={String(data.nodes.length)} icon={Factory} accent="border-cyan-400/50 bg-gradient-to-br from-cyan-50 via-white to-cyan-100" />
          <MetricCard title="Material Flows" value={String(data.flows.length)} icon={CheckCircle2} accent="border-emerald-400/50 bg-gradient-to-br from-emerald-50 via-white to-emerald-100" />
          <MetricCard title="BOM Components" value={String(data.bom.length)} icon={Timer} accent="border-violet-400/50 bg-gradient-to-br from-violet-50 via-white to-violet-100" />
          <MetricCard title="Suppliers Tracked" value={String(new Set(data.suppliers.map((s: Supplier) => s.supplier_name)).size)} icon={TrendingUp} accent="border-amber-400/50 bg-gradient-to-br from-amber-50 via-white to-amber-100" />
        </div>

        <ChartCard tourId="ontology-graph" title="Supply Chain Entity Relationship Graph" subtitle="Interactive force-directed graph of plants, suppliers, materials, and flows">
          {graphData && (
            <ReactECharts
              option={{
                tooltip: {
                  trigger: 'item',
                  formatter: (params: any) => {
                    if (params.dataType === 'node') return `<strong>${params.name}</strong><br/>${params.value}`;
                    if (params.dataType === 'edge') return `${params.data.source} → ${params.data.target}<br/>${params.data.value}`;
                    return '';
                  },
                },
                legend: {
                  data: NODE_CATEGORIES.map((c) => c.name),
                  bottom: 10,
                  textStyle: { color: '#6b7280', fontSize: 11 },
                },
                animationDuration: 1500,
                animationEasingUpdate: 'quinticInOut',
                series: [
                  {
                    type: 'graph',
                    layout: 'force',
                    data: graphData.nodes,
                    links: graphData.edges,
                    categories: NODE_CATEGORIES,
                    roam: true,
                    draggable: true,
                    label: {
                      show: true,
                      position: 'right',
                      fontSize: 10,
                      color: '#374151',
                    },
                    force: {
                      repulsion: 300,
                      gravity: 0.1,
                      edgeLength: [80, 200],
                      layoutAnimation: true,
                    },
                    emphasis: {
                      focus: 'adjacency',
                      lineStyle: { width: 5 },
                    },
                    lineStyle: { curveness: 0.2, opacity: 0.7 },
                    edgeSymbol: ['none', 'arrow'],
                    edgeSymbolSize: 8,
                  },
                ],
              }}
              style={{ height: 800 }}
            />
          )}
          <EdgeLegend rels={rels} />
        </ChartCard>
      </Tabs.Content>

      <Tabs.Content value="bom" className="space-y-6">
        {/* Product selector */}
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-sf-dark">Select Product:</label>
          <select
            value={selectedBomProduct}
            onChange={(e) => setSelectedBomProduct(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-sf-dark shadow-sm focus:border-sf-primary focus:outline-none focus:ring-1 focus:ring-sf-primary"
          >
            <option value="">-- Choose a top-level product --</option>
            {bomProducts.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          {selectedBomProduct && bomTreeData && (
            <span className="text-xs text-gray-500">
              {bomTreeData.children?.length || 0} direct components
            </span>
          )}
        </div>

        {!selectedBomProduct && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-center text-amber-800">
            Select a top-level product above to explore its Bill of Materials hierarchy.
          </div>
        )}

        {selectedBomProduct && bomTreeData && (
          <ChartCard title={`BOM: ${selectedBomProduct}`} subtitle="Expandable product structure tree — click nodes to expand/collapse">
            <ReactECharts
              option={{
                tooltip: {
                  trigger: 'item',
                  formatter: (params: any) => `<strong>${params.name}</strong><br/>${params.value || ''}`,
                },
                series: [
                  {
                    type: 'tree',
                    data: [bomTreeData],
                    top: '5%',
                    left: '12%',
                    bottom: '5%',
                    right: '20%',
                    symbolSize: 12,
                    orient: 'LR',
                    label: {
                      position: 'left',
                      verticalAlign: 'middle',
                      align: 'right',
                      fontSize: 12,
                      color: '#374151',
                      fontWeight: 'bold',
                    },
                    leaves: {
                      label: {
                        position: 'right',
                        verticalAlign: 'middle',
                        align: 'left',
                        fontWeight: 'normal',
                      },
                    },
                    emphasis: { focus: 'descendant' },
                    expandAndCollapse: true,
                    animationDuration: 550,
                    animationDurationUpdate: 750,
                    initialTreeDepth: 3,
                    itemStyle: { color: '#06b6d4', borderColor: '#0891b2' },
                    lineStyle: { color: '#d1d5db', width: 1.5 },
                  },
                ],
              }}
              style={{ height: 600 }}
            />
          </ChartCard>
        )}

        {selectedBomProduct && (
        <ChartCard title={`Component Costs: ${selectedBomProduct}`} subtitle="Direct component cost breakdown for selected product">
          <ReactECharts
            option={{
              tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
              grid: { top: 10, right: 30, bottom: 30, left: 180 },
              xAxis: {
                type: 'value',
                axisLabel: { color: '#6b7280', fontSize: 11, formatter: (v: number) => `$${(v / 1000).toFixed(0)}k` },
                splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
              },
              yAxis: {
                type: 'category',
                data: data.bom
                  .filter((b: BomRow) => b.parent_desc === selectedBomProduct)
                  .sort((a: BomRow, b: BomRow) => b.component_cost - a.component_cost)
                  .map((b: BomRow) => b.component_desc),
                axisLabel: { color: '#374151', fontSize: 10, width: 160, overflow: 'truncate' },
                axisLine: { show: false },
                axisTick: { show: false },
              },
              series: [
                {
                  type: 'bar',
                  data: data.bom
                    .filter((b: BomRow) => b.parent_desc === selectedBomProduct)
                    .sort((a: BomRow, b: BomRow) => b.component_cost - a.component_cost)
                    .map((b: BomRow, i: number) => ({
                      value: b.component_cost,
                      itemStyle: {
                        color: {
                          type: 'linear',
                          x: 0, y: 0, x2: 1, y2: 0,
                          colorStops: [
                            { offset: 0, color: PALETTE[i % PALETTE.length] },
                            { offset: 1, color: PALETTE[i % PALETTE.length] + '60' },
                          ],
                        },
                        borderRadius: [0, 5, 5, 0],
                      },
                    })),
                  barWidth: '55%',
                },
              ],
              animationDuration: 900,
              animationEasing: 'elasticOut',
            }}
            style={{ height: 350 }}
          />
        </ChartCard>
        )}
      </Tabs.Content>

      <Tabs.Content value="datamodel" className="space-y-6">
        <ChartCard title="Supply Chain Nodes" subtitle="All entities in the supply chain network">
          <DataTable
            columns={[
              { key: 'node_id', label: 'ID' },
              { key: 'node_name', label: 'Name' },
              { key: 'node_type', label: 'Type' },
              { key: 'city', label: 'City' },
              { key: 'country', label: 'Country' },
            ]}
            data={data.nodes}
          />
        </ChartCard>

        <ChartCard title="Supplier Quality Relationships" subtitle="Supplier → Material quality metrics">
          <DataTable
            columns={[
              { key: 'supplier_name', label: 'Supplier' },
              { key: 'material_desc', label: 'Material' },
              { key: 'defect_rate_pct', label: 'Defect Rate %' },
              { key: 'on_time_delivery_pct', label: 'OTD %' },
              { key: 'quality_score', label: 'Quality Score' },
            ]}
            data={data.suppliers}
          />
        </ChartCard>

        <ChartCard title="Material Flows" subtitle="All supply chain flow connections">
          <DataTable
            columns={[
              { key: 'source_name', label: 'Source' },
              { key: 'source_type', label: 'Source Type' },
              { key: 'target_name', label: 'Target' },
              { key: 'target_type', label: 'Target Type' },
              { key: 'material_category', label: 'Material' },
              { key: 'monthly_volume', label: 'Volume' },
              { key: 'monthly_value', label: 'Value ($)' },
            ]}
            data={data.flows}
          />
        </ChartCard>
      </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
