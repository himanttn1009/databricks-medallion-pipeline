# AI Capability Exercise — Assignment Requirements

> **Source of truth** for the Databricks Medallion Architecture assessment project.  
> Derived from the participant guide. Do not treat requirements outside this document as mandatory unless explicitly added by the assessor.

---

## 1. Assessment Objective

This is a **hands-on capability exercise** to develop and make visible how data engineers use AI tools effectively, responsibly, and practically across the data engineering lifecycle.

- **Not a graded test.** Participants receive a feedback report and a personalized growth path.
- **Shared baseline:** All data engineers in the competency take part; no one is measured against a different bar than their peers.
- **Primary deliverable:** Build a complete Databricks medallion data pipeline (**Bronze → Silver → Gold → Dashboard**) and show thinking across sample data generation, ingestion, data quality validation, aggregations, and visualization.
- **Part B objective:** Demonstrate practical AI-assisted delivery through a realistic Medallion Architecture data engineering assignment.
- **What matters:** Not only whether the final pipeline works, but **how AI was used** for design, implementation, validation, testing, debugging, and reflection. Making thinking visible is the point.

### Effort allocation (guide)

| Part | Focus | Emphasis |
|------|-------|----------|
| Part A | AI Workflow Foundation | 20% |
| Part B | Medallion Architecture Data Pipeline Project (Core + optional Stretch) | 60% |
| Part C | Submission and Reflection | 20% |

### Time and effort

- **Duration:** Self-paced; meant to be completed within **three weeks**.
- **Expected effort (mandatory Core):** Roughly **20–25 focused hours**.
- Remaining time goes into lifecycle artifacts (requirement analysis, prompt history, data quality validation notes, testing and debugging notes, reflection) — these are what feedback focuses on.
- **Do not expand pipeline complexity at the expense of these artifacts.**

### Feedback focus areas

- Requirement analysis and problem understanding
- Prompting and context-setting with AI tools
- Tool workflow and integration
- Data pipeline design (Bronze/Silver/Gold thinking)
- Code quality and maintainability
- Data quality validation depth
- Testing and validation approach
- Debugging methodology
- Data contracts and schema thinking
- Documentation and ownership
- Responsible AI judgment

---

## 2. Business Context

**Problem statement:** An e-commerce company ingests daily sales data from multiple sources (customer database, order system, product catalog) into Databricks. They need to:

| Layer | Need |
|-------|------|
| **Bronze** | Ingest raw CSV files from S3/DBFS |
| **Silver** | Apply data quality checks, clean and validate data |
| **Gold** | Create business-ready aggregations for analytics |
| **Dashboard** | BI dashboards for business stakeholders |

---

## 3. Source Datasets

Source files are **CSVs on S3/DBFS**.

| File | Sample rows | Approx. file size |
|------|-------------|-------------------|
| `customers.csv` | **10,000** | ~**500 KB** |
| `orders.csv` | **100,000** | ~**2–3 MB** |
| `products.csv` | **500** | ~**50 KB** |

---

## 4. Source Schemas

### Table 1: `customers.csv`

| Column | Type | Notes |
|--------|------|-------|
| `customer_id` | INT | Primary Key |
| `customer_name` | STRING | |
| `email` | STRING | |
| `country` | STRING | |
| `signup_date` | DATE | |
| `customer_segment` | STRING | Values: `Premium` / `Standard` / `Basic` |
| `lifetime_value` | DECIMAL | |

### Table 2: `orders.csv`

| Column | Type | Notes |
|--------|------|-------|
| `order_id` | INT | Primary Key |
| `customer_id` | INT | Foreign Key → `customers` |
| `order_date` | DATE | |
| `product_id` | INT | Foreign Key → `products` |
| `quantity` | INT | |
| `unit_price` | DECIMAL | |
| `total_amount` | DECIMAL | |
| `order_status` | STRING | Values: `Pending` / `Completed` / `Cancelled` |
| `payment_date` | DATE | Nullable |

### Table 3: `products.csv`

| Column | Type | Notes |
|--------|------|-------|
| `product_id` | INT | Primary Key |
| `product_name` | STRING | |
| `category` | STRING | |
| `price` | DECIMAL | |
| `cost` | DECIMAL | |
| `stock_quantity` | INT | |
| `reorder_level` | INT | |

---

## 5. Intentional Data Quality Issues

Sample data must include realistic quality issues for the Silver layer to catch.

### `customers.csv`

| Issue | Count | Quality dimension |
|-------|-------|-------------------|
| NULL `email` | **50** rows | Completeness |
| Duplicate `customer_id` | **10** rows | Uniqueness |

### `orders.csv`

| Issue | Count | Quality dimension |
|-------|-------|-------------------|
| NULL `customer_id` | **100** rows | Completeness |
| NULL `product_id` | **200** rows | Completeness |
| `customer_id` not in `customers` table | **50** rows | Referential integrity |
| `product_id` not in `products` table | **30** rows | Referential integrity |
| Duplicate `order_id` | **20** rows | Uniqueness |

### Totals

- **~700 problematic rows** out of **~100,000** total (**0.7%** — realistic data quality rate)

---

## 6. Bronze Requirements

1. Read CSVs from **S3/DBFS** into Databricks.
2. Create **Bronze tables** (raw, unchanged data).
3. Handle **schema inference and data types**.
4. **Log ingestion metadata** (row counts, timestamp).
5. **No transformations or cleaning** — raw ingest only.

### Sample data generation (prerequisite)

- Use AI to help design a **Python/PySpark** script.
- Generate all three CSVs with realistic data.
- Intentionally introduce the quality issues listed in Section 5.
- Document how data was generated and why quality issues exist.

---

## 7. Silver Requirements

### Quality checks to implement

| Check | Rule |
|-------|------|
| **Completeness** | No NULLs in critical fields: `email`, `customer_id`, `product_id` |
| **Uniqueness** | No duplicate rows for `order_id`, `customer_id` |
| **Referential integrity** | Foreign keys exist: every `customer_id`, every `product_id` |

### Processing rules

- **Flag bad rows** — do not delete.
- Add a **`quality_check_result`** column.
- Generate a **quality metrics report** showing **% passed** for each check.

### Thresholds (from submission template guidance)

| Check | Threshold |
|-------|-----------|
| Completeness | **>99%** complete |
| Uniqueness | **100%** unique |
| Referential integrity | **>99.9%** valid |

### Mandatory deliverable count

- Common technical requirements state: **Silver layer validation code (all 4 quality checks working)**.
- Core acceptance criteria state: **Silver layer implements all four quality checks**.

*(See Section 18 for ambiguity between “four quality checks” and the three check categories detailed above.)*

---

## 8. Gold Requirements

Build **three aggregation tables**:

### A) Sales by Product

| Column | |
|--------|---|
| `product_id` | |
| `product_name` | |
| `category` | |
| `total_orders` | |
| `total_revenue` | |
| `avg_order_value` | |

### B) Revenue by Customer

| Column | |
|--------|---|
| `customer_id` | |
| `customer_name` | |
| `customer_segment` | |
| `total_orders` | |
| `total_revenue` | |
| `avg_order_value` | |
| `lifetime_value_actual` | |

### C) Customer Segmentation

| Column | |
|--------|---|
| `segment_type` | Values: `High-Value` / `Repeat` / `One-Time` / `Inactive` |
| `customer_count` | |
| `avg_revenue` | |
| `total_revenue` | |

### Mandatory deliverable count

- Common technical requirements state: **Gold layer aggregation code (all 4 aggregations)**.
- Core acceptance criteria state: **Gold layer produces all three aggregation tables**.
- Aggregation calculations must be correct (sum, count, avg, etc.).

*(See Section 18 for ambiguity between “three” and “four” aggregations.)*

---

## 9. Dashboard Requirements

- Create a **Databricks SQL Dashboard** with **3+ tiles**.
- **Visualizations required:**
  1. **Top 10 products by revenue** — bar chart
  2. **Customer revenue distribution** — histogram
  3. **Customer segmentation** — pie chart
- Write queries, configure visualizations, and **add filters**.
- Deliverable: **Dashboard queries (3+ SQL queries for visualizations)**.

---

## 10. Testing Requirements

Every submission must include:

- **Input validation and error handling**
- **Data quality reporting**
- **At least one meaningful test tier** (data quality tests, pipeline tests)
- **Basic test suite** (data quality tests, pipeline integration tests)

### Verification expectations

- **Data quality tests pass** — verify checks catch intentional issues.
- Evidence of debugging (see required documentation).

---

## 11. Repository Structure Requirements

Submit a Git repository following this structure **as closely as possible**:

```
databricks-medallion-pipeline/
├── README.md
├── candidate-info.md
├── tool-workflow.md                    # Part A: AI Workflow Foundation
├── requirements-analysis.md
├── design-notes.md
├── data-model.md
├── data-quality-strategy.md
│
├── src/
│   ├── data_generation/
│   │   ├── generate_sample_data.py
│   │   └── DATA_GENERATION_NOTES.md
│   ├── bronze/
│   │   ├── 01_ingest_customers.py
│   │   ├── 02_ingest_orders.py
│   │   ├── 03_ingest_products.py
│   │   └── ingest_all.py
│   ├── silver/
│   │   ├── 01_quality_completeness.py
│   │   ├── 02_quality_uniqueness.py
│   │   ├── 03_quality_type_validation.py
│   │   ├── 04_quality_referential_integrity.py
│   │   ├── 05_quality_business_logic.py
│   │   └── create_silver_tables.py
│   ├── gold/
│   │   ├── 01_sales_by_product.sql
│   │   ├── 02_revenue_by_customer.sql
│   │   ├── 03_daily_weekly_trends.sql
│   │   ├── 04_customer_segmentation.sql
│   │   └── create_gold_tables.py
│   └── dashboard/
│       ├── dashboard_queries.sql
│       └── DASHBOARD_GUIDE.md
│
├── data/
│   ├── customers.csv
│   ├── orders.csv
│   └── products.csv
│
├── database/
│   ├── schema.sql
│   ├── seed-data-notes.md
│   └── setup-notes.md
│
├── debugging-notes.md
├── reflection.md
├── final-ai-usage-summary.md
│
└── ai-prompts/
    ├── data-generation.md
    ├── bronze-layer.md
    ├── silver-layer.md
    ├── gold-layer.md
    ├── dashboard.md
    ├── debugging.md
    └── documentation.md
```

### Common technical deliverables (every submission)

- Sample data generator script (creates realistic CSV files with intentional quality issues)
- Bronze layer ingestion code (Python/PySpark)
- Silver layer validation code (all 4 quality checks working)
- Gold layer aggregation code (all 4 aggregations)
- Dashboard queries (3+ SQL queries for visualizations)
- Database schema or setup script
- Seed/sample data (`customers`, `orders`, `products` CSVs)
- Input validation and error handling
- Data quality reporting
- At least one meaningful test tier (data quality tests, pipeline tests)
- README setup instructions
- **Full prompt history (CRITICAL)**
- All planning, design, testing, debugging, and reflection artifacts in the repository

> The full set of lifecycle artifacts is required regardless of stretch tier. Only the application scope is small — **the artifacts are the point.**

---

## 12. AI Workflow Requirements

### Part A: `tool-workflow.md`

Submit a document covering:

- Primary AI tool used (Cursor, Claude, etc.)
- How you provide project context to the tool
- How you use AI for requirement analysis
- How you use AI for pipeline design (Bronze/Silver/Gold — Medallion Architecture)
- How you use AI for code generation (Python/PySpark/SQL)
- How you validate AI-generated code and logic
- How you use AI for testing and validation
- How you use AI for debugging (issues, root causes)
- How you use AI for data quality checks
- What information you avoid sharing unnecessarily with AI tools (e.g., real customer PII)
- How you would reuse this workflow in a real production pipeline
- Lessons learned: what worked, what didn't

### Prompt history: `ai-prompts/{activity}.md`

For each activity, capture prompt history showing:

- Prompt text (or summary)
- AI response (summary or key excerpt)
- What you accepted (and why)
- What you changed (and why)
- What you rejected (and why)

Activities: data-generation, bronze-layer, silver-layer, gold-layer, dashboard, debugging, documentation.

### Part C: `reflection.md`

Cover at minimum:

- What I built
- How I used AI (across the lifecycle)
- What AI helped with most
- What AI got wrong
- How I validated AI output
- What I would improve next
- Reusable workflow

### Additional AI artifact

- `final-ai-usage-summary.md`

---

## 13. Cursor-Specific Expectations

Submit **`tool-specific/cursor-workflow/`** with:

| File | Purpose |
|------|---------|
| `project-context.md` | How you set up project context for Cursor |
| `spec.md` | Your design/specification document |
| `cursor-rules-or-instructions.md` | Cursor rules, `.cursorrules` file, or instructions you used |
| `task-breakdown.md` | Tasks as you defined them to Cursor |

### Show evidence of

- **Persistent project context** — how context was provided to Cursor repeatedly
- **Iteration** — multiple refinement cycles; accepting some suggestions, rejecting others
- **Validation** — how Cursor-generated code was verified before acceptance

### Strong Cursor usage

- Wrote a design spec, shared it with Cursor, and built against it
- Used `.cursorrules` or similar to enforce project standards
- Commit history shows iterating: accepting → testing → fixing → refining
- Prompts were specific (e.g., “Generate quality check for completeness on these 3 fields”) not vague (“write data quality code”)
- Tested Cursor-generated SQL/Python/PySpark before deploying
- Rejected suggestions that didn't match architecture

### Weak Cursor usage (avoid)

- One-line prompts only; no context provided upfront
- Copying code directly without understanding it
- No evidence of testing or validation
- Prompts like “generate code” with no specification
- Missing git history or shallow commits
- No documented reasoning for accepting/rejecting suggestions

---

## 14. Required Documentation

### Root-level artifacts

| File | Purpose |
|------|---------|
| `README.md` | Setup instructions (must work end-to-end) |
| `candidate-info.md` | Candidate and environment information |
| `tool-workflow.md` | Part A AI workflow foundation |
| `requirements-analysis.md` | Problem understanding, functional/non-functional requirements, assumptions, edge cases, clarifications |
| `design-notes.md` | Architecture, data model, layer designs, DQ strategy, debugging approach |
| `data-model.md` | Data model documentation |
| `data-quality-strategy.md` | Quality checks, thresholds, metrics report approach, sample issues |
| `debugging-notes.md` | Debugging record |
| `reflection.md` | Part C reflection |
| `final-ai-usage-summary.md` | AI usage summary |

### Supporting documentation

| Location | Files |
|----------|-------|
| `src/data_generation/` | `DATA_GENERATION_NOTES.md` |
| `src/dashboard/` | `DASHBOARD_GUIDE.md` |
| `database/` | `schema.sql`, `seed-data-notes.md`, `setup-notes.md` |
| `ai-prompts/` | Per-activity prompt history (see Section 12) |
| `tool-specific/cursor-workflow/` | Cursor-specific artifacts (see Section 13) |

### Submission templates (floor, not limit)

The participant guide provides starting structures for: `candidate-info.md`, `requirements-analysis.md`, `design-notes.md`, `data-quality-strategy.md`, `ai-prompts/{activity}.md`, and `reflection.md`.

---

## 15. Submission Requirements

### What to share

1. **Link to Git repository** using **ttn email id**.
   - Same repo can be cloned to **Databricks Community Edition** (free) for development/testing/validations.
2. **Short written answers** to questions in the online submission form.

### Form questions (explain in your own words)

- Your understanding of the medallion architecture problem
- How you used AI across data generation, ingestion, validation, aggregation
- Key design and implementation decisions made through AI
- Your testing and validation approach
- How you validated AI output
- What you'd improve next

> Be specific and honest. Generic or inflated answers produce less useful feedback.

### Follow-up

- Work is reviewed and a **feedback report** is shared.
- A mentor or competency owner **may** follow up for a short coaching conversation — not a re-examination.

---

## 16. Acceptance Criteria

### Core acceptance criteria

- [ ] Sample data generated (3 CSVs with intentional issues)
- [ ] Bronze layer ingests all three sources successfully
- [ ] Silver layer implements all **four** quality checks
- [ ] Quality report shows **% passed** for each check
- [ ] Gold layer produces all **three** aggregation tables
- [ ] Aggregation calculations are correct (sum, count, avg, etc.)
- [ ] Dashboard displays all **3+** visualizations
- [ ] All code is readable, commented, documented
- [ ] README setup instructions work end-to-end
- [ ] Data quality tests pass (verify checks catch intentional issues)

### What counts as complete (submission checklist)

- [ ] Working end-to-end pipeline (Bronze → Silver → Gold → Dashboard)
- [ ] Sample data generator with realistic quality issues
- [ ] All **four** quality checks implemented and working
- [ ] All **three** Gold layer aggregations
- [ ] Dashboard with **3+** SQL queries and visualizations
- [ ] Database schema/setup script and seed data
- [ ] README with working setup instructions
- [ ] Basic test suite (data quality tests, pipeline integration tests)
- [ ] Full prompt history with all AI interactions documented
- [ ] Requirement analysis, design notes, test strategy
- [ ] Debugging notes and code review notes
- [ ] Reflection on what you learned

> If pieces are missing, feedback is still provided but growth pointers will focus on filling those gaps.

### What good looks like

**Strong work usually shows:**

- Clear requirement understanding — good breakdown of Bronze/Silver/Gold layers, acceptance criteria
- Well-documented AI prompts — context-setting, refinement, correction of wrong suggestions
- Working pipeline end-to-end — all layers function, data persists, dashboard displays correctly
- Data quality thinking — all checks work, quality report is clear, intentional issues caught
- Clean, maintainable code — readable, documented, follows naming conventions
- Meaningful testing — quality validation tests, integration tests, evidence of debugging
- Honest reflection — can explain trade-offs, show what was learned, reusable patterns documented

**Weaker work usually shows:**

- Direct copy-paste from AI — little understanding; missing requirement analysis
- Shallow prompt history — no clear design; prompts lack context
- Broken setup instructions — README doesn't work; no data persistence
- Superficial testing — no evidence quality checks catch intentional issues
- Generic documentation — can't explain the code; no ownership
- Missing artifacts — prompt history, reflection, testing, or debugging notes absent

---

## 17. Important Constraints

| Constraint | Detail |
|------------|--------|
| **Not graded** | Development exercise; feedback and growth path, not a grade |
| **Time box** | **3 weeks**, self-paced |
| **Core effort** | **20–25 focused hours** for mandatory Core |
| **Artifacts over scope** | Do not expand pipeline complexity at the expense of lifecycle artifacts |
| **Everyone participates** | Shared competency exercise; shared baseline |
| **No deployment required** | No review call to book; nothing to host or deploy for submission |
| **Databricks target** | Databricks Community Edition or other; languages: Python, PySpark, SQL; libraries noted in guide: PySpark, Delta Lake, pandas |
| **PII caution** | Avoid sharing real customer PII unnecessarily with AI tools (per `tool-workflow.md` expectation) |
| **Honesty** | Specific, honest answers; journey and understanding matter as much as final code |

---

## 18. Ambiguities That Require an Engineering Decision

The following items are **not fully specified** in the assignment. Document decisions in `requirements-analysis.md`, `design-notes.md`, or `data-quality-strategy.md` before implementing.

| # | Ambiguity | What the assignment says | Decision needed |
|---|-----------|--------------------------|-----------------|
| 1 | **Number of Silver quality checks** | Silver section details **3** check categories (completeness, uniqueness, referential integrity). Common technical requirements and acceptance criteria require **4** quality checks. Repository structure lists **5** silver scripts (`type_validation`, `business_logic` in addition to the three above). | Which fourth check satisfies “all 4 quality checks”? What do `03_quality_type_validation.py` and `05_quality_business_logic.py` validate? |
| 2 | **Number of Gold aggregations** | Gold section specifies **3** aggregation tables (Sales by Product, Revenue by Customer, Customer Segmentation). Common technical requirements mention **all 4 aggregations**. Repository structure includes **`03_daily_weekly_trends.sql`** in addition to the three named tables. | Is `daily_weekly_trends` a required fourth aggregation, or optional/stretch? |
| 3 | **Customer segmentation logic** | Gold table C uses `segment_type` values **`High-Value` / `Repeat` / `One-Time` / `Inactive`**. Source `customers.customer_segment` uses **`Premium` / `Standard` / `Basic`**. Assignment does not define rules mapping orders/customers to the four `segment_type` values. | Define segmentation criteria (thresholds, time windows, order counts, revenue cutoffs, etc.). |
| 4 | **`lifetime_value_actual` calculation** | Gold table B includes `lifetime_value_actual` alongside source `lifetime_value`. Assignment does not define how `lifetime_value_actual` is computed vs. source `lifetime_value`. | Define whether this is sum of order revenue, reconciled against source field, or another rule. |
| 5 | **Silver “clean and validate” vs. flag-only** | Business context says Silver should “clean and validate data.” Silver requirements say **flag bad rows, don't delete** and add `quality_check_result`. | Clarify whether “cleaning” means producing separate valid/invalid datasets, quarantine tables, or only flagging in place. |
| 6 | **Uniqueness scope on `customer_id`** | Uniqueness check lists both `order_id` and `customer_id`. Source schema marks `customer_id` as PK on customers but FK on orders (many orders per customer expected). | Confirm uniqueness applies to `customer_id` in **customers** only and `order_id` in **orders** only, not globally across joined data. |
| 7 | **S3 vs. DBFS paths** | Sources described as S3/DBFS CSVs; Community Edition may not mirror production S3 layout. | Choose concrete paths and document in README/setup for local, DBFS, or Community Edition constraints. |
| 8 | **Delta Lake vs. other table formats** | Guide lists Delta Lake as a library; Bronze/Silver/Gold sections do not explicitly mandate Delta. | Decide table format (Delta recommended by stack) and document in `design-notes.md`. |
| 9 | **Dashboard filters** | Assignment requires filters but does not specify which dimensions (date range, category, segment, country, etc.). | Choose filter fields aligned with Gold outputs and dashboard tiles. |
| 10 | **“Code review notes”** | Listed in “what counts as complete” but no dedicated template file in repository structure. | Decide where code review notes live (`debugging-notes.md`, separate file, or PR/commit commentary exported to repo). |

---

*Last updated from participant guide: AI Capability Exercise — Build & Grow Your AI Workflow.*
