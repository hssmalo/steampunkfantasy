# The build tier is a functional core; race_config is never stored

Extends [ADR-0001](0001-two-tier-army-model.md), which records *that* the build
and resolved tiers are separate. This one records how the build tier behaves.

`ArmyModel`, `ArmyUnit` and `ArmyList` are all `@dataclass(frozen=True)`. Every
mutation — `upgrade`, `upgrade_model`, `upgrade_unit`, `upgrade_full_unit`,
`upgrade_all_models`, `add_unit`, `nick_unit`, `nick_model`, `duplicate_unit`,
`delete_unit` — returns a **new** instance built with `dataclasses.replace`
rather than changing the receiver. A caller that wants the old army back keeps
the old value; nothing has to be copied defensively or undone.

The Race catalogue reaches these methods as a keyword-only `race_config`
argument and is **never stored** on a build object. Mutations that need the
catalogue take it per call; ones that do not (`nick_unit`, `nick_model`,
`duplicate_unit`, `delete_unit`) never mention it.

**Why:** the build tier is where the player's choices accumulate, so it is the
one place where a stale or aliased value causes silent, hard-to-trace damage.
Making every step a value transformation means an `ArmyList` is fully described
by what it holds: two lists built the same way are equal, and any of them can be
serialized, cached or compared without asking where it came from.

## Storing `race_config` on `ArmyList` was rejected

It would remove the argument from a dozen signatures, and it was rejected
anyway. A `RaceConfig` field makes `ArmyList` impure data — it stops comparing
by value, it stops serializing cleanly, and the army becomes bound to one
particular in-memory catalogue instance rather than to the race it names. The
build object names its race as `race: RaceName`; resolving that name to a
catalogue is the caller's job, once, at the call site.

## `ArmyModel` still carries its `ModelConfig`

The never-store rule covers the *catalogue*, not the Model's own config.
`ArmyModel.config` is present (with `repr=False`) so that Holder capacity and an
Equipment's `requires` can be checked inside `upgrade()`, at the moment the
purchase is attempted.

Validating only at `resolve()` time was rejected: it would report an illegal
purchase far from the call that made it, and the build tier's whole reason for
holding config at all is to catch a bad choice while it is still one choice.
