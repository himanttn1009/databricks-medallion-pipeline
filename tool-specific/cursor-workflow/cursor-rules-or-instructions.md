# Cursor Rules and Instructions

## Project Rules

| File | Description |
|------|-------------|
| `.cursor/rules/project-engineering.mdc` | Production-oriented medallion architecture engineering standards |

Key rules enforced throughout the project:

- Understand requirements before implementing; design before code for significant tasks.
- Keep Bronze raw; validate in Silver; aggregate in Gold; Dashboard reads Gold only.
- Never silently delete bad data — flag and quarantine.
- Spark-native operations; Spark Connect compatible (no `_jvm`/`_jsc`/Hadoop FS).
- No credentials or real PII in repo.
- Validate AI-generated code before considering tasks complete.
- Minimal, reviewable changes — do not modify unrelated files.

## How Rules Are Used

1. **Always applied** — Cursor loads `project-engineering.mdc` automatically in agent mode.
2. **Reinforced in prompts** — Each layer interaction repeats layer boundaries and forbidden modifications.
3. **Design doc alignment** — Rules reference medallion principles that match `design-notes.md`.
4. **Review gate** — Static reviews check Spark Connect compatibility and layer boundary violations.

## Additional Instructions

Per-interaction prompt patterns used successfully:

```
IMPORTANT:
- [Layer] design is COMPLETE / IMPLEMENTED / RUNTIME VALIDATED
- Implement ONLY [allowed paths]
- DO NOT modify [forbidden layers]
- DO NOT claim runtime validation unless performed
```

Layer status declarations at the top of each prompt prevented AI from modifying completed upstream layers or claiming unverified runtime success.

For dashboard work:

```
- DO NOT create Databricks Dashboard UI automatically
- DO NOT execute Databricks queries
- Gold tables only — no bronze.* or silver.*
```

These constraints are documented in `ai-prompts/08-dashboard-layer.md` Interactions 1–3.
