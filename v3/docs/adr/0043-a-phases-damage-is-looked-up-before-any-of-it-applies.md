# A Phase's damage is looked up before any of it applies

`rules/round.md` says everything in a Phase happens at once: "roll all the
damage for a Phase together … and only then remove casualties." The damage
simulator resolves a Phase in two steps to honor that (#248):

1. **Roll and look up.** Every die of the Phase is rolled: hits, every Token's
   die, resistance dice, and any roll a row sets off ("roll again", "d6 psychic
   damage"). A Fire that goes out or a Bleed that stops is removed here. Each
   roll is looked up against the Unit as it stood when the Phase began: its
   Future Damage, its Future Crew Damage, and which table the roll goes to
   (Shaken routing included).
2. **Apply, in layers.**
   1. *Unit destroyed*: if any row says so, nothing else applies.
   2. *Everything else*, in roll order and each row in written order: Tokens,
      Raise, +Future Damage, +Future Crew Damage, spillover.
   3. *Amplify*: every Amplify of the Phase, after all placements and Raises,
      each stepping once.
   4. *Casualties*: kills in roll order, each with its own consequences
      (Endurance, halving Future Damage, the all-temporarily-killed
      replacement, removing the Bleed or Poison that killed). Then Poisons that
      did not kill step down.

The layer order follows `rules/round.md`: effects that remove a Unit come
first, and casualties come last.

The groups are the Phases: all `--start` rolls, one Round's `--incoming` hits,
and each Agony Phase. A run still stops as soon as the Unit is destroyed, but
every roll of the Phase was already looked up, so it counts in the table-roll and
Not-simulated figures.

## Considered options

- **Fix only Future Damage** (look each roll up with the Phase's starting Future
  Damage, then apply every effect straight away in roll order). This fixes the
  case #248 reported, but anything else a row changes still leaks between dice
  that land together, in whatever order the simulator happens to process them.
  With halving on a kill, the rolls +1, +1, kill from Future Damage 2 end at 2
  or 3 depending on which die comes first. With Crippled Crew, a Shaken placed
  by one hit decides whether another hit's psychic roll goes to the Crew table.
- **Also fix the table and wait to halve until the Phase ends.** This fixes both
  examples, but it is an ad hoc list of exceptions. The two-step model states
  one principle, and its layer ordering is written down here, not left implied.

## Consequences

- Where the rules leave a choice to the player, the simulator fixes one. If
  there are fewer Endurance Tokens than kills in a Phase, they save the first
  kills in roll order.
- Shaken placed by two rows of one Phase on an un-Shaken Unit gives 3 Tokens,
  not 4: being newly Shaken happens once.
- Every figure the simulator reports moves. Fire already rolled all its dice
  first, but its Future Damage used to leak from one Fire to the next.
