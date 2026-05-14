## Context

The `ArmyList` class in `src/spf/armies/build.py` provides immutable builder methods for assembling armies. Currently, single-unit mutations like `.upgrade_unit()` and `.upgrade_model()` require one call per model slot. Build scripts frequently need to perform the same action on all models in a unit (e.g., upgrade 4 infantry to elite simultaneously), leading to repetitive boilerplate.

The proposed convenience methods are pure additions—they wrap existing methods and don't change current API semantics.

## Goals / Non-Goals

**Goals:**
- Reduce boilerplate for common "apply-to-all" operations on units
- Maintain immutability and functional composition (all methods return new ArmyList)
- Fail-fast on validation errors (prevent partial upgrades)
- Complete CRUD: enable creating, duplicating, and deleting units in fluent chains

**Non-Goals:**
- Batch operations across multiple units
- Performance optimization
- Modify existing method signatures or behavior
- Add builder pattern classes or fluent interfaces beyond method chaining

## Decisions

### Decision: Implement as ArmyList methods only (not ArmyUnit)

**Rationale**: Users build at the ArmyList level. Adding convenience methods here keeps the API surface minimal and consistent with existing `.upgrade_unit()` and `.upgrade_model()` which also live at ArmyList level.

**Alternatives**: Could also add at ArmyUnit level for users building units in isolation—but the showcase script uses ArmyList, and duplication would increase maintenance burden.

### Decision: .upgrade_full_unit() loops through model slots, calling .upgrade_unit() for each

**Rationale**: Reuses existing validation logic without duplication. Each model slot is upgraded sequentially, so after upgrading slot 0, the "first occurrence" of the original model name now refers to slot 1.

**Pseudocode**:
```
for i in range(len(unit.models)):
    get current model name at slot i from updated army
    call upgrade_unit(unit_key, (model_name, 0), upgrade_model_name, race_config)
    store result
return final result
```

**Alternatives**: Could bulk-replace all models at once without looping—but the sequential approach mirrors the existing API and reuses validation.

### Decision: .upgrade_all_models() applies sequentially without pre-validation

**Rationale**: Immutability guarantees safety. If model 3 can't take the equipment, the exception propagates, and the caller receives an unchanged original ArmyList (not a partially upgraded one). Pre-validation adds complexity without preventing actual partial upgrades.

**Pseudocode**:
```
for each model slot in unit:
    call upgrade_model() to add equipment
    (if this raises, exception propagates, original is unchanged)
return final result
```

**Alternatives**: Could pre-validate all models before applying (more explicit but unnecessary overhead). Could skip models that can't upgrade (less conservative).

### Decision: .duplicate_unit() appends one copy (not multiple)

**Rationale**: Simpler, chainable API. Users call it once per duplicate needed: `.duplicate_unit(...).duplicate_unit(...)`.

**Pseudocode**:
```
resolve unit by key
create new ArmyUnit with same name, config, models
append to units tuple
```

**Alternatives**: Could take a `count` parameter—but off-by-one confusion in scripts ("duplicate 3 times" = 4 total or 3?).

### Decision: .delete_unit() removes by key, raises KeyError if not found

**Rationale**: Consistent with existing `.upgrade_unit()` and `.upgrade_model()` which also raise KeyError on missing keys. Prevents silent failures.

**Pseudocode**:
```
find unit index by key (raises KeyError if not found)
remove from units tuple
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| User confusion: "upgrade all models" could mean "upgrade to different models per slot" | Naming is clear: `.upgrade_full_unit()` for model replacement, `.upgrade_all_models()` for equipment. Docstrings explain. |
| Sequential loop creates many intermediate ArmyList objects (memory churn) | Trade-off accepted: convenience > performance for build-time code. Build scripts aren't performance-critical. |
| .duplicate_unit() must find original unit twice (once to read, once to append) | Acceptable: two O(n) scans, n is small (typically <10 units). |

## Migration Plan

**Deployment**: Add four new methods to ArmyList. No breaking changes.

**Rollout**: Direct—methods are opt-in. Existing code continues to work unchanged.

**Testing**: Unit tests for each method (success paths + validation failures).

## Open Questions

None.
