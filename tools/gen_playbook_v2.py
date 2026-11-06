"""Render docs/SAP BDC ProServe360 Demo Playbook_v2.docx from figures measured on the live build.

  .venv/bin/python tools/gen_playbook_v2.py --measure   query the build -> logs/playbook_v2_measured.json
  .venv/bin/python tools/gen_playbook_v2.py             render the .docx from that file

The v1 playbook is the style template (fonts, headings, table style). Every number in the
document is computed from the measured file; nothing is typed in by hand.
"""
import argparse
import json
import pathlib
import sys

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

ROOT = pathlib.Path(__file__).resolve().parent.parent
V1 = ROOT / "docs" / "SAP BDC ProServe360 Demo Playbook.docx"
V2 = ROOT / "docs" / "SAP BDC ProServe360 Demo Playbook_v2.docx"
MEASURED = ROOT / "logs" / "playbook_v2_measured.json"
BLUE = "29B5E8"

Q = {
    "portfolio_fy": "SELECT * FROM ACOCO_L2.SERVING.VW_PORTFOLIO_FY WHERE FISCAL_YEAR IN (2025, 2026) ORDER BY 1, 2",
    "story": "SELECT * FROM ACOCO_L2.SERVING.VW_PROJECT_HEALTH_NOW WHERE IS_STORY_PROJECT",
    "wps_level": "SELECT LEVEL, PEOPLE, ROUND(WPS_MEDIAN,1) WPS, ROUND(VC_MEDIAN,1) VC, ROUND(OE_MEDIAN,1) OE, ROUND(PD_MEDIAN,1) PD, "
                 "ROUND(TM_MEDIAN,1) TM, ROUND(100*BILLABILITY_MEDIAN,1) BILL, ROUND(100*UTILIZATION_MEDIAN,1) UTIL, "
                 "ROUND(100*BILLABILITY_TARGET,1) BILL_T, ROUND(100*UTILIZATION_TARGET,1) UTIL_T, ROUND(100*TM_COVERAGE,1) TM_COV "
                 "FROM ACOCO_L2.REASONING.WPS_BY_LEVEL WHERE SCOPE='FIRM' AND FISCAL_YEARS='FY26' ORDER BY LEVEL_SORT",
    "vendor_sig": "SELECT STRATUM, EXPOSURE, OUTCOME, ROUND(RHO,3) RHO, ROUND(CI_LOW,3) LO, ROUND(CI_HIGH,3) HI "
                  "FROM ACOCO_L2.REASONING.VENDOR_WPS_TEST WHERE SCOPE='FIRM' AND FISCAL_YEARS NOT LIKE '%pooled' "
                  "AND CELL_STATUS='OK' AND SIGNIFICANT ORDER BY OUTCOME, EXPOSURE, STRATUM",
    "token": "SELECT STRATUM, ROUND(RHO,3) RHO, ROUND(CI_LOW,3) LO, ROUND(CI_HIGH,3) HI, EFFECT_SIZE FROM ACOCO_L2.REASONING.TOKEN_WPS_TEST "
             "WHERE SCOPE='FIRM' AND FISCAL_YEARS='FY24-26' AND CELL_STATUS='OK'",
    "training": "SELECT STRATUM, ROUND(RHO,3) RHO, ROUND(CI_LOW,3) LO, ROUND(CI_HIGH,3) HI, EFFECT_SIZE FROM ACOCO_L2.REASONING.TRAINING_WPS_TEST "
                "WHERE SCOPE='FIRM' AND FISCAL_YEARS='FY24-26' AND CELL_STATUS='OK'",
    "curriculum_sig": "SELECT STRATUM, CURRICULUM, OUTCOME, ROUND(RHO,3) RHO FROM ACOCO_L2.REASONING.CURRICULUM_WPS_TEST "
                      "WHERE SCOPE='FIRM' AND FISCAL_YEARS='FY24-26' AND CELL_STATUS='OK' AND SIGNIFICANT",
    "ai_wps": "SELECT * FROM ACOCO_L2.REASONING.AI_WPS_TEST WHERE SCOPE IN ('FIRM','FS') AND STRATUM='ALL LEVELS'",
    "payback_wps": "SELECT * FROM ACOCO_L2.REASONING.LEARNING_WPS_PAYBACK_TEST WHERE SCOPE='FIRM' ORDER BY PAYBACK_WPS DESC",
    "truth": "SELECT VERDICT, COUNT(*) N FROM ACOCO_L2.REASONING.P6_TRUTH_RECOVERY GROUP BY 1",
    "ai_cost": "SELECT m.PRODUCT, ROUND(SUM(u.COST_USD)) COST, SUM(u.TOKENS) TOKENS FROM ACOCO_L2.AI_ADOPTION.DT_AI_USAGE_DAILY u "
               "JOIN ACOCO_L2.ONTOLOGY.ENT_AI_MODEL m ON m.AI_MODEL_ID=u.AI_MODEL_ID GROUP BY 1 ORDER BY 2 DESC",
    "ont_entity": "SELECT ENTITY, OWNING_SYSTEM, ROW_COUNT, BDC_CLD_SHARE_PCT, SEMANTIC_VIEWS, L1_SOURCE FROM ACOCO_L2.ONTOLOGY.ONT_ENTITY ORDER BY 1",
    "ont_rel": "SELECT FROM_ENTITY, VERB, TO_ENTITY, CARDINALITY, SEMANTIC_VIEWS FROM ACOCO_L2.ONTOLOGY.ONT_RELATIONSHIP ORDER BY 1, 3",
    "ont_metric": "SELECT PILLAR, COUNT(*) N FROM ACOCO_L2.ONTOLOGY.ONT_METRIC GROUP BY 1 ORDER BY 2 DESC",
    "lineage": "SELECT * FROM ACOCO_L2.SERVING.VW_LINEAGE",
    "roll_off": "SELECT COUNT(*) N, COUNT_IF(BELOW_PIPELINE_AI_LEVEL) BELOW FROM ACOCO_L2.SERVING.VW_ROLL_OFF_90D WHERE MD_GROUP_ID='FS'",
    "delivery_model": "SELECT * FROM ACOCO_L2.SERVING.VW_DELIVERY_MODEL_FY WHERE FISCAL_YEAR=2026",
    "svs": "SHOW SEMANTIC VIEWS IN SCHEMA ACOCO_L2.SEMANTIC",
    "serving_views": "SELECT COUNT(*) N FROM ACOCO_L2.INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA='SERVING'",
}


def measure():
    sys.path.insert(0, str(ROOT / "tools"))
    import sf
    out = {k: sf.query(q) for k, q in Q.items()}
    MEASURED.parent.mkdir(exist_ok=True)
    MEASURED.write_text(json.dumps(out, indent=1, default=str))
    print(f"measured {len(out)} queries -> {MEASURED}")


# ---------------------------------------------------------------------------------------------- figures
def f(x):
    return float(x) if x not in (None, "") else None


def usd_m(x):
    return f"${f(x) / 1e6:,.2f}M"


def pct(x, d=1):
    return f"{100 * f(x):.{d}f} %"


def figures(m):
    pf = {(r["MD_GROUP_ID"], r["FISCAL_YEAR"]): r for r in m["portfolio_fy"]}
    firm = {}
    for fy in (2025, 2026):
        rows = [r for (g, y), r in pf.items() if y == fy]
        rev, mar = sum(f(r["REVENUE"]) for r in rows), sum(f(r["MARGIN"]) for r in rows)
        firm[fy] = dict(revenue=rev, margin_pct=mar / rev, headcount=sum(int(r["CLOSING_HEADCOUNT"]) for r in rows),
                        ai_cost=sum(f(r["AI_COST"]) for r in rows))
    fs25, fs26 = pf[("FS", 2025)], pf[("FS", 2026)]
    s = m["story"][0]
    cld = [r for r in m["lineage"] if r["LAYER"] == "L0" and r["SOURCE_SYSTEM"] == "BDC_CLD"]
    pi_names = ("COREWORKFORCEDATA", "EMPLOYEEAVAILABILITY", "WORKFORCEPLANNEDWORKINGTIME", "ASSIGNMENTADDITIONALINFORMATION")
    pi = {n: sum(r["ROW_COUNT"] or 0 for r in cld if r["OBJECT_NAME"].upper().startswith(n)) for n in pi_names}
    dm = {(r["MD_GROUP_ID"], r["DELIVERY_MODEL"]): r for r in m["delivery_model"]}
    ai = {(r["SCOPE"], r["FISCAL_YEARS"]): r for r in m["ai_wps"]}
    cost = {r["PRODUCT"]: r for r in m["ai_cost"]}
    tok = {r["STRATUM"]: r for r in m["token"]}
    trn = {r["STRATUM"]: r for r in m["training"]}
    vend = {(r["STRATUM"], r["EXPOSURE"], r["OUTCOME"]): r for r in m["vendor_sig"]}
    truth = {r["VERDICT"]: r["N"] for r in m["truth"]}
    layers = {}
    for r in m["lineage"]:
        layers[r["LAYER"]] = layers.get(r["LAYER"], 0) + 1
    return dict(
        firm=firm, fs25=fs25, fs26=fs26, story=s, cld_tables=len(cld), cld_rows=sum(r["ROW_COUNT"] or 0 for r in cld),
        pi=pi, layers=layers, dm=dm, ai=ai, cost=cost, tok=tok, trn=trn, vend=vend, truth=truth,
        roll=m["roll_off"][0], wps=m["wps_level"], payback=m["payback_wps"], cur=m["curriculum_sig"],
        ents=m["ont_entity"], rels=m["ont_rel"], mets=m["ont_metric"], svs=sorted(r["name"] for r in m["svs"]),
        serving=m["serving_views"][0]["N"])


# ---------------------------------------------------------------------------------------------- docx helpers
class Doc:
    def __init__(self):
        self.d = docx.Document(str(V1))
        body = self.d.element.body
        for el in list(body):
            if el.tag != qn("w:sectPr"):
                body.remove(el)

    def p(self, text="", style="Normal", bold_lead=None, size=None, italic=False, color=None):
        para = self.d.add_paragraph(style=style)
        if bold_lead:
            para.add_run(bold_lead).bold = True
        run = para.add_run(text)
        run.italic = italic
        if size:
            run.font.size = Pt(size)
        if color:
            run.font.color.rgb = RGBColor.from_string(color)
        return para

    def h(self, text, level):
        return self.d.add_heading(text, level)

    def bullets(self, items):
        for it in items:
            if isinstance(it, tuple):
                self.p(it[1], "List Bullet", bold_lead=it[0])
            else:
                self.p(it, "List Bullet")

    def numbered(self, items):
        for it in items:
            self.p(it, "List Number")

    @staticmethod
    def _fix_widths(t, widths):
        """Fixed layout + explicit grid / cell widths, so Word does not auto-fit the columns."""
        t.autofit = False
        tblPr = t._tbl.tblPr
        lay = OxmlElement("w:tblLayout")
        lay.set(qn("w:type"), "fixed")
        tblPr.append(lay)
        for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
            gc.set(qn("w:w"), str(int(w * 567)))
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = docx.shared.Cm(w)

    @staticmethod
    def _cell(c, text, size, bold=False, white=False):
        c.text = ""
        r = c.paragraphs[0].add_run(str(text))
        r.font.size = Pt(size)
        r.bold = bold
        if white:
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        return c.paragraphs[0]

    def table(self, header, rows, widths=None, size=8.5):
        """header items are 'Title' or ('Title', 'small note on where it is defined')."""
        t = self.d.add_table(rows=1, cols=len(header))
        t.style = "Table Grid"
        for i, h in enumerate(header):
            title, note = (h, None) if isinstance(h, str) else h
            c = t.rows[0].cells[i]
            para = self._cell(c, title, size, bold=True, white=True)
            if note:
                r = para.add_run("\n" + note)
                r.font.size = Pt(size - 2)
                r.italic = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            shd = OxmlElement("w:shd")
            shd.set(qn("w:val"), "clear")
            shd.set(qn("w:color"), "auto")
            shd.set(qn("w:fill"), BLUE)
            c._tc.get_or_add_tcPr().append(shd)
        for row in rows:
            cells = t.add_row().cells
            for i, v in enumerate(row):
                self._cell(cells[i], v, size)
        self._fix_widths(t, widths or [17.0 / len(header)] * len(header))
        self.d.add_paragraph()
        return t

    def kv(self, rows, size=8.5):
        """Two-column label / value table (first column bold)."""
        t = self.d.add_table(rows=0, cols=2)
        t.style = "Table Grid"
        for k, v in rows:
            c = t.add_row().cells
            self._cell(c[0], k, size, bold=True)
            self._cell(c[1], v, size)
        self._fix_widths(t, [3.6, 13.4])
        self.d.add_paragraph()

    def _field(self, para, instr, placeholder=""):
        for kind, text in (("begin", None), (None, instr), ("separate", None), (None, placeholder), ("end", None)):
            r = para.add_run()
            if kind:
                fc = OxmlElement("w:fldChar")
                fc.set(qn("w:fldCharType"), kind)
                r._r.append(fc)
            elif text == instr:
                it = OxmlElement("w:instrText")
                it.set(qn("xml:space"), "preserve")
                it.text = instr
                r._r.append(it)
            else:
                r.text = text
        return para

    def toc(self):
        self.p("Contents", bold_lead="", size=14)
        self._field(self.d.add_paragraph(), 'TOC \\o "1-3" \\h \\z \\u',
                    "Right-click and choose Update Field to refresh the table of contents.")
        # ask Word to refresh fields (TOC, page numbers) when the file is opened
        upd = OxmlElement("w:updateFields")
        upd.set(qn("w:val"), "true")
        self.d.settings.element.append(upd)
        self.d.add_page_break()

    def page_numbers(self):
        for sec in self.d.sections:
            para = sec.footer.paragraphs[0] if sec.footer.paragraphs else sec.footer.add_paragraph()
            para.text = ""
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.add_run("Page ").font.size = Pt(8)
            self._field(para, "PAGE", "1")
            para.add_run(" of ").font.size = Pt(8)
            self._field(para, "NUMPAGES", "1")

    def save(self):
        self.page_numbers()
        self.d.save(str(V2))


def demo_step(doc, title, rows):
    doc.h(title, 3)
    doc.kv(rows)


# ---------------------------------------------------------------------------------------------- content
def render():
    m = json.loads(MEASURED.read_text())
    F = figures(m)
    s, fs25, fs26, firm = F["story"], F["fs25"], F["fs26"], F["firm"]
    story = s["PROJECT_ID"]
    sv_n = len(F["svs"])
    n_ent, n_rel, n_met = len(F["ents"]), len(F["rels"]), sum(r["N"] for r in F["mets"])
    ai26, aip, aifs = F["ai"][("FIRM", "FY26")], F["ai"][("FIRM", "FY24-26")], F["ai"][("FS", "FY24-26 pooled")]
    cx_all, cc_all = F["vend"][("ALL LEVELS", "CORTEX", "WPS")], F["vend"][("ALL LEVELS", "CLAUDE_CODE", "WPS")]
    cx_oe = F["vend"][("ALL LEVELS", "CORTEX", "OE")]
    tok_all, trn_all = F["tok"]["ALL LEVELS"], F["trn"]["ALL LEVELS"]
    pay = F["payback"]
    pay_top, pay_pm = pay[0], [r for r in pay if r["CURRICULUM"] == "PROJECT_MGMT"][0]
    fs_ha, fs_h = F["dm"][("FS", "HUMAN_AGENT")], F["dm"][("FS", "HUMAN")]
    pi_rows = sum(F["pi"].values())
    total_cost = sum(f(r["COST"]) for r in F["cost"].values())
    rec = F["truth"].get("RECOVERED", 0) + F["truth"].get("SIGN_RECOVERED", 0)
    seeded = rec + F["truth"].get("MISSED", 0)
    nulls_ok, nulls = F["truth"].get("NULL_OK", 0), F["truth"].get("NULL_OK", 0) + F["truth"].get("NULL_SIGNIFICANT", 0)
    person = F["ents"][[e["ENTITY"] for e in F["ents"]].index("person")]
    rel_n = {r["FROM_ENTITY"] + " " + r["VERB"] + " " + r["TO_ENTITY"]: r for r in F["rels"]}
    met_n = {r["PILLAR"]: r["N"] for r in F["mets"]}

    doc = Doc()
    doc.p("SNOWFLAKE | CONFIDENTIAL", size=8, color="7F7F7F")
    doc.h("SAP BDC ProServe360 Demo Playbook", 1)
    doc.p("Decision support for the Partner and Managing Director (MD) of a professional-services firm, built on SAP Business "
          "Data Cloud (BDC) and Snowflake.")
    doc.p("Demo date: 1 October 2026, the first day of fiscal year 2027 (FY27). Fiscal years run October to September, so FY26 "
          "(October 2025 – September 2026) has just closed. All figures come from the demo environment; transactional data is "
          "simulated and labelled as such.", size=9, italic=True)
    doc.toc()

    # 0 ---------------------------------------------------------------------------------------
    doc.h("Key Terms", 2)
    doc.p("Terms are spelled out the first time they appear; this table collects them for reference.", size=9)
    doc.table(["Term", "Meaning"], [
        ["MD", "Managing Director – the Partner who runs one of six industry groups, e.g. Financial Services (FS)"],
        ["SAP BDC", "SAP Business Data Cloud – SAP's platform that publishes SAP data as governed data products"],
        ["PI", "SAP SuccessFactors People Intelligence – the BDC data products for the workforce"],
        ["S/4HANA", "SAP's enterprise resource planning (ERP) system: finance, projects, cost centres"],
        ["CRM", "Customer relationship management – the sales pipeline of bids (opportunities)"],
        ["CLD", "Catalog-linked database – how a BDC data product appears in Snowflake, read in place (zero-copy)"],
        ["L0 / L1 / L2", "The three layers of the medallion architecture: source, domain, consumption-ready assets"],
        ["DT", "Dynamic table – a Snowflake table defined by a query and kept fresh automatically"],
        ["SV", "Semantic View – a Snowflake object that defines business entities, relationships and metrics for AI and BI"],
        ["Advisor", "The Cortex Agent (Snowflake's AI agent service) that answers questions using the Semantic Views"],
        ["P&L, CPI, SPI", "Profit and loss; cost performance index and schedule performance index (< 1 = over budget / late)"],
        ["LD", "Liquidated damages – contractual penalties on late fixed-price projects"],
        ["WPS", "Workforce Productivity Score – 0 to 100 per person per quarter, 50 = the average of the person's level"],
        ["VC / OE / PD / TM", "The WPS pillars: Value Creation, Operational Excellence, People Development, Team"],
        ["rho, CI", "Spearman rank correlation (association, -1 to +1); 90 % confidence interval around it"],
    ], widths=[3.2, 13.8])

    # 1 ---------------------------------------------------------------------------------------
    doc.h("1. Executive Summary", 2)
    doc.p("Professional-services firms sell people-hours priced by bill code. Margin leaks through fixed-price overrun, "
          "unfocused pursuit effort, bench (unassigned) time and skills mismatch – and nobody can say whether the money spent on "
          "artificial intelligence (AI) tools and training makes anyone more productive. SAP S/4HANA holds the project P&L and SAP "
          "SuccessFactors People Intelligence (PI) holds the workforce, but neither answers a cross-domain question on its own.",
          bold_lead="The problem. ")
    doc.p("SAP stays the System of Record. Snowflake is the System of Context and Reasoning: SAP BDC data products arrive "
          "zero-copy as catalog-linked databases (CLDs), are joined with data SAP does not hold (CRM pipeline, asset library, "
          "AI-tool telemetry, project-manager commentary) through a three-layer medallion and one shared ontology, and are reasoned "
          "over by Semantic Views (SVs), a Cortex Agent (the Advisor), Cortex Search and Snowflake ML.", bold_lead="Our position. ")
    doc.p("Recommendations", bold_lead="")
    doc.bullets([
        ("Lead with People Intelligence. ", f"The four live PI data products ({pi_rows:,} rows, read zero-copy) become far more "
         "valuable once joined with S/4HANA, CRM and AI telemetry: they power the time mix, roll-off, attrition risk and the new "
         "Workforce Productivity Score (WPS)."),
        ("Show the ontology as the reason the Advisor is accurate. ", f"{n_ent} shared entities, {n_rel} registered relationships "
         f"and {n_met} metrics across {sv_n} Semantic Views – one definition of 'person', 'project' and 'billability' everywhere."),
        (f"Make {story} {s['CUSTOMER_NAME']} the hero moment. ", f"A Large fixed-price {s['WORK_TYPE'].lower()} project forecast "
         f"at {pct(s['FORECAST_MARGIN_PCT'])} margin, cost performance index (CPI) {f(s['CPI']):.2f}, {usd_m(s['LD_EXPOSURE'])} "
         f"liquidated-damages (LD) exposure, {s['FORECAST_SLIP_WEEKS']} weeks late and no reusable asset applied."),
        ("Close on honest AI evidence. ", f"People active with AI score +{f(ai26['UPLIFT_WPS']):.1f} WPS points in FY26 "
         f"(90 % confidence interval +{f(ai26['CI_LOW']):.1f} to +{f(ai26['CI_HIGH']):.1f}); Snowflake Cortex use is associated "
         f"with WPS at rho {f(cx_all['RHO']):.2f}; and within Financial Services (FS) alone the uplift is not significant. "
         "Associations, never causes – the honesty is the differentiator."),
    ])

    # 2 ---------------------------------------------------------------------------------------
    doc.h("2. Business Value Delivered", 2)
    doc.p("The application turns three questions the MD asks every month – 'Where is my margin going?', 'Am I winning the right "
          "work?' and 'Are my people getting more productive?' – into measured answers that cite their source. Value is framed by "
          "three pillars – Operational Excellence, Value Creation and People Development – plus a cross-pillar overlay called "
          "ProServe360.")
    doc.table(["Pillar", "Decision it improves", "Value lever", "Measured proof (FY26)"], [
        ["Operational Excellence", "Intervene on fixed-price projects before the loss is booked; reuse assets",
         "Overrun and LDs avoided; delivery hours saved",
         f"{story}: CPI {f(s['CPI']):.2f}, forecast margin {pct(s['FORECAST_MARGIN_PCT'])}, LD {usd_m(s['LD_EXPOSURE'])}"],
        ["Value Creation", "Bid with the right effort and team; staff bench people onto pursuits",
         "Higher win-rate per pursuit dollar; bench cost turned into pipeline",
         f"FS win-rate {pct(fs26['WIN_RATE'])}; pursuit cost {f(fs26['PURSUIT_COST_PER_WON_USD']) * 100:.1f} cents per $ won"],
        ["People Development", "Staff, train and retain on evidence; fund the AI tools and curricula associated with productivity",
         "Billability, utilization, lower attrition, AI spend that returns",
         f"FS billability {pct(fs26['BILLABILITY'])}; {F['roll']['N']} FS roll-offs in 90 days, {F['roll']['BELOW']} below the pipeline AI-skill level"],
        ["AI delivery (agents)", "Choose People+Agents delivery where it pays", "Margin uplift from agent-assisted delivery",
         f"FS margin {fs_ha['MARGIN_PCT']} % People+Agents vs {fs_h['MARGIN_PCT']} % People-only"],
        ["ProServe360 overlay", "One scorecard and risk register across pillars", "One screen instead of four systems",
         f"FS revenue {usd_m(fs26['REVENUE'])}, margin {pct(fs26['MARGIN_PCT'])} ({100 * (f(fs26['MARGIN_PCT']) - f(fs25['MARGIN_PCT'])):+.1f} pts vs FY25)"],
    ], widths=[3.0, 4.8, 4.2, 5.0])
    doc.h("2.1 Value by buyer", 3)
    doc.table(["Persona", "What they get", "Lead with"], [
        ["Partner MD / Practice Lead", "Group scorecard, the one project that decides the year, bench-to-pipeline staffing", "P0, P2, P5"],
        ["Chief Operating / Financial Officer", f"Firm margin {pct(firm[2026]['margin_pct'])} on {usd_m(firm[2026]['revenue'])} revenue; "
         f"LD exposure; AI spend ({usd_m(total_cost)} to date) against productivity evidence", "P0, P1, Advisor WPS questions"],
        ["Chief HR Officer / Head of Talent", "A balanced productivity score by level, curriculum payback, attrition risk – all from People Intelligence data", "P3, P4, P6, WPS demo"],
        ["Chief Information Officer / Head of Data", "Zero-copy BDC, a governed semantic layer and one ontology; nothing copied out of SAP", "C4, P8, P9, ontology demo"],
        ["SAP account team", "Proof that PI and BDC data products gain value in Snowflake; publish-back of derived products", "PI demo track"],
    ], widths=[4.2, 9.3, 3.5])

    # 3 ---------------------------------------------------------------------------------------
    doc.h("3. Use Cases at a Glance", 2)
    doc.table(["#", "Use case", "Pillar", "Page(s)", "Headline proof (measured)"], [
        ["1", "ProServe360 Scorecard", "Overlay", "P0", f"FS FY26 revenue {usd_m(fs26['REVENUE'])}, margin {pct(fs26['MARGIN_PCT'])}"],
        ["2", "Fixed-price exposure & pyramid drift", "Operational Excellence", "P1 → P2", f"{story}: forecast margin {pct(s['FORECAST_MARGIN_PCT'])}, CPI {f(s['CPI']):.2f}"],
        ["3", "Asset harvest & reuse", "Operational Excellence", "P11", f"{story} reused no asset; matching assets shown as missed reuse"],
        ["4", "Pursuit payback & team fit", "Value Creation", "P5", f"FS win-rate {pct(fs26['WIN_RATE'])} (FY25 {pct(fs25['WIN_RATE'])})"],
        ["5", "Time mix, billability & roll-off", "People Development", "P3", f"{F['roll']['N']} FS roll-offs; {F['roll']['BELOW']} below pipeline AI-skill level"],
        ["6", "Skills demand & attrition risk", "People Development", "P4", f"FS voluntary attrition {pct(fs26['VOLUNTARY_ATTRITION'])} (FY25 {pct(fs25['VOLUNTARY_ATTRITION'])})"],
        ["7", "Workforce Productivity Score", "People Development", "P10 + Snowsight", f"Firm FY26 AI-active uplift +{f(ai26['UPLIFT_WPS']):.1f} WPS points"],
        ["8", "AI products, tokens & curricula", "People Development", "P10 + Snowsight", f"Cortex ~ WPS rho {f(cx_all['RHO']):.2f}; tokens rho {f(tok_all['RHO']):.2f}"],
        ["9", "Capacity what-if via the Advisor", "Overlay", "P10", "Bench-to-pipeline match and scenario with cited SQL"],
        ["10", "Ontology & lineage", "Platform", "C4, P8, P9", f"{n_ent} entities, {n_rel} relationships, {n_met} metrics; {F['cld_tables']} CLD tables"],
    ], widths=[0.7, 4.5, 3.0, 2.5, 6.3])

    # 4 ---------------------------------------------------------------------------------------
    doc.h("4. Focus Demo A – SAP SuccessFactors People Intelligence Data Products", 2)
    doc.p("People Intelligence is the SAP data product customers most want to see used beyond HR reporting. This track proves that "
          "PI data, shared zero-copy through SAP BDC, becomes the backbone of margin, staffing and AI-productivity decisions once "
          "Snowflake joins it with S/4HANA, CRM and AI telemetry.")
    doc.h("4.1 The data products and what each one powers", 3)
    pi = F["pi"]
    doc.table([
        ("PI data product", "as shared through SAP BDC"),
        ("Rows", "read zero-copy"),
        ("L1 domain view", "ACOCO_L1.<domain>.<object>"),
        ("Ontology entity", "defined once in ACOCO_L2.ONTOLOGY (ENT_* / REL_* tables, see section 5)"),
        ("Powers", "app page (P3, P4, P10 – see section 6) and metric (registered in ONTOLOGY.ONT_METRIC)"),
    ], [
        ["Core Workforce\n(COREWORKFORCEDATA_V1)", f"{pi['COREWORKFORCEDATA']:,}", "WORKFORCE.\nWORKFORCE_JOB", "person, level, md_group",
         "P3, P4, P10 – who each person is, their level and group; every per-person metric; leavers for attrition risk"],
        ["Employee Availability\n(EMPLOYEEAVAILABILITY_V1)", f"{pi['EMPLOYEEAVAILABILITY']:,}", "TIME.\nAVAILABILITY", "person (by day)",
         "P3, P10 – available hours, the base of billability_pct, utilization_pct and bench_pct"],
        ["Planned Working Time\n(WORKFORCEPLANNEDWORKINGTIME_V1)", f"{pi['WORKFORCEPLANNEDWORKINGTIME']:,}", "TIME.\nPLANNED_TIME", "person (by day)",
         "P3 – planned hours and absence, used to compute available hours"],
        ["Job relationships\n(ASSIGNMENTADDITIONALINFORMATION_V1)", f"{pi['ASSIGNMENTADDITIONALINFORMATION']:,}", "WORKFORCE.\nJOB_RELATIONSHIP",
         "person reports to person", "P10 – who manages whom; the Team pillar of the WPS (avg_team)"],
        ["Skills, Learning, Performance\n(simulated until shared)", "BDC-shaped", "TALENT.\nSKILL, LEARNING_ITEM", "skill, learning_item, learning_category",
         "P4, P5, P6 – skill fit of bid teams, AI-skill bands, curriculum tests"],
    ], widths=[4.1, 1.7, 2.7, 3.2, 5.3], size=8)
    doc.p(f"{F['cld_tables']} CLD tables ({F['cld_rows']:,} rows) are read in place, {pi_rows:,} of them from People Intelligence. "
          f"The person entity holds {person['ROW_COUNT']:,} people, {person['BDC_CLD_SHARE_PCT']} % of them straight from the PI share "
          "(SOURCE_SYSTEM = BDC_CLD); the rest is the simulated pool (SOURCE_SYSTEM = SIMULATED).", size=9)

    doc.h("4.2 How PI data flows to a decision – and why it is built this way", 3)
    doc.kv([
        ("L0 – Source", "The BDC Connect share exposes each PI data product as a catalog-linked database. Snowflake reads it in place; "
                        "nothing is copied and the share is never altered."),
        ("L1 – Domain views", "One view per business object (e.g. WORKFORCE.WORKFORCE_JOB) renames and casts PI fields and adds the "
                              "simulated pool with a SOURCE_SYSTEM tag. Views only, so zero-copy stays zero-copy."),
        ("L2 – Ontology", "ENT_PERSON, ENT_LEVEL and REL_PERSON_REPORTING_LINE are built once from L1 and shared by every mart."),
        ("L2 – Marts", "Dynamic tables such as DT_PERSON_MONTH_SCORECARD (billability, utilization, bench) and DT_PERSON_QUARTER_WPS "
                       "(the WPS) are keyed to ENT_PERSON."),
        ("Semantic layer", "SV_WORKFORCE_PERFORMANCE and SV_WORKFORCE_PRODUCTIVITY expose those facts with the shared dimensions."),
        ("Advisor and app", "The Advisor and pages P3, P4, P6 query only Semantic Views and serving views; each answer names its source."),
    ])
    doc.p("Design considerations", bold_lead="")
    doc.bullets([
        ("a) Why an L2 ontology. ", "Six source systems each describe a person, a project or a customer differently. The ontology "
         "defines each business entity once – one key, one set of attributes, one owning system – and every mart joins to it. "
         "Without it, 'headcount' in the workforce view and 'team size' in the pipeline view would disagree, and nothing could be "
         "joined across pillars. Example: ENT_PERSON merges the PI person record with timesheet, CRM bid-team and AI-telemetry "
         "identities under one PERSON_ID."),
        ("b) Why dynamic tables for the marts. ", "A dynamic table is declared as a query; Snowflake keeps it fresh to a target lag "
         "(1 hour here) and refreshes only what changed. There are no pipelines, schedulers or merge scripts to maintain, the "
         "dependency graph is tracked automatically, and when a new BDC share lands the change flows L1 → ontology → marts "
         "without extra code. Example: DT_PERSON_QUARTER_WPS recomputes a person's quarterly score when new timesheets arrive."),
        ("c) Why a semantic layer, and how dynamic tables implement it. ", "A Semantic View records business meaning – entities, "
         "relationships and metric formulas – on top of physical tables. Each mart dynamic table becomes a fact table in the view; "
         "the ENT_* tables become its dimensions; relationships are the joins between them. Metrics are defined once (e.g. "
         "billability_pct = delivery hours / available hours) so a dashboard, a SQL user and the Advisor all get the same number. "
         "Example: SV_WORKFORCE_PRODUCTIVITY uses DT_PERSON_QUARTER_WPS as its 'person_quarter' fact and ENT_PERSON / ENT_LEVEL as "
         "dimensions."),
        ("d) Why the Advisor answers more accurately. ", "Cortex Analyst writes SQL against a Semantic View, not against raw tables, "
         "so it can only use approved joins and metric definitions. Each view carries verified example questions with their "
         "SQL. The agent's routing instructions are generated from the ontology registry, so it knows which view holds which "
         "entity, and it splits a cross-pillar question across the right tools. Its answers cite the view and SQL used, and it "
         "is instructed to report associations with confidence intervals rather than claims of cause."),
    ])

    doc.h("4.3 Demo segment (8 minutes)", 3)
    demo_step(doc, "Step A1 – Where the PI data comes from (P8 BDC Sources & Lineage)", [
        ("Click", "P8. Filter the L0 layer to BDC_CLD; point at the four PI products."),
        ("Say", f"'These are SAP People Intelligence data products shared through BDC – {pi_rows:,} rows, read in place, nothing copied.'"),
        ("Show", "The lineage from COREWORKFORCEDATA_V1 to ENT_PERSON to the scorecard."),
    ])
    demo_step(doc, "Step A2 – Availability becomes billability (P3 Time Mix & Bench)", [
        ("Click", "P3, Financial Services, FY26."),
        ("Say", f"'Employee Availability gives the denominator. FS billability is {pct(fs26['BILLABILITY'])} against level targets; "
                f"{F['roll']['N']} people roll off in 90 days and {F['roll']['BELOW']} of them are below the AI-skill level the pipeline needs.'"),
        ("Value", "Bench cost is visible before it is incurred; the resource manager sees who to staff or train."),
    ])
    demo_step(doc, "Step A3 – Core Workforce drives attrition risk (P4 People Intelligence)", [
        ("Click", "P4; show the risk deciles and top drivers."),
        ("Say", f"'Leavers, tenure and level from Core Workforce train a Snowflake ML model. FS voluntary attrition is "
                f"{pct(fs26['VOLUNTARY_ATTRITION'])} in FY26. The list is a prompt for a conversation, not a prediction about a person.'"),
    ])
    demo_step(doc, "Step A4 – Job relationships create the Team pillar (Advisor + Snowsight)", [
        ("Ask the Advisor", "'What is the productivity (WPS) of the workforce at each level, and how do billability and utilization compare?'"),
        ("Say", "'The reporting line from the job-relationship data lets us score a manager on their team – direct reports for "
                "Managers, the whole reporting tree for Senior Managers and Principals.'"),
        ("Snowsight", "SELECT * FROM ACOCO_L2.SERVING.VW_WPS_BY_LEVEL WHERE SCOPE='FIRM' AND FISCAL_YEARS='FY26';"),
    ])
    demo_step(doc, "Step A5 – The 'one map entry' promise", [
        ("Say", "'Skills, Learning and Performance are simulated today in BDC shape. When SAP shares them, one entry in the L1 map "
                "changes and the view switches source – the ontology, Semantic Views, Advisor and app are untouched.'"),
    ])

    # 5 ---------------------------------------------------------------------------------------
    doc.h("5. Focus Demo B – The Ontology", 2)
    doc.p(f"The MD's questions cross six source systems and {sv_n} Semantic Views. The ontology is the one explicit model of the "
          "business they share – not a separate graph database, but a small set of governed tables in the ACOCO_L2.ONTOLOGY "
          "schema that every view, the Advisor and the app use.")
    doc.h("5.1 Entities", 3)
    doc.p("How entities are stored. Each entity is a dynamic table named ENT_<ENTITY> in ACOCO_L2.ONTOLOGY (e.g. ENT_PERSON), "
          "built from the L1 domain views with one row per business key (PERSON_ID, PROJECT_ID …), its attributes and a "
          "SOURCE_SYSTEM column. A registry table, ONTOLOGY.ONT_ENTITY, lists every entity with its definition, owning system, "
          "key, row count, share coming from BDC and the Semantic Views that use it – this is the table shown below.", size=9)
    doc.table(["Entity", "System of record", "Rows", "% from BDC", "Used by Semantic Views"],
              [[e["ENTITY"], e["OWNING_SYSTEM"], f"{e['ROW_COUNT']:,}", e["BDC_CLD_SHARE_PCT"], e["SEMANTIC_VIEWS"].replace("SV_", "")]
               for e in F["ents"]], widths=[2.8, 4.8, 1.5, 1.6, 6.3], size=8)
    doc.h("5.2 Relationships", 3)
    doc.p("How relationships are built and stored. A one-to-many link is a key on the entity itself (ENT_PERSON.MD_GROUP_ID → "
          "ENT_MD_GROUP). A many-to-many link is a relationship table REL_<NAME> in ACOCO_L2.ONTOLOGY, built as a dynamic table "
          "from the source events – e.g. REL_PERSON_SKILL (person holds skill, with proficiency) or REL_PERSON_REPORTING_LINE "
          "(manager → team member, by depth). In each Semantic View the relationship becomes a declared join. The registry "
          "table ONTOLOGY.ONT_RELATIONSHIP records each relationship with its verb, cardinality, join keys and the views that "
          "implement it; the build fails if a view joins two entities through a relationship that is not registered.", size=9)
    doc.table(["From", "Verb", "To", "Cardinality", "Implemented in"],
              [[r["FROM_ENTITY"], r["VERB"], r["TO_ENTITY"], r["CARDINALITY"], r["SEMANTIC_VIEWS"].replace("SV_", "")] for r in F["rels"]],
              widths=[2.6, 3.0, 2.8, 2.4, 6.2], size=8)
    doc.h("5.3 Metrics and build guarantees", 3)
    doc.p(f"ONT_METRIC is the metric registry: one row per metric published in any Semantic View, with its definition, SQL "
          f"expression, business pillar and the view and table that own it. There are {n_met} – "
          + ", ".join(f"{k} {v}" for k, v in met_n.items()) + ". It lets anyone ask 'what does billability mean, and where is it "
          "used?' with a query rather than a meeting.", size=9)
    doc.table(["Guarantee", "Example"], [
        ["Every Semantic View uses the same ENT_* tables as its dimensions, with the same names and keys.",
         "person_level in SV_WORKFORCE_PERFORMANCE and SV_WORKFORCE_PRODUCTIVITY both read ENT_PERSON.LEVEL, so 'by level' "
         "means the same in both views."],
        ["Each metric is defined once and reused.",
         "billability_pct = 100 × delivery hours / available hours is the same formula in the workforce, portfolio and "
         "productivity views."],
        ["Every join is fact → entity or a registered entity → entity relationship, and no fact reaches an entity by two paths.",
         "AI usage joins ai_tool and ai_model directly; ai_model is deliberately not joined to ai_tool, which would give usage two "
         "routes to the same tool and could double-count spend."],
        ["The build fails on an unregistered join, a duplicate key, an unregistered metric or a direct read of source data in L2.",
         "Adding a metric to a view without registering its pillar stops the build at the ontology check."],
        ["The Advisor's routing is generated from the registry, so it cannot drift from the views.",
         f"'person studies learning_category' is registered against SV_WORKFORCE_PRODUCTIVITY, so curriculum questions are "
         "routed to the productivity tool."],
    ], widths=[7.0, 10.0])
    doc.h("5.4 Demo segment (6 minutes)", 3)
    demo_step(doc, "Step B1 – The picture (C4 Platform Architecture)", [
        ("Click", "C4; the entity graph coloured by owner (S/4HANA, People Intelligence, non-SAP)."),
        ("Say", "'SAP is the record. Snowflake adds the context SAP does not hold – CRM, assets, AI telemetry – and the "
                "relationships between them.'"),
    ])
    demo_step(doc, "Step B2 – The registry is data (Snowsight)", [
        ("Run", "SELECT * FROM ACOCO_L2.ONTOLOGY.ONT_RELATIONSHIP ORDER BY 1;  then  SELECT PILLAR, COUNT(*) FROM ACOCO_L2.ONTOLOGY.ONT_METRIC GROUP BY 1;"),
        ("Say", f"'{n_rel} relationships, each with the Semantic Views that implement it. {n_met} metrics, each with one definition and a pillar.'"),
    ])
    demo_step(doc, "Step B3 – One question, two pillars (P10 Ask the Advisor)", [
        ("Ask", "'Which people rolling off in FS best match my open bids, and are they below the pipeline AI-skill level?'"),
        ("Say", "'Person is the same entity in the pipeline view and the workforce view, so the Advisor splits the question across "
                "two tools and joins the answers by person. That is the ontology at work.'"),
        ("Show", "The tool trace: pipeline_presales then workforce, with the SQL each ran."),
    ])
    demo_step(doc, "Step B4 – The ontology grows without breaking (talk track)", [
        ("Say", "'For the productivity score we added three entities and two relationships. The build re-checked every view and "
                "the Advisor's routing was regenerated from the registry. Nothing downstream was hand-edited.'"),
    ])

    # 6 ---------------------------------------------------------------------------------------
    doc.h("6. Section-by-Section Demo Guide – Two Tracks", 2)
    doc.p("Walk the same pages in the same order for either audience; change what you highlight. Track 1 is for architects and "
          "data leaders, Track 2 for the MD, finance and HR. Pages: C = context, P = pillar and platform pages.")
    pages = [
        ("C1 Business Overview", "Read the 'How ACoCo makes (and loses) money' card",
         "Business rules (bill codes, time targets by level) live in governed tables, not in the app code.",
         "One model of the business shared by every page and the Advisor.",
         f"Firm FY26: {usd_m(firm[2026]['revenue'])} revenue, {pct(firm[2026]['margin_pct'])} margin, {firm[2026]['headcount']:,} people",
         "Everyone sees how margin is made and lost: hours × rate – cost, five uses of time.", "Shared language for the leadership team."),
        ("C4 Platform Architecture", "Focus Demo B steps B1-B2",
         "Three-layer medallion; ontology registry queried as data.", "Zero-copy BDC sharing; governance and lineage built in.",
         f"{n_ent} entities, {n_rel} relationships, {sv_n} Semantic Views",
         "One connected view of people, projects, bids and assets.", "Answers to cross-functional questions without a data project."),
        ("P0 ProServe360 Overview", "Financial Services, FY26 vs FY25",
         "Every tile is a Semantic View or serving-view query; no metric is computed in the browser.",
         "Semantic Views give BI and AI the same numbers.",
         f"FS revenue {usd_m(fs26['REVENUE'])}, margin {pct(fs26['MARGIN_PCT'])}, billability {pct(fs26['BILLABILITY'])}, win-rate {pct(fs26['WIN_RATE'])}",
         "The group scorecard by pillar and the top risks by dollars at stake.", "Monthly review takes minutes, not a week of spreadsheets."),
        ("P1 Portfolio & Pareto", "Sort by forecast margin; pick the hero project",
         "S/4HANA journal and project data read zero-copy, joined to CRM.", "No extract from SAP; always current.",
         f"Large projects are {pct(fs26['LARGE_PROJECT_REVENUE_SHARE'])} of FS revenue",
         "Where revenue comes from and which fixed-price projects are below 10 % margin.", "Focus the MD's time on the few projects that decide the year."),
        ("P2 Project Health", f"Open {story}; press 'Why?'",
         "Earned value from S/4HANA plus Cortex Search over project-manager notes.", "Structured and unstructured data in one platform, one governance model.",
         f"{story}: CPI {f(s['CPI']):.2f}, SPI {f(s['SPI']):.2f}, LD {usd_m(s['LD_EXPOSURE'])}, {s['FORECAST_SLIP_WEEKS']} weeks late",
         "Why the project is off plan, from the numbers and the project manager's own words.", "Intervene before the loss is booked and LDs are triggered."),
        ("P11 Asset Library", f"Show missed reuse for {story}",
         "AI embeddings match each work package to library assets (AI_EMBED similarity).", "AI functions run in SQL next to the data.",
         "Matching assets not reused, with ESTIMATED hours saved",
         "Which accelerators would have helped, and how much they could have saved.", "Turn past work into margin on the next project."),
        ("P5 Pipeline & Pursuit", "Compare skill-fit bands; show suggested bench additions",
         "Win-rate compared within size class; bench-to-pipeline match scores people against bids.", "Reasoning (matching, ML) runs where the data is.",
         f"FS FY26 win-rate {pct(fs26['WIN_RATE'])}",
         "Which bids we win, at what pursuit cost, and who would raise the odds.", "Higher win-rate per pursuit dollar; bench time becomes pipeline."),
        ("P3 Time Mix & Bench", "Focus Demo A step A2",
         "PI availability is the base of every hours metric, defined once in the ontology registry.", "BDC data products used in place, joined with non-SAP time data.",
         f"{F['roll']['N']} FS roll-offs, {F['roll']['BELOW']} below the pipeline AI-skill level",
         "The five-way time mix by level vs target; who rolls off in 90 days.", "Bench cost seen before it is incurred."),
        ("P4 People Intelligence", "Focus Demo A step A3",
         "Snowflake ML attrition model and demand forecast trained on PI history.", "ML inside the governed platform; no data leaves.",
         f"FS attrition {pct(fs26['VOLUNTARY_ATTRITION'])}",
         "Who may leave and whether our skills match the pipeline.", "Retention conversations and hiring plans on evidence."),
        ("P6 AI Productivity & Learning + WPS", "Show AI spend and bands, then the WPS segment (section 7) in P10 or Snowsight",
         "Person-cluster bootstrap tests with confidence intervals; product-available windows; truth-recovery checks.",
         "Statistical reasoning in Snowflake, exposed through a Semantic View.",
         f"AI spend {usd_m(total_cost)} to date across five products; FY26 AI-active uplift +{f(ai26['UPLIFT_WPS']):.1f} WPS points",
         "A balanced productivity score by level and what is associated with it.", "Fund the AI tools and curricula that are associated with results."),
        ("P10 Ask the Advisor", "Use the prompts in section 9",
         f"Cortex Agent with {sv_n} Cortex Analyst tools and 2 Cortex Search tools; routing generated from the ontology.",
         "Agents grounded in governed Semantic Views, with cited SQL.",
         "Answers name their sources and report associations, not causes",
         "Ask anything across the pillars in plain language.", "Self-service answers for the MD, with the evidence attached."),
        ("P8 BDC Sources & Lineage", "Focus Demo A step A1",
         "Lineage from every CLD table through L1 to L2.", "Zero-copy sharing with full lineage.",
         f"{F['cld_tables']} CLD tables, {F['cld_rows']:,} rows read in place",
         "Where each number comes from.", "Trust the numbers in the board pack."),
        ("P9 Data Trust", "Close: consumers read L2 only",
         "Freshness, completeness and checks; ACCESS_HISTORY shows the source boundary is respected.", "Governance evidence is a query, not a promise.",
         "All checks green",
         "Can I trust it?", "Audit-ready decision support."),
    ]
    doc.h("6.1 Track 1 – Technical", 3)
    doc.table(["Page", "What to show", "Technical design to highlight", "Snowflake unique value", "Proof"],
              [[p[0], p[1], p[2], p[3], p[4]] for p in pages], widths=[2.6, 3.1, 4.3, 3.6, 3.4], size=8)
    doc.h("6.2 Track 2 – Business", 3)
    doc.table(["Page", "What to show", "Business question answered", "Value to the business", "Proof"],
              [[p[0], p[1], p[5], p[6], p[4]] for p in pages], widths=[2.6, 3.1, 4.0, 3.9, 3.4], size=8)
    doc.p("Pages C2 (Dashboard Overview), C3 (Demo Overview) and P7 (Context & Reasoning gallery) are supporting pages: use C2 as "
          "the agenda, and walk P7 while a long Advisor answer streams.", size=9)

    # 7 ---------------------------------------------------------------------------------------
    doc.h("7. Workforce Productivity Score – Demo Segment", 2)
    doc.p("The WPS answers 'what is a balanced way to measure productivity?'. It scores every person each fiscal quarter from 0 to "
          "100, where 50 is the average of their level in that year, across four pillars:")
    doc.table(["Pillar", "Inputs", "Why it is balanced"], [
        ["Value Creation (VC)", "Win-rate of bids the person was named on; earned-hour efficiency", "Rewards winning work, not just bid hours"],
        ["Operational Excellence (OE)", "Schedule performance; earned-hour efficiency", "Rewards delivering on plan"],
        ["People Development (PD)", "Billability, utilization, asset reuse, learning, asset creation (Manager and below: billability 30 / "
                                    "utilization 20; Senior Manager and above: 20 / 30; asset reuse 20, learning 15, asset creation 15)",
         "Weights follow the level's job"],
        ["Team (TM)", "Mean WPS of the team (Managers and above with at least 3 scored team members)", "Leaders are scored on their people"],
    ], widths=[3.5, 9.0, 4.5])
    doc.h("7.1 Productivity by level (FY26, firm)", 3)
    doc.table(["Level", "People", "Median WPS", "VC", "OE", "PD", "TM", "Billability (target)", "Utilization (target)", "TM coverage"],
              [[r["LEVEL"], r["PEOPLE"], r["WPS"], r["VC"], r["OE"], r["PD"], r.get("TM") or "n/a",
                f"{r['BILL']} % ({r['BILL_T']} %)", f"{r['UTIL']} % ({r['UTIL_T']} %)", f"{r['TM_COV']} %"] for r in F["wps"]],
              widths=[2.4, 1.3, 1.6, 1.1, 1.1, 1.1, 1.1, 2.6, 2.6, 2.1], size=8)
    doc.p("Talk track: medians sit near 50 by construction – the score is relative within level. The story is in the spread and in "
          "billability vs utilization: utilization includes recorded asset-building hours, which are not budgeted, so it can exceed "
          "its target and even 100 %.", size=9)
    doc.h("7.2 What is associated with productivity", 3)
    cx_lv = [r for (st, ex, oc), r in F["vend"].items() if ex == "CORTEX" and oc == "WPS" and st != "ALL LEVELS"]
    doc.table(["Question", "Test", "Firm result (all levels)", "By level", "How to say it"], [
        ["AI tokens", "Token use vs WPS", f"rho {f(tok_all['RHO']):.3f} (CI {f(tok_all['LO']):.3f} to {f(tok_all['HI']):.3f})",
         ", ".join(f"{k} {f(v['RHO']):.2f} {v['EFFECT_SIZE'].replace('_', ' ').lower()}" for k, v in F["tok"].items() if k != "ALL LEVELS"),
         "'Token use is associated with higher WPS for junior levels; not significant for Senior Managers and Principals.'"],
        ["AI products", "Product share of tokens vs WPS (only in quarters the product existed)",
         f"Cortex rho {f(cx_all['RHO']):.3f}; Claude Code {f(cc_all['RHO']):.3f}; Cortex → OE {f(cx_oe['RHO']):.3f}",
         f"Cortex significant at {len(cx_lv)} of 5 levels", "'Cortex use is associated with higher WPS – mostly through Operational Excellence.'"],
        ["Training hours", "Prior training vs WPS without the learning input",
         f"rho {f(trn_all['RHO']):.3f} (CI {f(trn_all['LO']):.3f} to {f(trn_all['HI']):.3f})",
         ", ".join(f"{k} {f(v['RHO']):.2f}" for k, v in F["trn"].items() if k != "ALL LEVELS"),
         "'Training is associated with later productivity – measured without counting the training itself.'"],
        ["Curricula", "Curriculum hours vs WPS and the curriculum's target pillar; payback after a course",
         f"Top payback {pay_top['CURRICULUM']} +{f(pay_top['PAYBACK_WPS']):.1f} WPS points; PROJECT_MGMT {f(pay_pm['PAYBACK_WPS']):+.1f}",
         f"{len(F['cur'])} significant curriculum × level results", "'AI curricula show the clearest payback; project-management training does not.'"],
    ], widths=[2.2, 3.4, 4.0, 4.0, 3.4], size=8)
    doc.h("7.3 Click path", 3)
    doc.numbered([
        "P10 Ask the Advisor: 'What is the productivity (WPS) of the workforce at each level, and how do billability and utilization compare?'",
        "P10: 'Is Claude Code, Codex or Cortex usage associated with productivity within each level?' – each product is only tested in "
        "quarters it existed (Claude Code and Codex from May 2025, Cortex from November 2025).",
        "P10: 'Which curricula are associated with higher productivity, by level?'",
        "Snowsight (technical audiences): SELECT * FROM SEMANTIC_VIEW(ACOCO_L2.SEMANTIC.SV_WORKFORCE_PRODUCTIVITY "
        "DIMENSIONS person.person_level METRICS person_quarter.avg_wps, person_quarter.billability_pct WHERE fiscal_month.fiscal_year = 2026);",
    ])
    doc.h("7.4 Why you can trust it", 3)
    doc.bullets([
        ("Truth recovery. ", f"The simulator plants known effects; the tests recover {rec} of {seeded} planted effects by sign and "
         f"leave {nulls_ok} of {nulls} no-effect cases non-significant."),
        ("Small groups are suppressed. ", "A result needs at least 15 people and 30 person-quarters, otherwise it is shown as a small cell."),
        ("Significance has a floor. ", "Significant means the 90 % confidence interval excludes 0 and |rho| is at least 0.05; smaller is negligible."),
        ("Known limitations, said aloud. ", "The Industry curriculum → win-rate link and three Claude Code results can show significance "
         "where none was planted; the Advisor is instructed to flag them."),
        ("FS alone is not significant. ", f"Financial Services on its own shows +{f(aifs['UPLIFT_WPS']):.1f} (CI {f(aifs['CI_LOW']):.1f} to "
         f"{f(aifs['CI_HIGH']):.1f}) – say so; the firm-wide result (+{f(aip['UPLIFT_WPS']):.1f}, FY24-FY26) is the evidence."),
    ])

    # 8 ---------------------------------------------------------------------------------------
    doc.h("8. Demo Scripts", 2)
    doc.h("8.1 Full demo (30 minutes)", 3)
    doc.table(["Min", "Beat", "Screen", "Spoken claim"], [
        ["0-3", "Framing", "C1 → C4", f"Bill codes, five uses of time, three pillars; firm FY26 {usd_m(firm[2026]['revenue'])}, {pct(firm[2026]['margin_pct'])} margin"],
        ["3-7", "People Intelligence data products", "P8 → P3", "Four PI products zero-copy; availability becomes billability; roll-offs"],
        ["7-10", "ProServe360", "P0", f"FS FY26 vs FY25 per pillar; margin {pct(fs26['MARGIN_PCT'])}"],
        ["10-15", "Operational Excellence", "P1 → P2 → P11", f"{story} in loss: CPI {f(s['CPI']):.2f}, LD {usd_m(s['LD_EXPOSURE'])}; why; missed reuse"],
        ["15-18", "Value Creation", "P5", "Win-rate by effort and fit; bench people who raise the odds"],
        ["18-24", "Workforce Productivity Score", "P10 (+ Snowsight)", "WPS by level; tokens, products, curricula – associations with confidence intervals"],
        ["24-28", "Ontology", "C4 → P10", "Registry as data; one cross-pillar question split across two tools"],
        ["28-30", "Close", "P9", "Governance evidence; what goes back to SAP per pillar"],
    ], widths=[1.3, 3.8, 3.2, 8.7])
    doc.h("8.2 People Intelligence & ontology deep-dive (15 minutes)", 3)
    doc.table(["Min", "Beat", "Screen"], [
        ["0-2", "Why PI data needs context", "C1"],
        ["2-7", "Focus Demo A steps A1-A3", "P8, P3, P4"],
        ["7-10", "Team pillar from job relationships (A4) + WPS by level", "P10"],
        ["10-14", "Focus Demo B steps B1-B3", "C4, Snowsight, P10"],
        ["14-15", "'One map entry' promise (A5)", "Talk track"],
    ], widths=[1.3, 10.0, 5.7])

    # 9 ---------------------------------------------------------------------------------------
    doc.h("9. Advisor Prompts", 2)
    doc.p(f"The Advisor has {sv_n} Cortex Analyst tools (one per Semantic View) and 2 Cortex Search tools. Ask these in this order; "
          "simple answers take under a minute, cross-pillar answers one to two minutes.")
    doc.table(["Prompt", "Tool(s)", "What to point out"], [
        ["Give me my FY26 ProServe360 scorecard against FY25.", "portfolio", "Pillar framing and the Sources line"],
        [f"What are the CPI and SPI of project {story} and its forecast margin?", "project_delivery", f"CPI {f(s['CPI']):.2f}"],
        [f"Why is project {story} behind schedule?", "project_commentary", "Search over project-manager notes, cited"],
        ["Which people rolling off in FS best match my open bids?", "pipeline_presales (+ workforce)", "Ontology: person joins two views"],
        ["What is the productivity (WPS) of the workforce at each level?", "productivity", "WPS 0-100, 50 = level average"],
        ["Is AI token usage associated with productivity within each level?", "productivity", "'associated with', rho and confidence interval"],
        ["Is Claude Code, Codex or Cortex usage associated with productivity?", "productivity", "Tested only in quarters each product existed"],
        ["Which curricula are associated with higher productivity, by level?", "productivity", "Payback and target-pillar results"],
        ["Does AI make my skilled-but-inactive consultants more productive?", "ai_adoption / productivity", "'No significant effect' – the honesty test"],
    ], widths=[7.5, 3.5, 6.0])

    # 10 --------------------------------------------------------------------------------------
    doc.h("10. Validation & Honesty", 2)
    doc.bullets([
        "Every figure in this playbook is measured from the demo environment, not designed.",
        "Simulated rows are demo data (SOURCE_SYSTEM = SIMULATED) – say so once, on P8.",
        "Hours saved by asset reuse are estimated.",
        "AI and learning results are associations within level, with 90 % confidence intervals – never 'causes', 'drives' or 'makes'.",
        "The attrition list is a prompt for a conversation, not a prediction about an individual. Never quote pay.",
    ])

    # 11 --------------------------------------------------------------------------------------
    doc.h("11. Architecture Summary", 2)
    doc.table(["", "L0 Source", "L1 Domain", "L2 Assets"], [
        ["Content", f"{F['cld_tables']} BDC CLD tables (S/4HANA + People Intelligence) + simulated gap-fill + Snowflake account usage",
         "Domain views (BDC data plus simulated pool, tagged SOURCE_SYSTEM)",
         f"Core calendar, ontology ({n_ent} entities), 6 marts, reasoning, {sv_n} Semantic Views, {F['serving']} serving views, quality checks"],
        ["Object type", "As shared / as loaded", "Views only", "Dynamic tables, views, Semantic Views, Cortex Search, ML"],
        ["Read by", "L1 only", "L2 only", "Advisor, app, publish-back – nothing else"],
    ], widths=[2.3, 4.5, 4.0, 6.2])

    # 12 --------------------------------------------------------------------------------------
    doc.h("12. Discovery Questions", 2)
    doc.bullets([
        "Which SAP SuccessFactors People Intelligence data products have you licensed, and which are shared through BDC today?",
        "How do you measure an individual's productivity today – and does it differ by level?",
        "Do you know whether the AI tools and curricula you fund are associated with better delivery?",
        "What share of your contracts are fixed price, and how early do you see an overrun?",
        "Can you tie pursuit hours to win or loss, and to who was on the pursuit team?",
        "How many consultants roll off in the next 90 days without a next assignment?",
        "Where do definitions like 'billability' live today – and do HR and Finance agree on them?",
    ])

    # 13 --------------------------------------------------------------------------------------
    doc.h("13. Go-to-Market", 2)
    doc.kv([
        ("Land", "BDC Connect zero-copy + People Development on the customer's own People Intelligence data products"),
        ("Anchor", f"Medallion + ontology + Semantic Views as the governed system of context across S/4HANA, PI and CRM"),
        ("Expand", "Advisor across pillars; Workforce Productivity Score; publish-back of an AI-readiness data product to BDC"),
    ])

    # 14 --------------------------------------------------------------------------------------
    doc.h("14. Roadmap", 2)
    doc.bullets([
        "A dedicated Workforce Productivity Score page (pillars, level distributions, results with confidence intervals).",
        "Skills, Learning, Performance, Compensation and Succession switch from simulated to BDC data products as SAP shares them.",
        "Write-back to SAP (staffing requests, learning assignments) and publish-back of derived data products to BDC.",
    ])
    doc.save()
    print(f"wrote {V2}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure", action="store_true")
    a = ap.parse_args()
    if a.measure:
        measure()
    render()


if __name__ == "__main__":
    main()
