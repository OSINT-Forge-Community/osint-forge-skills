#!/usr/bin/env python3
"""Development entrypoint; packaged skills carry their own runtime."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "shared"))
from forgekit.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
