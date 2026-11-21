# PROTOTYPE: how a token's damage table reads (#240)

Throwaway prototype for the wayfinder ticket "How a token's damage table
reads", on the map "Wayfinder: formalized damage tables and effect tokens"
(#237). It lives on a throwaway branch and is never merged.

Each file is the rulebook's **Tokens** section with the five Continuing Damage
tokens re-laid out, in rulebook order, as Markdown. It reads PR #235 as merged
(Bleed Raises instead of placing a new Bleed). Rule Links print as plain
labels, so judge the layout, not the links.

| Variant | Die / resistance       | Shared rider                     | Poison              |
| ------- | ---------------------- | -------------------------------- | ------------------- |
| [A](A-unit-card-mirror.md)   | Line above the table   | Repeated as notes on each token  | Table, `Any` row    |
| [B](B-rider-written-once.md) | Line above the table   | Written once, "Continuing Damage" | Prose              |
| [C](C-die-in-header.md)      | First column's header  | Written once                     | Table, `Any` row    |
| [D](D-one-overview-table.md) | A column in one table  | Written once, under that table   | Row in that table   |

## Things to react to

1. **Die line:** above the table (A, B) or in the header (C, `d6 − fire
   resistance`)? C gives each table one self-contained block, and in the
   TOML it would be a single field on the table.
2. **Rider:** repeated (A) or written once (B, C, D)? Written once creates a
   term, **Continuing Damage**, that rows cite: "Deal the roll as Continuing
   Damage". In A the rows say "Deal the roll as Regular damage" and the notes
   do the rest.
3. **Row wording:** "3+: Deal the roll as Regular damage" (A) vs "3+: Deal
   the roll as Continuing Damage" (B, C). Also "Remove this Bleed" vs a
   generic "Remove this token".
4. **Poison:** a one-row `Any` table (A, C), prose (B), or a row with no
   removal threshold (D).
5. **Acid rows:** cumulative "As 2, and …" (A, C, D) vs spelled out in full
   (B, very wide). The simulator's parser would need to understand "As N".
6. **Fire's low row:** "2 or less", not "1-2", because fire resistance can
   push the result to 0 or below. Should the row grammar allow "N or less"?

## Found while prototyping (not layout, but they affect the tables)

- **The rider is not uniform.** "Removed if it killed a Model" holds for
  Bleed and Poison, but today's Fire text does not say it, and neither does
  the simulator. So it is a per-token note, not part of the shared rider.
  Minor Acid and Acid deal no damage, so the rider doesn't apply to them.
- **Acid resistance.** The simulator subtracts acid resistance from the Acid
  and Minor Acid rolls (`docs/damage_simulator.md`), but the rulebook text
  does not mention it. The prototype follows the rulebook. One of them is
  wrong.
