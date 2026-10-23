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
        print(f"{k:>20s}  {v:.6g}")

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


def analyze_grid(hf):
    """Detectable areas and a thinning diagnostic for the single shower in an open h5py.File.

    a_det<rho>_m2:  the area of the cells with density above rho (muons / m^2), where the shower's core
    can land and leave a fixed point above that density.  Fine cells (grid_fine) inside the fine region,
    coarse cells (grid) outside it.
    a_det<rho>_fine_only_m2:  the fine cells alone, nothing from the coarse grid (at most the fine region's area).
    fine_nstored_median:  the median number of stored muons per fine cell, empty cells included."""
    if "grid_fine" not in hf:
        sys.exit(f"ERROR:  no fine grid (grid_fine) in {hf.filename}")
    coarse_edges = np.asarray(hf.attrs["bin_edges_m"], dtype=float)
    fine_edges = np.asarray(hf.attrs["fine_bin_edges_m"], dtype=float)
    coarse_m = float(hf.attrs["cell_width_m"])
    fine_m = float(fine_edges[1] - fine_edges[0])
    coarse = hf["grid"][:]
    fine = hf["grid_fine"][:]

    # the coarse cells lo..hi-1 (in x and in y) lie under the fine region;  its edges fall on coarse cell edges
    lo = np.searchsorted(coarse_edges, fine_edges[0] - 1e-6)
    hi = np.searchsorted(coarse_edges, fine_edges[-1] - 1e-6)
    assert np.isclose(coarse_edges[lo], fine_edges[0]) and np.isclose(coarse_edges[hi], fine_edges[-1])
    under_fine = (coarse["ix"] >= lo) & (coarse["ix"] < hi) & (coarse["iy"] >= lo) & (coarse["iy"] < hi)
    outside = ~under_fine

    rho_coarse = coarse["density_per_m2"].astype(float)
    rho_fine = fine["density_per_m2"].astype(float)
    a20_fine_only = np.sum(rho_fine > 20) * fine_m**2
    a50_fine_only = np.sum(rho_fine > 50) * fine_m**2
    a20 = a20_fine_only + np.sum((rho_coarse > 20) & outside) * coarse_m**2
    a50 = a50_fine_only + np.sum((rho_coarse > 50) & outside) * coarse_m**2

    # the fine grid lists occupied cells only:  the empty ones count as zero stored muons
    n_cells = (len(fine_edges) - 1)**2
    n_stored = np.concatenate([fine["n_stored"], np.zeros(n_cells - len(fine))])

    return {"a_det20_m2": float(a20), "a_det50_m2": float(a50),
            "a_det20_fine_only_m2": float(a20_fine_only), "a_det50_fine_only_m2": float(a50_fine_only),
            "fine_nstored_median": float(np.median(n_stored))}

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
    parser.add_argument("--save_grid_summary", action="store_true", help="save grid summary in output")
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

    any_save  = args.save_event or args.save_grid_summary
    need_grid = args.save_grid_summary or args.dump_grid_summary

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
                summary = analyze_grid(hf)
                if args.dump_grid_summary:
                    dump_grid_summary(summary)
            if not any_save:
                continue
            rec = {"file_index": ifile, "file": file}
            if args.save_event:
                rec.update(event_record(hf))
            if args.save_grid_summary:
                rec.update(summary)
            records.append(rec)

    if any_save:
        df = pd.DataFrame(records)
        df.to_feather(args.output)
        print(f"{len(df)} records written to {args.output}")

if __name__ == "__main__":
    main()
