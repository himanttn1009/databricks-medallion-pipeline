# Candidate Information

**Name:** Himanshu Kumar  
**Role:** SE  
**Primary Technology Stack:** Python / PySpark, SQL, Databricks  
**Primary AI Tool Used:** Cursor  
**Project Option Selected:** Data Pipeline (Medallion Architecture)  
**Assessment Start Date:** 12 August 2026  
**Submission Date:** 18 August 2026

## Tools & Environment

- Databricks: Free Edition (Unity Catalog, Serverless)
- Languages: Python, PySpark, SQL
- Libraries: PySpark, Delta Lake, pandas, Faker
- AI Tool: Cursor

## Setup Summary

| Step | Action | Doc reference |
|------|--------|---------------|
| 1 | Generate CSVs locally | `src/data_generation/generate_sample_data.py` |
| 2 | Upload to UC volume `/Volumes/workspace/default/medallion_data/` | `database/seed-data-notes.md` |
| 3 | Run Bronze ingest | `src/bronze/ingest_all.py` |
| 4 | Run Silver DQ | `src/silver/create_silver_tables.py` |
| 5 | Run Gold aggregations | `src/gold/create_gold_tables.py` |
| 6 | Build dashboard manually | `src/dashboard/DASHBOARD_GUIDE.md` |

Full setup: `README.md`

## Pipeline Status

| Layer | Status |
|-------|--------|
| Data generation | Complete + validated |
| Bronze | Complete + runtime validated |
| Silver | Complete + runtime validated |
| Gold | Complete + runtime validated |
| Dashboard | Complete (SQL + manual UI) |
| Automated tests | Not implemented |
