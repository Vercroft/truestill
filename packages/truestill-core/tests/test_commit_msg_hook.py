"""The commit-msg hook refuses what Engineering Practices §6.7 and §6.8 keep out of commit text.

A commit credits people only, so a `Co-authored-by:` trailer and a generated-by signature are
refused. A commit message carries no email address either, except a GitHub noreply address,
which is an identity rather than contact data. The hook names no tool: it refuses the shapes.

Run as git runs it, a subprocess given the message file, so the exit code is what is tested.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "check_commit_msg.py"


def _verdict(message: str, tmp_path: Path) -> int:
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text(message, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path)], capture_output=True, timeout=30, check=False
    ).returncode


@pytest.mark.parametrize(
    "message",
    [
        "Fix the scan\n\nCo-authored-by: Someone <someone@users.noreply.github.com>\n",
        "Fix the scan\n\nco-authored-by: someone\n",
        "Fix the scan\n\n\U0001f916 Generated with a tool\n",
        "Fix the scan\n\nGenerated with [a tool](https://example.com)\n",
        "Fix the scan\n\nReported by ada@example.com\n",
        "Fix the scan\n\nSigned: bot@vendor.example.org\n",
    ],
)
def test_the_hook_refuses(message: str, tmp_path: Path) -> None:
    assert _verdict(message, tmp_path) == 1, message


@pytest.mark.parametrize(
    "message",
    [
        "Fix the scan\n\nThe walk skipped hidden folders.\n",
        "Merge branch 'main'\n\nAuthor: 1+someone@users.noreply.github.com\n",
        "Docs: say where CONTRIBUTING.md moved the setup\n",
    ],
)
def test_the_hook_accepts(message: str, tmp_path: Path) -> None:
    assert _verdict(message, tmp_path) == 0, message
