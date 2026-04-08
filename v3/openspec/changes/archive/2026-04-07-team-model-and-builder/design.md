## Context

The existing codebase provides army definitions via TOML files validated into Pydantic models (`UnitConfig`, `ModelConfig`, `EquipmentConfig`). These are static definitions — there is no runtime concept of a "team" (a player's assembled force for a game). This change introduces that concept.

Key domain constraints informing the design:
- A team belongs to exactly one army/race.
- Units are the top-level building block; a unit instance is one copy of a `UnitConfig` with its models.
- A unit's default models come from `UnitConfig.models` (list of model keys). Multiple copies of the same unit may appear in a team.
- Model upgrades: a model can replace a default model only if the replacement's `ModelConfig.replaces` list includes the default model's name.
- Equipment upgrades: only equipment with a non-`None` `cost` field may be used as an upgrade. Equipment must satisfy its own `requires` CNF constraints relative to the model it is added to.
- `requires` CNF syntax: `[[A], [B, C]]` = "A AND (B OR C)". Each `Requirement` is either a type check (`key="type", value=ModelType`) or a holder-slot check (`key=EquipmentHolder, value=int`).
- Cost is additive: base unit cost + upgrade model costs + upgrade equipment costs.

## Goals / Non-Goals

**Goals:**
- Immutable, functional-core `Team` data structure (frozen dataclasses).
- Pure functions for team construction and querying — no side effects, no mutation.
- Clear validation errors returned as structured data, not raised exceptions.
- Full cost computation across all cost dimensions (`mp`, `cp`, `xp`, `ip`).
- Functions cover all team-building operations the user needs: `add_unit`, `upgrade_unit`, `upgrade_model`, `available_models`, `available_equipment`, `total_cost`, `validate_team`.

**Non-Goals:**
- CLI integration (separate change).
- Serialization / persistence of teams (separate change).
- Multi-army or allied teams.
- Point limits or list validation beyond structure and rules correctness.

## Decisions

### D1: Frozen dataclasses for Team, TeamUnit, TeamModel

**Decision**: Use `@dataclass(frozen=True)` with `tuple` for collections.

**Rationale**: Matches the project's functional-core preference. Frozen dataclasses give value semantics and hashability. Pydantic is not used here because `Team` is runtime-assembled state, not a schema-validated config.

**Alternatives considered**:
- Mutable dataclasses: easier to write but violates functional-core principle.
- Pydantic models: overkill for runtime state; the config models are already Pydantic.
- Named tuples: less ergonomic for nested structures.

### D2: Army config passed to functions, not stored in Team

**Decision**: `ArmyConfig` is passed to builder/query functions rather than embedded in `Team`.

**Rationale**: `Team` is pure data; the config is the "world" it operates in. This keeps `Team` lightweight and avoids coupling it to I/O. Callers load the army once and pass it through.

**Alternatives considered**:
- Store `ArmyConfig` in `Team`: convenient but conflates mutable army data with team state.

### D3: Equipment upgrades tracked as a separate set per TeamModel

**Decision**: `TeamModel.upgrades` is a `tuple[str, ...]` of equipment keys added as upgrades, separate from `TeamModel.config.equipments` (the defaults).

**Rationale**: Cleanly separates what came from the army definition vs what the player added. Cost computation only charges for items in `upgrades`. Validation checks both default + upgrade equipment together.

**Alternatives considered**:
- A single combined list with an `is_upgrade` flag per item: more complex, harder to reason about.

### D4: `validate_team` returns `list[str]` (error messages), not exceptions

**Decision**: Return a list of human-readable validation error strings. Empty list = valid.

**Rationale**: Callers often want to show all errors at once, not stop on the first. Exceptions are for unexpected failures; rule violations are expected in team-building workflows.

### D5: Units and models identified by `(name, idx)` compound keys

**Decision**: Functions take `unit_key: tuple[str, int]` and `model_key: tuple[str, int]` to identify positions. For example, `("goblin_warrior", 0)` is the first goblin warrior unit; `("rifle", 1)` is the second rifle model within a unit.

**Rationale**: A team can have multiple identical units, so names alone are ambiguous. Pure integer indices are unambiguous but opaque — `(name, idx)` retains the name for readability and grouping while the integer disambiguates between duplicates. This also makes it natural to iterate "all units of type X" or "all models named Y" without additional bookkeeping.

**Alternatives considered**:
- `int` indices alone: unambiguous but fragile and opaque; callers lose grouping information.
- Names alone: ambiguous when the same unit or model appears more than once.

## Risks / Trade-offs

- [`(name, idx)` keys must stay consistent] → If units are reordered, existing keys become stale. Mitigation: treat `Team` as append-only in this iteration; removal is out of scope.
- [Requires logic is complex] → CNF evaluation over holder slots and model types. Mitigation: implement as a small pure function `_satisfies_requires(model, equipment, current_equipment_keys, army_equipments) -> bool`.
- [No holder-slot tracking] → When checking available equipment, holder slot usage needs to be computed from current (default + upgrade) equipment. Mitigation: compute on-the-fly from `EquipmentLimit` and the union of default + upgrade equipment keys.

## Migration Plan

New file only — no migration needed.
