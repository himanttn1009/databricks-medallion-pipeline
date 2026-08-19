# Databricks notebook source
# COMMAND ----------
# Bronze runner

import sys

dbutils.widgets.text(
    "repo_path",
    "/Workspace/Users/himanshu.kumar1@tothenew.com/databricks-medallion-pipeline",
    "Repo path",
)
repo_path = dbutils.widgets.get("repo_path").strip()

if not repo_path:
    raise ValueError("repo_path widget is required")

bronze_path = f"{repo_path}/src/bronze"
if bronze_path not in sys.path:
    sys.path.insert(0, bronze_path)

from ingest_all import main as bronze_main

exit_code = bronze_main()
if exit_code != 0:
    raise RuntimeError(f"Bronze run failed with exit code {exit_code}")

print("Bronze completed successfully.")
