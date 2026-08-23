"""PROTOTYPE — throwaway. Wayfinder ticket #112.

Parses the three candidate TOML shapes, resolves each to the SAME normalised
instance model, prints them, and asserts the three agree. If they agree, the
shapes are equally expressive and the choice is purely ergonomic.

Run:  python3 prototypes/special-instance-shape/render.py
"""

import tomllib
from pathlib import Path

HERE = Path(__file__).parent
SLOTS = ("specials", "unit_specials", "model_specials", "assault_specials", "range_specials")


def find_slots(node, path=()):
    """Yield (source_path, slot_name, raw_value) for every *_specials table."""
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        if key in SLOTS:
            yield ".".join(path), key, value
        else:
            yield from find_slots(value, (*path, key))


def instances(shape, raw):
    """Normalise one slot's raw value into a list of (id, body) pairs."""
    if shape == "A":  # list of tables, id is a field
        return [(i["id"], {k: v for k, v in i.items() if k != "id"}) for i in raw]
    if shape == "B":  # handle -> table, id is a field
        return [(i["id"], {k: v for k, v in i.items() if k != "id"}) for i in raw.values()]
    if shape == "C":  # id -> list of tables, id is the key
        return [(ident, i) for ident, lst in raw.items() for i in lst]
    raise ValueError(shape)


def normalise(shape, path):
    """Resolve a whole file to a comparable sorted list of instances."""
    data = tomllib.loads(path.read_text())
    out = []
    for source, slot, raw in find_slots(data):
        for ident, body in instances(shape, raw):
            out.append(
                {
                    "source": source,
                    "slot": slot,
                    "id": ident,
                    "name": body.get("name"),
                    "args": body.get("args", {}),
                    "text": body.get("text"),
                    # B targets a handle, A/C a bool — compare only "is a replace"
                    "replace": bool(body.get("replace", False)),
                }
            )
    return sorted(out, key=lambda i: (i["source"], i["slot"], i["id"], str(i["args"]), str(i["text"])))


FILES = {
    "A": HERE / "shape_a_array_of_tables.toml",
    "B": HERE / "shape_b_local_handle.toml",
    "C": HERE / "shape_c_id_keyed_arrays.toml",
}

resolved = {shape: normalise(shape, path) for shape, path in FILES.items()}

for inst in resolved["C"]:
    flavour = f'  aka "{inst["name"]}"' if inst["name"] else ""
    mark = "  [REPLACE]" if inst["replace"] else ""
    args = ", ".join(f"{k}={v!r}" for k, v in inst["args"].items()) or "-"
    print(f"{inst['source']} .{inst['slot']}")
    print(f"    {inst['id']:<16} args({args}){flavour}{mark}")
    if inst["text"]:
        print(f"        text: {inst['text'][:78]}")

print()
counts = {s: len(v) for s, v in resolved.items()}
print(f"instances resolved: {counts}")
same = resolved["A"] == resolved["B"] == resolved["C"]
print(f"all three shapes resolve identically: {same}")

print()
for shape, path in FILES.items():
    lines = [ln for ln in path.read_text().splitlines() if ln.strip() and not ln.strip().startswith("#")]
    print(f"  shape {shape}: {len(lines):>3} non-comment lines for {counts[shape]} instances")

assert same, "shapes are NOT equivalent — the comparison is not purely ergonomic"
