"""Check that a lint-clean edit to a game-data value breaks no test.

The suite's one rule is that no test may fail because a TOML file under
`races/`, `armies/` or `rules/` was updated (`docs/agents/testing.md`,
ADR 0033). This mutates one value at a time in the committed corpus, discards
any edit the validators reject, runs the suite against the rest, and reports
every test that a legitimate rules edit would have broken.

Values only, never keys: a rename or a deletion is structural, and a test
noticing one is doing its job.
"""

import argparse
import atexit
import random
import signal
import subprocess
import sys
import types
from collections.abc import Iterator, MutableMapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import tomlkit

V3 = Path(__file__).resolve().parent.parent
CORPUS_GLOBS = ("races/*.toml", "rules/*.toml", "armies/*.toml", "armies/*/*.toml")

STRING_MARKER = " Zz"
"""Appended to prose. Title-cased so `spf race lint` keeps accepting names."""

PROSE_FIELDS = frozenset(
    {
        "comment",
        "description",
        "effect",
        "example",
        "explanation",
        "flavor",
        "heading",
        "lore",
        "name",
        "note",
        "remove",
        "text",
        "title",
        "tip",
        "todo",
    }
)
"""Fields whose value is prose a reader sees, not a reference to another record."""

NUMBER_FIELDS = frozenset(
    {
        "ap",
        "armor",
        "cp",
        "deflection",
        "ip",
        "mp",
        "N",
        "range",
        "strength",
        "vpm",
        "xp",
    }
)
"""Fields carrying a stat: an integer, or a per-angle list of them."""

MUTABLE_FIELDS = PROSE_FIELDS | NUMBER_FIELDS


#
# Mutation: pure, and the part the tests exercise
#


@dataclass(frozen=True)
class Target:
    """One value that could be mutated: where it lives, and under what name."""

    path: Path
    keys: tuple[str | int, ...]
    field: str

    def __str__(self) -> str:
        """Render as `races/dwarf.toml  units.dwarf_infantry.cost.mp`."""
        location = ".".join(str(key) for key in self.keys)
        return f"{self.path}  {location}"


def mutate_value(value: object) -> object | None:
    """Return `value` nudged by one step, or `None` when it cannot be nudged.

    Prose gains a marker and an integer gains one. A list of integers steps
    only its first entry, because its length is arity — an angle count or a
    table width — and therefore structure rather than content.
    """
    if isinstance(value, str):
        return value + STRING_MARKER
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value + 1
    if isinstance(value, list) and value and all(_is_integer(item) for item in value):
        return [value[0] + 1, *value[1:]]
    return None


def _is_integer(value: object) -> bool:
    """Check for a plain integer, excluding the bools that subclass one."""
    return isinstance(value, int) and not isinstance(value, bool)


def find_targets(text: str, path: Path | None = None) -> list[Target]:
    """Find every mutable value in one TOML document."""
    return [
        Target(path=path or Path(), keys=keys, field=str(keys[-1]))
        for keys, value in _walk(tomlkit.parse(text), ())
        if _is_mutable(str(keys[-1]), value)
    ]


def _is_mutable(field: str, value: object) -> bool:
    """Check that `field` is allowlisted *and* carries the kind it promises.

    `assault.ap` is a stat that is sometimes the string `"N/A"`; stepping that
    as prose would corrupt it rather than nudge it.
    """
    if mutate_value(value) is None:
        return False
    if field in PROSE_FIELDS:
        return isinstance(value, str)
    return field in NUMBER_FIELDS and not isinstance(value, str)


def _walk(
    node: object, prefix: tuple[str | int, ...]
) -> Iterator[tuple[tuple[str | int, ...], object]]:
    """Yield `(key path, value)` for every entry below `node`.

    Arrays of tables are descended into by index; every other list is a value
    in its own right, since its entries carry no key to be named by.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk(value, (*prefix, str(key)))
            yield (*prefix, str(key)), value
    elif isinstance(node, list) and any(isinstance(item, dict) for item in node):
        for index, item in enumerate(node):
            yield from _walk(item, (*prefix, index))


def apply_mutation(text: str, target: Target) -> str:
    """Return `text` with `target`'s value stepped and every key left alone."""
    document = tomlkit.parse(text)
    node: object = document
    for key in target.keys[:-1]:
        node = _container(node)[key]
    last = target.keys[-1]
    _container(node)[last] = mutate_value(_container(node)[last])
    return tomlkit.dumps(document)


def _container(node: object) -> MutableMapping[Any, Any]:
    """View a table or an array of tables as one indexable thing."""
    return cast("MutableMapping[Any, Any]", node)


def sample_targets(
    targets: Sequence[Target], *, per_field: int | None, seed: int
) -> list[Target]:
    """Pick at most `per_field` targets per field name, spread across files.

    A full pytest run per mutation is the cost that decides how many there can
    be, so the default sweep buys coverage of every *kind* of field rather than
    of every occurrence. `per_field=None` keeps the lot.
    """
    if per_field is None:
        return list(targets)

    rng = random.Random(seed)  # noqa: S311
    shuffled = list(targets)
    rng.shuffle(shuffled)

    sampled: list[Target] = []
    for field in sorted({target.field for target in targets}):
        of_field = [target for target in shuffled if target.field == field]
        # Rank each target among its own file's, then take the low ranks: one
        # field's picks land in as many different files as there are picks.
        seen: dict[Path, int] = {}
        ranked: list[tuple[int, Target]] = []
        for target in of_field:
            rank = seen.get(target.path, 0)
            seen[target.path] = rank + 1
            ranked.append((rank, target))
        ranked.sort(key=lambda pair: pair[0])
        sampled.extend(target for _, target in ranked[:per_field])
    return sampled


#
# Running: mutate, validate, test, restore
#


class Corpus:
    """The committed game data, and the promise to hand it back unedited.

    Every path this writes to is remembered with its original bytes and put
    back by `restore`, which runs from a `finally`, from an interrupt handler,
    and at exit. An interrupted run must never leave a dirty working tree.
    """

    def __init__(self) -> None:
        """Start with nothing touched."""
        self._original: dict[Path, bytes] = {}

    def write(self, path: Path, text: str) -> None:
        """Overwrite `path`, remembering what was there first."""
        self._original.setdefault(path, path.read_bytes())
        path.write_text(text, encoding="utf-8")

    def restore(self) -> None:
        """Put every file this touched back, byte for byte."""
        for path, content in self._original.items():
            path.write_bytes(content)
        self._original.clear()

    def guard(self) -> None:
        """Arm the paths out of a run that a `finally` alone does not cover."""
        atexit.register(self.restore)
        for received in (signal.SIGINT, signal.SIGTERM):
            signal.signal(received, self._on_signal)

    def _on_signal(self, number: int, _frame: types.FrameType | None) -> None:
        """Restore, then exit with the conventional code for the signal."""
        self.restore()
        raise SystemExit(128 + number)


def corpus_files() -> list[Path]:
    """Every game-data TOML, in a stable order."""
    return sorted(path for glob in CORPUS_GLOBS for path in V3.glob(glob))


def validate() -> str | None:
    """Run the validators over the corpus, returning the first complaint.

    A subprocess because the registry is cached for the life of a process, so
    an in-process check would read the edit only once (ADR 0024).
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(Path(__file__).resolve()), "--validate-corpus"],
        capture_output=True,
        text=True,
        check=False,
        cwd=V3,
    )
    if result.returncode == 0:
        return None
    complaints = (result.stdout + result.stderr).strip().splitlines()
    return complaints[-1][:200] if complaints else f"exit {result.returncode}"


def validate_corpus() -> int:
    """Load and lint every committed TOML, the way `just check` does.

    Mirrors `just validate lint-races lint-rules` in one process: the schemas
    are the hard gate, the linters the soft one (ADR 0016).
    """
    from spf import lint, races, registry, rules  # noqa: PLC0415
    from spf.armies import io  # noqa: PLC0415
    from spf.config import config  # noqa: PLC0415

    for race in races.list_races():
        races.get_race(race)
    rules.get_specials()
    rules.get_tokens()
    rules.get_hexes()
    rules.get_terrain()
    rules.get_modifiers()
    rules.get_namespaces()
    rules.get_rulebook()
    io.get_site_index(config.paths.armies / "site.toml")
    for pack in sorted(config.paths.armies.glob("*/pack.toml")):
        io.get_army_pack(pack)

    findings = [
        str(finding)
        for race in races.list_races(validate=True)
        for finding in lint.lint_race(race)
    ]
    findings += [
        str(finding)
        for finding in lint.lint_registry(registry.load_registry(), config.lint)
    ]
    for finding in findings:
        sys.stderr.write(f"{finding}\n")
    return 1 if findings else 0


def failing_tests() -> list[str]:
    """Run the suite and return the id of every test that failed."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        check=False,
        cwd=V3,
    )
    return sorted(
        {
            line.split(" ", 1)[0]
            for line in result.stdout.splitlines()
            if line.startswith(("FAILED", "ERROR"))
        }
    )


@dataclass(frozen=True)
class Finding:
    """A test that a legitimate edit to one value would have broken."""

    target: Target
    tests: list[str]


def run(targets: Sequence[Target], corpus: Corpus) -> list[Finding]:
    """Mutate each target in turn, reporting the tests that noticed."""
    findings: list[Finding] = []
    for number, target in enumerate(targets, start=1):
        path = V3 / target.path
        original = path.read_text(encoding="utf-8")
        _say(f"[{number}/{len(targets)}] {target}")
        try:
            corpus.write(path, apply_mutation(original, target))
            if (complaint := validate()) is not None:
                _say(f"    skipped, the validators reject it: {complaint}")
                continue
            if tests := failing_tests():
                _say(f"    {len(tests)} failing test(s)")
                findings.append(Finding(target=target, tests=tests))
            else:
                _say("    clean")
        finally:
            corpus.restore()
    return findings


def report(findings: Sequence[Finding], targets: Sequence[Target]) -> str:
    """Render the findings, grouped by the value whose edit produced them."""
    lines = [f"Mutated {len(targets)} value(s); {len(findings)} produced findings."]
    for finding in findings:
        lines += ["", f"{finding.target}", *(f"  {test}" for test in finding.tests)]
    if findings:
        by_file: dict[str, int] = {}
        for finding in findings:
            for test in finding.tests:
                file_name = test.split("::", 1)[0]
                by_file[file_name] = by_file.get(file_name, 0) + 1
        lines += ["", "Failures by test file:"]
        lines += [
            f"  {count:4d}  {file_name}"
            for file_name, count in sorted(by_file.items(), key=lambda x: -x[1])
        ]
    return "\n".join(lines)


def _say(message: str) -> None:
    """Write one progress line, flushed so a long run reads as it goes."""
    sys.stdout.write(f"{message}\n")
    sys.stdout.flush()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Read the command line."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--full",
        action="store_true",
        help="mutate every allowlisted value instead of a sample (slow)",
    )
    parser.add_argument(
        "--per-field",
        type=int,
        default=1,
        help="how many values to mutate per field name (default: 1)",
    )
    parser.add_argument("--seed", type=int, default=0, help="sampling seed")
    parser.add_argument(
        "--list", action="store_true", help="print the chosen targets and stop"
    )
    parser.add_argument(
        "--validate-corpus",
        action="store_true",
        help=argparse.SUPPRESS,  # How a mutation asks a clean process for a verdict.
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Mutate a sample of the corpus and report the tests that broke."""
    args = parse_args(argv)
    if args.validate_corpus:
        return validate_corpus()

    targets = [
        target
        for path in corpus_files()
        for target in find_targets(
            path.read_text(encoding="utf-8"), path.relative_to(V3)
        )
    ]
    chosen = sample_targets(
        targets, per_field=None if args.full else args.per_field, seed=args.seed
    )
    if args.list:
        _say("\n".join(str(target) for target in chosen))
        return 0

    corpus = Corpus()
    corpus.guard()
    try:
        findings = run(chosen, corpus)
    finally:
        corpus.restore()
    _say(report(findings, chosen))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
