"""Army builder frontend."""

import streamlit as st

from spf import races
from spf.armies import build

st.title("Hello, Steampunkfantasy!")
st.write("Let there be drones...")

race_name = st.selectbox("Choose a race:", races.list_races(validate=True))

army = build.ArmyList(race_name, nick=f"{race_name.title()}s'r'Us", units=[])
race_cfg = races.get_race(race_name)

army = army.add_unit(f"{race_name}_infantry", race_config=race_cfg)

st.write(f"Your army: {army}")
