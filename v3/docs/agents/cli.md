# The `spf` CLI

The `spf` CLI reads race definitions from TOML files in `races/` and
validates/displays them. Use it to inspect units, models, and equipment.

> **Note:** Not all TOML files in `races/` are valid — some still use a legacy
> format. Run `uv run spf race list` to get the list of currently valid TOML
> files.

```console
uv run spf --help
uv run spf race show goblin  # Validates TOML file, here races/goblin.toml

# List all things (units, models, equipment)
uv run spf race things goblin

# See all details for a given unit, model, or equipment
uv run spf race show goblin units.goblin_infantry
uv run spf race show goblin models.goblin_infantry
uv run spf race show goblin equipment.goblin_bow
```

## Assets

Generating, refining, and promoting Assets. Candidates are addressed by
**Lineage** — a dotted 1-based index that both `--from` and `--pick` take.

```console
# What's left? One row per Target, with its Asset status and Candidate count.
# Omit the race to cover every validating race; --kind narrows to one kind.
uv run spf assets list goblin
uv run spf assets list goblin --candidates   # expand rows into Lineages

# Generate Candidates for a race, or one unit of it (--count, --seed)
uv run spf assets image goblin
uv run spf assets image goblin goblin_infantry
# -> candidates/goblin/images/goblin_infantry.{1,2,3}.png

# Cover several Targets at once. At most one selector may be given.
uv run spf assets image goblin --all       # the race and every unit
uv run spf assets image goblin --missing   # every Target with no Asset yet

# Refine one Candidate by applying a Correction to it. The Correction is the
# whole prompt, verbatim; results land under the derived name <NAME>.<LINEAGE>.
uv run spf assets refine goblin image goblin_infantry --from 2 \
    "make the hat brass instead of leather"
# -> candidates/goblin/images/goblin_infantry.2.{1,2,3}.png

# Refinements chain, because the result is itself a Candidate
uv run spf assets refine goblin image goblin_infantry --from 2.1 "..."
# -> ...goblin_infantry.2.1.{1,2,3}.png

# Promote exactly one Candidate into the committed store
uv run spf assets promote goblin image goblin_infantry --pick 2.1
# -> assets/goblin/images/goblin_infantry.png
```

Refinement needs a `refine_workflow` authored for the selected Environment
(`assets.image.comfyui.env`); see `workflows/README.md`. It is available only
for kinds whose Service implements it — currently image alone.
