# Agent Guidance

This file provides guidance to AI agents when working with code in this repository.

> **Note:** Not all TOML files in races are valid, some still use a legacy format. Run `uv run spf race list` to get a list of the currently valid TOML files.

## Commands

```bash
# Run CLI
uv run spf --help
uv run spf race show goblin  # Validates TOML file, here races/goblin.toml

# Run tests
uv run pytest

# Lint and format
uv run ruff check src/
uv run ruff format src/

# Type checking
uv run pyright

# Spell checking
uv run typos
```

## Architecture

**SteamPunkFantasy (spf)** is a tabletop hex-based wargame army management tool. It reads information about races from TOML files and validates/displays them.
