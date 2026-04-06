#!/usr/bin/env python3
"""
scripts/run_pipeline.py
Run the ETL pipeline once manually.
Usage:  python scripts/run_pipeline.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.database     import setup_database
from src.etl_pipeline import run_pipeline
from src.reporter     import print_status

if __name__ == "__main__":
    setup_database()
    print("Running pipeline...")
    result = run_pipeline()
    print_status()
