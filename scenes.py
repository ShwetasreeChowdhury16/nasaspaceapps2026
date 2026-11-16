"""Dark page styling and a faint animated scene per topic: sun (Heat), waves (Water),
hills and clouds (Land), wind (Air). Each scene is an animated SVG used as a CSS background,
so it always sits behind the content."""

from urllib.parse import quote

BG = "#04060b"      # page
CARD = "#0e1a30"    # dark-blue panels
LINE = "#22355a"

# topic -> (glow colour at the top of the page, accent)
TOPIC = {
    "Heat": ("#5c3a05", "#f0b24f"),
    "Water": ("#0a3a78", "#62b4ee"),
    "Land": ("#124a20", "#7fd08a"),
    "Air": ("#30277a", "#b0a5f5"),
}

_NS = 'xmlns="http://www.w3.org/2000/svg"'

SUN = f"""<svg {_NS} viewBox="0 0 600 600"><style>.r{{transform-origin:300px 300px;animation:s 80s linear infinite}}
.g{{transform-origin:300px 300px;animation:p 5s ease-in-out infinite}}@keyframes s{{to{{transform:rotate(360deg)}}}}
@keyframes p{{50%{{transform:scale(1.08);opacity:.7}}}}</style>
<defs><radialGradient id="a"><stop offset="0" stop-color="#ffe9a8"/><stop offset=".55" stop-color="#ffcf63"/><stop offset="1" stop-color="#f5a623"/></radialGradient>
<radialGradient id="b"><stop offset=".45" stop-color="#ffc24d" stop-opacity=".5"/><stop offset="1" stop-color="#ffc24d" stop-opacity="0"/></radialGradient></defs>
<g opacity=".3"><circle class="g" cx="300" cy="300" r="290" fill="url(#b)"/>
<g class="r" stroke="#f2a52b" stroke-width="7" stroke-linecap="round">
<line x1="300" y1="92" x2="300" y2="36"/><line x1="300" y1="508" x2="300" y2="564"/><line x1="92" y1="300" x2="36" y2="300"/><line x1="508" y1="300" x2="564" y2="300"/>
<line x1="153" y1="153" x2="113" y2="113"/><line x1="447" y1="447" x2="487" y2="487"/><line x1="153" y1="447" x2="113" y2="487"/><line x1="447" y1="153" x2="487" y2="113"/></g>
<circle cx="300" cy="300" r="170" fill="url(#a)"/></g></svg>"""

_WAVE = "Q150 {a} 300 {y}T600 {y}T900 {y}T1200 {y}T1500 {y}T1800 {y}T2100 {y}T2400 {y}V150H0Z"
WAVES = f"""<svg {_NS} viewBox="0 0 1200 150" preserveAspectRatio="none"><style>
path{{animation:d 18s linear infinite}}.b{{animation-duration:27s;animation-direction:reverse}}.c{{animation-duration:40s}}
@keyframes d{{to{{transform:translateX(-1200px)}}}}</style><g opacity=".3">
<path class="c" fill="#8ec1ee" opacity=".5" d="M0 50{_WAVE.format(a=5, y=50)}"/>
<path class="b" fill="#5fa6e3" opacity=".5" d="M0 75{_WAVE.format(a=115, y=75)}"/>
<path fill="#2f86d1" opacity=".6" d="M0 100{_WAVE.format(a=65, y=100)}"/></g></svg>"""

HILLS = f"""<svg {_NS} viewBox="0 0 1200 230" preserveAspectRatio="none"><g opacity=".3">
<path fill="#9cc98f" opacity=".55" d="M0 120Q200 30 420 100T820 70T1200 95V230H0Z"/>
<path fill="#6fae63" opacity=".6" d="M0 170Q260 90 520 150T1000 125T1200 150V230H0Z"/>
<path fill="#4f9347" opacity=".55" d="M0 205Q300 160 600 195T1200 185V230H0Z"/></g></svg>"""

_CLOUD = "M40 70a30 30 0 0 1 6-59 42 42 0 0 1 80-4 34 34 0 0 1 58 22 22 22 0 0 1-4 41Z"
CLOUDS = f"""<svg {_NS} viewBox="0 0 1600 260"><style>path{{animation:c 70s linear infinite}}
.b{{animation-duration:95s;animation-delay:-40s}}@keyframes c{{from{{transform:translate(-260px,0)}}to{{transform:translate(1640px,0)}}}}</style>
<g fill="#fff" opacity=".22"><path d="{_CLOUD}" style="translate:0 40px"/><path class="b" d="{_CLOUD}" style="translate:0 140px;scale:.7"/></g></svg>"""

WIND = f"""<svg {_NS} viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice"><style>
path{{fill:none;stroke:#b0a5f5;stroke-width:3;stroke-linecap:round;stroke-dasharray:240 1400;animation:g 7s linear infinite}}
path:nth-child(2){{animation-duration:9s;animation-delay:-3s}}path:nth-child(3){{animation-duration:11s;animation-delay:-6s}}
path:nth-child(4){{animation-duration:8s;animation-delay:-1.5s}}path:nth-child(5){{animation-duration:13s;animation-delay:-8s}}
@keyframes g{{from{{stroke-dashoffset:1640}}to{{stroke-dashoffset:0}}}}</style><g opacity=".3">
<path d="M-50 120C200 80 380 160 560 120S860 60 980 110c60 26 40 80-10 70-40-8-30-52 6-46"/>
<path d="M-50 260C240 300 420 220 640 260S1000 300 1250 250"/>
<path d="M-50 420C180 380 330 450 520 410s250-70 330-20c46 30 20 78-22 66-34-10-24-48 8-42"/>
<path d="M-50 560C260 600 520 520 760 560S1100 600 1250 560"/>
<path d="M-50 690C220 650 400 720 620 690S980 640 1250 700"/></g></svg>"""


def _uri(svg: str) -> str:
    return 'url("data:image/svg+xml,' + quote(" ".join(svg.split())) + '")'


# topic -> list of (image, position, size)
_LAYERS = {
    "Heat": [(SUN, "right -300px top -300px", "600px 600px")],
    "Water": [(WAVES, "left bottom", "100% 170px")],
    "Land": [(HILLS, "left bottom", "100% 220px"), (CLOUDS, "left top 60px", "100% auto")],
    "Air": [(WIND, "center", "cover")],
}


def page_css(theme: str) -> str:
    """<style> block for the whole page, for the chosen topic."""
    glow, accent = TOPIC[theme]
    layers = _LAYERS[theme]
    images = ",".join([_uri(s) for s, _, _ in layers] + [f"linear-gradient(180deg,{glow} 0,{BG} 640px)"])
    positions = ",".join([p for _, p, _ in layers] + ["left top"])
    sizes = ",".join([z for _, _, z in layers] + ["100% 100%"])
    return f"""<style>
.stApp{{background-color:{BG};background-image:{images};background-position:{positions};
background-size:{sizes};background-repeat:no-repeat;}}
[data-testid="stAppViewContainer"],[data-testid="stMain"],.stMain{{background:transparent;}}
[data-testid="stHeader"]{{background:transparent;}}
[data-testid="stVerticalBlockBorderWrapper"],[class*="st-key-card"],[data-testid="stExpander"] details,
[role="tabpanel"]{{background:{CARD};border-radius:14px;}}
[data-testid="stExpander"] details{{border-color:{LINE};}}
[role="tabpanel"]{{padding:18px 20px;border:1px solid {LINE};margin-top:10px;}}
[data-testid="stAlert"]{{border:1px solid {LINE};}}
.stTabs [aria-selected="true"]{{color:{accent} !important;}}
.stTabs [data-baseweb="tab-highlight"]{{background-color:{accent} !important;}}
@media (prefers-reduced-motion:reduce){{.stApp{{background-image:linear-gradient(180deg,{glow} 0,{BG} 640px);
background-position:left top;background-size:100% 100%;}}}}
</style>"""
