# 🌍 Earth System Trend Detective

**Is it changing here, and is the change real?**

A Streamlit app that lets anyone pick a place on Earth and a climate question, then answers it with 45 years of NASA data and plain-language statistics. It removes the seasons, fits a trend, and tells you whether the change is real or could just be random year-to-year variation.

Built for the **2026 NASA Space Apps Challenge** - *Be an Earth System Trend Detective!*

> **Live app:** `<add your Streamlit Cloud URL here>`
> **Demo video:** `<add your video link here>`

---

## What it does

1. **Choose what to investigate** - Heat 🔥, Water 💧, Land 🌱 or Air 💨. The page colour and a faint animated background (sun, waves, hills, wind) follow the topic.
2. **Choose where** - pick from 12 preset places (cities, deserts, rainforest, Arctic, mountains, the Sahel) or **click anywhere on the interactive globe** to investigate that exact point.
3. **Choose the clue** - each topic offers variables with an everyday question and a plain definition (e.g. *"Is it getting hotter?"* → air temperature 2 m above the ground).
4. **Get a verdict** - a headline answer such as *"Yes, air temperature here is rising: about 0.34 °C every 10 years"*, with a confidence level and four plain-language cards:
   - **How fast is it changing?** (trend slope per decade)
   - **How sure are we about that speed?** (95% confidence interval)
   - **Could it just be a fluke?** (t-test p-value, expressed as "about 1 in N")
   - **Does a second check agree?** (Mann-Kendall test)

   Each card carries an evidence rating (Very strong / Strong / Weak hint / No real evidence), and an expandable guide explains every measure and what counts as good.

### Tabs
| Tab | What it shows |
|---|---|
| **Trend** | Monthly and yearly anomalies, linear trend and 95% confidence band, with a "how to read this" note |
| **What else is changing here?** | Tests every variable at the place, ranks them by evidence, and suggests which clues suit the region type (city, desert, rainforest, semi-arid, polar, mountain, temperate) |
| **Raw data and seasons** | The original series and the seasonal cycle that gets removed; CSV download |
| **Compare places** | The same variable's trend across all preset places, coloured by direction and significance |
| **Regional map** | Temperature trend per 0.5° grid cell around a region, marked by significance |
| **How it works** | Method, data source, assumptions and limits |

---

## Data

All data comes from one NASA source, so every variable is consistent in grid, period and processing:

- **NASA POWER API** (https://power.larc.nasa.gov) - monthly values, no API key needed
- Underlying data: **MERRA-2 reanalysis** from NASA's Global Modeling and Assimilation Office (GMAO)
- **Period:** 1981-2025 · **Resolution:** about 0.5° (~50 km)

| Topic | Variable | POWER code |
|---|---|---|
| Heat | Air temperature (2 m) | `T2M` |
| Heat | Daily maximum temperature | `T2M_MAX` |
| Heat | Land surface (skin) temperature | `TS` |
| Water | Precipitation | `PRECTOTCORR` |
| Water | Relative humidity (2 m) | `RH2M` |
| Land | Root-zone soil wetness | `GWETROOT` |
| Land | Surface albedo | `ALLSKY_SRF_ALB` |
| Air | Surface pressure | `PS` |
| Air | Wind speed (2 m) | `WS2M` |

---

## Method

1. **Deseasonalise** - subtract each calendar month's long-term mean, leaving the *anomaly* (difference from normal).
2. **Yearly averages** - average the anomalies for each complete year.
3. **Linear trend** - ordinary least squares on the yearly anomalies, with slope, 95% confidence interval and a t-test.
4. **Second check** - the non-parametric **Mann-Kendall** test and **Sen's slope**, which are robust to outliers and don't assume a straight line or normal errors. (Validated against the `pymannkendall` package.)
5. **Verdict** - both tests are combined into a confidence level and translated into plain language.

### Limits
- Linear trends only; the app does not forecast.
- Reanalysis is model-based, combining observations with a weather model, so it is not a raw station record.
- A 0.5° cell averages over roughly 50 km, so very local effects (a single city block, a valley) are smoothed out.
- Statistical significance shows *that* something changed, not *why*.

---

## Run locally

```bash
git clone <your-repo-url>
cd trend-detective
python3 -m pip install -r requirements.txt
python3 fetch_data.py          # one-time download into data/ (a few minutes)
python3 -m streamlit run app.py
```

Clicking a custom point on the globe fetches that location live from the POWER API, so an internet connection is needed.

## Deploy (Streamlit Community Cloud)

1. Push this folder to a **public** GitHub repo, **including `data/` and `.streamlit/`**.
2. Go to https://share.streamlit.io → **Create app** → choose the repo, branch `main`, main file `app.py` → **Deploy**.

## Project structure

```
trend-detective/
├── app.py              # Streamlit app: layout, globe, verdict, tabs
├── trends.py           # deseasonalising, OLS, Mann-Kendall, Sen's slope, plain-language verdicts
├── power.py            # NASA POWER API client (point and regional requests)
├── fetch_data.py       # one-time download of preset places and the regional grid
├── config.py           # places, topics, variable definitions, region-type hints
├── scenes.py           # dark theme and animated topic backgrounds
├── requirements.txt
├── .streamlit/config.toml
└── data/               # cached CSVs from fetch_data.py
```

## Future work
- More Earth-system variables: sea surface temperature, sea ice, snow cover, vegetation (NDVI), aerosols
- Change-point detection and non-linear trends
- Short-range projections for confirmed trends, with uncertainty
- Seasonal trends (e.g. "are summers warming faster than winters?")

## Use of AI
I chose the challenge and directed the design: globe-based place selection, the guided topic → place → variable flow, plain-language verdicts for non-experts, and topic-themed visuals. Claude (Anthropic), a large language model, was used as a coding and writing assistant. It suggested NASA POWER as a single consistent data source, which I adopted, and helped write and debug the code, implement the statistical tests (checked against the `pymannkendall` package), build the styling and animated backgrounds, and draft this documentation, which I reviewed. No AI-generated images, video or audio are used. All data and statistical results come from NASA POWER and the code in this repository.

## Acknowledgements
Data: NASA POWER Project, NASA Langley Research Center; MERRA-2, NASA GMAO.
Built for the 2026 NASA Space Apps Challenge.
