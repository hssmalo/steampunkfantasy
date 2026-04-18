# Spec: Resolved Army

## Purpose

Defines the resolved tier of the army type hierarchy: `Model`, `Unit`, and `Army`. These types carry fully resolved, self-contained state — all equipment names are resolved to `EquipmentConfig` objects at construction time, so no `race_config` is needed for any subsequent computation. The resolution process is defined here, including the equipment discard rule, specials merging, assault stacking, and cost methods.

## Requirements

### Requirement: Model exposes effective equipment using the discard rule
A resolved `Model` SHALL hold `default_equipment: tuple[EquipmentConfig, ...]` (resolved from `ModelConfig.equipment` at build time) and `upgrade_equipment: tuple[EquipmentConfig, ...]` (resolved from `ArmyModel.upgrades` at build time). The `equipment` property SHALL return `upgrade_equipment` when non-empty, otherwise `default_equipment`. This is Rule A: all default equipment is discarded when any paid upgrade is present.

#### Scenario: No upgrades — default equipment returned
- **WHEN** a `Model` has an empty `upgrade_equipment`
- **THEN** `model.equipment` SHALL return `model.default_equipment`

#### Scenario: Any upgrade present — defaults discarded
- **WHEN** a `Model` has one or more entries in `upgrade_equipment`
- **THEN** `model.equipment` SHALL return `model.upgrade_equipment` and SHALL NOT include any entry from `model.default_equipment`

### Requirement: Model exposes stacked unit and model specials
`Model.unit_specials` SHALL return a `dict[UnitSpecial, str]` formed by merging: `model.config.unit_special`, then each `equip.unit_special` for equipment in `model.equipment` in order. Later entries override earlier ones. `Model.model_specials` SHALL return a `dict[ModelSpecial, str]` formed by merging `model.config.special`, then each `equip.model_special` in order.

#### Scenario: Equipment unit_special overrides model config unit_special for same key
- **WHEN** both `model.config.unit_special` and an equipment's `unit_special` contain the same key
- **THEN** `model.unit_specials` SHALL contain the equipment's value for that key

#### Scenario: Model config model_special preserved when no equipment overrides it
- **WHEN** `model.config.special` has a key that no equipment's `model_special` shares
- **THEN** `model.model_specials` SHALL include that key with its original value

#### Scenario: All equipment specials are merged in equipment order
- **WHEN** two equipment pieces each contribute different keys to `unit_special`
- **THEN** `model.unit_specials` SHALL contain entries from both

### Requirement: Model exposes resolved AssaultConfig via assault()
`Model.assault()` SHALL return a full `AssaultConfig` computed by starting from `model.config.assault` and applying each `EquipmentAssaultConfig` from `model.equipment` in order. Stacker semantics: `add` for `int` (scalar) and `Angles[int]` (element-wise); `replace` for any type; `extend` for list types. `assault()` SHALL raise a descriptive `ValueError` when an invalid stacking operation is attempted: `add` or `extend` on `Die`/`DieResult` (strings), or `add` on `ap` when the current value is `"N/A"`.

#### Scenario: No equipment — base assault returned unchanged
- **WHEN** `model.equipment` is empty
- **THEN** `model.assault()` SHALL return values equal to `model.config.assault`

#### Scenario: add on scalar int ap increases the value
- **WHEN** an equipment has `assault.ap.add = 2` and the base `ap` is `3`
- **THEN** `model.assault().ap` SHALL be `5`

#### Scenario: add on Angles[int] is element-wise
- **WHEN** an equipment has `assault.strength.add = [1, 0, 1]` and base strength is `[3, 2, 3]`
- **THEN** `model.assault().strength` SHALL be `[4, 2, 4]`

#### Scenario: replace overrides the base value entirely
- **WHEN** an equipment has `assault.damage.replace = "2D6"`
- **THEN** `model.assault().damage` SHALL be `"2D6"` regardless of the base value

#### Scenario: add on Die raises ValueError
- **WHEN** an equipment specifies `assault.damage.add` (a `Die` string field)
- **THEN** `model.assault()` SHALL raise a `ValueError` naming the equipment and the invalid operation

#### Scenario: add on ap="N/A" raises ValueError
- **WHEN** `model.config.assault.ap` is `"N/A"` and an equipment specifies `assault.ap.add`
- **THEN** `model.assault()` SHALL raise a `ValueError` naming the equipment and the invalid operation

#### Scenario: assault special dict is merged across equipment
- **WHEN** multiple equipment pieces each contribute entries to `assault.special`
- **THEN** `model.assault().special` SHALL contain all entries, with later equipment overriding earlier for shared keys

### Requirement: Model.cost() returns the intrinsic upgrade cost
`Model.cost()` SHALL return the sum of `equip.cost` for all entries in `model.upgrade_equipment`. Equipment with `cost = None` SHALL NOT be included (default equipment never has a cost). This cost does NOT account for `upgrade_all` pricing; that logic belongs to `Unit.cost()`.

#### Scenario: Model with no upgrades has zero cost
- **WHEN** `model.upgrade_equipment` is empty
- **THEN** `model.cost()` SHALL return `Cost()`

#### Scenario: Upgrade equipment costs are summed
- **WHEN** a model has two upgrade equipment pieces with costs `Cost(mp=2)` and `Cost(cp=3)`
- **THEN** `model.cost()` SHALL return `Cost(mp=2, cp=3)`

### Requirement: Unit exposes stacked unit specials
`Unit.unit_specials` SHALL return a `dict[UnitSpecial, str]` formed by merging: `unit.config.special`, then each `model.unit_specials` for models in `unit.models` in order. Later entries override earlier ones.

#### Scenario: Unit config specials are the base
- **WHEN** no model contributes any unit specials
- **THEN** `unit.unit_specials` SHALL equal `unit.config.special`

#### Scenario: Model unit_specials override unit config for same key
- **WHEN** a model's `unit_specials` contains a key also in `unit.config.special`
- **THEN** `unit.unit_specials` SHALL use the model's value

### Requirement: Unit.cost() returns the full unit cost with upgrade_all semantics
`Unit.cost()` SHALL return the sum of: `unit.config.cost` (or `Cost()` if None), plus upgrade model costs, plus equipment costs applying `upgrade_all` logic. For each model's `upgrade_equipment`: if `upgrade_all is False`, the cost is multiplied by `len(unit.models)`; otherwise the cost is added flat. Model upgrade cost (when a model replaced a default) is added flat per model.

#### Scenario: Unit with no upgrades costs its base cost
- **WHEN** a unit has no model or equipment upgrades
- **THEN** `unit.cost()` SHALL return `unit.config.cost` (or `Cost()` if None)

#### Scenario: upgrade_all=False multiplies by unit size
- **WHEN** one model has an upgrade equipment with `upgrade_all=False` and `cost=Cost(mp=1)`, and the unit has 4 models
- **THEN** `unit.cost()` SHALL include `Cost(mp=4)` for that equipment

#### Scenario: upgrade_all=True adds flat cost once
- **WHEN** one model has an upgrade equipment with `upgrade_all=True` and `cost=Cost(mp=5)`, in a unit with 4 models
- **THEN** `unit.cost()` SHALL include `Cost(mp=5)` for that equipment (not multiplied)

### Requirement: Army.cost() returns the total army cost
`Army.cost()` SHALL return the sum of `unit.cost()` for all units in `army.units`.

#### Scenario: Empty army has zero cost
- **WHEN** `army.units` is empty
- **THEN** `army.cost()` SHALL return `Cost()`

#### Scenario: Army cost equals sum of unit costs
- **WHEN** an army has two units with costs `Cost(mp=3)` and `Cost(mp=7)`
- **THEN** `army.cost()` SHALL return `Cost(mp=10)`

### Requirement: ArmyList.resolve() produces a fully resolved Army
`ArmyList.resolve(race_config: RaceConfig) -> Army` SHALL construct a resolved `Army` by converting each `ArmyUnit` to a `Unit` and each `ArmyModel` to a `Model`, resolving equipment names to `EquipmentConfig` objects using `race_config`. After `resolve()` returns, no `race_config` is needed for any computation on the returned `Army`.

#### Scenario: resolve() produces an Army with all equipment resolved
- **WHEN** `army_list.resolve(race_config)` is called
- **THEN** the returned `Army`'s models SHALL have `default_equipment` and `upgrade_equipment` populated with `EquipmentConfig` objects (not name strings)

#### Scenario: resolve() preserves all unit and model structure
- **WHEN** `army_list.resolve(race_config)` is called
- **THEN** the unit count, model counts per unit, and names SHALL match the original `ArmyList`
