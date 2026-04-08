## Why

The game currently supports reading and validating army definitions, but has no concept of a "team" — a concrete selection of units, models, and equipment for play. Players need a way to build and validate teams from an army roster, respecting upgrade rules and cost constraints.

## What Changes

- Introduce a `Team` data model in `src/spf/teams.py` representing a player's assembled team from a single army/race.
- Add team-building functions: `add_unit()`, `upgrade_unit()`, `upgrade_model()`, `available_models()`, `available_equipment()`, `total_cost()`, and `validate_team()`.
- Unit instances within a team can have customized models (via `replaces`) and equipment (upgrades with a cost).
- Equipment must satisfy `requires` constraints — expressed as a CNF-style list of lists: `[[A], [B, C]]` means "A and (B or C)".
- Team cost is the sum of base unit costs + upgraded model costs + upgraded equipment costs.

## Capabilities

### New Capabilities

- `team-model`: Core `Team` data structure representing an assembled team from a single army — includes unit instances, per-unit model customizations, and per-model equipment customizations.
- `team-builder`: Functions for constructing and querying teams: `add_unit()`, `upgrade_unit()`, `upgrade_model()`, `available_models()`, `available_equipment()`, `total_cost()`, `validate_team()`.

### Modified Capabilities

<!-- No existing specs require requirement-level changes -->

## Impact

- New file: `src/spf/teams.py`
- New tests: `tests/test_teams.py`
- Reads existing army data via `spf.data` / `spf.armies` — no schema changes needed
- No changes to TOML army files or Pydantic models in `schemas/`
- No CLI changes in this iteration
