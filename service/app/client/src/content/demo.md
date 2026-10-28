## What SAP alone cannot answer

| Epic | The question | Why it needs Snowflake |
|---|---|---|
| Operational Excellence | Which fixed-price project is losing money, why, and which asset would have saved it? | S/4HANA holds the costs; the reasons live in PM notes and the asset library, joined by meaning (embeddings) |
| Value Creation | Which bids will we win, and who on the bench would raise the odds? | CRM holds the bids; skills and roll-offs live in People Intelligence |
| People Development | Is the time mix right, who is about to leave, and did AI learning make anyone faster? | Time, skills, AI telemetry and performance in one model, with a statistical test |
| ProServe360 | What should the MD do first? | One governed semantic layer across all of it, answered by the Advisor |

## Real and simulated data

- **Real (BDC catalog-linked databases, zero copy):** S/4HANA cost centres, profit centres, GL accounts, fiscal
  calendar, journal entries, projects / WBS, and the **People Intelligence** products Core Workforce, Employee
  Availability, Planned Working Time and Assignment information.
- **Simulated (shaped like the SAP data products not yet shared):** timesheets, CRM, skills and learning,
  performance, compensation, the asset library and AI-tool telemetry.
- Every row carries `SOURCE_SYSTEM` (`BDC_CLD` or `SIMULATED`); swapping a simulated source for a real product is
  a one-line change in the L1 map.

## What goes back to SAP

| Pillar | Published back |
|---|---|
| Operational Excellence | Project risk flags and estimate-at-completion for S/4HANA project controlling |
| Value Creation | Win probability and suggested bench additions for the CRM opportunity |
| People Development | Attrition-risk and AI-skill-gap lists for SuccessFactors talent processes |
