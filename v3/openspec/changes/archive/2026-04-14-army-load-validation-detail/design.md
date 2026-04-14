## Context

Validation of army equipment upgrades happens in `validate_army` (`src/spf/armies/data.py`). When equipment requires are unsatisfied, it calls `_satisfies_requires` which returns a plain boolean. The caller produces a generic error string: `"equipment '{key}' requires are not satisfied"`.

The `requires` field on an `EquipmentConfig` is a list of OR-groups (CNF): every outer group must have at least one satisfied inner `Requirement`. A requirement is either a type check (`type:<ModelType>`) or a slot-count check (`<holder>:<count>`). Slot availability is tracked by `_remaining_slots`, which subtracts consumed slots from the model's `equipment_limit`.

## Goals / Non-Goals

**Goals:**
- Replace the boolean `_satisfies_requires` with a helper that returns the specific OR-group(s) that failed.
- Update `validate_army` to embed those failing groups in the error string.
- Update tests to assert on the new message shape.

**Non-Goals:**
- Changing the set of armies or equipment that fails validation.
- Reporting *all* possible ways to satisfy a failed group (e.g., "you need Infantry OR Grunt").
- Altering the CLI exit code or error formatting.

## Decisions

### Return failing groups instead of a boolean

Rather than split `_satisfies_requires` into separate "check" and "describe" paths, replace it with a function that returns the list of OR-groups that failed evaluation. An empty list means "all satisfied". This keeps logic in one place and makes the error description a simple formatting step.

*Alternative considered*: keep the boolean and add a separate `_describe_failure` function. Rejected—it duplicates the evaluation logic and must stay in sync.

### Format failing requirements as human-readable strings

Each failing group is formatted as `"<key>:<value> or <key>:<value>"` joining the group's alternatives with " or ". For slot requirements, include available slots: `"Hands:2 (have 0)"`. For type requirements, omit slot detail: `"type:Infantry or type:Grunt"`.

*Alternative considered*: show only the first failing group. Rejected—if both a type group and a slot group fail, the user needs both pieces of information.

## Risks / Trade-offs

- [Test brittleness] → Error message strings are asserted in tests; they must be updated. Low risk: tests are co-located and easy to update.
- [Over-reporting] → If a model has multiple equipment upgrades and each fails, the error list grows long. Acceptable—each error line already names the specific equipment item.

## Open Questions

- None.
