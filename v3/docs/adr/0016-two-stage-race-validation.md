# Schema validation is a hard gate; style linting is a soft one

`spf race lint` only ever runs against Races that already pass schema
validation. A Race that fails validation produces **zero** findings, not an
error: the all-races sweep skips it silently, and naming it explicitly prints
`<race>: skipped (does not validate)` to stderr and exits 0.

**Why:** this extends ADR-0004 rather than contradicting it. That tolerance
exists so `spf race show` gives one actionable error per broken file while the
rest of the tool stays usable; the same reasoning applies to a second, later
gate. A schema-broken Race cannot be parsed into the `RaceConfig` the linter
walks, so linting it would mean either re-parsing raw TOML — a permanent
untyped-dict tax — or reporting the same failure `just validate` already
reports, one step further down the same `just check` run. `lint-races` sits
immediately after `validate` in the recipe order precisely so validation fails
first and owns that message.

**Consequence:** "the linter silently ignores invalid Races" is the design, not
a bug. Do not make the linter error on an unparseable Race — a green
`lint-races` means *every Race that validates is clean*, and `validate` is what
guarantees that set is all of them.
