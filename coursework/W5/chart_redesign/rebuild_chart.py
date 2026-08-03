"""Honest rebuild of Chart B (W5 chart-redesign activity).

The original is a state DOT area chart of highway fatalities, 2012-2024, drawn
with an INVERTED y-axis (300 at top, 700 at bottom) that is also truncated at
300. A rising series therefore descends across the panel and reads as a decline.

This rebuild fixes both axis distortions and rewrites the title to state the
direction of travel. The source series was never published, so values are
recovered from the original PNG by pixel measurement against its own calibrated
axes; they are approximate and are labelled as such. Source and provenance are
carried in the markdown deliverable's caption rather than drawn into the image.

Design notes
------------
Line, not filled area. The original's fill invites reading the shaded mass as
volume, which is exactly the encoding this rebuild is correcting; on a zero
baseline that mass is also mostly empty space, since the series never drops
below ~355. A line makes the level readable without implying accumulated
quantity, and leaves the lower panel as whitespace rather than ink.

Single series, so no legend: the title and y-label name what is plotted. Only
the three points the write-up cites are labelled, rather than every point.

Sized for projection, not print: 1920x1080, with type from 19pt up and 4px
marks, so the back of a room can read it. That budget is what keeps the labelled
points to three -- at this type size a fourth would collide with its neighbours.

The title bounds the rise by its endpoints and says nothing about the
intervention. Dating the rise *to* 2018 would imply the limit caused it; dating
it *from* 2017 as a trend already underway would imply the opposite, that the
limit arrived mid-trend and is incidental. Neither is supported (see the
write-up's note on the missing control group). Naming both endpoints instead
makes the claim checkable against the two labelled values on screen, and leaves
the 2018 marker sitting inside that span for the reader to interpret.

The 2018 marker is drawn as a plain vertical rule with a neutral label. The
chart cannot support a causal claim - there is no comparison group - so the
annotation states when the limit changed and nothing about what it caused.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# --- palette (matches src/w5_visuals.py, the project's reference instance) ----
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#7a7975"
# A darker step of the original chart's green. Keeping the hue ties the rebuild
# to the chart it corrects; the darker step is what carries a 2px line against
# the light surface, where the original's fill green would be too pale to read.
SERIES_EDGE = "#2f7d66"

# Values recovered from the original PNG by pixel measurement rather than by
# eye. The axis was calibrated from its own tick-label centers -- 300 -> row
# 143.0 and 700 -> row 717.0 vertically, 2012 -> col 232.5 and 2024 -> col
# 1304.0 horizontally -- and the 2018 gridline predicted by that fit lands
# within 0.25px of where it actually falls, so the mapping is sound. Values are
# still approximate (the source series was never published) but they are
# measured against the chart's own scale, not estimated against a gridline.
YEARS = [2012, 2013, 2014, 2015, 2016, 2017, 2018,
         2019, 2020, 2021, 2022, 2023, 2024]
FATALITIES = [410, 400, 382, 370, 365, 355, 400,
              430, 470, 510, 545, 565, 578]

# Points the prose cites, so the reader can check the numbers against the text.
ANNOTATE = {2012: "~410", 2017: "~355", 2024: "~578"}


def plot_rebuild(out_path: Path | str | None = None):
    """Draw the corrected chart. Returns (fig, ax)."""
    # 16:9 at 150dpi -> 1920x1080, native projector resolution.
    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    # --- Fix 1: axis runs the right way up. Fix 2: baseline at zero. ---------
    # Top is set just above the maximum so the series is not squashed into the
    # bottom third: zero-based, but scaled to the data.
    ax.set_ylim(0, 650)
    ax.set_xlim(2011.6, 2024.5)

    ax.plot(YEARS, FATALITIES, color=SERIES_EDGE, linewidth=4,
            solid_capstyle="round", zorder=3)
    ax.plot(YEARS, FATALITIES, "o", color=SERIES_EDGE, markersize=9,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=4)

    # --- the policy change, stated without a causal claim --------------------
    ax.axvline(2018, color="#8f8e8a", linewidth=2.5, linestyle=(0, (5, 4)),
               zorder=2)
    ax.text(2018.2, 638, "2018: limit raised to 75",
            color=TEXT_PRIMARY, fontsize=19, va="top", ha="left")

    # --- selective direct labels --------------------------------------------
    # 2017 is labelled below its point so the label clears the descending line.
    for year, label in ANNOTATE.items():
        value = FATALITIES[YEARS.index(year)]
        offset = -34 if year == 2017 else 20
        ax.annotate(label, (year, value), textcoords="offset points",
                    xytext=(0, offset), ha="center", fontsize=21,
                    fontweight="bold", color=TEXT_PRIMARY)

    # --- axes ----------------------------------------------------------------
    # No gridlines: the three labelled points carry the message, and at
    # projection distance the ruled lines competed with the series for
    # attention. The y tick labels stay as the remaining reference for the
    # unlabelled years, which now read as shape rather than as values.
    ax.yaxis.set_major_locator(MultipleLocator(100))
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#b8b7b4")
    ax.spines["bottom"].set_linewidth(1.5)
    ax.tick_params(colors=TEXT_PRIMARY, labelsize=20, length=0, pad=8)
    ax.set_xticks([2012, 2014, 2016, 2018, 2020, 2022, 2024])

    # --- Fix 3: title states the direction of travel -------------------------
    ax.set_title("Highway fatalities rose from 2017 to 2024",
                 color=TEXT_PRIMARY, fontsize=30, fontweight="bold",
                 loc="left", pad=22)
    ax.set_ylabel("Traffic fatalities", color=TEXT_PRIMARY, fontsize=21,
                  labelpad=12)

    # Source and provenance live in the markdown deliverable, not baked into the
    # raster: the caption can then be re-laid-out or cropped without fighting
    # text fixed at a position and size in the PNG.

    fig.tight_layout()

    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, facecolor=SURFACE, bbox_inches="tight")
    return fig, ax


if __name__ == "__main__":
    here = Path(__file__).parent
    plot_rebuild(here / "rebuilt_charts" / "chartB_rebuilt.png")
