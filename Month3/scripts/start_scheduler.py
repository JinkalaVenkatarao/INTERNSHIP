#!/usr/bin/env python3
"""
scripts/start_scheduler.py
Start automatic data collection every N minutes.
Usage:  python scripts/start_scheduler.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.database  import setup_database
from src.scheduler import start

if __name__ == "__main__":
    setup_database()
    start()
