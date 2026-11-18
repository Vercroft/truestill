"""No incidental vendor or personal naming in the repo (2026-07-31 naming sweep).

**Incidental is the whole point.** A name is incidental when the code would mean exactly the
same thing without it: "exiftool is 74% of wall on <vendor>" is a measurement on *a cloud FUSE
mount*, and naming the vendor tells a reader nothing they can act on while tying an open-source
repo to one person's storage provider. A name is **not** incidental when removing it would make
the code lie about what it does, and those are allowlisted below with the reason attached.

**What is deliberately still here**, because a blanket ban would have destroyed it:

* **Google Takeout, rclone, exiftool, SQLite, Playwright** - real formats, dependencies and
  tools. Renaming these would misdescribe the feature. They are not in :data:`BANNED` at all.
* **Cited evidence** - PhotoPrism, Immich, IMatch, Lightroom and the rest, where a
  docstring cites another tool's behaviour to justify an invariant. `hash_cache.py`'s
  size+mtime rule *is* PhotoPrism's rule, and IMatch is the documented counter-example that
  bounds it. Strip those and the invariant is left with no stated reason, which is the drift
  four audit passes were spent removing. Also not in :data:`BANNED`.
* **Drive nicknames** - "The Memory Cabinet", "Output". They are named corpora:
  `PERFORMANCE.md` §2.1 binds every measurement row to state its corpus, and "a cloud mount" is
  not traceable. A folder the maintainer fences is never among them: a public repository does
  not name a private tree, and the fence is enforced from the maintainer's own environment.
* **Wayanad** - a place name, not personal data, and
  ``test_the_real_wayanad_run_is_one_full_proposal_no_trim`` records that the fixture was checked
  against a remembered trip. ``test_the_real_trip_run`` would lose exactly that.

The allowlist stores the **reason**, not just the path, so the next person reads the ruling
rather than an unexplained exemption.

⚠ **THE BANNED TERMS ARE SHA-256 DIGESTS, NEVER TEXT.** A list of a person's name and private
folders, published to keep them out of the repository, publishes them. Each term is lowercased
with everything but letters and digits removed, then hashed. A line is checked by hashing each
word and its prefixes, so a term is found at the start of a longer word (a mount named after a
vendor); a two-word term is in :data:`BANNED_PAIRS` and checked against adjacent words only, so
"one drive" in a sentence is not a vendor. To add one:
``python3 -c "import hashlib; print(hashlib.sha256(b'term').hexdigest())"``.
"""

from __future__ import annotations

import functools
import hashlib
import itertools
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]

#: Digests of names that carry no meaning the surrounding text does not already carry, each with
#: what to write instead. Matched after the allowlist has been subtracted from the line.
BANNED: dict[str, str] = {
    "b4908884ffae28db7cd1c09edfac0d11b0cba4ab288611c03398887b88820d61": (
        "a storage vendor; say what the mount *is* (cloud FUSE mount, network mount)"
    ),
    "75170593d559f227f37d422056e701a9748849b661f92f74a8ffee3c977c1bb9": "a storage vendor",
    "567781541aa1d043041ec08be14e1c519629784e3952d0d079ac87640242ba5e": "a storage vendor",
    "e0aa81dd500c530a70b5511fc95959ae1e19dc19a01034e223bfc5ed78e3bdef": "a storage vendor",
    "f6bf30615ee0c7b025aee0ac2297af0d92665e36f71c2d573412a5e6f833c12e": "a storage vendor",
    "264d0fd5501b331fab1c488a11f69b33d79f9071cd7e1e1f8bb1149d05399a6b": "a storage vendor",
    "7a03c4bbd666dfa8aa5b86a15333b50a0c8755e5e499e0e75532ee7277a29a60": "a storage vendor",
    "5ec6881ba42f261646c989c418aa6d1eab40276e67c703a1edad399624628d2a": (
        "the maintainer's personal name; say 'the maintainer'"
    ),
    "3300c929757e9ef5dcc62c0326f4f113523925e33923ee80d72998c566ab0d5a": (
        "the maintainer's personal name; say 'the maintainer'"
    ),
    "887d814b066634a8b8ba0b65c506b5352df0e23a5c9ea98628e463cdc392dbc6": (
        "a level of the maintainer's private tree; use Input/2013 or Input/2014"
    ),
    "2636b739be3cd8ed6c49a233888160ca75c3b0677d86fa35324751b649cea983": (
        "a private repository's name; say 'an earlier prototype'"
    ),
}

#: Two-word terms, hashed with the space removed and matched against adjacent words only.
BANNED_PAIRS: dict[str, str] = {
    "e289236a3e78b6968b0cb0237aa66e232ca7733774310d77086b4af2f6e80ce7": (
        "the maintainer's locked folder; say 'the fenced folder'"
    ),
}

#: Prefix lengths hashed, so a term is found at the start of a longer word.
_PREFIX_LENGTHS = range(4, 17)

_WORD = re.compile(r"[a-z0-9]+")


@functools.cache
def _hit(candidate: str) -> str | None:
    """The reason for a banned digest among `candidate` and its prefixes, or `None`."""
    for end in (len(candidate), *(n for n in _PREFIX_LENGTHS if n < len(candidate))):
        reason = BANNED.get(hashlib.sha256(candidate[:end].encode()).hexdigest())
        if reason is not None:
            return reason
    return None


def _banned_in(text: str) -> list[str]:
    """The reason for every banned term in `text`: per word, then per adjacent pair of words."""
    words = _WORD.findall(text.lower())
    found = [reason for w in words if (reason := _hit(w)) is not None]
    for a, b in itertools.pairwise(words):
        reason = BANNED_PAIRS.get(hashlib.sha256((a + b).encode()).hexdigest())
        if reason is not None:
            found.append(reason)
    return found


# A PLACE NAME IS EXPOSURE WHEN IT IS THE MAINTAINER'S FOLDER, AND EVIDENCE WHEN IT IS A DATASET
# ROW. Read this before widening BANNED. On 2026-08-11 a blanket sweep replaced two city names
# everywhere they appeared, which was right inside a folder name taken from the fenced tree and
# WRONG inside a geocoding record, where the same two words are gazetteer test points with
# populations and coordinates. The sweep turned a measurement record into nonsense, and it was
# caught by reading the diff rather than by any test. So the question is never "is this word a
# place" but **whose sentence is it in**. BANNED holds names of the maintainer's own structure,
# never bare toponyms.

#: ``(pattern, reason)`` - text that legitimately contains a banned term. Subtracted from each
#: line *before* the scan, so these survive without exempting the whole file around them. An
#: entry is re-justified when the ruling behind it moves, never inherited.
ALLOWED: tuple[tuple[str, str], ...] = (
    (
        r"\(Vercroft\|[A-Za-z-]+\)/truestill/",
        (
            "the cosign `--certificate-identity-regexp` in README.md's verification section. "
            "v0.1.0 and v0.1.1 were signed while the repository belonged to the maintainer's own "
            "GitHub account, and a signature records the owner of its day, so the regexp names "
            "that login beside Vercroft. Without it those releases cannot be verified."
        ),
    ),
    (
        r'for vendor in \("[a-z]+", "[a-z]+", "dropbox", "onedrive"\):',
        (
            "the assertion in `test_run_health.py` that proves the disk-full message names NO "
            "cloud vendor. The names ARE the assertion here: the design ruling was to report "
            "the free-space DELTA rather than maintain a per-vendor cache-path table, and a "
            "test that checked for a genericised placeholder would assert nothing. Scoped to "
            "the one line."
        ),
    ),
    (
        r"Backblaze tells people to make another backup first",
        (
            "the field evidence behind restore stage 3's reassurance, in `truestill_core."
            "recover`, the Backups markup and their test. THE NAME IS THE EVIDENCE: the design "
            "ruling is that a restore button must say, before anything is pressed, that nothing "
            "is deleted or replaced - and that ruling rests on real products treating restore as "
            "the dangerous direction. Genericised to 'some backup software', the justification "
            "becomes an unsourced claim, which is the summary-instead-of-the-line failure "
            "CONTRIBUTING.md names. Scoped to the exact sentence so the name cannot spread."
        ),
    ),
    (
        r"rclone supports[^.]*",
        (
            "rclone.py documents which remotes a real dependency actually supports - the list "
            "is the capability described, and genericising it would make the sentence say nothing"
        ),
    ),
)

#: Files this guard cannot scan without flagging itself.
SKIP = {"packages/truestill-app/tests/test_no_incidental_naming.py"}


def _tracked_files() -> list[str]:
    """Everything that WILL be committed, not only what already is.

    ``git ls-files`` alone lists the index, so a brand-new file is invisible to this guard until
    the moment it is added - which is after the `make check` that was supposed to catch it. That
    is a false green with a delay fuse: the run that could act on it passes, and the failure
    arrives on the next one, or on CI. ``--others --exclude-standard`` adds untracked files while
    still honouring .gitignore, so the guard sees the working tree the way a reviewer would.
    """
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    tracked = [line for line in out.splitlines() if line and line not in SKIP]
    assert tracked, (
        "`git ls-files --cached --others --exclude-standard` returned nothing, so this "
        "guard has no subject and would find zero incidental names in zero files. "
        "See ENGINEERING_STANDARD.md 4, the fifty-second member: `check=True` turns a "
        "missing .git into an error, but a pathspec that stops matching returns zero rows "
        "at exit 0, and zero violations over zero files is the same green as zero over a "
        "clean repo. The repo restructure is exactly the change that moves a pathspec."
    )
    return tracked


def _strip_allowed(text: str) -> str:
    for pattern, _reason in ALLOWED:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text


def _offences(relative: str) -> list[str]:
    """``path:line: reason`` for every banned term left after the allowlist is subtracted."""
    path = REPO / relative
    found = [
        f"{relative}: in the FILE NAME, {reason}" for reason in _banned_in(_strip_allowed(relative))
    ]
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return found  # binary or unreadable: nothing to read, nothing to claim
    for number, line in enumerate(content.splitlines(), start=1):
        found.extend(
            f"{relative}:{number}: {reason}" for reason in _banned_in(_strip_allowed(line))
        )
    return found


def test_no_incidental_vendor_or_personal_naming() -> None:
    offences = [o for relative in _tracked_files() for o in _offences(relative)]
    assert not offences, (
        f"{len(offences)} incidental name(s) - each is a vendor or personal name the "
        "surrounding text does not need:\n"
        + "\n".join(offences[:60])
        + ("\n  ... and more" if len(offences) > 60 else "")
        + "\n\nEither reword it, or add an ALLOWED entry stating why the name is load-bearing."
    )


def test_every_banned_entry_is_a_digest() -> None:
    """A plain-text term here would publish what the guard exists to keep out."""
    malformed = [k for k in (*BANNED, *BANNED_PAIRS) if not re.fullmatch(r"[0-9a-f]{64}", k)]
    assert not malformed, f"BANNED keys must be sha256 hex digests: {malformed}"


@pytest.mark.parametrize(
    "line",
    [
        "synced through Dropbox overnight",
        "the DROPBOX-folder mount",
        "a Dropboxsync mount",
    ],
)
def test_the_scanner_finds_a_term_as_a_word_a_prefix_and_across_a_space(line: str) -> None:
    """Driven by a vendor that may be named in public, since the private terms cannot be."""
    assert _banned_in(line), f"the scanner missed a banned vendor in: {line}"


def test_the_guard_spares_the_legitimate_references() -> None:
    """Cry-wolf half: the allowlisted forms and the kept names must not be reported.

    The kept names are the load-bearing ones - a dependency, an input format, cited evidence,
    a named corpus, a place. If this ever fails, the sweep has started deleting meaning.
    """
    spared = [
        "--certificate-identity-regexp '^https://github\\.com/(Vercroft|someone)/truestill/'",
        "any remote rclone supports -- Dropbox, S3, SFTP, Google Drive -- is usable",
        "Size+mtime invalidation matches PhotoPrism's rule and is honest when the bytes change.",
        "Google Takeout's photoTakenTime is read before the filename tier.",
        "measured on The Memory Cabinet, 2,269 copies over a cloud FUSE mount",
        "test_the_real_wayanad_run_is_one_full_proposal_no_trim",
        "dropping the box, one drive at a time",
        "Drop box",
    ]
    for line in spared:
        flagged = _banned_in(_strip_allowed(line))
        assert not flagged, f"flagged a legitimate reference {flagged}: {line}"
