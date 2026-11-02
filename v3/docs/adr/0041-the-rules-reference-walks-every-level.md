# The Rules Reference walks every level

> [ADR-0042](0042-rule-links-are-authored-never-inferred.md) adds edges: the walk
> also seeds from the Rule Links in printed prose and follows them from a Record's
> `effect` and `remove`. Everything else here still stands.

From the rules an Army's Specials name, the walk follows `places` and `see_also`
unbounded, with a visited-set. This supersedes
[ADR-0029](0029-the-rules-reference-promotes-see-also-by-namespace.md)'s one-hop
`see_also` bound and its promotion by namespace. It applies to the Army
Reference, Army Pack and Race Overview, which share one resolution. ADR-0029's
"one entry per Record" still stands.

## Why

A player should be able to follow every reference inside the document. With
every level walked, every `see_also` target is an entry, so each line is a
working link and the dead-end case ADR-0029 described disappears. A promotion
rule is no longer needed, nor the distinction it drew between a thing on the
table and an editorial pointer.

## Cost

ADR-0029 rejected this for size, and the cost is real. Rules Reference entries
per showcase Army:

| Army | one hop, promoted | every level |
| --- | --- | --- |
| abomination | 36 | 50 |
| darkelf_dragon_flight | 27 | 38 |
| darkelf_mechahydra | 32 | 48 |
| darkelf_spider_swarm | 19 | 43 |
| dwarf | 30 | 39 |
| elf | 21 | 42 |
| gnome_air_wing | 30 | 39 |
| gnome_ballista_battery | 16 | 36 |
| goblin | 29 | 44 |
| ogre_hydra | 32 | 46 |
| ork_warband | 19 | 32 |

Smaller Armies roughly double, and an Army's list now prints rules it does not
field, such as Heal and Repair. Race Overviews grow from 54–67 entries to 60–78.
The list stays flat and alphabetical, with no marking for pulled-in rules.

## Rejected: a separate "related rules" section

The glossary keeps the **Rules Reference** flat, and a second section adds a
distinction players then need to learn.
