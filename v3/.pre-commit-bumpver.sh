#!/bin/sh
# Re-lock after the version bump, so `uv.lock`'s own `spf` entry does not stay
# on the old version. Run by bumpver from the repository root, hence the paths.
# `set -eu`: without it a failed `uv lock` would still exit 0 through the
# `git add` below, and bumpver would tag and push a release with a stale lock.
set -eu
uv lock --project v3
git add v3/uv.lock
