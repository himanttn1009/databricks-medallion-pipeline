# Databricks Medallion Pipeline

AI Capability Assessment — production-oriented medallion architecture pipeline for e-commerce sales data.

## Overview

```
Source CSVs → Bronze → Silver → Gold → Databricks SQL Dashboard
```

## Status

Repository scaffold in place. Pipeline implementation pending.

## Prerequisites

- Databricks (Community Edition or other)
- Python, PySpark, SQL
- Delta Lake

## Project References

- Assignment requirements: `assignment/assignment-requirements.md`
- Engineering rules: `.cursor/rules/project-engineering.mdc`

## Repository Layout

| Path | Purpose |
|------|---------|
| `src/data_generation/` | Sample CSV generator |
| `src/bronze/` | Raw ingestion |
| `src/silver/` | Data quality and validation |
| `src/gold/` | Business aggregations |
| `src/dashboard/` | Dashboard SQL and guide |
| `data/` | Generated CSV seed data |
| `database/` | Schema and setup scripts |
| `tests/` | Data quality and pipeline tests |
| `docs/` | Supplementary documentation |
| `ai-prompts/` | AI interaction history |
| `assignment/` | Assignment source of truth |

## Setup Instructions

_To be completed once the pipeline is implemented._

## Running the Pipeline

_To be completed once the pipeline is implemented._
