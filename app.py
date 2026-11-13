"""Research dashboard for international Spotify chart performance."""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import re
import unicodedata
from html import escape
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "data" / "spotify_top200_cleaned.csv"
RESEARCH_FILE = PROJECT_DIR / "Research" / "Afrobeats_Capstone_Final_Research_Workbook.xlsx"
NAV_ITEMS = [
    "Overview",
    "Global Market Performance",
    "Country Comparison",
    "Track & Artist Performance",
    "Afrobeats Artists & Tracks",
    "Growth Opportunities",
    "Data & Methodology",
]
NAVY = "#080C18"
PANEL = "#111827"
ACCENT_GOLD = "#D5B66C"
ACCENT_PURPLE = "#8F7BE8"
ACCENT_BLUE = "#4294D8"
ACCENT_TURQUOISE = "#39B8A9"
ACCENT_CORAL = "#FF7A85"
ACCENT_ELECTRIC = "#668BFF"
TEXT = "#F8FAFF"
MUTED = "#B5C0D1"
CHART_CONFIG = {"displayModeBar": "hover", "responsive": True}

# Common market codes in the Spotify chart files. Unmapped codes remain in
# metrics and tables; only mapped codes can be placed on the country map.
COUNTRY_NAMES = {
    "ar": "Argentina", "at": "Austria", "au": "Australia", "be": "Belgium",
    "bo": "Bolivia", "br": "Brazil", "ca": "Canada", "ch": "Switzerland",
    "cl": "Chile", "co": "Colombia", "cr": "Costa Rica", "cz": "Czechia",
    "de": "Germany", "dk": "Denmark", "do": "Dominican Republic", "ec": "Ecuador",
    "ee": "Estonia", "es": "Spain", "fi": "Finland", "fr": "France",
    "gb": "United Kingdom", "gr": "Greece", "gt": "Guatemala", "hk": "Hong Kong",
    "hn": "Honduras", "hu": "Hungary", "id": "Indonesia", "ie": "Ireland",
    "il": "Israel", "in": "India", "is": "Iceland", "it": "Italy",
    "jp": "Japan", "kr": "South Korea", "lt": "Lithuania", "lu": "Luxembourg",
    "lv": "Latvia", "mx": "Mexico", "my": "Malaysia", "ng": "Nigeria", "nl": "Netherlands",
    "no": "Norway", "nz": "New Zealand", "pa": "Panama", "pe": "Peru",
    "ph": "Philippines", "pl": "Poland", "pt": "Portugal", "py": "Paraguay",
    "ro": "Romania", "se": "Sweden", "sg": "Singapore", "sk": "Slovakia",
    "th": "Thailand", "tr": "Turkey", "tw": "Taiwan", "ua": "Ukraine",
    "us": "United States", "uy": "Uruguay", "vn": "Vietnam", "za": "South Africa",
}


st.set_page_config(
    page_title="Global Afrobeats Market Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_theme():
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: dark; }}
        .stApp {{ background: radial-gradient(ellipse at 82% -12%, #21183C 0%, #0C1020 36%, #07080D 78%); color: {TEXT}; }}
        [data-testid="stHeader"] {{ background: rgba(7,8,13,.88); }}
        [data-testid="stSidebar"] {{ background: linear-gradient(180deg, #11101E 0%, #0A0B13 55%, #08090E 100%); border-right: 1px solid #282438; }}
        [data-testid="stSidebar"] * {{ color: {TEXT}; }}
        .block-container {{ max-width: 1640px; padding: 1.15rem clamp(1rem, 2.8vw, 2.65rem) 2.6rem; }}
        h1, h2, h3, h4 {{ color: {TEXT} !important; letter-spacing: -.035em; }}
        h2 {{ margin-top: .7rem; margin-bottom:.35rem; }} h3 {{ margin-top:.45rem; margin-bottom:.25rem; }} h4 {{ margin-top:.25rem; margin-bottom:.2rem; }}
        p, label, .stCaption {{ color: {MUTED}; }}
        .eyebrow {{ color:{ACCENT_TURQUOISE}; text-transform:uppercase; letter-spacing:.16em; font-size:.66rem; font-weight:800; margin-bottom:.45rem; }}
        .hero {{ position:relative; overflow:hidden; padding:clamp(1.25rem, 2.5vw, 2.15rem); border:1px solid #373047; border-top:2px solid {ACCENT_GOLD}; border-radius:22px;
          background:radial-gradient(ellipse at 84% 14%, rgba(128,79,231,.25), transparent 34%), linear-gradient(120deg,#171323 0%,#101322 54%,#0B101B 100%);
          box-shadow:0 18px 50px rgba(0,0,0,.34); margin-bottom:.8rem; }}
        .hero-grid {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(235px, .42fr); align-items:center; gap:1.4rem; }}
        .hero-side {{ display:flex; flex-direction:column; align-items:flex-end; gap:.15rem; }}
        .hero h1 {{ color:#FFF; margin:0; font-size:clamp(1.75rem,3.3vw,3.2rem); line-height:.98; letter-spacing:-.055em; font-weight:850; }}
        .hero-title-sub {{ display:block; color:#C7B6FF; font-size:.72em; letter-spacing:.025em; margin-top:.18em; }}
        .hero p {{ color:#D4D2DF; margin:.85rem 0 0; max-width:690px; font-size:1rem; line-height:1.55; }}
        .hero-status {{ display:inline-flex; align-items:center; gap:.45rem; border:1px solid rgba(57,184,169,.35); color:#9BE6D9; background:rgba(24,120,112,.13); border-radius:999px; padding:.3rem .62rem; font-size:.64rem; letter-spacing:.1em; font-weight:800; text-transform:uppercase; margin-bottom:.8rem; }}
        .hero-status-dot {{ width:7px; height:7px; border-radius:50%; background:#55DCC6; box-shadow:0 0 12px #55DCC6; }}
        .welcome-topline {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; }}
        .welcome-heading {{ color:#FFF; margin:0; font-size:clamp(1.85rem,3.5vw,3.35rem); line-height:.98; letter-spacing:-.055em; font-weight:850; }}
        .welcome-heading span {{ color:#C1A6FF; }}
        .profile-panel {{ display:flex; align-items:center; gap:.65rem; border:1px solid rgba(255,255,255,.14); background:rgba(10,10,18,.56); border-radius:999px; padding:.42rem .72rem .42rem .45rem; box-shadow:0 6px 18px rgba(0,0,0,.2); }}
        .profile-avatar {{ width:38px; height:38px; display:grid; place-items:center; border-radius:50%; color:#FFF; font-size:.96rem; font-weight:900; background:linear-gradient(140deg,#9E68ED,#2FBCD0 70%,#FFC45B); box-shadow:0 0 18px rgba(119,94,230,.3); }}
        .profile-name {{ color:#FFF; font-size:.72rem; font-weight:800; letter-spacing:.06em; }} .profile-date {{ color:#AAA8BA; font-size:.61rem; margin-top:.12rem; white-space:nowrap; }}
        .hero-compact-title {{ color:#FFF; margin:0; font-size:clamp(1.5rem,2.7vw,2.4rem); line-height:1.02; letter-spacing:-.05em; font-weight:850; }}
        .waveform {{ height:82px; display:flex; align-items:center; justify-content:center; gap:5px; opacity:.9; }}
        .waveform span {{ display:block; width:5px; border-radius:8px; background:linear-gradient(180deg,#A78BFA,#48D7DE); box-shadow:0 0 14px rgba(121,104,243,.4); }}
        .hero-metrics {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:.55rem; margin-top:1.2rem; }}
        .hero-metric {{ padding:.68rem .8rem; border:1px solid rgba(180,168,215,.14); border-radius:12px; background:rgba(7,9,16,.45); min-width:0; }}
        .hero-metric-label {{ color:#A7A4B3; font-size:.59rem; text-transform:uppercase; letter-spacing:.12em; font-weight:750; }}
        .hero-metric-value {{ color:#FFF; display:block; font-size:1.1rem; font-weight:800; margin-top:.22rem; font-variant-numeric:tabular-nums; }}
        .hero-context {{ display:flex; flex-wrap:wrap; gap:.55rem; margin-top:.7rem; color:#BEBACB; font-size:.72rem; }}
        .hero-context span {{ padding:.24rem .55rem; border:1px solid #29283A; background:#0B0D15; border-radius:999px; }}
        .notice {{ border:1px solid rgba(213,182,108,.28); border-left:3px solid {ACCENT_GOLD}; background:linear-gradient(90deg,rgba(213,182,108,.09),rgba(20,17,29,.7)); color:#F1E8D4; padding:.65rem .85rem; border-radius:11px; font-size:.82rem; line-height:1.5; margin:.75rem 0 1.1rem; }}
        .section-heading {{ margin:1.25rem 0 .85rem; padding-bottom:.72rem; border-bottom:1px solid rgba(166,151,213,.16); }}
        .section-heading .eyebrow {{ margin-bottom:.22rem; color:#B49AF7; }} .section-heading h2 {{ margin:0; font-size:clamp(1.25rem,2vw,1.7rem); }}
        .section-heading p {{ margin:.28rem 0 0; font-size:.83rem; line-height:1.45; color:#9FA3B4; }}
        .panel-heading {{ display:flex; align-items:baseline; justify-content:space-between; gap:.5rem; margin:0 0 .35rem; }}
        .panel-heading strong {{ color:#F7F4FF; font-size:.96rem; }} .panel-heading span {{ color:#8C8A9D; font-size:.64rem; letter-spacing:.1em; text-transform:uppercase; }}
        .panel-copy {{ color:#A9A9B9; font-size:.77rem; line-height:1.45; margin:.15rem 0 .6rem; }}
        .kpi-card {{ min-height:126px; height:100%; padding:.86rem .9rem; border-radius:15px; border:1px solid #302D3E; background:linear-gradient(145deg,#191725 0%,#10121C 82%); box-shadow:0 9px 26px rgba(0,0,0,.2); position:relative; overflow:hidden; }}
        .kpi-card:after {{ content:''; position:absolute; top:0; right:0; width:42px; height:2px; background:linear-gradient(90deg,transparent,{ACCENT_TURQUOISE}); }}
        .kpi-top {{ display:flex; align-items:center; gap:.5rem; }} .kpi-icon {{ width:26px; height:26px; display:grid; place-items:center; border-radius:8px; color:#C7B8FF; background:rgba(136,103,232,.16); font-size:.8rem; }}
        .kpi-label {{ color:#A7A5B4; font-size:.61rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; line-height:1.25; }}
        .kpi-value {{ color:#FFF; font-size:clamp(1.32rem,1.8vw,1.85rem); font-weight:850; line-height:1.15; margin:.6rem 0 .18rem; letter-spacing:-.04em; font-variant-numeric:tabular-nums; }}
        .kpi-detail {{ color:#898A9B; font-size:.68rem; line-height:1.35; }}
        .rank-card {{ padding:.7rem .8rem; border:1px solid #302D3E; border-radius:13px; background:linear-gradient(110deg,#191725,#10131D); margin:.42rem 0; }}
        .rank-head {{ display:flex; align-items:center; gap:.55rem; }} .rank-no {{ color:#C1A2FF; font:800 .7rem/1 ui-monospace,monospace; width:24px; }}
        .rank-name {{ color:#F8F7FC; font-size:.85rem; font-weight:750; flex:1; }} .rank-value {{ color:#74E0D2; font-size:.83rem; font-weight:800; font-variant-numeric:tabular-nums; }}
        .rank-sub {{ color:#9293A4; font-size:.68rem; margin:.25rem 0 .35rem 29px; }} .rank-track {{ height:3px; border-radius:3px; background:#272638; margin-left:29px; overflow:hidden; }} .rank-track span {{ display:block; height:100%; border-radius:inherit; background:linear-gradient(90deg,#8F66EB,#44C9DB); }}
        .catalog-card {{ min-height:142px; height:100%; border:1px solid #383249; border-radius:14px; padding:.8rem .85rem; background:radial-gradient(circle at 100% 0,rgba(120,78,210,.18),transparent 44%),linear-gradient(145deg,#191725,#10131C); position:relative; overflow:hidden; }}
        .catalog-card:before {{ content:''; position:absolute; left:0; top:0; bottom:0; width:3px; background:linear-gradient(180deg,#A585F4,#48C8D7); }}
        .catalog-index {{ color:#A99BCE; font:700 .61rem/1 ui-monospace,monospace; letter-spacing:.1em; }} .catalog-title {{ color:#FFF; font-size:.91rem; font-weight:800; margin:.5rem 0 .2rem; line-height:1.2; }}
        .catalog-artist {{ color:#B5B1C5; font-size:.72rem; line-height:1.35; min-height:2em; }} .catalog-meta {{ display:flex; gap:.35rem; flex-wrap:wrap; margin-top:.65rem; }}
        .catalog-meta span {{ color:#82D9D2; border:1px solid rgba(78,191,184,.22); background:rgba(28,109,107,.12); border-radius:999px; padding:.2rem .42rem; font-size:.59rem; }}
        .track-tile {{ border:1px solid #353149; border-radius:16px; padding:.65rem; height:100%; min-height:260px; background:linear-gradient(155deg,#1A1727 0%,#11131D 80%); box-shadow:0 10px 26px rgba(0,0,0,.2); transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease; }}
        .track-tile:hover {{ transform:translateY(-3px); border-color:rgba(168,136,250,.6); box-shadow:0 13px 28px rgba(61,45,110,.24); }}
        .track-cover {{ width:100%; aspect-ratio:1/1; border-radius:11px; overflow:hidden; background:radial-gradient(circle at 25% 20%,rgba(255,122,133,.62),transparent 30%),radial-gradient(circle at 80% 72%,rgba(57,184,169,.52),transparent 40%),linear-gradient(140deg,#4E288B,#17192A 65%,#123841); position:relative; display:grid; place-items:center; }}
        .track-cover img {{ width:100%; height:100%; object-fit:cover; display:block; }}
        .cover-placeholder {{ display:flex; flex-direction:column; align-items:center; justify-content:center; width:100%; height:100%; color:#F8F5FF; text-align:center; }}
        .cover-placeholder b {{ font-size:1.9rem; line-height:1; text-shadow:0 2px 15px rgba(0,0,0,.4); }} .cover-placeholder small {{ color:#E7DFFF; font-size:.5rem; font-weight:800; letter-spacing:.16em; margin-top:.48rem; }}
        .track-chip {{ display:inline-block; color:#FFD58A; border:1px solid rgba(255,200,112,.24); background:rgba(171,109,37,.13); padding:.16rem .38rem; border-radius:999px; text-transform:uppercase; letter-spacing:.08em; font-size:.53rem; font-weight:800; margin:.52rem 0 .34rem; }}
        .track-tile-title {{ color:#FFF; font-size:.83rem; font-weight:850; line-height:1.2; overflow-wrap:anywhere; }} .track-tile-artist {{ color:#B9B4C7; font-size:.67rem; line-height:1.35; min-height:2.3em; margin-top:.2rem; }}
        .track-tile-stats {{ display:flex; flex-wrap:wrap; gap:.3rem; margin-top:.55rem; }} .track-tile-stats span {{ color:#89DDE1; border:1px solid rgba(93,188,199,.22); background:rgba(42,106,130,.12); border-radius:7px; padding:.2rem .32rem; font-size:.57rem; white-space:nowrap; }}
        .artwork-credit {{ margin-top:.42rem; font-size:.54rem; line-height:1.25; }} .artwork-credit a {{ color:#B6A4F4; text-decoration:none; }} .artwork-credit a:hover {{ color:#84E1D7; text-decoration:underline; }}
        .playlist-heading {{ display:flex; align-items:baseline; justify-content:space-between; gap:.6rem; margin:.8rem 0 .45rem; }} .playlist-heading strong {{ color:#FFF; font-size:1rem; }} .playlist-heading span {{ color:#9D99AE; font-size:.65rem; }}
        .artist-tile {{ min-height:139px; border:1px solid #363147; border-radius:15px; padding:.82rem; background:radial-gradient(circle at 100% 0,rgba(255,122,133,.12),transparent 40%),linear-gradient(145deg,#1A1726,#10131C); }}
        .artist-top {{ display:flex; align-items:center; gap:.6rem; }} .artist-avatar {{ width:42px; height:42px; display:grid; place-items:center; border-radius:50%; color:#FFF; font-weight:900; background:linear-gradient(140deg,#6C4BC1,#258999); border:1px solid rgba(199,177,255,.42); box-shadow:0 0 14px rgba(111,79,190,.22); }}
        .artist-tile-name {{ color:#FFF; font-size:.82rem; font-weight:800; line-height:1.2; }} .artist-tile-rank {{ color:#FFB1B7; font-size:.6rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }}
        .artist-metrics {{ color:#A8A4B6; font-size:.65rem; margin-top:.65rem; line-height:1.45; }} .artist-metrics b {{ color:#83DED4; font-weight:800; }}
        .insight-card {{ border:1px solid rgba(125,93,221,.24); border-radius:14px; padding:.86rem 1rem; background:linear-gradient(110deg,rgba(103,72,183,.12),rgba(16,18,28,.88)); color:#E4E0EF; line-height:1.5; font-size:.84rem; }}
        [data-testid="stVerticalBlockBorderWrapper"] {{ border-color:#302D3E !important; border-radius:16px !important; background:linear-gradient(145deg,rgba(22,21,33,.83),rgba(12,14,21,.82)); box-shadow:0 10px 28px rgba(0,0,0,.18); }}
        [data-testid="stMetric"] {{ background:linear-gradient(145deg,#191725,#10121C); border:1px solid #302D3E; border-radius:13px; padding:.8rem .9rem; min-height:95px; height:100%; }}
        [data-testid="stMetricLabel"] {{ color:#B8B4C5; font-size:.77rem; font-weight:650; white-space:normal; }} [data-testid="stMetricValue"] {{ color:#FFF; font-size:clamp(1.15rem,1.5vw,1.55rem); font-weight:800; line-height:1.2; white-space:normal; }}
        div[data-testid="stPlotlyChart"] {{ background:transparent; border:0; border-radius:10px; padding:0; width:100%; max-width:100%; box-sizing:border-box; }}
        div[data-testid="stDataFrame"] {{ border:1px solid #302D3E; border-radius:12px; overflow:hidden; }} [data-testid="stDataFrame"] {{ max-width:100%; }}
        [data-testid="stSidebar"] [data-testid="stDateInput"], [data-testid="stSidebar"] [data-testid="stMultiSelect"] {{ margin-bottom:.55rem; }}
        [data-testid="stMultiSelect"] [data-baseweb="tag"], .stApp [data-baseweb="tag"] {{ background-color:#49356F !important; background-image:linear-gradient(105deg,#49356F,#205969) !important; border:1px solid rgba(134,205,213,.34) !important; border-radius:999px !important; color:#F7F5FF !important; }}
        [data-testid="stMultiSelect"] [data-baseweb="tag"] *, .stApp [data-baseweb="tag"] * {{ color:#F7F5FF !important; fill:#D9F5F2 !important; }}
        [data-testid="stSidebar"] [role="radiogroup"] {{ gap:.16rem; }}
        [data-testid="stSidebar"] [role="radiogroup"] label {{ border:1px solid transparent; border-radius:10px; padding:.3rem .45rem; transition:all .16s ease; }}
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background:rgba(139,99,232,.1); border-color:rgba(139,99,232,.22); }}
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background:linear-gradient(100deg,rgba(124,86,209,.2),rgba(55,166,187,.06)); border-color:rgba(157,126,227,.26); box-shadow:inset 2px 0 #B49AF7; }}
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {{ color:#FFF; font-weight:750; }}
        [data-testid="stSidebar"] [data-testid="stBaseButton-primary"], [data-testid="stSidebar"] .stButton button[kind="primary"] {{ background:linear-gradient(105deg,#6D4CB8,#237E91) !important; color:#FFF !important; border:1px solid rgba(174,151,248,.42) !important; box-shadow:0 4px 14px rgba(86,63,150,.25); }}
        [data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover, [data-testid="stSidebar"] .stButton button[kind="primary"]:hover {{ border-color:#64D8D5 !important; color:#FFF !important; }}
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"], [data-testid="stSidebar"] .stButton button[kind="secondary"] {{ background:linear-gradient(110deg,#171622,#11131D) !important; border:1px solid #2B293A !important; color:#E7E4EF !important; }}
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover, [data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {{ border-color:rgba(117,207,210,.3) !important; color:#FFF !important; }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4 {{ color:#77768A !important; font-size:.62rem; text-transform:uppercase; letter-spacing:.16em; margin:1rem 0 .34rem; }}
        [data-baseweb="select"] > div, [data-baseweb="input"] > div {{ background-color:#15141F; border-color:#343143; border-radius:9px; }}
        .sidebar-brand {{ font-size:1.05rem; letter-spacing:.07em; font-weight:900; line-height:1.12; color:#F9F7FF; }}
        .sidebar-brand em {{ color:#B5A1FA; font-style:normal; }} .sidebar-tagline {{ color:#89889B; font-size:.68rem; margin-top:.52rem; }}
        .equalizer {{ height:19px; display:flex; align-items:center; gap:3px; margin:.7rem 0 .45rem; }} .equalizer i {{ display:block; width:3px; border-radius:2px; background:linear-gradient(180deg,#B39AFF,#42D0DB); }}
        .nav-note {{ color:#77768A; font-size:.63rem; letter-spacing:.12em; font-weight:800; text-transform:uppercase; margin:.75rem 0 .15rem; }}
        .section-note {{ color:#A2A2B2; font-size:.86rem; line-height:1.5; }} hr {{ border-color:#292637; margin:.75rem 0; }}
        [data-testid="stExpander"] {{ border-color:#302D3E; border-radius:12px; background:rgba(17,16,26,.65); }}
        @media (max-width:850px) {{ .hero-grid {{ grid-template-columns:1fr; }} .waveform {{ display:none; }} .hero-metrics {{ grid-template-columns:repeat(3,minmax(0,1fr)); }} }}
        @media (max-width:600px) {{ .block-container {{ padding-top:.8rem; }} .hero {{ border-radius:16px; }} .hero-metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .hero-context span {{ flex:1 1 42%; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner="Loading Spotify chart observations…")
def load_data(path: str, modified_time: float) -> pd.DataFrame:
    """Load the cleaned chart file and normalize analysis fields."""
    data = pd.read_csv(path, dtype={"cc": "string", "track_id": "string"})
    data["week_end"] = pd.to_datetime(data["week_end"], errors="coerce")
    for column in ("rank", "streams", "appearances", "peak", "prev_rank"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    for column in ("cc", "track_id", "title", "artists"):
        data[column] = data[column].fillna("").astype(str).str.strip()
    data["market_name"] = data["cc"].str.lower().map(COUNTRY_NAMES).fillna(data["cc"].str.upper())
    data["artist_list"] = data["artists"].apply(split_artists)
    data["year"] = data["week_end"].dt.year
    return data


def read_workbook_table(path, sheet_name, required_columns, scan_rows=12):
    """Read a workbook table by locating its actual header row, not assuming row 1/3."""
    sheet = pd.read_excel(path, sheet_name=sheet_name, header=None, engine="openpyxl")
    inspected_rows = []
    for row_index in range(min(scan_rows, len(sheet))):
        labels = [str(value).strip() if pd.notna(value) else "" for value in sheet.iloc[row_index].tolist()]
        actual_columns = {label for label in labels if label}
        inspected_rows.append((row_index + 1, sorted(actual_columns)))
        if required_columns.issubset(actual_columns):
            nonempty_labels = [label for label in labels if label]
            duplicates = sorted({label for label in nonempty_labels if nonempty_labels.count(label) > 1})
            if duplicates:
                raise ValueError(f"Workbook sheet '{sheet_name}' has duplicate header labels: {', '.join(duplicates)}")
            table = sheet.iloc[row_index + 1:].copy()
            table.columns = labels
            table = table.loc[:, [label for label in labels if label]]
            return table.dropna(how="all").reset_index(drop=True)
    raise ValueError(
        f"Could not find the required header in workbook sheet '{sheet_name}'. "
        f"Expected: {', '.join(sorted(required_columns))}. Inspected rows: {inspected_rows}"
    )


@st.cache_data(show_spinner="Loading validated Afrobeats research workbook…")
def load_validated_research(path: str, modified_time: float):
    """Load matched song credits and their balanced-date Spotify observations."""
    required_match_columns = {
        "normalized_title", "artists", "display_title", "spotify_id_count",
        "release_dates", "official_chart_match", "version_review_required", "validation_status",
    }
    required_observation_columns = {
        "normalized_title", "shortlist_artists", "cc", "week_end", "best_rank", "spotify_ids", "streams_sum",
    }
    required_early_columns = {
        "early_12_snapshot_songs", "latest_12_snapshot_songs", "change_in_song_breadth", "market_code",
    }
    required_shortlist_columns = {"Priority", "Market", "Matched songs", "Chart appearances", "Weeks present"}
    matches = read_workbook_table(path, "4. Matched Songs", required_match_columns)
    observations = read_workbook_table(path, "Raw - Balanced Date Observ", required_observation_columns)
    early_latest = read_workbook_table(path, "Raw - Early vs Latest", required_early_columns)
    shortlist = read_workbook_table(path, "6. Opportunity Shortlist", required_shortlist_columns)

    for label, frame, required in (
        ("4. Matched Songs", matches, required_match_columns),
        ("Raw - Balanced Date Observ", observations, required_observation_columns),
        ("Raw - Early vs Latest", early_latest, required_early_columns),
        ("6. Opportunity Shortlist", shortlist, required_shortlist_columns),
    ):
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"Workbook sheet '{label}' is missing columns: {', '.join(sorted(missing))}")

    for column in ("normalized_title", "artists", "display_title", "release_dates", "validation_status"):
        matches[column] = matches[column].fillna("").astype(str).str.strip()
    matches["official_chart_match"] = pd.to_numeric(matches["official_chart_match"], errors="coerce")
    matches["spotify_id_count"] = pd.to_numeric(matches["spotify_id_count"], errors="coerce").fillna(0).astype(int)
    matches = matches.loc[matches["official_chart_match"].eq(1)].copy()
    matches["song_artist_key"] = matches["normalized_title"] + "\x1f" + matches["artists"]
    matches = matches.drop_duplicates("song_artist_key")
    if matches.empty:
        raise ValueError("The workbook contains no rows with a confirmed Official UK Afrobeats Chart match.")

    for column in ("normalized_title", "shortlist_artists", "cc"):
        observations[column] = observations[column].fillna("").astype(str).str.strip()
    observations["week_end"] = pd.to_datetime(observations["week_end"], errors="coerce")
    for column in ("best_rank", "spotify_ids", "streams_sum"):
        observations[column] = pd.to_numeric(observations[column], errors="coerce")
    observations["song_artist_key"] = observations["normalized_title"] + "\x1f" + observations["shortlist_artists"]
    catalog = matches[["song_artist_key", "display_title", "artists", "spotify_id_count", "version_review_required"]]
    if "version_review_required" not in matches:
        matches["version_review_required"] = ""
        catalog = matches[["song_artist_key", "display_title", "artists", "spotify_id_count", "version_review_required"]]
    observations = observations.merge(catalog, on="song_artist_key", how="left", validate="many_to_one", indicator=True)
    unmatched = int(observations["_merge"].eq("left_only").sum())
    if unmatched:
        raise ValueError(f"{unmatched:,} workbook observations do not match a validated song–artist combination.")
    observations = observations.drop(columns="_merge")
    observations["market_name"] = observations["cc"].str.lower().map(COUNTRY_NAMES).fillna(observations["cc"].str.upper())
    observations["artist_list"] = observations["artists"].apply(split_artists)

    for column in ("market_code",):
        early_latest[column] = early_latest[column].fillna("").astype(str).str.strip()
    for column in ("early_12_snapshot_songs", "latest_12_snapshot_songs", "change_in_song_breadth"):
        early_latest[column] = pd.to_numeric(early_latest[column], errors="coerce")
    early_latest["market_name"] = early_latest["market_code"].str.lower().map(COUNTRY_NAMES).fillna(early_latest["market_code"].str.upper())
    for column in ("Priority", "Matched songs", "Chart appearances", "Weeks present", "Median best rank"):
        shortlist[column] = pd.to_numeric(shortlist[column], errors="coerce")
    shortlist = shortlist.loc[shortlist["Priority"].notna()].copy()
    return matches, observations, early_latest, shortlist


def split_artists(value):
    return [name.strip() for name in re.split(r"\s*[|;/&,]\s*", str(value)) if name.strip()]


def chart_layout(height=350, **kwargs):
    layout = dict(
        template="plotly_dark",
        height=height,
        margin=dict(l=50, r=34, t=64, b=42),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[ACCENT_PURPLE, ACCENT_TURQUOISE, ACCENT_ELECTRIC, ACCENT_CORAL, ACCENT_GOLD],
        font=dict(family="Inter, Aptos, Segoe UI, sans-serif", color=TEXT, size=11),
        title_font=dict(size=14, color="#F7F4FF"),
        title_x=0.02,
        title_xanchor="left",
        title_y=0.98,
        title_yanchor="top",
        legend=dict(bgcolor="rgba(17,16,26,.75)", font=dict(color=TEXT), bordercolor="rgba(160,145,210,.14)", borderwidth=1),
        hoverlabel=dict(bgcolor="#171522", bordercolor="#6F5AA5", font=dict(color="#FFFFFF", family="Inter, Aptos, sans-serif", size=11)),
        xaxis=dict(gridcolor="rgba(150,143,179,.12)", zerolinecolor="rgba(175,162,207,.3)", title_font_color=MUTED),
        yaxis=dict(gridcolor="rgba(150,143,179,.10)", zerolinecolor="rgba(175,162,207,.3)", title_font_color=MUTED),
    )
    layout.update(kwargs)
    return layout


def section_heading(kicker, title, description=None):
    description_html = f'<p>{escape(str(description))}</p>' if description else ""
    st.markdown(
        f'<div class="section-heading"><div class="eyebrow">{escape(str(kicker))}</div>'
        f'<h2>{escape(str(title))}</h2>{description_html}</div>',
        unsafe_allow_html=True,
    )


def panel_heading(title, detail=None):
    detail_html = f"<span>{escape(str(detail))}</span>" if detail else ""
    st.markdown(
        f'<div class="panel-heading"><strong>{escape(str(title))}</strong>{detail_html}</div>',
        unsafe_allow_html=True,
    )


def render_kpi_grid(items, columns=None):
    columns = columns or len(items)
    cols = st.columns(columns, gap="small")
    for index, (label, value, detail, icon) in enumerate(items):
        with cols[index % columns]:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-top"><span class="kpi-icon">{escape(str(icon))}</span>'
                f'<span class="kpi-label">{escape(str(label))}</span></div>'
                f'<div class="kpi-value">{escape(str(value))}</div>'
                f'<div class="kpi-detail">{escape(str(detail))}</div></div>',
                unsafe_allow_html=True,
            )


def render_market_rank_cards(summary, limit=5):
    if summary.empty:
        st.info("No matched-song country observations match the active filters.")
        return
    ranked = summary.sort_values(
        ["matched_song_artist_pairs", "song_market_snapshot_observations", "market_name"],
        ascending=[False, False, True],
    ).head(limit)
    max_value = max(1, int(ranked["matched_song_artist_pairs"].max()))
    for index, row in enumerate(ranked.itertuples(index=False), start=1):
        ratio = max(4, int(100 * row.matched_song_artist_pairs / max_value))
        st.markdown(
            f'<div class="rank-card"><div class="rank-head"><span class="rank-no">{index:02d}</span>'
            f'<span class="rank-name">{escape(str(row.market_name))}</span>'
            f'<span class="rank-value">{int(row.matched_song_artist_pairs):,}</span></div>'
            f'<div class="rank-sub">matched combinations · {int(row.song_market_snapshot_observations):,} chart observations · {int(row.weeks_with_presence):,} dates</div>'
            f'<div class="rank-track"><span style="width:{ratio}%"></span></div></div>',
            unsafe_allow_html=True,
        )


def render_opportunity_card(row, label=None):
    title = label or str(row["Market"])
    priority = "Domestic benchmark" if str(row["Market"]).casefold() == "nigeria" else f"Priority {int(row['Priority'])}"
    detail = escape(str(row.get("Reason for inclusion", "")))
    st.markdown(
        f'<div class="rank-card"><div class="rank-head"><span class="rank-no">{priority}</span>'
        f'<span class="rank-name">{escape(title)}</span><span class="rank-value">{int(row["Chart appearances"]):,}</span></div>'
        f'<div class="rank-sub">{int(row["Matched songs"]):,} matched songs · {int(row["Weeks present"]):,} weeks present · median best rank {float(row["Median best rank"]):.1f}</div>'
        f'<div class="panel-copy">{detail}</div></div>',
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=86400, show_spinner=False)
def normalize_artwork_match(value):
    folded = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.findall(r"[a-z0-9]+", folded.lower()))


@st.cache_data(ttl=86400, max_entries=512, show_spinner=False)
def itunes_track_artwork(track_title, credited_artists):
    """Return cover art only when iTunes matches the exact title and full artist credit."""
    expected_title = normalize_artwork_match(track_title)
    artist_credits = [normalize_artwork_match(name) for name in split_artists(credited_artists)]
    expected_artists = tuple(sorted(name for name in artist_credits if name))
    unavailable = {
        "artwork_url": "", "store_url": "", "source": "Apple iTunes Search API",
        "collection_name": "", "matched_title": "", "matched_artist": "",
        "match_confidence": "None", "verification_status": "Placeholder — no exact match",
    }
    if not expected_title or not expected_artists:
        return unavailable
    try:
        query = urlencode({
            "term": f"{track_title} {artist_credits[0]}",
            "entity": "song",
            "limit": 20,
            "country": "us",
        })
        request = Request(
            f"https://itunes.apple.com/search?{query}",
            headers={"User-Agent": "GlobalAfrobeatsMarketIntelligence/1.0"},
        )
        with urlopen(request, timeout=4.0) as response:
            payload = json.loads(response.read(1_000_000).decode("utf-8"))
        for result in payload.get("results", []):
            # Ignore non-song entities and require the full credited artist set;
            # matching only a lead artist can attach the wrong collaboration art.
            if result.get("wrapperType") != "track" or result.get("kind") != "song":
                continue
            if normalize_artwork_match(result.get("trackName")) != expected_title:
                continue
            matched_artists = tuple(sorted(
                name for name in (
                    normalize_artwork_match(part)
                    for part in split_artists(result.get("artistName", ""))
                ) if name
            ))
            if matched_artists != expected_artists:
                continue
            artwork_url = str(result.get("artworkUrl100", "")).strip()
            parsed = urlparse(artwork_url)
            store_url = str(result.get("trackViewUrl", "")).strip()
            store_parsed = urlparse(store_url)
            if (parsed.scheme == "https" and parsed.hostname and parsed.hostname.endswith("mzstatic.com")
                    and store_parsed.scheme == "https" and store_parsed.hostname
                    and store_parsed.hostname.endswith("apple.com")):
                return {
                    "artwork_url": artwork_url,
                    "store_url": store_url,
                    "source": "Apple iTunes Search API",
                    "collection_name": str(result.get("collectionName", "")),
                    "matched_title": str(result.get("trackName", "")),
                    "matched_artist": str(result.get("artistName", "")),
                    "match_confidence": "High — exact normalized title + full artist credit",
                    "verification_status": "Verified — exact track result",
                }
    except Exception:
        return {
            **unavailable,
            "match_confidence": "Not assessed",
            "verification_status": "Placeholder — lookup unavailable",
        }
    return unavailable


def resolve_itunes_artwork(track_records):
    unique_keys = list(dict.fromkeys(
        (str(title or "").strip(), str(artists or "").strip())
        for title, artists in track_records
    ))
    if not unique_keys:
        return {}
    artworks = {}
    with ThreadPoolExecutor(max_workers=min(4, len(unique_keys))) as pool:
        futures = {pool.submit(itunes_track_artwork, *key): key for key in unique_keys}
        for future in as_completed(futures):
            key = futures[future]
            try:
                artworks[key] = future.result()
            except Exception:
                artworks[key] = {
                    "artwork_url": "", "store_url": "", "source": "Apple iTunes Search API",
                    "collection_name": "", "matched_title": "", "matched_artist": "",
                    "match_confidence": "Not assessed",
                    "verification_status": "Placeholder — lookup unavailable",
                }
    return artworks


def render_artwork_audit():
    """Show a compact audit of image matches used by the visible track shelves."""
    audit = st.session_state.get("gami_artwork_audit", {})
    if not audit:
        return
    rows = []
    for (track_title, credited_artists), match in sorted(audit.items()):
        rows.append({
            "Track title": track_title,
            "Credited artist": credited_artists,
            "Artwork source": (
                f"{match.get('source', 'Apple iTunes Search API')} · {match.get('collection_name')}"
                if match.get("artwork_url") and match.get("collection_name")
                else match.get("source", "Apple iTunes Search API")
            ),
            "Artwork URL": match.get("artwork_url", ""),
            "Match confidence": match.get("match_confidence", "Not assessed"),
            "Verification status": match.get("verification_status", "Placeholder — no exact match"),
        })
    with st.expander(f"Artwork accuracy audit · {len(rows)} visible catalogue matches", expanded=False):
        st.caption("Images appear only for exact normalized title and full credited-artist matches to an iTunes song result. All other entries retain designed placeholders.")
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, key="gami_artwork_audit_table")


def build_music_catalogue(matches, observations):
    """Prepare display-ready track cards from the validated workbook rows and active observations."""
    catalogue_columns = [
        "song_artist_key", "display_title", "artists", "spotify_id_count", "spotify_track_ids",
        "chart_observations", "country_markets", "snapshot_dates", "global_observations", "last_seen",
    ]
    catalogue = matches[[
        "song_artist_key", "display_title", "artists", "spotify_id_count", "spotify_track_ids",
    ]].drop_duplicates("song_artist_key").copy()
    country_observations, global_observations = split_global_markets(observations)
    if country_observations.empty:
        country_summary = pd.DataFrame(columns=["song_artist_key", "chart_observations", "country_markets", "snapshot_dates", "last_seen"])
    else:
        country_summary = country_observations.groupby("song_artist_key", as_index=False).agg(
            chart_observations=("song_artist_key", "size"),
            country_markets=("market_name", "nunique"),
            snapshot_dates=("week_end", "nunique"),
            last_seen=("week_end", "max"),
        )
    if global_observations.empty:
        global_summary = pd.DataFrame(columns=["song_artist_key", "global_observations"])
    else:
        global_summary = global_observations.groupby("song_artist_key", as_index=False).size().rename(columns={"size": "global_observations"})
    catalogue = catalogue.merge(country_summary, on="song_artist_key", how="left", validate="one_to_one")
    catalogue = catalogue.merge(global_summary, on="song_artist_key", how="left", validate="one_to_one")
    for column in ("chart_observations", "country_markets", "snapshot_dates", "global_observations"):
        catalogue[column] = pd.to_numeric(catalogue[column], errors="coerce").fillna(0).astype(int)
    catalogue["last_seen"] = pd.to_datetime(catalogue["last_seen"], errors="coerce")
    return catalogue if not catalogue.empty else pd.DataFrame(columns=catalogue_columns)


def render_track_collection(title, subtitle, tracks, metric="chart_observations", metric_label="country observations", limit=4):
    st.markdown(
        f'<div class="playlist-heading"><strong>{escape(str(title))}</strong><span>{escape(str(subtitle))}</span></div>',
        unsafe_allow_html=True,
    )
    if tracks.empty:
        st.info("No validated track matches appear in this collection under the current filters.")
        return
    rows = tracks.head(limit).copy()
    lookup_keys = list(zip(rows["display_title"].fillna("").astype(str), rows["artists"].fillna("").astype(str)))
    artwork = resolve_itunes_artwork(lookup_keys)
    audit = st.session_state.setdefault("gami_artwork_audit", {})
    audit.update(artwork)
    columns = st.columns(min(4, len(rows)), gap="small")
    for index, row in enumerate(rows.itertuples(index=False), start=1):
        lookup = artwork.get((str(row.display_title), str(row.artists)), {})
        image_url = lookup.get("artwork_url", "")
        store_url = lookup.get("store_url", "")
        if image_url and store_url:
            cover = (
                f'<a href="{escape(store_url, quote=True)}" target="_blank" rel="noopener noreferrer" '
                f'aria-label="View {escape(str(row.display_title), quote=True)} in the iTunes Store">'
                f'<img src="{escape(image_url, quote=True)}" alt="Album artwork for {escape(str(row.display_title), quote=True)}"></a>'
            )
            artwork_credit = (
                f'<div class="artwork-credit"><a href="{escape(store_url, quote=True)}" target="_blank" '
                'rel="noopener noreferrer">View in iTunes · Artwork provided courtesy of iTunes</a></div>'
            )
        else:
            monogram = escape(str(row.display_title)[:1].upper() or "♫")
            cover = f'<div class="cover-placeholder"><b>{monogram}</b><small>ARTWORK UNAVAILABLE</small></div>'
            artwork_credit = ""
        observation_chips = (
            f'<span>{int(row.country_markets):,} country markets</span>'
            f'<span>{int(getattr(row, metric)):,} {escape(metric_label)}</span>'
        )
        if metric != "global_observations" and int(row.global_observations) > 0:
            observation_chips += f'<span>{int(row.global_observations):,} GLOBAL</span>'
        with columns[(index - 1) % len(columns)]:
            st.markdown(
                f'<div class="track-tile"><div class="track-cover">{cover}</div>'
                f'<div class="track-chip">Validated UK-chart match</div>'
                f'<div class="track-tile-title">{escape(str(row.display_title))}</div>'
                f'<div class="track-tile-artist">{escape(str(row.artists))}</div>'
                f'<div class="track-tile-stats">{observation_chips}</div>{artwork_credit}</div>',
                unsafe_allow_html=True,
            )


def render_artist_discovery_cards(artists, limit=6):
    if artists.empty:
        st.info("No credited artists have matched country-chart observations under the current filters.")
        return
    ranked = artists.head(limit)
    columns = st.columns(3, gap="small")
    for index, row in enumerate(ranked.itertuples(index=False), start=1):
        artist = str(row.artist)
        initials = escape("".join(part[0] for part in artist.split()[:2]).upper() or "♪")
        with columns[(index - 1) % len(columns)]:
            st.markdown(
                f'<div class="artist-tile"><div class="artist-top"><div class="artist-avatar">{initials}</div>'
                f'<div><div class="artist-tile-rank">#{index:02d} · matched visibility</div>'
                f'<div class="artist-tile-name">{escape(artist)}</div></div></div>'
                f'<div class="artist-metrics"><b>{int(row.matched_song_artist_pairs):,}</b> matched pairs · '
                f'<b>{int(row.country_markets):,}</b> country markets<br>'
                f'<b>{int(row.credited_song_market_snapshots):,}</b> credited country observations</div></div>',
                unsafe_allow_html=True,
            )


def show_header(section, date_range=None, selected_markets=None, market_options=None, match_count=0,
                matched_ids=0, country_markets=0, observation_count=0, snapshot_count=0, display_name=""):
    if isinstance(date_range, (tuple, list)):
        start = date_range[0] if len(date_range) > 0 else None
        end = date_range[1] if len(date_range) > 1 else None
        if start is not None and end is not None:
            period = f"{start:%b %d, %Y} – {end:%b %d, %Y}"
        elif start is not None:
            period = f"From {start:%b %d, %Y} · choose an end date"
        elif end is not None:
            period = f"Through {end:%b %d, %Y} · choose a start date"
        else:
            period = "Select a reporting period"
    elif date_range is not None:
        period = f"Through {date_range:%b %d, %Y}"
    else:
        period = "Dataset coverage"
    if selected_markets is None:
        market_context = "Awaiting data"
    elif market_options and len(selected_markets) == len(market_options):
        market_context = f"All {len(selected_markets):,} markets"
    else:
        market_context = f"{len(selected_markets):,} market(s) selected"
    validated = match_count > 0
    status = "Workbook validated" if validated else "Research data unavailable"
    today = datetime.now().astimezone().strftime("%A, %B %d, %Y")
    display_name = " ".join(str(display_name or "").split()).title()
    name_initials = "".join(part[0] for part in display_name.split()[:2]).upper() or "♫"
    is_overview = section == "Overview"
    hero_metrics = [
        ("Validated pairs", f"{match_count:,}"),
        ("Spotify IDs", f"{matched_ids:,}"),
        ("Country markets", f"{country_markets:,}"),
        ("Observations", f"{observation_count:,}"),
        ("Snapshot dates", f"{snapshot_count:,}"),
    ]
    metrics_html = "".join(
        f'<div class="hero-metric"><div class="hero-metric-label">{escape(label)}</div>'
        f'<span class="hero-metric-value">{escape(value)}</span></div>'
        for label, value in hero_metrics
    )
    if is_overview:
        if display_name:
            welcome_title = f'<h1 class="welcome-heading">Welcome,<br><span>{escape(display_name)}</span></h1>'
        else:
            welcome_title = '<h1 class="welcome-heading">Your music<br><span>intelligence workspace</span></h1>'
        hero_copy = (
            '<div class="eyebrow">GLOBAL AFROBEATS MARKET INTELLIGENCE</div>'
            f'{welcome_title}'
            '<p>Explore the validated chart footprint of Afrobeats across international markets. '
            'This research workspace maps visibility in Spotify charts using confirmed UK chart matches.</p>'
        )
        metrics_section = f'<div class="hero-metrics">{metrics_html}</div>'
        metrics_note = '<span>Workbook KPIs are full-sample totals; filter-dependent measures are shown below.</span>'
    else:
        hero_copy = (
            '<div class="eyebrow">Spotify chart intelligence · Capstone research</div>'
            '<h1 class="hero-compact-title">GLOBAL AFROBEATS<span class="hero-title-sub">MARKET INTELLIGENCE</span></h1>'
            f'<p>{escape(section)} · Mapping international chart visibility for emerging Afrobeats artists.</p>'
        )
        metrics_section = ""
        metrics_note = ""
    profile_name = escape(display_name) if display_name else "NAME NOT SET"
    waveform_bars = [21, 43, 29, 62, 40, 76, 52, 35, 68, 44, 82, 51, 31, 61, 39, 72, 46, 27, 55, 36, 66, 43, 24]
    waveform = "".join(f'<span style="height:{height}px"></span>' for height in waveform_bars)
    st.markdown(
        f'<div class="hero"><div class="hero-grid"><div><div class="hero-status"><i class="hero-status-dot"></i>{status}</div>'
        f'{hero_copy}</div><div class="hero-side"><div class="waveform" aria-hidden="true">{waveform}</div>'
        f'<div class="profile-panel"><div class="profile-avatar">{escape(name_initials)}</div><div><div class="profile-name">{profile_name}</div><div class="profile-date">{escape(today)}</div></div></div></div></div>'
        f'{metrics_section}'
        f'<div class="hero-context"><span>Reporting period · {escape(period)}</span>'
        f'<span>Market filter · {escape(market_context)}</span><span>Current view · {escape(section)}</span>'
        f'{metrics_note}</div></div>',
        unsafe_allow_html=True,
    )
    st.write("")
    if section != "Overview":
        st.subheader(section)


def split_global_markets(data):
    is_global = data["cc"].astype("string").str.casefold().eq("global") | data["market_name"].astype("string").str.casefold().eq("global")
    return data.loc[~is_global].copy(), data.loc[is_global].copy()


def metric_row(matches, observations):
    country_observations, global_observations = split_global_markets(observations)
    markets = country_observations["market_name"].nunique()
    snapshots = observations["week_end"].nunique()
    spotify_ids = matches["spotify_id_count"].sum(min_count=1)
    values = [
        ("Matched song–artist pairs", f"{len(matches):,}", "Confirmed matches to the Official UK Afrobeats Chart; not a universal genre label"),
        ("Matched Spotify IDs", format_total(spotify_ids), "IDs grouped under the validated song–artist combinations"),
        ("Country markets with presence", f"{markets:,}", "Observed in workbook rows under the current date and market filters"),
        ("Matched snapshot dates", f"{snapshots:,}", "Dates with at least one matched observation under the current filters"),
    ]
    columns = st.columns(4)
    for col, (label, value, help_text) in zip(columns, values):
        col.metric(label, value, help=help_text)
    return len(country_observations), len(global_observations)


def format_total(value):
    return "—" if pd.isna(value) else f"{value:,.0f}"


def filter_research_observations(observations, date_range, selected_markets):
    filtered = observations
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = map(pd.Timestamp, date_range)
        filtered = filtered.loc[filtered["week_end"].between(start_date, end_date)]
    return filtered.loc[filtered["market_name"].isin(selected_markets)].copy()


def build_research_market_summary(observations):
    columns = [
        "cc", "market_name", "matched_song_artist_pairs", "song_market_snapshot_observations",
        "weeks_with_presence", "median_best_rank", "mean_best_rank", "total_streams",
    ]
    if observations.empty:
        return pd.DataFrame(columns=columns)
    summary = observations.groupby(["cc", "market_name"], as_index=False).agg(
        matched_song_artist_pairs=("song_artist_key", "nunique"),
        song_market_snapshot_observations=("song_artist_key", "size"),
        weeks_with_presence=("week_end", "nunique"),
        median_best_rank=("best_rank", "median"),
        mean_best_rank=("best_rank", "mean"),
        total_streams=("streams_sum", lambda values: values.sum(min_count=1)),
    )
    return summary.sort_values(
        ["matched_song_artist_pairs", "song_market_snapshot_observations", "market_name"],
        ascending=[False, False, True],
    )


def render_research_market_chart(summary, metric, title, chart_key, limit=12):
    if summary.empty:
        st.info("No matched-song country-market observations match the current filters.")
        return
    ranked = summary.sort_values([metric, "market_name"], ascending=[False, True]).head(limit)
    if len(ranked) == 1:
        st.metric(title, format_total(ranked[metric].iloc[0]))
        st.caption("A country comparison chart is omitted because only one market has observations.")
        return
    labels = {
        "matched_song_artist_pairs": "Matched song–artist combinations",
        "song_market_snapshot_observations": "Song–market–snapshot observations",
        "weeks_with_presence": "Snapshots with matched-song presence",
    }
    label = labels[metric]
    ranked = ranked.sort_values([metric, "market_name"], ascending=[True, False])
    fig = px.bar(
        ranked, x=metric, y="market_name", orientation="h", text=metric,
        color_discrete_sequence=[ACCENT_GOLD], labels={metric: label, "market_name": "Country market"},
        hover_data={metric: ":,.0f", "matched_song_artist_pairs": True,
                    "song_market_snapshot_observations": True, "weeks_with_presence": True},
    )
    fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_layout(
        **chart_layout(max(300, min(430, 26 * len(ranked) + 112)), margin=dict(l=130, r=54, t=58, b=34)),
        showlegend=False,
    )
    fig.update_xaxes(tickformat=",d", automargin=True)
    fig.update_yaxes(title=None, automargin=True)
    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG, key=chart_key)


def render_matched_presence_trend(observations):
    country_observations, global_observations = split_global_markets(observations)
    st.markdown("#### Matched-song visibility across balanced snapshots")
    global_col, context_col = st.columns([1, 2])
    with global_col:
        st.metric("GLOBAL chart observations", f"{len(global_observations):,}")
    with context_col:
        st.caption("GLOBAL is counted separately. Country trend values describe appearances in the matched Spotify sample, not listener totals or market size.")
    if country_observations.empty:
        st.info("No country-market observations match the current date and market filters.")
        return
    trend = country_observations.groupby("week_end", as_index=False).agg(
        matched_song_artist_pairs=("song_artist_key", "nunique"),
        song_market_snapshot_observations=("song_artist_key", "size"),
    ).sort_values("week_end")
    if len(trend) == 1:
        st.metric("Matched song–artist combinations observed", f"{int(trend['matched_song_artist_pairs'].iloc[0]):,}")
        st.caption("A trend chart is omitted because only one matched snapshot date remains under the filters.")
        return
    fig = px.line(
        trend, x="week_end", y="matched_song_artist_pairs", markers=True,
        labels={"week_end": "Balanced snapshot date", "matched_song_artist_pairs": "Distinct matched song–artist combinations"},
        hover_data={"song_market_snapshot_observations": True},
        title="Distinct matched song–artist combinations visible in country charts",
    )
    fig.update_traces(line_color=ACCENT_TURQUOISE, marker_color=ACCENT_GOLD, line_width=2.5)
    fig.update_layout(**chart_layout(350, margin=dict(l=55, r=24, t=60, b=38)))
    fig.update_yaxes(tickformat=",d", dtick=1, rangemode="tozero", automargin=True)
    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG, key="validated-weekly-presence")
    st.caption("The workbook uses 37 dates with complete coverage across 38 Spotify markets. Snapshot counts measure chart visibility only.")


def render_market_map(data):
    market_counts = data.groupby(["cc", "market_name"], as_index=False).size().rename(columns={"size": "Observations"})
    market_counts["map_name"] = market_counts["cc"].str.lower().map(COUNTRY_NAMES)
    mapped = market_counts.dropna(subset=["map_name"])
    if mapped.empty:
        st.info("No market codes could be mapped for the geographic view.")
        return
    if mapped["map_name"].nunique() < 2:
        market = mapped["market_name"].iloc[0]
        count = int(mapped["Observations"].iloc[0])
        st.metric(f"Mapped market · {market}", f"{count:,} chart observations")
        st.caption("A world map is omitted when the active filters contain only one mappable country.")
        return
    fig = px.choropleth(
        mapped, locations="map_name", locationmode="country names", color="Observations",
        hover_name="market_name", hover_data={"cc": True, "Observations": ":,"},
        color_continuous_scale=[[0, "#26334A"], [0.55, ACCENT_BLUE], [1, ACCENT_GOLD]],
        labels={"Observations": "Chart observations"},
        title="Matched-song visibility by country market",
    )
    fig.update_geos(
        scope="world", projection_type="natural earth", bgcolor=PANEL,
        showframe=False, showcoastlines=False, landcolor="#18283B", lakecolor=PANEL,
    )
    fig.update_layout(
        **chart_layout(445, margin=dict(l=8, r=8, t=52, b=8),
                       coloraxis_colorbar=dict(title="Observations", tickfont_color=TEXT)),
        autosize=True,
    )
    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG, key="market-map-coverage")
    st.caption("Country shading counts matched song–market–snapshot observations. GLOBAL is excluded; chart presence does not measure total listening or market size.")


def render_market_bars(data, metric="streams", title="Reported streams by market", limit=12, chart_key=None):
    if metric == "streams":
        values = data.groupby("market_name", as_index=False)["streams"].sum(min_count=1)
        label = "Reported streams (sum)"
    elif metric == "observations":
        values = data.groupby("market_name", as_index=False).size().rename(columns={"size": "observations"})
        metric, label = "observations", "Chart observations"
    else:
        values = data.groupby("market_name", as_index=False)["appearances"].sum(min_count=1)
        label = "Reported appearances (sum)"
    values = values.dropna(subset=[metric])
    if values.empty:
        st.info("No market values are available under the current filters.")
        return
    values = values.sort_values([metric, "market_name"], ascending=[False, True])
    if limit is not None:
        values = values.head(limit)
    if len(values) == 1:
        market = values["market_name"].iloc[0]
        value = values[metric].iloc[0]
        st.metric(f"{market} · {label}", format_total(value))
        st.caption("A ranked chart is omitted when the current selection contains only one market.")
        return
    values = values.sort_values([metric, "market_name"], ascending=[True, False])
    fig = px.bar(values, x=metric, y="market_name", orientation="h", color_discrete_sequence=[ACCENT_BLUE],
                 labels={metric: label, "market_name": "Market"}, title=title,
                 hover_data={metric: ":,.0f"})
    value_format = "%{x:.3s}" if metric == "streams" else "%{x:,.0f}"
    axis_format = ".3s" if metric == "streams" else ",.0f"
    fig.update_traces(texttemplate=value_format, textposition="outside", cliponaxis=False)
    fig.update_layout(
        **chart_layout(max(300, min(410, 25 * len(values) + 110)), margin=dict(l=135, r=78, t=56, b=34)),
        showlegend=False,
    )
    fig.update_xaxes(tickformat=axis_format, automargin=True)
    fig.update_yaxes(title=None, automargin=True)
    st.plotly_chart(
        fig, use_container_width=True, config=CHART_CONFIG,
        key=chart_key or f"market-bars-{metric}",
    )


def render_time_series(data):
    trend = data.dropna(subset=["week_end"]).groupby("week_end", as_index=False).agg(
        streams=("streams", "sum"), observations=("track_id", "size")
    )
    if trend.empty:
        st.info("No weekly stream totals are available under the current filters.")
        return
    if len(trend) == 1:
        st.metric("Reported streams · selected chart week", format_total(trend["streams"].iloc[0]))
        st.caption("A trend line is omitted when the active date filter contains one chart week. The streams counting window is unconfirmed.")
        return
    fig = px.line(trend, x="week_end", y="streams", markers=False,
                  labels={"week_end": "Chart week", "streams": "Reported streams (sum)"},
                  hover_data={"streams": ":,.0f", "observations": True},
                  title="Reported streaming performance over time")
    fig.update_traces(line_color=ACCENT_TURQUOISE, line_width=2.5)
    fig.update_layout(**chart_layout(350))
    fig.update_yaxes(tickformat=".3s")
    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG, key="market-stream-trend")
    st.caption("Each point sums the supplied streams values for all selected track × market rows sharing that chart week. The source streams counting window has not been confirmed.")


def render_track_rankings(data):
    tracks = data[data["title"].ne("")].groupby(["track_id", "title", "artists"], as_index=False).agg(
        streams=("streams", "sum"), chart_weeks=("week_end", "nunique"), best_rank=("rank", "min")
    )
    top = tracks.nlargest(15, "streams").sort_values("streams", ascending=False)
    if top.empty:
        st.info("No track totals are available under the current filters.")
        return
    st.markdown("#### Ranked tracks")
    display = top.rename(columns={
        "title": "Track", "artists": "Credited artists", "streams": "Reported streams",
        "chart_weeks": "Chart weeks", "best_rank": "Best rank",
    })[["Track", "Credited artists", "Reported streams", "Chart weeks", "Best rank"]]
    st.dataframe(display, width="stretch", height="content", hide_index=True, key="track-performance-table", column_config={
        "Reported streams": st.column_config.NumberColumn(format="%,.0f"),
        "Chart weeks": st.column_config.NumberColumn(format="%,.0f"),
        "Best rank": st.column_config.NumberColumn(format="%d"),
    })
    if len(top) < 2:
        st.caption("A ranking chart is omitted because only one track is present in this selection.")
        return
    chart_data = top.sort_values("streams")
    fig = px.bar(chart_data, x="streams", y="title", orientation="h", color_discrete_sequence=[ACCENT_PURPLE],
                 hover_data={"artists": True, "chart_weeks": True, "best_rank": True, "streams": ":,.0f"},
                 labels={"streams": "Reported streams (sum)", "title": "Track", "artists": "Credited artists",
                         "chart_weeks": "Observed chart weeks", "best_rank": "Best observed rank"},
                 title="Reported streams by track · Top 15")
    fig.update_layout(**chart_layout(350, margin=dict(l=150, r=26, t=58, b=34)), showlegend=False)
    fig.update_xaxes(tickformat=".3s", automargin=True)
    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG, key="track-stream-rankings")


def render_artist_performance(data):
    records = data[["artist_list", "streams", "week_end", "track_id"]].explode("artist_list").rename(columns={"artist_list": "artist"})
    records = records[records["artist"].notna() & records["artist"].ne("")]
    artists = records.groupby("artist", as_index=False).agg(
        streams=("streams", "sum"), observed_tracks=("track_id", "nunique"), chart_weeks=("week_end", "nunique")
    )
    top = artists.nlargest(15, "streams").sort_values("streams", ascending=False)
    if top.empty:
        st.info("No artist totals are available under the current filters.")
        return
    st.markdown("#### Ranked artists")
    display = top.rename(columns={
        "artist": "Credited artist", "streams": "Reported streams",
        "observed_tracks": "Distinct tracks", "chart_weeks": "Chart weeks",
    })[["Credited artist", "Reported streams", "Distinct tracks", "Chart weeks"]]
    st.dataframe(display, width="stretch", height="content", hide_index=True, key="artist-performance-table", column_config={
        "Reported streams": st.column_config.NumberColumn(format="%,.0f"),
        "Distinct tracks": st.column_config.NumberColumn(format="%,.0f"),
        "Chart weeks": st.column_config.NumberColumn(format="%,.0f"),
    })
    if len(top) < 2:
        st.caption("A ranking chart is omitted because only one artist is present in this selection.")
        return
    chart_data = top.sort_values("streams")
    fig = px.bar(chart_data, x="streams", y="artist", orientation="h", color_discrete_sequence=[ACCENT_BLUE],
                 hover_data={"observed_tracks": True, "chart_weeks": True, "streams": ":,.0f"},
                 labels={"streams": "Reported streams (sum)", "artist": "Credited artist",
                         "observed_tracks": "Distinct chart track IDs", "chart_weeks": "Observed chart weeks"},
                 title="Reported streams by artist · Top 15")
    fig.update_layout(**chart_layout(350, margin=dict(l=145, r=26, t=58, b=34)), showlegend=False)
    fig.update_xaxes(tickformat=".3s", automargin=True)
    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG, key="artist-stream-rankings")
    st.caption("Artist credit strings are split on common separators; collaboration credits can contribute to each listed artist.")


def render_overview(matches, observations, full_observations=None):
    st.session_state["gami_artwork_audit"] = {}
    country_observations, global_observations = split_global_markets(observations)
    section_heading(
        "LIVE FILTER / CHART VISIBILITY",
        "Your current research view",
        "These counts respond to the date and market filters. The five full-workbook totals remain in the welcome panel above.",
    )
    render_kpi_grid([
        ("Country markets", f"{country_observations['market_name'].nunique():,}", "With matched observations in this view", "◎"),
        ("Country observations", f"{len(country_observations):,}", "Song × market × snapshot rows", "▦"),
        ("GLOBAL observations", f"{len(global_observations):,}", "Kept separate from countries", "◉"),
        ("Dates represented", f"{observations['week_end'].nunique():,}", "Matched snapshot dates in this view", "◷"),
    ], columns=3)
    catalogue = build_music_catalogue(matches, observations)
    in_view = catalogue.loc[catalogue["chart_observations"].gt(0)]
    featured = in_view.sort_values(["country_markets", "chart_observations", "display_title"], ascending=[False, False, True]).head(4)
    section_heading(
        "FEATURED / VALIDATED MATCHES",
        "Afrobeats tracks in focus",
        "Cards are selected by observed country-chart presence under the current filters. Cover art is shown only after an exact title and full credited-artist match to an iTunes song result; otherwise the card uses a designed placeholder.",
    )
    render_track_collection(
        "Featured Afrobeats",
        "Widest country-chart presence in this view",
        featured,
        metric="chart_observations",
        metric_label="country observations",
        limit=4,
    )
    global_radar = catalogue.loc[catalogue["global_observations"].gt(0)].sort_values(
        ["global_observations", "display_title"], ascending=[False, True]
    )
    render_track_collection(
        "Global Afrobeats Radar",
        "GLOBAL chart observations · separate entry",
        global_radar,
        metric="global_observations",
        metric_label="GLOBAL observations",
        limit=4,
    )
    render_artwork_audit()
    st.caption("Spotify chart appearances are visibility in the validated sample; they are not total listeners, revenue, profitability, or market size.")
    section_heading("MARKET VIEW / COUNTRY PRESENCE", "Where the matched tracks appear", "The map and ranked markets below show country-chart presence. GLOBAL remains outside the country rankings.")
    summary = build_research_market_summary(country_observations)
    map_column, ranking_column = st.columns([1.35, 1], gap="medium")
    with map_column:
        with st.container(border=True):
            panel_heading("Country visibility map", "Matched chart observations")
            st.markdown('<div class="panel-copy">Geographic distribution of validated song–artist presence. GLOBAL is reported in its own card.</div>', unsafe_allow_html=True)
            render_market_map(country_observations)
    with ranking_column:
        with st.container(border=True):
            panel_heading("Leading markets", "Ranked by matched-song breadth")
            st.markdown('<div class="panel-copy">Distinct validated song–artist combinations present under the current filters.</div>', unsafe_allow_html=True)
            render_market_rank_cards(summary, limit=6)
    if not summary.empty:
        leader = summary.sort_values(["matched_song_artist_pairs", "song_market_snapshot_observations"], ascending=False).iloc[0]
        st.markdown(
            f'<div class="insight-card"><span class="eyebrow">RESEARCH READOUT</span><br>'
            f'<strong>{escape(str(leader["market_name"]))}</strong> has the broadest observed matched-song footprint in the current selection '
            f'({int(leader["matched_song_artist_pairs"]):,} combinations across {int(leader["weeks_with_presence"]):,} snapshot dates). '
            'This is chart visibility within the workbook sample, not a measure of listening demand or market size.</div>',
            unsafe_allow_html=True,
        )


def render_global(observations):
    country_observations, global_observations = split_global_markets(observations)
    section_heading(
        "MARKET INTELLIGENCE / TIMELINE",
        "How matched-song visibility changes over snapshots",
        "Country-market presence is shown as a date-based trend. The GLOBAL chart remains an independent reporting line.",
    )
    render_kpi_grid([
        ("Country observations", f"{len(country_observations):,}", "Current filter scope", "▦"),
        ("GLOBAL observations", f"{len(global_observations):,}", "Kept separate from countries", "◉"),
        ("Snapshot dates", f"{observations['week_end'].nunique():,}", "Dates represented in selection", "◷"),
    ], columns=3)
    render_matched_presence_trend(observations)


def render_country(observations):
    country_observations, global_observations = split_global_markets(observations)
    summary = build_research_market_summary(country_observations)
    section_heading(
        "MARKET INTELLIGENCE / COUNTRY VIEW",
        "Compare chart presence by country",
        "Ranked chart observations and song breadth describe visibility in this matched sample; they do not estimate market size.",
    )
    render_kpi_grid([
        ("Countries with presence", f"{summary['market_name'].nunique():,}", "Current filter scope", "◎"),
        ("Country observations", f"{len(country_observations):,}", "Matched song × country × date", "▤"),
        ("GLOBAL observations", f"{len(global_observations):,}", "Separate chart entry", "◉"),
    ], columns=3)
    if summary.empty:
        st.info("No matched-song country-market observations match the current filters.")
    else:
        chart_column, rank_column = st.columns([1.35, .9], gap="medium")
        with chart_column:
            with st.container(border=True):
                panel_heading("Country comparison", "Top 12 markets")
                st.markdown('<div class="panel-copy">Number of distinct matched song–artist combinations observed in each country.</div>', unsafe_allow_html=True)
                render_research_market_chart(
                    summary, "matched_song_artist_pairs", "Distinct matched combinations by country",
                    chart_key="country-matched-combinations", limit=12,
                )
        with rank_column:
            with st.container(border=True):
                panel_heading("Leading market cards", "Pairs · observations · dates")
                render_market_rank_cards(summary, limit=5)
        display = summary.rename(columns={
            "market_name": "Country market",
            "matched_song_artist_pairs": "Matched song–artist combinations",
            "song_market_snapshot_observations": "Song–market–snapshot observations",
            "weeks_with_presence": "Snapshots with presence",
            "median_best_rank": "Median best rank",
            "mean_best_rank": "Mean best rank",
            "total_streams": "Supplied streams sum",
        })[["Country market", "Matched song–artist combinations", "Song–market–snapshot observations",
           "Snapshots with presence", "Median best rank", "Mean best rank", "Supplied streams sum"]]
        with st.container(border=True):
            panel_heading("Country comparison table", "All countries in current selection")
            st.dataframe(display, width="stretch", height="content", hide_index=True, key="country-research-table", column_config={
                "Matched song–artist combinations": st.column_config.NumberColumn(format="%,.0f"),
                "Song–market–snapshot observations": st.column_config.NumberColumn(format="%,.0f"),
                "Snapshots with presence": st.column_config.NumberColumn(format="%,.0f"),
                "Median best rank": st.column_config.NumberColumn(format="%.1f"),
                "Mean best rank": st.column_config.NumberColumn(format="%.1f"),
                "Supplied streams sum": st.column_config.NumberColumn(format="%,.0f"),
            })
    global_summary = build_research_market_summary(global_observations)
    st.markdown('<div class="eyebrow" style="margin:1rem 0 .3rem">SEPARATE REPORTING LINE</div>', unsafe_allow_html=True)
    if global_summary.empty:
        with st.container(border=True):
            panel_heading("GLOBAL chart entry", "Not in country rankings")
            st.info("No GLOBAL chart observations match the current filters.")
    else:
        row = global_summary.iloc[0]
        with st.container(border=True):
            panel_heading("GLOBAL chart entry", "Shown independently of countries")
            render_kpi_grid([
                ("Matched pairs", f"{int(row['matched_song_artist_pairs']):,}", "GLOBAL chart", "♫"),
                ("Chart observations", f"{int(row['song_market_snapshot_observations']):,}", "GLOBAL chart entry", "▤"),
                ("Snapshots present", f"{int(row['weeks_with_presence']):,}", "GLOBAL chart dates", "◷"),
            ], columns=3)
    st.caption("Appearances measure chart visibility. Supplied stream sums are not listener counts, revenue, or market size; stream counting scope is not defined by this comparison.")


def render_tracks(data):
    section_heading(
        "CATALOGUE / SPOTIFY TOP 200",
        "Track and artist performance",
        "Rankings use supplied Spotify chart stream values under the active date and market filters. Collaborative credits are counted for each credited artist.",
    )
    track_count = data.loc[data["track_id"].ne("") , "track_id"].nunique()
    artist_count = len({artist for credits in data["artist_list"] for artist in credits})
    render_kpi_grid([
        ("Chart observations", f"{len(data):,}", "Under active filters", "▤"),
        ("Distinct Spotify tracks", f"{track_count:,}", "Track IDs in selection", "♫"),
        ("Credited artists", f"{artist_count:,}", "Split from chart credits", "◈"),
    ], columns=3)
    track_column, artist_column = st.columns(2, gap="large")
    with track_column:
        with st.container(border=True):
            panel_heading("Track performance", "Ranked by supplied streams")
            st.markdown('<div class="panel-copy">Totals sum the source streams field across selected track and market rows. Its counting window remains unconfirmed.</div>', unsafe_allow_html=True)
            render_track_rankings(data)
    with artist_column:
        with st.container(border=True):
            panel_heading("Artist performance", "Collaborative credits included")
            st.markdown('<div class="panel-copy">Credited artists inherit the chart rows for each collaboration. Artist totals are not additive.</div>', unsafe_allow_html=True)
            render_artist_performance(data)
    st.markdown('<div class="insight-card">These are Spotify Top 200 dataset-wide rankings. The separate workbook-based Afrobeats section uses the 57 validated song–artist combinations matched to the Official UK Afrobeats Chart.</div>', unsafe_allow_html=True)


def build_matched_artist_summary(observations):
    columns = ["artist", "matched_song_artist_pairs", "credited_song_market_snapshots", "country_markets"]
    if observations.empty:
        return pd.DataFrame(columns=columns)
    records = observations[["artist_list", "song_artist_key", "cc", "week_end"]].explode("artist_list")
    records = records.rename(columns={"artist_list": "artist"})
    records = records.loc[records["artist"].notna() & records["artist"].ne("")]
    records = records.drop_duplicates(["artist", "song_artist_key", "cc", "week_end"])
    records["market_name"] = records["cc"].astype(str).str.upper()
    country_records, _ = split_global_markets(records)
    summary = country_records.groupby("artist", as_index=False).agg(
        matched_song_artist_pairs=("song_artist_key", "nunique"),
        credited_song_market_snapshots=("song_artist_key", "size"),
        country_markets=("cc", "nunique"),
    )
    return summary.sort_values(
        ["matched_song_artist_pairs", "credited_song_market_snapshots", "artist"],
        ascending=[False, False, True],
    )


def render_afrobeats(matches, observations):
    st.session_state["gami_artwork_audit"] = {}
    country_observations, global_observations = split_global_markets(observations)
    section_heading(
        "DISCOVERY / VALIDATED UK CHART MATCHES",
        "Artists and tracks in the Afrobeats catalogue",
        "Browse confirmed song–artist matches, their country-chart presence, and credited artist activity. No biographies or audience measures are inferred.",
    )
    st.markdown(
        '<div class="notice"><strong>Research status:</strong> 57 normalized song–artist combinations are matched to the Official UK Afrobeats Chart. '
        'This is a UK genre-chart signal, not an independent or universal classification, and the catalogue is not complete or representative.</div>',
        unsafe_allow_html=True,
    )
    artist_names = {artist for values in matches["artists"].apply(split_artists) for artist in values}
    render_kpi_grid([
        ("Validated song–artist pairs", f"{len(matches):,}", "Full workbook · confirmed chart matches", "♫"),
        ("Spotify IDs grouped", format_total(matches["spotify_id_count"].sum(min_count=1)), "Full workbook · version grouping retained", "◉"),
        ("Credited artist names", f"{len(artist_names):,}", "Distinct credited names in catalogue", "◈"),
        ("Country markets", f"{country_observations['market_name'].nunique():,}", "Current date and market filters", "▦"),
        ("Country observations", f"{len(country_observations):,}", "Current date and market filters", "◎"),
    ], columns=5)
    render_kpi_grid([
        ("GLOBAL observations", f"{len(global_observations):,}", "Separate chart entry · active filters", "◎"),
    ], columns=1)
    st.caption("Artist and track panels use country observations. GLOBAL remains outside country artist rankings. Collaborative credits appear for each credited artist and are not additive.")

    catalogue = build_music_catalogue(matches, observations)
    country_tracks = catalogue.loc[catalogue["chart_observations"].gt(0)]
    section_heading("PLAYLIST SHELVES / FILTERED SAMPLE", "Browse the matched catalogue", "Each shelf uses the validated workbook matches. Collection labels are browsing groupings, not commercial rankings or claims of audience growth.")
    render_track_collection(
        "Global Afrobeats Radar",
        "GLOBAL chart visibility · current filter scope",
        catalogue.loc[catalogue["global_observations"].gt(0)].sort_values(["global_observations", "display_title"], ascending=[False, True]),
        metric="global_observations", metric_label="GLOBAL observations",
    )
    render_track_collection(
        "Emerging Afrobeats",
        "Discovery shelf · validated matches, not a breakout ranking",
        country_tracks.sort_values(["last_seen", "display_title"], ascending=[False, True]),
        metric="chart_observations", metric_label="country observations",
    )
    render_track_collection(
        "International Chart Presence",
        "Sorted by distinct country markets observed",
        country_tracks.sort_values(["country_markets", "chart_observations", "display_title"], ascending=[False, False, True]),
        metric="chart_observations", metric_label="country observations",
    )
    render_track_collection(
        "Top Matched Tracks",
        "Sorted by country song–market–snapshot observations",
        country_tracks.sort_values(["chart_observations", "display_title"], ascending=[False, True]),
        metric="chart_observations", metric_label="country observations",
    )
    render_artwork_audit()

    artists = build_matched_artist_summary(country_observations)
    section_heading("ARTIST DISCOVERY / CREDITED PERFORMANCE", "Artists across the matched catalogue", "Cards show credited workbook artists and supported chart-presence metrics. Initials are design markers, not artist portraits.")
    render_artist_discovery_cards(artists, limit=6)

    chart_tracks, chart_artists = st.columns(2, gap="medium")
    with chart_tracks:
        with st.container(border=True):
            panel_heading("Track performance", "Country chart observations")
            if len(country_tracks) < 2:
                if country_tracks.empty:
                    st.info("No matched country-chart observations for tracks under the current filters.")
                else:
                    row = country_tracks.iloc[0]
                    st.metric(str(row["display_title"]), f"{int(row['chart_observations']):,} country observations")
                    st.caption("A ranking chart is omitted because only one matched combination remains.")
            else:
                top_tracks = country_tracks.nlargest(12, "chart_observations").sort_values("chart_observations", ascending=True).copy()
                top_tracks["track_label"] = top_tracks["display_title"] + " · " + top_tracks["artists"]
                fig = px.bar(
                    top_tracks, x="chart_observations", y="track_label", orientation="h", text="chart_observations",
                    color_discrete_sequence=[ACCENT_TURQUOISE],
                    labels={"chart_observations": "Country chart observations", "track_label": "Song · credited artist"},
                    hover_data={"country_markets": True, "snapshot_dates": True, "chart_observations": ":,.0f"},
                )
                fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
                fig.update_layout(**chart_layout(350, margin=dict(l=170, r=42, t=40, b=38)), showlegend=False)
                fig.update_xaxes(tickformat=",d", automargin=True)
                fig.update_yaxes(title=None, automargin=True)
                st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG, key="validated-track-performance")
    with chart_artists:
        with st.container(border=True):
            panel_heading("Artist performance", "Credited country observations")
            if len(artists) < 2:
                if artists.empty:
                    st.info("No matched country-chart observations for artists under the current filters.")
                else:
                    st.metric(str(artists.iloc[0]["artist"]), f"{int(artists.iloc[0]['credited_song_market_snapshots']):,} observations")
                    st.caption("A ranking chart is omitted because only one credited artist has observations.")
            else:
                top_artists = artists.head(12).sort_values("credited_song_market_snapshots", ascending=True)
                fig = px.bar(
                    top_artists, x="credited_song_market_snapshots", y="artist", orientation="h",
                    text="credited_song_market_snapshots", color_discrete_sequence=[ACCENT_PURPLE],
                    labels={"credited_song_market_snapshots": "Credited country observations", "artist": "Credited artist"},
                    hover_data={"matched_song_artist_pairs": True, "country_markets": True},
                )
                fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
                fig.update_layout(**chart_layout(350, margin=dict(l=130, r=42, t=40, b=38)), showlegend=False)
                fig.update_xaxes(tickformat=",d", automargin=True)
                fig.update_yaxes(title=None, automargin=True)
                st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG, key="validated-artist-performance")

    with st.expander(f"Full validated match catalogue · {len(matches):,} song–artist pairs"):
        catalog = matches.sort_values(["display_title", "artists"]).rename(columns={
            "display_title": "Song",
            "artists": "Credited artists",
            "spotify_id_count": "Spotify IDs grouped",
            "release_dates": "Release dates in shortlist",
            "version_review_required": "Version review required",
        })[["Song", "Credited artists", "Spotify IDs grouped", "Release dates in shortlist", "Version review required"]]
        st.dataframe(catalog, width="stretch", height="content", row_height=38, hide_index=True, key="validated-match-catalog", column_config={
            "Song": st.column_config.TextColumn(width="medium"),
            "Credited artists": st.column_config.TextColumn(width="large"),
            "Spotify IDs grouped": st.column_config.NumberColumn(width="small", format="%d"),
            "Release dates in shortlist": st.column_config.TextColumn(width="medium"),
            "Version review required": st.column_config.TextColumn(width="small"),
        })
        st.caption("Ten combinations contain multiple Spotify IDs. They are grouped for market counting; exact recording/version equivalence was not independently confirmed.")


def render_track_market_charts(observations, matches):
    st.markdown("#### Country visibility for one matched song–artist combination")
    if matches.empty:
        st.info("No validated song–artist combinations are available in the workbook.")
        return

    matches = matches.sort_values(["display_title", "artists"])
    labels = dict(zip(matches["song_artist_key"], matches["display_title"] + " · " + matches["artists"]))
    song_artist_key = st.selectbox(
        "Select a matched song–artist combination",
        matches["song_artist_key"].tolist(),
        format_func=lambda value: labels[value],
        key="growth-validated-song-selector",
    )
    selected = matches.loc[matches["song_artist_key"].eq(song_artist_key)].iloc[0]
    selected_observations = observations.loc[observations["song_artist_key"].eq(song_artist_key)]
    country_observations, global_observations = split_global_markets(selected_observations)
    st.markdown(f"**{selected['display_title']}**")
    st.caption(selected["artists"])
    total_col, global_col = st.columns(2)
    total_col.metric("Selected song–market–snapshot observations", f"{len(country_observations):,}")
    global_col.metric("GLOBAL chart observations", f"{len(global_observations):,}")
    if selected_observations.empty:
        st.info("No matching chart observations for this song under the current date and market filters.")
        return
    if country_observations.empty:
        st.info("No country-market observations for this song under the current filters. GLOBAL remains separate.")
        return

    country_counts = country_observations.groupby("market_name", as_index=False).size().rename(
        columns={"size": "Song–market–snapshot observations"}
    ).sort_values("Song–market–snapshot observations", ascending=False)
    if len(country_counts) == 1:
        market = country_counts["market_name"].iloc[0]
        count = int(country_counts["Song–market–snapshot observations"].iloc[0])
        st.metric(f"Country market · {market}", f"{count:,} observations")
        st.caption("A country chart is omitted because this combination appears in only one country market under the current filters.")
        return

    st.markdown("##### Song–market–snapshot observations by country")
    chart_data = country_counts.sort_values("Song–market–snapshot observations")
    fig = px.bar(
        chart_data, x="Song–market–snapshot observations", y="market_name", orientation="h",
        text="Song–market–snapshot observations", color_discrete_sequence=[ACCENT_GOLD],
        labels={"Song–market–snapshot observations": "Song–market–snapshot observations", "market_name": "Country market"},
    )
    fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_layout(
        **chart_layout(max(300, min(390, 25 * len(country_counts) + 120)), margin=dict(l=140, r=42, t=54, b=36)),
        showlegend=False,
    )
    fig.update_xaxes(tickformat=",d", automargin=True)
    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG, key="growth-validated-song-market-chart")


def render_opportunities(observations, early_latest, shortlist, matches, selected_markets):
    section_heading(
        "PRELIMINARY SCREEN / WORKBOOK PRIORITIES",
        "Growth opportunities",
        "Workbook-ranked international markets are presented alongside a separate Nigeria domestic benchmark and a separate GLOBAL chart line.",
    )
    st.warning(
        "PRELIMINARY MARKET SCREEN: The workbook covers 57 song–artist combinations matched to the Official UK Afrobeats Chart. "
        "Its shortlist supports research prioritization only; it is not a representative genre catalogue or validated market-size ranking. "
        "Chart visibility does not equal total listening demand, revenue, profitability, audience size, or market size."
    )

    selected_shortlist = shortlist.loc[shortlist["Market"].isin(selected_markets)].sort_values("Priority").copy()
    international = selected_shortlist.loc[~selected_shortlist["Market"].astype(str).str.casefold().eq("nigeria")].copy()
    nigeria_shortlist = selected_shortlist.loc[selected_shortlist["Market"].astype(str).str.casefold().eq("nigeria")]
    section_heading("INTERNATIONAL / WORKBOOK SHORTLIST", "Prioritized international markets", "Priority order and metrics below are copied from the validated workbook; this is a screening list, not a market-size estimate.")
    if international.empty:
        st.info("No international workbook-shortlist markets match the current sidebar market filter.")
    else:
        opportunity_columns = st.columns(3, gap="small")
        for index, (_, row) in enumerate(international.head(6).iterrows()):
            with opportunity_columns[index % 3]:
                render_opportunity_card(row)
        with st.container(border=True):
            panel_heading("International shortlist register", "Workbook values · full 37-date comparison")
            display_international = international.rename(columns={"Market": "International market"})
            st.dataframe(display_international, width="stretch", height="content", hide_index=True, key="validated-opportunity-shortlist", column_config={
                "Priority": st.column_config.NumberColumn(format="%d"),
                "Matched songs": st.column_config.NumberColumn(format="%,.0f"),
                "Chart appearances": st.column_config.NumberColumn(format="%,.0f"),
                "Weeks present": st.column_config.NumberColumn(format="%,.0f"),
                "Median best rank": st.column_config.NumberColumn(format="%.1f"),
            })

    section_heading("DOMESTIC BENCHMARK", "Nigeria", "Shown separately from international shortlist entries. Values describe chart visibility in the workbook sample.")
    if not nigeria_shortlist.empty:
        with st.container(border=True):
            panel_heading("Nigeria · domestic benchmark", "Workbook shortlist values")
            render_opportunity_card(nigeria_shortlist.iloc[0], label="Nigeria")
    else:
        nigeria_observations = observations.loc[observations["market_name"].astype(str).str.casefold().eq("nigeria")]
        nigeria_summary = build_research_market_summary(nigeria_observations)
        if nigeria_summary.empty:
            st.info("Nigeria is outside the current market selection or has no observations under the current date filter.")
        else:
            row = nigeria_summary.iloc[0]
            with st.container(border=True):
                panel_heading("Nigeria · domestic benchmark", "Current observation filter")
                render_kpi_grid([
                    ("Matched songs", f"{int(row['matched_song_artist_pairs']):,}", "Nigeria country chart", "♫"),
                    ("Chart observations", f"{int(row['song_market_snapshot_observations']):,}", "Selected dates", "▤"),
                    ("Dates present", f"{int(row['weeks_with_presence']):,}", "Selected dates", "◷"),
                ], columns=3)
                st.caption("A current-filter comparison only; workbook shortlist priority metrics are not inferred for this market.")

    st.caption("The workbook opportunity shortlist and early/latest comparisons use the full 37-date period. Sidebar dates affect the observation-based selected-track chart; market selection limits which country rows are displayed.")

    section_heading("BREADTH CHANGE / DESCRIPTIVE", "First 12 versus latest 12 snapshots", "Change is in distinct matched song–artist combinations present; it is not a listener-growth measure.")
    all_country_changes = early_latest.loc[
        ~early_latest["market_code"].astype(str).str.casefold().eq("global")
        & early_latest["market_name"].isin(selected_markets)
    ].copy()
    nigeria_change = all_country_changes.loc[all_country_changes["market_name"].astype(str).str.casefold().eq("nigeria")]
    international_changes = all_country_changes.loc[~all_country_changes["market_name"].astype(str).str.casefold().eq("nigeria")].copy()
    if international_changes.empty:
        st.info("No international country comparison matches the current market filter.")
    else:
        international_changes["absolute_change"] = international_changes["change_in_song_breadth"].abs()
        international_changes = international_changes.nlargest(12, "absolute_change").drop(columns="absolute_change")
        international_changes = international_changes.sort_values(["change_in_song_breadth", "market_name"])
        with st.container(border=True):
            panel_heading("International breadth comparison", "Up to 12 largest absolute changes")
            chart_col, table_col = st.columns([1.1, .9], gap="medium")
            if len(international_changes) == 1:
                row = international_changes.iloc[0]
                with chart_col:
                    st.metric(f"{row['market_name']} · breadth change", f"{int(row['change_in_song_breadth']):+d}")
                    st.caption("A comparison chart is omitted when one international country remains.")
            else:
                with chart_col:
                    fig = px.bar(
                        international_changes, x="change_in_song_breadth", y="market_name", orientation="h",
                        color="change_in_song_breadth", color_continuous_scale=[ACCENT_PURPLE, PANEL, ACCENT_TURQUOISE],
                        text="change_in_song_breadth",
                        labels={"change_in_song_breadth": "Change in distinct matched combinations", "market_name": "International market"},
                    )
                    fig.update_traces(texttemplate="%{x:+,.0f}", textposition="outside", cliponaxis=False)
                    fig.update_layout(**chart_layout(350, margin=dict(l=125, r=45, t=36, b=36)), showlegend=False, coloraxis_showscale=False)
                    fig.update_xaxes(zeroline=True, zerolinecolor="#7C8797", automargin=True)
                    fig.update_yaxes(title=None, automargin=True)
                    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG, key="growth-early-latest-change")
            with table_col:
                display_change = international_changes.rename(columns={
                    "market_name": "International market",
                    "early_12_snapshot_songs": "First 12 snapshots",
                    "latest_12_snapshot_songs": "Latest 12 snapshots",
                    "change_in_song_breadth": "Change",
                })[["International market", "First 12 snapshots", "Latest 12 snapshots", "Change"]]
                st.dataframe(display_change, width="stretch", height="content", hide_index=True, key="validated-early-latest-table", column_config={
                    "First 12 snapshots": st.column_config.NumberColumn(format="%d"),
                    "Latest 12 snapshots": st.column_config.NumberColumn(format="%d"),
                    "Change": st.column_config.NumberColumn(format="%+d"),
                })
    if not nigeria_change.empty:
        row = nigeria_change.iloc[0]
        with st.container(border=True):
            panel_heading("Nigeria domestic benchmark · breadth change", "Same workbook comparison period")
            render_kpi_grid([
                ("First 12 snapshots", f"{int(row['early_12_snapshot_songs']):,}", "Nigeria", "◷"),
                ("Latest 12 snapshots", f"{int(row['latest_12_snapshot_songs']):,}", "Nigeria", "◷"),
                ("Breadth change", f"{int(row['change_in_song_breadth']):+d}", "Latest less first", "↗"),
            ], columns=3)
    st.caption("International and domestic comparisons describe workbook chart presence only. They do not establish audience size, commercial growth, or causal change.")

    global_changes = early_latest.loc[
        early_latest["market_code"].astype(str).str.casefold().eq("global")
        & early_latest["market_name"].isin(selected_markets)
    ]
    if not global_changes.empty:
        row = global_changes.iloc[0]
        with st.container(border=True):
            panel_heading("GLOBAL · separate chart benchmark", "Never included in country rankings")
            render_kpi_grid([
                ("First 12 snapshots", f"{int(row['early_12_snapshot_songs']):,}", "GLOBAL chart", "◷"),
                ("Latest 12 snapshots", f"{int(row['latest_12_snapshot_songs']):,}", "GLOBAL chart", "◷"),
                ("Breadth change", f"{int(row['change_in_song_breadth']):+d}", "Latest less first", "↗"),
            ], columns=3)

    section_heading("TRACK EXPLORER / FILTERED OBSERVATIONS", "Country visibility for a selected matched track", "Select one validated song–artist combination to inspect country chart observations. GLOBAL stays separate.")
    with st.container(border=True):
        render_track_market_charts(observations, matches)
    st.caption("Spotify chart appearances measure visibility in this matched sample; they do not measure total listeners, revenue, profitability, audience size, or future growth.")


def render_methodology(data, matches, research_observations):
    first = data["week_end"].min()
    last = data["week_end"].max()
    country_observations, global_observations = split_global_markets(research_observations)
    section_heading(
        "METHOD / PROVENANCE",
        "How to read this research",
        "Separate the full Spotify chart dataset from the matched workbook sample. The figures below describe coverage and visibility, not the whole Afrobeats market.",
    )
    render_kpi_grid([
        ("Spotify chart rows", f"{len(data):,}", "Full cleaned Top 200 dataset", "▤"),
        ("Spotify market codes", f"{data['cc'].nunique():,}", f"{first:%b %Y} – {last:%b %Y}", "◎"),
        ("Validated pairs", f"{len(matches):,}", "Official UK Afrobeats Chart matches", "♫"),
        ("Matched Spotify IDs", format_total(matches["spotify_id_count"].sum(min_count=1)), "IDs grouped in workbook", "◉"),
        ("Matched observations", f"{len(research_observations):,}", f"{research_observations['week_end'].nunique():,} balanced dates", "◷"),
    ], columns=5)
    st.markdown(
        '<div class="insight-card"><strong>Interpretation boundary.</strong> Spotify chart appearances are evidence of chart visibility in these supplied datasets. '
        'They are not total listeners, revenue, profitability, audience size, or total market size.</div>',
        unsafe_allow_html=True,
    )

    with st.expander("01 · Data sources and coverage", expanded=True):
        st.markdown("### DATA PREPARATION")
        st.markdown(
            f"The Spotify Top 200 file `{DATA_FILE.relative_to(PROJECT_DIR)}` contains **{len(data):,} track–market–snapshot rows** "
            f"across **{data['cc'].nunique():,} market codes**, covering **{first:%Y-%m-%d} to {last:%Y-%m-%d}**. "
            "Each source row is one track in one market on one chart date. The existing cleaning and inspection scripts validate the prepared file; "
            "the dashboard retains those rows for the Spotify-wide views.\n\n"
            f"The validated workbook contributes **{len(research_observations):,} matched song–market–snapshot observations** on "
            f"**{research_observations['week_end'].nunique():,} dates**. The workbook uses dates with complete coverage across 38 Spotify markets. "
            f"Matched-song presence occurs in **{country_observations['market_name'].nunique():,} country markets**, plus a separate GLOBAL chart entry "
            f"({len(global_observations):,} observations in the current selection)."
        )

    with st.expander("02 · Matching and validated research sample"):
        st.markdown("### MATCHING AND RESEARCH SAMPLE")
        st.markdown(
            f"The workbook records **{len(matches):,} distinct normalized song–credited-artist combinations** matched to the Official UK Afrobeats Chart, "
            f"representing **{int(matches['spotify_id_count'].sum()):,} Spotify track IDs**. The matching process compared normalized title and credited artist "
            "between a 250-track Spotify shortlist and extracted weekly Official UK chart records (145 UK chart weeks and 2,900 records). "
            "Ten combinations contain multiple Spotify IDs; the workbook groups them to reduce duplicate-version inflation, but exact recording equivalence "
            "has not been independently confirmed.\n\n"
            "The Official UK Afrobeats Chart provides a UK chart-assigned genre signal. It is not an independent reclassification of each recording "
            "and is not a universal definition of Afrobeats. This dashboard uses the workbook’s final validated matches; the older first-20 review CSV "
            "is retained in the project but is not used for these analyses."
        )

    with st.expander("03 · Market metrics and definitions"):
        st.markdown("### MARKET ANALYSIS METRICS")
        st.markdown(
            "- **Matched song–artist combinations:** distinct normalized title and credited-artist pairs observed in a market.\n"
            "- **Song–market–snapshot observations:** matched combinations recorded in a country chart on a workbook snapshot date.\n"
            "- **Weeks with presence:** distinct snapshot dates in which at least one matched combination appeared; not all weeks between endpoints.\n"
            "- **Best rank:** the lowest numeric Spotify chart rank recorded; a lower number indicates a stronger chart position.\n"
            "- **Early/latest change:** latest 12 available workbook snapshots minus the first 12 available snapshots, measured as distinct matched combinations.\n"
            "- **Supplied stream sums:** sums of the workbook’s `streams_sum` field across matched Spotify IDs. Its counting scope is not established here."
        )

    with st.expander("04 · Limitations and interpretation"):
        st.markdown("### RESEARCH LIMITATIONS")
        st.markdown(
            "- The 57 combinations were matched from a shortlist using a UK chart reference; they are not a random or complete sample of Afrobeats releases.\n"
            "- Ten combinations include multiple Spotify IDs, and exact recording/version equivalence is not independently confirmed.\n"
            "- Spotify chart appearances measure visibility in the supplied charts, not total listeners, revenue, audience size, or total market size.\n"
            "- Supplied stream totals do not establish unique listeners or revenue, and their counting window is not confirmed.\n"
            "- Chart presence and early/latest change are descriptive. They do not prove causal growth or commercial opportunity.\n"
            "- The workbook’s opportunity shortlist is a preliminary screening judgement based on presence, persistence, rank, and early/latest change."
        )

    with st.expander("05 · Reproducibility and project files"):
        st.markdown("### RESEARCH REPRODUCIBILITY")
        st.markdown(
            "**Data and research files**\n\n"
            "- `data/spotify_top200_cleaned.csv` — full Spotify Top 200 chart observations for the Spotify-wide views.\n"
            "- `Research/Afrobeats_Capstone_Final_Research_Workbook.xlsx` — final matched research; `4. Matched Songs` holds the 57 groups, `Raw - Balanced Date Observ` holds the 939 matched observations, `Raw - Market Comparison` and `Raw - Early vs Latest` provide comparison summaries, and `6. Opportunity Shortlist` contains the workbook’s prioritization and rationale.\n"
            "- `data/spotify_data_dictionary.txt`, `data/data_inspection.txt`, and `data/spotify_data_summary.txt` — chart-field definitions and prepared-data coverage checks.\n"
            "- `data/afrobeats_first20_review.csv` and `data/afrobeats_classification_codebook.txt` — earlier pilot materials; they are not used to select this dashboard’s validated match sample.\n\n"
            "**Scripts and dashboard**\n\n"
            "- `src/clean_spotify_data.py` and `src/inspect_spotify_data.py` — clean and inspect the Spotify chart data.\n"
            "- `src/match_afrobeats_candidates.py` — candidate title and artist-credit matching workflow.\n"
            "- `app.py` — loads the prepared Spotify file and the validated research workbook and applies the dashboard filters."
        )
    st.caption("Source references for the Official UK Afrobeats Chart and IFPI industry context are listed on the workbook’s Sources & Method sheet. IFPI figures describe the recorded-music industry overall, not Afrobeats-only revenue.")


def activate_navigation(section):
    st.session_state["active_section"] = section


def render_sidebar_navigation():
    st.sidebar.markdown(
        '<div class="sidebar-brand">GLOBAL <em>AFROBEATS</em><br>MARKET INTELLIGENCE</div>'
        '<div class="equalizer" aria-hidden="true"><i style="height:8px"></i><i style="height:15px"></i>'
        '<i style="height:10px"></i><i style="height:19px"></i><i style="height:12px"></i>'
        '<i style="height:16px"></i><i style="height:7px"></i><i style="height:13px"></i></div>'
        '<div class="sidebar-tagline">Spotify chart research · Capstone project</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<div class="nav-note">Workspace</div>', unsafe_allow_html=True)
    if "active_section" not in st.session_state:
        st.session_state["active_section"] = "Overview"
    groups = [
        ("Overview", [("Overview", "◈")]),
        ("Markets", [("Global Market Performance", "◉"), ("Country Comparison", "▦")]),
        ("Music catalogue", [("Track & Artist Performance", "♫"), ("Afrobeats Artists & Tracks", "♪")]),
        ("Research", [("Growth Opportunities", "✦"), ("Data & Methodology", "ⓘ")]),
    ]
    for group, destinations in groups:
        if group != "Overview":
            st.sidebar.markdown(f'<div class="nav-note">{escape(group)}</div>', unsafe_allow_html=True)
        for label, icon in destinations:
            st.sidebar.button(
                f"{icon}  {label}",
                key=f"navigation-{label.lower().replace(' ', '-').replace('&', 'and')}",
                type="primary" if st.session_state["active_section"] == label else "secondary",
                use_container_width=True,
                on_click=activate_navigation,
                args=(label,),
            )
    current_name = str(st.session_state.get("display_name", "")).strip()
    if current_name:
        st.session_state.setdefault("display_name_editor", current_name)
        with st.sidebar.expander("Personalize this session", expanded=False):
            st.caption("Display name only — this is not an account or authentication system.")
            with st.form("display-name-editor"):
                new_name = st.text_input("Display name", max_chars=48, key="display_name_editor")
                submitted = st.form_submit_button("Save display name", width="stretch")
            if submitted:
                cleaned_name = " ".join(str(new_name or "").split()).title()
                if cleaned_name:
                    st.session_state["display_name"] = cleaned_name
                    st.rerun()
                else:
                    st.sidebar.warning("Enter a name to save this display name.")
    return st.session_state["active_section"]


def main():
    apply_theme()
    st.session_state.setdefault("display_name", "")
    if not str(st.session_state.get("display_name", "")).strip():
        st.markdown(
            '<div class="hero"><div class="eyebrow">GLOBAL AFROBEATS MARKET INTELLIGENCE · PERSONAL SESSION</div>'
            '<h1 class="welcome-heading">Welcome to your<br><span>music intelligence workspace</span></h1>'
            '<p>Explore validated chart visibility for Afrobeats across international Spotify markets. '
            'Choose a display name to begin; this is not an account or authentication system.</p></div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.subheader("Personalize your session")
            st.caption("Your display name is kept in Streamlit session state for this active session only.")
            with st.form("display-name-onboarding"):
                display_name_input = st.text_input("Display name", placeholder="For example, Teeyana", max_chars=48)
                submitted = st.form_submit_button("Continue to the dashboard", type="primary")
            if submitted:
                cleaned_name = " ".join(str(display_name_input or "").split()).title()
                if cleaned_name:
                    st.session_state["display_name"] = cleaned_name
                    st.session_state["display_name_editor"] = cleaned_name
                    st.rerun()
                else:
                    st.warning("Enter a display name to continue.")
        st.stop()

    section = render_sidebar_navigation()

    if not DATA_FILE.exists():
        show_header(section)
        st.error(f"The cleaned Spotify dataset was not found at `{DATA_FILE.relative_to(PROJECT_DIR)}`.")
        st.stop()
    if not RESEARCH_FILE.exists():
        show_header(section)
        st.error(f"The final validated research workbook was not found at `{RESEARCH_FILE.relative_to(PROJECT_DIR)}`.")
        st.stop()
    data = load_data(str(DATA_FILE), DATA_FILE.stat().st_mtime)
    if data.empty:
        show_header(section)
        st.warning("The cleaned Spotify dataset contains no observations.")
        st.stop()
    try:
        matches, full_research_observations, early_latest, shortlist = load_validated_research(
            str(RESEARCH_FILE), RESEARCH_FILE.stat().st_mtime,
        )
    except Exception as error:
        show_header(section)
        st.error(f"Unable to read the validated research workbook: {error}")
        st.stop()

    min_date = data["week_end"].min().date()
    max_date = data["week_end"].max().date()
    st.sidebar.markdown("#### Refine view")
    date_range = st.sidebar.date_input("Chart date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    market_options = sorted(data["market_name"].dropna().unique())
    selected_markets = st.sidebar.multiselect("Markets", market_options, default=market_options)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = map(pd.Timestamp, date_range)
        filtered = data[data["week_end"].between(start_date, end_date)]
    else:
        filtered = data
    filtered = filtered[filtered["market_name"].isin(selected_markets)]
    filtered_research = filter_research_observations(full_research_observations, date_range, selected_markets)
    st.sidebar.caption("Date and market filters apply to observation-based views. The workbook early/latest comparison and opportunity shortlist use the full 37-date comparison.")

    full_country_observations, _ = split_global_markets(full_research_observations)
    show_header(
        section, date_range, selected_markets, market_options,
        match_count=len(matches),
        matched_ids=int(matches["spotify_id_count"].sum(min_count=1)),
        country_markets=full_country_observations["market_name"].nunique(),
        observation_count=len(full_research_observations),
        snapshot_count=full_research_observations["week_end"].nunique(),
        display_name=st.session_state.get("display_name", ""),
    )

    if section == "Overview":
        render_overview(matches, filtered_research, full_research_observations)
    elif section == "Global Market Performance":
        render_global(filtered_research)
    elif section == "Country Comparison":
        render_country(filtered_research)
    elif section == "Track & Artist Performance":
        if filtered.empty:
            st.info("No Spotify-wide chart records match these filters.")
        else:
            render_tracks(filtered)
    elif section == "Afrobeats Artists & Tracks":
        render_afrobeats(matches, filtered_research)
    elif section == "Growth Opportunities":
        render_opportunities(filtered_research, early_latest, shortlist, matches, selected_markets)
    else:
        render_methodology(data, matches, full_research_observations)
    st.caption("GLOBAL AFROBEATS MARKET INTELLIGENCE · Workbook-validated UK chart matches · Chart visibility is not total listening or market size")
    st.caption("Created by Christiana Thomas Elumelu · GenData Data Analytics Capstone Project · 2026")


if __name__ == "__main__":
    main()
