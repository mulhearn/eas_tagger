"""Diagram of the shower-grid binning near the core: docs/figs/core_binning.pdf (core_binning.tex)."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

COARSE, FINE = "k", "0.6"
plt.rcParams.update({"font.size": 8})
NFINE, HFINE = 81, 40.0                 # proposed: 81 x 81 cells over the central +-40 m

def lines(ax, edges, **kw):
    for e in edges:
        ax.axvline(e, **kw); ax.axhline(e, **kw)

def fine(ax, n, h):
    """n x n cells filling |x|, |y| < h (n odd: one centred on the core), and the region's edge."""
    for e in np.linspace(-h, h, n + 1):
        ax.plot([e, e], [-h, h], color=FINE, lw=0.6)
        ax.plot([-h, h], [e, e], color=FINE, lw=0.6)
    ax.add_patch(Rectangle((-h, -h), 2 * h, 2 * h, fill=False, ec="C0", lw=2, zorder=3))

def frame(ax, xlim, ylim, title):
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal")
    ax.set_title(title, fontsize=8.5, loc="left"); ax.set_xlabel("x (m)")

def note(ax, x, y, s):
    ax.text(x, y, s, ha="center", fontsize=7.5, zorder=6, bbox=dict(fc="w", ec="none"))

COARSE_EDGES = np.arange(-100, 101, 20)  # the grid as now (to +-1 km), edges through the core
fig, (a, b, d) = plt.subplots(1, 3, figsize=(7.2, 3.1))

# (a) as now: 20 m cells, edges through the core
a.add_patch(Rectangle((-20, -20), 40, 40, fc="r", alpha=0.15))
lines(a, COARSE_EDGES, color=COARSE, lw=1)
a.plot(0, 0, "r+", ms=10, mew=2, zorder=5)
a.add_patch(Circle((0, 0), 8, fill=False, ec="r", lw=1.2, ls="--", zorder=5))
frame(a, (-60, 60), (-60, 60), "(a) now: core on a corner")
a.set_ylabel("y (m)")
note(a, 0, -54, "8 m footprint: 4 cells or none")

# (b) proposed, at the core: 81 x 81 cells over the central 4 x 4 coarse cells
fine(b, NFINE, HFINE)
b.add_patch(Rectangle((-HFINE / NFINE, -HFINE / NFINE), 2 * HFINE / NFINE, 2 * HFINE / NFINE,
                      fc="r", alpha=0.3, zorder=4))
lines(b, [0], color=COARSE, lw=1, ls="--", zorder=4)          # the 20 m edges through the core
b.plot(0, 0, "r+", ms=10, mew=2, zorder=5)
frame(b, (-5, 5), (-5, 5), f"(b) proposed, at the core")
note(b, 0, -4.4, "one cell centred on the core")

# (d) the edge, proposed: 81 cells over +-40 m end on the coarse edge
fine(d, NFINE, HFINE)
lines(d, COARSE_EDGES, color=COARSE, lw=1.5, zorder=5)
frame(d, (34, 46), (-6, 6), "(c) proposed, at the edge")
note(d, 40, 4.6, "fine edge = 20 m edge")
d.set_xticks([35, 40, 45]); a.set_xticks([-50, -25, 0, 25, 50])

fig.text(0.5, 0.01, "red +: shower core;  black: 20 m cell edges (dashed: through the core);\n"
         "grey: fine cells;  blue: edge of the fine region", ha="center", fontsize=8)
plt.tight_layout(rect=(0, 0.09, 1, 1))
plt.savefig(__file__.replace(".py", ".pdf"))
print("wrote", __file__.replace(".py", ".pdf"))
