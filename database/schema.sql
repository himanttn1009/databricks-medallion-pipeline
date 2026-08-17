-- Database Schema Reference
-- Databricks Medallion Pipeline
--
-- Tables are created by pipeline Python scripts (Delta Lake).
-- This file documents schema names and table inventory.
-- Authoritative column definitions: data-model.md

-- =============================================================================
-- Schemas (created by pipeline scripts)
-- =============================================================================

-- CREATE SCHEMA IF NOT EXISTS bronze;
-- CREATE SCHEMA IF NOT EXISTS silver;
-- CREATE SCHEMA IF NOT EXISTS gold;
-- CREATE SCHEMA IF NOT EXISTS audit;

-- =============================================================================
-- Bronze (src/bronze/) — raw CSV landing
-- =============================================================================
-- bronze.customers   (10,000 rows)
-- bronze.products    (500 rows)
-- bronze.orders      (100,000 rows)
-- audit.ingestion_log (append per ingest run)

-- =============================================================================
-- Silver (src/silver/) — DQ flags + metrics
-- =============================================================================
-- silver.customers    (all Bronze columns + quality_check_result, is_valid, _silver_processed_timestamp)
-- silver.products
-- silver.orders
-- silver.dq_metrics   (10 rows per run_id)

-- =============================================================================
-- Gold (src/gold/) — business aggregations
-- =============================================================================
-- gold.sales_by_product        (500 rows)
-- gold.revenue_by_customer     (9,940 rows)
-- gold.customer_segmentation   (4 rows)
-- gold.daily_weekly_trends     (2,679 rows — DAILY + WEEKLY)

-- =============================================================================
-- Dashboard (src/dashboard/) — read-only queries against gold.*
-- =============================================================================
-- No tables created. See dashboard_queries.sql.
