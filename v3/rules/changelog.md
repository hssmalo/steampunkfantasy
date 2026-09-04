# Rules changelog

A record of deliberate balance changes to the rules data in `rules/`. It
captures *why* a rule was changed.

| Date | Description | Why |
| ---------- | ------------------------------ | ------------------------------ |
| 04.09.2026 | Multiple Shots states a shot count per fire order, and the "per model" qualifiers are dropped | The qualifiers were misleading: the shots belong to the fire order, not to each model in the unit |
| 03.09.2026 | Focus Fire is the aim option, not the alternative to it, and its number is the dice rolled when aiming | Every weapon carrying it already described its non-aiming fire on another rule, so the rule contradicted its own call sites |
| 24.08.2026 | Added horrifying poison token| Too fun not to add |
| 24.08.2026 | The unnamed -1/+1 critical token is now Critical Damage (`token.critical_damage`) | Its name was a description of its own numbers; a player needs something to call it |
| 24.08.2026 | `special.reroll` is now `special.ork_reroll`, `token.plus_minus_one` is now `token.critical_damage`, and the distance bands are `normal_range` and `long_range` | Each id now spells the name the rule already prints |
| 24.08.2026 | The Angle modifier prints as On Edge rather than On-Edge of Firing-Angle | Its group heading already says Angle |
| 24.08.2026 | Fear moved to the assault slot, Pre-Assault Retreat to the unit slot | Each rule now sits where the Race data uses it |
| 24.08.2026 | Fire, Poison, Minor Acid and Gear Disruption are each two rules: assault_* and range_* | The assault forms count hits and the range forms are flat, so one name hid two rules |
| 24.08.2026 | Protection left the Special vocabulary; Endurance is a rule and a token of its own | Armor grants belong to the armor stat, endurance tokens to a rule that says what they do |
| 19.08.2026 | alpha version of references    | aid rules references.          |
| 11.08.2026 | tweaked to_hit.toml            | Internal logic presentation    |
| 06.08.2026 | bugfixed some possible values  | bugfix                         |
| 06.08.2026 | Aim and Shaken now follow one general first-placement rule; re-aiming an already-aimed unit adds a token instead of nothing | Aim stated the rule in its own words and meant something different; unified so Aim and Shaken behave alike |
| 05.08.2026 | added aim, and added orders    | Completing the rules           |
| 28.07.2026 | Bugfix and added missing       | Bugfix                         |
| 28.07.2026 | Added no command and no repair | Abomination flagship need them |
| 27.07.2026 | Renamed weapons to range       | To fit with army.pdf setup     |
| 27.07.2026 | Tweaked gear disruption        | Unnecessarily complicated      |
| 27.07.2026 | Added assault gear disruption  | For completeness               |
| 27.07.2026 | Added assault fire             | For completeness               |
