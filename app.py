"""Earth System Trend Detective - Streamlit app.  Run:  streamlit run app.py"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

from config import LOCATIONS, REGION_HINTS, THEMES, VARIABLES
from power import fetch_point
from scenes import TOPIC, page_css
import streamlit.components.v1 as components

# D3 globe (same as the preview): drag rotates smoothly, a single click investigates.
_globe = components.declare_component("globe", path=str(Path(__file__).parent / "globe_component"))
from trends import ALPHA, analyze, fmt_p, classify_region, grid_trends, metric_guide, plain_cards, scan_all, verdict

DATA = Path(__file__).parent / "data"
CUSTOM = "Custom coordinates…"

st.set_page_config(page_title="Trendy Earth - an Earth System Trend Detective", page_icon="🔎", layout="wide")


# ---------------------------------------------------------------- data access
@st.cache_data
def load_local():
    f = DATA / "power_monthly.csv"
    return pd.read_csv(f, parse_dates=["date"]) if f.exists() else None


@st.cache_data
def load_region():
    f = DATA / "region_T2M.csv"
    return pd.read_csv(f, parse_dates=["date"]) if f.exists() else None


@st.cache_data(show_spinner="Fetching 45 years of NASA data for this point…")
def fetch_live(lat, lon):
    return fetch_point(lat, lon)


@st.cache_data
def region_trends(grid):
    return grid_trends(grid)


def get_all(place, lat, lon):
    """Every variable for one place: saved file for presets, live NASA request otherwise."""
    local = load_local()
    if place != CUSTOM and local is not None:
        df = local[local.location == place]
        if not df.empty:
            return df
    return fetch_live(round(lat, 2), round(lon, 2))


def get_series(place, lat, lon, param):
    local = load_local()
    if place != CUSTOM and local is not None:
        df = local[(local.location == place) & (local.param == param)]
        if not df.empty:
            return df
    df = fetch_live(round(lat, 2), round(lon, 2))
    return df[df.param == param]


# ---------------------------------------------------------------- detective cases
CASES = {
    "Is Phoenix's afternoon heat getting worse?": ("Heat", "Phoenix, USA", "T2M_MAX"),
    "Is the Sahel recovering from its droughts?": ("Water", "Sahel (Niger)", "PRECTOTCORR"),
    "How fast is the Arctic warming?": ("Heat", "Arctic Alaska (Utqiagvik)", "T2M"),
}


def open_case(name):
    theme, place, var = CASES[name]
    st.session_state["theme"] = theme
    st.session_state["place"] = place
    st.session_state[f"var_{theme}"] = var


# ---------------------------------------------------------------- globe
# Plotly only reports clicks on data points, so the globe carries an invisible grid (about 5 degrees apart)
# of points (trace 0) that act as click targets, plus the preset places (trace 1).
# Fewer points near the poles keeps the spacing even and the globe light enough to drag smoothly.
_grid = [(lo, la) for la in np.arange(-80, 80.1, 5.0)
         for lo in np.linspace(-180, 180, max(8, int(round(72 * np.cos(np.radians(la))))), endpoint=False)]
GLON, GLAT = np.array([g[0] for g in _grid]).round(1), np.array([g[1] for g in _grid])
PLACE_NAMES = list(LOCATIONS)


def handle_globe_click():
    """Runs before the widgets are created, so it may set their session-state values."""
    click = st.session_state.get("globe3d")
    if not isinstance(click, dict) or click.get("n") == st.session_state.get("globe_last"):
        return
    st.session_state["globe_last"] = click.get("n")
    if click.get("place") in LOCATIONS:
        st.session_state["place"] = click["place"]
    else:
        st.session_state["place"] = CUSTOM
        st.session_state["custom_lat"] = float(click["lat"])
        st.session_state["custom_lon"] = float(click["lon"])


def make_globe(lat, lon, label):
    keep = dict(marker=dict(opacity=1))  # stop Plotly from fading unselected points after a click
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lon=GLON, lat=GLAT, mode="markers", marker=dict(size=6, color="rgba(0,0,0,0)"),
        hovertemplate="%{lat:.1f}°, %{lon:.1f}°<br>Click to investigate<extra></extra>",
        selected=keep, unselected=keep))
    fig.add_trace(go.Scattergeo(
        lon=[LOCATIONS[n]["lon"] for n in PLACE_NAMES], lat=[LOCATIONS[n]["lat"] for n in PLACE_NAMES],
        text=PLACE_NAMES, mode="markers",
        marker=dict(size=11, color="white", line=dict(width=2, color="#0d1b2a")),
        hovertemplate="%{text}<extra></extra>", selected=keep, unselected=keep))
    fig.add_trace(go.Scattergeo(
        lon=[lon], lat=[lat], text=[label], mode="markers+text", textposition="middle right",
        textfont=dict(size=13, color="#ffffff"),
        marker=dict(size=15, color="#ff4b4b", line=dict(width=2, color="white")),
        hoverinfo="skip", selected=keep, unselected=keep))
    fig.update_geos(
        projection_type="orthographic",
        projection_rotation=dict(lon=lon, lat=max(-55, min(55, lat))),
        resolution=50,  # detailed coastlines and borders
        showland=True, landcolor="#5fa57c", showocean=True, oceancolor="#1a4873",
        showlakes=True, lakecolor="#1a4873", showrivers=True, rivercolor="#2f6aa3", riverwidth=0.6,
        showcountries=True, countrycolor="rgba(255,255,255,0.45)", countrywidth=0.5,
        showcoastlines=True, coastlinecolor="#2c5a40", coastlinewidth=0.7,
        showframe=True, framecolor="#3a5f8f", framewidth=1,
        lataxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.14)", gridwidth=0.5, dtick=15),
        lonaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.14)", gridwidth=0.5, dtick=15),
        bgcolor="rgba(0,0,0,0)")
    fig.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      paper_bgcolor="rgba(0,0,0,0)", clickmode="event+select")
    return fig


handle_globe_click()
st.session_state.setdefault("custom_lat", 41.88)
st.session_state.setdefault("custom_lon", -87.63)

# ---------------------------------------------------------------- header + guided questions
brand, source = st.columns([1, 1])
brand.markdown("#### Trendy earth - an Earth System Trend Detective")
source.markdown(
    "<div style='text-align:right;color:#a9b8cb;font-size:0.9rem;padding-top:0.6rem'>"
    "NASA POWER · MERRA-2 reanalysis · 1981–2025</div>",
    unsafe_allow_html=True,
)
left, right = st.columns([1.05, 1], gap="large")
with left:
    st.title("Is it changing here, and is the change real?")
    st.markdown(
        "Pick **what** to investigate and **where**. The detective removes the seasons, fits a trend and "
        "tells you whether the change is real or could just be random year-to-year variation."
    )
    theme = st.radio("1 · What do you want to investigate?", list(THEMES), key="theme", horizontal=True)
    st.markdown(page_css(theme), unsafe_allow_html=True)  # dark page, topic glow and animated scene
    place = st.selectbox("2 · Where? Choose from the list or click the globe", list(LOCATIONS) + [CUSTOM], key="place")
    if place == CUSTOM:
        cc1, cc2 = st.columns(2)
        lat = cc1.number_input("Latitude", -89.0, 89.0, step=0.5, key="custom_lat")
        lon = cc2.number_input("Longitude", -180.0, 180.0, step=0.5, key="custom_lon")
        label = f"{lat:.1f}°, {lon:.1f}°"
    else:
        lat, lon = LOCATIONS[place]["lat"], LOCATIONS[place]["lon"]
        label = place.split(",")[0].split("(")[0].strip()
        st.caption(f"{LOCATIONS[place]['blurb']} · {lat:.2f}°, {lon:.2f}°")
    options = THEMES[theme]
    local_all = load_local()
    if place != CUSTOM and local_all is not None:  # hide variables the download could not get
        have = set(local_all.loc[local_all.location == place, "param"])
        options = [p for p in options if p in have] or options
    param = st.radio("3 · Which clue?", options, key=f"var_{theme}", horizontal=True,
                     format_func=lambda p: VARIABLES[p]["name"])
    var = VARIABLES[param]
    st.caption(f"**{var['question']}** {var['name']} ({var['unit']}): {var['definition']}")
    with st.expander("Or open a worked case"):
        for case in CASES:
            st.button(case, on_click=open_case, args=(case,), width="stretch")
with right:
    _globe(places=[{"name": n, "lat": LOCATIONS[n]["lat"], "lon": LOCATIONS[n]["lon"]} for n in PLACE_NAMES],
           selected={"lat": float(lat), "lon": float(lon), "label": label},
           accent=TOPIC[theme][1], height=500, key="globe3d", default=None)
    st.caption("Drag to rotate · click any point to investigate it · white markers are the preset places")


try:
    series = get_series(place, lat, lon, param)
except Exception as exc:
    st.error(f"Could not get data from NASA POWER for this point: {exc}")
    st.stop()
if series.empty:
    st.warning("No data for this choice.")
    st.stop()

if series.groupby("year").size().eq(12).sum() < 10:
    st.warning("Fewer than 10 complete years of data here, which is too short to test a trend.")
    st.stop()

result, monthly, annual = analyze(series)
level, headline, explanation = verdict(result, var)

# ---------------------------------------------------------------- verdict
box = {"strong": st.success, "some": st.warning, "none": st.info}[level]
icon = {"strong": "✅", "some": "⚠️", "none": "➖"}[level]
box(f"### {headline}\n{explanation}", icon=icon)

for i, (col, (question, answer, note, rating, colour)) in enumerate(zip(st.columns(4), plain_cards(result, var))):
    with col.container(border=True, key=f"card{i}"):
        st.markdown(f"**{question}**")
        st.markdown(f"#### {answer}")
        st.badge(rating, color=colour)
        st.caption(note)
with st.expander("What do these measures mean, and what counts as good?"):
    st.markdown(metric_guide(result, var))

# ---------------------------------------------------------------- charts
tab_trend, tab_scan, tab_raw, tab_compare, tab_map, tab_how = st.tabs(
    ["📈 Trend", "🧭 What else is changing here?", "🌀 Raw data & seasons", "🌍 Compare places",
     "🗺️ Regional map", "ℹ️ How it works"]
)

with tab_trend:
    x = annual["year"].to_numpy(float)
    y = annual["anomaly"].to_numpy(float)
    fit = result.intercept + result.slope_per_year * x
    n = len(x)
    s = np.sqrt(np.sum((y - fit) ** 2) / (n - 2))
    se_fit = s * np.sqrt(1 / n + (x - x.mean()) ** 2 / np.sum((x - x.mean()) ** 2))
    tcrit = stats.t.ppf(1 - ALPHA / 2, n - 2)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly["date"], y=monthly["anomaly"], mode="lines", name="Monthly anomaly",
                             line=dict(color="rgba(169,184,203,0.40)", width=1)))
    fig.add_trace(go.Scatter(x=pd.to_datetime(annual["year"].astype(str) + "-07-01"), y=y, mode="markers+lines",
                             name="Yearly average anomaly", line=dict(color="#5aa2f2", width=2)))
    xd = pd.to_datetime(annual["year"].astype(str) + "-07-01")
    fig.add_trace(go.Scatter(x=list(xd) + list(xd[::-1]), y=list(fit + tcrit * se_fit) + list((fit - tcrit * se_fit)[::-1]),
                             fill="toself", fillcolor="rgba(238,243,249,0.14)", line=dict(width=0),
                             name="95% confidence band", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xd, y=fit, mode="lines", name="Linear trend", line=dict(color="#ffffff", width=3)))
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.update_layout(height=430, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.1),
                      yaxis_title=f"Difference from normal ({var['unit']})", hovermode="x unified")
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "**How to read this.** Each blue dot is one year. Dots above the dotted zero line were higher than "
        "normal for this place, dots below were lower. The thick line is the overall direction: if it "
        "slopes up, the variable is rising. The shaded band shows how sure we are about that line. "
        "The faint grey line is the same thing month by month. (Scientists call 'difference from normal' "
        "an *anomaly*.)"
    )

with tab_scan:
    try:
        everything = get_all(place, lat, lon)
    except Exception as exc:
        everything = None
        st.error(f"Could not get the other variables for this point: {exc}")
    if everything is not None:
        kind = LOCATIONS[place]["kind"] if place != CUSTOM else classify_region(everything)
        kind_name, suggested, why = REGION_HINTS[kind]
        names = ", ".join(VARIABLES[c]["name"].lower() for c in suggested)
        st.markdown(f"**This looks like {kind_name}.** {why}  \n**Clues worth checking first:** {names}.")
        scan = scan_all(everything, VARIABLES)
        confirmed = scan[scan["Confidence"] == "High"]
        if confirmed.empty:
            st.info("The detective tested every clue for this place and none shows a confirmed trend yet.")
        else:
            top = "; ".join(f"{r['Clue'].lower()} ({r['Direction'].lower()})" for _, r in confirmed.head(3).iterrows())
            st.success(f"The detective tested every clue for this place. Strongest signals: {top}.")
        scan.insert(1, "Suggested for this kind of place", scan["_code"].isin(suggested).map({True: "Yes", False: ""}))
        st.dataframe(scan.drop(columns=["_p", "_code"]), hide_index=True, width="stretch")
        st.caption("**How to read this.** Every variable was run through the same two tests and sorted with the "
                   "most certain trends at the top. 'Suggested' marks the clues that the type of region makes "
                   "worth checking first. The suggestions come from simple rules about region types, not from a "
                   "trained model.")

with tab_raw:
    st.markdown(
        "Raw values swing with the seasons every year. That regular cycle can hide a slow long-term "
        "change, so the detective subtracts each calendar month's long-term average first."
    )
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=monthly["date"], y=monthly["value"], mode="lines", name="Monthly value",
                              line=dict(color="#5aa2f2", width=1)))
    fig2.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=10, b=10), yaxis_title=var["unit"])
    st.plotly_chart(fig2, width="stretch")
    clim = monthly.groupby("month")["value"].mean()
    fig3 = go.Figure(go.Bar(x=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                            y=clim.values, marker_color="#5aa2f2"))
    fig3.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=30, b=10), title="The seasonal cycle that gets removed",
                       yaxis_title=var["unit"])
    st.plotly_chart(fig3, width="stretch")
    out = monthly[["year", "month", "value", "climatology", "anomaly"]].assign(
        variable=param, latitude=lat, longitude=lon)
    st.download_button("⬇️ Download this data (CSV)", out.to_csv(index=False),
                       file_name=f"trend_detective_{param}_{lat:.2f}_{lon:.2f}.csv", mime="text/csv")

with tab_compare:
    local = load_local()
    if local is None:
        st.info("Run `python fetch_data.py` to enable place comparisons.")
    else:
        rows = []
        for loc in LOCATIONS:
            d = local[(local.location == loc) & (local.param == param)]
            if d.empty:
                continue
            r, _, _ = analyze(d)
            rows.append({"Place": loc, "Trend per decade": r.slope_per_decade,
                         "Significant": "Significant" if r.significant else "Not significant",
                         "t-test p": round(r.p_ttest, 4), "Mann-Kendall p": round(r.p_mk, 4)})
        comp = pd.DataFrame(rows).sort_values("Trend per decade")
        colors = np.where(comp["Significant"] == "Significant",
                          np.where(comp["Trend per decade"] > 0, "#f07171", "#5aa2f2"), "#5d6a7d")
        fig4 = go.Figure(go.Bar(x=comp["Trend per decade"], y=comp["Place"], orientation="h", marker_color=colors,
                                text=[f"{v:+.3g}" for v in comp["Trend per decade"]], textposition="outside"))
        fig4.add_vline(x=0, line_color="white")
        fig4.update_layout(height=70 + 34 * len(comp), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=40, t=30, b=10),
                           title=f"{var['name']}: trend per decade ({var['unit']})")
        st.plotly_chart(fig4, width="stretch")
        st.caption("**How to read this.** Each bar is one place. Bars to the right mean rising, to the left "
                   "falling; longer means faster. Coloured bars are trends we are confident in; grey bars could "
                   "be chance. The same variable can move in opposite directions in different places.")
        st.dataframe(comp, hide_index=True, width="stretch")

with tab_map:
    grid = load_region()
    if grid is None:
        st.info("Run `python fetch_data.py` to download the regional temperature grid.")
    else:
        gt = region_trends(grid)
        region_name = grid["region"].iloc[0] if "region" in grid else "Region"
        lim = float(np.abs(gt["slope_per_decade"]).max())
        fig5 = go.Figure()
        for sig, symbol, label in [(True, "square", "Significant"), (False, "square-open", "Not significant")]:
            d = gt[gt.significant == sig]
            fig5.add_trace(go.Scattergeo(
                lat=d.lat, lon=d.lon, mode="markers", name=label,
                marker=dict(symbol=symbol, size=11, color=d.slope_per_decade, colorscale="RdBu_r",
                            cmin=-lim, cmax=lim, colorbar=dict(title="°C/decade") if sig else None,
                            line=dict(width=1)),
                text=[f"{v:+.2f} °C/decade, t-test {fmt_p(p)}" for v, p in zip(d.slope_per_decade, d.p_ttest)],
                hoverinfo="text"))
        fig5.update_geos(fitbounds="locations", showcountries=True, showsubunits=True, resolution=50)
        fig5.update_layout(height=520, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=0),
                           title=f"Air temperature trend per grid cell, {region_name}, 1981–2025")
        st.plotly_chart(fig5, width="stretch")
        share = gt.significant.mean() * 100
        st.caption(f"**How to read this.** Each square covers an area about 50 km across. Redder means warming "
                   f"faster, bluer means cooling. Filled squares are trends we are confident in ({share:.0f}% of "
                   "them); hollow squares could be chance. Even within one region, warming is uneven.")

with tab_how:
    st.markdown(f"""
**Data.** Monthly values from NASA's POWER service, which serves the MERRA-2 reanalysis produced by NASA's
Global Modeling and Assimilation Office. MERRA-2 combines satellite and ground observations with a global
weather model, giving a consistent record since 1981 on a ~0.5° grid.

**Step 1 – Remove the seasons.** For each calendar month, subtract its average over the whole record.
What is left is the *anomaly*: how unusual that month was.

**Step 2 – Yearly averages.** Monthly anomalies are averaged per year (only complete years). Neighbouring
months are correlated, and testing on yearly values keeps the significance tests honest.

**Step 3 – Fit a straight line.** Ordinary least squares gives the rate of change; its standard error gives
a 95% confidence interval and a two-sided **t-test** of whether the slope differs from zero.

**Step 4 – Cross-check with Mann-Kendall.** A non-parametric test that only asks whether later years tend to
be higher (or lower) than earlier ones. It does not assume a straight line or normal errors and is robust
to outliers. **Sen's slope** (median of all pairwise slopes) is its rate estimate: here
{result.sen_per_decade:+.3g} {var['unit']} per decade vs. {result.slope_per_decade:+.3g} from least squares.

**Verdict.** *Significant* when both tests give p < {ALPHA}. When neither does, the detective estimates how
many years of data would be needed if the trend and noise stayed the same.

**Limits.** Linear trends only; reanalysis is a model-based estimate, not a direct measurement; a ~0.5° cell
averages over about 50 km, so local effects (a city's heat island, irrigation) may be smoothed out; a
significant trend says *that* something changed, not *why*.
""")

st.divider()
st.caption(
    "Data: NASA POWER, monthly MERRA-2 reanalysis (NASA GMAO), 1981–2025, ~0.5° grid. "
    "Built for the 2026 NASA Space Apps Challenge."
)
