from data import Team
import subprocess

e = Team('Elf')
d = Team('Dwarf')
de = Team('DarkElf')
o  = Team('Ork')

e.from_toml()
d.from_toml()
de.from_toml()
o.from_toml()

e.write_pdf()
d.write_pdf()
de.write_pdf()
o.write_pdf()


subprocess.call(['pdflatex', 'armies.tex'])
subprocess.call(['pdflatex', 'armies.tex'])




