"""Verify the tamper-evident hash chain of the audit log.

Walks the file line by line, recomputes each entry's prev_hash, and reports the
first break (if any). Exit codes:

    0 — chain intact
    1 — audit log not found or unreadable
    2 — malformed JSON on a line
    3 — chain broken (partial tampering detected)

Usage:

    mcp-gmail-manager-verify-log            # verify current audit.jsonl
    mcp-gmail-manager-verify-log path.jsonl # verify an arbitrary file
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from .config import load_config


def _verify_file(path: Path) -> int:
    if not path.is_file():
        print(f"Audit log not found at {path}", file=sys.stderr)
        return 1

    prev_hash: str | None = None
    verified = 0
    try:
        with path.open("rb") as f:
            for lineno, raw in enumerate(f, start=1):
                line = raw.rstrip(b"\n")
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Line {lineno}: invalid JSON: {e}", file=sys.stderr)
                    return 2
                actual_prev = entry.get("prev_hash")
                if actual_prev != prev_hash:
                    print(
                        "CHAIN BROKEN at line {n}\n"
                        "  op:           {op}\n"
                        "  ts:           {ts}\n"
                        "  entry prev_hash: {got}\n"
                        "  expected:        {want}\n"
                        "\n"
                        "This means the log was edited, truncated, or an entry was "
                        "removed between the prior line and this one.".format(
                            n=lineno,
                            op=entry.get("op"),
                            ts=entry.get("ts"),
                            got=actual_prev,
                            want=prev_hash,
                        ),
                        file=sys.stderr,
                    )
                    return 3
                prev_hash = hashlib.sha256(line).hexdigest()
                verified += 1
    except OSError as e:
        print(f"Could not read {path}: {e}", file=sys.stderr)
        return 1

    print(f"OK. Verified {verified} entries. Chain intact.")
    print(f"Latest tip: {prev_hash}")
    return 0


def run() -> int:
    args = sys.argv[1:]
    if args:
        path = Path(args[0]).expanduser().resolve()
    else:
        path = load_config().audit_log_path
    return _verify_file(path)


if __name__ == "__main__":
    sys.exit(run())
