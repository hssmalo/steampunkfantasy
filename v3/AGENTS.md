# Agent Guidance

This file provides guidance to AI agents when working with code in this repository.

> **Note:** Currently only abomination, goblin, and ogre are playable races

## Commands

```bash
# Run CLI
uv run spf --help
uv run spf show-race goblin

# Run tests
uv run pytest

# Lint and format
uv run ruff check src/
uv run ruff format src/

# Type checking
uv run ty check src/

# Check typos
uv run typos
```

## Architecture

**SteamPunkFantasy (spf)** is a tabletop hex-based wargame army management tool. It reads information about races from TOML files and validates/displays them.
