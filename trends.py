"""Statistics engine: remove the seasonal cycle, fit a linear trend, test its significance.

Method (kept deliberately simple, as the challenge asks for linear trends):
1. Seasonal cycle removal: each month's value minus that calendar month's long-term mean
   gives a monthly *anomaly*.
2. Monthly anomalies are averaged into annual anomalies. Testing on annual values avoids most
   of the month-to-month autocorrelation that would otherwise overstate significance.
3. Two independent tests on the annual series:
   - Ordinary least squares slope with a two-sided t-test and 95% confidence interval.
   - Mann-Kendall test (non-parametric, robust to outliers) with Sen's slope.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

ALPHA = 0.05


def deseasonalize(df: pd.DataFrame) -> pd.DataFrame:
    """df has columns year, month, value. Adds climatology and anomaly columns."""
    out = df.copy()
    out["climatology"] = out.groupby("month")["value"].transform("mean")
    out["anomaly"] = out["value"] - out["climatology"]
    return out


def annual_series(df: pd.DataFrame) -> pd.DataFrame:
    """Annual mean anomaly and value, keeping only years with all 12 months."""
    g = df.groupby("year").agg(anomaly=("anomaly", "mean"), value=("value", "mean"), n=("value", "size"))
    return g[g["n"] == 12].drop(columns="n").reset_index()


def mann_kendall(y: np.ndarray):
    """Mann-Kendall trend test with tie correction. Returns (z, p, sen_slope_per_step)."""
    y = np.asarray(y, dtype=float)
    n = len(y)
    i, j = np.triu_indices(n, k=1)
    diffs = y[j] - y[i]
    s = np.sign(diffs).sum()
    _, counts = np.unique(y, return_counts=True)
    ties = counts[counts > 1]
    var_s = (n * (n - 1) * (2 * n + 5) - (ties * (ties - 1) * (2 * ties + 5)).sum()) / 18
    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0.0
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    sen = np.median(diffs / (j - i))
    return float(z), float(p), float(sen)


def years_needed(slope: float, resid_sd: float, max_years: int = 300):
    """Rough estimate: how many years of data would make this slope significant (p < 0.05),
    if the trend and the year-to-year noise stay the same. Uses Var(b) = 12 s^2 / (n (n^2 - 1))."""
    if slope == 0 or resid_sd == 0:
        return None
    for n in range(5, max_years + 1):
        se = resid_sd * np.sqrt(12 / (n * (n**2 - 1)))
        if abs(slope) / se >= stats.t.ppf(1 - ALPHA / 2, n - 2):
            return n
    return None


@dataclass
class TrendResult:
    n_years: int
    first_year: int
    last_year: int
    mean_value: float
    slope_per_decade: float
    ci_low_per_decade: float
    ci_high_per_decade: float
    p_ttest: float
    sen_per_decade: float
    p_mk: float
    intercept: float
    slope_per_year: float
    years_for_significance: int | None

    @property
    def significant(self) -> bool:
        return self.p_ttest < ALPHA and self.p_mk < ALPHA

    @property
    def partly_significant(self) -> bool:
        return (self.p_ttest < ALPHA) != (self.p_mk < ALPHA)

    @property
    def direction(self) -> str:
        return "rising" if self.slope_per_decade > 0 else "falling"


def analyze(monthly: pd.DataFrame) -> tuple[TrendResult, pd.DataFrame, pd.DataFrame]:
    """monthly: rows for ONE variable at ONE place, columns year, month, value (and date).
    Returns (result, monthly_with_anomalies, annual)."""
    m = deseasonalize(monthly.sort_values(["year", "month"]))
    a = annual_series(m)
    x, y = a["year"].to_numpy(float), a["anomaly"].to_numpy(float)
    n = len(a)
    lr = stats.linregress(x, y)
    tcrit = stats.t.ppf(1 - ALPHA / 2, n - 2)
    resid_sd = float(np.std(y - (lr.intercept + lr.slope * x), ddof=2))
    _, p_mk, sen = mann_kendall(y)
    result = TrendResult(
        n_years=n,
        first_year=int(x.min()),
        last_year=int(x.max()),
        mean_value=float(m["value"].mean()),
        slope_per_decade=lr.slope * 10,
        ci_low_per_decade=(lr.slope - tcrit * lr.stderr) * 10,
        ci_high_per_decade=(lr.slope + tcrit * lr.stderr) * 10,
        p_ttest=float(lr.pvalue),
        sen_per_decade=sen * 10,
        p_mk=p_mk,
        intercept=float(lr.intercept),
        slope_per_year=float(lr.slope),
        years_for_significance=years_needed(lr.slope, resid_sd),
    )
    return result, m, a


def fmt_p(p: float) -> str:
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def odds(p: float) -> str:
    """Turn a p-value into everyday odds."""
    if p < 0.001:
        return "less than 1 in 1,000"
    if p > 0.33:
        return "more than 1 in 3"
    n = 1 / p
    if n >= 1000:
        n = round(n, -2)
    elif n >= 100:
        n = round(n, -1)
    return f"about 1 in {int(round(n)):,}"


def verdict(r: TrendResult, var: dict) -> tuple[str, str, str]:
    """Plain-language verdict. Returns (level, headline, explanation); level is
    'strong', 'some' or 'none'. Technical test results go at the end, in brackets."""
    unit = var["unit"]
    rate = f"{abs(r.slope_per_decade):.3g} {unit} every 10 years"
    if var.get("relative") and r.mean_value:
        pct = abs(r.slope_per_decade) / abs(r.mean_value) * 100
        rate += f" (about {pct:.1f}% of its usual level)"
    total = abs(r.slope_per_decade) * (r.last_year - r.first_year) / 10
    span = f"{r.first_year}–{r.last_year}"
    name = var["name"].lower()
    tech = f"(Technical: t-test {fmt_p(r.p_ttest)}, Mann-Kendall {fmt_p(r.p_mk)}.)"

    if r.significant:
        return (
            "strong",
            f"Yes, {name} here is {r.direction}: about {rate}.",
            f"**Confidence: high.** Over {span} that adds up to roughly {total:.3g} {unit}. The change is "
            f"steady enough that it is very unlikely to be a coincidence: the chance of seeing a trend "
            f"this strong from random year-to-year ups and downs alone is {odds(r.p_ttest)}, and a second, "
            f"independent check agrees. {tech}",
        )
    if r.partly_significant:
        return (
            "some",
            f"Probably: {name} here looks like it is {r.direction}, about {rate}.",
            f"**Confidence: medium.** One of our two checks says this is a real trend and the other is "
            f"not convinced, so treat it as likely but not yet confirmed. A few more years of data "
            f"should settle it. {tech}",
        )
    more = ""
    if r.years_for_significance and r.years_for_significance > r.n_years:
        more = (
            f" If things continue the same way, it would take about "
            f"{r.years_for_significance - r.n_years} more years of data before we could be sure."
        )
    return (
        "none",
        f"Not clear yet: {name} here shows no reliable trend.",
        f"**Confidence: low.** The numbers lean slightly {r.direction} ({rate}), but the swings from one "
        f"year to the next are much bigger than that lean, so it could easily be chance "
        f"({odds(r.p_ttest)}).{more} {tech}",
    )


def p_rating(p: float) -> tuple[str, str]:
    """How strong is the evidence for a trend? Returns (label, colour)."""
    if p < 0.01:
        return "Very strong evidence", "green"
    if p < ALPHA:
        return "Strong evidence", "green"
    if p < 0.10:
        return "Weak hint only", "orange"
    return "No real evidence", "gray"


def plain_cards(r: TrendResult, var: dict) -> list[tuple[str, str, str, str, str]]:
    """Four everyday questions: (question, answer, explanation, rating label, rating colour)."""
    unit = var["unit"]
    lo, hi = r.ci_low_per_decade, r.ci_high_per_decade
    crosses = lo < 0 < hi
    zero = (
        "This range includes zero, so no change at all is still possible."
        if crosses
        else "The whole range is on one side of zero, so the direction is clear."
    )
    mk_yes = r.p_mk < ALPHA
    return [
        (
            "How fast is it changing?",
            f"{r.slope_per_decade:+.3g} {unit}",
            "Average change every 10 years, from the straight line that best fits the yearly values. "
            "Plus means rising, minus means falling. (Technical name: trend slope.)",
            "Rising" if r.slope_per_decade > 0 else "Falling", "blue",
        ),
        (
            "How sure are we about that speed?",
            f"{lo:+.3g} to {hi:+.3g}",
            f"We are 95% sure the true rate is somewhere in this range. {zero} "
            "(Technical name: 95% confidence interval.)",
            *(("Direction uncertain", "orange") if crosses else ("Direction clear", "green")),
        ),
        (
            "Could it just be a fluke?",
            odds(r.p_ttest).capitalize(),
            "The chance that random year-to-year ups and downs alone would produce a trend this strong. "
            f"Scientists call a trend real when this is below 1 in 20. (Technical: t-test, {fmt_p(r.p_ttest)}.)",
            *p_rating(r.p_ttest),
        ),
        (
            "Does a second check agree?",
            "Yes, real trend" if mk_yes else "No clear trend",
            "A simpler test that only asks whether later years tend to be higher or lower than earlier "
            f"ones, so one freak year cannot fool it. (Technical: Mann-Kendall test, {fmt_p(r.p_mk)}.)",
            *p_rating(r.p_mk),
        ),
    ]


def metric_guide(r: TrendResult, var: dict) -> str:
    """Markdown notes: what each measure is, how to judge it, and how this result rates."""
    unit = var["unit"]
    crosses = r.ci_low_per_decade < 0 < r.ci_high_per_decade
    gap = abs(r.sen_per_decade - r.slope_per_decade)
    close = gap <= 0.25 * max(abs(r.slope_per_decade), abs(r.sen_per_decade), 1e-12)
    return f"""
**"Good" here means strong evidence, not good news.** These measures tell you how much to trust the
trend. A strongly confirmed warming trend is solid science, whether or not the change itself is welcome.

| Measure | What it tells you | How to judge it | This result |
|---|---|---|---|
| **Trend slope** | How fast the variable changes per decade, from the best-fitting straight line. | Neither good nor bad on its own. Its size only means something together with the three checks below. | {r.slope_per_decade:+.3g} {unit} per decade |
| **95% confidence interval** | The range the true rate very likely falls in. | **Good:** narrow, and entirely above zero or entirely below it. **Weak:** it crosses zero, so the direction itself is in doubt. | {r.ci_low_per_decade:+.3g} to {r.ci_high_per_decade:+.3g} → **{"direction uncertain" if crosses else "direction clear"}** |
| **t-test p-value** | The probability that chance alone would give a slope this large if nothing were really changing. It assumes a straight-line trend with bell-shaped year-to-year noise. | **Smaller is stronger.** Below 0.01: very strong. 0.01 to 0.05: strong (0.05 is the usual pass mark). 0.05 to 0.10: a weak hint. Above 0.10: no real evidence. | {fmt_p(r.p_ttest)} → **{p_rating(r.p_ttest)[0].lower()}** |
| **Mann-Kendall p-value** | The same question answered a different way: it compares every year with every later year and counts how often the later one is higher. It makes no assumption about a straight line or bell-shaped noise, so one extreme year cannot fool it. | Same scale as the t-test: **smaller is stronger**, below 0.05 passes. It matters most when it disagrees with the t-test, which usually means a few unusual years are driving the result. | {fmt_p(r.p_mk)} → **{p_rating(r.p_mk)[0].lower()}** |
| **Sen's slope** | The Mann-Kendall method's own estimate of the rate: the middle value of the slopes between all pairs of years. | **Good:** close to the trend slope, so both methods tell the same story. **Caution:** a big gap means outliers are pulling the straight line. | {r.sen_per_decade:+.3g} {unit} per decade → **{"agrees with the trend slope" if close else ("both estimates are small and uncertain" if not (r.significant or r.partly_significant) else "differs noticeably from the trend slope")}** |

**The rule this app uses:** a trend is called confirmed only when **both** p-values are below 0.05. If only
one passes, it is reported as "probably". If neither passes, it is reported as "not clear yet".

**What a p-value is not.** It is not the chance that the trend is wrong, and a small p-value does not mean a
big change. A tiny change can be very certain, and a large change can be uncertain if the data are noisy.
"""


def grid_trends(grid: pd.DataFrame) -> pd.DataFrame:
    """Trend per grid cell for a regional table with lat, lon, year, month, value."""
    rows = []
    for (lat, lon), cell in grid.groupby(["lat", "lon"]):
        r, _, _ = analyze(cell)
        rows.append(
            {
                "lat": lat,
                "lon": lon,
                "slope_per_decade": r.slope_per_decade,
                "p_ttest": r.p_ttest,
                "p_mk": r.p_mk,
                "significant": r.significant,
            }
        )
    return pd.DataFrame(rows)


def classify_region(all_monthly: pd.DataFrame) -> str:
    """Rough climate type for a custom point, from its own long-term averages."""
    means = all_monthly.groupby("param")["value"].mean()
    t, p = means.get("T2M"), means.get("PRECTOTCORR")
    if t is None or p is None:
        return "temperate"
    if t < 0:
        return "polar"
    if p < 0.7:
        return "desert"
    if p < 1.5:
        return "semi-arid"
    if t > 22 and p > 4:
        return "rainforest"
    return "temperate"


def scan_all(all_monthly: pd.DataFrame, variables: dict) -> pd.DataFrame:
    """Test every available variable at one place and rank them by strength of evidence."""
    rows = []
    for code, var in variables.items():
        d = all_monthly[all_monthly["param"] == code]
        if d.empty or d.groupby("year").size().eq(12).sum() < 10:
            continue
        r, _, _ = analyze(d)
        level = "High" if r.significant else "Medium" if r.partly_significant else "Low"
        rows.append({
            "Clue": var["name"],
            "Direction": ("Rising" if r.slope_per_decade > 0 else "Falling") if level != "Low" else "No clear trend",
            "Change every 10 years": f"{r.slope_per_decade:+.3g} {var['unit']}",
            "Confidence": level,
            "Chance it is a fluke": odds(max(r.p_ttest, r.p_mk)),
            "_p": max(r.p_ttest, r.p_mk),
            "_code": code,
        })
    return pd.DataFrame(rows).sort_values("_p").reset_index(drop=True)
