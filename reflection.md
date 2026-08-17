# Reflection

## What I Built

An end-to-end Databricks Medallion pipeline for synthetic e-commerce data:

- **Data generation** — Python script producing three CSVs with ~460 intentional quality defects.
- **Bronze** — Raw CSV ingestion into Delta tables with audit logging; defects preserved.
- **Silver** — Five DQ check categories, row-level flags, and 10 aggregate metrics per run.
- **Gold** — Four business aggregation tables for analytics consumption.
- **Dashboard** — Nine Gold-only SQL queries and a manually configured Databricks SQL Dashboard with KPIs, required visualizations, filters, and customer detail table.

The pipeline follows medallion layer boundaries: each layer reads only from the layer above; the dashboard reads Gold only.

## How I Used AI (Across the Lifecycle)

Cursor was the primary AI tool, used with persistent project rules (`.cursor/rules/project-engineering.mdc`) and structured prompts per layer. The workflow alternated between **design-only** interactions (specifications, ambiguities, acceptance criteria) and **implementation** interactions (code, SQL, documentation). Prompt history is captured in `ai-prompts/` with explicit accept/reject reasoning.

AI assisted with requirements structuring, architecture decisions, PySpark/SQL code generation, static review, and documentation — but runtime validation was always performed manually in Databricks before claiming success.

## What AI Helped With Most

- **Rapid scaffolding** — Modular layer structure (`config.py`, utilities, numbered scripts, orchestrators) generated consistently.
- **Design specification depth** — DQ rules, Gold aggregation logic, dashboard widget inventory with filter-to-query mapping.
- **Cross-document consistency** — Keeping `data-model.md`, `design-notes.md`, and layer READMEs aligned.
- **Constraint enforcement** — Prompts with explicit DO NOT lists prevented cross-layer modifications.

## What AI Got Wrong

- **Over-optimistic status** — Early READMEs and layer docs sometimes said "runtime not performed" when validation had since completed; required manual status sync.
- **Dashboard UI assumptions** — AI cannot configure Databricks Dashboard widgets; Counter defaults, filter defaults, and pie chart mapping required manual fixes.
- **Template file proliferation** — Empty `ai-prompts/` stubs were created alongside numbered history files; had to be cleaned up.
- **Transcript gaps** — Some interaction response bodies were not fully recoverable from Cursor transcripts; summaries based on artifacts instead.

## How I Validated AI Output

- Design specs reviewed before any implementation code.
- Static checks: file presence, Gold-only SQL grep, Spark Connect API restrictions.
- Local generator validation before CSV write.
- Databricks execution with observed row counts and DQ metrics.
- Dashboard KPI baseline cross-checked against Gold tables (e.g., Customer Count 9.94K = 9,940 rows).

## What I Would Improve Next

- **Automated tests** — `pytest` suite for Silver DQ logic and Gold aggregations (planned in `design-notes.md` but not implemented).
- **Dashboard-as-code** — Terraform or Databricks Asset Bundles for reproducible dashboard deployment.
- **CI validation** — Static checks and unit tests in GitHub Actions before Databricks runs.
- **Prompt file naming** — Consolidated to numbered `04–08` files; removed duplicate symlink copies.

## Reusable Workflow

1. Load assignment + design docs into AI context.
2. Design-only interaction → human review → persist to `design-notes.md`.
3. Implementation interaction with strict scope (one layer, no upstream changes).
4. Static verification → Databricks runtime → update README status.
5. Record interaction in `ai-prompts/` with validation evidence.
6. Document issues in `debugging-notes.md` regardless of AI vs manual resolution.

This pattern scales to production pipelines where AI accelerates scaffolding but human validation remains the gate for merge and deploy.
