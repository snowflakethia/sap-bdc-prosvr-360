import { randomUUID } from "node:crypto";
import { Router, type Request, type Response } from "express";
import { PAGES, run, runPage, type Params } from "../registry.js";
import { restAuthHeaders, restHost } from "../services/auth.js";

const router = Router();

// ---------------------------------------------------------------------------
// Filter validation: every value becomes a bind, and must be one the data offers.
// ---------------------------------------------------------------------------
const STORY_PROJECT = "P-0615";
let domain: Promise<{ groups: Set<string>; years: number[]; sizes: Set<string> }> | null = null;

function filterDomain() {
  if (!domain) {
    domain = runPage("filters", defaults()).then((r) => ({
      groups: new Set(r.f_groups.map((x) => String(x.md_group_id))),
      years: r.f_years.map((x) => Number(x.fiscal_year)),
      sizes: new Set(r.f_sizes.map((x) => String(x.size_class))),
    }));
    domain.catch(() => (domain = null));
  }
  return domain;
}

function defaults(): Params {
  return { g: "FS", fy0: 2022, fy1: 2026, s: "ALL", p: STORY_PROJECT, q: "", prompt: "" };
}

async function params(req: Request): Promise<Params> {
  const d = await filterDomain();
  const p = defaults();
  const g = String(req.query.group ?? "FS");
  p.g = g === "ALL" || d.groups.has(g) ? g : "FS";
  const fy0 = Number(req.query.fy0), fy1 = Number(req.query.fy1);
  if (d.years.includes(fy0)) p.fy0 = fy0;
  if (d.years.includes(fy1)) p.fy1 = fy1;
  if (p.fy0 > p.fy1) [p.fy0, p.fy1] = [p.fy1, p.fy0];
  const s = String(req.query.size ?? "ALL");
  p.s = d.sizes.has(s) ? s : "ALL";
  const proj = String(req.params.id ?? req.query.project ?? STORY_PROJECT);
  p.p = /^P-\d{4}$/.test(proj) ? proj : STORY_PROJECT;
  // Cortex Search request for the project's "Why?" notes; JSON is built here, then bound.
  p.q = JSON.stringify({
    query: "why is this project behind plan or over budget",
    columns: ["NOTE_DATE", "RAG_STATUS", "SEARCH_TEXT"],
    filter: { "@eq": { PROJECT_ID: p.p } },
    limit: 5,
  });
  return p;
}

function send(page: string) {
  return async (req: Request, res: Response) => {
    const t = Date.now();
    try {
      const data = await runPage(page, await params(req));
      res.json({ page, ms: Date.now() - t, data });
    } catch (err) {
      console.error(`GET ${req.path} error:`, err);
      res.status(500).json({ error: String(err) });
    }
  };
}

// ---------------------------------------------------------------------------
// Page APIs (PRD 8.4)
// ---------------------------------------------------------------------------
router.get("/api/filters", send("filters"));
router.get("/api/overview", send("overview"));
router.get("/api/portfolio", send("portfolio"));
router.get("/api/project/:id", send("project"));
router.get("/api/workforce", send("workforce"));
router.get("/api/people", send("people"));
router.get("/api/pipeline", send("pipeline"));
router.get("/api/ai", send("ai"));
router.get("/api/assets", send("assets"));
router.get("/api/reasoning", send("reasoning"));
router.get("/api/ontology", send("ontology"));
router.get("/api/lineage", send("lineage"));
router.get("/api/trust", send("trust"));
router.get("/api/context/:page", (req, res, next) =>
  ["c1", "c2", "c3"].includes(req.params.page) ? send(req.params.page)(req, res) : next());

// Asset library search (P11): Cortex Search over the harvested assets.
router.get("/api/assets/search", async (req: Request, res: Response) => {
  try {
    const p = await params(req);
    const text = String(req.query.q ?? "").slice(0, 200).trim();
    if (!text) return res.json({ data: { as_search: [] } });
    p.q = JSON.stringify({
      query: text,
      columns: ["ASSET_ID", "ASSET_TITLE", "ASSET_TYPE", "WORK_TYPE", "EFFORT_SAVING_HOURS", "SOURCE_PROJECT_ID"],
      limit: 8,
    });
    res.json({ data: { as_search: await run("as_search", p) } });
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// Ask Cortex (per card): re-run the page's registry statements, ask AI_COMPLETE to explain them.
// ---------------------------------------------------------------------------
router.post("/api/ask-cortex", async (req: Request, res: Response) => {
  try {
    const topic = String(req.body?.topic ?? "");
    if (!PAGES[topic] || topic === "filters") return res.status(400).json({ error: `unknown topic ${topic}` });
    const fakeReq = { query: req.body?.args ?? {}, params: { id: req.body?.args?.project } } as unknown as Request;
    const p = await params(fakeReq);
    const data = await runPage(topic, p);
    const facts = JSON.stringify(
      Object.fromEntries(Object.entries(data).map(([k, rows]) => [k, rows.slice(0, 40)]))).slice(0, 14000);
    const question = String(req.body?.question ?? "").slice(0, 500) ||
      "Explain what these numbers say for the Partner MD and the one action you would take first.";
    p.prompt = [
      "You are the ACoCo ProServe360 advisor for a Partner Managing Director of a professional-services firm.",
      `Scope: Business Group ${p.g === "ALL" ? "firm-wide" : p.g}, fiscal years FY${p.fy0 % 100}-FY${p.fy1 % 100} (Oct-Sep), as of 1 Oct 2026.`,
      `Page: ${topic}. The JSON below holds the exact figures shown on the page (registry statement -> rows).`,
      "Answer in under 180 words of markdown. Cite the numbers you use. Do not invent figures not in the data.",
      "Call an MD group a \"Business Group\" (the md_group_* fields); \"Partner MD\" is the leader's role.",
      "Hours saved are ESTIMATED; say so if you use them. A confidence interval spanning zero means no significant effect.",
      `Question: ${question}`,
      `Data: ${facts}`,
    ].join("\n");
    const rows = await run("ask_complete", p);
    res.json({ answer: String(rows[0]?.answer ?? "") });
  } catch (err) {
    console.error("POST /api/ask-cortex error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// Advisor (P10): stream the Cortex Agent :run response back to the browser as SSE.
// ---------------------------------------------------------------------------
const AGENT_PATH = "/api/v2/databases/ACOCO_DB/schemas/AGENT/agents/ACOCO_ADVISOR:run";

router.post("/api/advisor", async (req: Request, res: Response) => {
  const messages = Array.isArray(req.body?.messages) ? req.body.messages : [];
  const clean = messages.slice(-12).map((m: any) => ({
    role: m.role === "assistant" ? "assistant" : "user",
    content: [{ type: "text", text: String(m.text ?? "").slice(0, 4000) }],
  }));
  if (!clean.length) return res.status(400).json({ error: "messages required" });
  const abort = new AbortController();
  // The browser going away (response closed before we finish) cancels the agent call; req "close" fires too early.
  res.on("close", () => { if (!res.writableEnded) abort.abort(); });
  try {
    const upstream = await fetch(`https://${restHost()}${AGENT_PATH}`, {
      method: "POST",
      headers: { ...restAuthHeaders(), "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ messages: clean }),
      signal: abort.signal,
    });
    if (!upstream.ok || !upstream.body) {
      return res.status(upstream.status || 502).json({ error: `agent ${upstream.status}: ${(await upstream.text()).slice(0, 500)}` });
    }
    res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-cache", Connection: "keep-alive" });
    const reader = upstream.body.getReader();
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(Buffer.from(value));
    }
    res.end();
  } catch (err) {
    if (abort.signal.aborted) return;
    console.error("POST /api/advisor error:", err);
    if (!res.headersSent) res.status(502).json({ error: String(err) });
    else res.end();
  }
});

// ---------------------------------------------------------------------------
// Advisor as a job (what the browser uses). SPCS ingress ends any single request at ~90 s, and a what-if answer
// can take longer, so the agent run happens server-side and the client polls short requests for new events.
// ---------------------------------------------------------------------------
interface AdvisorEvent { event: string; data: string }
interface AdvisorJob { events: AdvisorEvent[]; done: boolean; abort: AbortController; touched: number; waiters: (() => void)[] }
const jobs = new Map<string, AdvisorJob>();
// Events the client folds into a turn (thinking deltas are dropped: large and not shown).
const KEEP = new Set(["response.text.delta", "response.status", "response.tool_use", "response.tool_result",
  "response.table", "response.suggested_queries", "error"]);

function push(job: AdvisorJob, e: AdvisorEvent | null) {
  if (e) job.events.push(e);
  else job.done = true;
  job.waiters.splice(0).forEach((w) => w());
}

async function runJob(job: AdvisorJob, messages: unknown[]) {
  try {
    const upstream = await fetch(`https://${restHost()}${AGENT_PATH}`, {
      method: "POST",
      headers: { ...restAuthHeaders(), "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ messages }),
      signal: job.abort.signal,
    });
    if (!upstream.ok || !upstream.body) {
      push(job, { event: "error", data: JSON.stringify({ message: `agent ${upstream.status}: ${(await upstream.text()).slice(0, 500)}` }) });
      return;
    }
    const reader = upstream.body.getReader();
    const decoder = new TextDecoder();
    let buf = "", event = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let nl: number;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).replace(/\r$/, "");
        buf = buf.slice(nl + 1);
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:") && KEEP.has(event)) push(job, { event, data: line.slice(5) });
      }
    }
  } catch (err) {
    if (!job.abort.signal.aborted) push(job, { event: "error", data: JSON.stringify({ message: String(err) }) });
  } finally {
    push(job, null);
  }
}

// Forget jobs nobody has polled for 10 minutes.
setInterval(() => {
  for (const [id, j] of jobs) if (Date.now() - j.touched > 600_000) { j.abort.abort(); jobs.delete(id); }
}, 60_000).unref();

router.post("/api/advisor/start", (req: Request, res: Response) => {
  const messages = Array.isArray(req.body?.messages) ? req.body.messages : [];
  const clean = messages.slice(-12).map((m: any) => ({
    role: m.role === "assistant" ? "assistant" : "user",
    content: [{ type: "text", text: String(m.text ?? "").slice(0, 4000) }],
  }));
  if (!clean.length) return res.status(400).json({ error: "messages required" });
  const id = randomUUID();
  const job: AdvisorJob = { events: [], done: false, abort: new AbortController(), touched: Date.now(), waiters: [] };
  jobs.set(id, job);
  void runJob(job, clean);
  res.json({ id });
});

router.get("/api/advisor/:id/events", async (req: Request, res: Response) => {
  const job = jobs.get(String(req.params.id));
  if (!job) return res.status(404).json({ error: "unknown advisor job" });
  job.touched = Date.now();
  const from = Math.max(0, parseInt(String(req.query.from ?? "0"), 10) || 0);
  if (job.events.length <= from && !job.done) {
    // Long-poll: return as soon as something arrives, at most 20 s (well inside the ingress limit).
    await new Promise<void>((resolve) => {
      const t = setTimeout(resolve, 20_000);
      job.waiters.push(() => { clearTimeout(t); resolve(); });
    });
  }
  res.json({ events: job.events.slice(from), next: job.events.length, done: job.done });
});

router.delete("/api/advisor/:id", (req: Request, res: Response) => {
  const job = jobs.get(String(req.params.id));
  if (job) { job.abort.abort(); jobs.delete(String(req.params.id)); }
  res.json({ ok: true });
});

export default router;
