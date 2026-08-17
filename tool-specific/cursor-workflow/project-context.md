# Cursor Project Context

## How Project Context Is Provided to Cursor

1. **Workspace rules** — `.cursor/rules/project-engineering.mdc` is always applied; defines medallion boundaries, DQ principles, and incremental workflow.
2. **Assignment anchor** — Each layer interaction starts by inspecting `assignment/assignment-requirements.md`.
3. **Planning docs** — `requirements-analysis.md`, `design-notes.md`, `data-model.md`, `data-quality-strategy.md` provide schemas, decisions, and acceptance criteria.
4. **Prior layer READMEs** — Downstream layers read upstream module docs (e.g., Silver reads Bronze README for runtime lessons).
5. **Explicit prompt constraints** — Each interaction specifies: design-only vs implementation, allowed file paths, forbidden layer modifications, and whether runtime claims are permitted.
6. **AI prompt history** — `ai-prompts/04–08` files provide continuity across interactions.

## Persistent Context Sources

| Source | Purpose |
|--------|---------|
| `.cursor/rules/project-engineering.mdc` | Engineering standards and workflow |
| `assignment/assignment-requirements.md` | Assignment source of truth |
| `requirements-analysis.md` | Requirements and decisions |
| `design-notes.md` | Architecture and layer design |
| `data-model.md` | Entity schemas |
| `data-quality-strategy.md` | DQ rules and thresholds |
| `ai-prompts/*.md` | Prior interaction history |

## Context-Setting Workflow

```
1. Open relevant design doc section (e.g., design-notes.md §5 for Gold)
2. Reference assignment acceptance criteria
3. State layer status (IMPLEMENTED / DESIGN ONLY / RUNTIME VALIDATED)
4. List explicit DO NOT constraints
5. Specify output files and validation expectations
6. After completion → update ai-prompts/ and layer README status
```

Example opening for an implementation interaction:

> Bronze: IMPLEMENTED + RUNTIME VALIDATED  
> Silver: DESIGN COMPLETE, IMPLEMENTATION NOT STARTED  
> Implement ONLY src/silver/. Do NOT modify Bronze or Gold.

This pattern prevented scope creep and cross-layer modifications throughout the project.
