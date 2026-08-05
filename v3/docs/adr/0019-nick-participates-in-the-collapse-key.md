# A Nick participates in the collapse key, with no special-casing

A Nick used to name one thing: an Army. Extending it to Unit and Model
instances puts it in front of two pieces of machinery that already decide when
two instances are "the same thing" — `_collapse_units` in
`spf.render.army_rules`, which merges identical `UnitEntry`s into
`Ork Infantry (3×)`, and the dedup key in `spf.render.cards.build_deck`, which
stops a Unit from printing the same order card twice.

Both keys are built from the rendered name. So the question is not *whether* a
Nick reaches them — it does, the moment a nicked instance renders — but whether
they should be taught to ignore it.

## The Nick is part of the name, and the name is part of the key

**Decision: the Nick enters `UnitEntry.name`, `ModelEntry.name`, and the
`build_deck` dedup key through one `display_name` property — `self.nick or
self.config.name` — and the collapse rules see it as they see any other name.
No branch anywhere asks "is this a Nick?".**

That single definition of the fallback is what makes the rest fall out:

- Identical un-nicked Units still collapse to `Ork Infantry (3×)`. No
  regression, and `_collapse_units` and `build_deck` are unchanged.
- Differently-nicked Units each get their own entry and their own card set.
  That is the point of having nicked them: you named them to tell them apart at
  the table, so each one gets a card to put beside its models.
- Identical Units sharing a Nick collapse to `Boyz (2×)` — a legitimate way to
  name a pair as one formation.

The same rule holds a level down: `model_summary` becomes
`["1x Grubnak", "3x Ork Infantry"]`, and a nicked Model gets its own
`ModelEntry` block even when its stats are identical to its squadmates'.

A Nick **replaces** the catalogue name outright — there is no
`Boyz (Ork Infantry)` parenthetical. The army-rules document is self-contained,
and the model summary line still reveals what the Unit is made of.

## Alternatives rejected

**Collapse on catalogue identity and list the Nicks inside the merged entry.**
Fewer pages, and the army-rules document would still name every Unit. But an
order card carries one name, so under this rule a Nick could never appear on a
card at all — and a card you cannot match to the models in front of you is the
thing the Nick existed to fix.

**Strip the Nick from the key but keep it in the rendered name.** Two entries
that collapse to one would then disagree about what to print, and the merged
entry would have to pick a winner. A key that ignores what it renders is a bug
waiting for its first duplicate.

## Consequences

- **Nicking costs pages and cards.** An army with three differently-nicked
  copies of one Unit prints three Unit entries and three card sets where it used
  to print one. This is accepted: the player asked for the distinction.
- **A Nick belongs to the slot, not the model type.** `upgrade_model` and
  `upgrade_unit` both preserve it, so a nicked Model promoted to an upgrade
  model keeps its Nick even though `upgrade_unit` resets `upgrades=[]` — that
  reset exists for a rules reason, and a Nick carries no rules weight.
- **A duplicate is un-nicked**, at Unit *and* Model level: a Nick names one
  instance, so it does not travel with a copy. `duplicate_unit(nick=…)` names
  the copy in the same call.
- **Addressing is untouched.** Instances are still addressed by
  `(toml_key, occurrence)`, and Image Assets are still looked up by TOML key.
  Nicking changes what renders, never what resolves.
- **Old army JSON needs no migration**: a Nick is omitted from the file when
  unset and read back with `.get`, so the committed armies regenerate
  byte-identically.
