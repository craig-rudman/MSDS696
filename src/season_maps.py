"""Season small-multiple maps for the Week 2 practice talk.

Renders CONUS EPA Level III ecoregions shaded by wildfire cause, faceted by
meteorological season, in three candidate encodings:

    A. natural_share    -- sequential: % of fires that are Natural (lightning)
    B. dominant_count   -- categorical: top cause by IGNITION COUNT
    C. dominant_acres   -- categorical: top cause by ACRES BURNED

and animates encoding A into a looping GIF (the hero talk visual).

Honesty conventions baked in, consistent with the feasibility notebook:
  * cause is read as SHARES, not counts;
  * region-seasons with < MIN_CELL fires are left blank (insufficient sample);
  * regions with >= HIGH_MISS_THRESHOLD missing-cause are hatched with a note,
    because missingness is strongly differential across ecoregions.

Paths are resolved relative to the project root so the module works whether
called from notebook/ or src/.
"""
from __future__ import annotations

import sqlite3
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

# --- project paths (module lives in <root>/src) ---
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "FPA_FOD_20221014.sqlite"
ECO_PATH = ROOT / "data" / "us_eco_l3_state_boundaries" / "us_eco_l3_state_boundaries.shp"
IMG_DIR = ROOT / "img"

SEASONS = ["Winter", "Spring", "Summer", "Fall"]
MIN_CELL = 30              # min fires per region-season to render a value
HIGH_MISS_THRESHOLD = 0.40  # regions >= this missing-cause rate get hatched
DEFAULT_SAMPLE = 400_000

# Categorical cause palette (brand-neutral, color-blind aware ordering).
CAUSE_COLORS = {
    "Natural": "#C1440E",
    "Debris and open burning": "#4E79A7",
    "Arson/incendiarism": "#59A14F",
    "Equipment and vehicle use": "#B07AA1",
    "Recreation and ceremony": "#EDC948",
    "Smoking": "#9C755F",
    "Power generation/transmission/distribution": "#E15759",
}
OTHER_COLOR = "#BAB0AC"
BLANK_COLOR = "#EEEEEE"     # insufficient sample


def to_season(doy: int) -> str:
    """Meteorological season from day-of-year (matches 01_feasibility.ipynb)."""
    if doy >= 335 or doy < 60:
        return "Winter"
    if doy < 152:
        return "Spring"
    if doy < 244:
        return "Summer"
    return "Fall"


def load_joined(sample_size: int = DEFAULT_SAMPLE, seed: int | None = None):
    """Sample fires, spatial-join to dissolved L3 ecoregions, tag season.

    Returns (joined, eco, high_miss) where `joined` is non-null-region fires
    with season/is_missing/is_nat flags, `eco` is the dissolved ecoregion
    GeoDataFrame, and `high_miss` is the set of high-missing region names.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with sqlite3.connect(DB_PATH) as conn:
            # SQLite RANDOM() is unseeded, so a plain "ORDER BY RANDOM()" gives a
            # different sample every run. For reproducible figures, order by a
            # deterministic hash of the row id salted with `seed`; fall back to
            # RANDOM() only when seed is None.
            if seed is None:
                order = "RANDOM()"
            else:
                order = f"substr(FOD_ID * 2654435761 + {int(seed)}, -8)"
            fires = pd.read_sql_query(
                "SELECT FIRE_YEAR, DISCOVERY_DOY, NWCG_GENERAL_CAUSE, "
                "LATITUDE, LONGITUDE, FIRE_SIZE FROM Fires "
                f"ORDER BY {order} LIMIT {sample_size}",
                conn,
            )

        eco = (
            gpd.read_file(ECO_PATH)[["US_L3NAME", "geometry"]]
            .dissolve("US_L3NAME")
            .reset_index()
        )

        pts = gpd.GeoDataFrame(
            fires.copy(),
            geometry=gpd.points_from_xy(fires.LONGITUDE, fires.LATITUDE),
            crs="EPSG:4326",
        ).to_crs(eco.crs)
        joined = gpd.sjoin(pts, eco, how="left", predicate="within")

    joined = joined[joined.US_L3NAME.notna()].copy()
    joined["season"] = joined.DISCOVERY_DOY.map(to_season)
    joined["is_missing"] = joined.NWCG_GENERAL_CAUSE.str.startswith("Missing")
    joined["is_nat"] = joined.NWCG_GENERAL_CAUSE.eq("Natural")

    miss_by_region = joined.groupby("US_L3NAME")["is_missing"].mean()
    high_miss = set(miss_by_region[miss_by_region >= HIGH_MISS_THRESHOLD].index)
    return joined, eco, high_miss


# --- per-season value/color producers -------------------------------------

def _natural_share(usable, season):
    g = usable[usable.season == season].groupby("US_L3NAME")
    cnt, share = g.size(), g["is_nat"].mean() * 100
    return share[cnt >= MIN_CELL].to_dict()


def _dominant(usable, season, weight):
    """weight='count' -> top cause by rows; weight='acres' -> by FIRE_SIZE."""
    sub = usable[usable.season == season]
    out = {}
    for region, g in sub.groupby("US_L3NAME"):
        if len(g) < MIN_CELL:
            continue
        if weight == "count":
            top = g.NWCG_GENERAL_CAUSE.value_counts().idxmax()
        else:
            top = g.groupby("NWCG_GENERAL_CAUSE")["FIRE_SIZE"].sum().idxmax()
        out[region] = CAUSE_COLORS.get(top, OTHER_COLOR)
    return out


def _draw_panel(ax, eco, high_miss, values, sequential):
    m = eco.copy()
    if sequential:
        m["v"] = m.US_L3NAME.map(values)
        m.plot(column="v", cmap="OrRd", vmin=0, vmax=100, ax=ax,
               edgecolor="white", linewidth=0.15,
               missing_kwds={"color": BLANK_COLOR})
    else:
        m["c"] = m.US_L3NAME.map(values).fillna(BLANK_COLOR)
        m.plot(color=m["c"], ax=ax, edgecolor="white", linewidth=0.15)
    eco[eco.US_L3NAME.isin(high_miss)].plot(
        ax=ax, facecolor="none", edgecolor="#555555", hatch="////", linewidth=0.0)
    ax.axis("off")


def _legend(sequential):
    if sequential:
        return [
            Patch(facecolor="#FEE8C8", label="0% (all human)"),
            Patch(facecolor="#E34A33", label="~50%"),
            Patch(facecolor="#7F0000", label="100% (all natural)"),
            Patch(facecolor="none", edgecolor="#555", hatch="////", label=">=40% missing"),
        ]
    handles = [Patch(facecolor=c, label=n.split("/")[0].split(" and ")[0][:22])
               for n, c in CAUSE_COLORS.items()]
    handles.append(Patch(facecolor="none", edgecolor="#555", hatch="////",
                         label=">=40% missing"))
    return handles


CAPTION = ("Hatched = >=40% cause-missing (read with caution). "
           "Gray = insufficient sample. FPA-FOD 1992-2020.")

# encoding registry: name -> (title, value-fn, sequential?)
ENCODINGS = {
    "natural_share": ("Natural (lightning) share of fires, by season",
                      lambda u, s: _natural_share(u, s), True),
    "dominant_count": ("Dominant cause by ignition COUNT, by season",
                       lambda u, s: _dominant(u, s, "count"), False),
    "dominant_acres": ("Dominant cause by ACRES BURNED, by season",
                       lambda u, s: _dominant(u, s, "acres"), False),
}


def render_small_multiples(joined, eco, high_miss, encoding, save=True, dpi=110):
    """Render one encoding as a 4-season small-multiple figure. Returns the fig."""
    title, value_fn, sequential = ENCODINGS[encoding]
    usable = joined[~joined.is_missing]

    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
    for ax, season in zip(axes.flat, SEASONS):
        _draw_panel(ax, eco, high_miss, value_fn(usable, season), sequential)
        ax.set_title(season, fontsize=15, weight="bold")
    fig.suptitle(title, fontsize=17, weight="bold", y=0.98)
    # Reserve a bottom band for the legend + caption, then place the legend
    # above the caption inside that band so the two never overlap.
    fig.tight_layout(rect=[0, 0.10, 1, 0.96])
    fig.legend(handles=_legend(sequential), loc="lower center", ncol=4,
               fontsize=9, frameon=False, bbox_to_anchor=(0.5, 0.045))
    fig.text(0.5, 0.02, CAPTION, ha="center", fontsize=8, style="italic", color="#555")

    if save:
        IMG_DIR.mkdir(exist_ok=True)
        fig.savefig(IMG_DIR / f"{encoding}_seasons.png", dpi=dpi, bbox_inches="tight")
    return fig


def render_gif(joined, eco, high_miss, encoding="natural_share", filename=None,
               ms_per_frame=None, pingpong=False, dpi=90):
    """Animate any encoding into a looping GIF saved to img/.

    `encoding` is one of ENCODINGS ('natural_share', 'dominant_count',
    'dominant_acres'). One frame per season, cycled Spring -> Summer -> Fall ->
    Winter in a repeating loop (the GIF loops, so it wraps Winter back to
    Spring). Categorical encodings default to a slower frame (their 7-color
    patchwork is harder to track in motion than a color ramp).
    Returns the output Path.
    """
    title, value_fn, sequential = ENCODINGS[encoding]
    if filename is None:
        filename = f"{encoding}_seasons.gif"
    if ms_per_frame is None:
        ms_per_frame = 1500 if sequential else 2000  # slow the categorical loop
    usable = joined[~joined.is_missing]
    IMG_DIR.mkdir(exist_ok=True)
    out = IMG_DIR / filename

    frames = []
    from PIL import Image
    cycle = ["Spring", "Summer", "Fall", "Winter"]  # repeating seasonal order
    for season in cycle:
        fig, ax = plt.subplots(figsize=(9, 6))
        _draw_panel(ax, eco, high_miss, value_fn(usable, season), sequential)
        ax.set_title(season, fontsize=14, weight="bold")
        fig.tight_layout(rect=[0, 0.12, 1, 1])
        fig.legend(handles=_legend(sequential), loc="lower center", ncol=4,
                   fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.05))
        fig.text(0.5, 0.02, CAPTION, ha="center", fontsize=7,
                 style="italic", color="#555")

        fig.canvas.draw()
        buf = fig.canvas.buffer_rgba()  # RGBA buffer -> PIL (backend-agnostic)
        frames.append(Image.frombytes("RGBA", fig.canvas.get_width_height(),
                                       bytes(buf)).convert("RGB"))
        plt.close(fig)

    seq = frames + frames[-2:0:-1] if pingpong else frames
    seq[0].save(out, save_all=True, append_images=seq[1:],
                duration=ms_per_frame, loop=0, disposal=2)
    return out


def render_natural_share_gif(joined, eco, high_miss, **kwargs):
    """Backwards-compatible wrapper: animate the Natural-share (hero) map."""
    return render_gif(joined, eco, high_miss, encoding="natural_share", **kwargs)


# --- non-map slide visuals -------------------------------------------------

ACCENT = "#C1440E"     # burnt orange -- same accent as the Natural encoding
CONTEXT_GRAY = "#BAB0AC"
INK = "#1A1A2E"

def render_burn_concentration(joined, filename="burn_concentration.png",
                              highlight_pct=0.01, dpi=130):
    """Lorenz-style concentration curve: cumulative % of fires vs % of acres.

    Emphasis form -- one accent line + gray equality reference, with the
    'top 1% of fires = ~N% of acres' headline called out. Built from the same
    loaded sample. Returns (Path, headline_share) so the caller can cite the
    exact figure the figure shows.
    """
    sizes = joined["FIRE_SIZE"].sort_values(ascending=False).to_numpy()
    n, total = len(sizes), sizes.sum()
    cum_acres = sizes.cumsum() / total
    cum_fires = (1 + np.arange(n)) / n
    k = max(1, int(n * highlight_pct))
    headline = sizes[:k].sum() / total   # acres share of the top highlight_pct

    fig, ax = plt.subplots(figsize=(8.5, 6))
    # equality reference (if every fire burned the same acreage)
    ax.plot([0, 1], [0, 1], color=CONTEXT_GRAY, lw=2, ls=(0, (4, 4)),
            label="if every fire burned equally")
    # actual concentration curve
    ax.plot(cum_fires, cum_acres, color=ACCENT, lw=3,
            label="actual (FPA-FOD)")
    # callout at the highlight point
    ax.axvline(highlight_pct, color=INK, lw=1, alpha=0.35)
    ax.plot([highlight_pct], [headline], "o", color=ACCENT, ms=9,
            markeredgecolor="white", markeredgewidth=1.5, zorder=5)

    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("Share of fires (largest first)", fontsize=11)
    ax.set_ylabel("Share of total acres burned", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, color="#EEEEEE", lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=10)

    # hero number
    fig.text(0.30, 0.72,
             f"The top {highlight_pct:.0%} of fires\ndrive {headline:.0%} of all "
             f"acres burned",
             fontsize=17, weight="bold", color=INK, va="center")
    fig.text(0.5, 0.005,
             f"Cumulative acres vs. fires, {n:,}-fire sample, FPA-FOD 1992-2020.",
             ha="center", fontsize=8, style="italic", color="#555")
    fig.suptitle("Burn is extremely concentrated", fontsize=17, weight="bold", y=0.97)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    IMG_DIR.mkdir(exist_ok=True)
    out = IMG_DIR / filename
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    return out, headline


def render_text_card(lines, filename, subtitle=None, dpi=130,
                     size=(11, 6.2), accent_first=True):
    """Render a simple title/data slide card as a PNG.

    `lines` is a list of strings shown large and centered; the first is accent
    colored if accent_first. `subtitle` (optional) is a smaller line beneath.
    For Slide 1 (the question) and the provenance card.
    """
    fig = plt.figure(figsize=size)
    fig.patch.set_facecolor("white")
    n = len(lines)
    y0 = 0.62 if subtitle else 0.55
    step = 0.13
    for i, line in enumerate(lines):
        fig.text(0.5, y0 - i * step, line, ha="center", va="center",
                 fontsize=22 if i == 0 else 17,
                 weight="bold" if i == 0 else "normal",
                 color=ACCENT if (i == 0 and accent_first) else INK)
    if subtitle:
        fig.text(0.5, y0 - n * step - 0.02, subtitle, ha="center", va="center",
                 fontsize=12, style="italic", color="#555")
    IMG_DIR.mkdir(exist_ok=True)
    out = IMG_DIR / filename
    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out
