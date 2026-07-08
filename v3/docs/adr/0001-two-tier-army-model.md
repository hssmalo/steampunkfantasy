# Two-tier army model: build tier and resolved tier

The tool serves two distinct uses: **building** an army (choosing units, swapping
models, adding equipment upgrades) and **referencing** an assembled army's rules
during play. We model these as two hierarchies rather than one.

- **Build tier** — `ArmyList` / `ArmyUnit` / `ArmyModel` (in `spf.armies.build`).
  Mutable-friendly, immutable dataclasses that hold the `UnitConfig` /
  `ModelConfig` and equipment upgrade *keys*. They keep enough of the Race
  catalogue to validate slot requirements while the army is being assembled.

- **Resolved tier** — `Army` / `Unit` / `Model` (in `spf.armies`). Produced by
  `ArmyList.resolve(race_config)`, which turns every equipment name into an
  embedded `EquipmentConfig`. The result is fully self-contained: cost, specials,
  assault, and display need no `race_config` afterward.

**Why:** the two tiers mirror the two uses. The build tier needs the catalogue to
validate choices; the resolved tier is far simpler to consume for reference and
display because it carries all its own state. The alternative — one mutable model
that looks everything up in the Race lazily — would entangle the two uses and
thread `race_config` through every read.
