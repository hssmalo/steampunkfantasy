# Prose rules fire only where the data contradicts itself

`spf lint` checks the corpus's prose and its Order Cards, alongside the name
rules it already ran. Two prose rules — **whitespace** and
**terminal-punctuation** — apply to every sentence field a Race or a rule
registry declares. Five order rules — **order-whitespace**, **order-separator**,
**order-name**, **order-spacing** and **order-argument** — apply to every cell
of every Order Card.

Each fires only where the data disagrees with itself. None encodes a preference
about how the game should be written.

## Why the punctuation rule runs one way only

The obvious rule is symmetric: a value containing sentence punctuation must end
with it, and a value containing none must not. The second half is wrong, and
the corpus says so. Run against `races/` and `rules/`, it flags 81 values, and
they are things like:

    Robotic iron dragon breathing acid.
    Fires 3 shot per fire order.
    These are tiny robot crabs, which swarm in big numbers.

One well-formed sentence each. The rule mistakes "one sentence" for "a
fragment", and enforcing it would strip the period off good prose.

Leading capitalization does not rescue it either: `Range = 1` and `Within
weapon range` are capitalized fragments, and the lowercase population is mostly
`key: Sentence.` prefixes that are lowercase on purpose.

So only the first half survives. A value that has already closed a sentence
inside itself is prose all the way to its end, and must close its last one —
116 values did not. A value with no internal punctuation is left alone
whichever way it ends. Deciding whether a lone clause wants a period is a
judgment no predicate can make, and the corpus is better served by a rule that
never guesses than by one that is right more often.

Two characters are accepted as terminators besides `.!?:` — `+` and `-` —
because `Ignore the damage at {N}+` and `Treat all F as -` end on notation, and
a period after it reads as part of the notation.

## Why damage-table rows are exempt

A row carries its own `effect` field, so the prose walk reaches it for free.
It should not. A row is a table cell:

    Kill 1 model
    +2 to future damage, destroy one minor head

Holding a cell to sentence punctuation would put a period on one row of a table
and not on the terser row beside it, which is less consistent than leaving both
alone. `todo` is out for a different reason: it is the game designer's working
notes, kept verbatim, and part of it is Norwegian.

## Why Order Cards need rules of their own

An order cell is the most-printed string in the game and the only one no gate
could read. `typos` skips any token containing a `+`, so `F+Depoloy` was
invisible to it — on a Dwarf card, while `typos.toml` already carried that
misspelling as a word to correct.

The cells are a closed vocabulary of about thirty orders written thousands of
times, which is exactly the shape a linter is good at and a spell checker is
not. Parsing a cell — orders joined with `+`, each optionally parenthesized,
each optionally carrying a lowercase argument list — also caught the same order
spelled two ways: `flee` beside `Flee`, `Fire (bow)` beside `Fire(bow)` in one
table, `360°,F` where the cards join with `+`.

## Why the order vocabulary lives in config, not in `rules/orders.toml`

`rules/orders.toml` is the obvious source: it is the order registry. It is also
a draft — nothing loads it, and it sat with a `.` where a `,` belonged, invalid
TOML that no gate had ever opened.

A linter reading it would hold that draft to a schema, and drafting a new rules
file is something this project does often. The vocabulary is authored under
`[lint]` in `configs/spf.toml` instead, beside the name conventions. When
`orders.toml` becomes a loaded registry, the vocabulary can move to it; until
then the linter does not depend on a file that is still being written.

## Why every `rules/*.toml` must nonetheless parse

That is the one thing a draft does owe. The registry opens only the files a
namespace declares, so `orders.toml` was never read and its syntax error could
have sat there indefinitely. `spf lint rules` now parses each unowned rules
file for its syntax alone. Files a loader owns are skipped rather than checked
twice — loading one is the stronger gate, and a defect is reported once, at its
cause (ADR 0016).

## Consequences

- Findings print with Rich markup off. An argument list is square-bracketed,
  and Rich had been reading `A[f, fly]` as a style tag and printing it as `A`.
- The prose and order walks run over the dumped model, not the file. Fields a
  schema does not declare never reach the rules, which is what keeps a rules
  file still being drafted out of the corpus these checks police.
- A new order name is a config edit, not a code change.
- The rules are narrow on purpose. Prose that could merely read better is not
  the linter's business, and a rule that rewrites good writing costs more than
  the inconsistency it removes.
