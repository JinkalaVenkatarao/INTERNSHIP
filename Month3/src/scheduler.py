# ============================================================
#  src/scheduler.py
#  Runs the pipeline automatically every N minutes.
#  Press Ctrl+C to stop cleanly.
# ============================================================

import time
import signal
import threading
from datetime import datetime

import schedule

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from src.config       import COLLECT_INTERVAL, get_logger
from src.etl_pipeline import run_pipeline

logger    = get_logger("scheduler")
_stop     = threading.Event()


# ===========================================================
# JOBS
# ===========================================================

def job_collect() -> None:
    """Collect weather data — called on schedule."""
    logger.info(
        f"Scheduled collection triggered at "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    try:
        run_pipeline()
    except Exception as exc:
        logger.error(f"Scheduled job failed: {exc}")


# ===========================================================
# SCHEDULER CONTROL
# ===========================================================

def start(interval_minutes: int = None, run_immediately: bool = True) -> None:
    """
    Start the scheduler loop.
    - interval_minutes: override the config value
    - run_immediately: collect once right now, then wait for schedule
    """
    interval = interval_minutes or COLLECT_INTERVAL
    schedule.clear()
    schedule.every(interval).minutes.do(job_collect)

    logger.info(f"Scheduler started — collecting every {interval} minute(s)")

    # Graceful shutdown on Ctrl+C / SIGTERM
    def _handle_signal(signum, frame):
        logger.info("Stop signal received — shutting down scheduler")
        _stop.set()

    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    if run_immediately:
        logger.info("Running initial collection now...")
        job_collect()

    logger.info("Scheduler running. Press Ctrl+C to stop.")
    while not _stop.is_set():
        schedule.run_pending()
        time.sleep(20)

    logger.info("Scheduler stopped.")


def get_next_run() -> str:
    """Return when the next job is scheduled."""
    jobs = schedule.jobs
    if not jobs:
        return "No jobs scheduled"
    return str(jobs[0].next_run)


# Run directly:  python src/scheduler.py
if __name__ == "__main__":
    from src.database import setup_database
    setup_database()
    start()
