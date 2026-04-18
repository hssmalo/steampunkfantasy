## MODIFIED Requirements

### Requirement: Army data is organized into focused modules
The army data package SHALL expose two tiers of types from dedicated modules:

**Build-time tier** (`spf.armies.build`): `ArmyModel`, `ArmyUnit`, and `ArmyList` dataclasses for assembling and mutating armies. These SHALL NOT be re-exported from `spf.armies.__init__` but SHALL be importable via `from spf.armies.build import ArmyList`.

**Resolved tier** (`spf.armies`): `Model`, `Unit`, and `Army` dataclasses that carry fully resolved, self-contained state. These SHALL be the primary public API and SHALL be re-exported from `spf.armies.__init__`.

The resolved types SHALL live in dedicated modules: `model.py` → `Model`, `unit.py` → `Unit`, `army.py` → `Army`. The `__init__.py` SHALL re-export `Army`, `Unit`, `Model`, `ArmyList`, and any remaining public functions (`available_models`, `available_equipment`, `validate_army`). The `spf.armies.data` sub-module SHALL NOT exist.

#### Scenario: Resolved types are importable from the package root
- **WHEN** a caller imports `from spf.armies import Army, Unit, Model`
- **THEN** all three resolved classes are available

#### Scenario: Build-time types are importable from spf.armies.build
- **WHEN** a caller imports `from spf.armies.build import ArmyList, ArmyUnit, ArmyModel`
- **THEN** all three build-time classes are available

#### Scenario: Build-time types are not exposed from package root
- **WHEN** a caller imports `from spf.armies import ArmyUnit`
- **THEN** an `ImportError` is raised (not in `__init__` exports)

#### Scenario: spf.armies.data is removed
- **WHEN** a caller attempts `from spf.armies.data import Army`
- **THEN** an `ImportError` is raised (the module no longer exists)
