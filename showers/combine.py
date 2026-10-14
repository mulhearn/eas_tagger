#!/usr/bin/env python3
"""
Configurable combination of HDF5 files containing CORSIKA-simulated showers.
"""
import argparse
import glob
import sys
import h5py
import pandas as pd
import numpy as np
import os

def determine_inputs(args):
    """Parse command line options to determine HDF5 input files."""
    patterns = list(args.patterns)

    if args.list:
        with open(args.list) as f:
            patterns += [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if args.dir:
        patterns.append(f"{args.dir}/*.h5")

    if not patterns:
        sys.exit("ERROR:  No input files were specified. Use a glob pattern, --list, or --dir.")

    files = set()
    for file in patterns:
        matches = glob.glob(file)
        if not matches:
            sys.exit(f"ERROR:  requested file does not exist: {file}")
        files.update(matches)

    return sorted(files)

def dump_event(hf):
    """Print the event contents an open h5py.File."""
    events = pd.DataFrame(hf["events"][:])
    print(f"--- events ({len(events)} rows) ---")
    print(events.to_string())

def dump_grid(hf, n=None):
    """Print the grid contents an open h5py.File."""
    grid = pd.DataFrame(hf["grid"][:])
    if n is not None:
        print(f"--- grid ({len(grid)} rows, showing first {n}) ---")
        print(grid.head(n).to_string())
    else:
        print(f"--- grid ({len(grid)} rows) ---")
        print(grid.to_string())

def dump_grid_summary(summary):
    print("--- grid summary ---")
    for k, v in summary.items():
        print(f"{k:>16s}  {v:.6g}")

def dump_lateral(lateral):
    print("--- lateral (fraction of muons, bins labeled by upper edge in m) ---")
    for k, v in lateral.items():
        print(f"{k:>10s}  {v:.5f}")

def event_record(hf):
    """Flatten the single event row of an open h5py.File."""
    ev = hf["events"][0]
    return {
        "event": int(ev["event"]),
        "primary_id": int(ev["primary_id"]),
        "E_GeV": float(ev["primary_energy_GeV"]),
        "zenith_deg": float(ev["zenith_deg"]),
        "azimuth_deg": float(ev["azimuth_deg"]),
        "first_int_height_km": float(ev["first_int_height_km"]),
        "n_muons": int(ev["n_muons"]),
    }

        
# grid analysis parameters (the cell size is read from each file's cell_width_m):

SUB_M    = 1.0     # sub-sampling resolution (m)
RHO_DET  = 50.0    # detectability threshold (muons / m^2)

LAT_FINE_MAX = 400   # 20 m bins out to here, then 100 m bins
R_SUB_M  = LAT_FINE_MAX + 50.0   # keep sub-sampling past the last 20 m edge
LAT_EDGES = np.array(list(range(0, LAT_FINE_MAX + 1, 20)) + list(range(LAT_FINE_MAX + 100, 1001, 100)))
LAT_NAMES = [f"r{e}" for e in LAT_EDGES[1:]] + [f"r_gt{LAT_EDGES[-1]}"]

_SUB = {}
def sub_offsets(cell_m):
    """Sub-cell center offsets (m) relative to the cell center, for cells of cell_m."""
    if cell_m not in _SUB:
        o = (np.arange(int(round(cell_m / SUB_M))) + 0.5) * SUB_M - cell_m / 2
        _SUB[cell_m] = tuple(a.ravel() for a in np.meshgrid(o, o))
    return _SUB[cell_m]


def analyze_grid(hf):
    """Return (summary, lateral) dicts for the single shower in an open h5py.File."""
    CELL_M = float(hf.attrs["cell_width_m"])
    SUB_DX, SUB_DY = sub_offsets(CELL_M)
    g   = hf["grid"][:]
    ix  = g["ix"].astype(float)
    iy  = g["iy"].astype(float)
    w   = g["count"].astype(float)
    rho = g["density_per_m2"].astype(float)
    wsum = w.sum()

    summary = {
        "n_muons": int(hf["events"][0]["n_muons"]),
        "grid_count_sum": wsum,
        "rho_peak": float(rho.max()) if len(rho) else 0.0,
    }
    if wsum <= 0:
        summary.update(core_ix=np.nan, core_iy=np.nan, rho_core=0.0, r_det_m=0.0,
                       r_rms_m=np.nan, r50_m=np.nan, r90_m=np.nan)
        return summary, {name: np.nan for name in LAT_NAMES}

    # density-weighted centroid (index units; cell centers at integer indices)
    cx = np.sum(w * ix) / wsum
    cy = np.sum(w * iy) / wsum
    kx, ky = int(np.floor(cx + 0.5)), int(np.floor(cy + 0.5))
    at_core = (g["ix"] == kx) & (g["iy"] == ky)
    rho_core = float(rho[at_core].sum()) if at_core.any() else 0.0

    # cell-center positions relative to the core (m)
    x = (ix - cx) * CELL_M
    y = (iy - cy) * CELL_M
    rc = np.hypot(x, y)

    det = rho > RHO_DET
    r_det = float(rc[det].max()) if det.any() else 0.0

    # two tiers: 1 m sub-sampling near the core, cell centers farther out
    inner = rc < R_SUB_M
    xs = (x[inner, None] + SUB_DX).ravel()
    ys = (y[inner, None] + SUB_DY).ravel()
    ws = np.repeat(w[inner] / SUB_DX.size, SUB_DX.size)
    r  = np.concatenate([np.hypot(xs, ys), rc[~inner]])
    wr = np.concatenate([ws, w[~inner]])

    r_rms = float(np.sqrt(np.sum(wr * r**2) / wsum))

    # one 1 m radial histogram serves r50, r90, and the lateral fractions
    h = np.bincount(np.floor(r).astype(int), weights=wr, minlength=LAT_EDGES[-1] + 1)
    c = np.concatenate([[0.0], np.cumsum(h)])      # c[k] = weight with r < k meters
    r50 = float(np.searchsorted(c, 0.5 * wsum))     # 1 m resolution
    r90 = float(np.searchsorted(c, 0.9 * wsum))

    summary.update(core_ix=cx, core_iy=cy, rho_core=rho_core, r_det_m=r_det,
                   r_rms_m=r_rms, r50_m=r50, r90_m=r90)

    fr = [(c[b] - c[a]) / wsum for a, b in zip(LAT_EDGES[:-1], LAT_EDGES[1:])]
    fr.append((wsum - c[LAT_EDGES[-1]]) / wsum)
    lateral = dict(zip(LAT_NAMES, fr))
    return summary, lateral

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("patterns", nargs="*", help="glob pattern(s) or explicit file paths, e.g. corsika_h5/*.h5")
    parser.add_argument("--list", help="text file with one path/pattern per line")
    parser.add_argument("--dir", help="shorthand for DIR/*.h5")
    parser.add_argument("-o", "--output", default="events.feather", help="output Feather file (default: events.feather)")
    parser.add_argument("--dump_event", action="store_true", help="dump event tree contents to screen")
    parser.add_argument("--dump_grid",  action="store_true", help="dump grid content to screen")
    parser.add_argument("--save_event",  action="store_true", help="save event tree contents in output")
    parser.add_argument("--dump_grid_summary", action="store_true", help="dump grid summary to screen")
    parser.add_argument("--dump_lateral",      action="store_true", help="dump lateral fractions to screen")
    parser.add_argument("--save_grid_summary", action="store_true", help="save grid summary in output")
    parser.add_argument("--save_lateral",      action="store_true", help="save lateral fractions in output")
    parser.add_argument("-n", "--max_files", type=int, default=None, help="process at most this many files per subdirectory")
    
    args = parser.parse_args()

    files = determine_inputs(args)

    if args.max_files is not None:
        per_dir = {}
        kept = []
        for f in files:
            d = os.path.dirname(os.path.abspath(f))
            per_dir[d] = per_dir.get(d, 0) + 1
            if per_dir[d] <= args.max_files:
                kept.append(f)
        print(f"INFO: limiting to {args.max_files} files per directory: "
              f"kept {len(kept)} of {len(files)} across {len(per_dir)} directories.")
        files = kept
    
    print(f"INFO: processing {len(files)} files.")

    any_save  = args.save_event or args.save_grid_summary or args.save_lateral
    need_grid = (args.save_grid_summary or args.save_lateral
                 or args.dump_grid_summary or args.dump_lateral)

    records = []
    for ifile, file in enumerate(files):
        print(f"INFO: processing file:  {file}")
        with h5py.File(file, "r") as hf:
            n_ev = hf["events"].shape[0]
            if n_ev != 1:
                print(f"WARNING: {file} has {n_ev} events; combine.py assumes one per file")
            if args.dump_event:
                dump_event(hf)
            if args.dump_grid:
                dump_grid(hf)
            if need_grid:
                summary, lateral = analyze_grid(hf)
                if args.dump_grid_summary:
                    dump_grid_summary(summary)
                if args.dump_lateral:
                    dump_lateral(lateral)
            if not any_save:
                continue
            rec = {"file_index": ifile, "file": file}
            if args.save_event:
                rec.update(event_record(hf))
            if args.save_grid_summary:
                rec.update(summary)
            if args.save_lateral:
                rec.update(lateral)
            records.append(rec)

    if any_save:
        df = pd.DataFrame(records)
        df.to_feather(args.output)
        print(f"{len(df)} records written to {args.output}")

if __name__ == "__main__":
    main()
