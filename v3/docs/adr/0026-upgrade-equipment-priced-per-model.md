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

## A Fixture's multiplicity is its purchase count

A Unit Fixture is not a yes/no. It is bought *for the whole Unit* — one purchase
equips every Model with one copy, and each copy claims a Holder on the Model
carrying it — and **it may be bought more than once**. N purchases cost N × Cost
and apply their effects N times.

`Unit.fixture_purchases` is the one place that answers how many purchases a Unit
holds, and `Unit.cost()` and `Unit.armor` both read it. They are not the last
two traversals that will need the answer, and the rule drifting apart across
hand-written walks of the same Models is how the rule broke once already:
`cost()` charged the copies found on the first carrying Model, while `armor`
collapsed every copy to a single application.

The count is the **maximum** number of copies on any single Model, not the count
on the first one. Promoting a Model resets its `upgrades` to `[]`, so a Unit can
go ragged without anyone buying or selling anything, and what the Unit paid for
is what survives on the Models that were not promoted.

A ragged Unit is refused by the builder and tolerated at load.
`ArmyUnit.upgrade_model()` raises for a Fixture, because a frontend that could
sell half a Fixture would be selling something the rules have no price for;
`io.load_army()` accepts a ragged Army that already exists on disk, because
validity is referential (ADR 0036) and historical Armies stay loadable.

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
