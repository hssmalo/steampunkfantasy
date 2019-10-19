from collections import Counter
from dataclasses import dataclass
import random
import re


from data import Team


@dataclass
class Costs:
    ip: int = 0  # Industry points
    mp: int = 0  # Manpower
    cp: int = 0  # Crafts points
    xp: int = 0  # Xperience points
    command: int = 0  # Command

    @classmethod
    def from_string(cls, string):
        cost_strings = string.split()
        costs = {
            "".join(c for c in s if c.isalpha()): int(
                "".join(c for c in s if c.isdigit())
            )
            for s in cost_strings
            if re.match(r"(\d+)([a-z]+)", s)
        }
        return cls(**costs)

    def __bool__(self):
        return any(self.__dict__.values())

    def __sub__(self, other):
        return self.__class__(
            **{k: s - getattr(other, k) for k, s in self.__dict__.items()}
        )

    def __add__(self, other):
        return self.__class__(
            **{k: s + getattr(other, k) for k, s in self.__dict__.items()}
        )

    def __mul__(self, other):
        return self.__class__(**{k: s * other for k, s in self.__dict__.items()})

    def __ge__(self, other):
        return all(v >= other.__dict__[k] for k, v in self.__dict__.items())


def pick_units(team, game="small", seed=42):
    random.seed(seed)
    armies = dict(
        small="12ip 12mp 12cp 12xp",
        standard="12ip 24mp 12cp 12xp",
        advanced="12ip 24mp 12cp 12xp 12command",
    )

    funds = Costs.from_string(armies[game])
    unit_costs = {u.name: Costs.from_string(u.cost) for u in team.units.values()}
    units = list()

    while funds and unit_costs:
        name, cost = random.choice(list(unit_costs.items()))
        if cost and cost <= funds:
            print(f"Adding {name} to army")
            units.append(name)
            funds -= cost
        else:
            del unit_costs[name]

    return Counter(units)


team_name = input("Choose team: ")
team = Team(team_name)
team.from_toml()
unit_costs = {u.name: Costs.from_string(u.cost) for u in team.units.values()}
units = pick_units(team)
print(f"\n{'=' * 70}\n{team_name.upper().center(70)}")
for unit in sorted(units, key=team.unit_sort):
    count = units[unit]
    print(f"{count:2d} - {unit:<25} {unit_costs[unit] * count}")

print(
    f"\n     {'Total':<25} "
    f"{sum((unit_costs[u] * c for u, c in units.items()), Costs())}"
)
