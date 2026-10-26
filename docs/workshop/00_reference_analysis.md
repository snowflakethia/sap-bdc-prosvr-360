# Reference Analysis — SAP BDC Connect + Snowflake Workshop (Accenture)

Source folder: `./references` (4 documents) plus the demo repo (`sap-bdc-supply-chain-360`).
Purpose: decide what each document contributes to a 4-hour **technical** hands-on workshop for Accenture consultants, what to reuse, what to fix, and what must not be given to a partner audience.

**Revision 2 changes:** added the SAP BDC Opportunity TechUp deck, which now provides the workshop's storyline (SAP = System of Record; Snowflake = System of Context and Reasoning). The L200 deck is now a minor source: partnership and commercial content has been removed from the workshop.

---

## Summary

| # | Document | Type | Depth | Workshop role | Relevance |
|---|---|---|---|---|---|
| 1 | `SAP_BDC_Opportunity_TechUp_v1.0.pptx` (34 slides, Oct 2026) | Internal Snowflake SE enablement | L200–L300 | **Storyline and positioning** (Module 1); ontology concept (Module 4); reference architecture (Module 3) | **Very high** for slides 4–13, 21; **excluded** for slides 22–33 |
| 2 | `SAP_BDC_Medallion_Architecture_Deep_Dive.pdf` (14 pp.) | Architecture and field guide | L300–L400 | Prepare and Trust layers (Modules 3, 6); cost-aware design | **Very high**; the engineering backbone |
| 3 | `BDC_Connect_Deep_Dive_with_Speaker_Notes.pptx` (16 slides, May 2026) | Technical deep dive with Q&A and accuracy checks | L300 | Access layer (Module 2) | **High**; most current integration source |
| 4 | `SAP and Snowflake - L200 Customer Deck (3).PPTX` (54 slides) | Customer sales deck | L200 | Integration pattern catalogue only (Module 2) | **Low–medium**; mostly partnership / commercial |
| — | Demo repo (`sql/`, `app/`, `docs/`) | Working reference build | L300 | All labs | **Very high** |

How they fit together: **TechUp** gives the *why* (Record vs Context and Reasoning, the ontology argument) and the shape of the stack, **BDC Connect Deep Dive** explains *Access*, the **Medallion PDF** explains *Prepare* and *Trust*, and the **demo** is a working example of all of it. The L200 deck adds only the pattern catalogue.

### Distribution status (important for a partner audience)

| Document | Marking | Can Accenture receive it? |
|---|---|---|
| TechUp | "CONFIDENTIAL – INTERNAL USE ONLY" | **No.** Rebuild the reusable concept slides into a partner-safe deck; never hand out the original |
| L200 Customer Deck | Customer-facing, with internal-only slides and one NDA slide | Selected slides only, with internal and NDA slides removed |
| BDC Connect Deep Dive | No restriction marked; presenter-only notes | Slides yes, after removing the presenter accuracy notes |
| Medallion PDF | No restriction marked; written as a public guide | Yes |

---

## 1. SAP BDC Opportunity TechUp (new — primary storyline)

**What it is.** An internal Snowflake enablement session (about 27 minutes plus Q&A) in three acts: *Why SAP pays* · *SAP records, Snowflake reasons, zero-copy first* · *Make it real*. Act 2 is a technical argument with a live demo of this repo's app.

**Key content, by act.**

| Slides | Content | Use in workshop |
|---|---|---|
| 4–5 | **SAP as System of Record** (an integrated chain that auditors trust) vs **Snowflake as System for Context and Reasoning** (reasons over SAP and non-SAP data; semantics make the reasoning reliable). Snowflake reasons over SAP and never replaces it. | **Module 1 core message** |
| 6 | BDC high-level architecture (Intelligent Apps, Datasphere, BW PCE, Data Product Generator, BDC Connect, SAP- vs customer-managed products) | Module 2 context |
| 8 | **System of Reasoning stack:** Connect (Snowflake-native, metadata connectors, unstructured) → Enrich (Business Ontology, Semantic Views, Cortex Sense, Horizon Catalog) → Activate (CoWork, CoCo, Streamlit, App Runtime, external agents via MCP) | Module 1 frame; check the status of each component |
| 9–11 | **Traditional database access vs ontology-based access** for one question: *"Factory F1 closes. Which orders are at risk, and can C18 replace C17?"* Identity, dependency (transitive part-of) and policy (quality bar = 90 → candidate / blocked / review) as explicit meaning rather than meaning buried in one analyst's SQL | **Module 1 exercise and Module 4 concept** — the best teaching material in the set |
| 12 | Semantics in practice: **1 Access** (BDC Connect → CLD → CSN semantic views in `SNOWFLAKE$`, 0 relationships) → **2 Prepare** (verified IDs, `ENT_*` entity views, recursive BOM SQL, policy evaluation) → **3 Define** (enterprise semantic view `SAP_SUPPLY_CHAIN_360`) → reason | **Becomes the workshop's module structure** |
| 13–19 | Demo run sheet: Scenario → Architecture → Semantic layer → Cortex Analyst → Decision (Festo AG: $1.5M at risk; switch / blocked / review) | Module 0 hook and Module 5 demo |
| 21 | **Zero-copy-first reference architecture** and **5 principles**: Mount, don't move · Publish once, reuse widely · Govern every access · Transform freely, persist selectively · Operate sharing reliably. Three lanes in (zero-copy, batch ELT, streaming), each with its own L0/L1 | **Module 3 opener**; closing checklist |
| 24 | SAP data-sharing fee: formula, "efficiency counts twice", fee stops at L2/L3 | Module 3 (as a technical design driver only) |
| 22–23, 25–33 | GTM Assistant, territory qualification, **internal L0 rebate**, competitor fee objection handling, urgency triggers, sizing, mandate tracks, White-Glove programme, SE call to action | **Exclude.** Snowflake-internal, commercial and not technical |

**Relevance.** Very high. It turns the workshop from a feature tour into an architectural argument that consultants can repeat to clients: *SAP holds the record; Snowflake adds context and reasoning; BDC Connect links them without copying data.* The F1/C17/C18 example lets consultants feel the difference between "SQL encodes meaning" and "the model declares meaning".

**Issues to handle.**
- **Internal-only marking.** Rebuild slides 4–5, 8–12 and 21 in a partner-safe template. Remove internal figures (for example "1,078 APJ customers"), the GTM Assistant, the rebate and the competitor-fee material.
- **Roadmap items.** Slide 8 lists *Business Ontology*, *Cortex Sense* and *metadata connectors*; slide 19 is titled "Business Ontology (Future)". Label every non-GA item and check its status before delivery.
- **Number mismatch.** Slide 12 says `SAP_SUPPLY_CHAIN_360` has "17 entities and 11 relationships"; the repo README says 13 relationships after V2 patches 8–9. Run `DESCRIBE SEMANTIC VIEW` and use the live figure.
- Slide 14 title typo ("Scenration").
- The fee slide cites SAP sources. Keep it, but frame it as a design input and say that rates must be confirmed with SAP.

---

## 2. SAP BDC Medallion Architecture Deep Dive (PDF)

**What it is.** A practitioner guide to turning BDC shares into a medallion overlay, written from real builds.

**Key content.** Catalog sprawl (280–900+ CLDs) · L0 / L1 / L2 overlay · the fee boundary at L2 (0.604 CU per US$ of compute that reads the share, non-SOLEX; TARGET_LAG as a pricing lever) · design rules (business-area grouping, master data as its own area, generate L1 from `INFORMATION_SCHEMA`, `TRY_TO_DATE` with a format mask, no `CURRENT_DATE()` inside dynamic tables, semantic-view mapping is physical-first) · observability kit (freshness, completeness, baseline, DMFs attached at L2) · seven field lessons · `LIMIT 0` validation harness · "What good looks like".

**Relevance.** Very high. It is the detailed engineering content for TechUp principles 4 ("Transform freely, persist selectively") and 5 ("Operate sharing reliably"), and it carries the consulting discipline of *profiling before promising*.

**Issues.** Rates must be confirmed with SAP. Field-lesson figures are magnitudes to measure, not benchmarks. The SOLEX / non-SOLEX distinction stays only as a one-line design caveat; it is no longer a qualification topic.

---

## 3. BDC Connect Deep Dive with Speaker Notes

**What it is.** A 16-slide technical deep dive (May 2026) whose notes contain key points, likely Q&A, and presenter-only accuracy checks.

**Key content.** Zerocopy Connector GA (4 May 2026) · prerequisites (edition, AWS/Azure commercial, same region as BDC Core, ORGADMIN terms) · setup flow (`CREATE ZEROCOPY CONNECTOR ... PARTNER = SAP_BDC` → invitation link → list shares → CLD) · CSN-generated semantic views in `SNOWFLAKE$` · share-back (Iceberg V3, `SYSTEM$SAP_PUBLISH_DATA_PRODUCT`, ORD/CSN) · how BDC builds managed, extended and custom data products · the Snowflake-first example.

**Relevance.** High. It is the source for the *Access* layer (Module 2). Its Q&A blocks become facilitator notes.

**Issues.** Slide 5's visual still says "catalog integration"; slide 12 makes a claim flagged CONTRADICTED; slide 16 lists a "Zero-Copy" menu item flagged NOT FOUND. Fix these or call them out. Remove the presenter accuracy notes before sharing.

---

## 4. SAP and Snowflake — L200 Customer Deck (downgraded)

**What it is.** A customer sales deck about the partnership.

**Revised use.** Only the **integration pattern catalogue** (slides 29–38: managed data products, custom via Datasphere, BW PCE, Snowflake-first, copy to bucket, copy to Kafka) and the connector SQL slide (50) are used, both in Module 2. The partnership, offering (SolEx vs BDC Connect), commercial, Iceberg marketing and AI-vision slides are out of scope for a technical workshop.

**Exclude.** Slides 1–2 (internal), slide 22 (NDA competitive), and any slide with placeholder notes. Slides that duplicate deck 3 are superseded by deck 3.

---

## 5. The demo repo (lab material)

The demo maps directly onto TechUp slide 12, which makes it a good teaching vehicle:

| Stack layer | Demo asset | Snowflake features exercised |
|---|---|---|
| **Access** | L0 `A_*` tables (21 objects, 16 schemas); `sql/00` bootstraps them from the internal listing | Catalog-linked DB (simulated), listings, CSN semantic views (shown in demo) |
| **Prepare** | `sql/03` dynamic tables, `sql/02` serving views, `ENT_*` entity views, `sql/06`/`07a` enrichment | Dynamic Tables, TARGET_LAG, views, recursive SQL |
| **Define** | `sql/04` semantic view `SAP_SUPPLY_CHAIN_360` (relationships, verified queries) | Semantic views, verified queries |
| **Reason** | `sql/05` agent `SAP_SC360_ANALYST_AGENT`; Ask Cortex in the app | Cortex Analyst, Cortex Agents, Snowflake Intelligence, `AI_COMPLETE` |
| **Activate** | Native App `SUPPLY_CHAIN_360_APP` (React + Express on SPCS), org listing | Native Apps, SPCS, listings |
| **Trust** | `sql/07b` guard (11 named checks) | Procedures, guard tables; DMFs to be added in the lab |

**Gaps to teach from rather than hide:** no L1 business-area layer · `TARGET_LAG = DOWNSTREAM` means no scheduled refresh · data is synthetic and fixed (Jan–Sep 2025) · the semantic view is hand-authored, not generated from CSN · a live connector needs a real BDC tenant, so it can only be an instructor demo.

---

### Lab portability (revision 3)

Participants have no SAP access and only Snowflake, and lab material must come from GitHub. Assessment of the demo against that:

| Demo dependency | Portable as-is? | Action for the lab repo |
|---|---|---|
| L0 from internal listing `ORGDATACLOUD$INTERNAL$SAP_BDC_SUPPLY_CHAIN_360` (`sql/00`) | No — org-internal | Export the 21 objects (398 rows) to files; load with `COPY INTO` from the Git repo stage; make the database read-only to mimic a CLD |
| `tools/gen_ops_ext.py` (local Python) | No — needs local tooling | Ship pre-generated OPS_EXT output as files |
| `sql/02`–`07b` (hard-coded `SAP_SUPPLY_CHAIN`, ACCOUNTADMIN) | Mostly | Parameterise database names; split into per-lab files with solutions |
| CSN semantic views in `SNOWFLAKE$` | No — need a real CLD | Ship one simulated "CSN-style" semantic view with 0 relationships for contrast |
| Native App, SPCS, Docker build, org listing | No — heavy, account-specific | Instructor demo only |
| Repo itself (`snowflakethia/...`, private, contains presales/internal material) | No | New curated public lab repo |

## Recommendations for the workshop build

1. Structure the workshop on **TechUp slide 12's stack** (Access → Prepare → Define → Reason → Activate, with Trust across all layers), framed by **System of Record vs System of Context and Reasoning**.
2. Rebuild the TechUp concept slides in a **partner-safe deck**; do not distribute the original TechUp or L200 decks.
3. Use the PDF's L0/L1/L2 naming throughout.
4. Introduce each Snowflake feature **in the layer where it is used** (see the outline's feature map), not as a separate feature catalogue.
5. Before delivery, verify: GA status of every slide-8 component, the live relationship count, connector features, Snowsight labels, and BDC Connect rates.
6. Provision lab accounts with L0 pre-loaded (`sql/00`) and give each participant a pre-built "finished" schema for the Module 0 hook.
