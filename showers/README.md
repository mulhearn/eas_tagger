# CORSIKA showers

Showers simulated with CORSIKA, vertical protons at sea level, SIBYLL, thinning THIN 1e-6 1e4 0,
muons above 0.1 GeV.  See steering card at corsika_steering.txt.

showers/
  README.md              (this file)
  corsika_steering.txt   notes on CORSIKA steering
  corsika_showers.ipynb  sanity check plots
  python/                python utilities for processing CORSIKA showers
  datasets/              file listings for specific data sets
  data/                  (not in git) imported CORSIKA showers
  tables/                (not in git) processed data

In data, there is one HDF5 file per CORSIKA shower containing:

  events      one row:  primary_id, primary_energy_GeV, zenith_deg, azimuth_deg,
              first_int_height_km, n_muons
  grid        muon counts on a 20 m grid (100 x 100 cells, +-1 km):  one row per
              occupied cell, with ix, iy, count, density_per_m2, mean_energy_GeV, n_stored
  grid_fine   the same on an 81 x 81 grid of 0.988 m cells inside +-40 m around the core
              (its muons are also counted in grid)
  attributes  bin edges and cell widths of both grids, the CORSIKA file name

Thinned showers:  count and density are sums of thinning weights;  n_stored is the
number of muons CORSIKA actually stored in the cell (small n_stored means a noisy cell).
python/read_muons_h5.py prints the contents of one file.

The combine.py utility produces tables with one row per shower:
energy and geometry, muon number, the detectable areas above 20 and 50 muons/m^2 (`a_det20_m2`,
`a_det50_m2`:  the area of the cells above threshold, fine cells inside the fine region, coarse cells
outside it), the same from the fine cells alone (`a_det20_fine_only_m2`, `a_det50_fine_only_m2`, at most the
fine region's 6,400 m^2), and the median number of stored muons per fine cell (`fine_nstored_median`).

datasets:  finecore (9,360 showers, the main set), finecore_small (11 per energy, quick),
           thinh (922, lighter thinning:  THINH 10. 10. added to the card)

make tables: python/combine.py on datasets/X.txt to make tables/X.feather.

