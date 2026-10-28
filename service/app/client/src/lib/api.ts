// Data access: every call goes to the Express server, which runs named registry statements (PRD 8.4).
const BASE = '/api';

export interface Filters {
  group: string; // MD group id or 'ALL'
  fy0: number;
  fy1: number;
  size: string; // size class or 'ALL'
}

export type Rows = Record<string, any>[];
export type PageData = Record<string, Rows>;

function qs(f: Filters, extra: Record<string, string> = {}): string {
  const p = new URLSearchParams({ group: f.group, fy0: String(f.fy0), fy1: String(f.fy1), size: f.size, ...extra });
  return p.toString();
}

export async function getPage(path: string, f: Filters, extra: Record<string, string> = {}): Promise<PageData> {
  const res = await fetch(`${BASE}/${path}?${qs(f, extra)}`);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error ?? `API error ${res.status}`);
  return body.data as PageData;
}

export async function searchAssets(text: string): Promise<Rows> {
  const res = await fetch(`${BASE}/assets/search?q=${encodeURIComponent(text)}`);
  if (!res.ok) throw new Error(`search error ${res.status}`);
  return (await res.json()).data.as_search;
}

export interface AskCortexRequest {
  topic: string;
  args?: Record<string, string>;
  question?: string;
}

export async function askCortex(r: AskCortexRequest, signal?: AbortSignal): Promise<string> {
  const res = await fetch(`${BASE}/ask-cortex`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(r),
    signal,
  }).catch((e) => {
    throw new Error(e.name === 'AbortError' ? 'cancelled' : String(e));
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error ?? `Ask Cortex error ${res.status}`);
  return body.answer as string;
}

/** One turn of the advisor stream, folded from the agent's SSE events. */
export interface AdvisorTurn {
  text: string;
  status: string;
  tools: { name: string; type: string }[];
  sql: string[];
  tables: { columns: string[]; rows: any[][] }[];
  suggestions: string[];
  error?: string;
  done: boolean;
}

export function emptyTurn(): AdvisorTurn {
  return { text: '', status: 'Starting…', tools: [], sql: [], tables: [], suggestions: [], done: false };
}

function collectSql(node: any, out: string[]) {
  if (!node || typeof node !== 'object') return;
  for (const [k, v] of Object.entries(node)) {
    if (k === 'sql' && typeof v === 'string' && v.trim()) out.push(v.trim());
    else if (typeof v === 'object') collectSql(v, out);
  }
}

/** POST /api/advisor and fold the streamed events into a turn; calls onUpdate as events arrive. */
/** Fold one agent :run event into the turn being built. */
function fold(turn: AdvisorTurn, event: string, raw: string) {
  let d: any;
  try {
    d = JSON.parse(raw);
  } catch {
    return;
  }
  if (event === 'response.text.delta') turn.text += d.text ?? '';
  else if (event === 'response.status') turn.status = d.message ?? turn.status;
  else if (event === 'response.tool_use') turn.tools.push({ name: d.name, type: d.type });
  else if (event === 'response.tool_result') collectSql(d.content, turn.sql);
  else if (event === 'response.table' && d.result_set) {
    turn.tables.push({
      columns: (d.result_set.resultSetMetaData?.rowType ?? []).map((c: any) => c.name),
      rows: d.result_set.data ?? [],
    });
  } else if (event === 'response.suggested_queries') turn.suggestions = (d.suggested_queries ?? []).map((q: any) => q.query);
  else if (event === 'error') turn.error = d.message ?? JSON.stringify(d);
}

/**
 * Ask the Advisor. The server runs the agent as a job and the browser long-polls for new events: SPCS ingress
 * ends any single request at ~90 s, and a what-if answer can take longer than that.
 */
export async function streamAdvisor(
  messages: { role: 'user' | 'assistant'; text: string }[],
  onUpdate: (t: AdvisorTurn) => void,
  signal?: AbortSignal,
): Promise<AdvisorTurn> {
  const turn = emptyTurn();
  const fail = (msg: string) => {
    turn.error = msg;
    turn.done = true;
    onUpdate({ ...turn });
    return turn;
  };
  const start = await fetch(`${BASE}/advisor/start`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ messages }), signal,
  });
  const body = await start.json().catch(() => ({}));
  if (!start.ok || !body.id) return fail(body.error ?? `advisor error ${start.status}`);
  const id: string = body.id;
  const cancel = () => { void fetch(`${BASE}/advisor/${id}`, { method: 'DELETE' }); };
  signal?.addEventListener('abort', cancel, { once: true });
  let from = 0;
  for (;;) {
    let page: { events: { event: string; data: string }[]; next: number; done: boolean };
    try {
      const r = await fetch(`${BASE}/advisor/${id}/events?from=${from}`, { signal });
      if (!r.ok) return fail(`advisor error ${r.status}`);
      page = await r.json();
    } catch (e) {
      if (signal?.aborted) throw e;
      continue; // a dropped poll is retried; the job keeps running server-side
    }
    for (const e of page.events) fold(turn, e.event, e.data);
    from = page.next;
    if (page.events.length) onUpdate({ ...turn });
    if (page.done) break;
  }
  turn.done = true;
  onUpdate({ ...turn });
  return turn;
}
