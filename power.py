"""Download monthly data from the NASA POWER API (MERRA-2 meteorology). No API key needed."""

import pandas as pd
import requests

from config import END_YEAR, PARAMS, START_YEAR

POINT_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
REGION_URL = "https://power.larc.nasa.gov/api/temporal/monthly/regional"
MISSING = -999


def _parse_parameter_block(block: dict) -> pd.DataFrame:
    """POWER returns {"PARAM": {"YYYYMM": value, ...}}. Month 13 is the annual mean; drop it."""
    rows = []
    for param, series in block.items():
        for key, value in series.items():
            year, month = int(key[:4]), int(key[4:])
            if month == 13 or value is None or value == MISSING:
                continue
            rows.append({"param": param, "year": year, "month": month, "value": float(value)})
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(dict(year=df.year, month=df.month, day=15))
    return df


def _point_request(lat, lon, params, start, end) -> pd.DataFrame:
    resp = requests.get(
        POINT_URL,
        params={
            "parameters": ",".join(params),
            "community": "AG",
            "latitude": lat,
            "longitude": lon,
            "start": start,
            "end": end,
            "format": "JSON",
        },
        timeout=60,
    )
    resp.raise_for_status()
    return _parse_parameter_block(resp.json()["properties"]["parameter"])


def fetch_point(lat: float, lon: float, params=PARAMS, start=START_YEAR, end=END_YEAR) -> pd.DataFrame:
    """Monthly values for one point. Returns long table: param, year, month, value, date.
    If the service rejects the combined request (for example one variable is not offered
    monthly), each variable is requested on its own and the rejected ones are skipped."""
    try:
        return _point_request(lat, lon, params, start, end)
    except requests.HTTPError:
        frames = []
        for p in params:
            try:
                frames.append(_point_request(lat, lon, [p], start, end))
            except requests.HTTPError as exc:
                print(f"  skipped {p}: {exc}")
        if not frames:
            raise
        return pd.concat(frames, ignore_index=True)


def fetch_region(lat_min, lat_max, lon_min, lon_max, param="T2M", start=START_YEAR, end=END_YEAR) -> pd.DataFrame:
    """Monthly values on POWER's 0.5° grid for a box (one parameter per request).
    Returns long table: lat, lon, param, year, month, value, date."""
    resp = requests.get(
        REGION_URL,
        params={
            "parameters": param,
            "community": "AG",
            "latitude-min": lat_min,
            "latitude-max": lat_max,
            "longitude-min": lon_min,
            "longitude-max": lon_max,
            "start": start,
            "end": end,
            "format": "JSON",
        },
        timeout=300,
    )
    resp.raise_for_status()
    frames = []
    for feature in resp.json()["features"]:
        lon, lat = feature["geometry"]["coordinates"][:2]
        df = _parse_parameter_block(feature["properties"]["parameter"])
        df["lat"], df["lon"] = lat, lon
        frames.append(df)
    return pd.concat(frames, ignore_index=True)
