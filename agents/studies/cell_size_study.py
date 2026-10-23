"""How the detectable area depends on the cell size, from the fine grid alone.

The fine grid (81 x 81 cells of 0.988 m, +-40 m about the axis) is re-binned into blocks of k x k fine cells
(k = 3, 9, 27:  cells of 3, 9 and 27 m), and the area above THRESHOLD is compared with the fine area itself.
The real 20 m coarse grid (core at a cell corner) over the same +-40 m region is compared too.  The table gives,
per bin of the detectable radius r = sqrt(A_fine / pi), each cell size's area over the fine area.

From showers/, on the quick set (2026-10-23:  the basis for asking Daniel for a larger fine region):

    python ../agents/studies/cell_size_study.py $(sed -e 's/#.*//' datasets/finecore_small.txt | grep .)

The per-shower areas are kept in cell_size_study.feather, next to this script (not in git).
"""
import glob
import sys
from pathlib import Path
import h5py
import numpy as np
import pandas as pd

THRESHOLD = 50.0           # muons / m^2

files = sorted(f for pattern in sys.argv[1:] for f in glob.glob(pattern))
rows = []
for path in files:
    with h5py.File(path, "r") as hf:
        E = float(hf["events"][0]["primary_energy_GeV"]) * 1e9
        fine_edges = np.asarray(hf.attrs["fine_bin_edges_m"], dtype=float)
        coarse_edges = np.asarray(hf.attrs["bin_edges_m"], dtype=float)
        fine_m = fine_edges[1] - fine_edges[0]
        coarse_m = float(hf.attrs["cell_width_m"])
        fine = hf["grid_fine"][:]
        coarse = hf["grid"][:]

    n = len(fine_edges) - 1
    counts = np.zeros((n, n))                       # muons (sum of weights) per fine cell
    counts[fine["ix"], fine["iy"]] = fine["density_per_m2"] * fine_m**2

    row = {"E": E, "a_fine": np.sum(counts / fine_m**2 > THRESHOLD) * fine_m**2}
    for k in (3, 9, 27):
        blocks = counts.reshape(n // k, k, n // k, k).sum(axis=(1, 3))
        cell = k * fine_m
        row[f"a_{k}"] = np.sum(blocks / cell**2 > THRESHOLD) * cell**2

    # the coarse cells under the fine region
    lo = np.searchsorted(coarse_edges, fine_edges[0] - 1e-6)
    hi = np.searchsorted(coarse_edges, fine_edges[-1] - 1e-6)
    under = (coarse["ix"] >= lo) & (coarse["ix"] < hi) & (coarse["iy"] >= lo) & (coarse["iy"] < hi)
    row["a_coarse20"] = np.sum(coarse["density_per_m2"][under] > THRESHOLD) * coarse_m**2
    rows.append(row)

areas = pd.DataFrame(rows)
areas.to_feather(Path(__file__).with_suffix(".feather"))

# each cell size's area over the fine area, by the detectable radius
areas = areas[areas.a_fine > 0].copy()
areas["r"] = np.sqrt(areas.a_fine / np.pi)
print(f"{len(files)} showers;  area over the fine (0.988 m) area, Phi_D = {THRESHOLD:g}")
print(f"{'r (m)':>8s} {'n':>4s} {'3 m':>6s} {'9 m':>6s} {'27 m':>6s} {'20 m grid':>10s}")
edges = [3, 5, 8, 12, 16, 20, 25, 30, 35]
for r_lo, r_hi in zip(edges[:-1], edges[1:]):
    b = areas[(areas.r > r_lo) & (areas.r <= r_hi)]
    print(f"{r_lo:3d}-{r_hi:<4d} {len(b):4d} {b.a_3.sum() / b.a_fine.sum():6.2f} {b.a_9.sum() / b.a_fine.sum():6.2f}"
          f" {b.a_27.sum() / b.a_fine.sum():6.2f} {b.a_coarse20.sum() / b.a_fine.sum():10.2f}")
