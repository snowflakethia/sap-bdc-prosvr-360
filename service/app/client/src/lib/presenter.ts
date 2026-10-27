// ---------------------------------------------------------------------------
// Presenter content — one place to edit the talk track and KPI definitions.
//   PRESENTER_NOTES: per-page hover notes (aspiration/problem → Snowflake → say this)
//   KPI_INFO:        metric definitions shown by the "i" icon on cards/charts.
// Formulas mirror the SQL in server/src/routes (api.ts, ops.ts) and the base
// tables of the SAP_SUPPLY_CHAIN_360 semantic view.
// ---------------------------------------------------------------------------
import type { PageId } from '@/components/Sidebar';

export interface PresenterNote {
  aspiration: string;
  snowflake: string[];
  sayThis: string;
}

export const PRESENTER_NOTES: Record<PageId, PresenterNote> = {
  scenario: {
    aspiration: 'One trusted, explainable view of supply risk across plants, suppliers and customers — in minutes, not weeks.',
    snowflake: ['SAP BDC data products arrive zero-copy, with business context intact', 'One semantic view feeds dashboards, SQL and AI alike'],
    sayThis: 'This is not a dashboard project — it is a program to make SAP data answer business questions directly.',
  },
  architecture: {
    aspiration: 'Use SAP data outside SAP without building, paying for and babysitting extraction pipelines.',
    snowflake: ['Catalog-linked databases (CLD) mount BDC data products zero-copy', 'Dynamic Tables build the medallion declaratively', 'Horizon governs every layer; Native App ships it anywhere'],
    sayThis: 'Everything right of the CLD is Snowflake-native — no external engine, no copies to reconcile.',
  },
  overview: {
    aspiration: 'Executives want one version of OEE, yield and delivery across every plant.',
    snowflake: ['KPIs computed from Dynamic Tables over SAP BDC data', 'Same definitions reused by Cortex Analyst via the semantic view'],
    sayThis: 'Every number here has the same definition the AI uses — hover the i icons.',
  },
  production: {
    aspiration: 'Planners need to see where capacity turns into scrap and delay, per plant and product.',
    snowflake: ['Production orders from SAP BDC, refreshed by Dynamic Tables', 'Ask Cortex explains the trend using live SQL facts'],
    sayThis: 'Yield and scrap come straight from SAP confirmations — no spreadsheet reconciliation.',
  },
  bom: {
    aspiration: 'Engineering and procurement want cost and risk rolled up through the product structure.',
    snowflake: ['Multi-level BOM explosion as a Dynamic Table', 'BOM is a first-class entity in the ontology (semantic view)'],
    sayThis: 'The BOM is the spine of the ontology — it links suppliers to plants to customer orders.',
  },
  inventory: {
    aspiration: 'Finance wants working capital freed; operations wants no stock-outs.',
    snowflake: ['Stock positions from SAP BDC with turnover and obsolescence computed in SQL', 'Governed sharing to finance without copies'],
    sayThis: 'Obsolete stock and turnover are calculated once, governed once, used everywhere.',
  },
  logistics: {
    aspiration: 'Customer service needs to know which shipping points break the delivery promise.',
    snowflake: ['Delivery performance joined to inventory in the semantic view', 'Natural-language drill-down via Cortex Analyst'],
    sayThis: 'Late is defined once — the dashboard and the AI agree by construction.',
  },
  fulfillment: {
    aspiration: 'Sales wants OTIF up and the cost of lateness explained by root cause.',
    snowflake: ['Order lines with late cost and cause in a Dynamic Table', 'Ask Cortex traces cause → units lost → ship slip → cost'],
    sayThis: 'We move from "we were late" to "equipment cost us $X, shortages cost us $Y".',
  },
  equipment: {
    aspiration: 'Maintenance wants to act 48 hours before a tool fails, not after.',
    snowflake: ['Sensor readings next to SAP work centers in one platform', 'Risk scoring in SQL; can extend to Snowflake ML'],
    sayThis: 'Operational telemetry and SAP master data meet without an integration project.',
  },
  components: {
    aspiration: 'Quality wants serial-level traceability from supplier lot to customer.',
    snowflake: ['Digital thread joins lots, inspections and orders in SQL', 'Lineage visible in Horizon'],
    sayThis: 'A recall question becomes a single query, not a week of emails.',
  },
  workcenter: {
    aspiration: 'Operations needs to find bottlenecks before they set the ship date.',
    snowflake: ['Available vs used hours from SAP work centers', 'Utilisation thresholds governed in the semantic layer'],
    sayThis: 'Bottlenecks are visible across plants because the data is no longer siloed per site.',
  },
  projects: {
    aspiration: 'PMO wants budget and schedule variance on capital projects in one place.',
    snowflake: ['SAP project/WBS data products, zero-copy', 'Same platform as operations data — no separate PMO extract'],
    sayThis: 'Capital projects sit next to the operations they are meant to improve.',
  },
  supplychain: {
    aspiration: 'Supply-chain leaders want to see concentration risk across the physical network.',
    snowflake: ['Nodes and flows modelled as entities in the ontology', 'Geo data served from Dynamic Tables to a Native App'],
    sayThis: 'This map is a view over the ontology — the same graph the AI traverses.',
  },
  ontology: {
    aspiration: 'Give people and AI one shared model of what a supplier, material, plant and flow are — and how they relate.',
    snowflake: ['Semantic view = governed ontology: entities, relationships, facts, metrics, synonyms', 'Cortex Analyst and Agents reason over it directly'],
    sayThis: 'The semantic layer is what turns tables into an ontology the business and the AI both understand.',
  },
  optimization: {
    aspiration: 'Leadership wants the next best action ranked by value, not another report.',
    snowflake: ['Optimization levers computed over the same governed data', 'Cortex explains the trade-offs in plain language'],
    sayThis: 'We go from describing the supply chain to prescribing what to change.',
  },
  forecasting: {
    aspiration: 'Planning wants a forward view of demand, OEE, scrap and supplier quality.',
    snowflake: ['Trends and projections in SQL over Dynamic Tables', 'Extendable to SNOWFLAKE.ML.FORECAST without moving data'],
    sayThis: 'Forecasts run where the SAP data already lives.',
  },
  lineage: {
    aspiration: 'Architects need to prove where every number came from.',
    snowflake: ['L0 CLD → L2 Dynamic Tables → serving views → semantic view → app', 'Synthetic demo rows are labelled, never hidden'],
    sayThis: 'Every figure traces back to an SAP BDC data product — or is flagged as demo data.',
  },
  analyst: {
    aspiration: 'Business users want to ask What, Why, What-next, What-if and How-to — and trust the answer.',
    snowflake: ['Cortex Analyst generates SQL over the semantic view — answers are inspectable', 'Verified queries and synonyms raise accuracy'],
    sayThis: 'Every answer shows its SQL — explainable AI, grounded in the ontology.',
  },
};

export interface KpiInfo {
  definition: string;
  formula?: string;
  source: string;
}

const PO = 'SAP BDC production order data products → ANALYTICS.DT_PRODUCTION_ORDER_360';
const MK = 'Monthly plant KPIs → ANALYTICS.DT_MANUFACTURING_KPI';
const INV = 'SAP BDC stock data products → ANALYTICS.DT_INVENTORY_OVERVIEW';
const DEL = 'SAP BDC outbound deliveries → ANALYTICS.DT_DELIVERY_PERFORMANCE';
const GEO = 'ANALYTICS.DT_SUPPLY_CHAIN_GEO (L0 flows + SUPPLIER_EXT demo flows)';

export const KPI_INFO: Record<string, KpiInfo> = {
  'production orders': { definition: 'Number of SAP production orders in the selected plants.', formula: 'COUNT(production orders)', source: PO },
  'total orders': { definition: 'Number of orders in scope.', formula: 'COUNT(*)', source: PO },
  'confirmed qty': { definition: 'Quantity confirmed (reported complete) against production orders.', formula: 'SUM(CONFIRMED_QTY)', source: PO },
  'total confirmed': { definition: 'Quantity confirmed against production orders.', formula: 'SUM(CONFIRMED_QTY)', source: PO },
  'total planned': { definition: 'Quantity planned on production orders.', formula: 'SUM(PLANNED_QTY)', source: PO },
  'avg cycle time': { definition: 'Average days from order start to finish.', formula: 'AVG(CYCLE_TIME_DAYS)', source: PO },
  'yield %': { definition: 'Good output as a share of planned quantity.', formula: '100 × SUM(YIELD_QTY) ÷ SUM(PLANNED_QTY)', source: PO },
  'oee': { definition: 'Overall Equipment Effectiveness — how much of planned production time is truly productive.', formula: 'Availability × Performance × Quality (averaged per plant-month: AVG(OEE_PCT))', source: MK },
  'avg oee': { definition: 'Average OEE across plants and months in scope.', formula: 'AVG(OEE_PCT)', source: MK },
  'scrap rate': { definition: 'Share of output scrapped.', formula: 'AVG(SCRAP_RATE_PCT) per plant-month', source: MK },
  'avg scrap rate': { definition: 'Average scrap rate across plants and months.', formula: 'AVG(SCRAP_RATE_PCT)', source: MK },
  'on-time delivery': { definition: 'Share of deliveries shipped on or before the promised date.', formula: 'AVG(ON_TIME_DELIVERY_PCT) per plant-month', source: MK },
  'on-time %': { definition: 'Deliveries flagged on time as a share of all deliveries.', formula: '100 × COUNT(ON_TIME_FLAG = Y) ÷ COUNT(*)', source: DEL },
  'avg delay (late)': { definition: 'Average days late, counting late deliveries only.', formula: 'AVG(DELAY_DAYS) where DELAY_DAYS > 0', source: DEL },
  'total deliveries': { definition: 'Number of outbound deliveries.', formula: 'COUNT(*)', source: DEL },
  'total qty shipped': { definition: 'Quantity shipped on outbound deliveries.', formula: 'SUM(delivered qty)', source: DEL },
  'inventory turnover': { definition: 'How many times inventory is consumed and replaced per year.', formula: 'AVG(INVENTORY_TURNOVER) — annual COGS ÷ average inventory', source: MK },
  'total stock value': { definition: 'Value of stock on hand.', formula: 'SUM(stock value)', source: INV },
  'obsolete %': { definition: 'Share of inventory flagged obsolete (no movement).', formula: 'obsolete stock value ÷ total stock value', source: INV },
  'avg days of inventory': { definition: 'Days of demand the current stock covers.', formula: 'AVG(DAYS_OF_INVENTORY)', source: INV },
  'otif': { definition: 'On-Time In-Full: order lines delivered complete and on the promised date.', formula: '100 × COUNT_IF(OTIF) ÷ COUNT(order lines)', source: 'ANALYTICS.DT_ORDER_FULFILLMENT (demo enrichment keyed to SAP plants/materials)' },
  'late-delivery cost': { definition: 'Cost of lateness: contractual penalty plus expedite spend.', formula: 'SUM(PENALTY_USD + EXPEDITE_USD)', source: 'ANALYTICS.DT_ORDER_FULFILLMENT' },
  'open orders at risk': { definition: 'Open order lines not yet shipped and flagged at risk of missing the committed date.', formula: "COUNT_IF(ORDER_STATUS = 'Open - at risk')", source: 'ANALYTICS.DT_ORDER_FULFILLMENT' },
  'late orders': { definition: 'Order lines not delivered on time.', formula: 'COUNT_IF(NOT ON_TIME)', source: 'ANALYTICS.DT_ORDER_FULFILLMENT' },
  'value at risk (48h)': { definition: 'Open order value exposed to tools likely to fail in the next 48 hours.', formula: 'SUM(order value) where tool failure probability is high', source: 'ANALYTICS.DT_EQUIPMENT_HEALTH (demo enrichment keyed to SAP work centers)' },
  'tools at high risk': { definition: 'Tools whose 48-hour failure probability is above threshold.', formula: 'COUNT(tools) where FAILURE_PROB_48H is high', source: 'ANALYTICS.DT_EQUIPMENT_HEALTH' },
  'avg utilization': { definition: 'Used hours as a share of available hours.', formula: '100 × SUM(used hrs) ÷ SUM(available hrs)', source: 'SAP work centers → ANALYTICS.DT_WORK_CENTER_UTILIZATION' },
  'total available hrs': { definition: 'Capacity hours available at work centers.', formula: 'SUM(AVAILABLE_HOURS)', source: 'ANALYTICS.DT_WORK_CENTER_UTILIZATION' },
  'total used hrs': { definition: 'Capacity hours consumed by production.', formula: 'SUM(USED_HOURS)', source: 'ANALYTICS.DT_WORK_CENTER_UTILIZATION' },
  'work centers': { definition: 'Distinct SAP work centers in scope.', formula: 'COUNT(DISTINCT work center)', source: 'ANALYTICS.DT_WORK_CENTER_UTILIZATION' },
  'total budget': { definition: 'Planned budget across projects.', formula: 'SUM(budget)', source: 'SAP project/WBS → ANALYTICS.DT_PROJECT_STATUS' },
  'avg budget variance': { definition: 'Average actual-vs-budget deviation per project.', formula: 'AVG(BUDGET_VARIANCE_PCT)', source: 'ANALYTICS.DT_PROJECT_STATUS' },
  'avg completion': { definition: 'Average completion percentage of projects.', formula: 'AVG(COMPLETION_PCT)', source: 'ANALYTICS.DT_PROJECT_STATUS' },
  'active projects': { definition: 'Projects not yet closed.', formula: 'COUNT(projects) where status is active', source: 'ANALYTICS.DT_PROJECT_STATUS' },
  'connected nodes': { definition: 'Plants, suppliers and customers on the network.', formula: 'COUNT(DISTINCT node)', source: GEO },
  'network nodes': { definition: 'Entities on the supply network (plants, suppliers, customers).', formula: 'COUNT(DISTINCT node)', source: GEO },
  'supply chain nodes': { definition: 'Entities on the supply network.', formula: 'COUNT(DISTINCT node)', source: GEO },
  'active routes': { definition: 'Distinct material flows between two nodes.', formula: 'COUNT(flows)', source: GEO },
  'material flows': { definition: 'Directed material movements between nodes (inbound, outbound, inter-plant).', formula: 'COUNT(flows)', source: GEO },
  'countries': { definition: 'Countries with at least one network node.', formula: 'COUNT(DISTINCT country)', source: GEO },
  'monthly flow value': { definition: 'Value moving across the network per month.', formula: 'SUM(MONTHLY_VALUE)', source: GEO },
  'suppliers tracked': { definition: 'Suppliers with quality scoring (6 from SAP BDC + 9 synthetic alternates).', formula: 'COUNT(DISTINCT supplier)', source: 'ANALYTICS.DT_SUPPLIER_QUALITY (L0 + SUPPLIER_EXT)' },
  'bom components': { definition: 'Component lines in the bill of materials.', formula: 'COUNT(BOM component rows)', source: 'ANALYTICS.DT_BOM_EXPLOSION' },
  'total component cost': { definition: 'Rolled-up cost of components in the BOM.', formula: 'SUM(component qty × unit cost)', source: 'ANALYTICS.DT_BOM_EXPLOSION' },
  'unique boms': { definition: 'Distinct parent materials with a BOM.', formula: 'COUNT(DISTINCT parent material)', source: 'ANALYTICS.DT_BOM_EXPLOSION' },
  'forecast accuracy': { definition: 'How closely confirmed output matched plan.', formula: 'Confirmed ÷ Planned × 100', source: PO },
  'forecast bias': { definition: 'Systematic over- or under-planning.', formula: '(Planned − Confirmed) ÷ Planned', source: PO },
  'component shortfall': { definition: 'Components whose days of cover are below supplier lead time — a shortage already locked in.', formula: 'SUPPLIER_LEAD_TIME_DAYS − DAYS_OF_COVER > 0', source: 'ANALYTICS.DT_COMPONENT_COVER (demo enrichment keyed to the SAP BOM)' },
};

export function kpiInfo(title: string): KpiInfo | undefined {
  return KPI_INFO[title.trim().toLowerCase()];
}

// ---------------------------------------------------------------------------
// Guided tour — the demo storyline, one step per highlighted element.
// `anchor` matches a data-tour="…" attribute; if missing the card is centred.
// Numbers re-checked against verified queries SUPPLIER_STOP_ORDERS_AT_RISK and
// ALTERNATE_SUPPLIER_DECISION in SAP_SUPPLY_CHAIN_360.
// ---------------------------------------------------------------------------
export interface TourStep {
  page: PageId;
  anchor?: string;
  title: string;
  body: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  activate?: string; // data-tour id of a tab trigger to select before anchoring
}

// Auto-start on a browser's first visit. Set false for live demos (or open with ?tour=0).
export const TOUR_AUTOSTART = true;

export const TOUR_STEPS: TourStep[] = [
  { page: 'scenario', anchor: 'scenario-storyline', placement: 'top', title: 'The question',
    body: 'Festo AG, a key component supplier, stops supplying. What is at risk, and what do we do about it?' },
  { page: 'architecture', anchor: 'architecture-flow', placement: 'right', title: 'Zero-copy by design',
    body: 'SAP BDC data product → catalog-linked database → dynamic tables → one semantic view. Nothing is copied or re-extracted.' },
  { page: 'overview', anchor: 'overview-kpis', placement: 'bottom', title: 'One version of the KPIs',
    body: 'Live SAP data. Hover any i for the definition, formula and source — the same ones the AI uses.' },
  { page: 'fulfillment', anchor: 'fulfillment-at-risk', placement: 'left', title: '3 open orders at risk',
    body: '2 of them trace back to Festo AG parts through the bill of materials.' },
  { page: 'lineage', anchor: 'lineage-medallion', placement: 'bottom', title: 'Trace every number',
    body: 'From the SAP BDC source data products, through the medallion layers, to this app.' },
  { page: 'ontology', activate: 'ontology-tab-semantic', anchor: 'semantic-entities', placement: 'left', title: 'The business meaning layer',
    body: '17 tables, 13 relationships and 14 verified queries in one semantic view.' },
  { page: 'ontology', activate: 'ontology-tab-graph', anchor: 'ontology-graph', placement: 'top', title: 'Relationships become a graph',
    body: 'The semantic view’s relationships form a knowledge graph: supplier → part → BOM → product → customer order.' },
  { page: 'analyst', anchor: 'analyst-panel', placement: 'left', title: 'Ask in plain English',
    body: 'Ask “If Festo AG stops delivering, which open customer orders are at risk?” → SO-4500226 (Infineon, $964k) and SO-4500488 (GlobalFoundries, $511k).' },
  { page: 'analyst', anchor: 'analyst-panel', placement: 'left', title: 'Decide',
    body: 'Alternates at quality ≥ 90: Venture 91.2 and K&S 92.7 are Candidate, Jenoptik 89.4 is Blocked, Detector Assembly needs Review (no alternate). One semantic layer serves dashboards, SQL and AI.' },
];
