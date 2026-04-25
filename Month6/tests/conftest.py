import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ml-pipeline"))
os.environ["PROJECT_ROOT"] = PROJECT_ROOT
