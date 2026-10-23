# agents:  work by Michael's agents

Agents commit here under their own names, so work in progress stays in git without cluttering the rest of the repo.
Everything outside `agents/` is checked and committed by Michael;  agents propose changes there.  Only Michael
pushes.  When a piece here is ready, Michael reduces it to what he wants and it moves out of `agents/`.

| Path | What |
|---|---|
| `spectrum/` | The stopgap spectrum while CRDB is down:  `make_spectrum.py` writes `../analysis/crspectra_spectrum.yaml` from `crspectra.db`, the SQLite database shipped with crspectra 1.1.1 (PyPI, K. Krings, GPL-3), a 2017 compilation of published cosmic-ray spectra;  unchanged (sha256 26c340cc...).  From `agents/`:  `python spectrum/make_spectrum.py ../analysis/crspectra_spectrum.yaml`. |
| `studies/` | `cell_size_study.py`:  the detectable area against the cell size, from the fine grid re-binned into 3, 9 and 27 m cells and from the 20 m grid (2026-10-23;  usage in its docstring). |
| `docs/` | `core_binning.tex`, the one-page proposal for the fine core grid (2026-10-14, the binning Daniel used);  `python figs/core_binning.py` makes its figure, then `pdflatex core_binning.tex`, from `docs/`. |
