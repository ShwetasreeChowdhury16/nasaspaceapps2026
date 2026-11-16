"""Shared settings: demo locations, variables and plain-language definitions."""

START_YEAR = 1981
END_YEAR = 2025  # POWER monthly data runs to the previous full year

LOCATIONS = {
    "Chicago, USA": {"kind": "city", "lat": 41.88, "lon": -87.63, "blurb": "Large Midwestern city on Lake Michigan"},
    "Phoenix, USA": {"kind": "desert", "lat": 33.45, "lon": -112.07, "blurb": "Fast-growing city in the Sonoran Desert"},
    "Central Amazon, Brazil": {"kind": "rainforest", "lat": -3.47, "lon": -62.37, "blurb": "Tropical rainforest near Manaus"},
    "Sahel (Niger)": {"kind": "semi-arid", "lat": 14.0, "lon": 2.0, "blurb": "Semi-arid belt south of the Sahara"},
    "Arctic Alaska (Utqiagvik)": {"kind": "polar", "lat": 71.29, "lon": -156.79, "blurb": "Northernmost US town, on the Arctic Ocean"},
    "Delhi, India": {"kind": "city", "lat": 28.61, "lon": 77.21, "blurb": "Megacity on the Indo-Gangetic Plain"},
    "London, UK": {"kind": "city", "lat": 51.51, "lon": -0.13, "blurb": "Temperate maritime city in north-west Europe"},
    "Tokyo, Japan": {"kind": "city", "lat": 35.68, "lon": 139.69, "blurb": "Humid subtropical megacity on the Pacific coast"},
    "Sydney, Australia": {"kind": "city", "lat": -33.87, "lon": 151.21, "blurb": "Coastal city in south-east Australia"},
    "Cape Town, South Africa": {"kind": "city", "lat": -33.92, "lon": 18.42, "blurb": "Mediterranean-climate city at Africa's southern tip"},
    "São Paulo, Brazil": {"kind": "city", "lat": -23.55, "lon": -46.63, "blurb": "Largest city in the Southern Hemisphere"},
    "Tibetan Plateau (Nagqu)": {"kind": "mountain", "lat": 31.48, "lon": 92.06, "blurb": "High-altitude plateau, about 4,500 m"},
}

# theme -> list of variable codes
THEMES = {
    "Heat": ["T2M", "T2M_MAX", "TS"],
    "Water": ["PRECTOTCORR", "RH2M"],
    "Land": ["GWETROOT", "ALLSKY_SRF_ALB"],
    "Air": ["PS", "WS2M"],
}

VARIABLES = {
    "T2M": {
        "name": "Air temperature",
        "unit": "°C",
        "question": "Is it getting hotter?",
        "definition": (
            "The average temperature of the air 2 meters above the ground, roughly where people "
            "breathe. A rise here is the most direct sign of local warming."
        ),
        "relative": False,
    },
    "T2M_MAX": {
        "name": "Daily maximum temperature",
        "unit": "°C",
        "question": "Are the hottest part of the days getting hotter?",
        "definition": (
            "The highest air temperature reached each day, averaged over the month. It tracks "
            "afternoon heat, which matters for heat stress on people, crops and power grids."
        ),
        "relative": False,
    },
    "PRECTOTCORR": {
        "name": "Precipitation",
        "unit": "mm/day",
        "question": "Is it getting wetter or drier?",
        "definition": (
            "Rain and snow (as liquid water) falling on the ground, averaged per day. Rainfall is "
            "noisy from year to year, so trends here usually need many years to become significant."
        ),
        "relative": True,
    },
    "RH2M": {
        "name": "Relative humidity",
        "unit": "%",
        "question": "Is the air getting more or less humid?",
        "definition": (
            "How close the air is to being saturated with water vapor, from 0% (bone dry) to 100% "
            "(saturated). Warmer air can hold more water, so humidity can fall even as temperature rises."
        ),
        "relative": False,
    },
    "GWETROOT": {
        "name": "Root-zone soil wetness",
        "unit": "fraction (0–1)",
        "question": "Is the soil drying out?",
        "definition": (
            "How wet the soil is in the top meter, where plant roots live: 0 means completely dry, "
            "1 means fully saturated. It links rainfall, evaporation and plant health."
        ),
        "relative": True,
    },
    "TS": {
        "name": "Land surface temperature",
        "unit": "°C",
        "question": "Is the ground itself getting hotter?",
        "definition": (
            "The temperature of the Earth's surface itself (soil, rock, water or ice), also called skin "
            "temperature. It can differ from air temperature, especially over deserts, cities and snow."
        ),
        "relative": False,
    },
    "ALLSKY_SRF_ALB": {
        "name": "Surface albedo",
        "unit": "fraction (0–1)",
        "question": "Is the surface reflecting more or less sunlight?",
        "definition": (
            "The share of incoming sunlight the surface reflects: fresh snow is about 0.8, forest about "
            "0.15. Albedo falls when snow and ice retreat or vegetation spreads, and darker surfaces "
            "absorb more heat. This record comes from satellite measurements and starts later than 1981."
        ),
        "relative": True,
    },
    "PS": {
        "name": "Surface pressure",
        "unit": "kPa",
        "question": "Is the weight of the air above changing?",
        "definition": (
            "The pressure of the atmosphere at ground level, what a barometer measures. Long-term shifts "
            "point to changes in where high- and low-pressure weather systems tend to sit."
        ),
        "relative": False,
    },
    "WS2M": {
        "name": "Wind speed",
        "unit": "m/s",
        "question": "Is it getting windier or calmer?",
        "definition": (
            "The average speed of the wind 2 meters above the ground. Wind drives evaporation, moves dust "
            "and weather systems, and matters for wind power."
        ),
        "relative": True,
    },
}

PARAMS = list(VARIABLES.keys())


# What kind of place is this, and which variables are most likely to show change there?
# Rule-based suggestions from the region's characteristics (not a trained model).
REGION_HINTS = {
    "city": ("a large city", ["TS", "T2M_MAX", "RH2M"],
             "Concrete and asphalt store heat, so cities often warm faster than their surroundings. "
             "A grid cell here averages about 50 km, so the city's own effect is diluted."),
    "desert": ("a desert", ["T2M_MAX", "GWETROOT", "PRECTOTCORR"],
               "Dry air and bare ground heat up fast, so afternoon heat is the first thing to check, "
               "followed by what little soil moisture and rain there is."),
    "rainforest": ("a tropical rainforest", ["PRECTOTCORR", "RH2M", "GWETROOT"],
                   "Rainforests make much of their own rain. Drying air, falling rainfall or drier soil "
                   "can be early signs of stress from deforestation or a longer dry season."),
    "semi-arid": ("a semi-arid region", ["PRECTOTCORR", "GWETROOT", "WS2M"],
                  "Life here depends on a short rainy season, so rainfall and soil moisture swing between "
                  "drought and recovery. Wind matters too, because it lifts dust."),
    "polar": ("a polar region", ["T2M", "ALLSKY_SRF_ALB", "TS"],
              "The Arctic warms faster than the rest of the planet. As snow and ice retreat, the surface "
              "gets darker (albedo falls) and absorbs more heat, which speeds up the warming."),
    "mountain": ("a high mountain region", ["T2M", "ALLSKY_SRF_ALB", "PRECTOTCORR"],
                 "High ground stores water as snow and ice. Warming and a darker, less snowy surface "
                 "change when and how much water flows downstream."),
    "temperate": ("a temperate region", ["T2M", "PRECTOTCORR", "GWETROOT"],
                  "Seasons are strong here, so slow changes hide behind them. Temperature is usually the "
                  "clearest signal, with rainfall and soil moisture much noisier."),
}
