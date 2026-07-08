# Strict race validation, but tolerant listing during migration

Race schemas extend pydantic `StrictModel`, so unknown or malformed fields are
rejected — a race either fully validates or raises `ValidationError`. Yet the
tool does not fall over on a bad race: `list_races(validate=True)` catches
`ValidationError` per file and simply omits races that don't validate, so
`spf race show <race>` gives actionable errors while `spf race list` shows only
the currently valid ones.

**Why:** the race TOML is mid-migration to a new structure (see `MIGRATE_TOML.md`),
so legacy files that don't yet conform must coexist with converted ones. Strict
validation keeps converted data honest; tolerant listing lets the tool stay
usable while files are migrated one at a time.

**Consequence:** a race silently missing from `spf race list` is the signal that
its TOML hasn't been migrated (or has a validation error) — run `spf race show`
on it to see why.
