# AI Workflow Foundation (Part A)

## Primary AI Tool Used

**Cursor** — IDE-integrated AI assistant with project rules, codebase context, and agent mode for multi-file implementation.

## How I Provide Project Context to the Tool

- **Persistent rules:** `.cursor/rules/project-engineering.mdc` defines medallion boundaries, DQ principles, and workflow.
- **Assignment anchor:** `assignment/assignment-requirements.md` referenced at the start of each layer interaction.
- **Design artifacts:** `requirements-analysis.md`, `design-notes.md`, `data-model.md`, `data-quality-strategy.md` loaded or cited before design/implementation prompts.
- **Layer READMEs:** Prior layer docs inform downstream work (e.g., Bronze runtime lessons → Silver Spark Connect constraints).
- **Explicit constraints in prompts:** Each interaction states what to modify, what to skip, and whether design-only vs implementation.

## How I Use AI for Requirement Analysis

- Initial pass: assignment doc → structured `requirements-analysis.md` with ambiguities, acceptance criteria, and open decisions.
- AI helps extract mandatory vs optional deliverables, map assignment sections to repo structure, and flag contradictions (e.g., Gold table count, fourth DQ check type).
- Human review accepts/rejects AI interpretations; unresolved items documented explicitly rather than silently assumed.

## How I Use AI for Pipeline Design (Bronze/Silver/Gold — Medallion Architecture)

- **Design-only interactions first:** Each layer started with a design-only prompt — no code until spec approved.
- AI produced layer specifications: read/write contracts, schemas, DQ rules, aggregation logic, dashboard widget inventory.
- Decisions recorded with IDs (SD-01, GD-07, DD-01, etc.) and persisted to `design-notes.md` and `data-model.md`.
- Layer boundaries enforced: Bronze raw, Silver validates, Gold aggregates, Dashboard reads Gold only.

## How I Use AI for Code Generation (Python/PySpark/SQL)

- Implementation prompts reference finalized design docs and forbid upstream layer changes.
- AI generates modular scripts per layer (`config.py`, utilities, numbered scripts, orchestrator).
- SQL dashboard queries generated in `dashboard_queries.sql` with parameter documentation.
- Incremental scope: one layer per interaction; static verification before claiming runtime success.

## How I Validate AI-Generated Code and Logic

- **Static review:** File presence, import patterns, Spark Connect compatibility, forbidden API checks.
- **Design alignment:** Compare implementation against design spec and assignment acceptance criteria.
- **No false runtime claims:** AI interactions explicitly state when Databricks execution was not performed.
- **Manual Databricks validation:** Pipeline run layer-by-layer; row counts and DQ metrics compared to expected values.
- **Dashboard UI:** Manual widget/filter testing against Gold baseline KPIs.

## How I Use AI for Testing and Validation

- Data generator includes `validate_generated_data()` pre-write checks.
- Independent CSV validation after generation (row counts, defect counts).
- Silver runtime: 10 `dq_metrics` rows per run; threshold MET/NOT MET interpretation.
- Gold runtime: four table row counts and dashboard KPI cross-check.
- Automated `pytest` suite planned but not implemented — manual validation documented in layer READMEs.

## How I Use AI for Debugging (Issues, Root Causes)

- Bronze static code review surfaced orchestrator and column-order issues before runtime.
- Silver NULL-key uniqueness fix applied after static review.
- Dashboard issues (Counter defaults, filter defaults, pie chart config) resolved manually in Databricks UI and documented in `debugging-notes.md` and `ai-prompts/08-dashboard-layer.md`.
- AI used for root-cause analysis of design ambiguities; runtime UI fixes were manual.

## How I Use AI for Data Quality Checks

- Silver DQ design: five check categories, canonical failure code order, `is_valid` semantics.
- AI helped map intentional generator defects to specific check scripts and threshold expectations.
- `silver.dq_metrics` grain: one row per `(run_id, entity, check_name)` — 10 rows per run.
- Dashboard does not re-run DQ; consumes Gold aggregates only.

## What Information I Avoid Sharing Unnecessarily with AI Tools

- No real customer PII, credentials, API keys, or production secrets.
- Databricks workspace URLs and personal tokens not embedded in repo.
- Synthetic data only; generator uses Faker with fixed seeds for reproducibility.

## How I Would Reuse This Workflow in a Real Production Pipeline

1. **Rules + spec first** — Cursor rules and design docs as persistent context.
2. **Design before code** — Layer-by-layer design interactions with explicit acceptance criteria.
3. **Constrained implementation prompts** — Scope limits prevent cross-layer drift.
4. **Static then runtime validation** — Never claim success without observed metrics.
5. **Prompt history** — `ai-prompts/` captures accept/reject reasoning for auditability.
6. **Manual CE gaps** — Document manual steps (dashboard UI) where automation is out of scope.

## Lessons Learned

### What Worked

- Design-only interactions prevented rework across Bronze → Dashboard.
- Explicit DO NOT lists in prompts kept layer boundaries clean.
- Numbered decision IDs (SD-, GD-, DD-) made traceability easy across docs.
- Fail-fast orchestration and fixed `REFERENCE_DATE` improved reproducibility.
- Gold-only dashboard contract simplified consumption layer.

### What Didn't

- Empty `ai-prompts/` template files created noise — removed; content kept in numbered history files.
- Initial dashboard README lagged behind manual UI completion — needed explicit status sync.
- Automated tests deferred — manual validation sufficient for assessment but not for production.
- Some AI prompt history transcripts partially redacted — summaries based on artifacts and observed results.
