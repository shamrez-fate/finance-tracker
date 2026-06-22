"""
Personal Finance Tracker
Entry point for the application.
"""

import os
import sys
from pathlib import Path

cache_dir = Path(__file__).resolve().parent / ".mplcache"
cache_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))

from app import FinanceTrackerApp

def main():
    app = FinanceTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()