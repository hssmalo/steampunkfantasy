
import re

#steampunkFantazy imports
import build
from data import Team


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
    units = build.pick_units(team, seed=team_number)
    build.print_units(team, units)
