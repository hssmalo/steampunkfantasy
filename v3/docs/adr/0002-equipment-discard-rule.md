# Upgrade equipment replaces all default equipment

When a Model has any paid **upgrade** equipment, all of its **default** (free)
equipment is discarded. `Model.equipment` returns `upgrade_equipment` if it is
non-empty, otherwise `default_equipment` — the two are never combined.

**Why:** an upgrade occupies the same slot (hands, mount, hardpoint) as the free
default it replaces, so a paid weapon supersedes the default rather than stacking
on top of it. Modelling this as "any upgrade discards all defaults" keeps loadout
and cost unambiguous.

**Consequence:** there is no partial upgrade — a Model either runs its full
default loadout or a fully player-specified upgrade loadout. Adding a single
upgrade means the player must re-add any default items they want to keep.
