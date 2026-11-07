"""Run data collection for one or all sources.

Usage (from project root):
    python -m scripts.run_collection            # all sources
    python -m scripts.run_collection --source wfp
Exit code 1 if any enabled source failed (useful for GitHub Actions).
"""

import argparse
import sys

from src.collection import fetch_wfp, fetch_worldbank
from src.collection.utils import load_config

COLLECTORS = {"wfp": fetch_wfp.run, "worldbank": fetch_worldbank.run}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=[*COLLECTORS, "all"], default="all")
    args = parser.parse_args()

    cfg = load_config()
    names = COLLECTORS if args.source == "all" else [args.source]
    failed = False
    for name in names:
        if not cfg["sources"][name].get("enabled", True):
            print(f"[skip] {name} disabled in config")
            continue
        result = COLLECTORS[name]()
        print(f"[{result['status']}] {name}: {result['message']}")
        failed |= result["status"] == "error"
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
