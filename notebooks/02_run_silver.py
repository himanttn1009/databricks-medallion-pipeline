# Databricks notebook source
# COMMAND ----------
# Silver runner

import sys

dbutils.widgets.text(
    "repo_path",
    "/Workspace/Users/himanshu.kumar1@tothenew.com/databricks-medallion-pipeline",
    "Repo path",
)
repo_path = dbutils.widgets.get("repo_path").strip()

if not repo_path:
    raise ValueError("repo_path widget is required")

silver_path = f"{repo_path}/src/silver"
if silver_path not in sys.path:
    sys.path.insert(0, silver_path)

from create_silver_tables import main as silver_main

exit_code = silver_main()
if exit_code != 0:
    raise RuntimeError(f"Silver run failed with exit code {exit_code}")

print("Silver completed successfully.")
