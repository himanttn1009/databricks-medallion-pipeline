# Databricks notebook source
# COMMAND ----------
# One-click full pipeline runner
# Runs Bronze -> Silver -> Gold -> Validation

dbutils.widgets.text(
    "repo_path",
    "/Workspace/Users/himanshu.kumar1@tothenew.com/databricks-medallion-pipeline",
    "Repo path",
)
repo_path = dbutils.widgets.get("repo_path").strip()

if not repo_path:
    raise ValueError("repo_path widget is required")

print(f"Using repo path: {repo_path}")

notebooks = [
    f"{repo_path}/notebooks/01_run_bronze",
    f"{repo_path}/notebooks/02_run_silver",
    f"{repo_path}/notebooks/03_run_gold",
    f"{repo_path}/notebooks/04_validate_counts",
]

for nb in notebooks:
    print(f"Running: {nb}")
    dbutils.notebook.run(nb, timeout_seconds=3600, arguments={"repo_path": repo_path})

print("Full pipeline run completed.")
