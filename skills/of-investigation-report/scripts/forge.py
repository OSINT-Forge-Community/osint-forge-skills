#!/usr/bin/env python3
"""The distribution incorporates the canonical shared runtime."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from forgekit.cli import main
except ImportError:
    print('{"status":"error","code":"PACKAGED_RUNTIME_REQUIRED"}')
    raise SystemExit(2)

if __name__ == "__main__":
    raise SystemExit(main())
