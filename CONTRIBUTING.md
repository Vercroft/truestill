# Contributing to Truestill

This file says how you can help and how work is done in this repository.

## Licence and contributions

Truestill is source-available under [PolyForm Strict 1.0.0](LICENSE): free for personal and other
noncommercial use; business use needs a commercial licence. v0.1.0 and v0.1.1 were released under
Apache-2.0 and stay so.

- **Bug reports and ideas are welcome** in [Issues](https://github.com/dinesh-ad/truestill/issues).
  The bug report template asks for what is needed to reproduce.
- **Code contributions are not accepted.** Pull requests are closed without review.
- Never report a security problem in public: follow [SECURITY.md](SECURITY.md).

The reasoning is recorded in `docs/DECISIONS.md` D22. Internal planning is kept privately.

## Rules

We follow [Engineering Practices](https://github.com/Vercroft/engineering-practices), written down
in its [STANDARD.md](https://github.com/Vercroft/engineering-practices/blob/main/STANDARD.md):
commits, pull requests and merging follow its §6. This file adds only what is specific here.
`docs/IMPLEMENTATION_STANDARDS.md` is the binding product contract and wins on any conflict about
product behaviour; `docs/ENGINEERING_STANDARD.md` holds this repository's working principles.

**Until the Rust rewrite, minimal investment.** Truestill will be rewritten in Rust. Until then
this codebase gets safety fixes (a critical or high advisory in a runtime dependency; a bug that
loses data or gives a wrong answer) and whatever keeps `main` and the scheduled lanes green. No
refactors, clean-ups or new tooling for code that will be replaced; a fix gets the test that
proves it and no more.

## Set up a fresh clone

```sh
sudo apt install -y libimage-exiftool-perl         # macOS: brew install exiftool
uv sync --all-packages --group dev --locked
uv run prek install
uv run prek install --hook-type commit-msg
uv run prek install --hook-type pre-push           # refuses a push onto a red run
make check                                         # no browser, no Node needed
make e2e-install && make frontend-install          # browsers and npm ci, once
```

`exiftool` must be on `PATH` for the metadata paths. The React bundle is a build artifact and is
not committed: `make e2e` builds it first, and a test compares the served bundle's digest with the
frontend sources.

- **The pre-commit hooks are NINE: `gitleaks` (secrets in the staged changes), ruff, ruff-format,
  mypy, three prose guards (`dash-style`, `product-name`, `no-redirect-artifacts`), the commit-msg
  guard `commit-message-policy` and the pre-push `push-gate`. They do not run the suite, and their green
  output is not the gate.** `make check` is. The sentence is pinned to `.pre-commit-config.yaml`
  by `test_the_hook_census_is_not_a_guess.py`.

## Commands

Each row is what CI runs, in the job named in the last column. The required checks are `Gate summary`,
which passes only when every CI job passed or was skipped, the secret scan, CodeQL and the link
check.

| To | Run | CI job |
|---|---|---|
| Install the workspace and dev tools | `uv sync --all-packages --group dev --locked` | check |
| Lint | `uv run ruff check .` | check |
| Check formatting | `uv run ruff format --check --target-version py313 .` | check |
| Check types (`make typecheck` also checks the tests, on every platform) | `uv run mypy packages/truestill-core/src/truestill_core packages/truestill-cli/src/truestill_cli packages/truestill-app/src/truestill_app scripts packaging conftest.py suite_scratch.py` | check |
| Run the tests (one file: `uv run pytest packages/truestill-core/tests/test_hash_cache.py`) | `uv run pytest packages/` | check |
| All of the above, locally, under the 90 s ceiling | `make check` | check |
| Iterate on the browser lane (chromium, parallel) | `make e2e-loop` | - |
| Run the browser lane once before a commit (both engines, parallel) | `make e2e-fast` | e2e (nightly) |
| Audit the workflows (set up once: `VENV="${TMPDIR:-/tmp}/truestill-ci-venv"; python3 -m venv "$VENV"; "$VENV/bin/pip" install --require-hashes -r .github/requirements/zizmor.txt`) | `"$VENV/bin/zizmor" --offline .github/workflows` | zizmor |
| Check the links between the repository's own files | `lychee --offline --no-progress './**/*.md'` | Local links |
| Scan the staged changes for secrets, with `.gitleaks.toml` (CI scans the full history through Vercroft's shared workflow) | `uv run prek run gitleaks` | Secret scan / Full history |

`make check` runs before every commit. Capture its exit code; never pipe it into `tail`, which
returns zero on a red suite.

## Map

| Path | Holds |
|---|---|
| `packages/truestill-core/` | The core library and the safety-critical logic |
| `packages/truestill-cli/` | The `truestill` command |
| `packages/truestill-app/` | The local web UI (`truestill-app`), which imports core only; `frontend/` is the React, TypeScript, Vite and Tailwind v4 source, built into `static/dist/` |
| `scripts/` | Repository checks, measurement and release helpers |
| `packaging/` | The PyInstaller spec, the Debian and Windows installers, the bundled exiftool |
| `tests/e2e/` | The browser lane (Playwright) |
| `tests/golden/` | The date resolver's snapshot over a real library, checked on demand |
| `docs/` | Decisions, the two standards, the frontend contract, the design system, performance, brand and user guides |
| `brand/` | The brand artwork and its provenance |
| `.gitleaks.toml`, `.gitleaksignore`, `.pre-commit-config.yaml` | The secret and personal-data rules, the history findings that are not secrets, and the git hooks |
| `.github/workflows/` | CI with its Gate summary, the release, the secret scan, CodeQL, Scorecard and the link checks |
| `.github/requirements/` | Hash-pinned CI tools (zizmor) |
| `.github/ISSUE_TEMPLATE/` | The bug report form and the issue chooser settings |
| `.github/dependabot.yml` | Monthly grouped updates for the actions, the Python and npm packages and the CI tools |

## Removed documents

The backlog, the project status and shipped list, the research, soak, audit and measurement
records, the handoffs, the plans for future work and the working guides of the time were removed
by the decision of 2026-11-17. A comment, test or document that still names one (`docs/BACKLOG.md`,
`docs/<name>-record.md`, a backlog letter such as `(aje)` with its body
`docs/research/backlog/aje.md`) refers to git history: `git show 6ef7f911:<path>` prints it.

## Working rules

- **The browser lane is not routine.** Run it only when a change could make a screen stop
  showing something (deleting a payload field a renderer reads is that). Run the affected
  `tests/e2e/` files first, then the full lane once before the commit; never iterate on the full
  lane. CI runs it nightly and on `workflow_dispatch`.
- **Cite a symbol, never a line number**, in a living document: `drive.py:library_independence`.
  `uv run python scripts/cite_symbols.py <doc>` converts one, and
  `test_live_documents_cite_code_that_exists.py` refuses a line number where a symbol encloses it.
- **Quote the line, do not summarise it.** A finding that rests on a log or a run record pastes
  the line it rests on.
- **Re-run a census or a claim before acting on it**, and sweep the whole tree, not only
  Markdown: `git grep -nI -e "<claim>" -- .`. Read each hit before calling it a defect.
- **Prove a guard bites** with `scripts/mutate_once.py` (one proof) or
  `uv run python scripts/mutation_matrix.py --suite <name>` (a whole suite).
- **`warnings.catch_warnings` is unusable in the hot path**, because hashing runs on a thread
  pool; use `truestill_core.decode_noise`.
- **Benchmarks state their filesystem.** `/tmp` is often tmpfs, which measures RAM while claiming
  disk; the suite's own scratch location is `suite_scratch.scratch_root()`.
- **Refs.** Work arrives through a short-lived pull request branch, deleted after merge. Nothing
  else lives on the remote but `main` and release tags: `git ls-remote --heads origin` and
  `git ls-remote --tags origin` are the source.
- **Corpora.** Format edge cases come from the public `ianare/exif-samples` and
  `drewnoakes/metadata-extractor-images` repositories, cited by commit. An observation of a real
  library is a snapshot, never a fixture.

