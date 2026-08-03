"""W5 executive visuals — the pinpoint-vs-area confound, drawn.

Two candidates for the practice-talk visual (V1), rendered from the same data so
they can be compared side by side before one is chosen:

* `plot_one_fire()`  — a single fire's true burned perimeter with the one point
  the record stores, hexgrid faint underneath. The argument in one picture, no
  axis or statistical literacy required.
* `plot_before_after()` — the same region twice: hexes shaded by point-attributed
  acres, then by perimeter-distributed acres. The methods story — what the naive
  target would have measured versus what the corrected one does.

Design notes
------------
Audience is non-technical executives, so these are deliberately *not* analyst
charts: no axes, no gridlines, no tick labels.

**Headlines and captions are not drawn into the images.** Each figure carries only
its marks plus the few labels that name them, and every plotting function *returns*
the numbers a caption would need (`n_hex_before`, `acres`, the chosen fire's name
and size). The prose lives in the notebook's markdown, so the PNGs stay composable:
a slide can crop, re-title, or re-lay-out them without fighting text baked into the
raster at a fixed position and size.

Color, and why the two figures do not share a palette
-----------------------------------------------------
`plot_before_after` shades hexes by burned magnitude alone, so it uses the
**flame ramp** (`SEQ_FLAME`) — validated single-hue, light->dark. Nothing else
in that figure competes for the same visual channel.

`plot_one_fire` is different: it carries two *kinds* of thing at once, a burned
area and a recorded coordinate. There the area stays **blue** and the point stays
categorical **orange**, because a flame-ramped perimeter would put the point and
the area in the same hue family and the dot would read as "a hotter part of the
fire" rather than "what the record stores". Keeping the burned area cool there is
what makes the single orange mark legible.

So: flame where color means *how much burned*; blue-and-orange where color means
*which thing is which*.

Fire complexes are excluded from the single-fire visual on purpose. When several
fires share one `MTBS_ID` (the 2020 August Complex binds 8 FPA-FOD rows), MTBS
maps the complex once, so drawing "one fire's perimeter" would in fact be drawing
eight fires' combined footprint. See `hex_burn.build_hex_acres` for how the acre
split handles that case; for a *picture* the honest move is to pick a fire that
is genuinely alone inside its perimeter.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import hex_burn

# --- palette (from the project's reference instance) -------------------------
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#7a7975"

# Sequential blue, 100 -> 700: continuous burned-acre magnitude.
SEQ_BLUE = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
    "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
    "#184f95", "#104281", "#0d366b",
]
# Sequential red-orange, light -> dark: burned-acre magnitude on the choropleth
# pair. Flame-colored by request, but still a SINGLE hue family ramped by
# lightness rather than a yellow->orange->red rainbow. The rainbow version reads
# as three categories on continuous data, collapses in grayscale, and loses its
# ordering for red-green colorblind viewers; this keeps the fire association while
# staying a legitimate sequential scale.
#
# Validated with the project's palette validator (light surface, --ordinal):
#   lightness monotone PASS | adjacent dL PASS | light-end contrast 2.22:1 PASS
#   | single hue 14 deg spread PASS
# The light end deliberately starts at a mid-orange rather than a near-white
# tint: warm hues are intrinsically light, so a pale flame step fails the 2:1
# contrast floor against the surface and becomes indistinguishable from the
# no-burn gray. Starting darker costs some dynamic range at the bottom and buys
# a ramp whose lightest burned hex is still visibly *burned*.
SEQ_FLAME = [
    "#fc8f5e", "#ef5530", "#c62d15", "#8c180c", "#520c05",
]
# Categorical slot 2 — the ignition point on V1-A. A different KIND of thing than
# burned magnitude, so it never comes from a sequential ramp.
POINT_ORANGE = "#eb6834"
PERIM_FILL = "#2a78d6"
HEX_EDGE = "#d8d7d3"
# Hexes with no burn at all. A neutral warm-gray, deliberately NOT the palest step
# of the flame ramp: "nothing burned here" is a different state from "a little
# burned here", and a near-ramp gray would blur the two.
NO_BURN = "#eeece8"


def _seq_cmap(palette=None):
    """Sequential colormap for burned magnitude. Defaults to the flame ramp."""
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list("proj_seq", palette or SEQ_FLAME)


def _strip(ax):
    """Remove every axis affordance. These are maps, not plots."""
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_facecolor(SURFACE)


def pick_solo_fire(fires: pd.DataFrame, perims, *, min_acres: float = 1000.0,
                   mtbs_col: str = "MTBS_ID", require_point_inside: bool = True):
    """A large fire that is the ONLY FPA-FOD row on its perimeter.

    Returns the row nearest the median size among such fires. Choosing near the
    median rather than the maximum is deliberate: the visual should show what is
    typical, not what is most dramatic. Complex constituents are excluded because
    their perimeter is the complex's, not theirs.

    `require_point_inside` additionally demands that the recorded ignition point
    actually falls within the fire's own perimeter. Only **75%** of solo large
    fires satisfy that — in the other quarter the stored coordinate lies outside
    the area that burned. That is a real and reportable defect, but it is a
    *separate* claim from the one V1 makes: a headline about the scale mismatch
    should not also be arguing that the point is in the wrong place, or a viewer
    reasonably objects that the fire simply moved. The outside-perimeter cases
    belong in their own diagnostic, not in this visual.
    """
    import geopandas as gpd

    f = fires.copy()
    f["_mid"] = f[mtbs_col].fillna("").astype(str).str.strip()
    resolvable = set(perims["event_id"].astype(str).str.strip())
    cand = f[(f["_mid"].isin(resolvable)) & (f["FIRE_SIZE"] >= min_acres)]

    solo_ids = cand.groupby("_mid")["FOD_ID"].count()
    solo_ids = set(solo_ids[solo_ids == 1].index)
    cand = cand[cand["_mid"].isin(solo_ids)].copy()
    if cand.empty:
        raise ValueError("no solo perimeter-backed fire above min_acres")

    if require_point_inside:
        geo = perims.copy()
        geo["event_id"] = geo["event_id"].astype(str).str.strip()
        geo = geo[geo["event_id"].isin(set(cand["_mid"]))].to_crs(4326).set_index("event_id")
        geo = geo[~geo.index.duplicated(keep="first")]
        pts = gpd.points_from_xy(cand["LONGITUDE"], cand["LATITUDE"])
        keep = [
            m in geo.index and geo.loc[m].geometry.contains(p)
            for m, p in zip(cand["_mid"], pts)
        ]
        inside = cand[keep]
        if not inside.empty:
            cand = inside

    target = cand["FIRE_SIZE"].median()
    return cand.iloc[(cand["FIRE_SIZE"] - target).abs().argsort().iloc[0]]


def plot_one_fire(fire, perims, hexgrid, out_path: Path, *, pad_frac: float = 0.45):
    """V1-A — 'The record says a fire happened here. It burned all of this.'"""
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from shapely.geometry import Point

    mid = str(fire["MTBS_ID"]).strip()
    geom = perims[perims["event_id"].astype(str).str.strip() == mid].to_crs(hexgrid.crs)
    pt = gpd.GeoDataFrame(
        geometry=[Point(fire["LONGITUDE"], fire["LATITUDE"])], crs=4326
    ).to_crs(hexgrid.crs)

    minx, miny, maxx, maxy = geom.total_bounds
    padx, pady = (maxx - minx) * pad_frac, (maxy - miny) * pad_frac
    pad = max(padx, pady)
    win = (minx - pad, miny - pad, maxx + pad, maxy + pad)

    near = hexgrid.cx[win[0]:win[2], win[1]:win[3]]

    fig, ax = plt.subplots(figsize=(9, 8.2), facecolor=SURFACE)
    _strip(ax)

    near.boundary.plot(ax=ax, color=HEX_EDGE, linewidth=0.8, zorder=1)
    geom.plot(ax=ax, facecolor=PERIM_FILL, edgecolor=PERIM_FILL,
              alpha=0.30, linewidth=2.0, zorder=2)
    geom.boundary.plot(ax=ax, color=PERIM_FILL, linewidth=2.0, zorder=3)

    # 2px surface ring on the overlapping mark, per the mark spec.
    pt.plot(ax=ax, color=POINT_ORANGE, markersize=155, zorder=5,
            edgecolor=SURFACE, linewidth=2.0)

    ax.set_xlim(win[0], win[2])
    ax.set_ylim(win[1], win[3])

    # Labels are placed outside the shape and pointed in, so they never sit on top
    # of each other or on the mark they describe. The point label leaves to the
    # left, the area label to the right, regardless of where in the shape the
    # ignition happens to fall.
    px, py = float(pt.geometry.x.iloc[0]), float(pt.geometry.y.iloc[0])
    ax.annotate(
        "what the record stores:\na single point",
        xy=(px, py), xycoords="data",
        xytext=(0.04, 0.30), textcoords="axes fraction",
        fontsize=13, color=TEXT_PRIMARY, fontweight="700", ha="left", va="center",
        arrowprops=dict(arrowstyle="-", color=TEXT_SECONDARY, linewidth=1.4,
                        shrinkA=2, shrinkB=8, connectionstyle="arc3,rad=0.12"),
    )
    b = geom.total_bounds
    edge_x, edge_y = b[2], (b[1] + b[3]) / 2
    ax.annotate(
        f"what actually burned:\n{fire['FIRE_SIZE']:,.0f} acres",
        xy=(edge_x, edge_y), xycoords="data",
        xytext=(0.97, 0.72), textcoords="axes fraction",
        fontsize=13, color="#0d366b", fontweight="700", ha="right", va="center",
        arrowprops=dict(arrowstyle="-", color="#5598e7", linewidth=1.4,
                        shrinkA=2, shrinkB=6, connectionstyle="arc3,rad=-0.12"),
    )

    # No headline or caption is drawn: the figure carries only marks and the two
    # labels that name them. Titles and sourcing live in the notebook's markdown,
    # so the image can be composed into a slide without baked-in text.
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)

    return {
        "path": out_path,
        "fire_name": str(fire.get("FIRE_NAME", "")).title(),
        "year": int(fire["FIRE_YEAR"]),
        "region": fire["region"],
        "acres": float(fire["FIRE_SIZE"]),
        "hex_acres": hex_burn.hex_area_acres(5),
    }


def plot_before_after(hex_acres: pd.DataFrame, hexgrid, fires: pd.DataFrame,
                      out_path: Path, *, region: str, resolution: int = 5,
                      year: int | None = None):
    """V1-B — 'We knew how much burned. We didn't know where.'

    Left: every fire's acres credited to its ignition hex (what a naive target
    measures). Right: acres distributed by the satellite-mapped perimeter. Both
    panels share one color scale, so the difference is in the pattern rather than
    in the shading.

    `year` scopes both panels to a single fire year, and it matters. Pooled over
    the full 1992-2020 record, essentially every hex in a fire-prone region has
    burned at some point, so both panels saturate and the comparison shows
    nothing — the aggregate hides exactly the difference the visual exists to
    make. One season is also the unit a planner actually allocates against.
    """
    import h3
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    grid = hexgrid[hexgrid["region"] == region].copy()
    keep = set(grid["hex_id"])

    # BEFORE — naive point attribution, computed here so the comparison is explicit.
    f = fires[fires["region"] == region].dropna(subset=["LATITUDE", "LONGITUDE"])
    if year is not None:
        f = f[f["FIRE_YEAR"] == year]
        hex_acres = hex_acres[hex_acres["fire_key"].isin(set(f["FOD_ID"]))]
    naive_hex = [
        h3.latlng_to_cell(la, lo, resolution)
        for la, lo in zip(f["LATITUDE"].to_numpy(), f["LONGITUDE"].to_numpy())
    ]
    before = (
        pd.DataFrame({"hex_id": naive_hex, "ac": f["FIRE_SIZE"].to_numpy()})
        .groupby("hex_id")["ac"].sum()
    )
    after = (
        hex_acres[hex_acres["hex_id"].isin(keep)]
        .groupby("hex_id")["hex_acres"].sum()
    )

    g = grid.set_index("hex_id")
    g["before"] = before.reindex(g.index).fillna(0.0)
    g["after"] = after.reindex(g.index).fillna(0.0)

    vmax = float(max(g["before"].max(), g["after"].max()))
    vmin = max(1.0, vmax / 5000)
    norm = LogNorm(vmin=vmin, vmax=vmax)
    cmap = _seq_cmap()

    fig, axes = plt.subplots(1, 2, figsize=(11, 6.6), facecolor=SURFACE)
    for ax, col in zip(axes, ["before", "after"]):
        _strip(ax)
        plot = g.copy()
        plot.loc[plot[col] <= 0, col] = np.nan
        plot.plot(ax=ax, column=col, cmap=cmap, norm=norm,
                  edgecolor=HEX_EDGE, linewidth=0.4,
                  missing_kwds={"color": NO_BURN, "edgecolor": HEX_EDGE, "linewidth": 0.4})

    # Panels are drawn bare. Which is left and which is right is stated in the
    # notebook markdown, so the pair can be cropped or re-laid-out for a slide
    # without fighting baked-in titles.
    # Each panel is set to the SAME extent so the two maps are directly
    # comparable, then packed close: with no titles between them, wide spacing
    # just reads as a gap.
    for ax in axes:
        ax.set_xlim(*g.total_bounds[[0, 2]])
        ax.set_ylim(*g.total_bounds[[1, 3]])
        ax.set_aspect("equal")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01, wspace=-0.10)
    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)

    return {
        "path": out_path,
        "region": region,
        "year": year,
        "n_hex_before": int((g["before"] > 0).sum()),
        "n_hex_after": int((g["after"] > 0).sum()),
        "n_hex_total": int(len(g)),
        "acres": float(g["after"].sum()),
        "hex_acres": hex_burn.hex_area_acres(resolution),
    }


def plot_national(hex_acres: pd.DataFrame, conus_layer, out_path: Path, *,
                  resolution: int = 5, since_year: int | None = None,
                  fires: pd.DataFrame | None = None, top_frac: float | None = 0.10,
                  min_acres: float | None = None, year: int | None = None,
                  alpha_low: float | None = None):
    """National view — CONUS hexes shaded by total perimeter-corrected burned acres.

    CONUS only, and deliberately so: Alaska is in the panel (20.4% of burned acres)
    but cannot share a projection with the lower 48. Drawing both on one canvas
    would either distort Alaska beyond recognition or shrink CONUS to illegibility,
    and the inset-map convention that solves this is a composition decision for the
    slide, not something to bake into the raster. The number reported alongside
    this figure should always name the scope.

    Colored by burned *fraction of hex area* rather than raw acres so that hexes
    clipped small at a coastline are not penalised for being small.
    """
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    ha = hex_acres
    if since_year is not None or year is not None:
        if fires is None:
            raise ValueError("since_year/year require `fires` to map fire_key -> year")
        yr = fires.set_index("FOD_ID")["FIRE_YEAR"]
        mapped = ha["fire_key"].map(yr)
        ha = ha[mapped == year] if year is not None else ha[mapped >= since_year]

    eco = gpd.read_file(conus_layer) if not hasattr(conus_layer, "crs") else conus_layer
    eco = eco.rename(columns={"US_L3NAME": "region"})[["region", "geometry"]]
    grid = hex_burn.build_hexgrid(eco, resolution, crs=hex_burn.ALBERS_CONUS)

    tot = ha.groupby("hex_id")["hex_acres"].sum()
    grid = grid.set_index("hex_id")
    grid["acres"] = tot.reindex(grid.index).fillna(0.0)
    grid["frac"] = grid["acres"] / grid["land_area_acres"]

    fig, ax = plt.subplots(figsize=(13, 8.2), facecolor=SURFACE)
    _strip(ax)

    # Shade only the hexes that carry the burn. A log ramp over every hex with any
    # burn at all colors 93% of the map and reads as "everywhere burns" -- the
    # opposite of what the data says, because the median hex burns 0.5% of its own
    # area over 29 years. Thresholding to the top decile makes the ink match the
    # claim: these are the hexes a planner would actually shortlist.
    plot = grid.copy()
    if alpha_low is not None:
        # Magnitude carries BOTH lightness and opacity, so trivial burns fade
        # toward the surface instead of being cut at a hard boundary.
        #
        # The floor is not zero, and that is the whole design of this branch: a
        # fully transparent mark is invisible, and a nearly-transparent one drops
        # below the 2:1 contrast the palette validator enforces -- it survives on
        # a monitor and disappears on a projector. `alpha_low` is therefore the
        # *minimum legible* opacity, not "off". Hexes with genuinely no burn stay
        # the flat no-burn gray, which is a categorical state rather than the
        # bottom of the ramp.
        import matplotlib as mpl

        burned = plot["frac"] > 0
        lo = float(plot.loc[burned, "frac"].min())
        hi = float(plot.loc[burned, "frac"].max())
        norm = LogNorm(vmin=max(lo, 1e-6), vmax=hi)
        cmap = _seq_cmap()

        plot["_a"] = 0.0
        v = norm(plot.loc[burned, "frac"].to_numpy()).clip(0, 1)
        plot.loc[burned, "_a"] = alpha_low + (1.0 - alpha_low) * v

        rgba = cmap(norm(plot["frac"].fillna(0).to_numpy()))
        rgba[:, 3] = plot["_a"].to_numpy()
        rgba[~burned.to_numpy()] = mpl.colors.to_rgba(NO_BURN)

        plot.plot(ax=ax, color=rgba, edgecolor="none", linewidth=0)
        ax.set_aspect("equal")
        fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
        fig.savefig(out_path, dpi=200, facecolor=SURFACE,
                    bbox_inches="tight", pad_inches=0.2)
        plt.close(fig)
        s0 = grid["acres"].sort_values(ascending=False)
        c0 = s0.cumsum() / s0.sum()
        return {
            "path": out_path, "mode": "opacity", "alpha_low": alpha_low,
            "year": year, "n_hexes": int(len(grid)),
            "n_burned": int(burned.sum()), "acres": float(grid["acres"].sum()),
            "n_shaded": int(burned.sum()), "shaded_acre_share": 1.0,
            "top1_share": float(c0.iloc[int(len(s0) * 0.01) - 1]),
            "top10_share": float(c0.iloc[int(len(s0) * 0.10) - 1]),
            "since_year": since_year, "top_frac": None, "min_acres": None,
        }
    if min_acres is not None:
        # Absolute cut, required for a single season. A percentile threshold works
        # on the 29-year pool but breaks down on one year: in 2020 the top 10% of
        # *burned* hexes already hold 97% of the acres and the median burned hex
        # burns 0.01% of its own area, so any percentile either shades thousands
        # of effectively-empty hexes or collapses to the megafires alone. An acre
        # floor is also the interpretable one -- "at least 100 acres burned here"
        # needs no explanation, unlike "above the 90th percentile".
        cut = float(min_acres) / hex_burn.hex_area_acres(resolution)
    else:
        cut = float(plot["frac"].quantile(1 - top_frac))
    plot.loc[plot["frac"] < cut, "frac"] = np.nan
    plot.plot(ax=ax, column="frac", cmap=_seq_cmap(),
              norm=LogNorm(vmin=max(cut, 1e-4), vmax=float(plot["frac"].max())),
              edgecolor="none", linewidth=0,
              missing_kwds={"color": NO_BURN, "edgecolor": "none"})
    ax.set_aspect("equal")

    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)

    s = grid["acres"].sort_values(ascending=False)
    cum = s.cumsum() / s.sum()
    shaded = grid["frac"] >= cut
    return {
        "path": out_path,
        "top_frac": top_frac,
        "min_acres": min_acres,
        "year": year,
        "n_shaded": int(shaded.sum()),
        "shaded_acre_share": float(grid.loc[shaded, "acres"].sum() / grid["acres"].sum()),
        "n_hexes": int(len(grid)),
        "n_burned": int((grid["acres"] > 0).sum()),
        "acres": float(grid["acres"].sum()),
        "top1_share": float(cum.iloc[int(len(s) * 0.01) - 1]),
        "top10_share": float(cum.iloc[int(len(s) * 0.10) - 1]),
        "since_year": since_year,
    }


SEASON_LABEL = {0: "Winter", 1: "Spring", 2: "Summer", 3: "Fall"}


def animate_national(hex_acres: pd.DataFrame, fires: pd.DataFrame, conus_layer,
                     out_path: Path, *, resolution: int = 5, alpha_low: float = 0.12,
                     trail: int = 3, trail_decay: float = 0.45, floor_acres: float = 100.0,
                     ms_per_frame: int = 260, base_year: int = 1992,
                     verbose: bool = True):
    """Timelapse of burned area across CONUS, one frame per season-year.

    117 frames on the project's `season_idx` spine (winter 1992 -> 2020), rendered
    to an animated GIF following the convention in `src/season_maps.py`.

    Two encoding decisions do the work:

    **One color scale across every frame.** Computed once over all frames and held
    fixed. A per-frame scale would renormalise each season to its own maximum, so a
    quiet winter would look identical to summer 2020 — the animation would show
    *where* fire was and hide *how much*, which inverts the project's central
    finding that the volatility is the story.

    **A fade trail.** Each frame draws the current season at full strength plus the
    previous `trail` seasons at geometrically decaying opacity. This is a *design
    choice, not data*: the older burns are not still burning. It exists because a
    single season at 260ms flashes past too quickly to register, and because
    successive frames in the same place read as recurrence. Any caption must say so
    — see the notebook markdown.

    Note on what a frame means: a fire's acres land in the season it was
    *discovered*. `CONT_DATE` is null for 38% of records, so true within-season
    spread is not recoverable and is not implied here.
    """
    import geopandas as gpd
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    from PIL import Image as PILImage

    eco = gpd.read_file(conus_layer) if not hasattr(conus_layer, "crs") else conus_layer
    eco = eco.rename(columns={"US_L3NAME": "region"})[["region", "geometry"]]
    grid = hex_burn.build_hexgrid(eco, resolution, crs=hex_burn.ALBERS_CONUS)
    grid = grid.set_index("hex_id")

    si = fires.set_index("FOD_ID")["season_idx"]
    ha = hex_acres.assign(_si=hex_acres["fire_key"].map(si)).dropna(subset=["_si"])
    ha = ha[ha["hex_id"].isin(grid.index)]

    # Absolute acres, NOT fraction-of-hex. The fraction denominator flatters small
    # clipped hexes -- 30 acres in a sliver at a coastline scores higher than 3,000
    # acres in a full hex -- and at animation scale, where a hex is a few pixels,
    # that reads as saturation everywhere. Acres are also what the caption quotes.
    per = ha.groupby(["_si", "hex_id"])["hex_acres"].sum()

    frames_idx = sorted(int(x) for x in ha["_si"].unique())
    vmax = float(per.max())
    # Floor on POSITIVE values only, and guard against a zero quantile. `per` is a
    # sparse series, so its low quantiles are 0.0 -- feeding that to LogNorm makes
    # every hex saturate at full color and the map reads as "the whole country
    # burned". Anchor instead at 10 acres in a res-5 hex, which is interpretable
    # and safely positive.
    # Anchor the ramp where burn becomes meaningful rather than at the data floor.
    # Below ~100 acres in a 62,494-acre hex the burn is invisible on the ground and
    # only adds noise to the animation; those hexes render at the alpha floor.
    vmin = float(floor_acres)
    norm = LogNorm(vmin=vmin, vmax=vmax)          # <-- fixed across all frames
    cmap = _seq_cmap()
    no_burn_rgba = mpl.colors.to_rgba(NO_BURN)

    tmp_dir = out_path.parent / f"_{out_path.stem}_frames"
    tmp_dir.mkdir(exist_ok=True)
    written: list[Path] = []

    for n, idx in enumerate(frames_idx):
        rgba = np.tile(np.array(no_burn_rgba), (len(grid), 1))
        # Oldest first so the current season paints last and wins.
        for back in range(trail, -1, -1):
            layer = per.get(idx - back, None) if (idx - back) in frames_idx else None
            if layer is None:
                continue
            vals = layer.reindex(grid.index)
            # Only hexes at or above the floor are drawn at all. Giving sub-floor
            # hexes the minimum alpha instead was the bug that made every frame
            # look like a national conflagration: ~13,000 hexes burn under 100
            # acres in a busy season, and at animation scale a hex is a few pixels,
            # so a floor-alpha wash over all of them saturates the map and hides
            # the megafires the frame is about.
            m = vals.notna().to_numpy() & (vals.fillna(0).to_numpy() >= vmin)
            if not m.any():
                continue
            weight = trail_decay ** back
            c = cmap(norm(vals.fillna(0).to_numpy()))
            a = (alpha_low + (1 - alpha_low) * norm(vals.fillna(0).to_numpy()).clip(0, 1)) * weight
            rgba[m, :3] = c[m, :3]
            rgba[m, 3] = np.maximum(rgba[m, 3], a[m])

        fig, ax = plt.subplots(figsize=(8.5, 5.4), facecolor=SURFACE)
        _strip(ax)
        grid.plot(ax=ax, color=rgba, edgecolor="none", linewidth=0)
        ax.set_aspect("equal")
        yr = base_year + idx // 4
        ax.text(0.02, 0.06, f"{SEASON_LABEL[idx % 4]} {yr}", transform=ax.transAxes,
                fontsize=17, fontweight="700", color=TEXT_PRIMARY, ha="left")
        fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
        fp = tmp_dir / f"f{n:04d}.png"
        fig.savefig(fp, dpi=100, facecolor=SURFACE)
        plt.close(fig)
        written.append(fp)
        if verbose and n % 20 == 0:
            print(f"    frame {n + 1}/{len(frames_idx)}", flush=True)

    imgs = [PILImage.open(f).convert("P", palette=PILImage.ADAPTIVE, colors=96) for f in written]
    imgs[0].save(out_path, save_all=True, append_images=imgs[1:],
                 duration=ms_per_frame, loop=0, disposal=2, optimize=True)
    for f in written:
        f.unlink()
    tmp_dir.rmdir()

    return {"path": out_path, "n_frames": len(written),
            "vmin": vmin, "vmax": vmax, "trail": trail,
            "ms_per_frame": ms_per_frame,
            "size_mb": out_path.stat().st_size / 1e6}
