# AI Prompts — Bronze Layer

## Objective

Design the Bronze layer for ingesting generated e-commerce CSV sources into Databricks Delta tables — raw landing only, with no Silver transformations.

**Stage status (as of this document):**

| Phase | Status |
|-------|--------|
| Design | Complete — Bronze Layer Design Specification produced (Interaction 1) |
| Implementation | Complete — Bronze layer code implemented (Interaction 2) |
| Static code review | Complete — senior-level static review performed (Interaction 3) |
| Review fixes | Complete — fail-fast orchestration and column-order validation (Interaction 4) |
| Runtime validation | **Not performed** |

---

## Interaction 1 — Bronze Design

### Objective

Design the Bronze layer for the e-commerce Medallion Architecture: ingest `customers.csv`, `products.csv`, and `orders.csv` into Databricks as Bronze Delta tables while preserving intentional source defects for Silver validation. No implementation code.

### Exact Prompt Sent

```
We are now starting the Bronze Layer of the Databricks Medallion Pipeline.

Review the following project context before designing anything:

@assignment/assignment-requirements.md
@requirements-analysis.md
@data-model.md
@data-quality-strategy.md
@design-notes.md
@src/data_generation/DATA_GENERATION_NOTES.md
@.cursor/rules/project-engineering.mdc

Also inspect the generated source files:

@data/customers.csv
@data/products.csv
@data/orders.csv

## Objective

Design the Bronze layer for the e-commerce Medallion Architecture.

The Bronze layer must ingest the three generated CSV source files:

1. customers.csv
2. products.csv
3. orders.csv

into Databricks as Bronze Delta tables.

## Assignment requirements

The Bronze layer must:

- ingest all three CSV sources
- preserve source data as raw as practical
- handle CSV schema and data types appropriately
- explicitly handle empty CSV fields as NULL
- add ingestion metadata
- capture ingestion timestamp
- capture source file information
- validate expected row counts
- provide meaningful error handling
- create persistent Bronze tables
- be reproducible and easy to rerun

Expected source row counts:

customers = 10,000
products = 500
orders = 100,000

## Important architectural constraint

Do not perform Silver transformations in Bronze.

Bronze should not:
- remove bad records
- deduplicate records
- fix NULLs
- repair foreign keys
- apply business aggregations
- calculate Silver quality status

Those responsibilities belong to Silver.

## Source quality

The generated CSVs intentionally contain the exact defects required by the assignment.

Bronze must preserve those defects because Silver is responsible for detecting and flagging them.

Therefore:

- NULL values must remain NULL
- duplicate records must remain present
- orphan foreign keys must remain present
- Bronze must not silently filter bad records

## Design questions

Before implementation, explain:

1. Recommended Databricks storage location for the CSV inputs
2. Whether to use DBFS, Databricks Volumes, or another appropriate approach for this assignment environment
3. Bronze table naming convention
4. Whether to use explicit schemas or schema inference, and why
5. How empty CSV fields will become Spark NULL values
6. How dates and decimal fields should be represented
7. Which ingestion metadata columns should be added
8. How source filename/path should be captured
9. How ingestion timestamp should be captured
10. How row-count validation should work
11. How rerunning the ingestion should behave
12. How errors should be handled
13. How the three datasets should be ingested
14. Whether ingestion should be implemented as separate notebooks/scripts or one orchestrator
15. How the design remains compatible with the later Silver layer

## Expected output

Do NOT write implementation code yet.

Produce a Bronze Layer Design Specification containing:

- architecture
- storage approach
- table names
- schemas
- ingestion strategy
- metadata strategy
- NULL handling strategy
- validation strategy
- rerun/idempotency strategy
- error handling
- assumptions
- edge cases
- recommended implementation structure

Also identify any ambiguity in the assignment that requires an explicit engineering decision.

Do not modify project files yet.
```

### AI Response Summary

Cursor produced a **Bronze Layer Design Specification** (design-only; no code; no file changes). Summary:

**Architecture:** `data/*.csv` → upload to DBFS landing → PySpark Bronze ingestion (`01_ingest_customers.py`, `02_ingest_orders.py`, `03_ingest_products.py`, `ingest_all.py`) → Delta tables `bronze.customers`, `bronze.products`, `bronze.orders` + append-only `audit.ingestion_log` → Silver reads Bronze unchanged.

**Storage:** Default landing path `dbfs:/FileStore/medallion_pipeline/data/` (configurable). **DBFS** recommended for assessment; Unity Catalog Volumes and S3 documented as alternatives. No claim that Community Edition availability is guaranteed.

**Tables:** `bronze.customers`, `bronze.products`, `bronze.orders` — Delta Lake, schema `bronze`, no partitioning, **overwrite** per full refresh run.

**Schemas:** **Explicit `StructType`** per entity (not `inferSchema=True`). Business types: `IntegerType`, `StringType`, `DateType`, `DecimalType(18,2)` as appropriate; nullable business columns to preserve defects. **Explicit CSV header validation** required (StructType alone does not reject extra/missing columns).

**NULL contract:** `nullValue=""` on CSV read; `Python None → empty CSV field → Spark NULL → Delta NULL`; no coalesce to empty strings or sentinel values.

**Metadata:** Row-level `_ingest_timestamp`, `_source_file`, `_ingest_batch_id`; run-level `audit.ingestion_log` (simple append design).

**DQ preservation:** All intentional defects must survive Bronze (50 NULL emails, 10 duplicate customer rows, 100/200 NULL FKs, 50/30 orphans, 20 duplicate order rows — 460 total). Bronze does not validate defect counts.

**Validation (Bronze only):** Source exists; header/schema match; row counts 10,000 / 500 / 100,000 (fatal on mismatch); malformed CSV fatal; post-write count check. No Silver DQ checks in Bronze.

**Error handling:** Fatal — missing source, schema/header mismatch, parse errors, row-count mismatch, Delta write failure. Non-fatal — NULLs, duplicates, orphan FKs (ingest unchanged).

**Implementation structure:** `src/bronze/config.py`, `schemas.py`, `ingest_utils.py`, three entity ingest scripts, `ingest_all.py`.

**Ambiguities resolved:** Explicit schema vs inference; DBFS vs Volumes; overwrite vs append; row-count mismatch fail vs warn; configured path vs `input_file_name()` for `_source_file`; ingest order; no Bronze defect-count validation.

**CSV inspection noted:** Empty fields observed for NULL email, NULL FKs, and empty `payment_date` on Cancelled orders; quoted commas in product names handled by standard CSV reader.

### Key Decisions

| Decision | Outcome |
|----------|---------|
| Landing zone | DBFS (`dbfs:/FileStore/medallion_pipeline/data/`), paths configurable |
| Table format | Delta Lake in schema `bronze` |
| Schema approach | Explicit Spark schemas + explicit header validation |
| NULL handling | `nullValue=""`; no NULL repair |
| Metadata | `_ingest_timestamp`, `_source_file`, `_ingest_batch_id` + `audit.ingestion_log` |
| Write mode | Overwrite per table (idempotent full refresh) |
| Ingestion layout | Separate entity scripts + `ingest_all.py` orchestrator |
| Layer boundary | Bronze ingests only; Silver owns all DQ |
| Row-count validation | Fatal mismatch at 10,000 / 500 / 100,000 |
| Defect preservation | All 460 explicit defect-participating rows must reach Silver |

### Accepted

- Assignment Bronze requirements (ingest three CSVs, metadata, row counts, raw fidelity, rerun).
- Architectural constraint: no Silver work in Bronze (no dedup, NULL repair, FK validation, filtering, quality flags, aggregations).
- Source quality rules: preserve NULLs, duplicates, and orphan FKs.
- Design-only deliverable; no implementation code in this interaction.
- Prompt instruction: do not modify project files yet.

### Rejected

- `inferSchema=True` as the sole typing strategy.
- Bronze-level data quality checks or defect-count validation.
- Filtering, deduplicating, or repairing intentional bad records at ingest.
- Append-only Bronze tables for assessment full-refresh workflow.
- Production infrastructure beyond simple audit logging (streaming, complex observability).

### Reasoning

Bronze must land source data faithfully so Silver can detect the exact intentional defect populations validated in `DATA_GENERATION_NOTES.md`. Explicit schemas and fatal structural validation catch infrastructure errors early; row-level DQ failures are the purpose of the Silver layer. DBFS with configurable paths minimizes assessment setup friction while documenting production alternatives.

### Files Changed

**None.** The prompt explicitly required design only and stated: *"Do not modify project files yet."*

No repository files were created or updated during this interaction.

### Validation Status

| Type | Status |
|------|--------|
| Design | Complete — Bronze Layer Design Specification delivered in chat |
| Implementation | **Not started** — no `src/bronze/` ingest code written |
| Runtime validation | **Not performed** — no Databricks execution, no Bronze table loads verified |

Implementation followed in Interaction 2.

---

## Interaction 2 — Bronze Implementation

### Objective

Implement the Bronze layer for the e-commerce Medallion pipeline using PySpark and Delta.

### Exact Prompt Sent

```
Implement the Bronze Layer based on the approved design.

Review all relevant project context first:

@assignment/assignment-requirements.md
@requirements-analysis.md
@data-model.md
@data-quality-strategy.md
@design-notes.md
@src/data_generation/DATA_GENERATION_NOTES.md
@src/data_generation/generate_sample_data.py
@.cursor/rules/project-engineering.mdc

Source files:

@data/customers.csv
@data/products.csv
@data/orders.csv

## Objective

Implement a working PySpark Bronze ingestion layer for the three generated CSV files.

Create:

src/bronze/

├── README.md
├── config.py
├── schemas.py
├── ingest_utils.py
├── 01_ingest_customers.py
├── 02_ingest_orders.py
├── 03_ingest_products.py
└── ingest_all.py

## Requirements

### 1. Configuration

Create config.py containing centralized configuration for:

- DBFS input base path
- entity-specific input paths
- Bronze schema name
- audit schema name
- Bronze table names
- expected row counts
- relevant CSV options

Do not hard-code the same path/table/count values in multiple files.

The DBFS input base path should be configurable.

Default:

dbfs:/FileStore/medallion_pipeline/data/

### 2. Explicit schemas

Create schemas.py containing explicit PySpark StructType schemas for:

customers
products
orders

Use the approved data model.

Use:

IntegerType for IDs and integer quantities
StringType for strings
DateType for dates
DecimalType(18,2) for monetary columns

Business columns must remain nullable in Bronze.

### 3. CSV ingestion

Implement shared ingestion logic in ingest_utils.py.

The reader must:

- header = true
- explicit schema
- empty CSV fields → Spark NULL
- date format = yyyy-MM-dd
- strict malformed-record handling
- standard CSV quoting
- no inferSchema

Do not transform business values beyond required CSV parsing/type conversion.

### 4. Header/schema validation

Explicitly validate the CSV header before reading the data.

The validation must detect:

- missing required columns
- unexpected extra columns

Fail clearly if the header does not match the expected schema.

Do not assume StructType alone performs this validation.

### 5. Metadata

Add these columns to every Bronze row:

_ingest_timestamp
_source_file
_ingest_batch_id

Generate one batch ID for the complete pipeline run.

Use one ingestion timestamp per entity ingestion.

Use the configured source path as _source_file.

Do not modify source business columns.

### 6. Row-count validation

Validate:

customers = 10,000
products = 500
orders = 100,000

Row-count mismatch must be fatal.

Perform validation before writing the corresponding Bronze table.

Also perform a lightweight post-write row-count verification.

### 7. Bronze tables

Create the Bronze schema if required.

Write Delta tables:

bronze.customers
bronze.products
bronze.orders

Use overwrite for the assessment's full-refresh workflow.

Do NOT partition these tables.

### 8. Audit table

Create:

audit.ingestion_log

Keep this implementation simple.

At minimum capture:

- run_id
- layer
- entity
- status
- row_count
- source_path
- target_table
- message
- run_timestamp

Write one audit record per entity ingestion.

Use append mode for audit history.

Do not store secrets or sensitive information in error messages.

### 9. Defect preservation

This is critical.

Bronze MUST preserve all source defects.

Do NOT:

- dropDuplicates
- filter NULL records
- repair NULLs
- repair foreign keys
- remove orphan records
- remove duplicate IDs
- calculate quality flags
- join against parent tables
- perform business aggregations

The following must survive Bronze and be available for Silver:

- 50 NULL customer emails
- 10 duplicate customer_id participant rows
- 100 NULL order customer_id
- 200 NULL order product_id
- 50 orphan customer_id
- 30 orphan product_id
- 20 duplicate order_id participant rows

### 10. Entity scripts

Create:

01_ingest_customers.py
02_ingest_orders.py
03_ingest_products.py

Each should be a thin entity-specific entry point that uses the shared ingestion utilities.

Do not duplicate ingestion logic unnecessarily.

### 11. Orchestrator

Create:

ingest_all.py

It should:

1. create/reuse Spark session
2. generate one batch ID
3. ingest customers
4. ingest orders
5. ingest products
6. collect results
7. fail the pipeline if an entity fails
8. provide a concise final summary

The orchestrator should not duplicate the shared ingestion logic.

### 12. Error handling

Handle at least:

- missing source file
- empty source file
- header mismatch
- malformed CSV
- row-count mismatch
- Delta write failure

Errors must include useful context:

- entity
- source path
- target table
- expected vs actual count where applicable

Do not expose secrets.

### 13. Rerun behavior

The Bronze layer must be idempotent for this assessment.

Running the same source data again should replace the Bronze tables rather than duplicate rows.

Audit records should remain historical.

### 14. Documentation

Create/update:

src/bronze/README.md

Document:

- prerequisites
- DBFS upload process
- expected source paths
- how to run individual entity ingestion
- how to run ingest_all.py
- Bronze table names
- audit table
- expected row counts
- rerun behavior
- important limitation that Bronze does not perform data-quality cleaning

### 15. Code quality

Follow the project engineering rules.

Use:

- clear function names
- type hints where appropriate
- meaningful docstrings
- constants/configuration instead of magic numbers
- small reusable functions
- useful error messages
- no unnecessary framework or abstraction

Do not over-engineer this assessment.

## Important Databricks compatibility requirement

Before choosing APIs that depend on a specific Databricks runtime, inspect the existing project documentation/context.

Keep the implementation compatible with a normal PySpark + Delta Databricks environment.

Do not introduce external dependencies unless absolutely necessary.

## Important implementation constraint

Do not modify:

- Silver
- Gold
- Dashboard
- generated CSV data
- data-generation code

Only create/update files required for Bronze implementation and Bronze documentation.

After implementation:

1. list all files created/modified
2. summarize the architecture implemented
3. explain how NULLs are handled
4. explain how defects are preserved
5. explain how row counts are validated
6. explain how reruns behave
7. provide the exact commands/notebook steps needed to execute Bronze in Databricks

Do NOT claim runtime success.

Do NOT execute Databricks code unless the environment is actually available.
```

### AI Response Summary

Cursor implemented the full Bronze layer under `src/bronze/` per the approved Interaction 1 design and the detailed implementation prompt. No Silver, Gold, Dashboard, CSV, or data-generation files were modified.

**Files created:**

| File | Purpose |
|------|---------|
| `config.py` | Centralized paths, schema/table names, expected row counts, CSV reader options |
| `schemas.py` | Explicit `StructType` schemas for customers, products, orders, and audit log |
| `ingest_utils.py` | Shared ingestion pipeline (validation, read, metadata, write, audit) |
| `01_ingest_customers.py` | Thin entry point for `customers.csv` |
| `02_ingest_orders.py` | Thin entry point for `orders.csv` |
| `03_ingest_products.py` | Thin entry point for `products.csv` |
| `ingest_all.py` | Orchestrator for customers → orders → products |
| `README.md` | Operational documentation (replaced placeholder) |

**Bronze architecture:**

```
config.py + schemas.py
        ↓
ingest_utils.py (shared pipeline)
        ↓
01/02/03_*.py (entity entry points)  or  ingest_all.py (orchestrator)
        ↓
bronze.customers | bronze.products | bronze.orders  (Delta, overwrite)
        ↓
audit.ingestion_log  (Delta, append)
```

**CSV ingestion approach:** Shared `read_csv_with_schema()` in `ingest_utils.py` uses Spark CSV reader with centralized options from `config.py`: `header=true`, explicit schema (no `inferSchema`), `nullValue=""`, `dateFormat=yyyy-MM-dd`, `mode=FAILFAST`, standard quoting/escape. Business values are not transformed beyond CSV parsing and type conversion.

**Explicit schemas:** `schemas.py` defines nullable business `StructType` per entity using `IntegerType`, `StringType`, `DateType`, and `DecimalType(18,2)` per the approved data model. Metadata and audit schemas are defined separately.

**NULL handling:** Empty CSV fields map to Spark `NULL` via `nullValue=""`. Business columns are nullable in schema. No `coalesce`, default fills, or imputation.

**Metadata columns:** Every Bronze row receives `_ingest_timestamp`, `_source_file` (configured DBFS path), and `_ingest_batch_id`. `ingest_all.py` shares one `batch_id` per pipeline run; each entity gets its own ingestion timestamp. Standalone entity scripts generate their own `batch_id` when run individually.

**Header validation:** `validate_csv_header()` compares actual CSV header columns (read via `limit(0)` peek) against expected business columns from `schemas.py`. Detects missing and extra columns; raises `BronzeIngestionError` on mismatch.

**Row-count validation:** Pre-write `count()` compared against `EXPECTED_ROW_COUNTS` in `config.py` (10,000 / 500 / 100,000). Fatal on mismatch with entity, source path, target table, and expected vs actual in the error message. Post-write verification via `spark.table(target_table).count()`.

**Delta table creation:** `ensure_schemas_exist()` creates `bronze` and `audit` schemas. `write_bronze_table()` writes Delta with `mode("overwrite")` and `overwriteSchema=true`; tables are not partitioned.

**Audit logging:** `write_audit_record()` appends one record per entity ingestion to `audit.ingestion_log` with `run_id`, `layer`, `entity`, `status`, `row_count`, `source_path`, `target_table`, `message`, `run_timestamp`. Success and failure paths both write audit records.

**Error handling:** `BronzeIngestionError` raised for missing source, empty/header-only source, header mismatch, row-count mismatch, and Delta write failure. Malformed CSV handled via `FAILFAST`. Generic exceptions wrapped with entity, source path, and target table context. No secrets in error messages.

**Rerun behavior:** Bronze tables use Delta overwrite (idempotent full refresh). Audit log uses append mode (historical runs preserved).

Static Python syntax check (`py_compile` / `ast.parse`) passed locally. Runtime execution in Databricks was not performed.

### Key Decisions

| Decision | Outcome |
|----------|---------|
| Schema approach | Explicit `StructType` in `schemas.py`; no `inferSchema` |
| NULL handling | `nullValue=""` on CSV read; nullable business columns; no repair |
| Defect preservation | No dedup, filter, FK repair, quality flags, or joins in Bronze |
| Bronze write mode | Delta `overwrite` per table (full-refresh idempotency) |
| Audit write mode | Delta `append` to `audit.ingestion_log` |
| Input paths | Configurable DBFS base via `MEDALLION_DBFS_INPUT_BASE` env var; default `dbfs:/FileStore/medallion_pipeline/data` |
| Code layout | Shared `ingest_utils.py` + thin entity scripts + `ingest_all.py` orchestrator |
| Header validation | Explicit pre-read header check (not relying on StructType alone) |
| Orchestrator order | customers → orders → products |
| Path existence check | Hadoop `FileSystem.exists()` via Spark JVM (DBFS-compatible) |
| Audit `row_count` type | `LongType` in audit schema (aligned with data model BIGINT) |

### Accepted

- Approved Bronze design from Interaction 1 (DBFS landing, explicit schemas, metadata columns, row-count validation, defect preservation, overwrite Bronze / append audit).
- All 15 implementation requirements from the prompt (configuration, schemas, CSV ingestion, header validation, metadata, row counts, Delta tables, audit log, defect preservation, entity scripts, orchestrator, error handling, rerun behavior, README, code quality).
- Constraint to modify only Bronze implementation and Bronze documentation files.
- Constraint not to claim runtime success without Databricks execution.
- PySpark + Delta only; no additional external dependencies.

### Rejected

No implementation decisions were explicitly rejected during this interaction.

### Reasoning

The implementation follows the approved Interaction 1 design: Bronze lands raw source data faithfully so Silver can detect the exact intentional defect populations. Explicit schemas and fatal structural validation catch infrastructure and format errors early; row-level DQ failures remain Silver's responsibility. Centralized `config.py` avoids duplicated magic numbers and paths. Shared `ingest_utils.py` keeps entity scripts thin and the orchestrator free of duplicated logic. Delta overwrite on Bronze tables supports idempotent assessment reruns; append-only audit preserves run history. `nullValue=""` with nullable schemas ensures empty CSV fields become Spark NULL without repair. No deduplication, filtering, or FK validation in Bronze preserves all 460 defect-participating rows for Silver.

### Files Changed

Exactly the following files were created or modified during this interaction:

- `src/bronze/config.py`
- `src/bronze/schemas.py`
- `src/bronze/ingest_utils.py`
- `src/bronze/01_ingest_customers.py`
- `src/bronze/02_ingest_orders.py`
- `src/bronze/03_ingest_products.py`
- `src/bronze/ingest_all.py`
- `src/bronze/README.md`

### Validation Status

| Type | Status |
|------|--------|
| Static implementation | Complete — all Bronze modules created; local Python syntax check passed |
| Runtime execution | **Not performed** |
| Databricks runtime validation | **Not performed** |
| Bronze runtime success | **Must not be claimed** — no CSV ingest or Delta table load verified in Databricks |

---

## Interaction 3 — Bronze Static Code Review

### Objective

Perform a senior-level static review of the Bronze implementation against the assignment, approved design, data model, data quality strategy, and project engineering rules.

### Exact Prompt Sent

```
Perform a static senior-level code review of the Bronze implementation.

Review:

@src/bronze/config.py
@src/bronze/schemas.py
@src/bronze/ingest_utils.py
@src/bronze/01_ingest_customers.py
@src/bronze/02_ingest_orders.py
@src/bronze/03_ingest_products.py
@src/bronze/ingest_all.py
@src/bronze/README.md

Also review against:

@assignment/assignment-requirements.md
@requirements-analysis.md
@data-model.md
@data-quality-strategy.md
@design-notes.md
@src/data_generation/DATA_GENERATION_NOTES.md
@.cursor/rules/project-engineering.mdc

Do NOT modify any file.

Check:

1. Explicit schemas exactly match the data model.
2. All business columns remain nullable in Bronze.
3. Empty CSV fields correctly map to NULL.
4. Header validation detects missing columns.
5. Header validation detects unexpected columns.
6. Malformed CSV handling is appropriate.
7. Expected row counts are exactly 10,000 / 500 / 100,000.
8. Row count is checked before Delta write.
9. Row count is checked after Delta write.
10. Bronze tables use Delta.
11. Bronze uses overwrite as designed.
12. No partitioning is introduced.
13. All three source datasets are ingested.
14. All 460 intentional defects are preserved.
15. No dropDuplicates is used.
16. No DQ filtering is performed.
17. No FK validation/repair is performed.
18. No Silver logic is performed in Bronze.
19. Metadata columns are correctly populated.
20. One batch ID is shared across the pipeline run.
21. Audit logging is implemented correctly.
22. Audit records are appended rather than overwritten.
23. Failure handling is correct.
24. Missing/empty source files fail clearly.
25. Delta write failures are handled.
26. Rerun behavior is idempotent.
27. Configuration is centralized.
28. There are no unnecessary hard-coded paths or magic numbers.
29. Entity scripts are thin and reuse shared logic.
30. ingest_all.py properly orchestrates the entities.
31. The implementation is reasonably compatible with Databricks PySpark.
32. No unnecessary external dependencies were introduced.
33. README instructions match the implementation.
34. No assignment requirements were changed.
35. No unrelated project files were modified.

For each item return:

PASS / FAIL / NEEDS ATTENTION

with a short explanation.

Then provide:

### Critical Issues
### Medium Issues
### Minor Issues
### Recommended Fixes
### Overall Verdict

Do not claim runtime success.
```

### AI Response Summary

Cursor performed a static senior-level review of all eight Bronze files against assignment, design, data model, data quality strategy, and project engineering rules. No files were modified.

**35-item checklist results:**

| Result | Count |
|--------|-------|
| PASS | 33 |
| NEEDS ATTENTION | 2 |
| FAIL | 0 |

**Areas that passed:**

- Core Bronze requirements (raw ingest, no cleansing, three entities, centralized config)
- Explicit schemas match `data-model.md` (types and columns)
- All business columns nullable in Bronze
- NULL handling via `nullValue=""`
- Header validation detects missing and extra columns
- Malformed CSV handling via `mode=FAILFAST`
- Expected row counts exactly 10,000 / 500 / 100,000
- Pre-write and post-write row-count validation
- Delta persistence with overwrite; no partitioning
- Metadata columns (`_ingest_timestamp`, `_source_file`, `_ingest_batch_id`)
- Shared batch ID in `ingest_all.py`
- Audit logging with append mode
- Failure handling with context and audit `FAILED` records
- Missing/empty source file checks
- Delta write failure wrapping
- Idempotent rerun (overwrite Bronze, append audit)
- No `dropDuplicates`, DQ filtering, FK validation, or Silver logic
- Defect preservation by static inspection (no dedup/filter/repair in code)
- Thin entity scripts reusing `ingest_utils.py`
- No unnecessary external dependencies
- README matches implementation
- Assignment requirements unchanged; Bronze scope only

**NEEDS ATTENTION (2 items):**

- **Item 30 — Orchestrator:** `ingest_all.py` continues ingesting remaining entities after a failure, which can leave a partially updated Bronze state within one run.
- **Item 31 — Databricks compatibility:** Flat imports require `sys.path` setup; Unity Catalog may need catalog-qualified schema names; timezone-aware `datetime` in `lit()` may vary by Spark version.

**Header validation limitation (not a checklist FAIL):** Validation checks column name sets but not column order. Spark CSV reads with explicit schema map by position; reordered columns with the same names would pass header validation but misalign data. Safe for current generated CSVs where order matches schema.

**Issue summary:**

| Severity | Count | Examples |
|----------|-------|----------|
| Critical | 0 | — |
| Medium | 4 | Partial orchestrator failure; column-order gap; UC assumptions; defect preservation not runtime-proven |
| Minor | 6 | Unused `EntityConfig` import; unused `METADATA_SCHEMA`; full-file line scan for empty check; audit-write failure masking; timezone-aware timestamps; no automated tests |

**Overall verdict:** **APPROVE WITH MINOR RESERVATIONS** — core implementation is assignment-aligned and design-faithful; operational gaps should be addressed or validated before claiming Databricks runtime success.

### Key Decisions

| Finding | Outcome |
|---------|---------|
| Explicit schemas vs data model | PASS — columns and types align with `data-model.md` §7–8 |
| Business column nullability | PASS — all business fields `nullable=True` |
| NULL handling | PASS — `nullValue=""`; no repair |
| Header validation (missing/extra) | PASS |
| Header validation (column order) | Gap identified — name-set check only; positional CSV mapping risk |
| Row-count validation | PASS — pre-write and post-write |
| Delta overwrite / no partition | PASS |
| Defect preservation | PASS by static inspection; not runtime-verified |
| Audit append | PASS |
| Orchestrator fail-fast | NEEDS ATTENTION — continues after entity failure |
| Databricks compatibility | NEEDS ATTENTION — path imports, UC, timestamp behavior |
| Critical issues | None identified |
| Overall acceptance | Approve with minor reservations |

### Accepted

- Bronze implementation meets core assignment and approved design requirements.
- Explicit schemas, centralized configuration, and shared `ingest_utils.py` architecture.
- NULL handling contract (`nullValue=""`, nullable business columns, no coalesce/repair).
- Header validation for missing and unexpected columns.
- Pre-write and post-write row-count gates at 10,000 / 500 / 100,000.
- Delta overwrite for Bronze tables; append for `audit.ingestion_log`.
- Metadata column population without modifying business values.
- One shared `batch_id` per `ingest_all.py` run.
- Audit logging on success and failure paths.
- Defect preservation by design (no dedup, filter, FK repair, quality flags, or Silver logic in Bronze code).
- Idempotent rerun behavior for Bronze tables.
- Thin entity scripts and README consistency with code.
- No unnecessary external dependencies.
- Bronze files confined to `src/bronze/`; no assignment requirement changes.
- Review verdict: acceptable for assessment codebase pending Databricks runtime validation.

### Rejected

No implementation decisions were explicitly rejected during this interaction.

The review identified gaps requiring attention (orchestrator partial-failure behavior, column-order validation, Databricks environment assumptions) but did not reject the implementation approach or require redesign.

### Reasoning

The reviewer considered the core Bronze implementation acceptable because it faithfully implements the approved Interaction 1 design: raw CSV landing with explicit schemas, fatal structural validation, metadata and audit logging, row-count gates, Delta overwrite, and strict preservation of source defects for Silver. Thirty-three of thirty-five checklist items passed with no failures and no critical issues.

The two NEEDS ATTENTION items are operational rather than architectural:

1. **Orchestrator partial failure:** Continuing after an entity error can refresh some Bronze tables while leaving others stale in the same run. This does not violate static code correctness but weakens atomic full-layer refresh semantics.
2. **Databricks compatibility:** The code is reasonable for standard Databricks Runtime but makes assumptions (flat imports via `sys.path`, Hive-style `CREATE SCHEMA`, timezone-aware `lit()`) that should be confirmed at runtime, especially on Unity Catalog workspaces.

The column-order header validation gap is a medium-severity design limitation: name-set validation is insufficient when Spark maps CSV columns by position. This is safe for the current generated CSVs but should be tightened or validated before production use.

### Files Changed

The static code review did **not** modify the Bronze implementation or any other project file. This interaction updated only `ai-prompts/05-bronze-layer.md`.

### Validation Status

| Type | Status |
|------|--------|
| Static code review | Complete — 35-item checklist; verdict: approve with minor reservations |
| Runtime execution | **Not performed** |
| Databricks runtime validation | **Not performed** |
| Bronze runtime success | **Must not be claimed** — defect counts and ingest behavior not verified in Databricks |

---

## Interaction 4 — Bronze Review Fixes

### Objective

Address the two medium issues identified during the Bronze static code review.

### Exact Prompt Sent

```
Apply the following two targeted fixes to the Bronze implementation.

Review first:

@src/bronze/ingest_all.py
@src/bronze/ingest_utils.py
@src/bronze/config.py
@src/bronze/schemas.py
@src/bronze/README.md
@design-notes.md

## Fix 1 — Fail-fast orchestration

Update `ingest_all.py` so that when one entity ingestion fails:

1. Record the failure through the existing audit mechanism.
2. Stop processing subsequent entities.
3. Return a non-zero failure result / raise the appropriate existing error.
4. Do not continue ingesting remaining entities after the first failure.
5. Preserve the existing successful audit records for entities that completed before the failure.

Do not redesign the audit system.

Do not introduce unnecessary transaction/framework abstractions.

## Fix 2 — Strict CSV column order validation

Update the existing header validation so that it validates:

1. No required columns are missing.
2. No unexpected columns exist.
3. Columns appear in exactly the expected order defined by the corresponding schema.

This is important because Spark CSV parsing with an explicit schema is positional.

Use the existing schema/configuration as the source of truth.

Produce a clear error showing:

- expected column order
- actual column order

Do not change the generated CSV files.

## Constraints

Do not modify:

- data generation code
- generated CSVs
- Silver
- Gold
- Dashboard
- assignment requirements

Do not introduce new dependencies.

Keep the existing architecture.

After making the changes, provide:

1. Files modified
2. Exact changes made
3. Why each change was necessary
4. Confirmation that no other behavior was intentionally changed

Do not claim runtime success.
```

### AI Response Summary

Cursor applied two targeted fixes addressing Interaction 3 medium issues (partial orchestrator failure and column-order header validation gap).

**Fix 1 — `ingest_all.py` (fail-fast orchestration):**

- Replaced accumulating `failures` list with `failed_entity` / `failure_message` tracking.
- On `BronzeIngestionError` or any other exception, the entity loop **`break`s** immediately instead of continuing to later entities.
- Prints summary for entities that succeeded, then `Stopped after first failure (...)` and returns exit code `1`.
- Failed-entity audit still handled by existing `ingest_entity()` `except` blocks (`AUDIT_STATUS_FAILED` via `write_audit_record()` before re-raise). No audit system redesign.

**Fix 2 — `ingest_utils.py` (`validate_csv_header()`):**

- Early return when `actual_columns == expected_columns`.
- Retains missing-column and extra-column detection via set comparison.
- Adds explicit column-order validation: when names match but order differs, error includes `Column order does not match expected schema.`
- Error messages now show `Expected column order:` and `Actual column order:` as ordered lists.
- Expected column order sourced from `expected_business_columns()` in `schemas.py` (unchanged).

**`README.md` updates:**

- Documents fail-fast orchestration and preserved `SUCCESS` audit records for entities completed before failure.
- Documents column-order validation in validation and error-handling sections.

**`config.py` and `schemas.py`:** Reviewed; no changes required.

**Follow-up static verification (same session):** 13-item checklist on the fixes — all **PASS** (orchestrator stop, audit behavior, header missing/extra/order checks, no DQ/Silver changes). Static only; no Databricks execution.

### Key Decisions

| Decision | Outcome |
|----------|---------|
| Fail-fast orchestration | `ingest_all.py` stops on first entity failure via `break`; returns exit code `1` |
| Audit on failure | Reuse existing `ingest_entity()` failure audit path; no new audit framework |
| Preserve prior SUCCESS audits | Entities completing before failure retain append-only `SUCCESS` audit records |
| Strict column-order validation | `validate_csv_header()` requires exact list equality with schema-defined order |
| Error messaging | Show ordered `Expected column order` and `Actual column order` on mismatch |
| Scope discipline | Only orchestrator, header validation, and README updated; no CSV or other layer changes |

### Accepted

- Fail-fast orchestration in `ingest_all.py` as the remediation for partial-failure behavior flagged in Interaction 3.
- Strict CSV column-order validation in `validate_csv_header()` to align with Spark positional CSV mapping.
- Continued use of existing `ingest_entity()` audit mechanism for both `SUCCESS` and `FAILED` records.
- Existing architecture preserved (no new dependencies, no audit redesign, no assignment scope changes).
- `expected_business_columns()` from `schemas.py` as source of truth for column order.

### Rejected

No implementation decisions were explicitly rejected during this interaction.

### Reasoning

Interaction 3 identified two medium issues: the orchestrator continued after entity failures (risking partially updated Bronze state) and header validation checked column name sets but not order (unsafe because Spark CSV reads with explicit schema map by position).

Fail-fast orchestration ensures a failed `ingest_all.py` run does not ingest remaining entities while entities that already succeeded keep their Bronze tables and `SUCCESS` audit history. Strict column-order validation closes the positional-mapping gap with clear expected-vs-actual order errors, without changing generated CSVs or the broader Bronze design.

### Files Changed

- `src/bronze/ingest_all.py`
- `src/bronze/ingest_utils.py`
- `src/bronze/README.md`
- `ai-prompts/05-bronze-layer.md` *(this interaction history update only)*

### Validation Status

| Type | Status |
|------|--------|
| Static fix implementation | Complete — two targeted fixes applied |
| Static fix review | Complete — 13-item post-fix checklist; all PASS |
| Databricks runtime execution | **Not performed** |
| Bronze runtime success | **Must not be claimed** — ingest and audit behavior not verified in Databricks |
