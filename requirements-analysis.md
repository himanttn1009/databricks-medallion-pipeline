# Requirement Analysis

> **Status:** Analysis complete. Pipeline implemented and manually runtime-validated (Bronze → Silver → Gold → Dashboard). Automated tests not implemented.  
> **Source of truth:** `assignment/assignment-requirements.md`  
> **Engineering standards:** `.cursor/rules/project-engineering.mdc`

---

## 1. Problem Statement

An e-commerce company operates three operational data sources — a **customer database**, an **order system**, and a **product catalog** — that produce daily sales-related extracts. These extracts arrive as **CSV files** and must be integrated into **Databricks** using a **Medallion Architecture** so that analytics consumers can trust and use the data.

From an engineering perspective, the problem is to design and deliver a **batch data pipeline** that:

1. **Lands** raw source files without loss of fidelity (Bronze).
2. **Validates and curates** data by applying structured quality rules and preserving invalid records for audit (Silver).
3. **Publishes** business-ready aggregated datasets for reporting (Gold).
4. **Exposes** those datasets to business stakeholders through a **Databricks SQL Dashboard**.

The assignment additionally requires demonstrating **AI-assisted data engineering** across the full lifecycle — not only building the pipeline, but making design, implementation, validation, testing, debugging, and reflection **visible and auditable**.

This is a **capability exercise**, not a graded test. Success is measured by a working end-to-end pipeline **and** the quality of lifecycle artifacts (documentation, prompt history, reflection).

---

## 2. Business Objectives

Business stakeholders need the following outcomes from this pipeline:

| Objective | Business need | Pipeline contribution |
|-----------|---------------|----------------------|
| **Trusted raw data archive** | Ability to audit what was received from source systems | Bronze layer ingests CSVs unchanged with ingestion metadata |
| **Data quality assurance** | Confidence that customer, order, and product data meets minimum standards before analytics | Silver layer applies completeness, uniqueness, and referential integrity checks; reports pass rates |
| **Revenue and sales insight** | Understand product performance and customer value | Gold aggregations: sales by product, revenue by customer, customer segmentation |
| **Self-service analytics** | Business users can explore metrics without writing SQL | Databricks SQL Dashboard with product, customer, and segmentation visualizations |
| **Operational transparency** | Visibility into data problems without silent data loss | Invalid records flagged (not deleted); quality metrics reported |

The assignment scope is intentionally small (~110,500 rows) so effort can focus on **engineering discipline and AI workflow evidence**, not big-data scale challenges.

---

## 3. Functional Requirements

All items below are **assignment requirements** unless marked as *(engineering consideration)*.

### 3.1 Assessment structure

| Part | Focus | Effort emphasis |
|------|-------|-----------------|
| Part A | AI Workflow Foundation (`tool-workflow.md`) | 20% |
| Part B | Medallion Architecture Data Pipeline (Core) | 60% |
| Part C | Submission and Reflection | 20% |

- Complete within **three weeks**, self-paced.
- Mandatory Core scoped to **20–25 focused hours**.
- Do not expand pipeline complexity at the expense of lifecycle artifacts.

### 3.2 Sample data generation

- Provide a **sample data generator script** (Python/PySpark) that creates realistic CSV files.
- Generate all three source files: `customers.csv`, `orders.csv`, `products.csv`.
- Intentionally inject the quality issues specified in Section 6 (exact counts).
- Document how data was generated and why quality issues exist (`DATA_GENERATION_NOTES.md`).
- Use AI to help design the generator script.

### 3.3 Bronze layer

- Read CSVs from **S3/DBFS** into Databricks.
- Create **Bronze tables** containing raw, unchanged data.
- Handle **schema inference and data types**.
- **Log ingestion metadata** (row counts, timestamp).
- Perform **no transformations or cleaning** — raw ingest only.
- Provide per-source ingest scripts and an orchestrator (`ingest_all.py`).

### 3.4 Silver layer

- Implement data quality checks (assignment requires **four** working checks — see Section 17 for ambiguity on the fourth).
- Three explicitly defined check categories:
  - **Completeness:** No NULLs in critical fields (`email`, `customer_id`, `product_id`).
  - **Uniqueness:** No duplicate `order_id` or `customer_id`.
  - **Referential integrity:** Every `customer_id` and `product_id` in orders exists in parent tables.
- **Flag bad rows** — do not delete.
- Add a **`quality_check_result`** column.
- Generate a **quality metrics report** showing **% passed** for each check.
- Apply data quality checks, clean and validate data *(business context)* within the flagging model above.

### 3.5 Gold layer

- Build **three aggregation tables** (core acceptance criteria):
  - **A) Sales by Product:** `product_id`, `product_name`, `category`, `total_orders`, `total_revenue`, `avg_order_value`
  - **B) Revenue by Customer:** `customer_id`, `customer_name`, `customer_segment`, `total_orders`, `total_revenue`, `avg_order_value`, `lifetime_value_actual`
  - **C) Customer Segmentation:** `segment_type` (`High-Value` / `Repeat` / `One-Time` / `Inactive`), `customer_count`, `avg_revenue`, `total_revenue`
- Aggregation calculations must be correct (sum, count, avg, etc.).
- Common technical requirements also reference **four aggregations** — see Section 17.

### 3.6 Dashboard

- Create a **Databricks SQL Dashboard** with **3+ tiles**.
- Required visualizations:
  1. Top 10 products by revenue — **bar chart**
  2. Customer revenue distribution — **histogram**
  3. Customer segmentation — **pie chart**
- Write queries, configure visualizations, and **add filters**.
- Deliver `dashboard_queries.sql` (3+ SQL queries) and `DASHBOARD_GUIDE.md`.

### 3.7 Database and seed data

- Provide **database schema or setup script** (`database/schema.sql`).
- Provide **seed/sample data** (the three CSVs in `data/`).
- Document seed data and setup (`seed-data-notes.md`, `setup-notes.md`).

### 3.8 Code quality and operations

- **Input validation and error handling** in pipeline code.
- **Data quality reporting** as a deliverable.
- All code must be **readable, commented, and documented**.
- `README.md` with setup instructions that work **end-to-end**.

### 3.9 Testing

- **At least one meaningful test tier** (data quality tests or pipeline tests).
- **Basic test suite:** data quality tests and pipeline integration tests.
- Data quality tests must verify that checks **catch intentional issues**.

### 3.10 Documentation and AI artifacts

- Full set of lifecycle artifacts (see Section 13).
- **Full prompt history (CRITICAL)** in `ai-prompts/`.
- `tool-workflow.md`, `reflection.md`, `final-ai-usage-summary.md`.
- `debugging-notes.md` and code review notes.
- Cursor-specific workflow folder: `tool-specific/cursor-workflow/`.

### 3.11 Technology stack *(assignment + project rules)*

| Component | Requirement source |
|-----------|-------------------|
| Databricks | Assignment |
| Python, PySpark, Spark SQL | Assignment |
| Delta Lake | Assignment (library); project rules (stack) |
| Git / GitHub | Assignment; project rules |

---

## 4. Non-Functional Requirements

Requirements are split by source. **Assignment requirements** are mandatory deliverable expectations. **Engineering considerations** are reasonable production practices aligned with project rules but not always explicitly stated in the assignment.

### 4.1 Reliability

| ID | Requirement | Source |
|----|-------------|--------|
| REL-01 | Pipeline must run end-to-end: Bronze → Silver → Gold → Dashboard | Assignment |
| REL-02 | Input validation and error handling in pipeline code | Assignment |
| REL-03 | Ingestion must log row counts and timestamps for audit | Assignment |
| REL-04 | Fail loudly with context on unexpected errors *(e.g., missing source files, schema read failures)* | Engineering consideration (project rules) |
| REL-05 | README setup instructions must be reproducible on Databricks Community Edition | Assignment |

### 4.2 Maintainability

| ID | Requirement | Source |
|----|-------------|--------|
| MNT-01 | Code must be readable, commented, and documented | Assignment |
| MNT-02 | Modular layer structure: separate scripts per source/check/aggregation | Assignment (repo structure) |
| MNT-03 | Small functions, clear naming, separation of concerns | Engineering consideration (project rules) |
| MNT-04 | Follow existing repository conventions and medallion layer boundaries | Engineering consideration (project rules) |
| MNT-05 | Avoid unnecessary complexity; prefer simplest correct solution | Engineering consideration (project rules) |
| MNT-06 | Do not expand pipeline complexity at the expense of artifacts | Assignment |

### 4.3 Data quality

| ID | Requirement | Source |
|----|-------------|--------|
| DQ-01 | Silver implements four quality checks (per acceptance criteria) | Assignment |
| DQ-02 | Flag invalid rows; do not silently delete | Assignment; project rules |
| DQ-03 | Preserve traceability of invalid records | Project rules |
| DQ-04 | Quality metrics report with % passed per check | Assignment |
| DQ-05 | Thresholds: completeness >99%, uniqueness 100%, referential integrity >99.9% | Assignment (template guidance) |
| DQ-06 | Sample data must include ~700 intentional defects at specified counts | Assignment |
| DQ-07 | Data quality tests must prove checks detect intentional issues | Assignment |

### 4.4 Testability

| ID | Requirement | Source |
|----|-------------|--------|
| TST-01 | At least one meaningful test tier | Assignment |
| TST-02 | Basic test suite: DQ tests + pipeline integration tests | Assignment |
| TST-03 | Tests must verify intentional quality issues are caught | Assignment |
| TST-04 | Evidence of debugging documented in `debugging-notes.md` | Assignment |
| TST-05 | Validate AI-generated code before considering tasks complete | Engineering consideration (project rules) |

### 4.5 Traceability

| ID | Requirement | Source |
|----|-------------|--------|
| TRA-01 | Bronze preserves raw source fidelity | Assignment; project rules |
| TRA-02 | `quality_check_result` column on Silver records | Assignment |
| TRA-03 | Ingestion metadata (row counts, timestamp) on Bronze | Assignment |
| TRA-04 | Full AI prompt history with accept/reject reasoning | Assignment |
| TRA-05 | Document assumptions, ambiguities, and engineering decisions | Assignment; project rules |
| TRA-06 | Git commit history showing iterative development | Assignment (Cursor expectations) |

### 4.6 Scalability

| ID | Requirement | Source |
|----|-------------|--------|
| SCL-01 | Use Spark-native operations (DataFrame API, Spark SQL, Delta Lake) | Engineering consideration (project rules) |
| SCL-02 | Design for distributed processing even though dataset is small (~110K rows) | Engineering consideration (project rules) |
| SCL-03 | No specific throughput, latency, or cluster-size requirements stated | Assignment (not specified) |

> **Note:** The assignment does not define performance SLAs. Scalability requirements above reflect stack choices and production-oriented project rules, not explicit assignment mandates.

---

## 5. Source Data Requirements

Source files are **CSV format**, stored on **S3/DBFS**, and also committed/generated under `data/` in the repository.

### 5.1 `customers.csv`

| Attribute | Value |
|-----------|-------|
| **Rows** | 10,000 |
| **Approx. size** | ~500 KB |
| **Role** | Customer dimension |

| Column | Type | Constraints |
|--------|------|-------------|
| `customer_id` | INT | Primary Key |
| `customer_name` | STRING | |
| `email` | STRING | |
| `country` | STRING | |
| `signup_date` | DATE | |
| `customer_segment` | STRING | `Premium` / `Standard` / `Basic` |
| `lifetime_value` | DECIMAL | |

### 5.2 `orders.csv`

| Attribute | Value |
|-----------|-------|
| **Rows** | 100,000 |
| **Approx. size** | ~2–3 MB |
| **Role** | Sales fact table |

| Column | Type | Constraints |
|--------|------|-------------|
| `order_id` | INT | Primary Key |
| `customer_id` | INT | Foreign Key → `customers` |
| `order_date` | DATE | |
| `product_id` | INT | Foreign Key → `products` |
| `quantity` | INT | |
| `unit_price` | DECIMAL | |
| `total_amount` | DECIMAL | |
| `order_status` | STRING | `Pending` / `Completed` / `Cancelled` |
| `payment_date` | DATE | Nullable |

### 5.3 `products.csv`

| Attribute | Value |
|-----------|-------|
| **Rows** | 500 |
| **Approx. size** | ~50 KB |
| **Role** | Product dimension |

| Column | Type | Constraints |
|--------|------|-------------|
| `product_id` | INT | Primary Key |
| `product_name` | STRING | |
| `category` | STRING | |
| `price` | DECIMAL | |
| `cost` | DECIMAL | |
| `stock_quantity` | INT | |
| `reorder_level` | INT | |

### 5.4 Relationships

```
customers (1) ──< orders (many) >── (1) products
```

- `orders.customer_id` → `customers.customer_id`
- `orders.product_id` → `products.product_id`

---

## 6. Intentional Data Quality Issues

The sample data generator must inject these defects so Silver quality checks can be verified.

### 6.1 `customers.csv`

| # | Issue | Count | Quality dimension |
|---|-------|-------|-------------------|
| 1 | NULL `email` | **50** | Completeness |
| 2 | Duplicate `customer_id` | **10** | Uniqueness |

### 6.2 `orders.csv`

| # | Issue | Count | Quality dimension |
|---|-------|-------|-------------------|
| 3 | NULL `customer_id` | **100** | Completeness |
| 4 | NULL `product_id` | **200** | Completeness |
| 5 | `customer_id` not in `customers` table | **50** | Referential integrity |
| 6 | `product_id` not in `products` table | **30** | Referential integrity |
| 7 | Duplicate `order_id` | **20** | Uniqueness |

### 6.3 Summary

| Metric | Value |
|--------|-------|
| Total intentional defect rows | **~700** |
| Total dataset rows (approx.) | **~110,500** (10,000 + 100,000 + 500) |
| Defect rate (assignment figure) | **0.7%** (assignment references ~100,000 as denominator) |

> Individual defect counts sum to **460** rows if each defect is on a distinct row. The assignment states **~700 problematic rows**, which may imply overlapping defects on the same rows or additional defects not itemized. **Exact overlap behavior is not specified** — see Section 17.

---

## 7. Bronze Requirements

| # | Requirement |
|---|-------------|
| B-01 | Read `customers.csv`, `orders.csv`, `products.csv` from S3/DBFS |
| B-02 | Create Bronze tables with raw, unchanged source data |
| B-03 | Handle schema inference and apply correct data types |
| B-04 | Log ingestion metadata: row counts and timestamp |
| B-05 | No transformations, cleansing, deduplication, or quality filtering |
| B-06 | Provide `01_ingest_customers.py`, `02_ingest_orders.py`, `03_ingest_products.py`, `ingest_all.py` |
| B-07 | Acceptable minimal additions: ingestion metadata columns (per project rules) |

**Out of scope for Bronze:** quality checks, joins, aggregations, business logic.

---

## 8. Silver Requirements

### 8.1 Quality checks (assignment-defined categories)

| Check | Rule | Fields / keys |
|-------|------|---------------|
| **Completeness** | No NULLs in critical fields | `email` (customers), `customer_id` and `product_id` (orders) |
| **Uniqueness** | No duplicate values | `order_id`, `customer_id` |
| **Referential integrity** | Foreign keys must exist in parent tables | `customer_id` → customers; `product_id` → products |

### 8.2 Processing rules

| # | Requirement |
|---|-------------|
| S-01 | Flag bad rows; **do not delete** |
| S-02 | Add `quality_check_result` column |
| S-03 | Generate quality metrics report with **% passed** per check |
| S-04 | Implement **four** quality checks (acceptance criteria) |
| S-05 | Provide modular scripts per check type and `create_silver_tables.py` orchestrator |

### 8.3 Quality thresholds (submission template guidance)

| Check | Threshold |
|-------|-----------|
| Completeness | >99% complete |
| Uniqueness | 100% unique |
| Referential integrity | >99.9% valid |

### 8.4 Repository-implied additional checks (not fully specified)

The required repo structure includes:

- `03_quality_type_validation.py`
- `05_quality_business_logic.py`

The assignment does not define what these validate. **Decision deferred** — see Section 17.

---

## 9. Gold Requirements

### 9.1 Aggregation table A — Sales by Product

| Column |
|--------|
| `product_id` |
| `product_name` |
| `category` |
| `total_orders` |
| `total_revenue` |
| `avg_order_value` |

### 9.2 Aggregation table B — Revenue by Customer

| Column |
|--------|
| `customer_id` |
| `customer_name` |
| `customer_segment` |
| `total_orders` |
| `total_revenue` |
| `avg_order_value` |
| `lifetime_value_actual` |

### 9.3 Aggregation table C — Customer Segmentation

| Column | Notes |
|--------|-------|
| `segment_type` | `High-Value` / `Repeat` / `One-Time` / `Inactive` |
| `customer_count` | |
| `avg_revenue` | |
| `total_revenue` | |

### 9.4 General Gold requirements

| # | Requirement |
|---|-------------|
| G-01 | Produce all **three** aggregation tables (core acceptance criteria) |
| G-02 | Calculations must be correct: sum, count, avg |
| G-03 | Provide SQL scripts and `create_gold_tables.py` orchestrator |
| G-04 | Common technical requirements reference **four aggregations** — see Section 17 |
| G-05 | Repo structure includes `03_daily_weekly_trends.sql` — purpose not defined in Gold spec |

---

## 10. Dashboard Requirements

| # | Requirement |
|---|-------------|
| D-01 | Databricks SQL Dashboard with **3+ tiles** |
| D-02 | **Bar chart:** Top 10 products by revenue |
| D-03 | **Histogram:** Customer revenue distribution |
| D-04 | **Pie chart:** Customer segmentation |
| D-05 | Write **3+ SQL queries** for visualizations (`dashboard_queries.sql`) |
| D-06 | Configure visualizations in Databricks |
| D-07 | Add **filters** (dimensions not specified — see Section 17) |
| D-08 | Document setup in `DASHBOARD_GUIDE.md` |
| D-09 | Dashboard should consume **Gold layer** outputs |

---

## 11. Testing Requirements

### 11.1 Assignment requirements

| # | Requirement |
|---|-------------|
| T-01 | Input validation and error handling in pipeline code |
| T-02 | Data quality reporting implemented |
| T-03 | At least **one meaningful test tier** |
| T-04 | **Basic test suite:** data quality tests + pipeline integration tests |
| T-05 | Data quality tests must verify checks catch **intentional issues** |
| T-06 | Debugging evidence in `debugging-notes.md` |
| T-07 | Code review notes (location not specified — see Section 17) |

### 11.2 Expected test categories *(engineering consideration)*

| Category | Purpose |
|----------|---------|
| **Data quality tests** | Assert flagged row counts align with known intentional defects |
| **Pipeline integration tests** | Assert Bronze → Silver → Gold runs and produces expected tables |
| **Unit tests** | Validate aggregation logic and segmentation rules once defined |

### 11.3 Current status

**No tests have been written or executed.** Test strategy to be detailed in `design-notes.md` during implementation.

---

## 12. AI Workflow Requirements

### 12.1 Part A — `tool-workflow.md`

Must document:

- Primary AI tool used
- How project context is provided to the tool
- AI use for: requirement analysis, pipeline design, code generation, validation, testing, debugging, data quality checks
- Information avoided when using AI (e.g., real customer PII)
- How workflow would be reused in production
- Lessons learned

### 12.2 Prompt history — `ai-prompts/` (CRITICAL)

Seven activity files (layer history in numbered `04–08` files):

- `04-data-generation.md`
- `05-bronze-layer.md`
- `06-silver-layer.md`
- `07-gold-layer.md`
- `08-dashboard-layer.md`
- `debugging.md`
- `documentation.md`

See `ai-prompts/README.md` for the index.

Each must capture: prompt text (or summary), AI response summary, what was accepted/changed/rejected, and why.

### 12.3 Part C — `reflection.md`

Must cover: what was built, AI usage across lifecycle, what AI helped with most, what AI got wrong, validation approach, improvements, reusable workflow.

### 12.4 Additional artifacts

- `final-ai-usage-summary.md`
- `tool-specific/cursor-workflow/` with: `project-context.md`, `spec.md`, `cursor-rules-or-instructions.md`, `task-breakdown.md`

### 12.5 Cursor usage expectations

| Expectation | Detail |
|-------------|--------|
| Persistent context | Rules, specs, assignment doc referenced repeatedly |
| Iteration | Multiple refinement cycles documented |
| Validation | AI-generated code verified before acceptance |
| Specific prompts | Not vague one-liners |
| Git history | Shows accept → test → fix → refine cycles |

### 12.6 Project rules — AI capability dimensions

AI usage should be visible across: requirement analysis, architecture, data modeling, data generation, implementation, testing, debugging, code review, documentation, reflection.

### 12.7 Security constraints *(project rules)*

- Never introduce credentials, secrets, API keys, or real customer data.
- Use placeholders and secure configuration patterns.

---

## 13. Repository Requirements

Repository must follow the assignment structure as closely as possible.

### 13.1 Root-level files

`README.md`, `candidate-info.md`, `tool-workflow.md`, `requirements-analysis.md`, `design-notes.md`, `data-model.md`, `data-quality-strategy.md`, `debugging-notes.md`, `reflection.md`, `final-ai-usage-summary.md`

### 13.2 Source code layout

```
src/
├── data_generation/   → generate_sample_data.py, DATA_GENERATION_NOTES.md
├── bronze/            → 01_ingest_*.py, ingest_all.py
├── silver/            → 01–05 quality scripts, create_silver_tables.py
├── gold/              → 01–04 SQL scripts, create_gold_tables.py
└── dashboard/         → dashboard_queries.sql, DASHBOARD_GUIDE.md
```

### 13.3 Data and database

```
data/          → customers.csv, orders.csv, products.csv
database/      → schema.sql, seed-data-notes.md, setup-notes.md
```

### 13.4 AI and Cursor artifacts

```
ai-prompts/                    → 7 activity prompt history files
tool-specific/cursor-workflow/   → 4 Cursor workflow files
```

### 13.5 Common technical deliverables (every submission)

- Sample data generator with intentional quality issues
- Bronze ingestion code (Python/PySpark)
- Silver validation code (4 quality checks working)
- Gold aggregation code (assignment references 4; acceptance criteria references 3)
- Dashboard queries (3+ SQL)
- Database schema/setup script
- Seed CSVs
- Input validation and error handling
- Data quality reporting
- Meaningful test tier + basic test suite
- README with end-to-end setup
- Full prompt history
- All planning, design, testing, debugging, reflection artifacts

> The full lifecycle artifact set is required regardless of stretch tier. **Artifacts are the point.**

---

## 14. Submission Requirements

### 14.1 What to submit

1. **Git repository link** using **ttn email id**
   - Cloneable to Databricks Community Edition for development/testing
2. **Online submission form** with short written answers

### 14.2 Form questions (answer in your own words)

- Understanding of the medallion architecture problem
- How AI was used across data generation, ingestion, validation, aggregation
- Key design and implementation decisions made through AI
- Testing and validation approach
- How AI output was validated
- What would be improved next

### 14.3 Constraints

| Constraint | Detail |
|------------|--------|
| Not graded | Feedback and growth path, not a grade |
| Time box | 3 weeks, self-paced |
| Core effort | 20–25 focused hours |
| No deployment | Nothing to host or deploy |
| Honesty | Specific, honest answers required for useful feedback |

### 14.4 Follow-up

- Feedback report shared after review
- Mentor/competency owner may schedule a short coaching conversation (not a re-examination)

---

## 15. Assumptions

Assumptions below are **working hypotheses** for planning. They are **not resolved requirements** and must be confirmed or replaced during design (see Section 17 for unresolved items).

| # | Assumption | Rationale |
|---|------------|-----------|
| A-01 | Pipeline runs in **batch mode** (not streaming) | Assignment describes daily CSV ingestion |
| A-02 | **Databricks Community Edition** is the primary development target | Assignment explicitly references it |
| A-03 | Uniqueness on `customer_id` applies to the **customers table only**; uniqueness on `order_id` applies to the **orders table only** | `customer_id` is FK on orders (many orders per customer expected) |
| A-04 | Gold aggregations will read from **Silver validated data**, not Bronze | Medallion architecture principle |
| A-05 | No real customer PII will be used; synthetic data only | Assignment + project security rules |
| A-06 | **Delta Lake** will be used for persistent tables | Project rules list Delta Lake in stack; assignment lists it as a library |
| A-07 | CSVs can be stored under `data/` locally and uploaded to DBFS for Databricks runs | Practical CE workflow; exact paths TBD |
| A-08 | Dashboard is built manually in Databricks SQL UI using queries from the repo | Assignment describes configuring visualizations |
| A-09 | Overlapping defects (one row failing multiple checks) may exist unless generator enforces mutual exclusivity | Explains gap between 460 itemized defects and ~700 stated total |

---

## 16. Edge Cases

Edge cases to address during design and implementation. **None have been tested yet.**

### 16.1 Data generation

| Edge case | Consideration |
|-----------|---------------|
| Overlapping quality defects on same row | May affect total ~700 count vs sum of individual counts |
| Future-dated `signup_date` or `order_date` | Not specified as intentional defect; type/business logic checks may catch |
| `total_amount` ≠ `quantity × unit_price` | Not listed as intentional defect; business logic check may apply |
| Completed orders with NULL `payment_date` | Nullable field — may be valid or a business rule violation (undefined) |

### 16.2 Bronze ingestion

| Edge case | Consideration |
|-----------|---------------|
| Missing or empty CSV file | Error handling required |
| Schema drift (extra/missing columns) | Schema inference vs explicit schema |
| Type coercion failures (e.g., bad date strings) | May surface in Bronze or Silver type validation |
| Duplicate rows in source | Must land in Bronze unchanged; Silver flags them |

### 16.3 Silver validation

| Edge case | Consideration |
|-----------|---------------|
| Row fails multiple checks | How `quality_check_result` represents multiple failures (undefined) |
| Duplicate `customer_id` with different attribute values | Which row is "valid" (undefined) |
| Orphan `customer_id` that is also NULL | Completeness and referential integrity may both flag |
| Referential integrity when parent table has duplicate PKs | Check order and dependency between uniqueness and RI |

### 16.4 Gold aggregations

| Edge case | Consideration |
|-----------|---------------|
| Cancelled or Pending orders in revenue totals | Assignment does not specify order_status filter |
| Customers with only invalid orders | Segmentation and revenue attribution |
| Products with no valid orders | Appear in catalog but zero revenue |
| `lifetime_value` (source) vs `lifetime_value_actual` (computed) | May diverge by design — calculation undefined |

### 16.5 Dashboard

| Edge case | Consideration |
|-----------|---------------|
| Fewer than 10 products with revenue | "Top 10" may return fewer rows |
| Histogram bin boundaries | Not specified |
| Filter interactions across tiles | Must be documented in DASHBOARD_GUIDE.md |

---

## 17. Ambiguities

The following items are **explicitly unresolved**. They must be decided and documented in `design-notes.md` and `data-quality-strategy.md` before implementation. **No decision is made in this document.**

### 17.1 Silver quality checks — count and scope

| What assignment says | Conflict |
|---------------------|----------|
| Three check categories detailed (completeness, uniqueness, referential integrity) | Acceptance criteria require **four** checks |
| Repo lists **five** scripts: completeness, uniqueness, type_validation, referential_integrity, business_logic | Only three categories described in narrative |

**Open questions:**
- Which check is the mandatory fourth?
- What do `type_validation` and `business_logic` validate?
- Is `business_logic` required or stretch?

### 17.2 Gold aggregations — count

| What assignment says | Resolution |
|---------------------|------------|
| Three named aggregation tables (core acceptance criteria) | **Required:** `sales_by_product`, `revenue_by_customer`, `customer_segmentation` |
| Common technical requirements say **four aggregations** | **Required fourth:** `gold.daily_weekly_trends` (GD-06) |

**Resolved:** Implement all four Gold tables per `design-notes.md` §5.2.

### 17.3 Customer segmentation logic

- Gold `segment_type`: `High-Value` / `Repeat` / `One-Time` / `Inactive`
- Source `customer_segment`: `Premium` / `Standard` / `Basic`

**Resolved:** Behavioral rules and P75 threshold finalized in `design-notes.md` §5.6 and `data-model.md` §11.3. Segmentation uses complete valid-customer population (LEFT JOIN qualifying orders).

### 17.4 `lifetime_value_actual` calculation

- Present in Gold table B alongside source `lifetime_value`

**Resolved:** `lifetime_value_actual = total_revenue` = `SUM(total_amount)` of qualifying orders per customer; 0.00 when no orders (GD-11, DA-08). Source `lifetime_value` remains in Silver only.

### 17.5 Silver "clean" vs flag-only

- Business context: "clean and validate data"
- Technical requirements: flag only, do not delete
- **Unclear** whether cleaning means separate valid/quarantine datasets or in-place flagging only

### 17.6 Uniqueness scope for `customer_id`

- Listed alongside `order_id` in uniqueness check
- `customer_id` is PK on customers but FK on orders
- **Likely** per-table scope (see Assumption A-03) but not explicitly confirmed in assignment

### 17.7 Storage paths — S3 vs DBFS

- Sources described as S3/DBFS
- CE constraints may differ from production S3 layout
- **Concrete paths not specified**

### 17.8 Table format — Delta Lake

- Delta Lake listed as library; not explicitly mandated for Bronze/Silver/Gold tables
- Project rules recommend Delta Lake in stack

### 17.9 Dashboard filters

- Filters required; **dimensions not specified**

### 17.10 Code review notes location

- Required in "what counts as complete"
- **No dedicated file** in repository structure

### 17.11 Defect count reconciliation

- Itemized defects sum to **460** rows
- Assignment states **~700 problematic rows**
- **Unclear** whether overlap is intended or additional defects are expected

### 17.12 Gold aggregation filters

- Whether `total_orders`, `total_revenue`, `avg_order_value` include all order statuses or only `Completed` — **not specified**

---

## 18. Acceptance Criteria

Checklist derived from assignment core acceptance criteria and "what counts as complete." **Runtime-validated items marked complete; automated tests and personal submission fields remain pending.**

### 18.1 Core pipeline

- [x] Sample data generated: 3 CSVs with intentional quality issues
- [x] Bronze layer ingests all three sources successfully
- [x] Silver layer implements all **four** quality checks (plus type validation as fifth category)
- [x] Quality report shows **% passed** for each check (`silver.dq_metrics`)
- [x] Gold layer produces all **three** assignment aggregation tables (+ fourth trends table)
- [x] Aggregation calculations are correct (sum, count, avg, etc.) — runtime validated
- [x] Dashboard displays all **3+** visualizations (9 widgets total)
- [x] All code is readable, commented, documented
- [x] README setup instructions work end-to-end
- [x] Data quality tests pass (automated CSV defect tests in `tests/test_data_quality.py`)

### 18.2 Submission completeness

- [x] Working end-to-end pipeline (Bronze → Silver → Gold → Dashboard)
- [x] Sample data generator with realistic quality issues
- [x] All four quality checks implemented and working
- [x] All three Gold layer aggregations (+ `daily_weekly_trends`)
- [x] Dashboard with 3+ SQL queries and visualizations
- [x] Database schema/setup script and seed data
- [x] README with working setup instructions
- [x] Basic test suite (data quality tests — `tests/test_data_quality.py`; pipeline integration tests not implemented)
- [x] Full prompt history with all AI interactions documented
- [x] Requirement analysis, design notes, test strategy
- [x] Debugging notes and code review notes
- [x] Reflection on what was learned

### 18.3 AI workflow artifacts

- [x] `tool-workflow.md` complete (Part A)
- [x] `reflection.md` complete (Part C)
- [x] `final-ai-usage-summary.md` complete
- [x] `ai-prompts/` — all 7 activity files with accept/reject reasoning
- [x] `tool-specific/cursor-workflow/` — all 4 files
- [x] Evidence of iteration and validation in git history

### 18.4 Documentation artifacts

- [x] `candidate-info.md`
- [x] `design-notes.md`
- [x] `data-model.md`
- [x] `data-quality-strategy.md`
- [x] `DATA_GENERATION_NOTES.md`
- [x] `DASHBOARD_GUIDE.md`
- [x] `database/schema.sql`, `seed-data-notes.md`, `setup-notes.md`
- [ ] Online submission form answers prepared *(outside repository — complete on assessment portal)*

### 18.5 Quality indicators ("what good looks like")

- [x] Clear requirement understanding demonstrated
- [x] Well-documented AI prompts with context and refinement
- [x] Data quality thinking: checks work, report is clear, intentional issues caught
- [x] Clean, maintainable code following naming conventions
- [x] Meaningful testing with debugging evidence (CSV data quality tests + manual Databricks validation)
- [x] Honest reflection with trade-offs and reusable patterns

---

*Document version: 1.1 — requirements analysis from assignment source; pipeline implementation and manual runtime validation complete; automated tests not implemented.*
