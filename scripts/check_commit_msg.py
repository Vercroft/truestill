#!/usr/bin/env python3
"""commit-msg hook: a commit credits people only and carries no email address.

Engineering Practices §6.8: no co-author trailer and no generated-by signature in commit text.
§6.7: no email address in a commit message; a GitHub noreply address is an identity, not contact
data, so it is allowed. The hook names no tool; it refuses the shapes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_FORBIDDEN = re.compile(
    r"co-authored-by:|\U0001f916|generated with \[",
    re.IGNORECASE,
)

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_NOREPLY = re.compile(r"@users\.noreply\.github\.com$", re.IGNORECASE)


def main() -> int:
    message = Path(sys.argv[1]).read_text(encoding="utf-8")
    found = _FORBIDDEN.search(message)
    refused = found.group(0) if found is not None else None
    if refused is None:
        refused = next(
            (m.group(0) for m in _EMAIL.finditer(message) if not _NOREPLY.search(m.group(0))),
            None,
        )
    if refused is not None:
        print(f"commit-msg: refused -- forbidden content {refused!r}.", file=sys.stderr)
        print(
            "Project rule: no co-author trailer, generated-by signature or email address "
            "in a commit message.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
