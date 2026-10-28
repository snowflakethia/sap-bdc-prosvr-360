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
export async function streamAdvisor(
  messages: { role: 'user' | 'assistant'; text: string }[],
  onUpdate: (t: AdvisorTurn) => void,
  signal?: AbortSignal,
): Promise<AdvisorTurn> {
  const turn = emptyTurn();
  const res = await fetch(`${BASE}/advisor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
    signal,
  });
  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => ({}));
    turn.error = body.error ?? `advisor error ${res.status}`;
    turn.done = true;
    onUpdate({ ...turn });
    return turn;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  let event = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let nl: number;
    while ((nl = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, nl).replace(/\r$/, '');
      buf = buf.slice(nl + 1);
      if (line.startsWith('event:')) event = line.slice(6).trim();
      else if (line.startsWith('data:')) {
        let d: any;
        try {
          d = JSON.parse(line.slice(5));
        } catch {
          continue;
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
        onUpdate({ ...turn });
      }
    }
  }
  turn.done = true;
  onUpdate({ ...turn });
  return turn;
}
