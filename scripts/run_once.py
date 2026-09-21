#!/usr/bin/env python3
"""스케줄러 없이 스냅샷을 1회 생성해서 확인하는 스크립트."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from assetmgr.scheduler import run_once  # noqa: E402

if __name__ == "__main__":
    snapshot = run_once()
    print(json.dumps(snapshot, ensure_ascii=False, indent=2, default=str))
