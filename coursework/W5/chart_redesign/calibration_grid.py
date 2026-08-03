"""Overlay a calibrated grid on the original Chart B: 10-fatality rows + yearly columns.

Y calibration (tick-label centers):  300 -> row 143.0,  700 -> row 717.0
X calibration (tick-label centers): 2012 -> col 232.5, 2024 -> col 1304.0
Checked against 2018 -> col 768.0 (predicted 768.25, off by 0.25 px).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SRC = Path("/Users/crudman/Documents/GitHub/MSDS696/coursework/W5/chart_redesign/"
           "original_charts/chartB_highway_fatalities.png")
OUT = Path("/Users/crudman/Documents/GitHub/MSDS696/coursework/W5/chart_redesign/"
           "original_charts/chartB_calibration_grid.png")

Y300_ROW, Y700_ROW = 143.0, 717.0
PX_PER_UNIT = (Y700_ROW - Y300_ROW) / (700 - 300)

X2012_COL, X2024_COL = 232.5, 1304.0
PX_PER_YEAR = (X2024_COL - X2012_COL) / (2024 - 2012)

PLOT_TOP, PLOT_BOTTOM = 90, 717


def row_for(value: float) -> float:
    return Y300_ROW + (value - 300) * PX_PER_UNIT


def col_for(year: float) -> float:
    return X2012_COL + (year - 2012) * PX_PER_YEAR


print(f"px/year = {PX_PER_YEAR:.3f}")
print(f"check 2018 -> {col_for(2018):.2f} (measured 768.0)")

im = Image.open(SRC).convert("RGB")
d = ImageDraw.Draw(im, "RGBA")

try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
    small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 11)
except OSError:
    font = small = ImageFont.load_default()

# --- horizontal: every 10 fatalities, heavier every 50 ----------------------
for value in range(300, 701, 10):
    y = row_for(value)
    major = value % 50 == 0
    d.line([(col_for(2011.7), y), (col_for(2024.35), y)],
           fill=(0, 0, 0, 150) if major else (0, 0, 0, 70),
           width=2 if major else 1)
    if major:
        d.text((col_for(2024.35) + 6, y - 8), str(value),
               fill=(150, 0, 0), font=font)

# --- vertical: every year, heavier on the labelled even years ---------------
for year in range(2012, 2025):
    x = col_for(year)
    major = year % 2 == 0
    d.line([(x, PLOT_TOP), (x, PLOT_BOTTOM)],
           fill=(150, 0, 0, 160) if major else (150, 0, 0, 80),
           width=2 if major else 1)
    if not major:
        d.text((x - 12, PLOT_TOP - 16), str(year), fill=(150, 0, 0), font=small)

im.save(OUT)
print("wrote", OUT)
