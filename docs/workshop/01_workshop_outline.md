# Workshop Outline — SAP BDC Connect + Snowflake: From System of Record to System of Reasoning

**Audience:** Accenture SAP and data consultants (architects, data engineers, solution leads)
**Duration:** 4 hours (240 min) including two breaks
**Mode:** Technical, hands-on, instructor-led
**Lab environment:** Snowflake only. Participants have **no SAP or SAP BDC access**. All lab material is **cloned from a public GitHub repo** into Snowflake.
**Vehicle:** the SAP BDC Supply Chain 360 demo, repackaged as a lab repo
**Source analysis:** [`00_reference_analysis.md`](00_reference_analysis.md)

**Revision 3 changes:** added the lab environment design and the GitHub lab repo as a deliverable. Every module now has a second level of detail (slide list, demo script, lab steps, exercise brief) for review before build.

**Revision 4 — confirmed decisions:**

| Topic | Decision |
|---|---|
| GitHub | Owner is `snowflakethia`. Lab content is built and checked into this repo first (`sap-bdc-supply-chain-360/workshop/lab-repo/`), then copied by the owner into a new public lab repo |
| Accounts | One Snowflake **trial account per participant**, created by the Accenture team themselves. Cortex Analyst and Agents are assumed available in their region |
| Publishing | Cleared: all lab data is synthetic |
| Module 2 | **Live BDC demo**: share an SAP data product from BDC and mount it as a CLD in Snowflake |

---

## Core message

> **SAP holds the record. Snowflake adds context and reasoning. SAP BDC Connect links them without copying data.**

## Structure: one question, built bottom-up

> *"If Festo AG stops delivering, which orders are at risk, and for each part can we switch supplier, is the switch blocked, or does it need review?"*

```
Module 1  Why        System of Record  vs  System of Context and Reasoning
Module 2  ACCESS     SAP BDC data products -> zero-copy -> catalog-linked DBs (L0)
Module 3  PREPARE    Medallion: L1 views, L2 Dynamic Tables, entity views
Module 4  DEFINE     Semantic view = the ontology
Module 5  REASON +   Cortex Analyst, Cortex Agent, Native App
          ACTIVATE
Module 6  TRUST      Data quality, observability, validation
```

## Design decisions (carried from revision 2)

1. **Technical positioning, not partnership.** Module 1 is about System of Record vs System of Context and Reasoning (TechUp slides 4–5, 8–11). No GTM, rebate or competitor content.
2. **Concept first, build in dependency order.** Module 0 shows the finished answer; Module 1 explains why semantics matter. The semantic view is then built *after* the medallion because it depends on it.
3. **Features introduced just-in-time** in the layer that uses them (Dynamic Tables in Prepare, semantic views in Define, Cortex in Reason). The feature map is the handout.

---

## Lab environment design (new)

### Constraints

| Constraint | Consequence for the design |
|---|---|
| No SAP / SAP BDC access | Zero-copy connector and CLDs cannot be built by participants. **Module 2 is a live instructor demo**; participants work on a **simulated L0** that has the same objects and shape |
| The demo's L0 comes from an org-internal listing (`ORGDATACLOUD$INTERNAL$...`) | Not reachable from Accenture accounts. **L0 data must ship in the lab repo** as files (21 objects, 398 rows — small) |
| Demo repo is private (`snowflakethia/...`) and contains presales and internal material | Stage curated lab content in `workshop/lab-repo/` (self-contained, with no references to the rest of this repo), then copy it into a **separate public lab repo**; the demo repo stays private |
| `tools/gen_ops_ext.py` generates OPS_EXT with Python locally | Ship the **pre-generated output as files**; participants need no local Python |
| Labs must run inside Snowflake | Use **Snowflake Git integration** (`API INTEGRATION` + `GIT REPOSITORY`) and **Workspaces from Git**; load data with `COPY INTO` from the Git stage; run scripts with `EXECUTE IMMEDIATE FROM` |
| The Native App needs SPCS, an image registry and Docker | **Not built in the lab.** Instructor demo only (Module 5) |

### What is simulated vs real

| Element | In the lab | Shown how |
|---|---|---|
| BDC data products mounted as CLDs | **Simulated:** database `SC360_L0` with the 16 data-product schemas, loaded from repo files and made **read-only** to the lab role (mirrors a CLD) | Lab 1 |
| CSN-generated semantic view in `SNOWFLAKE$` | **Simulated:** one sample "CSN-style" semantic view over one data product, with 0 relationships (mirrors TechUp slide 12) | Lab 3 contrast |
| Zerocopy connector, BDC sharing, CLD mount | **Real, live instructor demo** on the instructor's BDC tenant and Snowflake account | Module 2 demo |
| Share-back to BDC | Slide only | Module 2 / 5 |
| L1, L2 Dynamic Tables, semantic view, agent, DMFs | **Real**, built by participants | Labs 1–5 |
| Native App on SPCS | **Real**, instructor only | Module 5 demo |

Every lab page states the simulated parts explicitly ("in a client account this database is a catalog-linked database created by the Zerocopy connector"). One known difference is raised in Module 6: DMFs **cannot** attach to a real share, but they *could* attach to the simulated L0 tables. The lab attaches them at L2, as in production.

### Participant accounts (confirmed)

Each participant uses their own Snowflake trial account (Enterprise edition recommended, AWS or Azure) with ACCOUNTADMIN, so there is no per-user prefixing or shared-account role setup. The pre-work email asks participants to create the trial at least 2 days ahead and run `setup/99_check.sql`. Trial credit consumption for the whole lab is expected to be small (XSMALL warehouse, 398-row dataset); this will be measured during the dry run.

### Setup flow (participants, about 10 min, done **before** the workshop)

1. Sign up for a trial (or receive credentials for the shared account).
2. In Snowsight, run `setup/00_connect_git.sql`. It creates the `API INTEGRATION` for `https://github.com/<org>`, the `GIT REPOSITORY` object and the warehouse `LAB_WH` (XSMALL).
3. Create a **Workspace from the Git repo** so the lab SQL files open in the editor.
4. Run `setup/01_load_l0.sql`: creates `SC360_L0`, runs `COPY INTO` from `@sc360_lab_repo/branches/main/data/l0/`, sets the database read-only for the lab role, and checks counts (expects 21 objects and 398 rows).
5. Run `setup/02_reference_build.sql`: builds the finished stack into `SC360_REF` (used for the Lab 0 hook and as a catch-up for anyone who falls behind).
6. Run `setup/99_check.sql`: a green / red checklist (Git, L0 counts, Cortex reachable, agent answers).

A **reset script** (`setup/98_reset_module.sql`) rebuilds any module's starting point, so a participant who falls behind can catch up in one command.

---

## Deliverable: the GitHub lab repo (new)

**Staging:** `sap-bdc-supply-chain-360/workshop/lab-repo/` (this repo, checked in first).
**Published:** a new public repo under `github.com/snowflakethia/`, created by the owner. Working name `sap-bdc-sc360-workshop`; the setup SQL keeps the repo URL in one variable so a rename is a one-line change. Because the repo is public, no Git secret is needed in participant accounts.

```
sap-bdc-sc360-workshop/
├── README.md                    What this is, prerequisites, 10-minute setup
├── LICENSE                      Plus a note that the data is synthetic
├── setup/
│   ├── 00_connect_git.sql       API integration, Git repo object, warehouse
│   ├── 01_load_l0.sql           Simulated L0 (16 schemas, 21 objects), read-only, count check
│   ├── 02_reference_build.sql   Finished stack in SC360_REF (Lab 0 hook, catch-up)
│   ├── 98_reset_module.sql      Rebuild the starting point for module N
│   └── 99_check.sql             Readiness checklist
├── data/
│   ├── l0/                      21 CSV/Parquet files (SAP BDC-shaped, synthetic)
│   └── ext/                     Pre-generated OPS_EXT and SUPPLIER_EXT
├── labs/
│   ├── lab0_hook/               Ask the reference agent
│   ├── lab1_access_profile/     Profiling queries, L1 view template + solution
│   ├── lab2_prepare_dt/         L2 Dynamic Tables, entity views, TARGET_LAG task + solution
│   ├── lab3_define_sv/          CSN-style SV, enterprise SV, add-a-relationship task + solution
│   ├── lab4_reason_agent/       Analyst questions, agent DDL, break-it task
│   └── lab5_trust/              Guard checks, DMF, LIMIT 0 harness
├── docs/
│   ├── lab_guide.md             Step-by-step for every lab, with expected results
│   ├── feature_map.md           Layer -> feature -> design question handout
│   ├── simulated_vs_real.md     What a client account would have instead
│   └── troubleshooting.md       Cortex region, Git auth, common SQL errors
└── exercises/
    ├── ex1_record_vs_reasoning.md
    └── capstone_scenarios.md
```

**Build approach.** Derive the files from the demo repo's `sql/02`–`07b`, parameterised by database name (the demo hard-codes `SAP_SUPPLY_CHAIN`). Export L0 and the extensions to files, and strip everything internal (presales kit, deployment scripts, account URLs, listing names). Tag a release (`v1.0-workshop`) so the content doesn't change between dry run and delivery.

---

## Format key

| Format | Meaning |
|---|---|
| **Slides** | Instructor presentation with discussion |
| **Demo** | Instructor drives the live system |
| **Lab** | Participants build in their own Snowflake account from the lab repo |
| **Exercise** | Group whiteboard or design exercise; no keyboard |

## Schedule at a glance

| Time | Min | # | Topic | Format |
|---|---|---|---|---|
| 0:00 – 0:10 | 10 | 0 | The question, and the answer we will build | Demo + Lab 0 |
| 0:10 – 0:35 | 25 | 1 | System of Record vs System of Context and Reasoning | Slides + Exercise |
| 0:35 – 1:10 | 35 | 2 | Access: SAP BDC data products and zero-copy | Slides + Demo |
| 1:10 – 2:00 | 50 | 3 | Prepare: medallion layers, Dynamic Tables, fee boundary | Slides + Labs 1–2 |
| 2:00 – 2:10 | 10 | — | Break | |
| 2:10 – 2:45 | 35 | 4 | Define: the semantic view as the ontology | Slides + Lab 3 |
| 2:45 – 3:15 | 30 | 5 | Reason and Activate: Cortex Analyst, Agent, Native App | Lab 4 + Demo |
| 3:15 – 3:25 | 10 | — | Break | |
| 3:25 – 3:45 | 20 | 6 | Trust: data quality, observability and validation | Slides + Lab 5 |
| 3:45 – 4:00 | 15 | 7 | Design review capstone and wrap-up | Exercise + Slides |

Setup is a **pre-workshop** task. A 30-minute optional "setup clinic" the day before catches account and Git problems without using workshop time.

---

## Module 0 — The question, and the answer we will build (10 min)

**Format:** Demo (5 min) + Lab 0 (5 min)

**Slides (2)**
1. Title and agenda: one question, six layers, four hours.
2. "The question": Festo AG stops delivering. Which orders are at risk? For each part: switch, blocked or review?

**Demo (3 min)**
- Native App *Business Scenario* page: company context and the Festo storyline.
- *Technology Architecture* page, a single pass: SAP BDC → CLD → Dynamic Tables → semantic view → Cortex → app. "We will build the middle of this."

**Lab 0 — the hook (5 min)** · `labs/lab0_hook/`
- In Snowflake Intelligence, select the reference agent (built by `setup/02` in `SC360_REF`).
- Ask: *"If Festo AG stops delivering, which customer orders are at risk and what is their value?"*
- Expected: 2 open orders, about $1.475M.
- Write the answer down; it is checked again in Lab 4.

**Key takeaway:** Start from the business decision. Every layer we build is there to make this answer correct, fresh, affordable and explainable.

---

## Module 1 — System of Record vs System of Context and Reasoning (25 min)

**Format:** Slides (15 min) + Exercise (10 min)

**Slides (7)**
1. **SAP is the System of Record:** one integrated chain (plan → procure → make → deliver → finance) that auditors trust. A global manufacturer example.
2. **The questions the board asks span SAP and non-SAP data:** plant status, disruption alerts, certifications, external risk.
3. **Snowflake as System of Context and Reasoning:** reasons over SAP plus non-SAP data; semantics make the reasoning reliable; SAP is never replaced.
4. **The stack:** Connect → Enrich → Activate, mapped to the workshop modules (Access, Prepare, Define, Reason, Activate, Trust). Roadmap items are labelled.
5. **Traditional access:** meaning hidden in SQL (crosswalk "B Ltd" = V204, recursive joins, hard-coded quality rule). Every team rebuilds it and gets a different answer.
6. **Ontology-based access:** the same question with declared identity, typed relationships (transitive part-of) and an explicit policy (quality bar = 90 → candidate / blocked / review).
7. **Where semantics operates:** source values → explicit meaning → consequences. "This is what Modules 3–5 build."

**Exercise — "Traditional vs ontology access" (10 min)** · `exercises/ex1_record_vs_reasoning.md`
- Groups of 3–4, each with a worksheet showing the F1 / C17 / C18 example (TechUp slide 9 data, rebuilt).
- Task A (4 min): list every piece of business meaning an analyst hard-codes today.
- Task B (3 min): sort each item into **Identity**, **Relationship** or **Policy**, and say where it should be declared once.
- Debrief (3 min): instructor reveals the reference list. Each group keeps its worksheet as the **checklist for Lab 3**.

**Key takeaway:** The value is not moving SAP data; it is declaring business meaning once so every team, BI tool and agent reasons the same way.

---

## Module 2 — Access: SAP BDC data products and zero-copy (35 min)

**Format:** Slides (20 min) + Demo (15 min). **No lab:** participants have no BDC tenant.

**Slides (8)**
1. **How BDC builds a data product:** S/4HANA CDS views → APRS → object store → Spark → data product, described by CSN and discovered via ORD.
2. **Three kinds of data product:** SAP-managed · extended (CDS pass-through fields) · custom (Datasphere local tables), and what Snowflake receives from each.
3. **Zero-copy into Snowflake:** Zerocopy Connector → invitation link → formation → list shares → catalog-linked database (read-only, Iceberg/Delta, no copy).
4. **Prerequisites that are architecture decisions:** same region as BDC Core (inter-region transfer is charged), AWS/Azure commercial, edition, ORGADMIN acceptance.
5. **CSN-generated semantic views (`SNOWFLAKE$`):** SAP field meaning arrives for free, but with 0 relationships, no cross-product joins and no policy. This is the gap Modules 3–4 fill.
6. **Share-back to SAP:** Iceberg V3, ORD/CSN, `SYSTEM$SAP_PUBLISH_DATA_PRODUCT`; SAP apps consume Snowflake output as a data product.
7. **Choosing the integration pattern:** managed DP zero-copy · custom via Datasphere · BW PCE · Snowflake-first (ECC, multi-ERP; one formation = one S/4 system) · copy to bucket or Kafka for non-BDC sources.
8. **What you'll use in the lab:** a simulated L0 with the same 16 data-product schemas and 21 objects, read-only; what is real vs simulated.

**Demo (15 min) — live:** SAP BDC sharing a data product → mounted as a CLD in Snowflake
1. **SAP BDC cockpit (4 min):** show the formation that includes SAP BDC Connect for Snowflake; pick one SAP-managed data product (e.g. Bill of Material) and share it to the Snowflake system.
2. **Snowflake, connector (3 min):** `SHOW`/`DESCRIBE ZEROCOPY CONNECTOR` (already connected; walk through the `CREATE ... PARTNER = SAP_BDC` and `CONNECT WITH CONFIG (INVITATION_LINK = ...)` SQL that was run beforehand).
3. **Mount (3 min):** `SYSTEM$ZEROCOPY_CONNECTOR_LIST_SHARES` → the newly shared product appears → create the catalog-linked database.
4. **Explore the CLD (3 min):** tables, read-only behaviour, the generated `SNOWFLAKE$` semantic view; `DESCRIBE` it to show 0 relationships.
5. **Map to the lab (2 min):** open the participant's `SC360_L0` side by side: same shape, simulated source.

Demo prep: the connector is connected and tested the day before; the data product used live is *unshared* beforehand so the share → mount step is genuinely new. A backup screen recording of the same flow is captured during the dry run, in case BDC is unavailable on the day.

**Key takeaway:** Mount, don't move. Zero-copy brings SAP data and its field meaning, but not cross-domain relationships or policy; those are what Snowflake adds.

---

## Module 3 — Prepare: medallion layers, Dynamic Tables and the fee boundary (50 min)

**Format:** Slides (15 min) + Lab 1 (15 min) + Lab 2 (20 min)

**Slides (7)**
1. **Zero-copy-first reference architecture:** three lanes in (zero-copy, batch ELT, streaming), each with its own L0/L1; the **5 principles**.
2. **Catalog sprawl:** one CLD per data product, 280–900+ databases; what breaks (discovery, governance, cross-domain joins, cost).
3. **The overlay:** L0 (never modified) → L1 (business-area views, one schema per data product, typed dates, normalised IDs) → L2 (Dynamic Tables by business process, plus entity views). Naming note.
4. **Dynamic Tables in one slide:** declarative SQL, TARGET_LAG, incremental vs full refresh, DT graph; keep `CURRENT_DATE()` in a view on top of the DT.
5. **The fee boundary:** reads on L0/L1 carry the SAP data-sharing fee (0.604 CU per US$ of compute, where applicable; confirm with SAP); reads on L2 don't, only refreshes do. Worked example: about 92% lower. TARGET_LAG is a cost lever.
6. **Preparing for the ontology:** `ENT_*` entity views (one row per key) = identity; recursive BOM paths = dependency.
7. **Lab briefing:** what you will build, and where it sits on the diagram.

**Lab 1 — Explore and profile L0, write one L1 view (15 min)** · `labs/lab1_access_profile/`
1. Browse `SC360_L0`: 16 schemas, 21 `A_*` objects. Try an `INSERT` to confirm the database is read-only.
2. Run four profiling queries: blank rate per key column · distinct values of one code field · date columns held as VARCHAR · orphan keys between BOM and material.
3. Record the findings in the lab sheet (feeds Module 6).
4. Write `SC360_L1_SUPPLY_CHAIN.<schema>.<business_object>` from the template, with `TRY_TO_DATE(...,'YYYYMMDD')`, `UPPER(TRIM())` keys and a `COMMENT` naming the SAP source.
5. Check: compare the view with the solution file; select from it.

**Lab 2 — Build L2 with Dynamic Tables (20 min)** · `labs/lab2_prepare_dt/`
1. Run `lab2_01_dynamic_tables.sql` (from demo `sql/03`) to create the 9 L2 DTs; run `lab2_02_serving_views.sql` (from `sql/02`).
2. In Snowsight, open one DT: graph, refresh mode (incremental or full), lag.
3. **Find the gap:** the DTs use `TARGET_LAG = DOWNSTREAM` with nothing downstream, so they have no schedule. Set an explicit lag on the leaf DT, run a manual refresh, and check the refresh history.
4. Create the entity views `ENT_SUPPLIER`, `ENT_MATERIAL`, `ENT_PLANT`.
5. Discussion (3 min): this demo skips L1. When would this client need it? What lag would you set, and why?

**Key takeaway:** Transform freely, persist selectively. L1 for discovery and governance; L2 for speed, concurrency and predictable cost.

---

## Break (10 min)

---

## Module 4 — Define: the semantic view as the ontology (35 min)

**Format:** Slides (10 min) + Lab 3 (25 min)

**Slides (5)**
1. **Semantic view = executable ontology:** logical tables (entities), relationships, facts, dimensions, metrics, verified queries.
2. **Mapping TechUp's three layers to semantic-view syntax:** concepts → logical tables; part-of → relationships; quality bar → verified query and instruction.
3. **CSN view vs enterprise view:** start from SAP field meaning, then add cross-domain relationships and policy.
4. **Design rules:** physical-first mapping, one metric definition for every consumer, `UNVALIDATED` labels, synonyms and sample values for entity resolution.
5. **Lab briefing:** the Festo path you will make answerable.

**Lab 3 — Build the ontology (25 min)** · `labs/lab3_define_sv/`
1. **Contrast first (5 min):** query the simulated CSN-style semantic view over one data product and try to ask a supplier → order question. It can't be answered: 0 relationships.
2. **Build (7 min):** run `lab3_01_semantic_view.sql` (from `sql/04`) to create `SC360_GOLD.SAP_SUPPLY_CHAIN_360`. Run `DESCRIBE SEMANTIC VIEW` and count entities and relationships.
3. **Trace (5 min):** follow the Festo path through the relationships: supplier → component → assembly → plant → order.
4. **Checklist (3 min):** tick off each Identity / Relationship / Policy item from the Module 1 worksheet.
5. **Extend (5 min):** add one synonym (so that "Festo" resolves to "Festo AG") or one verified query of your own, then re-create the view.

**Key takeaway:** If a relationship or policy is not declared in the semantic view, every consumer has to re-invent it, and they will get different answers.

---

## Module 5 — Reason and Activate: Cortex Analyst, Agent and the Native App (30 min)

**Format:** Lab 4 (20 min) + Demo (10 min)

**Slides (2, inside the lab briefing)**
1. Question → Cortex Analyst (SQL over the semantic view) → Agent (orchestrates tools and views) → Snowflake Intelligence.
2. The question ladder: What → Why → What next → What if → How to.

**Lab 4 — Reason over your own ontology (20 min)** · `labs/lab4_reason_agent/`
1. Run `lab4_01_agent.sql` (from `sql/05`) to create the agent on *your* semantic view.
2. In Snowflake Intelligence, climb the ladder with five preset questions; compare the Festo answer with Lab 0 (it should match).
3. Open the generated SQL for one answer and find the relationships it used.
4. **Break it:** drop the supplier → material relationship (or the decision verified query), re-ask, and watch the answer degrade or change. Restore it.
5. Test the synonym you added in Lab 3 by asking about "Festo".

**Demo — Activate (10 min)**
1. Native App: Ontology tab (entity graph drawn from `DESCRIBE SEMANTIC VIEW`), Ask the Agent, Components/Orders pages with switch, blocked and review decisions (6 min).
2. How it is packaged: SPCS, application package, org listing across three regions (2 min).
3. Closing the loop: share-back to BDC so SAP apps consume the decision (2 min, slide).

**Key takeaway:** The quality of the reasoning is set by the quality of the context.

---

## Break (10 min)

---

## Module 6 — Trust: data quality, observability and validation (20 min)

**Format:** Slides (8 min) + Lab 5 (12 min)

**Slides (4)**
1. **A share is a dependency you don't control:** it can be re-published, re-keyed, truncated or refreshed empty.
2. **The observability kit:** freshness, completeness, baseline, exceptions, task, alert, DMFs at L2 (not attachable to shares; the lab's simulated L0 would allow it, production does not).
3. **The seven field lessons as client conversations;** link back to the Lab 1 profiling findings.
4. **The `LIMIT 0` harness:** compile a whole layer without creating anything; validate the validator.

**Lab 5 — Guard and validate (12 min)** · `labs/lab5_trust/`
1. Run the guard procedure (from `sql/07b`, 11 named checks) and read `GUARD_RESULTS` (4 min).
2. Attach `SNOWFLAKE.CORE.NULL_COUNT` to a key column of one L2 DT; check the schedule and results (4 min).
3. Compile one L2 DT body with its L0 dependencies inlined as CTEs and `LIMIT 0`. Introduce a typo and see it fail at compile time (4 min).

**Key takeaway:** Profile before you promise, flag what you cannot reconcile, and make drift visible before a user finds it.

---

## Module 7 — Design review capstone and wrap-up (15 min)

**Format:** Exercise (10 min) + Slides (5 min)

**Exercise — Design review (10 min)** · `exercises/capstone_scenarios.md`
- Each group draws one of three scenarios: (a) procure-to-pay spend and supplier risk across S/4 plus Ariba-like data; (b) workforce cost across SuccessFactors plus a contractor system; (c) order-to-cash OTIF plus carrier tracking.
- 6 minutes to fill in a one-page canvas: **Access** (data products, lane for non-SAP data) · **Prepare** (L2 tables, TARGET_LAG) · **Define** (entities, relationships, one policy) · **Reason** (the three questions the agent must answer) · **Trust** (three things to profile first).
- 4 minutes: two groups present; peers score against the 5 principles.

**Slides (3)**
1. Recap: core message plus the stack.
2. "What good looks like" checklist (from the medallion PDF).
3. Next steps: keep the lab repo, the sibling patterns (Finance / People / Sales 360), Snowflake docs, and how to request a live BDC sandbox.

**Key takeaway:** A credible design answers, for every layer, what lives there and why.

---

## Deliverables

| # | Deliverable | Location | Format |
|---|---|---|---|
| 1 | Workshop outline (this document) | `workshop/01_workshop_outline.md` | Markdown |
| 2 | **Lab repo:** setup, data, labs 0–5 with solutions, docs, exercises | Staged in `workshop/lab-repo/`; published by the owner to `github.com/snowflakethia/<new-repo>` | Git repo |
| 3 | Partner-safe slide deck (about 45 slides across Modules 0–7) | `workshop/02_slides/` | PPTX |
| 4 | Lab guide (participant) | in lab repo `docs/lab_guide.md` | Markdown |
| 5 | Exercise sheets and capstone canvas | in lab repo `exercises/` | Markdown / PDF |
| 6 | Facilitator notes: talk track, timings, Q&A, pre-delivery checks | `workshop/03_facilitator_notes.md` | Markdown |
| 7 | Module 2 live demo script, prep checklist and backup recording | `workshop/04_demo_assets/` | Markdown + MP4 |
| 8 | Pre-workshop participant email: account signup and setup steps | `workshop/05_participant_prework.md` | Markdown |

## Open items (remaining)

- Final public repo name (setup SQL keeps it in one variable).
- Which data product to share live in Module 2 (suggest Bill of Material, so it ties to the Festo path).
- GA status of the TechUp slide 8 components; live relationship count in the semantic view; current BDC Connect rates.

## Build order (proposed)

1. Lab repo in `workshop/lab-repo/`: export L0 + extension data, parameterised setup and lab SQL, solutions.
2. End-to-end test in a fresh trial account (setup → Lab 5), timing every lab.
3. Lab guide, exercises, feature map, troubleshooting.
4. Partner-safe slide deck.
5. Facilitator notes, Module 2 demo script and prep checklist, participant pre-work email.
6. Dry run, including the live BDC demo and the backup recording.
