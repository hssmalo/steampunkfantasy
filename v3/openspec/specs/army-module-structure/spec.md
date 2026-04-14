## Purpose

Defines the module layout for the army data package. Army-related dataclasses and their associated functions are organised into focused, single-responsibility modules, with the package root re-exporting all public names for backward-compatible imports.

## Requirements

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
