from collections import Counter
from dataclasses import dataclass
import pathlib
import random
import re


from data import Team

ARMIES = dict(
    small="12ip 12mp 12cp 12xp",
    standard="12ip 24mp 12cp 12xp",
    advanced="12ip 24mp 12cp 12xp 12command",
)


@dataclass
class Costs:
    ip: int = 0  # Industry points
    mp: int = 0  # Manpower
    cp: int = 0  # Crafts points
    xp: int = 0  # Xperience points
    command: int = 0  # Command

    @classmethod
    def from_string(cls, string):
        """Parse a string of costs"""
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
        """A Costs object is False when all costs are 0"""
        return any(self.__dict__.values())

    def __add__(self, other):
        """Add two Costs together"""
        return self.__class__(
            **{k: s + getattr(other, k) for k, s in self.__dict__.items()}
        )

    def __sub__(self, other):
        """Subtract one Costs from another"""
        return self.__class__(
            **{k: s - getattr(other, k) for k, s in self.__dict__.items()}
        )

    def __mul__(self, other):
        """Multiply a Costs by a number"""
        return self.__class__(**{k: s * other for k, s in self.__dict__.items()})

    def __ge__(self, other):
        """A Costs is >= than another, if all costs are >="""
        return all(v >= other.__dict__[k] for k, v in self.__dict__.items())


def get_unit_costs(team):
    """Create Costs objects for all units in a team"""
    return {u.name: Costs.from_string(u.cost) for u in team.units.values()}


def pick_units(team, game="small", seed=42):
    """Pick units for an army

    The units are chosen randomly based on the random seed.

    TODO: Elite units are not handled correctly
    """
    random.seed(seed)

    funds = Costs.from_string(ARMIES[game])
    unit_costs = get_unit_costs(team)
    units = list()

    while funds and unit_costs:
        name, cost = random.choice(list(unit_costs.items()))
        if not cost:
            # Some special objects don't have a cost, ignore them
            del unit_costs[name]
            continue

        if name.startswith("Elite "):
            # Support for elite units not yet implemented, ignore them
            del unit_costs[name]
            continue

        # Add as many units as possible
        while cost <= funds:
            units.append(name)
            funds -= cost

        # Delete unit from list of possible candidates
        del unit_costs[name]

    return Counter(units)


def print_units(team, units):
    """Print information about an army"""
    unit_costs = get_unit_costs(team)
    print(f"\n{'=' * 79}\n{team.name.upper().center(79)}")

    for unit in sorted(units, key=team.unit_sort):
        count = units[unit]
        print(f"{count:2d} - {unit:<25} {unit_costs[unit] * count}")

    print(
        f"\n     {'Total':<25} "
        f"{sum((unit_costs[u] * c for u, c in units.items()), Costs())}"
    )


# Ask for input, team name should correspond to a TOML file
team_name = input("Choose team: ")
team = Team(team_name)
try:
    team.from_toml()
except FileNotFoundError:
    team_files = pathlib.Path.cwd().glob("[A-Z]*.toml")
    teams = sorted(t.stem for t in team_files)
    print(f"Unknown team {team_name!r}. Choose one of {', '.join(teams)}")
    raise SystemExit()

# Team numbers can be a list of numbers, pick a random team if none is given
team_numbers = input("Choose team numbers: ")
if team_numbers:
    team_numbers = [int(n) for n in re.split(r"[\s,]+", team_numbers)]
else:
    team_numbers = [random.randint(0, 1_000_000)]
    print(f"Using team number {team_numbers[0]}")

# Choose armies and print them out
for team_number in team_numbers:
    units = pick_units(team, seed=team_number)
    print_units(team, units)
