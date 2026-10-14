#!/usr/bin/env python3
"""
Example: read back a muon density HDF5 file produced by muons_grid.py

Usage: python read_muons_h5.py output.h5
"""
import sys
import numpy as np
import pandas as pd
import h5py

if len(sys.argv) < 2:
    print("Usage: python read_muons_h5.py <output.h5>")
    sys.exit(1)

h5_path = sys.argv[1]

with h5py.File(h5_path, "r") as hf:

    # ── File-level metadata ──────────────────────────────────────────
    print("=== File attributes ===")
    print(f"  CORSIKA source file : {hf.attrs['corsika_file']}")
    print(f"  Grid bins           : {hf.attrs['grid_nbins']}×{hf.attrs['grid_nbins']}")
    print(f"  Cell size           : {hf.attrs['cell_width_m']:.1f} m")
    print(f"  Grid extent         : ±{hf.attrs['grid_half_extent_cm']/100:.0f} m")
    print(f"  Units               : {hf.attrs['units_note']}")
    print()

    # ── Load the two tables ──────────────────────────────────────────
    events = pd.DataFrame(hf["events"][:])
    grid   = pd.DataFrame(hf["grid"][:])
    edges  = hf.attrs["bin_edges_m"]          # grid edge array in metres

# ── Fix dtypes (HDF5 → pandas can promote ints to float) ────────────
for col in ["event", "primary_id", "n_muons"]:
    events[col] = events[col].astype(int)
for col in ["event", "ix", "iy"]:                  # not count: in THIN mode it is a sum of weights
    grid[col] = grid[col].astype(int)

# ── Event-level summary ──────────────────────────────────────────────
print(f"=== {len(events)} event(s) ===")
for _, ev in events.iterrows():
    print(f"  Event {int(ev['event']):>4d}:  "
          f"primary={int(ev['primary_id']):<6d}  "
          f"E={ev['primary_energy_GeV']:.3e} GeV  "
          f"θ={ev['zenith_deg']:6.2f}°  "
          f"φ={ev['azimuth_deg']:6.2f}°  "
          f"1st int={ev['first_int_height_km']:.2f} km  "
          f"nμ={int(ev['n_muons'])}")
print()

# ── Iterate through grid entries for each event ─────────────────────
for _, ev in events.iterrows():
    evt_num = int(ev["event"])
    evt_grid = grid[grid["event"] == evt_num]

    print(f"=== Event {evt_num}: {len(evt_grid)} non-empty grid cells ===")
    print(f"    {'ix':>4s} {'iy':>4s}  {'x_m':>8s} {'y_m':>8s}  "
          f"{'count':>6s}  {'density':>12s}  {'<E> GeV':>10s}")

    for _, cell in evt_grid.iterrows():
        # Recover cell centre from the edge array stored in the file
        ix = int(cell["ix"])
        iy = int(cell["iy"])
        xc = 0.5 * (edges[ix] + edges[ix + 1])
        yc = 0.5 * (edges[iy] + edges[iy + 1])

        print(f"    {ix:4d} {iy:4d}  "
              f"{xc:8.1f} {yc:8.1f}  "
              f"{cell['count']:6.1f}  "
              f"{cell['density_per_m2']:12.6f}  "
              f"{cell['mean_energy_GeV']:10.4f}")

    print()

# ── Example: merge tables for analysis ───────────────────────────────
merged = grid.merge(events, on="event")
print("=== Merged table (first 5 rows) ===")
print(merged.head().to_string(index=False))
