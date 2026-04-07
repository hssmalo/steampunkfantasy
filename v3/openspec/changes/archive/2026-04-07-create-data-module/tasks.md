## 1. Create `data.py` module

- [x] 1.1 Create `src/spf/data.py` with `list_armies()` function that scans the data directory for TOML files and returns army names
- [x] 1.2 Add `get_race(army_name)` function returning `RaceConfig` for a given army
- [x] 1.3 Add `get_units(army_name)` function returning `dict[str, UnitConfig]` filtered by race
- [x] 1.4 Add `get_models(army_name)` function returning `dict[str, ModelConfig]` filtered by race
- [x] 1.5 Add `get_equipments(army_name)` function returning `dict[str, EquipmentConfig]` filtered by race
- [x] 1.6 Re-export `get_army` from `armies.py` in `data.py` for a single import point

## 2. Tests

- [x] 2.1 Write tests for `list_armies()` verifying it returns known army names
- [x] 2.2 Write tests for `get_race()` verifying correct `RaceConfig` is returned
- [x] 2.3 Write tests for `get_units()` verifying race filtering and return type
- [x] 2.4 Write tests for `get_models()` verifying race filtering and return type
- [x] 2.5 Write tests for `get_equipments()` verifying race filtering and return type
- [x] 2.6 Write test for error case when invalid army name is given to `get_race()`
