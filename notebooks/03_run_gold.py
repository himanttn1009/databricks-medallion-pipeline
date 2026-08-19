# Databricks notebook source
# COMMAND ----------
# Gold runner

import sys

dbutils.widgets.text(
    "repo_path",
    "/Workspace/Users/himanshu.kumar1@tothenew.com/databricks-medallion-pipeline",
    "Repo path",
)
repo_path = dbutils.widgets.get("repo_path").strip()

if not repo_path:
    raise ValueError("repo_path widget is required")

gold_path = f"{repo_path}/src/gold"
if gold_path not in sys.path:
    sys.path.insert(0, gold_path)

from create_gold_tables import main as gold_main

exit_code = gold_main()
if exit_code != 0:
    raise RuntimeError(f"Gold run failed with exit code {exit_code}")

print("Gold completed successfully.")
