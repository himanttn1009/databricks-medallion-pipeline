# Task Breakdown

Incremental implementation plan for Cursor-assisted development.

## Phase 0: Foundation

- [x] Resolve engineering decisions (assignment ambiguities)
- [x] Complete requirements-analysis.md
- [x] Complete design-notes.md, data-model.md, data-quality-strategy.md
- [x] Finalize spec.md

## Phase 1: Data Generation

- [x] Implement generate_sample_data.py
- [x] Generate and validate CSVs in data/
- [x] Document in DATA_GENERATION_NOTES.md

## Phase 2: Bronze

- [x] Implement per-source ingest scripts
- [x] Implement ingest_all.py
- [x] Verify raw ingestion and metadata logging
- [x] Runtime validation in Databricks

## Phase 3: Silver

- [x] Implement quality checks (5 categories including type validation)
- [x] Implement create_silver_tables.py
- [x] Quality metrics report (silver.dq_metrics)
- [x] Runtime validation in Databricks
- [x] Data quality automated tests (manual runtime validation complete; pytest not implemented)

## Phase 4: Gold

- [x] Implement aggregation scripts (PySpark)
- [x] Implement create_gold_tables.py
- [x] Validate aggregation calculations (runtime)
- [x] Update ai-prompts/07-gold-layer.md with runtime interaction

## Phase 5: Dashboard

- [x] Write dashboard_queries.sql
- [x] Configure Databricks SQL Dashboard (manual UI)
- [x] Complete DASHBOARD_GUIDE.md
- [x] Runtime dashboard validation

## Phase 6: Testing & Documentation

- [ ] Integration tests (pytest)
- [x] README end-to-end setup
- [x] AI workflow and reflection artifacts
- [ ] Submission preparation (git commit/push + online form)

## Remaining Optional Items

- Automated test suite (`tests/`)
- Gold runtime validation entry in `ai-prompts/07-gold-layer.md`
- Personalize `candidate-info.md` (name, dates)
- Online submission form answers
