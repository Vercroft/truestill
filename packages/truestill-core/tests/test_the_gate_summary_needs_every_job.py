"""`Gate summary` is the one CI check a ruleset requires, so it must judge every other CI job.

A matrix job's check name carries its operating system and Python version (`check (ubuntu-latest,
py3.14)`), so a required check named that way breaks the day either changes. One job that needs
every other job and fails unless each passed or was skipped keeps the required name stable. Two
ways it could stop meaning anything, and each has a test here: a job added to `ci.yml` but left
out of `needs` runs with nothing requiring it to pass, and a verdict that accepts a failure lets
every job fail behind a green check.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
CI = ROOT / ".github" / "workflows" / "ci.yml"
GATE = "gate-summary"

_POSIX_ONLY = pytest.mark.skipif(
    sys.platform == "win32", reason="executes a bash step; the runner's own bash is not under test"
)


def _jobs() -> dict[str, Any]:
    jobs: dict[str, Any] = yaml.safe_load(CI.read_text(encoding="utf-8"))["jobs"]
    assert len(jobs) > 1, f"{CI} parsed to {len(jobs)} job(s); the shape changed"
    return jobs


def _gate() -> dict[str, Any]:
    jobs = _jobs()
    assert GATE in jobs, f"ci.yml has no `{GATE}` job; the ruleset requires its check"
    gate: dict[str, Any] = jobs[GATE]
    return gate


def test_the_gate_is_named_for_the_ruleset_and_always_runs() -> None:
    gate = _gate()
    assert gate.get("name") == "Gate summary", "the ruleset requires the check by this name"
    # Without always(), one failed job skips the gate, and a skipped required check is not a red one.
    assert gate.get("if") == "always()"


def test_the_gate_needs_every_other_job() -> None:
    jobs = _jobs()
    needs = _gate().get("needs", [])
    needed = {needs} if isinstance(needs, str) else set(needs)
    missing = sorted(set(jobs) - {GATE} - needed)
    assert not missing, f"`{GATE}` does not need {missing}, so nothing requires them to pass"


def _verdict(results: dict[str, str], tmp_path: Path) -> int:
    """Run the gate's own step, as CI does, on the needs results given."""
    steps = _gate()["steps"]
    run = next(step["run"] for step in steps if "NEEDS_JSON" in step.get("env", {}))
    script = tmp_path / "gate.sh"
    script.write_text(run, encoding="utf-8")
    needs = {job: {"result": result, "outputs": {}} for job, result in results.items()}
    env = {**os.environ, "NEEDS_JSON": json.dumps(needs)}
    return subprocess.run(["bash", str(script)], env=env, timeout=30, check=False).returncode


@_POSIX_ONLY
@pytest.mark.parametrize("bad", ["failure", "cancelled"])
def test_the_gate_fails_when_any_job_did_not_pass(bad: str, tmp_path: Path) -> None:
    assert _verdict({"check": "success", "e2e": bad, "zizmor": "success"}, tmp_path) != 0


@_POSIX_ONLY
def test_the_gate_passes_when_every_job_passed_or_was_skipped(tmp_path: Path) -> None:
    assert _verdict({"check": "success", "e2e": "skipped", "zizmor": "success"}, tmp_path) == 0
