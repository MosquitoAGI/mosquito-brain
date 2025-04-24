"""Run logs.

One JSON object per line, flushed as it is written, so a run that ends with a
traceback still leaves a readable record of how far it got.
"""

from __future__ import annotations

import json
import time
from pathlib import Path


class Journal:
    def __init__(self, directory: str | Path, enabled: bool = True, every_n: int = 5):
        self.enabled = enabled
        self.every_n = max(int(every_n), 1)
        self.rows = 0
        self.path: Path | None = None
        if enabled:
            d = Path(directory)
            d.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y%m%d-%H%M%S")
            self.path = d / ("bridge-%s.jsonl" % stamp)
            self._fh = self.path.open("w", encoding="utf-8")
        else:
            self._fh = None

    def write(self, frame: int, event: str, **fields) -> None:
        if self._fh is None or frame % self.every_n:
            return
        row = {"frame": frame, "event": event, "t": time.time()}
        row.update({k: v for k, v in fields.items() if v is not None})
        self._fh.write(json.dumps(row, separators=(",", ":")) + "\n")
        self._fh.flush()
        self.rows += 1

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def __enter__(self) -> "Journal":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
