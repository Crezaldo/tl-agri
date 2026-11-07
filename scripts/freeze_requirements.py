"""Pin requirements.txt to the versions installed on THIS machine.

Usage (from project root, after everything works):
    python -m scripts.freeze_requirements

Keeps comments and package order; replaces '>=' ranges with '=='.
Reason: ARIMA order selection gave different results with different
statsmodels versions - pinning makes results reproducible.
"""

import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "requirements.txt"
out = []
for line in path.read_text().splitlines():
    m = re.match(r"^\s*([A-Za-z0-9_.\-]+)\s*([<>=!~]=?[^#\s]*)?\s*(#.*)?$", line)
    if not m or line.strip().startswith("#"):
        out.append(line)
        continue
    name, _, comment = m.groups()
    try:
        pinned = f"{name}=={version(name)}"
    except PackageNotFoundError:
        pinned = line.split("#")[0].strip()          # not installed: keep as is
        print(f"[not installed] {name}")
    out.append(f"{pinned:<28}{comment or ''}".rstrip())
    print(out[-1])
path.write_text("\n".join(out) + "\n")
print(f"\nWritten: {path}")
