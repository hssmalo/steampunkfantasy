## Context

This change is a pure structural refactor. No functional requirements are added, modified, or removed. All existing specs remain unchanged.

The only structural requirement introduced is the module layout itself.

## ADDED Requirements

### Requirement: Army data is organized into focused modules
The army data package SHALL expose `ArmyModel`, `ArmyUnit`, and `Army` dataclasses, together with their associated functions, from dedicated modules (`model.py`, `unit.py`, `army.py`). The package root (`__init__.py`) SHALL re-export all public names. The `spf.armies.data` sub-module SHALL no longer exist; all callers are migrated to import from `spf.armies` directly.

#### Scenario: Public symbols remain importable from the package root
- **WHEN** a caller imports `from spf.armies import Army, ArmyUnit, ArmyModel`
- **THEN** all three classes are available without any import path changes

#### Scenario: spf.armies.data is removed
- **WHEN** a caller attempts `from spf.armies.data import Army`
- **THEN** an ImportError is raised (the module no longer exists)

#### Scenario: No behavioral changes
- **WHEN** any existing function in the army package is called
- **THEN** it behaves identically to the pre-refactor implementation
