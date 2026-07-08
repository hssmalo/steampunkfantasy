# TOML for race catalogues, JSON for saved armies

Race definitions live as hand-authored **TOML** files in `races/` (one per
Race). Saved armies are serialized to **JSON** in `armies/`.

**Why:** the two datasets have different authors. Race catalogues are written and
edited by humans maintaining the rulebook, and TOML's tables, comments, and
multi-line strings suit that hand-authoring well. Armies are produced by the tool
(the builder and scripts) and read back by it, so JSON is a clean, ubiquitous
machine round-trip with no hand-editing ergonomics to preserve.
