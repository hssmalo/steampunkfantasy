# Rules loading raises Python's regex cache

`spf race show ork` took 16.8 seconds. It had taken a couple. Nothing in `spf`
had changed: the commit that did it was *"tiny tweaks to specials to make
showcase goblin look better"*, which added four keys to `rules/special.toml`.

## The mechanism

`spf.rules._read` loads each registry through `configaroo`'s
`Configuration.parse_dynamic()`, which resolves `{section.key}` placeholders.
For every string value in the file, `configaroo` loops over *every* key in that
same file and runs `re.findall` with a pattern it builds from the key name:

```python
pattern = r"({{{word}(?:![ars])?(?:|:[^}}]*)}})"
for word, replacement in replacers.items():
    for match in re.findall(pattern.format(word=word), text):
```

Because the pattern is built per key, each `findall` is a distinct pattern
string, and Python's `re` module caches exactly **512** compiled patterns.

The loop walks all the patterns in the same order for every string. While a
file flattens to 512 keys or fewer they all stay cached and each is compiled
once. Past 512, the pattern needed next is always the one just evicted, the hit
rate collapses to nothing, and every `findall` becomes a full parse and
compile.

`rules/special.toml` sat at exactly 512 flat keys. The four new keys took it to
516.

Measured across the two commits, timing `race show ork` in-process so that
interpreter startup and import are excluded:

| flat keys in `special.toml` | `re.findall` calls | `spf race show ork` |
| --- | --- | --- |
| 512 | 201,746 | 1.03 s |
| 516 | 203,502 | 14.22 s |

Call volume rose 0.9%. Wall time rose 1279%. 160,928 of those calls now
recompile from scratch.

## Decision

**`spf.rules._read` raises `re._MAXCACHE` to 8192 before loading a registry.**

That is enough headroom for every registry to keep all of its patterns cached,
and it restores the previous timings exactly: the in-process figure goes back to
1.04 s, and `uv run spf race show ork` from 16.8 s to 2.4 s.

## Why here, and not at an entry point

Raising a process-wide interpreter setting looks like entry-point work, and the
first sketch put it in `spf/__main__.py`. It belongs in `_read` instead, for
three reasons.

`_read` is the only place that provokes the problem, so the workaround sits
next to the code that explains it. Anyone who deletes the call has the
adjacent comment and this ADR in front of them.

It covers every caller. The CLI is not the only thing that loads registries —
so do the test suite, the scripts under `scripts/`, and the Streamlit builder
frontend. `just validate` alone runs fifteen registry-loading commands, and at
14.5 s each the difference is three and a half minutes per run.

And it is not an import side effect. A library module that mutates `re` when
imported surprises everyone who imports it; a function that does so when
called, right before the call that needs it, does not.

## Why not the alternatives

**Trim `rules/special.toml` back under 512 keys.** This works exactly once. The
threshold is a Python implementation detail that the rules data has no reason
to know about, and the next Special crosses it again — for a second time,
silently, as a 14× slowdown attributed to whoever happened to add the key.
Rules data must stay free to grow; that is what the file is for.

**Wait for `configaroo`.** The real fix is upstream: one static regex matching
any placeholder, with the field name looked up in the replacers, which removes
both the cache pressure and the quadratic scan. That work is scoped and handed
over, but it is a release of another package, and `just validate` is slow now.

## What this does not fix

The scan is still quadratic — every string is still tested against every key,
203,502 `re.findall` calls for one file. Raising the cache only stops each of
those calls from recompiling; it does not stop them from happening. A registry
that grows several times over will be slow again, on a curve rather than a
cliff.

Loading the seven registries still costs about a second, and roughly half of
`spf`'s remaining import time is a separate `configaroo` problem: `parse_dynamic`
calls `find_pyproject_toml()` — and through it `inspect.stack()` — 43 times per
config load.

## Consequences

- `re._MAXCACHE` is raised for the whole process, not just for `spf`. The cost
  is bounded: a larger cache of compiled patterns, on the order of a few MB in
  the worst case observed here.
- Touching a private name in the standard library means this can break on a
  Python upgrade. It is written to fail soft — if `re` ever stops exposing
  `_MAXCACHE`, the code leaves it alone and the only symptom is the old
  slowness.
- **This is a stopgap.** It is deleted when `configaroo` ships the fix, along
  with the comment in `spf/rules.py` that points here.
