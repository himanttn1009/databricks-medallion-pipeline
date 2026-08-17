# Supplementary Documentation

Additional documentation supporting the assessment submission.

## Core Planning & Design

| Document | Purpose |
|----------|---------|
| `assignment/assignment-requirements.md` | Assignment source of truth |
| `requirements-analysis.md` | Requirements, ambiguities, acceptance criteria |
| `design-notes.md` | Architecture, layer designs (§4 Silver, §5 Gold, §6 Dashboard) |
| `data-model.md` | Entity schemas and relationships |
| `data-quality-strategy.md` | DQ rules, thresholds, defect inventory |

## Layer Module Documentation

| Layer | Location |
|-------|----------|
| Data generation | `src/data_generation/README.md`, `DATA_GENERATION_NOTES.md` |
| Bronze | `src/bronze/README.md` |
| Silver | `src/silver/README.md` |
| Gold | `src/gold/README.md` |
| Dashboard | `src/dashboard/README.md`, `DASHBOARD_GUIDE.md` |

## AI Workflow & Assessment Artifacts

| Document | Purpose |
|----------|---------|
| `tool-workflow.md` | Part A — AI workflow across lifecycle |
| `reflection.md` | Part C — what was built and lessons learned |
| `final-ai-usage-summary.md` | High-level AI usage summary |
| `debugging-notes.md` | Issues, root causes, resolutions |
| `candidate-info.md` | Candidate and environment details |
| `tool-specific/cursor-workflow/` | Cursor rules, spec, task breakdown |

## AI Prompt History

See `ai-prompts/README.md` for the full index.

| File | Activity |
|------|----------|
| `ai-prompts/04-data-generation.md` | Data generation |
| `ai-prompts/05-bronze-layer.md` | Bronze layer |
| `ai-prompts/06-silver-layer.md` | Silver layer |
| `ai-prompts/07-gold-layer.md` | Gold layer |
| `ai-prompts/08-dashboard-layer.md` | Dashboard layer |
| `ai-prompts/debugging.md` | Debugging |
| `ai-prompts/documentation.md` | Documentation |

## Database & Seed Data

| Document | Purpose |
|----------|---------|
| `database/schema.sql` | Schema reference (tables created by pipeline scripts) |
| `database/setup-notes.md` | Databricks environment setup |
| `database/seed-data-notes.md` | CSV generation and upload |
| `data/README.md` | Seed data file inventory |

## Test Strategy

Automated tests: `tests/test_data_quality.py` validates seed CSV defect counts. See `tests/README.md`.

Design-level testing strategy: `design-notes.md` — Testing Strategy section.
