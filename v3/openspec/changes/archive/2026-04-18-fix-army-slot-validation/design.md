## Context

`_remaining_slots` is the central slot-accounting helper in `build.py`. It is called by `upgrade_model` (build-time), `validate_army` (load-time), and `available_equipment` (query-time). All three paths share the same bug: `_remaining_slots` iterates over `(*model.config.equipment, *model.upgrades)`, counting both default and upgrade equipment against the slot pool. Rule A (`Model.equipment` in the resolved layer) already discards defaults when upgrades exist, but `_remaining_slots` was never updated to match.

A second, independent bug exists in `validate_army`: it calls `_unsatisfied_groups(equip.requires, team_model, race_config)` where `team_model` holds *all* upgrades. `_remaining_slots` therefore subtracts every upgrade — including the one currently being validated — before checking whether that upgrade fits. The result is over-subtraction even for models with no default equipment.

## Goals / Non-Goals

**Goals:**
- `_remaining_slots` counts only upgrades for slot consumption (Rule A applied uniformly)
- `validate_army` checks each upgrade against remaining capacity excluding that upgrade's own consumption
- `available_equipment` correctly shows upgrades as available on models whose defaults would be discarded

**Non-Goals:**
- No change to build-time `upgrade()` error message text
- No change to `Model.equipment` (already correct)
- No change to JSON or TOML formats

## Decisions

### D1: `_remaining_slots` counts only `model.upgrades`, never `model.config.equipment`

Default equipment is always excluded from slot accounting, regardless of whether upgrades are present.

**Rationale:** The function is only ever called in contexts where we're asking "can an upgrade be added?" or "are the current upgrades valid?" In both contexts, Rule A means defaults are gone: either they are already discarded (upgrades exist) or they *will* be discarded the moment any upgrade is added. Keeping defaults out of the accounting is the single consistent rule that handles both cases.

**Alternative considered:** Only exclude defaults when `model.upgrades` is non-empty. Rejected — this still fails for the first upgrade check on a model with slot-consuming defaults, because at check time `model.upgrades` is empty and defaults would be counted.

### D2: `validate_army` builds a partial model for each upgrade check

When validating upgrade at index `j`, construct a temporary `ArmyModel` with `upgrades = team_model.upgrades[:j]` and pass it to `_unsatisfied_groups`. This excludes the upgrade being validated from the slot subtraction.

**Rationale:** Mirrors the semantics of `ArmyModel.upgrade()`, which is called when `self.upgrades` does *not* yet contain the new equipment. Validation should reproduce the same accept/reject decision that build-time would have made.

**Alternative considered:** Subtract the current upgrade's slot consumption back out after the fact. Rejected — more complex and fragile; the partial-model approach is a direct expression of intent.

## Risks / Trade-offs

- **Armies that were previously valid might now show `available_equipment` results they didn't before.** This is the correct behavior. No risk of data loss.
- **Armies that were previously *invalid* become valid after the fix.** The `geir_arne` army is the known case. Any other stored armies should be re-validated.
- **`upgrade_model` at build time is unaffected in interface** — it already passes the pre-upgrade model to `_remaining_slots`, so D2 doesn't change its behavior. D1 changes its slot accounting (defaults no longer consumed), which is the desired correction.
