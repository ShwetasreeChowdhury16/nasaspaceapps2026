"""Run once on your machine (needs internet):  python fetch_data.py
Downloads 1981-2025 monthly data for the demo locations, plus one regional temperature grid,
into data/. The app reads these files, so the demo works even if the API is slow."""

import time
from pathlib import Path

import pandas as pd

from config import LOCATIONS, PARAMS
from power import fetch_point, fetch_region

DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

# Regional grid for the trend map. POWER limits regional boxes to roughly 10° x 10°.
# Default: the US Southwest, where some cells warm much faster than others.
REGION = {"name": "US Southwest", "lat_min": 30, "lat_max": 40, "lon_min": -120, "lon_max": -110}


def main():
    frames = []
    for name, loc in LOCATIONS.items():
        print(f"Downloading {name} ...", flush=True)
        df = fetch_point(loc["lat"], loc["lon"])
        df["location"] = name
        frames.append(df)
        time.sleep(1)  # be polite to the API
    points = pd.concat(frames, ignore_index=True)
    points.to_csv(DATA / "power_monthly.csv", index=False)
    print(f"Saved {len(points):,} rows to data/power_monthly.csv")
    got = set(points["param"].unique())
    print("Variables downloaded:", ", ".join(sorted(got)))
    missing = [p for p in PARAMS if p not in got]
    if missing:
        print("Not available from the service (the app hides these):", ", ".join(missing))

    print(f"Downloading regional temperature grid for {REGION['name']} (can take 1-3 minutes) ...", flush=True)
    try:
        grid = fetch_region(REGION["lat_min"], REGION["lat_max"], REGION["lon_min"], REGION["lon_max"], "T2M")
        grid["region"] = REGION["name"]
        grid.to_csv(DATA / "region_T2M.csv", index=False)
        print(f"Saved {len(grid):,} rows to data/region_T2M.csv")
    except Exception as exc:  # the map is optional; the app still works without it
        print(f"Regional download failed ({exc}). The app will skip the map.")


if __name__ == "__main__":
    main()
