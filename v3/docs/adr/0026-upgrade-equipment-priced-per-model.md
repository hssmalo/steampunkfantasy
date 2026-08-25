# Upgrade Equipment is priced per Model unless it is a Unit Fixture

Extends [ADR-0020](0020-defaults-yield-holders-to-upgrades.md), which records
that retained Defaults are free and that `Unit.cost()` prices Upgrades only.
This one records *how* those Upgrades are priced.

`Unit.cost()` is the authority on what a Unit costs. It walks the Unit's Models
and charges each Upgrade Equipment in one of two ways, chosen by that
Equipment's `upgrade_all` flag:

- **`upgrade_all = False` — per Model.** Every Model carrying the Equipment adds
  its `cost` again. Arming all four Models of a four-Model Unit with the same
  weapon therefore costs four times the listed price.
- **`upgrade_all = True` — per Unit.** The Equipment is charged once for the
  whole Unit, however many of its Models carry it. This is the **Unit Fixture**
  of `CONTEXT.md`.

**Why:** most Equipment is a thing each Model holds, and paying per Model is the
only pricing that matches what is on the table. Some Equipment is a single
Unit-wide fitting that the data has to hang off the Models anyway, because a
Model is the only thing Equipment attaches to. Charging it once per Unit prices
what the player actually bought, and keeping the distinction in the catalogue
rather than in the pricing code means a new Unit-wide item is a data change.

## The Fixture dedup is across Models, not within one

`Unit.cost()` deduplicates a Fixture by Equipment name as it walks the Unit's
Models, but it folds each Model's newly-seen names into the running set only
*after* that Model's Equipment loop. Two copies of the same Fixture on a
*single* Model are therefore charged twice, while one copy on each of four
Models is charged once.

This is a consequence of the loop's shape rather than a decision, and it
disagrees with `Unit.armor`, which dedupes the same Fixtures against a set it
updates immediately. Nothing stops a player reaching it: `ArmyModel.upgrade()`
appends unconditionally, so the same Equipment can be bought twice on one Model
whenever its Holders have room. The rule this ADR records is the per-Unit one;
where the code charges twice, the code is wrong and not the record of a
deliberate choice.

## `upgrade_all` is required wherever a `cost` is

`EquipmentConfig.upgrade_all` is typed `bool | None`, but
`check_upgrade_all_matches_cost` requires it be set if and only if `cost` is
set. Every priced Equipment therefore states its pricing explicitly and nothing
falls back to a default; costless Default Equipment, which is never priced at
all, must leave it unset.

## Multiplying by the Unit's declared `size` was rejected

The obvious per-Model formula is `cost × unit.config.size`. It is wrong: **Size**
is a categorical value in the game data, not a count of Models. The runtime
length of `unit.models` is the correct multiplier, and it is also the one that
stays right when a Unit's Models are replaced by Upgrade Models.

## `Model.cost()` is intrinsic and deliberately incomplete

`Model.cost()` sums the Model's own Upgrade Equipment costs and knowingly
ignores `upgrade_all` — a Model cannot see its siblings, so it cannot know
whether a Fixture has already been paid for. Only `Unit.cost()` has the whole
Unit in view, so only `Unit.cost()` is authoritative. Summing `Model.cost()`
across a Unit over-charges every Fixture.
