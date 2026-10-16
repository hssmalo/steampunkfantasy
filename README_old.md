# SteampunkFantasy

The rules are available in [markdown](rules.md) and [PDF](rules.pdf).

Additional rules for each army:

- Dark-Elf ([PDF](darkelf.pdf))
- Dwarf ([PDF](dwarf.pdf))
- Elf ([PDF](elf.pdf))
- Ork ([PDF](ork.pdf))


## Build Your Army

The script [`build.py`](build.py) can assist in building your army. Run it as follows:

    $ python build.py

Choose your team--either `DarkElf`, `Dwarf`, `Elf`, or `Ork`, and optionally choose one or more team numbers. The numbers can be used to recreate the same team later. If number is left blank, a random team is created.

**Note:** Currently the builder does not handle `Elite` upgrades correctly


## Create New Weapons, Units, or Armies

Information about the armies are stored in TOML-files. The script [`data.py`](data.py) can assist in creating new army rules. Run it as follows:

    $ python data.py

This leaves you in an interactive IPython shell where you can run new commands. For example, you can load information about the Elf army from the TOML file as follows:

    >>> elf = Team("Elf")
    >>> elf.from_toml()


### Update Army Rules PDF

Use `.write_pdf()` to update the PDF file for a given army:

    >>> elf = Team("Elf")
    >>> elf.from_toml()
    >>> elf.write_pdf()

This updates the file `Elf.tex`. You can then create a PDF file by running:

    $ pdflatex armies

This creates or updates the file `armies.pdf`.


### Add a Weapon to a Team

Adding weapons, units, and teams are supported by questionaires implemented by `data.py`. The following example adds the weapon `Laser` to the Elf team:

    >>> elf = Team("Elf")
    >>> elf.from_toml()
    >>> weapon = Weapon("Laser", elf)
    >>> weapon.write()
    # Answer questions
    >>> elf.store_data()


### Add a Unit to a Team

Adding weapons, units, and teams are supported by questionaires implemented by `data.py`. The following example adds the unit `Shield Surfer` to the Elf team:

    >>> elf = Team("Elf")
    >>> elf.from_toml()
    >>> unit = Unit("Shield Surfer", elf)
    >>> unit.write()
    # Answer questions
    >>> elf.store_data()


### Create a New Team

You can also create completely new teams. You then start with a new team, and adds some new units and weapons to it. You can later update these, just as above. The following creates a new `Spartan` team:

    >>> team = Team("Spartan")
    >>> unit = Unit("Unit 1", team)
    >>> unit.write()
    # Answer questions
    >>> unit = Unit("Unit 2", team)
    >>> unit.write()
    # Answer questions
    ...
    >>> weapon = Weapon("Weapon 1", team)
    >>> weapon.write()
    # Answer questions
    ...
    >>> team.store_data()

This creates a new TOML file with information about your new team. You should also update the file [`armies.tex`](armies.tex) to include your new team in the army rules PDF.