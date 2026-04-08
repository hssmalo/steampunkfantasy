# Agent Guidance

This file provides guidance to AI agents when working with code in this repository.

> **Note:** Currently only abomination, goblin, ogre, and ork are working TOML files. The other races use a legacy format.

## Commands

```bash
# Run CLI
uv run spf --help
uv run spf race show goblin

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
