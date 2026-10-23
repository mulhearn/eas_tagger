"""Write analysis/crspectra_spectrum.yaml:  measured all-particle spectra, a stopgap while CRDB is down, from
crspectra.db (crspectra 1.1.1, K. Krings' 2017 compilation;  energies in GeV, flux in 1 / (GeV m^2 s sr), errors
as offsets from the flux).  Per experiment:  E (eV), E dJ/dE (1 / (m^2 sr s)), and the low and high errors on it,
statistical and systematic in quadrature;  upper limits dropped.

    python spectrum/make_spectrum.py ../analysis/crspectra_spectrum.yaml    (from agents/)
"""
import sqlite3
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
EXPERIMENTS = ["Tibet-III (QGSJet-01C, HD)", "KASCADE (QGSJet-I)", "GAMMA", "IceTop-73", "KASCADE-Grande",
               "HiRes/MIA", "HiRes-I", "HiRes-II", "Auger"]      # all-particle, in our energy range

def flow(x):
    """A YAML flow list;  every number with a signed exponent, which YAML 1.1 needs to read it as a float."""
    return "[" + ", ".join(f"{v:.4e}" for v in x) + "]"

con = sqlite3.connect(f"file:{HERE / 'crspectra.db'}?mode=ro", uri=True)
lines = ["# measured all-particle spectra (crspectra 2017 compilation):  E (eV), E dJ/dE (1 / (m^2 sr s)), errors"]
for name in EXPERIMENTS:
    d = np.array(con.execute(f'SELECT energy, flux, stat_low, stat_up, sys_low, sys_up, is_uplim FROM "{name}"')
                 .fetchall(), dtype=float)
    d = d[d[:, 6] == 0]
    E = d[:, 0]
    lines += [f'"{name}":',
              f"  E: {flow(E * 1e9)}",
              f"  EdJdE: {flow(E * d[:, 1])}",
              f"  lo: {flow(E * np.hypot(d[:, 2], d[:, 4]))}",
              f"  hi: {flow(E * np.hypot(d[:, 3], d[:, 5]))}"]
    print(f"{name:28s} {len(E):3d} points")
Path(sys.argv[1]).write_text("\n".join(lines) + "\n")
print("wrote", sys.argv[1])
