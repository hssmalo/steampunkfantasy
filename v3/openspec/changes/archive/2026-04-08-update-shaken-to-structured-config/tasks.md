## 1. Migrate abomination.toml

- [x] 1.1 Convert `units.abomination_infantry.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]`
- [x] 1.2 Convert `units.horror.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]`
- [x] 1.3 Convert `units.robot_crab.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]` (mechanical, no speed/movement in string)
- [x] 1.4 Convert `units.giant_frog_riders.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]`
- [x] 1.5 Convert `units.hippopotamus_riders.shaken`: `speed = "fast"`, `movement_order = ["-", "chase", "chase"]`, `fire_order = "Normal"` (fire orders explicitly allowed)
- [x] 1.6 Convert `units.squ.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]`
- [x] 1.7 Convert `units.frost88.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]`

## 2. Migrate goblin.toml

- [x] 2.1 Convert `units.goblin_infantry.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]`
- [x] 2.2 Convert `units.goblin_infantry_carrier.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]`
- [x] 2.3 Convert `units.heavy_carrier.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]`
- [x] 2.4 Convert `units.mechanical_fire_bird.shaken`: `speed = "fast_flying"`, `movement_order = ["-", "F", "F"]`

## 3. Migrate ogre.toml

- [x] 3.1 Convert `units.ogre_infantry.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]`
- [x] 3.2 Convert `units.ogre_robot.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]`
- [x] 3.3 Convert `units.pet_panther.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]`
- [x] 3.4 Convert `units.ogre_assault_scout.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]`
- [x] 3.5 Convert `units.drone_swarm.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "-"]`
- [x] 3.6 Convert `units.repair_drone.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "-"]`
- [x] 3.7 Convert `units.medic_drone.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "-"]`
- [x] 3.8 Convert `units.main_engine.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "-"]`
- [x] 3.9 Convert `units.broadside_wagon.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]` (mechanical, speed/movement inferred — string only says "May not fire weapons")
- [x] 3.10 Convert `units.artillery_wagon.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]` (mechanical, speed/movement inferred — string only says "May not fire weapons")

## 4. Migrate ork.toml

- [x] 4.1 Convert `units.ork_infantry.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]`
- [x] 4.2 Convert `units.troll.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]` (biological, empty string)
- [x] 4.3 Convert `units.champion.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]` (biological, empty string)
- [x] 4.4 Convert `units.warg_rider.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]` (biological, empty string)
- [x] 4.5 Convert `units.speedhead.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]` (mechanical, empty string)
- [x] 4.6 Convert `units.hammerhead.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]` (mechanical, empty string)
- [x] 4.7 Convert `units.battlewagon.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]` (mechanical, empty string)
- [x] 4.8 Convert `units.grunt.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]` (biological, empty string)
- [x] 4.9 Convert `units.ork_werewarg.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]`
- [x] 4.10 Convert `units.bioengineered_ork.shaken`: `speed = "slow"`, `movement_order = ["-", "-", "flee"]` (biological, empty string)
- [x] 4.11 Convert `units.ork_char_b1.shaken`: `speed = "still"`, `movement_order = ["-", "-", "-"]` (mechanical, movement inferred — string says "Speed set to still, cannot use weapons")

## 5. Verify

- [x] 5.1 Run `uv run spf race show abomination` and confirm no validation errors
- [x] 5.2 Run `uv run spf race show goblin` and confirm no validation errors
- [x] 5.3 Run `uv run spf race show ogre` and confirm no validation errors
- [x] 5.4 Run `uv run spf race show ork` and confirm no validation errors
- [x] 5.5 Run `uv run pytest` and confirm all tests pass
- [x] 5.6 Run `uv run ruff check src/` and `uv run ruff format src/`
- [x] 5.7 Run `uv run pyright`
- [x] 5.8 Run `uv run typos`
