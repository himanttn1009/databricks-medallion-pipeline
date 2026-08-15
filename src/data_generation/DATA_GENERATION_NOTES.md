# Data Generation Notes

> **Design:** Approved specification (this document).  
> **Implementation:** Complete — `src/data_generation/generate_sample_data.py`  
> **Runtime validation:** **Executed successfully** — generator internal validation and independent CSV validation passed (see Runtime Validation Results)  
> **Output:** `data/customers.csv`, `data/products.csv`, `data/orders.csv`  
> **Dependencies:** `requirements-data-generation.txt`  
> **Related docs:** `data-quality-strategy.md`, `data-model.md`, `design-notes.md`

| Phase | Status |
|-------|--------|
| **Design** | Approved — defect counts, pools, business rules, and layer contracts defined here |
| **Implementation** | Complete — generator script implements the design |
| **Runtime validation** | Complete — generator exit code 0; independent CSV analysis confirms expected counts |

---

## 1. Generation Approach

The generator follows a **generate clean → inject defects → validate → write** pipeline.

| Phase | Action |
|-------|--------|
| **1. Clean generation** | Produce realistic rows that satisfy schema, type rules, and referential integrity |
| **2. Defect injection** | Mutate **pre-selected disjoint row indices** to introduce exact assignment-specified defect counts |
| **3. Validation** | Assert exact row counts and exact per-defect counts; fail fast before writing CSVs if any assertion fails |
| **4. Write** | Output CSV files to `data/` (default) with Python `None` represented as empty CSV fields |

**Principles:** correctness, reproducibility, realistic data, testability, and simplicity. No unnecessary complexity.

**Two-phase per file:** clean data is generated first so that ~99%+ of rows are analytics-ready; defects are applied only on reserved pools.

---

## 2. Dataset Sizes

| File | Target row count | Approx. file size (assignment) |
|------|------------------|--------------------------------|
| `customers.csv` | **10,000** | ~500 KB |
| `products.csv` | **500** | ~50 KB |
| `orders.csv` | **100,000** | ~2–3 MB |

Final CSVs must contain **exactly** these row counts, including defective rows.

---

## 3. Generation Order

Generation is **dependency-driven**:

```
1. products.csv   (500 rows)    — no foreign key dependencies
2. customers.csv (10,000 rows) — no foreign key dependencies
3. orders.csv   (100,000 rows) — references customers and products
```

Orders are generated last so that valid `customer_id` and `product_id` values can be sampled from existing parent ID pools. Orphan FK defects use ghost ID ranges that are never inserted into parent files.

---

## 4. Libraries and Dependencies

| Library | Purpose |
|---------|---------|
| `faker` | Realistic synthetic names, emails, and text (no real PII) |
| `random` | Weighted distributions, sampling, index shuffling |
| `datetime` / `date` | `signup_date`, `order_date`, `payment_date` generation |
| `csv` | CSV file output (standard library `csv.DictWriter`) |
| explicit rounding | Monetary fields rounded to two decimal places via `round_money()` |

### Pinned Faker dependency

| Constant / file | Value |
|-----------------|-------|
| `FAKER_VERSION` | **40.36.0** |
| `FAKER_LOCALE` | **en_US** |
| Dependency file | `requirements-data-generation.txt` |

Install:

```bash
pip install -r requirements-data-generation.txt
```

The implementation instantiates Faker as `Faker(FAKER_LOCALE)` with `Faker.seed()` and `fake.seed_instance()` using the master random seed. Faker output can vary across package versions; the pinned version above is required for reproducibility.

**Not required:** PySpark for local generation — dataset size (~110,500 rows) is suitable for a standalone Python script.

---

## 5. Referential Integrity Strategy

### 5.1 Valid references (clean rows)

| Child column | Valid parent set |
|--------------|------------------|
| `orders.customer_id` | `customer_id` values present in `customers.csv` (1–10,000 on clean rows) |
| `orders.product_id` | `product_id` values present in `products.csv` (1–500) |

### 5.2 Invalid references (orphan defects)

Orphan defects require **non-null** foreign key values that do **not** exist in parent tables. See Section 14 for ghost ID ranges.

| Defect | Count | Rule |
|--------|-------|------|
| Orphan `customer_id` | 50 | Non-null `customer_id` not in `customers.csv` |
| Orphan `product_id` | 30 | Non-null `product_id` not in `products.csv` |

### 5.3 NULL foreign keys (completeness defects)

| Defect | Count | Rule |
|--------|-------|------|
| NULL `customer_id` | 100 | `customer_id = None`; `product_id` remains valid |
| NULL `product_id` | 200 | `product_id = None`; `customer_id` remains valid |

NULL and orphan pools are **disjoint** — a row cannot be both NULL and orphan for the same foreign key column.

### 5.4 Order dates vs customer signup

For orders with a **valid, non-null** `customer_id`:

```
customer.signup_date <= order.order_date <= REFERENCE_DATE
```

`REFERENCE_DATE` is a **fixed calendar date** (`2026-08-15`), not the system clock. This replaces any dynamic `date.today()` upper bound so that signup dates, order dates, and payment-date capping produce **identical output across calendar days** when seed and dependency versions are held constant.

Defect rows with NULL `customer_id` skip the signup join at generation time but still receive a plausible `order_date` bounded by `REFERENCE_DATE`.

---

## 6. Defect Injection Strategy

### 6.1 Approach

1. Define all defect counts as **named constants** (see Section 7).
2. Build a shuffled list of row indices per entity using a **fixed random seed**.
3. **Reserve disjoint index pools** for each defect type in a fixed allocation order.
4. Verify pools do not intersect before applying mutations.
5. Generate clean data for all rows.
6. Apply mutations only on reserved indices.
7. Run validation (Section 13) before writing CSVs.

### 6.2 Disjoint pools

Defect pools are kept **disjoint wherever possible** so each required defect count can be independently validated by Silver data quality tests.

#### Customers (10,000 rows)

| Pool | Defect | Rows |
|------|--------|------|
| A | NULL `email` | 50 |
| B | Duplicate `customer_id` (5 pairs) | 10 |
| Clean | — | 9,940 |

`A ∩ B = ∅`

#### Orders (100,000 rows)

| Pool | Defect | Rows |
|------|--------|------|
| C | NULL `customer_id` | 100 |
| D | NULL `product_id` | 200 |
| E | Orphan `customer_id` | 50 |
| F | Orphan `product_id` | 30 |
| G | Duplicate `order_id` (10 pairs) | 20 |
| Clean | — | 99,600 |

All pools C–G are pairwise disjoint.

#### Products (500 rows)

No intentional defects. All rows are clean.

### 6.3 Duplicate row behavior

For duplicate PK defects, only the **primary key is copied** between paired rows; other attributes may differ to simulate realistic key collisions. **All rows** participating in a duplicate group are counted toward the defect total and expected to be flagged by Silver uniqueness checks.

When duplicate `customer_id` rows exist, `build_customer_lookup()` uses the **first encountered row** for order generation and signup-date validation.

---

## 7. Exact Defect Counts

These are the **acceptance criteria** for the generator. Each count is implemented exactly — **no additional defects** are introduced to approximate the assignment's ~700 narrative figure.

| # | File | Defect | Count | Silver check |
|---|------|--------|-------|--------------|
| 1 | `customers.csv` | NULL `email` | **50** | Completeness |
| 2 | `customers.csv` | Duplicate `customer_id` | **10 rows** in duplicate groups | Uniqueness |
| 3 | `orders.csv` | NULL `customer_id` | **100** | Completeness |
| 4 | `orders.csv` | NULL `product_id` | **200** | Completeness |
| 5 | `orders.csv` | Invalid `customer_id` (orphan) | **50** | Referential integrity |
| 6 | `orders.csv` | Invalid `product_id` (orphan) | **30** | Referential integrity |
| 7 | `orders.csv` | Duplicate `order_id` | **20 rows** in duplicate groups | Uniqueness |

**Total explicit defect-participating rows: 460**

| Entity | Defect rows |
|--------|-------------|
| Customers | 60 (50 + 10) |
| Orders | 400 (100 + 200 + 50 + 30 + 20) |
| Products | 0 |
| **Total** | **460** |

### Implemented named constants

```text
RANDOM_SEED                  = 42
REFERENCE_DATE               = 2026-08-15
FAKER_LOCALE                 = en_US

CUSTOMER_ROW_COUNT           = 10_000
PRODUCT_ROW_COUNT            = 500
ORDER_ROW_COUNT              = 100_000

NULL_EMAIL_COUNT             = 50
DUPLICATE_CUSTOMER_ID_ROWS   = 10
DUPLICATE_CUSTOMER_ID_PAIRS  = 5
NULL_ORDER_CUSTOMER_ID       = 100
NULL_ORDER_PRODUCT_ID        = 200
ORPHAN_CUSTOMER_ID_COUNT     = 50
ORPHAN_PRODUCT_ID_COUNT      = 30
DUPLICATE_ORDER_ID_ROWS      = 20
DUPLICATE_ORDER_ID_PAIRS     = 10

TOTAL_EXPLICIT_DEFECT_ROWS   = 460
```

---

## 8. The 460 vs Approximately 700 Discrepancy

### What the assignment states

| Source | Figure |
|--------|--------|
| Seven explicitly itemized defect types | **460 rows** (sum of counts in Section 7) |
| Assignment total narrative | **~700 problematic rows** (~0.7% of ~100,000) |

### Engineering decision (final)

**Explicit defect counts are the acceptance criteria.**

- Implement every specified defect count **exactly** as itemized (460 total).
- **Do not** invent additional unspecified defects to approximate 700.
- The gap between 460 and ~700 (~240 rows) is **not explained** by additional specified defect types in the assignment.

### Rationale

| Reason | Detail |
|--------|--------|
| Testability | Silver DQ tests assert specific counts per defect type; inventing extra defects would obscure validation |
| Traceability | Each defect maps to a named check in `data-quality-strategy.md` |
| Honesty | Document the discrepancy rather than silently fabricating data |

**Runtime validation status:** Generator executed successfully; observed counts recorded in **Runtime Validation Results**.

---

## 9. Duplicate ID Definitions

### 9.1 Duplicate `customer_id`

| Attribute | Specification |
|-----------|---------------|
| Structure | **5 duplicate pairs** (`DUPLICATE_CUSTOMER_ID_PAIRS = 5`) |
| Rows participating | **10 rows** total (`DUPLICATE_CUSTOMER_ID_ROWS = 10`) |
| Mechanism | 5 distinct `customer_id` values each appear on **exactly 2 rows** |
| Implementation validation | `validate_duplicate_pair_structure()` asserts exactly 5 duplicate keys, each with frequency 2 |
| Silver uniqueness expectation | All **10 rows** in duplicate groups flagged with `UNIQUENESS` |
| Pool overlap | Disjoint from NULL `email` pool |

### 9.2 Duplicate `order_id`

| Attribute | Specification |
|-----------|---------------|
| Structure | **10 duplicate pairs** (`DUPLICATE_ORDER_ID_PAIRS = 10`) |
| Rows participating | **20 rows** total (`DUPLICATE_ORDER_ID_ROWS = 20`) |
| Mechanism | 10 distinct `order_id` values each appear on **exactly 2 rows** |
| Implementation validation | `validate_duplicate_pair_structure()` asserts exactly 10 duplicate keys, each with frequency 2 |
| Silver uniqueness expectation | All **20 rows** in duplicate groups flagged with `UNIQUENESS` |
| Pool overlap | Disjoint from NULL FK, orphan FK, and other order defect pools |

---

## 10. NULL Representation

### 10.1 During generation (Python)

| Rule | Detail |
|------|--------|
| Missing values | Represented as Python **`None` only** |
| Empty strings | **Not** used to represent NULL |
| Equivalence | Empty string (`""`) is **not** treated as inherently equivalent to NULL |

### 10.2 CSV output

| Rule | Detail |
|------|--------|
| `None` → CSV | Written as an **empty field** (empty CSV cell) via `format_cell()` |
| Convention | Documented here for Bronze ingestion design |

### 10.3 Bronze ingestion (downstream requirement)

The Bronze CSV reader must be **explicitly configured** so that empty fields are interpreted as NULL (e.g. Spark `nullValue` / empty-string handling). This is a Bronze design responsibility, not the generator's — but the contract between layers is:

```
Python None  →  empty CSV field  →  NULL in Bronze/Delta
```

Bronze must **explicitly** interpret empty fields as NULL. Silver completeness checks evaluate true SQL/DataFrame NULLs after Bronze ingest.

---

## 11. Reproducibility Strategy

| Mechanism | Implemented value / behavior |
|-----------|------------------------------|
| Master seed | `RANDOM_SEED = 42` |
| `random.Random()` | Isolated seeded instance for all stdlib random operations |
| `Faker.seed()` / `seed_instance()` | Called before Faker use |
| Faker locale | `FAKER_LOCALE = en_US` |
| Faker version | `FAKER_VERSION = 40.36.0` (see `requirements-data-generation.txt`) |
| Reference date | `REFERENCE_DATE = 2026-08-15` — fixed upper bound for all date generation (replaces `date.today()`) |
| Index shuffling | Seeded shuffle for defect pool allocation |
| Output ordering | Rows sorted by primary key before CSV write (see Section 11.1) |
| CLI override | `--reference-date` accepts ISO date string (default: `2026-08-15`) |

**Expected behavior:** Same seed + same constants + same `REFERENCE_DATE` + same Faker version and locale → identical CSV output across runs and calendar days.

**Runtime validation status:** Reproducibility confirmed by successful generator execution on **2026-08-15** with `REFERENCE_DATE = 2026-08-15` (see **Runtime Validation Results**).

### 11.1 Deterministic sorting before CSV output

Before writing, datasets are sorted by primary key for stable diffs:

| File | Sort key |
|------|----------|
| `customers.csv` | `customer_id` |
| `products.csv` | `product_id` |
| `orders.csv` | `order_id` |

### 11.2 Temporary-file CSV writing

Each CSV is written using a **write-then-replace** pattern:

1. Write content to a sibling temporary file (e.g. `customers.csv.tmp`).
2. On success, atomically replace the final path via `Path.replace()`.
3. On failure during the write, delete the temporary file if it exists and re-raise the exception.

This avoids leaving a truncated file at the final path when a single-file write fails. Validation runs **before** any CSV write; if validation fails, no files are written.

**Note:** The three output files are written sequentially. A failure on a later file does not roll back earlier successfully replaced files.

---

## 12. Order Business Rules

These rules apply to **all order rows** unless a defect explicitly targets a field (none of the seven specified defects target `total_amount` or `payment_date`).

### 12.1 `total_amount`

```
total_amount = round(quantity * unit_price, 2)
```

Always computed programmatically. Never hand-authored.

### 12.2 `order_status` and `payment_date`

| `order_status` | `payment_date` |
|----------------|----------------|
| **Completed** | **Not None** — set to `order_date` or `order_date + 0–3 days` (deterministic from seeded RNG); capped at `REFERENCE_DATE` |
| **Pending** | `None` |
| **Cancelled** | `None` |

Status mix: approximately 70% Completed, 20% Pending, 10% Cancelled.

### 12.3 `order_date` vs `signup_date`

For orders with valid, non-null `customer_id`:

```
signup_date <= order_date <= REFERENCE_DATE
```

`REFERENCE_DATE = 2026-08-15` is used instead of the system date to ensure reproducibility.

### 12.4 Realistic clean-row characteristics

| Field | Behavior |
|-------|----------|
| `unit_price` | Approximately product catalog `price` with small variance |
| `quantity` | Positive integer (1–5 typical) |
| Enums | `order_status` ∈ {`Pending`, `Completed`, `Cancelled`} |

---

## 13. Validation Strategy

### 13.1 Pre-write validation (implemented in generator)

`validate_generated_data()` runs **before** CSV files are written. On any failure, the script prints diagnostic counts and exits non-zero without writing output.

| Assertion | Expected value |
|-----------|----------------|
| Customer row count | 10,000 |
| Product row count | 500 |
| Order row count | 100,000 |
| NULL `email` count | 50 |
| Rows in duplicate `customer_id` groups | 10 |
| Duplicate `customer_id` structure | Exactly **5** keys, each appearing **twice** |
| NULL `customer_id` count | 100 |
| NULL `product_id` count | 200 |
| Orphan `customer_id` count (non-null, not in parents) | 50 |
| Orphan `product_id` count (non-null, not in parents) | 30 |
| Rows in duplicate `order_id` groups | 20 |
| Duplicate `order_id` structure | Exactly **10** keys, each appearing **twice** |
| Total explicit defect rows | 460 |
| Disjoint pools | No index appears in more than one pool |
| `total_amount` | Equals `round(quantity * unit_price, 2)` on all rows |
| Completed orders | `payment_date` is not None |
| Date bounds | `signup_date` and `order_date` not after `REFERENCE_DATE` |
| Clean-row type rules | Valid enums; non-negative numerics |

**Runtime validation status:** Confirmed by successful generator execution and independent CSV validation (see **Runtime Validation Results**).

### 13.2 Post-write documentation

Observed counts and validation outcomes are recorded in **Runtime Validation Results** below.

### 13.3 Downstream validation (later pipeline phases)

| Phase | Planned validation |
|-------|-------------------|
| Bronze | Row counts match CSV line counts; empty fields ingested as NULL |
| Silver | `tests/test_data_quality.py` asserts defect detection per `data-quality-strategy.md` |
| Gold | Non-zero revenue; segmentation segments populated |

**Runtime validation status:** The generator has been executed successfully. Actual observed counts are recorded in **Runtime Validation Results**.

---

## Runtime Validation Results

> Observed values from generator execution (internal pre-write validation) and independent CSV analysis. Empty CSV fields were treated as NULL during independent validation.

| Field | Value |
|-------|-------|
| **Validation date** | **2026-08-15** |
| **Execution status** | **Success** — generator exit code **0**; CSV files written to `data/` |
| **Reference date used** | **2026-08-15** (`REFERENCE_DATE`) |
| **Output files** | `data/customers.csv`, `data/products.csv`, `data/orders.csv` |

### Actual row counts

| File | Observed rows |
|------|---------------|
| `customers.csv` | **10,000** |
| `products.csv` | **500** |
| `orders.csv` | **100,000** |

### Actual defect counts

| # | Defect | Expected | Observed (generator) | Observed (independent CSV) |
|---|--------|----------|----------------------|----------------------------|
| 1 | NULL `email` | 50 | 50 | 50 |
| 2 | Duplicate `customer_id` participant rows | 10 | 10 | 10 |
| 3 | NULL order `customer_id` | 100 | 100 | 100 |
| 4 | NULL order `product_id` | 200 | 200 | 200 |
| 5 | Orphan `customer_id` | 50 | 50 | 50 |
| 6 | Orphan `product_id` | 30 | 30 | 30 |
| 7 | Duplicate `order_id` participant rows | 20 | 20 | 20 |
| | **Total explicit defect-participating rows** | **460** | **460** | **460** |

Generator internal validation summary (pre-write):

```
reference_date: 2026-08-15
customers: 10,000 rows
products:  500 rows
orders:    100,000 rows
NULL email: 50
duplicate customer_id participants: 10
NULL order customer_id: 100
NULL order product_id: 200
orphan customer_id: 50
orphan product_id: 30
duplicate order_id participants: 20
total explicit defect rows: 460
```

### Duplicate-pair validation

**Customers — observed duplicate `customer_id` values: 5 (10 participant rows)**

| `customer_id` | Frequency |
|---------------|-----------|
| 1242 | 2 |
| 4532 | 2 |
| 5251 | 2 |
| 5582 | 2 |
| 7797 | 2 |

**Orders — observed duplicate `order_id` values: 10 (20 participant rows)**

| `order_id` | Frequency |
|------------|-----------|
| 4543 | 2 |
| 8111 | 2 |
| 14831 | 2 |
| 19631 | 2 |
| 38452 | 2 |
| 51775 | 2 |
| 58339 | 2 |
| 63560 | 2 |
| 98467 | 2 |
| 98650 | 2 |

All observed duplicate keys appeared **exactly twice** (pair structure confirmed).

**Products:** duplicate `product_id` values observed: **0**.

### Referential-integrity validation

Independent CSV analysis (non-null FK not in parent file):

| Check | Expected | Observed |
|-------|----------|----------|
| Orphan `customer_id` | 50 | **50** |
| Orphan `product_id` | 30 | **30** |
| Duplicate `product_id` in products | 0 | **0** |

Orphan defects used ghost ranges documented in Section 14. NULL FK rows were excluded from orphan counts (empty `customer_id` / `product_id` fields in CSV).

### Business-rule validation

Independent CSV analysis:

| Rule | Violations observed |
|------|---------------------|
| `order_status` ∈ {Completed, Pending, Cancelled} | **0** |
| `price > cost` (all products) | **0** |
| `total_amount = round(quantity × unit_price, 2)` | **0** |
| Completed orders → `payment_date` present | **0** |
| Pending/Cancelled orders → `payment_date` empty | **0** |
| `signup_date` / `order_date` not after `2026-08-15` | **0** |
| Valid-FK `order_date >= signup_date` (first customer row per `customer_id`) | **0** |

**Observed `order_status` distribution:** Completed **70,251**; Pending **19,918**; Cancelled **9,831**.

**Duplicate-customer signup note (observed):** `customer_id` **5251** appears on two customer rows with signup dates `2021-01-27` and `2024-07-29`. Under first-row signup lookup (generator behavior), **0** order-date violations were observed. Checking against **all** rows sharing `customer_id` 5251, **12** orders had `order_date` before `2024-07-29` — consistent with documented first-wins duplicate-customer semantics, not a defect-count mismatch.

### Execution status

| Step | Result |
|------|--------|
| Generator `validate_generated_data()` (pre-write) | **Passed** |
| CSV files written | **Yes** — `data/customers.csv`, `data/products.csv`, `data/orders.csv` |
| Generator exit code | **0** |
| Independent CSV validation | **Passed** — observed counts and business rules match specification |

---

## 14. Ghost ID Ranges

Ghost IDs are used **only** for orphan referential integrity defects. They are **never** inserted into parent CSV files.

| Column | Ghost range | Count | Parent file |
|--------|-------------|-------|-------------|
| `customer_id` | **90,001 – 90,050** | 50 | `customers.csv` (IDs 1–10,000 only) |
| `product_id` | **901 – 930** | 30 | `products.csv` (IDs 1–500 only) |

Ghost ranges are disjoint from valid parent ID domains and from NULL FK defect rows.

---

## 15. Edge Cases

| # | Edge case | Handling |
|---|-----------|----------|
| 1 | 460 vs ~700 total | Document discrepancy; do not fabricate extra defects (Section 8) |
| 2 | `""` vs NULL | `None` only in Python; Bronze maps empty CSV → NULL (Section 10) |
| 3 | Duplicate group counting | All 10 customer / 20 order rows in groups count as duplicate participants |
| 4 | Duplicate pair structure | Validation requires exactly 5 / 10 keys each with frequency 2 — not merely participant row totals |
| 5 | NULL + orphan on same FK | Prevented by disjoint pools |
| 6 | NULL `customer_id` + NULL `product_id` on same row | Prevented — separate pools (100 + 200 on distinct rows) |
| 7 | Orphan + duplicate on same row | Prevented — disjoint pools |
| 8 | Duplicate rows with different attributes | Copy PK only; other fields may differ |
| 9 | Order before customer signup | Rejected for rows with valid `customer_id` during validation |
| 10 | Completed order without `payment_date` | Not allowed — all Completed rows get `payment_date` |
| 11 | Float money precision | Always `round(..., 2)` for `total_amount` |
| 12 | CSV special characters | Proper CSV quoting via standard `csv` writer |
| 13 | Faker version drift | Pinned in `requirements-data-generation.txt` (`FAKER_VERSION = 40.36.0`) |
| 14 | Calendar-day reproducibility | `REFERENCE_DATE` replaces `date.today()` for all date upper bounds |
| 15 | Customer with zero orders | Allowed — supports Inactive segmentation in Gold |
| 16 | Product with zero orders | Allowed — zero revenue in Gold is valid |
| 17 | Type/business logic on defect rows | No defects target amount arithmetic or payment fields; all rows should pass BR-01 and Completed payment rules |
| 18 | Partial multi-file write | Per-file temp write protects against truncated single files; earlier files may remain if a later write fails |

---

## 16. Final Engineering Decisions

| ID | Decision | Status |
|----|----------|--------|
| **FD-01** | Explicit defect counts are the acceptance criteria — implement exactly **460** itemized defects; do not invent defects to reach ~700 | **Final** |
| **FD-02** | Document 460 vs ~700 discrepancy in this file (Section 8) | **Final** |
| **FD-03** | Duplicate `customer_id`: **5 pairs, 10 rows**; uniqueness validation counts all 10 | **Final** |
| **FD-04** | Duplicate `order_id`: **10 pairs, 20 rows**; uniqueness validation counts all 20 | **Final** |
| **FD-05** | NULL = Python **`None` only**; empty strings are not used to represent NULL | **Final** |
| **FD-06** | CSV: `None` → empty field; Bronze reader must configure empty → NULL | **Final** |
| **FD-07** | Defect pools disjoint wherever possible for independent validation | **Final** |
| **FD-08** | Fixed random seed for full reproducibility | **Final** |
| **FD-09** | `order_date >= customer.signup_date` for valid-FK orders | **Final** |
| **FD-10** | `total_amount = round(quantity × unit_price, 2)` on all rows | **Final** |
| **FD-11** | Completed → non-null `payment_date`; Pending/Cancelled → `None` | **Final** |
| **FD-12** | Orphan FKs use ghost ranges 90,001–90,050 and 901–930 | **Final** |
| **FD-13** | Products: no intentional defects | **Final** |
| **FD-14** | Row counts: exactly 10,000 / 500 / 100,000 | **Final** |
| **FD-15** | Generator validates exact counts before write; fail fast on mismatch | **Final** |
| **FD-16** | Avoid unnecessary complexity; prioritize correctness, reproducibility, realism, testability | **Final** |
| **FD-17** | `REFERENCE_DATE = 2026-08-15` replaces `date.today()` for reproducibility across calendar days | **Final** |
| **FD-18** | Sort by primary key before CSV write; use temp-file write-then-replace per output file | **Final** |
| **FD-19** | Pin Faker `40.36.0` with locale `en_US` in `requirements-data-generation.txt` | **Final** |

---

## Appendix — Defect Pool Summary

```
CUSTOMERS  [10,000]
  Pool A:   50  →  email = None
  Pool B:   10  →  5 duplicate customer_id pairs
  Clean:  9,940

PRODUCTS   [500]
  Clean:    500

ORDERS     [100,000]
  Pool C:  100  →  customer_id = None
  Pool D:  200  →  product_id = None
  Pool E:   50  →  customer_id = ghost 90001–90050
  Pool F:   30  →  product_id = ghost 901–930
  Pool G:   20  →  10 duplicate order_id pairs
  Clean: 99,600

TOTAL EXPLICIT DEFECT ROWS: 460
```

---

*Document version: 1.2 — design approved; implementation complete; runtime validation recorded 2026-08-15.*
