# Earth System Trend Detective

Pick **what** to investigate (heat, water, land, air) and **where**. The app downloads 45 years of
monthly NASA MERRA-2 data (via the NASA POWER API), removes the seasonal cycle, fits a linear
trend and tests whether it is statistically significant with a t-test and the Mann-Kendall test.
It then explains the result in plain language.

2026 NASA Space Apps Challenge – "Be An Earth System Trend Detective!"

## Features
- Guided questions: theme → place → variable, with a plain-language definition of every variable
- Trend chart: monthly and yearly anomalies, linear trend, 95% confidence band
- Verdict card: rate per decade, total change, t-test and Mann-Kendall p-values, and, when not
  significant, an estimate of how many years of data would be needed
- Compare places: the same variable trending in opposite directions in different climates
- Regional map: temperature trend per 0.5° grid cell, marked by significance
- Three worked "detective cases"; CSV download of any series; custom coordinates (live API)

## Data
NASA POWER monthly API (https://power.larc.nasa.gov), MERRA-2 meteorology from NASA GMAO,
1981–2025, ~0.5° grid. Variables: T2M, T2M_MAX, TS, PRECTOTCORR, RH2M, GWETROOT, ALLSKY_SRF_ALB, PS, WS2M.

## Run locally
```bash
pip install -r requirements.txt
python fetch_data.py      # one-time download into data/ (~1-3 min)
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)
1. Push this folder, **including the data/ folder**, to a public GitHub repo.
2. Go to https://share.streamlit.io → New app → pick the repo, branch `main`, file `app.py` → Deploy.

## Method and limits
See the "How it works" tab in the app. Linear trends only; reanalysis is model-based; a 0.5° cell
averages over ~50 km; significance shows *that* something changed, not *why*.
