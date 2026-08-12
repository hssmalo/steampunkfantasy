# Default Equipment yields Holders to Upgrades, per Holder

Supersedes [ADR-0002](0002-equipment-discard-rule.md), which discarded *all* of
a Model's Default Equipment as soon as it bought *any* Upgrade.

A Model's **effective equipment** is all of its Default Equipment plus all of its
Upgrade Equipment, minus those Defaults that must be evicted so the remaining
claims fit within the Model's Holder limits. `Model.equipment` returns the
survivors first, in catalogue order, then the Upgrades in purchase order.

**Why:** the old rule read "an Upgrade replaces the Default it sits on" as "an
Upgrade replaces everything", which is only right when the two occupy the same
Holder. Abomination Infantry has `Hands:2` *and* `Tentacles:4`; buying a
Tentacles mortar has nothing to do with the gun in its hands, and there was no
way to get the gun back — Defaults are costless, and `ArmyModel.upgrade()`
rejects costless equipment, so a discarded Default was gone for good. Eviction
is therefore decided per Holder: freeing `Hands` never drops a `Tentacles` item.

## Upgrades never yield

Only Defaults are evictable. Upgrades claim their capacity first and keep it —
the player paid for them, and a purchase that silently un-made an earlier
purchase would be worse than either rule it replaced.

## A Default that claims no Holder is permanent

Equipment with no requirements occupies nothing, so nothing can crowd it out. It
now survives every Upgrade. This is the largest behavioural change in the rule:
roughly forty equipment entries across thirty Models, mostly vehicle main guns,
which the old rule threw away the moment a vehicle bought anything.

## Upgrade legality is deliberately unchanged

An Upgrade is legal iff the **Upgrades alone** fit the Model's limits.
`_remaining_slots` ignores Defaults and must keep ignoring them: counting them
would make previously-legal purchases illegal and retroactively invalidate every
saved Army. Defaults yield after the fact instead of blocking a purchase.

## Eviction is declaration-order first-fit, with no tolerance

Defaults are walked in the order the Model declares them; each is kept if it
still fits and dropped if it does not. This is not a search for the best set to
evict — first-fit is easy to reason about, and the order can be revisited if it
ever produces a bad loadout at the table.

Capacity is exactly what the Model declares. Seeding each Holder with
`max(declared_limit, total_default_claims)` was considered, so that a Default
could only ever yield to an Upgrade, and rejected: it buys protection against
bad data at the price of a special case in the one function everything else
reads. The `default-equipment-limit` lint rule guards the data instead.

**Consequence:** a Model whose Defaults over-claim its own limits loses one even
with zero Upgrades bought. That is a data defect, it is reported by
`spf race lint`, and it is fixed in the TOML rather than tolerated in code.

**Consequence:** retention is derived on every read, never stored. Army JSON
keeps its `{name, upgrades, nick}` shape, so there is no migration and no stale
state when a player adds or removes an Upgrade.

**Consequence:** saved Armies change what they carry — specials, assault stats
and orders all move as retained Defaults reappear. They do not change what they
cost: `Unit.cost()` prices Upgrades only, and retained Defaults are free.
