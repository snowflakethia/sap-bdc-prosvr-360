import fs from "node:fs";
import path from "node:path";
import { runQuery } from "./services/snowflake.js";

/**
 * The SQL registry (registry.sql): every statement the app runs, named, with ordered bind names.
 * Routes never write SQL; they pick statements by name and pass filter values as binds.
 */
interface Statement {
  name: string;
  binds: string[];
  sql: string;
}

export interface Params {
  g: string; // MD group id or 'ALL'
  fy0: number;
  fy1: number;
  s: string; // size class or 'ALL'
  p: string; // project id
  q: string; // Cortex Search request JSON (built server-side)
  prompt: string; // Ask Cortex prompt (built server-side)
}

const REGISTRY_FILE = [path.resolve(import.meta.dirname, "registry.sql"), path.resolve(import.meta.dirname, "../src/registry.sql")]
  .find((f) => fs.existsSync(f));
if (!REGISTRY_FILE) throw new Error("registry.sql not found");

function parse(text: string): Map<string, Statement> {
  const out = new Map<string, Statement>();
  for (const block of text.split(/^-- name: /m).slice(1)) {
    const lines = block.split("\n");
    const name = lines[0].trim();
    if (!lines[1].startsWith("-- binds:")) throw new Error(`registry ${name}: missing binds line`);
    const binds = lines[1].slice("-- binds:".length).split(",").map((b) => b.trim()).filter(Boolean);
    const sql = lines.slice(2).join("\n").trim().replace(/;\s*$/, "");
    out.set(name, { name, binds, sql });
  }
  return out;
}

export const REGISTRY = parse(fs.readFileSync(REGISTRY_FILE, "utf-8"));

/** Page -> registry statements (PRD 8.4). */
export const PAGES: Record<string, string[]> = {
  filters: ["f_groups", "f_years", "f_sizes"],
  c1: ["cx_firm", "cx_groups"],
  c2: ["cx_metrics"],
  c3: ["cx_story"],
  ontology: ["on_graph", "on_lineage"],
  overview: ["ov_scorecard", "ov_on_time", "ov_time_mix", "ov_trend", "ov_risks", "ov_ai_uplift"],
  portfolio: ["pf_size", "pf_pareto", "pf_fp_watch"],
  project: ["pj_list", "pj_header", "pj_months", "pj_work_packages", "pj_pyramid", "pj_assets", "pj_why"],
  workforce: ["wf_time_mix", "wf_mix_trend", "wf_bench_month", "wf_roll_off"],
  people: ["pe_headcount", "pe_risk", "pe_supply", "pe_demand", "pe_curriculum"],
  pipeline: ["pi_size", "pi_win_rate", "pi_open", "pi_bookings"],
  ai: ["ai_adoption", "ai_test", "ai_inactive", "ai_payback", "ai_cost", "ai_delivery_model"],
  reasoning: ["rs_bench", "rs_forecast", "rs_margin_leak", "rs_attrition"],
  lineage: ["ln_layers", "ln_objects"],
  trust: ["tr_freshness", "tr_completeness", "tr_checks", "tr_access"],
  assets: ["as_fy", "as_top", "as_reuse_value", "as_match"],
};

function bindValue(name: string, p: Params): string | number {
  switch (name) {
    case "g": return p.g;
    case "gf": return p.g === "ALL" ? "FIRM" : p.g; // reasoning tests label the firm scope FIRM
    case "fy0": return p.fy0;
    case "fy1": return p.fy1;
    case "s": return p.s;
    case "p": return p.p;
    case "q": return p.q;
    case "prompt": return p.prompt;
    default: throw new Error(`unknown bind ${name}`);
  }
}

// Short-lived result cache: the data refreshes hourly (dynamic tables), pages re-render often.
const CACHE_MS = Number(process.env.ACOCO_CACHE_MS ?? 10 * 60 * 1000); // 0 disables (gate timing)
const cache = new Map<string, { at: number; rows: Record<string, unknown>[] }>();

export async function run(name: string, params: Params): Promise<Record<string, unknown>[]> {
  const stmt = REGISTRY.get(name);
  if (!stmt) throw new Error(`no registry statement ${name}`);
  const binds = stmt.binds.map((b) => bindValue(b, params));
  const key = `${name}|${JSON.stringify(binds)}`;
  const hit = cache.get(key);
  if (CACHE_MS > 0 && hit && Date.now() - hit.at < CACHE_MS && name !== "ask_complete") return hit.rows;
  const rows = await runQuery(stmt.sql, binds);
  if (name !== "ask_complete") cache.set(key, { at: Date.now(), rows });
  return rows;
}

export async function runPage(page: string, params: Params): Promise<Record<string, Record<string, unknown>[]>> {
  const names = PAGES[page];
  if (!names) throw new Error(`unknown page ${page}`);
  const results = await Promise.all(names.map((n) => run(n, params)));
  return Object.fromEntries(names.map((n, i) => [n, results[i]]));
}
