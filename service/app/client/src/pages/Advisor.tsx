import { useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Loader2, Send, Square } from 'lucide-react';
import { Card, PageFrame } from '@/components/ui';
import { emptyTurn, streamAdvisor, type AdvisorTurn } from '@/lib/api';

/** Suggested prompts per story (PRD 8.3 P10). */
const PROMPTS: { story: string; text: string }[] = [
  { story: 'PMD-0', text: 'Give me the FY26 vs FY25 scorecard for Financial Services across the three pillars.' },
  { story: 'PMD-2', text: 'Why is project P-0615 losing margin, and what do the PM notes say?' },
  { story: 'PMD-3', text: 'How does the FS time mix compare to the target by level in FY26?' },
  { story: 'PMD-6', text: 'Do FS bids with above-median pursuit intensity win more often, within the same size class?' },
  { story: 'PMD-7', text: 'Is there a significant productivity uplift for AI-active people in FS in FY26?' },
  { story: 'PMD-9', text: 'Which assets could P-0615 have reused, and how many hours might that have saved?' },
  { story: 'PMD-10', text: 'Which bench or roll-off people best match the open FS bids?' },
  { story: 'PMD-11', text: 'If I move the 10 best-matched roll-off people onto open bids, what happens to bench cost and pipeline skill fit?' },
];

interface Msg { role: 'user' | 'assistant'; text: string; turn?: AdvisorTurn }

function TurnView({ t }: { t: AdvisorTurn }) {
  return (
    <div className="space-y-2">
      {!t.done && <p className="flex items-center gap-2 text-xs text-gray-500"><Loader2 className="h-3.5 w-3.5 animate-spin" /> {t.status}</p>}
      {t.tools.length > 0 && (
        <p className="text-[11px] text-gray-400">Tools: {[...new Set(t.tools.map((x) => x.name))].join(', ')}</p>
      )}
      {t.text && <div className="cortex-md"><ReactMarkdown remarkPlugins={[remarkGfm]}>{t.text}</ReactMarkdown></div>}
      {t.tables.map((tb, i) => (
        <div key={i} className="overflow-auto rounded border border-gray-200" style={{ maxHeight: 280 }}>
          <table className="min-w-full text-xs">
            <thead><tr className="bg-sf-dark text-white">{tb.columns.map((c) => <th key={c} className="px-2 py-1 text-left font-medium">{c}</th>)}</tr></thead>
            <tbody>{tb.rows.slice(0, 100).map((r, j) => <tr key={j} className={j % 2 ? 'bg-sky-50/50' : ''}>{r.map((v, k) => <td key={k} className="px-2 py-1">{String(v ?? '')}</td>)}</tr>)}</tbody>
          </table>
        </div>
      ))}
      {t.sql.length > 0 && (
        <details className="text-xs">
          <summary className="cursor-pointer text-sf-dark">Cited SQL ({t.sql.length})</summary>
          {t.sql.map((s, i) => <pre key={i} className="mt-1 overflow-auto rounded bg-gray-900 p-2 text-[11px] text-gray-100">{s}</pre>)}
        </details>
      )}
      {t.error && <p className="text-sm text-red-600">{t.error}</p>}
    </div>
  );
}

export default function Advisor() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const abort = useRef<AbortController | null>(null);

  async function ask(text: string) {
    if (!text.trim() || busy) return;
    const history = [...msgs, { role: 'user' as const, text }];
    setMsgs([...history, { role: 'assistant', text: '', turn: emptyTurn() }]);
    setInput('');
    setBusy(true);
    abort.current = new AbortController();
    try {
      const final = await streamAdvisor(history.map((m) => ({ role: m.role, text: m.text })), (t) =>
        setMsgs((cur) => [...cur.slice(0, -1), { role: 'assistant', text: t.text, turn: t }]), abort.current.signal);
      setMsgs((cur) => [...cur.slice(0, -1), { role: 'assistant', text: final.text, turn: final }]);
    } catch (e: any) {
      setMsgs((cur) => [...cur.slice(0, -1), { role: 'assistant', text: '', turn: { ...emptyTurn(), done: true, error: e.name === 'AbortError' ? 'Stopped.' : String(e) } }]);
    } finally {
      setBusy(false);
    }
  }

  const last = msgs[msgs.length - 1]?.turn;
  return (
    <PageFrame id="P10" title="Ask the Advisor" subtitle="Chat with the Cortex Agent ACOCO_ADVISOR: five Semantic Views, Cortex Search over PM notes and the asset library, and the reasoning views. Answers stream with tables and the SQL they ran.">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
        <Card title="Suggested prompts" className="lg:col-span-1">
          <div className="space-y-2">
            {PROMPTS.map((p) => (
              <button key={p.story} disabled={busy} onClick={() => ask(p.text)}
                className="w-full rounded-lg border border-indigo-200 bg-white p-2 text-left text-xs text-indigo-800 hover:bg-indigo-50 disabled:opacity-50">
                <span className="font-bold">{p.story}</span> - {p.text}
              </button>
            ))}
          </div>
        </Card>
        <Card title="Conversation" className="lg:col-span-3">
          <div className="space-y-4">
            {msgs.length === 0 && <p className="text-sm text-gray-400">Pick a prompt or ask your own question. Answers take 30-90 seconds while the agent plans, queries and checks.</p>}
            {msgs.map((m, i) => m.role === 'user'
              ? <div key={i} className="ml-auto max-w-[80%] rounded-xl bg-sf-dark px-4 py-2 text-sm text-white">{m.text}</div>
              : <div key={i} className="rounded-xl border border-gray-200 bg-gray-50 p-4">{m.turn && <TurnView t={m.turn} />}</div>)}
            {last?.done && last.suggestions.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {last.suggestions.map((s) => <button key={s} onClick={() => ask(s)} className="rounded-full border border-indigo-200 bg-white px-2.5 py-1 text-xs text-indigo-700 hover:bg-indigo-50">{s}</button>)}
              </div>
            )}
            <form onSubmit={(e) => { e.preventDefault(); ask(input); }} className="flex gap-2">
              <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask the Advisor…"
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none" />
              {busy
                ? <button type="button" onClick={() => abort.current?.abort()} className="rounded-lg bg-rose-500 px-3 text-white"><Square className="h-4 w-4" /></button>
                : <button type="submit" className="rounded-lg bg-indigo-500 px-3 text-white hover:bg-indigo-600"><Send className="h-4 w-4" /></button>}
            </form>
          </div>
        </Card>
      </div>
    </PageFrame>
  );
}
