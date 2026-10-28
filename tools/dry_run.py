"""CP-11 scripted dry run of the 30-minute demo (PRD section 11) against the deployed SPCS app.

Walks the beats in order, loads each beat's pages exactly as the browser does (the page's /api route, FS default
filters, cache as the presenter would see it after the warm-up), asks the Advisor the PMD-11 what-if plus one free
question, and times every step. Writes logs/dry_run_cp11.md.

  python tools/dry_run.py <ingress host>
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from spcs_ingress import Ingress  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BEATS = [  # (minutes, beat, [(page code, api route)])
    ("0-3", "Framing", [("C1", "context/c1"), ("C4", "ontology")]),
    ("3-5", "Where the data comes from", [("P8", "lineage")]),
    ("5-8", "ProServe360", [("P0", "overview")]),
    ("8-14", "Operational Excellence", [("P1", "portfolio"), ("P2", "project/P-0615"), ("P11", "assets"),
                                        ("P11 search", "assets/search?q=data%20migration%20accelerator")]),
    ("14-18", "Value Creation", [("P5", "pipeline")]),
    ("18-24", "People Development", [("P3", "workforce"), ("P4", "people"), ("P6", "ai")]),
    ("24-28", "What-if", [("P7", "reasoning")]),
    ("28-30", "Close", [("P9", "trust")]),
]
QUESTIONS = [
    ("P10 PMD-11 what-if", "If the FS people rolling off in the next 90 days below the pipeline's AI-skill level take the "
                           "Agentic-AI curriculum instead of sitting on the bench, what happens to FS bench cost and which "
                           "open bids could they staff? Give figures and sources."),
    ("P10 free question", "What are the top three risks for FS and what do I do first?"),
]


def main(host):
    ig = Ingress(host)
    rows, t0 = [], time.time()
    for mins, beat, pages in BEATS:
        for code, route in pages:
            try:
                st, sec, body = ig.request("/api/" + route, timeout=120)
                data = json.loads(body).get("data", {})
                empty = [k for k, v in data.items() if not v]
                ok = st == 200 and not empty
                note = f"{len(data)} result sets" + (f"; empty {empty}" if empty else "")
            except Exception as e:  # a failed beat is reported, not raised
                sec, ok, note = 0.0, False, str(e)[:100]
            rows.append((mins, beat, code, sec, ok, note))
    for code, q in QUESTIONS:
        t = time.time()
        try:
            kinds, text, _ = ig.advisor(q)
            ok = bool(text) and "error" not in kinds
            note = f"{len(text)} chars answer; tool calls {kinds.get('response.tool_use', 0)}" + (f"; error" if "error" in kinds else "")
        except Exception as e:
            ok, note = False, str(e)[:100]
        rows.append(("24-28", "What-if", code, time.time() - t, ok, note))
    total = time.time() - t0
    lines = [f"# CP-11 dry run ({time.strftime('%Y-%m-%d %H:%M')})", "",
             f"Endpoint `{host}`, default view FS / FY22-FY26 / P-0615. System time for all beats: **{total:.0f} s** "
             f"(the rest of the 30 minutes is talk time).", "",
             "| Min | Beat | Page | Load (s) | OK | Note |", "|---|---|---|---|---|---|"]
    lines += [f"| {m} | {b} | {c} | {s:.2f} | {'PASS' if ok else 'FAIL'} | {n} |" for m, b, c, s, ok, n in rows]
    bad = [r for r in rows if not r[4]]
    pages = [r for r in rows if not r[2].startswith("P10")]
    lines += ["", f"**{len(rows) - len(bad)}/{len(rows)} steps PASS**; slowest page "
              f"{max(pages, key=lambda r: r[3])[2]} {max(r[3] for r in pages):.2f} s; Advisor "
              f"{', '.join(f'{r[3]:.0f} s' for r in rows if r[2].startswith('P10'))}.", ""]
    (ROOT / "logs" / "dry_run_cp11.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
