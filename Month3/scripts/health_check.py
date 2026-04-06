#!/usr/bin/env python3
"""
scripts/health_check.py
Check the health of every pipeline component.
Usage:  python scripts/health_check.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.monitor import print_health_report

if __name__ == "__main__":
    print_health_report()
