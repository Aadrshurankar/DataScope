from io import BytesIO
from pathlib import Path
import html
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


def spreadsheet_safe(frame):
    """Prefix formula-like text so exported spreadsheets treat it as text."""
    def safe_cell(value):
        if isinstance(value, str) and value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    safe_frame = frame.copy()
    safe_frame.columns = [safe_cell(str(column)) for column in safe_frame.columns]
    for position in range(safe_frame.shape[1]):
        safe_frame.iloc[:, position] = safe_frame.iloc[:, position].astype(object).map(safe_cell)
    return safe_frame


st.set_page_config(page_title="DataScope | Dataset Insights", page_icon="📊", layout="wide")
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "day"
if "missing_values_filter" not in st.session_state:
    st.session_state.missing_values_filter = False
if "scroll_to_preview" not in st.session_state:
    st.session_state.scroll_to_preview = False

def toggle_theme():
    st.session_state.theme_mode = "night" if st.session_state.theme_mode == "day" else "day"

def show_missing_values():
    """Open the preview tab and filter it to rows containing missing values."""
    st.session_state.missing_values_filter = True
    st.session_state.search_data = ""
    st.session_state.workspace_tab = "▦ Data Preview"
    st.session_state.scroll_to_preview = True

def open_metric(index):
    """Take a clicked overview card to the relevant dataset analysis."""
    if index == 2:
        show_missing_values()
    else:
        st.session_state.missing_values_filter = False
        st.session_state.workspace_tab = "▦ Data Preview" if index < 2 else "⬡ Data Quality"

# -------------------- Styling --------------------
st.markdown("""
<style>
.stApp { background:#12101A; color:#F3EFF8; font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; overflow:hidden !important; height:100vh; color-scheme:dark; }
html, body { max-width:100%; overflow-x:hidden !important; }
header[data-testid="stHeader"] { display:none !important; height:0 !important; min-height:0 !important; }
[data-testid="stAppViewContainer"] { isolation:isolate; height:100vh; overflow:hidden; display:flex; flex-direction:column; }
[data-testid="stMain"] { margin-top:80px; height:calc(100vh - 80px); flex:0 0 auto; overflow-y:auto; overflow-x:hidden; }
.block-container { max-width:1440px; padding-top:0 !important; padding-bottom:2rem; }
[data-testid="stAppDeployButton"] { display:none !important; }
#MainMenu, footer { visibility:hidden; }

.brandbar { position:fixed; top:0; left:0; right:0; z-index:1000; display:flex; align-items:center; gap:12px;
  min-height:80px; box-sizing:border-box; width:100%; max-width:none;
  margin:0; padding:12px max(44px,calc((100vw - 1440px)/2));
  padding-left:max(110px,calc((100vw - 1440px)/2 + 66px));
  background:rgba(25,22,35,.98); border-bottom:1px solid #342C43;
  box-shadow:0 3px 14px rgba(0,0,0,.22); }
.brandlogo { width:40px; height:40px; flex:0 0 40px; display:flex; align-items:center; justify-content:center;
  border:1px solid rgba(218,174,255,.3); border-radius:11px; background:linear-gradient(145deg,#563A82,#7E3D73);
  color:#F7EFFF; font-size:20px; font-weight:800; text-decoration:none; box-shadow:0 4px 14px rgba(168,85,247,.24); }
.brandlogo svg { width:26px; height:26px; display:block; }
.brandlogo:hover { background:linear-gradient(145deg,#7049A6,#A3488F); color:#fff; box-shadow:0 5px 17px rgba(194,111,255,.34); }
.brandcopy { flex:1; min-width:0; display:flex; flex-direction:column; justify-content:center; gap:0; }
.brandname { font-size:23px; font-weight:800; letter-spacing:-.7px; color:#F5F1FA; line-height:1.1; }
.brandname span { color:#A855F7; }
.brandtag { font-size:12px; color:#B7AEC5; margin-top:1px; }
.panelhead { display:flex; align-items:center; gap:12px; margin-bottom:14px; }
.panelicon { width:42px; height:42px; flex:0 0 42px; display:flex; align-items:center; justify-content:center;
  border-radius:12px; background:#332442; border:1px solid #533B67; color:#D6A8FF; font-size:22px; font-weight:750; }
.panelicon.blue { background:#1D3835; border-color:#315C55; color:#7BD5B8; }
.paneltitle { font-size:20px; font-weight:750; color:#F3EFF8; line-height:1.2; }
.purple { color:#D49BFF; } .blueword { color:#7BD5B8; }
.sub { font-size:13px; color:#B7AEC5; margin-top:4px; line-height:1.5; }
[data-testid="stHorizontalBlock"] { align-items:stretch !important; gap:16px !important; }
[data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width:0 !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:#1B1825 !important; border:1px solid #352D43 !important;
  border-radius:14px !important; box-shadow:0 3px 12px rgba(0,0,0,.16) !important; box-sizing:border-box !important; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(.upload-card-heading),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-upload_panel),
.st-key-upload_panel { height:380px !important; min-height:380px !important; padding:0 18px !important; align-self:stretch !important; flex:1 1 auto !important; box-sizing:border-box !important; }
@media(min-width:901px) {
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.upload-card-heading),
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-upload_panel) { transform:translateX(-40px); }
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.panelicon.blue) { height:100% !important; min-height:100% !important; padding:0 !important; align-self:stretch !important; flex:1 1 auto !important; }
@media(min-width:901px) {
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.panelicon.blue) { height:510px !important; min-height:510px !important; }
}
@media(max-width:900px) {
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.upload-card-heading),
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-upload_panel),
  .st-key-upload_panel { height:380px !important; min-height:380px !important; }
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.panelicon.blue) { height:auto !important; min-height:0 !important; }
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.upload-card-heading):hover,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.panelicon.blue):hover { border-color:#574767 !important; box-shadow:0 5px 16px rgba(0,0,0,.25) !important; }
.upload-card-heading { padding-top:36px; transform:translateY(-8px); }
.upload-card-heading .panelicon { transform:translateY(-6px); }
.upload-card-spacer { height:0; }
[data-testid="stFileUploader"] { position:relative !important; width:calc(92% - 10px) !important; min-height:220px !important; margin:10px auto 14px !important;
  box-sizing:border-box !important; background:#171420 !important; border:1px dashed #6C5484 !important;
  border-radius:12px !important; padding:14px !important; transition:border-color .18s,background .18s; }
[data-testid="stFileUploader"]::after { content:"Supported formats: CSV, XLSX, XLS  |  Maximum size: 200MB"; position:absolute;
  left:14px; right:14px; bottom:12px; display:block; color:#B7AEC5; font-size:13px; line-height:1.45; }
[data-testid="stFileUploader"]:hover { background:#211A2C !important; border-color:#B879E8 !important; }
[data-testid="stFileUploader"] section { min-height:140px !important; box-sizing:border-box !important; background:transparent !important; border:0 !important; }
[data-testid="stFileUploader"] section > div { width:100% !important; display:flex !important; flex-direction:column !important; align-items:center !important; gap:8px !important; }
[data-testid="stFileUploader"] section button:not([aria-label*="Remove"]) { display:block !important; width:132px !important; min-height:46px !important; margin:6px auto 0 !important;
  padding:8px 18px !important; font-size:25px !important; font-weight:700 !important; transform:translateY(-8px); }
[data-testid="stFileUploader"] section button:not([aria-label*="Remove"]) svg { width:18px !important; height:18px !important; }
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] { display:flex !important; align-items:center !important; gap:10px !important;
  min-height:54px !important; padding:8px 10px !important; margin:4px 0 10px !important; border-radius:12px !important; box-sizing:border-box !important; }
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button,
[data-testid="stFileUploader"] button[aria-label*="Remove"] { display:flex !important; flex:0 0 36px !important; width:36px !important; min-width:36px !important;
  height:36px !important; min-height:36px !important; margin:0 0 0 auto !important; padding:0 !important; transform:none !important;
  align-items:center !important; justify-content:center !important; border-radius:9px !important; }
[data-testid="stFileUploader"] small { color:#B7AEC5 !important; }
.st-key-chart_x [data-testid="stSelectbox"], .st-key-chart_y [data-testid="stSelectbox"],
.st-key-chart_type [data-testid="stSelectbox"], .st-key-quick_number_column [data-testid="stSelectbox"],
.st-key-quick_category_column [data-testid="stSelectbox"], .st-key-quick_trend_date [data-testid="stSelectbox"],
.st-key-quick_trend_number [data-testid="stSelectbox"] { width:min(100%,300px) !important; max-width:300px !important; }
.st-key-chart_x [data-baseweb="select"], .st-key-chart_y [data-baseweb="select"],
.st-key-chart_type [data-baseweb="select"], .st-key-quick_number_column [data-baseweb="select"],
.st-key-quick_category_column [data-baseweb="select"], .st-key-quick_trend_date [data-baseweb="select"],
.st-key-quick_trend_number [data-baseweb="select"] { width:min(100%,300px) !important; max-width:300px !important; flex:0 0 min(100%,300px) !important; }
.st-key-quick_trend_date [data-testid="stSelectbox"], .st-key-quick_trend_number [data-testid="stSelectbox"] { width:min(100%,300px) !important; max-width:300px !important; }
.st-key-chart_x [role="combobox"], .st-key-chart_y [role="combobox"], .st-key-chart_type [role="combobox"],
.st-key-quick_number_column [role="combobox"], .st-key-quick_category_column [role="combobox"],
.st-key-quick_trend_date [role="combobox"], .st-key-quick_trend_number [role="combobox"] {
  min-height:38px !important; height:38px !important; max-height:38px !important; padding-top:0 !important;
  padding-bottom:0 !important; border-radius:9px !important; box-sizing:border-box !important; }
.st-key-chart_x [data-baseweb="select"] span, .st-key-chart_y [data-baseweb="select"] span,
.st-key-chart_type [data-baseweb="select"] span, .st-key-quick_number_column [data-baseweb="select"] span,
.st-key-quick_category_column [data-baseweb="select"] span { font-size:13px !important; }
.metrics { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:8px; margin:8px 0 14px; }
.metric { min-height:106px; padding:12px 10px; border-radius:12px; border:1px solid #352D43; background:#211D2B;
  display:grid; grid-template-columns:34px minmax(0,1fr); grid-template-rows:38px 1fr; align-items:center; column-gap:8px;
  overflow-wrap:anywhere; box-sizing:border-box; transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease; }
.metric:hover { transform:translateY(-2px); box-shadow:0 5px 15px rgba(0,0,0,.24); }
.st-key-overview_metrics_row [data-testid="stHorizontalBlock"] { gap:8px !important; }
.st-key-missing_values_filter_wrap { width:100% !important; }
.st-key-missing_values_filter_wrap [data-testid="stButton"] { width:100% !important; margin:0 !important; }
.st-key-missing_values_filter_wrap [data-testid="stElementContainer"]:has(style) { display:none !important; }
.st-key-missing_values_filter_wrap [data-testid="stButton"] button {
  position:relative !important; display:grid !important; grid-template-columns:34px minmax(0,1fr) !important;
  grid-template-rows:38px 1fr !important; column-gap:8px !important; align-items:center !important;
  width:100% !important; height:106px !important; min-height:106px !important; box-sizing:border-box !important; padding:12px 10px !important;
  text-align:left !important; color:#172033 !important; border:1px solid #F0D09A !important; border-top:3px solid #CF8120 !important;
  border-radius:12px !important; background:linear-gradient(145deg,#FFF0D8 0%,#FFFAF1 100%) !important;
  box-shadow:none !important; cursor:pointer !important; }
.st-key-missing_values_filter_wrap [data-testid="stButton"] button:hover {
  border-color:#CF8120 !important; background:linear-gradient(145deg,#FFE7C1 0%,#FFF6E8 100%) !important;
  box-shadow:0 5px 15px rgba(0,0,0,.24) !important; transform:translateY(-2px); }
.st-key-missing_values_filter_wrap [data-testid="stButton"] button::before {
  content:"◷"; position:absolute; top:16px; left:10px; width:30px; height:30px; display:flex;
  align-items:center; justify-content:center; border-radius:9px; background:#FFE8BE;
  color:#9A5A12; font-size:15px; }
.st-key-missing_values_filter_wrap [data-testid="stButton"] [data-testid="stMarkdownContainer"] {
  position:static !important; display:block !important; grid-column:2 !important; grid-row:1 !important;
  align-self:center !important; width:100% !important; height:auto !important; }
.st-key-missing_values_filter_wrap [data-testid="stButton"] button > div {
  position:static !important; display:block !important; grid-column:2 !important; grid-row:1 !important;
  align-self:center !important; width:100% !important; height:auto !important; text-align:left !important; }
.st-key-missing_values_filter_wrap [data-testid="stButton"] [data-testid="stMarkdownContainer"] p,
.st-key-missing_values_filter_wrap [data-testid="stButton"] button > div p {
  position:static !important; width:auto !important; min-height:0 !important; box-sizing:border-box !important; margin:0 !important; padding:0 !important;
  color:#172033 !important; font-size:14px !important; font-weight:650 !important; line-height:1.35 !important; text-align:left !important; }
.st-key-missing_values_filter_wrap [data-testid="stButton"] button::after {
  content:attr(data-missing-count); position:static !important; grid-column:1 / -1 !important; grid-row:2 !important;
  justify-self:center !important; align-self:end !important; margin-top:5px !important; color:#172033;
  font-family:inherit !important; font-size:clamp(18px,1.35vw,23px) !important; font-weight:800 !important;
  line-height:1.2 !important; font-variant-numeric:tabular-nums; text-align:center; pointer-events:none; }
.metric .ico { grid-column:1; grid-row:1; width:30px; height:30px; border-radius:9px; display:flex; align-items:center; justify-content:center; font-size:15px; margin:0; }
.metric .label { grid-column:2; grid-row:1; font-size:14px; font-weight:650; padding-left:0; color:#C2B8D0; line-height:1.35; min-height:0; overflow-wrap:anywhere; }
.metric .num { grid-column:1 / -1; grid-row:2; justify-self:center; align-self:end; font-size:clamp(18px,1.35vw,23px); line-height:1.2; font-weight:800; color:#F5F1FA; margin-top:5px; overflow-wrap:anywhere; font-variant-numeric:tabular-nums; }
.m-blue { background:linear-gradient(135deg,#303953 0%,#35445A 100%); border-color:#65789B; }
.m-blue .ico { background:linear-gradient(135deg,#455577,#3D5A70); color:#D0D0FF; }
.m-pink { background:linear-gradient(135deg,#49334B 0%,#493650 100%); border-color:#826088; }
.m-pink .ico { background:linear-gradient(135deg,#63466A,#654C70); color:#FFD0EC; }
.m-yellow { background:linear-gradient(135deg,#50402F 0%,#51403B 100%); border-color:#91734F; }
.m-yellow .ico { background:linear-gradient(135deg,#725936,#70504A); color:#FFE0A8; }
.m-green { background:linear-gradient(135deg,#29463F 0%,#2D4651 100%); border-color:#568376; }
.m-green .ico { background:linear-gradient(135deg,#3B6858,#3D6470); color:#B2F3D8; }
.m-purple { background:linear-gradient(135deg,#49313C 0%,#49344A 100%); border-color:#875C70; }
.m-purple .ico { background:linear-gradient(135deg,#674450,#644968); color:#FFD0DB; }
.m-blue:hover { border-color:#8580CC; }
.m-pink:hover { border-color:#A7659A; }
.m-yellow:hover { border-color:#B28A56; }
.m-green:hover { border-color:#5DA88D; }
.m-purple:hover { border-color:#B86D86; }
.sectiontitle { font-size:13px; font-weight:700; color:#E2D9ED; margin:12px 0 8px; }
.filegrid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:4px 10px; }
.fileitem { display:flex; gap:9px; align-items:center; padding:7px 2px; min-height:44px; min-width:0; }
.fileico { width:30px; height:30px; flex:0 0 30px; display:flex; align-items:center; justify-content:center;
  background:#2A2435; color:#CEC3DB; border-radius:9px; font-size:14px; }
.filelabel { font-size:11px; color:#B7AEC5; margin-bottom:3px; }
.filevalue { font-size:12px; color:#F3EFF8; font-weight:650; overflow-wrap:anywhere; word-break:break-word; line-height:1.35; }
.stButton>button,.stDownloadButton>button { background:linear-gradient(100deg,#9333EA,#C43F91); color:#fff; border:0; border-radius:9px; font-weight:650; }
.stButton>button:hover,.stDownloadButton>button:hover { background:linear-gradient(100deg,#7E22CE,#A92B76); color:#fff; }
.st-key-workspace_tab [role="radiogroup"] { display:flex; gap:8px; flex-wrap:nowrap; background:transparent; border-bottom:1px solid #352D43; padding:5px 0; }
.st-key-workspace_tab [role="radio"] { color:#B7AEC5 !important; font-size:14px; font-weight:600; padding:10px 6px; border-radius:0 !important; border-bottom:2px solid transparent; background:transparent !important; white-space:nowrap; }
.st-key-workspace_tab input[type="radio"], .st-key-workspace_tab [role="radio"] > div:first-child,
.st-key-workspace_tab [data-baseweb="radio"] { display:none !important; }
.st-key-workspace_tab [role="radio"][aria-checked="true"] { color:#D49BFF !important; border-bottom-color:#A855F7; }
[data-testid="stDataFrame"] { border:1px solid #51465F; border-radius:10px;
  --gdg-border-color:#665B74; --gdg-horizontal-border-color:#665B74; }
[data-testid="stDataFrame"] .glideDataEditor { --gdg-border-color:#665B74; --gdg-horizontal-border-color:#665B74; }
[data-testid="stMetric"] { background:#211D2B; padding:12px; border-radius:10px; border:1px solid #352D43; }
div[data-testid="stAlert"] { background:#292337 !important; border:1px solid #554369 !important; color:#EEE8F6 !important; }
.footer { text-align:center; border-top:1px solid #352D43; padding-top:13px; margin-top:28px; color:#B7AEC5; font-size:12px; }
.quality-hint { font-size:12px; color:#B7AEC5; font-weight:500; margin-top:3px; line-height:1.45; }
.download-card-title { font-size:16px; font-weight:750; margin:0 0 5px; }
.download-card-copy { font-size:13px; font-weight:550; line-height:1.5; color:#334155; min-height:38px; margin-bottom:10px; }
.download-card-note { font-size:12px; font-weight:500; line-height:1.45; color:#334155; margin:9px 0 0; }
[data-testid="stDownloadButton"] button, [data-testid="stDownloadButton"] button * { color:#FFFFFF !important; }
.corr-table-wrap { width:100%; overflow-x:auto; border:1px solid #514362; border-radius:10px; }
.corr-table { width:100%; border-collapse:collapse; color:#F5F1FA; background:#211D2B; font-size:14px; }
.corr-table th, .corr-table td { padding:10px 14px; border:1px solid #514362; border-bottom-width:2px; }
.corr-table th { background:#302A3C; color:#F5F1FA; font-weight:700; text-align:left; }
.corr-table td { color:#F5F1FA; text-align:right; font-variant-numeric:tabular-nums; }
.data-table-wrap { width:100%; max-height:500px; overflow:auto; border:1px solid #665B74; border-radius:10px; }
.data-table { width:100%; border-collapse:separate; border-spacing:0; color:#F5F1FA; background:#211D2B; font-size:14px; }
.data-table th, .data-table td { padding:9px 12px; border-right:1px solid #51465F; border-bottom:1.5px solid #665B74; text-align:left; }
.data-table thead th { position:sticky; top:0; z-index:1; background:#302A3C; color:#F5F1FA; font-weight:750; border-bottom:2px solid #8D80A0; }
.data-table tbody th, .data-table-wrap.no-index .data-table tbody td:first-child { background:#302A3C; color:#F5F1FA; font-weight:700; }
.data-table tr > :last-child { border-right:0; }
@media(max-width:1100px) { .metrics { grid-template-columns:repeat(3,minmax(0,1fr)); } .filegrid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media(max-width:700px) { [data-testid="stMain"] { margin-top:60px; height:calc(100vh - 60px); } .brandbar { min-height:60px; padding:8px 14px 8px 80px; margin-bottom:14px; }
  .brandlogo { width:36px; height:36px; flex-basis:36px; } .brandname { font-size:21px; }
  .metrics { grid-template-columns:repeat(2,minmax(0,1fr)); } .filegrid { grid-template-columns:1fr; }
  .paneltitle { font-size:18px; } }
@media(max-width:900px) { .upload-card-spacer { height:0; } }
.st-key-theme_toggle { position:fixed !important; top:17px; right:max(44px,calc((100vw - 1440px)/2)); z-index:1002; }
.st-key-theme_toggle button { width:44px; height:40px; min-height:40px; padding:0; border:1px solid #A855F7 !important; border-radius:11px;
  background:linear-gradient(100deg,#9333EA,#C43F91) !important; color:#FFFFFF !important; font-size:19px; }
.st-key-theme_toggle button:hover { border-color:#A855F7; filter:brightness(1.08); }
@media(max-width:700px) { .st-key-theme_toggle { top:8px; right:14px; } .st-key-theme_toggle button { width:40px; height:38px; min-height:38px; } }
</style>
""", unsafe_allow_html=True)

# -------------------- Header --------------------
st.markdown("""
<div class="brandbar" id="top">
  <a class="brandlogo" href="/" target="_self" title="Refresh DataScope" aria-label="DataScope home">
    <svg viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <rect x="6.5" y="7.5" width="26" height="33" rx="4" stroke="currentColor" stroke-width="2.5"/>
      <path d="M7 16h25M7 24h16M7 32h14M15 8v8m9-8v8m-9 8v8m-9-8h25" stroke="currentColor" stroke-width="2"/>
      <circle cx="31.5" cy="30.5" r="8.5" fill="currentColor" fill-opacity=".18" stroke="currentColor" stroke-width="2.5"/>
      <path d="m38 37 5 5" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
    </svg>
  </a>
  <div class="brandcopy">
    <div class="brandname">Data<span>Scope</span></div>
    <div class="brandtag">Your dataset, clearly understood.</div>
  </div>

</div>
""", unsafe_allow_html=True)

st.button("☀️" if st.session_state.theme_mode == "day" else "🌙",
          key="theme_toggle",
          help="Switch to dark mode" if st.session_state.theme_mode == "day" else "Switch to day mode",
          on_click=toggle_theme)

if st.session_state.theme_mode == "day":
    st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .block-container { background:#F4F6FA !important; color:#172033 !important; color-scheme:light; }
    .brandbar { background:rgba(255,255,255,.98) !important; border-color:#B8C4D6 !important; box-shadow:0 3px 14px rgba(28,40,65,.12); }
    .brandcopy { gap:0; }
    .brandname { color:#1E1B4B !important; font-size:24px; line-height:1.1; letter-spacing:-.5px; }
    .brandname span { color:#7C3AED !important; }
    .brandtag { color:#64748B !important; font-weight:500; }
    .brandlogo { background:linear-gradient(145deg,#E9D5FF,#DDD6FE) !important; border-color:#C4B5FD !important;
      color:#6D28D9 !important; box-shadow:0 3px 10px rgba(109,40,217,.14) !important; }
    .brandlogo:hover { background:linear-gradient(145deg,#DDD6FE,#C4B5FD) !important; color:#5B21B6 !important; }
    .paneltitle, .sectiontitle, .stApp p, .stApp label, .stApp [data-testid="stMarkdownContainer"] { color:#172033; }
    .stTabs [data-baseweb="tab-panel"] [data-testid="stCaptionContainer"],
    .stTabs [data-baseweb="tab-panel"] [data-testid="stCaptionContainer"] *,
    .stTabs [data-baseweb="tab-panel"] [data-testid="stText"],
    .stTabs [data-baseweb="tab-panel"] [data-testid="stText"] *,
    .stTabs [data-baseweb="tab-panel"] [data-testid="stWidgetLabel"],
    .stTabs [data-baseweb="tab-panel"] [data-testid="stWidgetLabel"] * { color:#334155 !important; }
    .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] *,
    .stApp [data-testid="stText"], .stApp [data-testid="stText"] * { color:#1F2937 !important; font-weight:550 !important; }
    .purple { color:#7C3AED !important; } .blueword { color:#0F766E !important; }
    .brandtag, .sub, .metric .label, .filelabel, .footer, .quality-hint { color:#465366 !important; }
    [data-testid="stFileUploader"]::after { color:#526176 !important; }
    .download-card-copy { color:#334155 !important; }
    .download-card-note { color:#334155 !important; }
    .corr-table-wrap { border-color:#CBD5E1; }
    .corr-table { color:#172033; background:#FFFFFF; }
    .corr-table th { background:#E9EEF7; color:#172033; }
    .corr-table th, .corr-table td { border-color:#AAB8CC; }
    .corr-table td { color:#172033; }
    .data-table-wrap { border-color:#B8C4D6; }
    .data-table { color:#172033; background:#FFFFFF; }
    .data-table th, .data-table td { border-color:#AAB8CC; }
    .data-table thead th { background:#E9EEF7; color:#172033; border-bottom-color:#AAB8CC; }
    .data-table tbody th, .data-table-wrap.no-index .data-table tbody td:first-child { background:#E9EEF7; color:#172033; }
    .stApp, .stApp * { color-scheme:light; }
    .stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stMarkdownContainer"] * { color:#172033; }
    .panelicon { background:#F1EAFE !important; border-color:#DDC9F7 !important; color:#7C3AED !important; }
    .panelicon.blue { background:#E4F5F2 !important; border-color:#B9E2D9 !important; color:#0F766E !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background:#FFFFFF !important; border-color:#B8C4D6 !important; box-shadow:0 3px 12px rgba(28,40,65,.08) !important; }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.upload-card-heading) { background:#FFFFFF !important; border:1px solid #CBD5E1 !important; }
    .metric, .m-blue, .m-pink, .m-yellow, .m-green, .m-purple { background:#F9FAFC !important; border-color:#D9E0EB !important; }
    .metric { border-radius:16px; box-shadow:0 5px 14px rgba(30,41,59,.07); }
    .m-blue { background:linear-gradient(145deg,#E7F1FF 0%,#F7FAFF 100%) !important; border:1px solid #B8D1F4 !important; border-top:3px solid #5487D6 !important; }
    .m-pink { background:linear-gradient(145deg,#F4E9FF 0%,#FCF8FF 100%) !important; border:1px solid #DFC3F5 !important; border-top:3px solid #A34CC4 !important; }
    .m-yellow { background:linear-gradient(145deg,#FFF0D8 0%,#FFFAF1 100%) !important; border:1px solid #F0D09A !important; border-top:3px solid #CF8120 !important; }
    .m-green { background:linear-gradient(145deg,#E2F7EE 0%,#F5FCF8 100%) !important; border:1px solid #B4E2CF !important; border-top:3px solid #258B68 !important; }
    .m-purple { background:linear-gradient(145deg,#FFE9EF 0%,#FFF8FA 100%) !important; border:1px solid #EEC2D0 !important; border-top:3px solid #CC5575 !important; }
    .m-blue:hover { box-shadow:0 10px 22px rgba(67,119,196,.16) !important; }
    .m-pink:hover { box-shadow:0 10px 22px rgba(163,76,196,.15) !important; }
    .m-yellow:hover { box-shadow:0 10px 22px rgba(207,129,32,.16) !important; }
    .m-green:hover { box-shadow:0 10px 22px rgba(37,139,104,.15) !important; }
    .m-purple:hover { box-shadow:0 10px 22px rgba(204,85,117,.15) !important; }
    .metric .num, .filevalue { color:#172033 !important; }
    .metric .ico, .fileico { background:#E9EDF5 !important; color:#6241A5 !important; }
    .m-blue .ico { background:#D6E7FF !important; color:#3156A3 !important; }
    .m-pink .ico { background:#ECD9FC !important; color:#853EAB !important; }
    .m-yellow .ico { background:#FFE8BE !important; color:#9A5A12 !important; }
    .m-green .ico { background:#CFF1E1 !important; color:#13785A !important; }
    .m-purple .ico { background:#F9DDE4 !important; color:#A23C58 !important; }
    [data-testid="stFileUploader"] { background:#F9FAFC !important; border-color:#BDA7D7 !important; color:#344054 !important; }
    [data-testid="stFileUploader"]:hover { background:#F9FAFC !important; border-color:#8B5CF6 !important; }
    [data-testid="stFileUploader"] section { background:transparent !important; }
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] p { color:#344054 !important; }
    [data-testid="stFileUploader"] button,
    [data-testid="stFileUploader"] button * { background:#FFFFFF !important; color:#4C1D95 !important; border-color:#C9B6DD !important; }
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] { background:#E9EEF7 !important; }
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button,
    [data-testid="stFileUploader"] button[aria-label*="Remove"] { background:#E4EAF5 !important; color:#475569 !important; border:1px solid #D3DCEB !important; }
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button *,
    [data-testid="stFileUploader"] button[aria-label*="Remove"] * { background:transparent !important; color:inherit !important; }
    [data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"],
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input, [data-testid="stTimeInput"] input { background:#FFFFFF !important; border-color:#C8D1DF !important; color:#172033 !important; }
    [data-baseweb="select"] > div { border:1px solid #475569 !important; }
    [data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] * { color:#172033 !important; }
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] { background:#FFFFFF !important; color:#172033 !important; }
    [role="option"] { color:#172033 !important; }
    [data-testid="stExpander"], [data-testid="stExpander"] details, [data-testid="stDataFrame"] { background:#FFFFFF !important; color:#172033 !important; border-color:#D9E0EB !important; }
    [data-testid="stDataFrame"], [data-testid="stDataFrame"] .glideDataEditor {
      --gdg-border-color:#B8C4D6 !important; --gdg-horizontal-border-color:#AAB8CC !important; }
    .stButton>button, .stDownloadButton>button { color:#FFFFFF !important; }
    .st-key-workspace_tab [role="radiogroup"] { border-color:#AAB8CC !important; }
    .st-key-workspace_tab [role="radio"] { color:#4B5568 !important; }
    .st-key-workspace_tab [role="radio"][aria-checked="true"] { color:#7C3AED !important; border-bottom-color:#7C3AED !important; }
    .st-key-missing_values_filter_wrap [data-testid="stButton"] button { color:#172033 !important; background:linear-gradient(145deg,#FFF0D8 0%,#FFFAF1 100%) !important; border-color:#F0D09A !important; border-top-color:#CF8120 !important; }
    .st-key-missing_values_filter_wrap [data-testid="stButton"] button::before { background:#FFE8BE !important; color:#9A5A12 !important; }
    .st-key-missing_values_filter_wrap [data-testid="stButton"] [data-testid="stMarkdownContainer"] p,
    .st-key-missing_values_filter_wrap [data-testid="stButton"] button::after { color:#172033 !important; }
    [data-testid="stDataFrame"], [data-testid="stMetric"] { background:#FFFFFF !important; border-color:#B8C4D6 !important; }
    [data-testid="stMetric"] { border:1px solid #64748B !important; }
    div[data-testid="stAlert"] { background:#EAF2FF !important; border-color:#AAB8CC !important; color:#172033 !important; }
    div[data-testid="stAlert"] * { color:#172033 !important; }
    .st-key-theme_toggle button { background:linear-gradient(145deg,#8B5CF6,#6D28D9) !important; border-color:#6D28D9 !important;
      color:#FFFFFF !important; box-shadow:0 4px 12px rgba(109,40,217,.24) !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .block-container { background:#12101A !important; color:#F3EFF8 !important; color-scheme:dark; }
    .stApp, .stApp * { color-scheme:dark; }
    .brandbar { background:rgba(25,22,35,.98) !important; border-color:#342C43 !important; }
    .stApp div[data-testid="stVerticalBlockBorderWrapper"] { background:#302B3B !important; border:1px solid rgb(255 255 255 / 87%) !important; box-shadow:0 5px 18px rgba(0,0,0,.3) !important; }
    .stApp div[data-testid="stVerticalBlockBorderWrapper"]:has(.upload-card-heading) { background:#382D43 !important; border:1px solid rgb(255 255 255 / 87%) !important; }
    .stApp div[data-testid="stVerticalBlockBorderWrapper"]:has(.panelicon.blue) { background:#2D3B46 !important; border:1px solid rgb(255 255 255 / 87%) !important; }
    .stApp div[data-testid="stVerticalBlockBorderWrapper"]:has(.upload-card-heading):hover,
    .stApp div[data-testid="stVerticalBlockBorderWrapper"]:has(.panelicon.blue):hover { border-color:rgb(255 255 255 / 87%) !important; }
    .stApp [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child [data-testid="stVerticalBlockBorderWrapper"],
    .stApp [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) [data-testid="stVerticalBlockBorderWrapper"] {
      border:1px solid rgb(255 255 255 / 87%) !important;
    }
    .stApp .st-key-upload_panel, .stApp .st-key-overview_panel {
      border:1px solid rgb(255 255 255 / 87%) !important;
      box-shadow:0 5px 18px rgba(0,0,0,.3) !important;
    }
    .stApp div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-upload_panel),
    .stApp div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-overview_panel) {
      border:1px solid rgb(255 255 255 / 87%) !important;
      box-shadow:0 5px 18px rgba(0,0,0,.3) !important;
    }
    .stApp .metric { border-width:1px !important; border-style:solid !important; border-radius:16px !important;
      box-shadow:0 5px 16px rgba(0,0,0,.18),inset 0 1px rgba(255,255,255,.035) !important; }
    .stApp .m-blue { background:linear-gradient(145deg,#263754 0%,#202A3D 100%) !important; border-color:#718DBB !important; }
    .stApp .m-pink { background:linear-gradient(145deg,#3C2C49 0%,#302438 100%) !important; border-color:#966DB0 !important; }
    .stApp .m-yellow { background:linear-gradient(145deg,#453625 0%,#342B25 100%) !important; border-color:#B28A52 !important; }
    .stApp .m-green { background:linear-gradient(145deg,#23443D 0%,#1E3437 100%) !important; border-color:#5D9D87 !important; }
    .stApp .m-purple { background:linear-gradient(145deg,#442C3A 0%,#342433 100%) !important; border-color:#A06B82 !important; }
    .stApp .metric:hover { transform:translateY(-3px); box-shadow:0 12px 24px rgba(0,0,0,.28) !important; }
    .brandname { color:#F5F8FF !important; } .brandname span { color:#78D8CB !important; }
    .brandtag, .sub, .metric .label, .filelabel, .quality-hint, .footer { color:#C2B8D0 !important; }
    .stApp .brandlogo { background:linear-gradient(145deg,#263B56,#235149) !important; border-color:#5EA99E !important;
      color:#A5F3E7 !important; box-shadow:0 4px 14px rgba(68,190,168,.2) !important; }
    .stApp .brandlogo:hover { background:linear-gradient(145deg,#315273,#2C6B5D) !important; color:#D5FFF7 !important; }
    .sectiontitle { color:#EEE7F5 !important; } .filevalue, .metric .num { color:#F8FAFC !important; }
    [data-testid="stFileUploader"], [data-testid="stExpander"], [data-testid="stExpander"] details { background:#2C2637 !important; color:#F3EFF8 !important; border-color:#927BA6 !important; }
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] small { color:#E9E1F0 !important; }
    [data-testid="stFileUploader"] button { background:#292337 !important; color:#F8FAFC !important; border:1px solid #57466D !important; }
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] { background:#252232 !important; border:1px solid #514362 !important; }
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button,
    [data-testid="stFileUploader"] button[aria-label*="Remove"] { background:#352E43 !important; color:#E9D5FF !important; border:1px solid #655477 !important; }
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button *,
    [data-testid="stFileUploader"] button[aria-label*="Remove"] * { background:transparent !important; color:inherit !important; }
    [data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"],
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input, [data-testid="stTimeInput"] input { background:#211D2B !important; border:1px solid #514362 !important; color:#F3EFF8 !important; }
    .stApp [data-baseweb="select"] > div { border:1px solid #E9E1F0 !important; }
    .stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stWidgetLabel"] *,
    .stApp [data-testid="stTextInput"] label, .stApp [data-testid="stTextInput"] label *,
    .stApp [data-testid="stSelectbox"] label, .stApp [data-testid="stSelectbox"] label *,
    .stApp [data-testid="stNumberInput"] label, .stApp [data-testid="stNumberInput"] label *,
    .stApp [data-testid="stDateInput"] label, .stApp [data-testid="stTimeInput"] label { color:#E9E1F0 !important; }
    .stApp [data-testid="stTextInput"] [data-baseweb="base-input"],
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    .stApp [data-testid="stNumberInput"] [data-baseweb="input"] > div,
    .stApp [data-testid="stDateInput"] [data-baseweb="input"] > div,
    .stApp [data-testid="stTimeInput"] [data-baseweb="input"] > div { background:#211D2B !important; border:1px solid #514362 !important; }
    .stApp [data-testid="stTextInput"] input, .stApp [data-testid="stSelectbox"] *,
    .stApp [data-testid="stNumberInput"] input, .stApp [data-testid="stDateInput"] input,
    .stApp [data-testid="stTimeInput"] input { color:#F3EFF8 !important; }
    .stApp [data-testid="stTextInput"] input::placeholder { color:#A99DB8 !important; opacity:1; }
    [data-testid="stDataFrame"], [data-testid="stMetric"] { background:#211D2B !important; border-color:#51465F !important; }
    [data-testid="stDataFrame"], [data-testid="stDataFrame"] .glideDataEditor {
      --gdg-border-color:#665B74 !important; --gdg-horizontal-border-color:#776B85 !important; }
    [data-testid="stDataFrame"] *, [data-testid="stMetric"] * { color:#F3EFF8 !important; }
    [data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"],
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input, [data-testid="stTimeInput"] input { background:#211D2B !important; border-color:#514362 !important; color:#F3EFF8 !important; }
    [data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] * { color:#F3EFF8 !important; }
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] { background:#211D2B !important; color:#F3EFF8 !important; }
    [role="option"] { color:#F3EFF8 !important; }
    .st-key-workspace_tab [role="radiogroup"] { border-color:#352D43 !important; }
    .st-key-workspace_tab [role="radio"] { color:#D5CBE3 !important; }
    .st-key-workspace_tab [role="radio"][aria-checked="true"] { color:#D49BFF !important; border-bottom-color:#A855F7 !important; }
    .st-key-missing_values_filter_wrap [data-testid="stButton"] button { color:#F8FAFC !important; background:linear-gradient(145deg,#453625 0%,#342B25 100%) !important; border-color:#B28A52 !important; border-top-color:#CF8120 !important; }
    .st-key-missing_values_filter_wrap [data-testid="stButton"] button::before { background:linear-gradient(135deg,#725936,#70504A) !important; color:#FFE0A8 !important; }
    .st-key-missing_values_filter_wrap [data-testid="stButton"] [data-testid="stMarkdownContainer"] p,
    .st-key-missing_values_filter_wrap [data-testid="stButton"] button::after { color:#F8FAFC !important; }
    .stApp [data-testid="stMarkdownContainer"] * { color:#E9E1F0 !important; }
    .stApp .brandname { color:#F8FAFC !important; } .stApp .brandname span { color:#78D8CB !important; }
    .stApp .brandlogo { color:#A5F3E7 !important; }
    .stApp .brandtag, .stApp .sub, .stApp .metric .label, .stApp .filelabel,
    .stApp .quality-hint, .stApp .footer { color:#D5CBE3 !important; }
    .stApp .download-card-copy { color:#F0EAF7 !important; }
    .stApp .download-card-note { color:#E9E1F0 !important; }
    .stApp [data-testid="stFileUploader"]::after { color:#D5CBE3 !important; }
    .stApp .purple { color:#D8B4FE !important; } .stApp .blueword { color:#6EE7C8 !important; }
    .stApp .panelicon { color:#E9D5FF !important; } .stApp .panelicon.blue { color:#7BD5B8 !important; }
    .stApp .filevalue, .stApp .metric .num { color:#F8FAFC !important; }
    .stApp .m-blue .ico { color:#C4B5FD !important; } .stApp .m-pink .ico { color:#F5B4DD !important; }
    .stApp .m-yellow .ico { color:#FFD18B !important; } .stApp .m-green .ico { color:#8CE0C2 !important; }
    .stApp .m-purple .ico { color:#FFB0C0 !important; } .stApp .fileico { color:#D5CBE3 !important; }
    .st-key-theme_toggle button { background:linear-gradient(145deg,#1E3A5F,#0F766E) !important; border-color:#5EA99E !important;
      color:#D5FFF7 !important; box-shadow:0 4px 14px rgba(68,190,168,.22) !important; }
    </style>
    """, unsafe_allow_html=True)

px.defaults.template = "plotly_white" if st.session_state.theme_mode == "day" else "plotly_dark"

def style_chart(fig):
    """Keep chart titles, axis ticks, and plotted values readable in either theme."""
    day_mode = st.session_state.theme_mode == "day"
    foreground = "#172033" if day_mode else "#F5F1FA"
    grid = "#94A3B8" if day_mode else "#514A60"
    hover_bg = "#FFFFFF" if day_mode else "#282333"
    fig.update_layout(
        font={"family":"Inter, ui-sans-serif, system-ui, sans-serif", "size":14, "color":foreground},
        title_font={"size":19, "color":foreground},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel={"bgcolor":hover_bg, "font":{"color":foreground, "size":13}},
    )
    fig.update_xaxes(title_font={"size":14, "color":foreground}, tickfont={"size":12, "color":foreground},
                     gridcolor=grid, zerolinecolor=grid, linecolor=grid)
    fig.update_yaxes(title_font={"size":14, "color":foreground}, tickfont={"size":12, "color":foreground},
                     gridcolor=grid, zerolinecolor=grid, linecolor=grid)
    fig.update_traces(textfont_color=foreground, selector={"type":"bar"})
    fig.update_traces(textfont_color=foreground,
                      colorbar={"tickfont":{"color":foreground}, "title":{"font":{"color":foreground}}},
                      selector={"type":"heatmap"})
    return fig

def style_frame(frame):
    """Give interactive tables readable cell and header colors in both modes."""
    day_mode = st.session_state.theme_mode == "day"
    foreground = "#172033" if day_mode else "#F5F1FA"
    cell_bg = "#FFFFFF" if day_mode else "#211D2B"
    header_bg = "#E9EEF7" if day_mode else "#302A3C"
    return frame.style.set_properties(**{"color":foreground, "background-color":cell_bg}).set_table_styles([
        {"selector":"th", "props":[("color",foreground), ("background-color",header_bg), ("font-weight","700"),
            ("border-bottom","2px solid #AAB8CC" if day_mode else "2px solid #8D80A0")]},
        {"selector":"td", "props":[("color",foreground), ("background-color",cell_bg),
            ("border-bottom","2px solid #AAB8CC" if day_mode else "2px solid #8D80A0")]},
        {"selector":"tbody th", "props":[("color",foreground), ("background-color",header_bg),
            ("border-bottom","2px solid #AAB8CC" if day_mode else "2px solid #8D80A0")]},
    ])

def render_table(frame, hide_index=False, max_height=500):
    """Render tables with explicit, consistent header and row-label styling."""
    index_class = "no-index" if hide_index else "has-index"
    table_html = frame.to_html(index=not hide_index, escape=True, border=0, classes="data-table")
    st.markdown(
        f'<div class="data-table-wrap {index_class}" style="max-height:{int(max_height)}px">{table_html}</div>',
        unsafe_allow_html=True,
    )

def correlation_table_html(frame):
    headers = ''.join(f'<th scope="col">{html.escape(str(col))}</th>' for col in frame.columns)
    rows = []
    for row_label, row in frame.iterrows():
        cells = []
        for value in row:
            shown = f"{float(value):.6f}" if pd.notna(value) and np.isfinite(value) else "—"
            cells.append(f'<td>{shown}</td>')
        rows.append(f'<tr><th scope="row">{html.escape(str(row_label))}</th>{"".join(cells)}</tr>')
    return '<div class="corr-table-wrap"><table class="corr-table"><thead><tr><th></th>' + headers + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'

def show_chart_with_download(fig):
    styled_fig = style_chart(fig)
    st.plotly_chart(
        styled_fig,
        use_container_width=True,
        config={
            "responsive":True,
            "displayModeBar":True,
            "displaylogo":False,
            "modeBarButtonsToAdd":["toImage"],
        },
    )

# -------------------- Upload + overview --------------------
st.markdown('<div id="upload-section"></div>', unsafe_allow_html=True)
left, right = st.columns([0.7, 1.3], gap="small")
with left:
    # Keep the upload heading, uploader and supported-format note inside one card.
    with st.container(border=True, key="upload_panel"):
        st.markdown("""
        <div class="upload-card-heading">
          <div class="panelhead">
            <div class="panelicon">↑</div>
            <div>
              <div class="paneltitle">Upload your <span class="purple">dataset</span></div>
              <div class="sub">Upload a CSV or Excel file to preview, check data quality and get instant insights.</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        uploaded = st.file_uploader("Drag and drop your CSV or Excel file here, or click Browse files",
                                    type=["csv","xlsx","xls"], key="uploaded_dataset")
        st.markdown('<div class="upload-card-spacer"></div>', unsafe_allow_html=True)

df = None
file_info = {}
if uploaded is not None:
    try:
        suffix = Path(uploaded.name).suffix.lower()
        uploaded.seek(0)
        if suffix == ".csv":
            try:
                df = pd.read_csv(uploaded)
                encoding = "UTF-8"
            except UnicodeDecodeError:
                uploaded.seek(0)
                df = pd.read_csv(uploaded, encoding="latin-1")
                encoding = "Latin-1"
            file_type = "CSV"
        elif suffix in (".xlsx", ".xls"):
            df = pd.read_excel(uploaded)
            encoding = "Excel workbook"
            file_type = suffix.lstrip(".").upper()
        else:
            raise ValueError("Please upload a CSV or Excel file.")
        file_info = {
            "File Name": uploaded.name,
            "File Type": file_type,
            "Data Shape": f"{len(df):,} × {len(df.columns):,}",
            "File Size": f"{uploaded.size/1024:.1f} KB" if uploaded.size < 1048576 else f"{uploaded.size/1048576:.2f} MB",
            "Encoding": encoding,
            "Memory Usage": f"{df.memory_usage(deep=True).sum()/1024:.1f} KB",
        }
    except Exception:
        st.error("Could not read this file. Check that it is a valid CSV or Excel file and try again.")

with right:
    # Match the upload section: one native bordered card contains the whole overview.
    with st.container(border=True, key="overview_panel"):
        st.markdown("""
        <div class="panelhead" id="overview-section">
          <div class="panelicon blue">▥</div>
          <div>
            <div class="paneltitle">Dataset <span class="blueword">Overview</span></div>
            <div class="sub">Quick summary of your uploaded dataset</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if df is None:
            metric_data = [("Rows","0","m-blue","♧"),("Columns","0","m-pink","▦"),
                           ("Missing Values","0","m-yellow","◷"),("Blank Cells","0","m-green","↧"),
                           ("Duplicate Rows","0","m-purple","▤")]
            info = [("File Name","—"),("File Type","—"),("Data Shape","—"),
                    ("File Size","—"),("Encoding","—"),("Memory Usage","—")]
        else:
            textcols = df.select_dtypes(include=["object","string","category"])
            blank_count = int(textcols.apply(lambda col: col.astype("string").str.strip().eq("").sum()).sum()) if len(textcols.columns) else 0
            metric_data = [
                ("Rows",f"{len(df):,}","m-blue","♧"),
                ("Columns",f"{len(df.columns):,}","m-pink","▦"),
                ("Missing Values",f"{int(df.isna().sum().sum()):,}","m-yellow","◷"),
                ("Blank Cells",f"{blank_count:,}","m-green","↧"),
                ("Duplicate Rows",f"{int(df.duplicated().sum()):,}","m-purple","▤"),
            ]
            info = list(file_info.items())
        with st.container(key="overview_metrics_row"):
            metric_columns = st.columns(5, gap="small")
            for metric_index, ((label, value, color, icon), metric_column) in enumerate(zip(metric_data, metric_columns)):
                with metric_column:
                    if df is None:
                        st.markdown(f'<div class="metric {color}"><div class="ico">{icon}</div><div class="label">{label}</div><div class="num">{value}</div></div>', unsafe_allow_html=True)
                    else:
                        with st.container(key=f"overview_metric_{metric_index}"):
                            st.button(f"{label} · {value}", key=f"metric_card_button_{metric_index}",
                                      help=f"Open {label.lower()} details", use_container_width=True,
                                      on_click=open_metric, args=(metric_index,))
                            card_bg = "linear-gradient(145deg,#211D2B,#292333)" if st.session_state.theme_mode == "night" else "linear-gradient(145deg,#F9FAFC,#F1F5FA)"
                            card_text = "#F5F1FA" if st.session_state.theme_mode == "night" else "#172033"
                            card_label = "#C2B8D0" if st.session_state.theme_mode == "night" else "#465366"
                            card_border = ["#65789B", "#826088", "#91734F", "#568376", "#875C70"][metric_index]
                            st.markdown(f'''<style>
                            .st-key-overview_metric_{metric_index} [data-testid="stButton"] button {{
                              position:relative; height:106px; min-height:106px; padding:12px 10px;
                              text-align:left; justify-content:flex-start; align-items:flex-start;
                              color:transparent !important; background:{card_bg} !important;
                              border:1px solid {card_border} !important; border-top:3px solid {card_border} !important;
                              border-radius:12px; box-shadow:0 5px 14px rgba(30,41,59,.07);
                            }}
                            .st-key-overview_metric_{metric_index} [data-testid="stButton"] button:hover {{ transform:translateY(-2px); box-shadow:0 10px 22px rgba(67,119,196,.16); }}
                            .st-key-overview_metric_{metric_index} [data-testid="stButton"] button p {{ font-size:0 !important; }}
                            .st-key-overview_metric_{metric_index} [data-testid="stButton"] button::before {{
                              content:"{icon}  {label}"; position:absolute; top:20px; left:10px; right:5px;
                              color:{card_label}; font-family:inherit; font-size:13px; font-weight:650; line-height:1.35; white-space:normal;
                            }}
                            .st-key-overview_metric_{metric_index} [data-testid="stButton"] button::after {{
                              content:"{html.escape(value)}"; position:absolute; left:0; right:0; bottom:14px;
                              text-align:center; color:{card_text}; font-size:clamp(18px,1.35vw,23px); font-weight:800;
                            }}
                            </style>''', unsafe_allow_html=True)
        st.markdown('<div class="sectiontitle">Basic Information</div><div style="border-top:1px solid #ded9ed;margin-bottom:7px"></div>', unsafe_allow_html=True)
        info_html = '<div class="filegrid">' + ''.join(
            f'<div class="fileitem"><div class="fileico">▤</div><div><div class="filelabel">{label}</div><div class="filevalue">{html.escape(str(value))}</div></div></div>'
            for label,value in info
        ) + '</div>'
        st.markdown(info_html, unsafe_allow_html=True)
        st.markdown('<div class="quality-hint">Data quality issues are summarized here. Open the Data Quality tab below to inspect them by column.</div>', unsafe_allow_html=True)

st.markdown('<div id="workspace-section"></div>', unsafe_allow_html=True)
st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
workspace_tabs = ["▦ Data Preview","⬡ Data Quality","▥ Quick Analysis","◉ Visualizations","▦ Correlation","↓ Download"]
if "workspace_tab" not in st.session_state:
    st.session_state.workspace_tab = workspace_tabs[0]
st.radio("Workspace sections", workspace_tabs, key="workspace_tab", horizontal=True, label_visibility="collapsed")

if df is None:
    if st.session_state.workspace_tab == workspace_tabs[0]:
        st.info("Upload a CSV or Excel file to begin exploring your dataset.")
    if st.session_state.workspace_tab == workspace_tabs[1]:
        st.info("Upload a dataset to see column-level data quality.")
    if st.session_state.workspace_tab == workspace_tabs[2]:
        st.info("Upload a dataset to see a statistical summary.")
    if st.session_state.workspace_tab == workspace_tabs[3]:
        st.info("Upload a dataset to create charts.")
    if st.session_state.workspace_tab == workspace_tabs[4]:
        st.info("Upload a dataset with at least two numeric columns to see correlation.")
    if st.session_state.workspace_tab == workspace_tabs[5]:
        st.info("Upload a dataset to download reports.")
else:
    if st.session_state.workspace_tab == workspace_tabs[0]:
        preview_title, search_col = st.columns([1, 0.7], vertical_alignment="top")
        with preview_title:
            st.markdown('<div id="data-preview"></div>', unsafe_allow_html=True)
            st.subheader("Data Preview")
            rows_control, _ = st.columns([0.32, 0.68])
            with rows_control:
                nrows = st.selectbox("Show rows", [10,25,50,100,500], index=0)
        with search_col:
            search = st.text_input("Search in data...", key="search_data")
        preview_mask = pd.Series(True, index=df.index)
        if search.strip():
            preview_mask &= df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False, regex=False)).any(axis=1)
        if st.session_state.missing_values_filter:
            preview_mask &= df.isna().any(axis=1)
            status_col, clear_col = st.columns([1, 0.3], vertical_alignment="center")
            with status_col:
                st.info("Showing only rows with one or more missing values.")
            with clear_col:
                if st.button("Clear filter", key="clear_missing_values_filter", use_container_width=True):
                    st.session_state.missing_values_filter = False
                    st.rerun()
        preview = df[preview_mask]
        if st.session_state.missing_values_filter and preview.empty:
            st.info("No rows with missing values match the current search.")
        render_table(preview.head(nrows), max_height=350)
        st.caption(f"Showing {min(nrows,len(preview)):,} rows · {len(df.columns):,} columns")
        if st.session_state.scroll_to_preview:
            st.html("""
            <script>
            (() => {
              const jumpToPreview = () => {
                const main = document.querySelector('[data-testid="stMain"]');
                const target = document.getElementById('data-preview');
                if (!main || !target) return;
                const top = main.scrollTop + target.getBoundingClientRect().top - main.getBoundingClientRect().top - 16;
                main.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
              };
              requestAnimationFrame(() => requestAnimationFrame(jumpToPreview));
            })();
            </script>
            """, unsafe_allow_javascript=True)
            st.session_state.scroll_to_preview = False
        st.subheader("Column Information")
        col_info = pd.DataFrame({
            "Column": df.columns.astype(str),
            "Data Type": df.dtypes.astype(str).values,
            "Non-null": df.notna().sum().values,
            "Unique": df.nunique(dropna=True).values,
        })
        render_table(col_info, hide_index=True)

    if st.session_state.workspace_tab == workspace_tabs[1]:
        st.subheader("Data Quality")
        textcols = df.select_dtypes(include=["object","string","category"])
        blanks_by_col = {col:int(textcols[col].astype("string").str.strip().eq("").sum()) for col in textcols.columns}
        quality = pd.DataFrame({
            "Column":df.columns.astype(str),
            "Data Type":df.dtypes.astype(str).values,
            "Missing Values":df.isna().sum().values,
            "Missing %":((df.isna().mean()*100).round(2) if len(df) else pd.Series(["—"]*len(df.columns))).values,
            "Blank Cells":[blanks_by_col.get(col,0) for col in df.columns],
            "Unique Values":df.nunique(dropna=True).values,
        })
        render_table(quality, hide_index=True)
        st.caption("Empty file cells are counted as missing. Text cells containing only spaces are counted as blank.")
        st.info(f"Duplicate rows: {int(df.duplicated().sum()):,}")
        if int(quality["Missing Values"].sum()) > 0:
            st.warning(f"Missing values found: {int(quality['Missing Values'].sum()):,}")
        else:
            st.success("No missing values found.")

    if st.session_state.workspace_tab == workspace_tabs[2]:
        st.subheader("Quick Analysis")
        numeric = df.select_dtypes(include="number").replace([np.inf, -np.inf], np.nan)
        date_series = {}
        for date_col in df.select_dtypes(include=["datetime", "datetimetz"]).columns:
            date_series[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        for date_col in df.select_dtypes(include=["object", "string"]).columns:
            raw_dates = df[date_col].dropna().astype("string")
            if raw_dates.empty or raw_dates.str.contains(r"[-/:]", regex=True).mean() < 0.7:
                continue
            parsed_dates = pd.to_datetime(df[date_col], errors="coerce", format="mixed", dayfirst=True)
            if parsed_dates.notna().sum() / len(raw_dates) >= 0.8:
                date_series[date_col] = parsed_dates

        date_cols = list(date_series)
        category_cols = [
            col for col in df.select_dtypes(include=["object", "string", "category", "bool"]).columns
            if col not in date_cols
        ]

        st.caption("A quick snapshot of what this dataset contains.")
        summary = st.columns(5)
        summary[0].metric("Rows", f"{len(df):,}")
        summary[1].metric("Columns", f"{len(df.columns):,}")
        summary[2].metric("Number columns", f"{len(numeric.columns):,}")
        summary[3].metric("Category columns", f"{len(category_cols):,}")
        summary[4].metric("Date columns", f"{len(date_cols):,}")

        st.subheader("Important numbers")
        if not numeric.empty:
            number_col = st.selectbox("Choose a number to explore", numeric.columns, key="quick_number_column")
            values = numeric[number_col].dropna()
            if values.empty:
                st.text(f"There are no finite numbers in {number_col}.")
            else:
                number_stats = st.columns(4)
                number_stats[0].metric("Total", f"{values.sum():,.2f}")
                number_stats[1].metric("Average", f"{values.mean():,.2f}")
                number_stats[2].metric("Smallest", f"{values.min():,.2f}")
                number_stats[3].metric("Largest", f"{values.max():,.2f}")
                st.text(f"For {number_col}, the average is {values.mean():,.2f}; values range from {values.min():,.2f} to {values.max():,.2f}.")
            with st.expander("See detailed statistics for all number columns"):
                render_table(numeric.describe().T.round(3))
        else:
            st.info("This dataset has no number columns to summarize.")

        st.subheader("Most common category values")
        if category_cols:
            category_col = st.selectbox("Choose a category", category_cols, key="quick_category_column")
            category_counts = df[category_col].dropna().astype("string").str.strip()
            category_counts = category_counts[category_counts.ne("")].value_counts().head(5)
            if category_counts.empty:
                st.text(f"There are no filled-in values in {category_col}.")
            else:
                top_categories = category_counts.rename_axis("Value").reset_index(name="Rows")
                category_fig = px.bar(
                    top_categories.sort_values("Rows"), x="Rows", y="Value", orientation="h",
                    text="Rows", title=f"The 5 most common values in {category_col}",
                )
                category_fig.update_layout(showlegend=False, xaxis_title="Number of rows", yaxis_title=None)
                show_chart_with_download(category_fig)
                most_common = category_counts.index[0]
                st.text(f"Most common value: {most_common} ({category_counts.iloc[0]:,} rows).")
        else:
            st.info("No text or category columns were found for a top-values summary.")

        st.subheader("Changes over time")
        if date_cols and not numeric.empty:
            trend_date_control, trend_number_control = st.columns(2, gap="medium")
            with trend_date_control:
                trend_date_col = st.selectbox("Choose a date column", date_cols, key="quick_trend_date")
            with trend_number_control:
                trend_number_col = st.selectbox("Choose a number for the trend", numeric.columns, key="quick_trend_number")
            trend_data = pd.DataFrame({
                "Date": pd.to_datetime(date_series[trend_date_col], errors="coerce", utc=True).dt.tz_convert(None),
                "Value": pd.to_numeric(df[trend_number_col], errors="coerce").replace([np.inf, -np.inf], np.nan),
            }).dropna().sort_values("Date")
            if trend_data.empty:
                st.info("There are no matching dates and numbers to show a trend.")
            else:
                trend_data = trend_data.set_index("Date").resample("M")["Value"].sum().reset_index()
                trend_fig = px.line(
                    trend_data, x="Date", y="Value", markers=True,
                    title=f"{trend_number_col} total by month",
                    labels={"Date": "Month", "Value": f"Total {trend_number_col}"},
                )
                show_chart_with_download(trend_fig)
                st.caption("Each point adds up the selected number for that month.")
                st.caption("Ambiguous text dates are interpreted day-first (DD/MM).")
        elif not date_cols:
            st.info("No date column was recognized, so a time trend cannot be shown.")
        else:
            st.info("Add a number column to the dataset to see a time trend.")

    if st.session_state.workspace_tab == workspace_tabs[3]:
        st.subheader("Visualizations")
        plot_numeric = df.select_dtypes(include="number").replace([np.inf, -np.inf], np.nan)
        numeric_cols = plot_numeric.columns[plot_numeric.notna().any()].tolist()
        if numeric_cols:
            plot_df = df.copy()
            plot_df[numeric_cols] = plot_numeric[numeric_cols]
            chart_controls = st.columns(3, gap="small")
            with chart_controls[0]:
                x = st.selectbox("Bottom axis (left to right)", numeric_cols, key="chart_x")
            with chart_controls[1]:
                y = st.selectbox("Side axis (bottom to top)", numeric_cols, index=min(1,len(numeric_cols)-1), key="chart_y")
            with chart_controls[2]:
                chart_type = st.selectbox(
                    "Choose a chart",
                    ["Scatter","Line","Bar","Histogram"],
                    format_func=lambda kind: {
                        "Scatter":"Dots · compare two numbers",
                        "Line":"Line · see how values change",
                        "Bar":"Bars · compare sizes",
                        "Histogram":"Groups · count values",
                    }[kind],
                    key="chart_type",
                )
            if chart_type == "Scatter":
                st.caption("Each dot is one row. Its place shows the two numbers for that row.")
                fig = px.scatter(plot_df, x=x, y=y, title="Each dot is one row: compare the two numbers")
            elif chart_type == "Line":
                st.caption("Follow the line from left to right. Higher points mean bigger values.")
                fig = px.line(plot_df, x=x, y=y, title=f"How {y} changes as {x} changes")
            elif chart_type == "Bar":
                st.caption("Each bar is one row. Taller bars mean bigger values.")
                fig = px.bar(plot_df, x=x, y=y, title=f"Compare {y} for each {x}")
            else:
                st.caption("Each bar counts how many rows have values in that range.")
                fig = px.histogram(plot_df, x=x, title=f"How often each {x} value appears")
            show_chart_with_download(fig)
        else:
            st.info("No columns with finite numbers were found for plotting.")

    if st.session_state.workspace_tab == workspace_tabs[4]:
        st.subheader("Correlation")
        numeric = df.select_dtypes(include="number")
        if len(numeric.columns) >= 2:
            corr = numeric.replace([np.inf, -np.inf], np.nan).corr(numeric_only=True)
            chart_corr = corr.dropna(axis=0, how="all").dropna(axis=1, how="all")
            st.info("Red means two numbers usually rise together. Blue means one may rise while the other falls. Pale colors mean no clear pattern. Numbers closer to 1 or −1 show a stronger pattern.")
            if len(chart_corr.columns) >= 2:
                corr_colors = ([[0,"#D8E9F8"],[0.5,"#F7F8FC"],[1,"#F5D6DB"]]
                               if st.session_state.theme_mode == "day" else
                               [[0,"#23466B"],[0.5,"#383440"],[1,"#75384B"]])
                fig = px.imshow(chart_corr, text_auto=".2f", color_continuous_scale=corr_colors, zmin=-1, zmax=1,
                                aspect="auto", title="How pairs of numbers move together",
                                labels={"color":"How closely they move"})
                show_chart_with_download(fig)
            else:
                st.info("A relationship heatmap needs at least two number columns with changing values.")
            st.markdown(correlation_table_html(corr), unsafe_allow_html=True)
        else:
            st.info("At least two numeric columns are required for correlation.")

    if st.session_state.workspace_tab == workspace_tabs[5]:
        st.subheader("Download Reports")
        safe_dataset = spreadsheet_safe(df)
        textcols = df.select_dtypes(include=["object", "string", "category"])
        blanks_by_col = {
            col: int(textcols[col].astype("string").str.strip().eq("").sum())
            for col in textcols.columns
        }
        quality = pd.DataFrame({
            "Column":df.columns.astype(str),
            "Data Type":df.dtypes.astype(str).values,
            "Missing Values":df.isna().sum().values,
            "Missing %":((df.isna().mean()*100).round(2) if len(df) else pd.Series(["—"]*len(df.columns))).values,
            "Blank Cells":[blanks_by_col.get(col,0) for col in df.columns],
            "Unique Values":df.nunique(dropna=True).values,
        })
        safe_quality = spreadsheet_safe(quality)
        max_excel_rows, max_excel_columns = 1_048_576, 16_384
        excel_available = len(df) + 1 <= max_excel_rows and len(df.columns) <= max_excel_columns
        overview_report = None
        excel_buffer = None
        if excel_available:
            overview_report = pd.DataFrame([{
                "Rows": len(df),
                "Columns": len(df.columns),
                "Missing Values": int(df.isna().sum().sum()),
                "Blank Cells": int(sum(blanks_by_col.values())),
                "Duplicate Rows": int(df.duplicated().sum()),
            }])
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                safe_dataset.to_excel(writer,index=False,sheet_name="Data")
                safe_quality.to_excel(writer,index=False,sheet_name="Quality Report")
                spreadsheet_safe(overview_report).to_excel(writer,index=False,sheet_name="Overview")

        download_cols = st.columns(3, gap="medium")
        with download_cols[0]:
            with st.container(border=True, key="download_dataset_card"):
                st.markdown('<div class="download-card-title">Dataset CSV</div><div class="download-card-copy">Your complete dataset, ready to open or share as a CSV file.</div>', unsafe_allow_html=True)
                st.download_button("Download dataset (CSV)", safe_dataset.to_csv(index=False).encode("utf-8"),
                                   file_name="datascope_dataset.csv", mime="text/csv", use_container_width=True)
                st.markdown('<div class="download-card-note">Formula-like text is prefixed with an apostrophe for export safety.</div>', unsafe_allow_html=True)
        with download_cols[1]:
            with st.container(border=True, key="download_quality_card"):
                st.markdown('<div class="download-card-title">Data quality CSV</div><div class="download-card-copy">Missing values, blank cells, data types, and unique-value counts by column.</div>', unsafe_allow_html=True)
                st.download_button("Download quality report (CSV)", safe_quality.to_csv(index=False).encode("utf-8"),
                                   file_name="datascope_quality_report.csv", mime="text/csv", use_container_width=True)
                st.markdown('<div class="download-card-note">Empty cells count as missing; cells containing only spaces count as blank.</div><div class="download-card-note">Formula-like text is prefixed with an apostrophe for export safety.</div>', unsafe_allow_html=True)
        with download_cols[2]:
            with st.container(border=True, key="download_excel_card"):
                st.markdown('<div class="download-card-title">Excel workbook</div><div class="download-card-copy">One workbook with Data, Quality Report, and Overview sheets.</div>', unsafe_allow_html=True)
                if excel_available:
                    st.download_button("Download Excel report", excel_buffer.getvalue(),
                                       file_name="datascope_report.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True)
                    st.markdown(f'<div class="download-card-note">Duplicate rows: {int(df.duplicated().sum()):,} (listed in the Overview sheet).</div><div class="download-card-note">Formula-like text is prefixed with an apostrophe for export safety.</div>', unsafe_allow_html=True)
                else:
                    st.warning("This dataset is larger than Excel's worksheet limit. Download the full data as CSV instead.")

st.markdown('<div class="footer">DataScope · Upload once · Preview · Data Quality · Visual Analysis</div>', unsafe_allow_html=True)
