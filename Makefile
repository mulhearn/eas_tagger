# eas_tagger.  Run from the repo root, with the crayfis env active (conda activate crayfis).
#   make           the plots, then the write-up (docs/tagger.pdf)
#   make tables    the shower tables (showers/tables/*.feather) from the CORSIKA files;  a few minutes
#   make clean-nb  clear the notebooks' outputs before a commit
#   make whitespace  strip trailing whitespace from the tracked text files (outside agents/)
#   make jup       JupyterLab in the repo root (rjup);  make jup-stop ends it
NOTEBOOKS := $(wildcard analysis/*.ipynb showers/*.ipynb)

.PHONY: all plots doc tables clean-nb whitespace jup jup-stop env

all: doc

env:
	@[ "$$CONDA_DEFAULT_ENV" = crayfis ] || { echo "make: activate the env first:  conda activate crayfis" >&2; exit 1; }

# run each notebook headless from its own directory;  the figures come from its savefig calls, and the executed
# copy is discarded, so the notebooks stay as committed
plots: env
	for f in $(NOTEBOOKS); do (cd $$(dirname $$f) && \
	  jupyter nbconvert --log-level=ERROR --to notebook --execute --stdout $$(basename $$f) >/dev/null) || exit 1; done

# the shower tables:  showers/datasets/X.txt (a list of CORSIKA files) gives showers/tables/X.feather;
# combine.py's progress goes to showers/tables/tables.log
DATASETS := $(basename $(notdir $(wildcard showers/datasets/*.txt)))

tables: env
	cd showers && mkdir -p tables && rm -f tables/tables.log && \
	  for d in $(DATASETS); do \
	    python python/combine.py --list datasets/$$d.txt --save_event --save_grid_summary \
	      -o tables/$$d.feather >> tables/tables.log || exit 1; done && \
	  grep "records written" tables/tables.log

# the write-up, from fresh plots;  latexmk -c removes the by-products, keeping the PDF
doc: plots
	cd docs && latexmk -pdf -interaction=nonstopmode -halt-on-error tagger.tex && latexmk -c tagger.tex

# clear all notebook outputs, execution counts and cell metadata (timings), keeping the kernel (before committing)
clean-nb: env
	jupyter nbconvert --clear-output --inplace \
	  --ClearMetadataPreprocessor.enabled=True \
	  --ClearMetadataPreprocessor.preserve_nb_metadata_mask='[("kernelspec",),("language_info",)]' \
	  $(NOTEBOOKS)

# strip trailing spaces and tabs from the tracked text files (-I skips binaries);  agents/ is left to the agents
whitespace:
	git grep -IlP '[ \t]+$$' -- . ':!agents' | xargs -r sed -i 's/[ \t]*$$//'

# JupyterLab in the repo root, in tmux session rjup (or report the running one)
jup: env
	rjup

jup-stop:
	rjup stop
