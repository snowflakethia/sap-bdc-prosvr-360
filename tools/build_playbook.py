"""Build docs/SAP BDC ProServe360 Demo Playbook.docx in the style of docs/ref_playbook."""
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

NAVY, LABEL, GOOD, BAD = "11567F", "E8F6FC", "D1FAE5", "FEE2E2"
OUT = "docs/SAP BDC ProServe360 Demo Playbook.docx"

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, m, Inches(1))
st = doc.styles["Normal"]
st.font.name, st.font.size = "Arial", Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
for name, size in (("Heading 1", 20), ("Heading 2", 14), ("Heading 3", 11.5)):
    h = doc.styles[name]
    h.font.name, h.font.size, h.font.bold = "Arial", Pt(size), True
    h.font.color.rgb = RGBColor.from_string(NAVY)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def rich(p, text):
    """**bold** segments inside text."""
    parts = text.split("**")
    for i, t in enumerate(parts):
        if t:
            r = p.add_run(t); r.bold = i % 2 == 1


def para(text, bold_lead=None, style=None):
    p = doc.add_paragraph(style=style)
    if bold_lead:
        p.add_run(bold_lead).bold = True
        p.add_run(" ")
    rich(p, text)
    p.paragraph_format.space_after = Pt(4)
    return p


def bullets(items):
    for t in items:
        rich(doc.add_paragraph(style="List Bullet"), t)


def table(header, rows, widths=None, label_col=False, verdict_col=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""
        r = c.paragraphs[0].add_run(h); r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); r.font.size = Pt(9)
        shade(c, NAVY)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]; rich(p, v)
            for r in p.runs: r.font.size = Pt(9)
            if label_col and i == 0:
                for r in p.runs: r.bold = True
                shade(cells[i], LABEL)
            if verdict_col is not None and i == verdict_col:
                shade(cells[i], BAD if v.lower().startswith(("gap", "roadmap", "simulated")) else GOOD)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths): row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def _card(rows):
    t = doc.add_table(rows=0, cols=2); t.style = "Table Grid"
    for k, v in rows:
        c = t.add_row().cells
        c[0].text = ""; r = c[0].paragraphs[0].add_run(k); r.bold = True; r.font.size = Pt(9); shade(c[0], LABEL)
        c[1].text = ""; rich(c[1].paragraphs[0], v)
        for r in c[1].paragraphs[0].runs: r.font.size = Pt(9)
    for row in t.rows:
        row.cells[0].width, row.cells[1].width = Inches(1.5), Inches(5.0)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ---------------------------------------------------------------- cover
p = doc.add_paragraph(); r = p.add_run("SNOWFLAKE | INTERNAL – CONFIDENTIAL"); r.bold = True
doc.add_heading("SAP BDC ProServe360 Demo Playbook", level=1)
para("Partner MD decision support for a professional-services firm on SAP Business Data Cloud + Snowflake")
para("PRD v2.6 (28 Oct 2026), measured presenter card (CP-11), runbook, and the live build on "
     "SFSEAPAC.SNOWFLAKE_SAP_APJ (repo snowflakethia/sap-bdc-prosvr-360). Demo today = 1 Oct 2026; FY26 just closed. "
     "Present live; do not send decks to customers.", bold_lead="Sources:")

# ---------------------------------------------------------------- 1
doc.add_heading("1. Executive Summary", level=2)
para("Professional-services firms sell people-hours priced by bill code. Margin is lost to fixed-price overrun, "
     "thin pursuit effort, bench cost and skills mismatch. S/4HANA shows the project P&L and SAP People Intelligence "
     "shows headcount and availability, but neither can say which bench consultant should join which bid, whether "
     "reusing an asset would have saved a loss-making project, or whether AI training made anyone faster.",
     bold_lead="The problem.")
para("SAP is the System of Record; Snowflake is the System of Context and Reasoning. SAP BDC data products arrive "
     "zero-copy as catalog-linked databases, are joined with data SAP does not hold (CRM pipeline, asset library, "
     "AI-tool telemetry, PM commentary) through a strict medallion and a shared ontology, and are reasoned over by "
     "Semantic Views, a Cortex Agent, Cortex Search and Snowflake ML. Decisions go back to SAP as actions.",
     bold_lead="Our position.")
para("Recommendations", bold_lead=None).runs[0].bold = True
bullets([
    "Lead with **People Development** (the SAP People Intelligence epic): it is the strongest proof that BDC data "
    "products become more valuable once joined with S/4, CRM and AI telemetry in Snowflake.",
    "Make **P-0615 Atlas Bank** the hero moment: a Large fixed-price project forecast at **-16.9 %** margin, "
    "CPI 0.70, $1.46M LD exposure, with **3** matching library assets it never reused.",
    "Close on the **AI productivity test**: +11.8 % uplift (90 % CI +9.8 to +13.8 %) for AI-active people, and "
    "**no significant effect** for skilled-but-inactive people. The honesty is the differentiator.",
    "Use the platform pages (C4, P8, P9) to land the architecture story: zero-copy L0, L1 domains, L2 ontology "
    "and Semantic Views, fee boundary evidenced by ACCESS_HISTORY.",
])

# ---------------------------------------------------------------- 2
doc.add_heading("2. Use Cases at a Glance", level=2)
table(["#", "Use Case", "Pillar", "Buyer", "Headline Proof (measured)"], [
    ["1", "ProServe360 Scorecard (PMD-0)", "Overlay", "Partner MD, COO", "FS FY26 revenue $70.29M, margin 34.3 % (-0.7 pts vs FY25)"],
    ["2", "Fixed-Price Exposure & Pyramid Drift (PMD-1, 2, 8)", "Operational Excellence", "Partner MD, Delivery Lead", "P-0615: forecast margin -16.9 %, CPI 0.70, LD $1.46M"],
    ["3", "Asset Harvest & Reuse (PMD-9)", "Operational Excellence", "COO, Head of Knowledge", "FS harvest 9.1 % → 29.2 %; median CPI 1.19 with reuse vs 1.10 without"],
    ["4", "Pursuit Payback & Team Fit (PMD-6, 10)", "Value Creation", "Partner MD, Sales Lead", "FS Large bids: 55.2 % win-rate (high effort + fit) vs 33.3 %"],
    ["5", "Time Mix, Bench & Roll-off (PMD-3)", "People Development", "Partner MD, Resource Mgr", "36 FS roll-offs in 90 days; 88.9 % below pipeline AI level"],
    ["6", "Skills Demand & Attrition Risk (PMD-4, 5)", "People Development", "CHRO, Partner MD", "Firm attrition 19.6 % (FY22) → 12.9 % (FY26)"],
    ["7", "AI Productivity & Learning Payback (PMD-7, 12)", "People Development", "CHRO, CIO, CFO", "+11.8 % uplift (significant); Agentic-AI payback +3.7 % FS"],
    ["8", "Capacity What-if via Advisor (PMD-11)", "Overlay", "Partner MD", "Bench-to-pipeline match + agent scenario with sources"],
], widths=[0.3, 2.0, 1.2, 1.3, 2.2])

# ---------------------------------------------------------------- 3
doc.add_heading("3. How We Validated", level=2)
para("Every figure the presenter speaks is measured, not designed. tools/presenter_card.py re-runs the exact registry "
     "statement each page uses; **37 / 37** figures match the pinned values. Thirteen story anchors (A1-A13) were "
     "measured at CP-11; four missed their design band and were accepted because the story still holds.")
table(["Anchor", "Design target", "Measured", "Verdict"], [
    ["A1 FS fixed-price loss", "margin < 0 %, CPI ~0.73", "P-0615 -16.9 %, CPI 0.70, SPI 0.96", "Accepted – over budget more than late"],
    ["A2 Firm Delivery / bench FY26", "~72 % / 1-2 %", "70.9 % / 1.4 %", "On target"],
    ["A5 People+Agents vs People-only", "margin ~+10 pts", "40.8 % vs 29.0 % (+11.8 pts)", "On target"],
    ["A6 Pursuit intensity win-rate", "~50 % vs ~30 %", "54.6 % vs 23.7 %", "Accepted – gap larger"],
    ["A8 Asset harvest firm", "15 % → 40 %", "11 % → 30 %", "Accepted – lower harvest"],
    ["A10 AI productivity uplift", "~+8 %, CI excludes 0", "+11.8 %, CI [+9.8, +13.8]", "Accepted – larger uplift"],
    ["A12 AI skilled but inactive", "~20 %", "34 of 170 (20 %)", "On target"],
], widths=[1.7, 1.5, 1.9, 1.5], verdict_col=3)
para("Honesty lines the presenter always states: simulated rows are demo data (SOURCE_SYSTEM = SIMULATED); hours "
     "saved by reuse are ESTIMATED; AI results are associations within level x work type, never causation; the "
     "attrition list is a conversation prompt, not a prediction.")

# ---------------------------------------------------------------- 4
doc.add_heading("4. Medallion Architecture", level=2)
para("A strict three-layer medallion. Each layer has one job, one reader and one writer; consumers read L2 only "
     "(the fee boundary).")
table(["", "L0 Source", "L1 Domain", "L2 Assets"], [
    ["Purpose", "Data as delivered by SAP BDC and non-SAP sources", "Trusted business objects, one domain at a time", "Cross-domain, consumption-ready assets for agent and app"],
    ["Content", "13 S/4HANA + 4 People Intelligence CLDs; ACOCO_SIM (34 tables); ACCOUNT_USAGE", "9 domain schemas, 41 views; CLD UNION SIM with SOURCE_SYSTEM", "CORE, ONTOLOGY, 5 marts, REASONING, SEMANTIC (5 SVs), SERVING (35 views), QUALITY"],
    ["Object type", "As shared / as loaded", "Views only – zero-copy stays zero-copy", "Dynamic tables, views, Semantic Views, Cortex Search, ML"],
    ["Allowed logic", "None", "Rename, cast, conform keys, drop technical columns, union", "Joins, entities, metrics, as-of logic, ML, search"],
    ["Read by", "L1 only", "L2 only", "Agent, app, publish-back – nothing else"],
], widths=[1.1, 1.8, 1.8, 1.9], label_col=True)

doc.add_heading("4.1 L0 – Zero-copy access", level=3)
_card([
    ["Connector", "SAP_BDC_CONNECTOR_APJ.PUBLIC.SNOWFLAKE_APJ (CONNECTED) – reused, never altered; CLDs shared with other demos are read-only"],
    ["People Intelligence", "COREWORKFORCEDATA_V1, EMPLOYEEAVAILABILITY_V1, WORKFORCEPLANNEDWORKINGTIME_V1, ASSIGNMENTADDITIONALINFORMATION_V1"],
    ["S/4HANA", "ENTRYVIEWJOURNALENTRY_V1 (13.7M rows), JOURNALENTRYHEADER_V1, PROJECT_V1, FINANCIALPLANNINGENTRYITEM_V1, COSTCENTER_V1, COSTCENTERACTIVITYTYPE_V1, PROFITCENTER_V1, GENERALLEDGERACCOUNT_V1, CUSTOMER_V1, SALESCONTRACT_V1, FISCALYEAR_V1, code lists"],
    ["Gap-fill", "ACOCO_SIM: CRM opportunities, timesheets, assignments, asset library, AI telemetry, and BDC-shaped back-history for products not yet shared (Skills, Learning, Performance)"],
    ["Proof point", "**16.9M rows** read from **13** CLD tables; nothing copied"],
])
doc.add_heading("4.2 L1 – Nine data domains", level=3)
table(["Domain", "Business objects", "L0 sources"], [
    ["ORGANISATION", "Cost centre, profit centre, activity type, GL, fiscal period, MD group, level", "COSTCENTER, ACTIVITYTYPE, PROFITCENTER, GL, FISCALYEAR CLDs"],
    ["FINANCE", "Journal item (reversal flag), header, plan item, internal order", "ENTRYVIEWJOURNALENTRY, JOURNALENTRYHEADER, FINANCIALPLANNING CLDs + SIM"],
    ["PROJECTS", "Project, WBS, milestone, work package, assignment, PM notes", "PROJECT_V1 + SIM"],
    ["TIME", "Timesheet record (Delivery/Bid/Learning/Admin), availability, planned time", "EMPLOYEEAVAILABILITY, PLANNEDWORKINGTIME CLDs + SIM"],
    ["SALES", "Customer, sales contract, opportunity, required skills", "CUSTOMER_V1, SALESCONTRACT_V1 + CRM (SIM)"],
    ["WORKFORCE", "Job record, job relationship, performance, compensation band, succession", "COREWORKFORCEDATA, ASSIGNMENTADDITIONALINFO CLDs + back-history"],
    ["TALENT", "Skill, person skill, learning item, completion", "SIM until SAP shares Skills / Learning"],
    ["ASSETS", "Asset, harvest, usage", "SIM (knowledge-management catalogue in production)"],
    ["AI_TELEMETRY", "AI tool, usage event", "SIM (OpenAI, Anthropic) + ACCOUNT_USAGE (Cortex)"],
], widths=[1.3, 2.9, 2.4], label_col=True)
para("Why L1 matters: when SAP shares a product that is simulated today, only one map entry changes and the L1 view "
     "switches source. L2, Semantic Views, agent and app are untouched.")
doc.add_heading("4.3 L2 – Data assets", level=3)
table(["Schema", "Assets", "Consumed by"], [
    ["CORE", "Fiscal month, VW_AS_OF (2026-10-01), DT_TIME_TARGET", "All L2"],
    ["ONTOLOGY", "12 ENT_*, 7 REL_*, ONT_ENTITY / ONT_RELATIONSHIP / ONT_METRIC", "Marts, SVs, agent, C4 graph"],
    ["5 marts", "PORTFOLIO_360, PROJECT_DELIVERY, PIPELINE_PRESALES, WORKFORCE_PERFORMANCE, AI_ADOPTION (DT_* facts keyed to ENT_*)", "Semantic Views"],
    ["REASONING", "Attrition risk, skill-demand forecast, bench-to-pipeline match, asset match, 2 Cortex Search services", "Agent tools, P4-P7, P11"],
    ["SEMANTIC", "SV_PORTFOLIO_360, SV_PROJECT_DELIVERY, SV_PIPELINE_PRESALES, SV_WORKFORCE_PERFORMANCE, SV_AI_ADOPTION", "Agent, app"],
    ["SERVING / QUALITY", "35 app-facing VW_*; checks, freshness, lineage counts, ACCESS_HISTORY snapshot", "App, P8, P9"],
], widths=[1.3, 3.7, 1.6], label_col=True)
para("Design rules worth saying: no CURRENT_DATE anywhere (today only via CORE.VW_AS_OF); TARGET_LAG = 1 hour on "
     "every DT a Semantic View reads; the app runs only SEMANTIC_VIEW() or SERVING queries – no metric is computed "
     "in TypeScript.")

# ---------------------------------------------------------------- 5
doc.add_heading("5. Ontology", level=2)
para("The MD's questions cross six sources and five Semantic Views. Without one explicit model, each view redefines "
     "\"person\" or \"project\" and the agent cannot route a cross-pillar question. The ontology is that model – not a "
     "graph database, but a small set of L2 assets in ACOCO_L2.ONTOLOGY.")
table(["Entity", "System of record", "L2 object"], [
    ["Person", "SAP People Intelligence (Core Workforce)", "ENT_PERSON"],
    ["Level / bill code", "PI payGrade + S/4 activity type", "ENT_LEVEL"],
    ["MD group", "S/4 cost-centre hierarchy", "ENT_MD_GROUP"],
    ["Customer", "S/4 Customer", "ENT_CUSTOMER"],
    ["Project / work package", "S/4 Project (WBS)", "ENT_PROJECT, ENT_WORK_PACKAGE"],
    ["Opportunity", "CRM (non-SAP)", "ENT_OPPORTUNITY"],
    ["Asset", "Asset library (non-SAP)", "ENT_ASSET"],
    ["Skill / learning item", "PI Skills (TIH) / Learning", "ENT_SKILL, ENT_LEARNING_ITEM"],
    ["AI tool / agent", "AI telemetry + S/4 AGT_* activity types", "ENT_AI_TOOL"],
    ["Time category", "Timesheet (Delivery, Bid, Learning, Admin, Bench)", "ENT_TIME_CATEGORY"],
], widths=[1.8, 2.8, 2.0], label_col=True)
para("**18 registered relationships** (ONT_RELATIONSHIP), e.g. Person holds Skill, Person pursues Opportunity, "
     "Opportunity becomes Project, Project reuses Asset, Asset embodies Skill, Work package requires Skill, "
     "Project consumes AI agent. **75 metrics** are registered once in ONT_METRIC with their pillar and owning "
     "Semantic View.")
table(["Where it is used", "What the audience sees"], [
    ["Platform Architecture page (C4)", "Entity graph coloured by owner (S/4HANA, People Intelligence, non-SAP): \"SAP is the record; Snowflake adds context\" on one screen"],
    ["Cortex Agent ACOCO_ADVISOR", "Entity → Semantic View map in its instructions, so a cross-pillar question is split across the right Analyst tools"],
    ["Build discipline", "All five SVs share the same ENT_* dimensions; CI fails on an unregistered join, a non-unique key or any L0 reference in L2"],
], widths=[2.0, 4.6], label_col=True)

# ---------------------------------------------------------------- 6
doc.add_heading("6. Use Case Detail", level=2)
details = [
    ("6.1 ProServe360 Scorecard", [
        ["Customer question", "\"How did my group do in FY26 against FY25, and where do my people's hours actually go?\""],
        ["SAP data", "Universal Journal, Project, Plan, Core Workforce, Employee Availability"],
        ["Snowflake", "SV_PORTFOLIO_360, DT_CAPACITY_MIX_MONTH vs DT_TIME_TARGET; Ask Cortex per card"],
        ["Proof", "FS: revenue $70.29M, margin 34.3 %, Delivery 71.3 % (target ~70 %), bench 1.4 %, win-rate 50.0 %, on-time 90.0 %"],
        ["Page · Story", "P0 · PMD-0"]]),
    ("6.2 Fixed-Price Exposure & Asset Reuse", [
        ["Customer question", "\"Which project decides my year, why is it slipping, and did we reuse what we already built?\""],
        ["SAP data", "ENTRYVIEWJOURNALENTRY, PROJECT (WBS), FINANCIALPLANNINGENTRYITEM, ACTIVITYTYPE rates, payGrade"],
        ["Non-SAP context", "PM status commentary, asset library harvest and usage"],
        ["Snowflake", "SV_PROJECT_DELIVERY; CSS_PROJECT_COMMENTARY (\"Why?\"); CSS_ASSET_LIBRARY + AI_EMBED asset match"],
        ["Proof", "P-0615 Atlas Bank: -16.9 % forecast margin, CPI 0.70, SPI 0.96, LD $1.46M; 3 matching assets not reused. FS reuse: median CPI 1.19 vs 1.10"],
        ["Page · Story", "P1 → P2 → P11 · PMD-1, 2, 8, 9"]]),
    ("6.3 Pursuit Payback & Team Fit", [
        ["Customer question", "\"Am I bidding the right deals, with the right people and the right effort?\""],
        ["SAP data", "Pre-sales GL on internal orders, activity-type rates, Core Workforce level"],
        ["Non-SAP context", "CRM opportunity stages, required skills, pursuit-team hours"],
        ["Snowflake", "SV_PIPELINE_PRESALES; win-rate by intensity and skill fit within size class; bench-to-pipeline match"],
        ["Proof", "FS Large bids: 55.2 % win-rate with high effort + fit vs 33.3 %; 22 open FS bids with suggested bench additions"],
        ["Page · Story", "P5 · PMD-6, 10"]]),
    ("6.4 Time Mix, Bench & Roll-off", [
        ["Customer question", "\"Who is on the bench, who is about to be, and are they skilled for what I sell next?\""],
        ["SAP data", "People Intelligence: Core Workforce, Employee Availability, Planned Working Time, Assignment Additional Information"],
        ["Snowflake", "SV_WORKFORCE_PERFORMANCE; five-way time mix by level vs target; VW_ROLL_OFF_90D"],
        ["Proof", "36 FS people roll off before 30 Dec 2026; 88.9 % sit below the pipeline's AI-skill level"],
        ["Page · Story", "P3 · PMD-3"]]),
    ("6.5 Skills Demand & Attrition Risk", [
        ["Customer question", "\"Which skills does my pipeline need that I lack, and who might leave?\""],
        ["SAP data", "Core Workforce (terminations, tenure, salary range), Skills, Learning (simulated until shared)"],
        ["Snowflake", "DT_ATTRITION_RISK (Snowflake ML), FC_DEMAND_BY_SKILL (ML forecast)"],
        ["Proof", "Firm voluntary attrition 19.6 % → 12.9 % FY22-FY26; FS FY26 13.1 %"],
        ["Page · Story", "P4 · PMD-4, 5"]]),
    ("6.6 AI Productivity & Learning Payback", [
        ["Customer question", "\"Does AI skill and AI use actually make my people faster – and is the learning paying back?\""],
        ["SAP data", "Skills (Agentic-AI family), Core Workforce level, AGT_* journal allocations"],
        ["Non-SAP context", "OpenAI, Anthropic and Cortex usage per person"],
        ["Snowflake", "SV_AI_ADOPTION; stratified test within level x work type, 90 % bootstrap CI; matched-control payback"],
        ["Proof", "+11.8 % uplift (CI +9.8 to +13.8 %); skilled-but-inactive +2.6 %, not significant (37 FS people); Agentic-AI payback +3.7 % FS; margin 40.7 % Human+Agent vs 26.3 % Human-only"],
        ["Page · Story", "P6 · PMD-7, 12"]]),
    ("6.7 Capacity What-if (Advisor)", [
        ["Customer question", "\"If my roll-offs join this pursuit, what happens to bench cost and the bid's skill fit?\""],
        ["Snowflake", "Cortex Agent ACOCO_ADVISOR: 5 Cortex Analyst tools (one per SV) + 2 Cortex Search tools; streamed answer with cited SQL"],
        ["Action in SAP", "Staffing request in S/4 Resource Management, WBS re-plan, SF Learning assignment (narrated, not executed)"],
        ["Page · Story", "P7 + P10 · PMD-11"]]),
]
for title, rows in details:
    doc.add_heading(title, level=3); _card(rows)

# ---------------------------------------------------------------- 7
doc.add_heading("7. Demo Script (30 minutes)", level=2)
table(["Min", "Beat", "Screen", "Spoken claim"], [
    ["0-3", "Framing", "C1 → C4", "Bill codes, five uses of time, three pillars; five-layer platform and ontology graph. Firm FY26: $327.94M, 35.2 % margin, 1,956 people"],
    ["3-5", "Where the data comes from", "P8", "13 CLD tables, 16.9M rows zero-copy incl. four People Intelligence products; 34 simulated tables and why"],
    ["5-8", "ProServe360", "P0", "FS FY26 vs FY25 per pillar; time mix by level vs target; top cross-pillar risks"],
    ["8-14", "Operational Excellence", "P1 → P2 → P11", "P-0615 in loss; critical work package and pyramid drift; \"why\" from PM notes; 3 assets it never reused"],
    ["14-18", "Value Creation", "P5", "Win-rate 55.2 % vs 33.3 %; open bids with weak fit and the bench people who raise it"],
    ["18-24", "People Development", "P3 → P4 → P6", "36 roll-offs; skills vs pipeline; attrition; AI uplift +11.8 % and the no-effect stratum"],
    ["24-28", "What-if", "P10 then P7", "Ask the PMD-11 what-if first (~2 min to answer); walk the P7 reasoning gallery while it runs"],
    ["28-30", "Close", "P9", "ACCESS_HISTORY fee-boundary evidence; publish-back to BDC; what goes back to SAP per pillar"],
], widths=[0.5, 1.3, 1.1, 3.7])

# ---------------------------------------------------------------- 8
doc.add_heading("8. Discovery Questions", level=2)
bullets([
    "What share of your contracts are fixed price, and how early do you see an overrun today?",
    "Can you tie pursuit hours to win or loss, and to who was on the pursuit team?",
    "How many consultants roll off in the next 90 days without a next assignment, and what does bench cost you?",
    "Have you licensed SAP People Intelligence or BDC, and which data products are shared?",
    "Do you know whether the AI tools and AI training you fund make anyone faster?",
    "Where do your reusable assets live, and do you measure harvest and reuse?",
    "Where does CRM pipeline data live, and how does it reach your SAP reporting?",
])

# ---------------------------------------------------------------- 9
doc.add_heading("9. Buying Group", level=2)
table(["Persona", "Role", "What they care about"], [
    ["Partner MD / Practice Lead", "Business sponsor", "Group margin, fixed-price risk, win-rate, bench, people risk"],
    ["COO / CFO", "Economic buyer", "Firm margin, utilisation vs target, LD exposure, AI spend return"],
    ["CHRO / Head of Talent", "Business sponsor", "Attrition, skills vs demand, learning payback – value from People Intelligence"],
    ["CIO / Head of Data", "Champion", "Zero-copy BDC, no pipeline rebuilds, governed semantic layer, one ontology"],
    ["SAP account team", "Partner", "BDC and People Intelligence adoption; publish-back of derived data products"],
], widths=[1.9, 1.3, 3.4])

# ---------------------------------------------------------------- 10
doc.add_heading("10. Go-to-Market", level=2)
_card([
    ["Land", "BDC Connect zero-copy + one pillar (People Development on People Intelligence) on the customer's own CLDs"],
    ["Anchor", "Medallion + ontology + five Semantic Views as the governed system of context across S/4, PI and CRM"],
    ["Expand", "Cortex Agent across pillars; reasoning use cases R1-R14; publish-back of an Agentic-AI Readiness data product to BDC"],
    ["Reuse", "Same SPCS React skeleton as Supply Chain 360, Finance 360 and Mining 360 on this account"],
])

# ---------------------------------------------------------------- 11
doc.add_heading("11. Demo Operations", level=2)
_card([
    ["App", "ACOCO_DB.APP.ACOCO_COMMAND_CENTER on compute pool ACOCO_POOL (CPU_X64_XS), owned by ACOCO_APP_ROLE, warehouse WH_ACOCO_APP"],
    ["Warm-up (5 min before)", "ALTER COMPUTE POOL ACOCO_POOL RESUME IF SUSPENDED; ALTER SERVICE … RESUME; wait for READY; click C1, P0, P2, P10 once"],
    ["Suspend (after)", "ALTER SERVICE … SUSPEND; then ALTER COMPUTE POOL ACOCO_POOL SUSPEND – the pool keeps running otherwise"],
    ["Timing", "Pages 1-2 s after warm-up; first click 5-10 s; Advisor ~1 min simple, ~2 min for PMD-11"],
    ["Troubleshoot", "SYSTEM$GET_SERVICE_LOGS for failures; grant ALL_ENDPOINTS_USAGE if \"not authorized\"; full detail in docs/RUNBOOK.md"],
])

# ---------------------------------------------------------------- 12
doc.add_heading("12. Gaps & Next Steps", level=2)
bullets([
    "Simulated data: transactions, CRM, asset library and AI telemetry are SOURCE_SYSTEM = SIMULATED; say so on P8.",
    "Skills, Learning, Performance, Compensation and Succession are simulated until SAP shares them; confirm exact product names in the BDC catalog.",
    "Fee boundary is a code rule plus ACCESS_HISTORY evidence, not a grant – in production it is a role.",
    "Write-back to SAP and publish-back to BDC are narrated, not executed; R4, R7, R8, R10, R11 are roadmap cards.",
    "The BDC sharing-fee rate is unconfirmed; do not quote it.",
])

doc.save(OUT)
print("wrote", OUT)
