from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st

from bizpilot.business import (
    calculate_invoice_total,
    calculate_profit,
    calculate_profit_margin,
    low_stock_report,
    parse_inventory_csv,
)


# ---------- BizPilot AI: editorial "growth studio" theme ----------
# Inspired by the structure and motion of astounddigital.com:
# a dark hero with a scrolling ticker, big confident type, numbered
# sections, count-up statistics, hover-fill cards and a dark closing band.
# The palette and copy are original to BizPilot AI.

BIZPILOT_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

/* Lets the CSS-only count-up animation tween whole numbers. */
@property --n { syntax:'<integer>'; inherits:false; initial-value:0; }

:root {
  --ink:#0a0a0f;
  --paper:#f3f2ed;
  --accent:#ff4d2e;
  --accent-2:#ff8a4c;
  --violet:#7a5cff;
  --muted:#6c6c78;
  --line:rgba(10,10,15,.10);
  --ease:cubic-bezier(.2,.8,.2,1);
}

::selection { background:var(--accent); color:#fff; }

/* ----- Base ----- */
.stApp {
  font-family:'Inter',sans-serif;
  color:var(--ink);
  background:
    radial-gradient(900px 520px at 100% -10%,rgba(255,77,46,.07),transparent 60%),
    radial-gradient(800px 520px at -10% 30%,rgba(122,92,255,.06),transparent 60%),
    var(--paper);
}
.stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp select { font-family:'Inter',sans-serif; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
  font-family:'Inter Tight','Inter',sans-serif !important;
  letter-spacing:-.03em;
  color:var(--ink);
}
.stApp h3 { font-size:26px; font-weight:700; }
[data-testid="stHeader"] { background:transparent; }
footer { visibility:hidden; }
.block-container { max-width:1400px; padding:1.2rem 2.2rem 4rem; }
hr { border-color:var(--line) !important; }

/* ----- Sidebar ----- */
section[data-testid="stSidebar"] {
  background:var(--ink);
  border-right:1px solid rgba(255,255,255,.07);
}
section[data-testid="stSidebar"] * { color:#f2f2f7; }
section[data-testid="stSidebar"] input {
  color:var(--ink) !important;
  background:#fff !important;
  border-radius:12px !important;
}
.bp-brand { display:flex; align-items:center; gap:12px; padding:6px 0 18px; }
section[data-testid="stSidebar"] .bp-logo {
  width:44px; height:44px; border-radius:14px; display:grid; place-items:center;
  color:var(--ink);
  background:linear-gradient(135deg,var(--accent),var(--accent-2));
  font:800 17px 'Inter Tight',sans-serif; letter-spacing:-.04em;
  box-shadow:0 10px 30px rgba(255,77,46,.35);
}
.bp-brand-name { font:700 20px 'Inter Tight',sans-serif; letter-spacing:-.04em; }
.bp-brand-sub { font-size:9px; letter-spacing:.24em; opacity:.55; margin-top:3px; }
.bp-nav-heading {
  font-size:10px; letter-spacing:.2em; font-weight:700;
  color:#8d8d9b; margin:4px 0 8px; text-transform:uppercase;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] > label,
section[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"],
section[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"] * {
  color:#8d8d9b !important; font-size:10px !important; font-weight:700 !important;
  letter-spacing:.2em !important; text-transform:uppercase !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] { gap:8px !important; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] {
  display:flex !important; align-items:center !important; padding:13px 14px !important;
  border-radius:14px !important; background:rgba(255,255,255,.035) !important;
  border:1px solid rgba(255,255,255,.08) !important; cursor:pointer !important;
  transition:transform .25s var(--ease),background .25s ease,border-color .25s ease !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:hover {
  transform:translateX(4px);
  background:rgba(255,255,255,.09) !important;
  border-color:rgba(255,255,255,.22) !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
  background:linear-gradient(100deg,#ff4d2e,#ff7a45) !important;
  border-color:transparent !important;
  box-shadow:0 10px 28px rgba(255,77,46,.28);
  font-weight:600;
}

/* ----- Hero ----- */
.bp-hero {
  position:relative; overflow:hidden; isolation:isolate;
  border-radius:32px; background:var(--ink); color:#fff;
  padding:54px 52px 0; margin:4px 0 0; min-height:500px;
  box-shadow:0 30px 70px rgba(10,10,15,.18);
}
.bp-grid {
  position:absolute; inset:0; z-index:-1;
  background-image:
    linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);
  background-size:64px 64px;
  -webkit-mask-image:radial-gradient(ellipse at 72% 28%,#000 0,transparent 72%);
  mask-image:radial-gradient(ellipse at 72% 28%,#000 0,transparent 72%);
  animation:bp-grid 18s linear infinite;
}
.bp-blob { position:absolute; z-index:-1; border-radius:50%; filter:blur(70px); }
.bp-blob.b1 {
  width:540px; height:540px; right:-140px; top:-190px; opacity:.8;
  background:radial-gradient(circle,#ff4d2e 0%,rgba(255,77,46,0) 68%);
  animation:bp-float1 14s ease-in-out infinite;
}
.bp-blob.b2 {
  width:600px; height:600px; left:32%; bottom:-340px; opacity:.75;
  background:radial-gradient(circle,#7a5cff 0%,rgba(122,92,255,0) 68%);
  animation:bp-float2 18s ease-in-out infinite;
}
.bp-eyebrow {
  display:inline-flex; align-items:center; gap:10px;
  font-size:11px; font-weight:600; letter-spacing:.18em; text-transform:uppercase;
  padding:9px 15px; border:1px solid rgba(255,255,255,.18); border-radius:999px;
  background:rgba(255,255,255,.06); animation:bp-rise .8s var(--ease) both;
}
.bp-live {
  width:8px; height:8px; border-radius:50%; background:var(--accent);
  animation:bp-pulse 2s infinite;
}
.bp-h1 {
  font:800 clamp(42px,6.6vw,96px)/.98 'Inter Tight',sans-serif;
  letter-spacing:-.05em; color:#fff; margin:28px 0 24px; max-width:1000px;
}
.bp-h1 .w { display:inline-block; overflow:hidden; vertical-align:top; padding-bottom:.12em; margin-bottom:-.12em; }
.bp-h1 .w > span { display:inline-block; animation:bp-word .95s var(--ease) both; }
.bp-h1 .acc {
  background:linear-gradient(90deg,#ff4d2e,#ffa35c);
  -webkit-background-clip:text; background-clip:text; color:transparent;
}
.bp-lead {
  max-width:620px; color:rgba(255,255,255,.72); font-size:16px; line-height:1.75;
  animation:bp-rise .9s .55s var(--ease) both;
}
.bp-chips { display:flex; flex-wrap:wrap; gap:10px; margin-top:26px; animation:bp-rise .9s .7s var(--ease) both; }
.bp-chips span {
  font-size:12px; font-weight:500; padding:8px 14px; border-radius:999px;
  border:1px solid rgba(255,255,255,.16); color:rgba(255,255,255,.85);
  background:rgba(255,255,255,.04);
}
.bp-marquee {
  margin:56px -52px 0; border-top:1px solid rgba(255,255,255,.14);
  overflow:hidden; white-space:nowrap; padding:17px 0;
  background:rgba(255,255,255,.025);
}
.bp-track { display:inline-flex; animation:bp-marquee 34s linear infinite; will-change:transform; }
.bp-track span {
  font-size:12px; font-weight:600; letter-spacing:.22em; text-transform:uppercase;
  color:rgba(255,255,255,.78); padding-right:30px; display:inline-flex; gap:30px;
}
.bp-track i { font-style:normal; color:var(--accent); }

/* ----- Sections ----- */
.bp-label {
  display:flex; align-items:center; gap:10px; margin:72px 0 16px;
  font-size:11px; font-weight:700; letter-spacing:.2em; text-transform:uppercase; color:var(--muted);
}
.bp-label:before { content:""; width:9px; height:9px; border-radius:2px; background:var(--accent); }
.bp-statement {
  font:600 clamp(26px,3.5vw,48px)/1.12 'Inter Tight',sans-serif;
  letter-spacing:-.035em; max-width:1020px; color:var(--ink); margin:0;
}
.bp-statement .dim { color:#8c8c99; }

/* ----- Count-up statistics ----- */
.bp-stats { display:grid; grid-template-columns:repeat(4,1fr); border-top:1px solid var(--line); margin-top:8px; }
.bp-stat { padding:26px 24px 10px 0; animation:bp-rise .8s var(--ease) both; }
.bp-stat + .bp-stat { padding-left:24px; border-left:1px solid var(--line); }
.bp-num {
  font:700 clamp(46px,5.6vw,88px)/1 'Inter Tight',sans-serif;
  letter-spacing:-.055em; color:var(--ink); font-variant-numeric:tabular-nums;
}
.bp-count {
  --n:var(--to,0);
  counter-reset:bpn var(--n);
  animation:bp-count 2s cubic-bezier(.2,.7,.2,1) .35s both;
}
.bp-count:after { content:counter(bpn); }
.bp-stat-label { font-weight:600; font-size:15px; margin-top:10px; color:var(--ink); }
.bp-stat-note { font-size:12px; color:var(--muted); margin-top:3px; }
.bp-live-note { font-size:12px; color:var(--muted); margin-top:14px; }

/* ----- Workspace cards ----- */
.bp-card {
  position:relative; overflow:hidden; isolation:isolate;
  display:flex; flex-direction:column; min-height:270px;
  background:#fff; border:1px solid var(--line); border-radius:26px; padding:26px;
  margin-bottom:12px; animation:bp-rise .8s var(--ease) both;
  transition:transform .35s var(--ease),box-shadow .35s var(--ease),border-color .35s ease;
}
.bp-card:before {
  content:""; position:absolute; inset:0; z-index:-1; background:var(--ink);
  transform:translateY(101%); transition:transform .5s var(--ease);
}
.bp-card:hover { transform:translateY(-6px); box-shadow:0 26px 50px rgba(10,10,15,.16); border-color:var(--ink); }
.bp-card:hover:before { transform:translateY(0); }
.bp-card-top { display:flex; justify-content:space-between; align-items:center; }
.bp-card-num { font:700 13px 'Inter Tight',sans-serif; letter-spacing:.12em; color:var(--accent); }
.bp-arrow {
  width:36px; height:36px; border-radius:50%; display:grid; place-items:center;
  border:1px solid var(--line); font-size:15px; color:var(--ink);
  transition:transform .4s var(--ease),background .3s ease,color .3s ease,border-color .3s ease;
}
.bp-card:hover .bp-arrow { transform:rotate(45deg); background:var(--accent); border-color:var(--accent); color:#fff; }
.bp-card-title {
  font:700 25px/1.1 'Inter Tight',sans-serif; letter-spacing:-.035em;
  margin:34px 0 10px; color:var(--ink); transition:color .3s ease;
}
.bp-card-text { font-size:14px; line-height:1.65; color:var(--muted); flex:1; transition:color .3s ease; }
.bp-tags { display:flex; flex-wrap:wrap; gap:6px; margin-top:20px; }
.bp-tags span {
  font-size:11px; font-weight:600; padding:5px 11px; border-radius:999px;
  border:1px solid var(--line); color:var(--ink); transition:color .3s ease,border-color .3s ease;
}
.bp-card:hover .bp-card-title { color:#fff; }
.bp-card:hover .bp-card-text { color:rgba(255,255,255,.7); }
.bp-card:hover .bp-tags span { color:#fff; border-color:rgba(255,255,255,.3); }

/* ----- Approach band ----- */
.bp-band {
  position:relative; overflow:hidden; isolation:isolate;
  margin-top:76px; padding:56px; border-radius:32px; background:var(--ink); color:#fff;
}
.bp-band:before {
  content:""; position:absolute; z-index:-1; right:-140px; top:-200px;
  width:500px; height:500px; border-radius:50%; filter:blur(55px);
  background:radial-gradient(circle,rgba(255,77,46,.6),transparent 68%);
  animation:bp-float1 16s ease-in-out infinite;
}
.bp-band .bp-label { color:rgba(255,255,255,.55); margin-top:0; }
.bp-band-title {
  font:700 clamp(30px,4.4vw,64px)/1.02 'Inter Tight',sans-serif;
  letter-spacing:-.045em; max-width:860px; color:#fff;
}
.bp-band-title .acc {
  background:linear-gradient(90deg,#ff4d2e,#ffa35c);
  -webkit-background-clip:text; background-clip:text; color:transparent;
}
.bp-process { display:grid; grid-template-columns:repeat(4,1fr); position:relative; margin-top:48px; }
.bp-process:before {
  content:""; position:absolute; top:11px; left:0; right:0; height:2px; background:rgba(255,255,255,.14);
}
.bp-process:after {
  content:""; position:absolute; top:11px; left:0; height:2px; width:0;
  background:linear-gradient(90deg,var(--accent),var(--violet));
  animation:bp-progress 8s linear infinite;
}
.bp-pstep { position:relative; padding-top:44px; }
.bp-pstep:before {
  content:""; position:absolute; top:0; left:0; width:24px; height:24px; border-radius:50%;
  background:var(--ink); border:2px solid rgba(255,255,255,.25); z-index:1;
  animation:bp-pdot 8s infinite; animation-delay:calc(var(--i) * 1.3s);
}
.bp-pstep-title { font:600 19px 'Inter Tight',sans-serif; letter-spacing:-.02em; color:#fff; margin-bottom:6px; }
.bp-pstep-text { font-size:13px; line-height:1.6; color:rgba(255,255,255,.62); padding-right:24px; }
.bp-foot {
  display:flex; justify-content:space-between; flex-wrap:wrap; gap:12px;
  margin-top:44px; padding-top:20px; border-top:1px solid rgba(255,255,255,.12);
  font-size:12px; color:rgba(255,255,255,.5);
}

/* ----- Page headers (inner pages) ----- */
.bp-kicker {
  display:flex; align-items:center; gap:10px; margin:8px 0 12px;
  font-size:11px; font-weight:700; letter-spacing:.2em; text-transform:uppercase; color:var(--muted);
  animation:bp-rise .6s var(--ease) both;
}
.bp-kicker:before { content:""; width:9px; height:9px; border-radius:2px; background:var(--accent); }
.bp-title {
  font:800 clamp(38px,5.2vw,72px)/1 'Inter Tight',sans-serif;
  letter-spacing:-.05em; color:var(--ink); animation:bp-rise .7s .05s var(--ease) both;
}
.bp-title:after {
  content:""; display:block; height:4px; width:72px; margin-top:18px; border-radius:3px;
  background:linear-gradient(90deg,var(--accent),var(--violet)); animation:bp-draw .9s .35s var(--ease) both;
}
.bp-sub { max-width:640px; margin:16px 0 30px; color:var(--muted); font-size:15px; line-height:1.7; animation:bp-rise .7s .15s var(--ease) both; }

/* ----- Streamlit components ----- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  border-radius:999px; border:1.5px solid var(--ink) !important;
  background:transparent !important; color:var(--ink) !important;
  font-weight:600; padding:.55rem 1.3rem;
  transition:transform .25s var(--ease),box-shadow .25s var(--ease),background .25s ease,color .25s ease;
}
.stButton > button *, .stDownloadButton > button *, .stFormSubmitButton > button * { color:inherit !important; }
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  background:var(--ink) !important; color:#fff !important;
  transform:translateY(-2px); box-shadow:0 12px 26px rgba(10,10,15,.2);
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"],
.stFormSubmitButton > button[data-testid="stBaseButton-primaryFormSubmit"] {
  background:var(--accent) !important; border-color:var(--accent) !important; color:#fff !important;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover,
.stFormSubmitButton > button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
  background:#e63a1c !important; border-color:#e63a1c !important;
  box-shadow:0 12px 28px rgba(255,77,46,.35);
}
[data-testid="stForm"] {
  background:#fff; border:1px solid var(--line); border-radius:26px; padding:26px;
  box-shadow:0 14px 44px rgba(10,10,15,.045); animation:bp-rise .7s .1s var(--ease) both;
}
input, textarea, [data-baseweb="select"] > div { border-radius:12px !important; }
div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within,
[data-baseweb="select"] > div:focus-within {
  border-color:var(--accent) !important; box-shadow:0 0 0 3px rgba(255,77,46,.16) !important;
}
div[data-testid="stMetric"] {
  background:#fff; border:1px solid var(--line); border-radius:20px; padding:20px 22px;
  box-shadow:0 10px 30px rgba(10,10,15,.04); transition:transform .25s var(--ease),box-shadow .25s ease;
}
div[data-testid="stMetric"]:hover { transform:translateY(-4px); box-shadow:0 18px 40px rgba(10,10,15,.09); }
div[data-testid="stMetricLabel"] { color:var(--muted); font-size:12px; font-weight:600; letter-spacing:.04em; }
div[data-testid="stMetricValue"] { color:var(--ink); font:700 32px 'Inter Tight',sans-serif; letter-spacing:-.04em; }
[data-testid="stAlert"] { border-radius:16px; border:1px solid var(--line); }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:16px; overflow:hidden; }
div[data-testid="stExpander"] {
  border:1px solid var(--line); border-radius:18px; background:#fff;
  transition:box-shadow .25s ease,border-color .25s ease;
}
div[data-testid="stExpander"]:hover { box-shadow:0 12px 30px rgba(10,10,15,.06); border-color:rgba(10,10,15,.22); }

/* ----- Readable text on the light canvas -----
   Streamlit follows the OS colour scheme. In dark mode it paints labels
   near-white and inputs near-black, which disappears on the white cards
   above. These rules pin the main area to dark ink on light surfaces. The
   sidebar is deliberately excluded (it has its own dark styling). */
[data-testid="stMain"] { color-scheme:light; }

/* Body text and captions */
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] li,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] strong { color:var(--ink); }
[data-testid="stMain"] [data-testid="stCaptionContainer"],
[data-testid="stMain"] [data-testid="stCaptionContainer"] p { color:var(--muted) !important; }

/* Field labels */
[data-testid="stMain"] [data-testid="stWidgetLabel"],
[data-testid="stMain"] [data-testid="stWidgetLabel"] p,
[data-testid="stMain"] [data-testid="stWidgetLabel"] label,
[data-testid="stMain"] label,
[data-testid="stMain"] label p {
  color:var(--ink) !important; font-weight:600; font-size:14px;
}

/* Text, number and text-area fields */
[data-testid="stMain"] div[data-baseweb="input"],
[data-testid="stMain"] div[data-baseweb="base-input"],
[data-testid="stMain"] div[data-baseweb="textarea"],
[data-testid="stMain"] div[data-baseweb="select"] > div {
  background-color:#faf9f5 !important; color:var(--ink) !important;
}
[data-testid="stMain"] div[data-baseweb="input"],
[data-testid="stMain"] div[data-baseweb="textarea"],
[data-testid="stMain"] div[data-baseweb="select"] > div {
  border:1px solid rgba(10,10,15,.16) !important;
}
[data-testid="stMain"] input,
[data-testid="stMain"] textarea {
  color:var(--ink) !important; -webkit-text-fill-color:var(--ink) !important;
  caret-color:var(--accent); background:transparent !important;
}
[data-testid="stMain"] input::placeholder,
[data-testid="stMain"] textarea::placeholder {
  color:#80808c !important; -webkit-text-fill-color:#80808c !important; opacity:1;
}
/* Re-declared with higher specificity so the focus ring survives the border rule above. */
[data-testid="stMain"] div[data-baseweb="input"]:focus-within,
[data-testid="stMain"] div[data-baseweb="textarea"]:focus-within,
[data-testid="stMain"] div[data-baseweb="select"] > div:focus-within {
  border-color:var(--accent) !important; box-shadow:0 0 0 3px rgba(255,77,46,.16) !important;
}

/* Select boxes */
[data-testid="stMain"] div[data-baseweb="select"] * { color:var(--ink) !important; }
[data-testid="stMain"] div[data-baseweb="select"] svg { fill:var(--ink) !important; }

/* Number input +/- steppers */
[data-testid="stMain"] [data-testid="stNumberInput"] button {
  background:#efede6 !important; color:var(--ink) !important;
}
[data-testid="stMain"] [data-testid="stNumberInput"] button:hover { background:#e4e1d8 !important; }
[data-testid="stMain"] [data-testid="stNumberInput"] button svg { fill:var(--ink) !important; color:var(--ink) !important; }

/* Select dropdown list (rendered in a popover outside the main area) */
div[data-baseweb="popover"] > div {
  background:#fff !important; border:1px solid var(--line); border-radius:14px;
  box-shadow:0 18px 40px rgba(10,10,15,.14); overflow:hidden;
}
div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] li,
div[data-baseweb="menu"],
div[data-baseweb="menu"] li {
  background:#fff !important; color:var(--ink) !important;
}
div[data-baseweb="popover"] li *, div[data-baseweb="menu"] li * { color:var(--ink) !important; }
div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] li[aria-selected="true"],
div[data-baseweb="menu"] li:hover { background:var(--paper) !important; }

/* File uploader */
[data-testid="stMain"] [data-testid="stFileUploaderDropzone"] {
  background:#fff !important; border:1.5px dashed rgba(10,10,15,.28) !important; border-radius:18px !important;
}
[data-testid="stMain"] [data-testid="stFileUploaderDropzone"] *,
[data-testid="stMain"] [data-testid="stFileUploaderFile"] * { color:var(--ink) !important; }
[data-testid="stMain"] [data-testid="stFileUploaderDropzone"] small { color:var(--muted) !important; }
[data-testid="stMain"] [data-testid="stFileUploaderDropzone"] button {
  background:#fff !important; border:1.5px solid var(--ink) !important; border-radius:999px !important;
}
[data-testid="stMain"] [data-testid="stFileUploaderDropzone"] button:hover { background:var(--paper) !important; }

/* Metrics, alerts, expanders, spinner (icons keep their own colour) */
[data-testid="stMain"] [data-testid="stMetricLabel"],
[data-testid="stMain"] [data-testid="stMetricLabel"] * { color:var(--muted) !important; }
[data-testid="stMain"] [data-testid="stMetricValue"],
[data-testid="stMain"] [data-testid="stMetricValue"] * { color:var(--ink) !important; }
[data-testid="stMain"] [data-testid="stAlert"] p,
[data-testid="stMain"] [data-testid="stAlert"] [data-testid="stMarkdownContainer"] * { color:var(--ink) !important; }
[data-testid="stMain"] [data-testid="stExpander"] summary,
[data-testid="stMain"] [data-testid="stExpander"] summary * { color:var(--ink) !important; }
[data-testid="stMain"] [data-testid="stSpinner"],
[data-testid="stMain"] [data-testid="stSpinner"] * { color:var(--ink) !important; }

/* ----- Keyframes ----- */
@keyframes bp-word { from { transform:translateY(112%); } to { transform:translateY(0); } }
@keyframes bp-rise { from { opacity:0; transform:translateY(26px); } to { opacity:1; transform:translateY(0); } }
@keyframes bp-marquee { from { transform:translateX(0); } to { transform:translateX(-50%); } }
@keyframes bp-count { from { --n:0; } to { --n:var(--to,0); } }
@keyframes bp-float1 { 0%,100% { transform:translate(0,0) scale(1); } 50% { transform:translate(-60px,50px) scale(1.12); } }
@keyframes bp-float2 { 0%,100% { transform:translate(0,0) scale(1); } 50% { transform:translate(70px,-40px) scale(.92); } }
@keyframes bp-grid { to { background-position:64px 64px,64px 64px; } }
@keyframes bp-pulse { 0%,100% { box-shadow:0 0 0 0 rgba(255,77,46,.55); } 70% { box-shadow:0 0 0 10px rgba(255,77,46,0); } }
@keyframes bp-draw { from { width:0; } to { width:72px; } }
@keyframes bp-progress { 0% { width:0; opacity:1; } 65% { width:100%; opacity:1; } 92% { width:100%; opacity:1; } 100% { width:100%; opacity:0; } }
@keyframes bp-pdot {
  0% { background:var(--ink); border-color:rgba(255,255,255,.25); box-shadow:none; }
  8%,70% { background:var(--accent); border-color:var(--accent); box-shadow:0 0 0 7px rgba(255,77,46,.2); }
  92%,100% { background:var(--ink); border-color:rgba(255,255,255,.25); box-shadow:none; }
}

/* ----- Responsive and accessibility ----- */
@media (max-width:900px) {
  .bp-stats { grid-template-columns:repeat(2,1fr); }
  .bp-stat:nth-child(3) { padding-left:0; border-left:0; }
  .bp-stat:nth-child(n+3) { border-top:1px solid var(--line); margin-top:16px; }
  .bp-process { grid-template-columns:repeat(2,1fr); row-gap:30px; }
  .bp-process:before, .bp-process:after { display:none; }
  .bp-band { padding:34px 26px; }
}
@media (max-width:760px) {
  .block-container { padding:1rem 1rem 3rem; }
  .bp-hero { padding:30px 24px 0; min-height:440px; border-radius:24px; }
  .bp-marquee { margin:40px -24px 0; }
}
@media (prefers-reduced-motion:reduce) {
  *, *:before, *:after { animation:none !important; transition:none !important; }
}
</style>
"""


def render_html(block: str) -> None:
    """Render an HTML block through Streamlit's markdown parser.

    Blank lines and 4+ leading spaces make the markdown parser treat HTML as
    a code block, so every line is stripped and the block is joined into a
    single line before rendering.
    """
    compact = " ".join(
        line.strip() for line in block.splitlines() if line.strip()
    )
    st.markdown(compact, unsafe_allow_html=True)


def animated_words(
    text: str,
    accent: tuple[str, ...] = (),
    start: float = 0.2,
    step: float = 0.08,
) -> str:
    """Wrap each word in spans so it slides up one after another."""
    spans = []

    for index, word in enumerate(text.split()):
        delay = start + index * step
        css_class = (
            ' class="acc"'
            if word.strip(".,!?").lower() in accent
            else ""
        )
        spans.append(
            f'<span class="w"><span{css_class} '
            f'style="animation-delay:{delay:.2f}s">{escape(word)}</span></span>'
        )

    return " ".join(spans)


def render_bizpilot_hero() -> None:
    headline = animated_words(
        "Run your business with clarity.",
        accent=("clarity",),
    )

    ticker_set = "".join(
        f"<span>{label}<i>—</i></span>"
        for label in ("Prepare", "Review", "Approve", "Save securely")
    )
    ticker_half = ticker_set * 6

    render_html(f"""
        <div class="bp-hero">
          <div class="bp-grid"></div>
          <div class="bp-blob b1"></div>
          <div class="bp-blob b2"></div>
          <div class="bp-eyebrow"><span class="bp-live"></span>Local-first AI workspace</div>
          <div class="bp-h1" role="heading" aria-level="1">{headline}</div>
          <div class="bp-lead">
            BizPilot AI helps freelancers and retailers draft documents, manage
            inventory and check the numbers, with AI that runs on your own
            machine and never saves anything without your approval.
          </div>
          <div class="bp-chips">
            <span>Ollama models on your machine</span>
            <span>Human-approved saves</span>
            <span>Local SQLite storage</span>
          </div>
          <div class="bp-marquee"><div class="bp-track">{ticker_half}{ticker_half}</div></div>
        </div>
    """)


def render_page_header(kicker: str, title: str, subtitle: str) -> None:
    render_html(f"""
        <div class="bp-kicker">{escape(kicker)}</div>
        <div class="bp-title" role="heading" aria-level="1">{escape(title)}</div>
        <div class="bp-sub">{escape(subtitle)}</div>
    """)


# ---------- Configuration ----------

PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_DIR / "data" / "bizpilot.sqlite3"

DRAFT_TYPES = [
    "Proposal",
    "Email",
    "Quotation",
    "Payment reminder",
]

PAGES = [
    "Overview",
    "Freelance",
    "Retail",
    "Business calculations",
    "Saved drafts",
]

WORKSPACES = [
    {
        "num": "01",
        "page": "Freelance",
        "title": "Freelance studio",
        "text": (
            "Draft proposals, emails, quotations and payment reminders "
            "with local AI, then review them before anything is saved."
        ),
        "tags": ["Proposals", "Quotations", "Reminders"],
        "button": "Open freelance studio ↗",
        "key": "overview_freelance",
    },
    {
        "num": "02",
        "page": "Retail",
        "title": "Retail operations",
        "text": (
            "Upload inventory CSVs, preview every change and approve "
            "the import before it touches your database."
        ),
        "tags": ["Inventory", "Stock levels", "Import preview"],
        "button": "Open retail operations ↗",
        "key": "overview_retail",
    },
    {
        "num": "03",
        "page": "Business calculations",
        "title": "Business calculations",
        "text": (
            "Work out profit, margins and invoice totals with "
            "plain Python, with no guesswork involved."
        ),
        "tags": ["Profit", "Margin", "Invoices"],
        "button": "Open calculations ↗",
        "key": "overview_calculations",
    },
    {
        "num": "04",
        "page": "Saved drafts",
        "title": "Draft library",
        "text": (
            "Every draft you approved, stored on your own machine "
            "and ready to reopen whenever you need it."
        ),
        "tags": ["Approved", "Local", "Searchable"],
        "button": "Open draft library ↗",
        "key": "overview_drafts",
    },
]


def go_to_page(page: str) -> None:
    """Switch the sidebar page.

    This runs as a button callback, which is the supported way to change a
    widget's session state (the sidebar radio) without a Streamlit error.
    """
    st.session_state["bizpilot_navigation"] = page


# ---------- Database ----------

def connect_database(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Create the local database and required tables."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity >= 0),
            reorder_level INTEGER NOT NULL CHECK (reorder_level >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    return conn


def save_approved_draft(
    conn: sqlite3.Connection,
    draft: dict,
) -> None:
    """Save a draft after the user approves it."""
    conn.execute(
        """
        INSERT INTO drafts (kind, title, content)
        VALUES (?, ?, ?)
        """,
        (draft["kind"], draft["title"], draft["content"]),
    )
    conn.commit()


def get_inventory(conn: sqlite3.Connection) -> list[dict]:
    """Read saved inventory records."""
    rows = conn.execute("""
        SELECT sku, name, quantity, reorder_level,
               created_at, updated_at
        FROM inventory
        ORDER BY name
    """).fetchall()

    return [dict(row) for row in rows]


def get_overview_stats() -> dict:
    """Read the live numbers shown on the Overview page (read-only)."""
    conn = connect_database()

    try:
        drafts = conn.execute(
            "SELECT COUNT(*) FROM drafts"
        ).fetchone()[0]

        products, units, reorder = conn.execute("""
            SELECT
                COUNT(*),
                COALESCE(SUM(quantity), 0),
                COALESCE(SUM(CASE WHEN quantity <= reorder_level
                                  THEN 1 ELSE 0 END), 0)
            FROM inventory
        """).fetchone()
    finally:
        conn.close()

    return {
        "drafts": int(drafts),
        "products": int(products),
        "units": int(units),
        "reorder": int(reorder),
    }


def preview_inventory_import(
    conn: sqlite3.Connection,
    incoming: list[dict],
) -> list[dict]:
    """Compare uploaded products with the current database."""
    existing = {
        row["sku"]: row
        for row in conn.execute("""
            SELECT sku, name, quantity, reorder_level
            FROM inventory
        """).fetchall()
    }

    preview = []

    for item in incoming:
        old = existing.get(item["sku"])

        if old is None:
            action = "New product"
            changed = True
        else:
            action = "Update product"
            changed = (
                old["name"] != item["name"]
                or old["quantity"] != item["quantity"]
                or old["reorder_level"] != item["reorder_level"]
            )

        preview.append({
            **item,
            "action": action,
            "changed": changed,
        })

    return preview


def save_inventory_import(
    conn: sqlite3.Connection,
    incoming: list[dict],
) -> tuple[int, int]:
    """
    Insert new products and update changed products atomically.

    The caller must obtain explicit user approval before calling this.
    """
    inserted = 0
    updated = 0

    with conn:
        for item in incoming:
            old = conn.execute("""
                SELECT name, quantity, reorder_level
                FROM inventory
                WHERE sku = ?
            """, (item["sku"],)).fetchone()

            if old is None:
                conn.execute("""
                    INSERT INTO inventory
                        (sku, name, quantity, reorder_level)
                    VALUES (?, ?, ?, ?)
                """, (
                    item["sku"],
                    item["name"],
                    item["quantity"],
                    item["reorder_level"],
                ))
                inserted += 1

            elif (
                old["name"] != item["name"]
                or old["quantity"] != item["quantity"]
                or old["reorder_level"] != item["reorder_level"]
            ):
                conn.execute("""
                    UPDATE inventory
                    SET name = ?,
                        quantity = ?,
                        reorder_level = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE sku = ?
                """, (
                    item["name"],
                    item["quantity"],
                    item["reorder_level"],
                    item["sku"],
                ))
                updated += 1

    return inserted, updated


# ---------- Local AI ----------

def generate_draft(
    model: str,
    base_url: str,
    draft_type: str,
    business_name: str,
    client_name: str,
    service: str,
    amount: str,
    due_date: str,
    tone: str,
    notes: str,
) -> str:
    """Generate a draft using the local Ollama API."""
    if not model.strip():
        raise ValueError("Enter an Ollama model name.")

    prompt = f"""
You are the writing assistant for BizPilot AI.

Prepare a {draft_type.lower()} for a freelancer.

Tone: {tone}
Business name: {business_name or "Not provided"}
Client name: {client_name or "Not provided"}
Service or project: {service or "Not provided"}
Amount: {amount or "Not provided"}
Due date: {due_date or "Not provided"}
Additional facts: {notes or "None provided"}

Instructions:
- Use only the facts provided.
- Do not invent prices, dates, names, or promises.
- Use placeholders where information is missing.
- Return only the draft for the user to review.
"""

    url = base_url.strip().rstrip("/") + "/api/chat"

    payload = {
        "model": model.strip(),
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

        content = result.get("message", {}).get("content", "").strip()

        if not content:
            raise RuntimeError("Ollama returned an empty draft.")

        return content

    except HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(
                "Ollama could not find this model. Check the model name "
                "and verify it is installed."
            ) from exc

        raise RuntimeError(
            f"Ollama returned HTTP error {exc.code}."
        ) from exc

    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            "Cannot connect to Ollama. Check that Ollama is running "
            "and the URL is correct."
        ) from exc

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Ollama returned an invalid response."
        ) from exc


# ---------- Freelancer drafts ----------

def render_freelance_tools(model: str, base_url: str) -> None:
    st.subheader("Freelancer drafts")

    with st.form("freelance_form"):
        draft_type = st.selectbox("Draft type", DRAFT_TYPES)
        business_name = st.text_input("Your business name")
        client_name = st.text_input("Client name")
        service = st.text_input("Service or project")
        amount = st.text_input("Amount")
        due_date = st.text_input("Due date")
        tone = st.selectbox(
            "Tone",
            ["professional", "friendly", "firm", "concise"],
        )
        notes = st.text_area("Additional facts to include")

        submitted = st.form_submit_button("Generate draft")

    if submitted:
        if not client_name.strip() or not service.strip():
            st.error("Enter the client name and service or project.")
            return

        with st.spinner("Generating your draft locally..."):
            try:
                content = generate_draft(
                    model=model,
                    base_url=base_url,
                    draft_type=draft_type,
                    business_name=business_name,
                    client_name=client_name,
                    service=service,
                    amount=amount,
                    due_date=due_date,
                    tone=tone,
                    notes=notes,
                )
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))
                return

        st.session_state["pending_draft"] = {
            "kind": draft_type.lower().replace(" ", "_"),
            "title": f"{draft_type} for {client_name.strip()}",
            "content": content,
        }

    pending = st.session_state.get("pending_draft")

    if pending:
        st.subheader("Review draft before saving")

        st.text_input(
            "Draft title",
            value=pending["title"],
            key="pending_draft_title",
        )

        st.text_area(
            "Generated content",
            value=pending["content"],
            height=250,
            key="pending_draft_content",
        )

        st.caption("The draft is not saved until you approve it.")

        approve_col, reject_col = st.columns(2)

        if approve_col.button(
            "Approve and save draft",
            type="primary",
        ):
            title = st.session_state["pending_draft_title"].strip()
            content = st.session_state["pending_draft_content"].strip()

            if not title or not content:
                st.error("The title and content cannot be empty.")
                return

            conn = connect_database()

            try:
                save_approved_draft(conn, {
                    "kind": pending["kind"],
                    "title": title,
                    "content": content,
                })
            finally:
                conn.close()

            st.session_state.pop("pending_draft", None)
            st.session_state.pop("pending_draft_title", None)
            st.session_state.pop("pending_draft_content", None)

            st.success("Approved draft saved locally.")
            st.rerun()

        if reject_col.button("Reject draft"):
            st.session_state.pop("pending_draft", None)
            st.session_state.pop("pending_draft_title", None)
            st.session_state.pop("pending_draft_content", None)
            st.warning("Draft rejected. Nothing was saved.")
            st.rerun()


# ---------- Retail inventory ----------

def render_retail_tools() -> None:
    st.subheader("Retail inventory")

    uploaded = st.file_uploader(
        "Upload inventory CSV",
        type=["csv"],
        key="inventory_csv",
    )

    st.caption(
        "Required columns: sku, name, quantity, reorder_level."
    )

    conn = connect_database()

    try:
        # Display existing records when no file is being uploaded.
        if uploaded is None:
            st.subheader("Saved inventory")
            saved = get_inventory(conn)

            if saved:
                st.dataframe(saved, use_container_width=True)
                st.text_area(
                    "Current low-stock report",
                    value=low_stock_report(saved),
                    height=180,
                )
            else:
                st.info("No inventory has been saved yet.")

            return

        csv_bytes = uploaded.getvalue()
        fingerprint = hashlib.sha256(csv_bytes).hexdigest()

        # Do not re-import the same approved file on every rerun.
        if st.session_state.get("approved_inventory_hash") == fingerprint:
            st.success("This CSV has already been approved and imported.")

            saved = get_inventory(conn)

            if saved:
                st.dataframe(saved, use_container_width=True)
                st.text_area(
                    "Current low-stock report",
                    value=low_stock_report(saved),
                    height=180,
                )

            return

        if st.session_state.get("rejected_inventory_hash") == fingerprint:
            st.info(
                "This CSV was rejected. No inventory changes were saved."
            )
            return

        try:
            csv_text = csv_bytes.decode("utf-8-sig")
            incoming = parse_inventory_csv(csv_text)
        except UnicodeDecodeError:
            st.error("The CSV must use UTF-8 encoding.")
            return
        except ValueError as exc:
            st.error(f"Invalid inventory CSV: {exc}")
            return

        pending = st.session_state.get("pending_inventory_import")

        # Build a new preview when the uploaded file changes.
        if not pending or pending["fingerprint"] != fingerprint:
            pending = {
                "fingerprint": fingerprint,
                "records": incoming,
                "preview": preview_inventory_import(conn, incoming),
            }
            st.session_state["pending_inventory_import"] = pending

        preview = pending["preview"]

        new_count = sum(
            item["action"] == "New product"
            for item in preview
        )

        update_count = sum(
            item["action"] == "Update product" and item["changed"]
            for item in preview
        )

        unchanged_count = sum(
            not item["changed"]
            for item in preview
        )

        st.subheader("Import preview")
        st.write(f"New products: **{new_count}**")
        st.write(f"Products to update: **{update_count}**")
        st.write(f"Unchanged products: **{unchanged_count}**")

        st.dataframe(preview, use_container_width=True)

        st.warning(
            "Nothing has been saved yet. Review the preview before "
            "approving this import."
        )

        approve_col, reject_col = st.columns(2)

        if approve_col.button(
            "Approve and save inventory",
            type="primary",
            key="approve_inventory_import",
        ):
            try:
                inserted, updated = save_inventory_import(
                    conn,
                    pending["records"],
                )
            except sqlite3.Error as exc:
                st.error(
                    "Inventory import failed and the transaction "
                    f"was rolled back: {exc}"
                )
                return

            st.session_state["approved_inventory_hash"] = fingerprint
            st.session_state.pop("pending_inventory_import", None)
            st.session_state.pop("rejected_inventory_hash", None)

            st.success(
                f"Import approved. Added {inserted} new products "
                f"and updated {updated} existing products."
            )
            st.rerun()

        if reject_col.button(
            "Reject import",
            key="reject_inventory_import",
        ):
            st.session_state["rejected_inventory_hash"] = fingerprint
            st.session_state.pop("pending_inventory_import", None)

            st.warning("Import rejected. No inventory records were changed.")
            st.rerun()

    finally:
        conn.close()


# ---------- Business calculations ----------

def render_business_calculations() -> None:
    st.subheader("Business calculations")

    st.markdown("**Profit and profit margin**")

    with st.form("profit_form"):
        income = st.number_input(
            "Income",
            min_value=0.0,
            step=100.0,
        )
        expenses = st.number_input(
            "Expenses",
            min_value=0.0,
            step=100.0,
        )
        calculate = st.form_submit_button("Calculate profit")

    if calculate:
        profit = calculate_profit(income, expenses)
        margin = calculate_profit_margin(income, expenses)

        st.metric("Profit / loss", f"{profit:,.2f}")
        st.metric("Profit margin", f"{margin:.2f}%")

    st.divider()
    st.markdown("**Invoice total**")

    with st.form("invoice_form"):
        quantity = st.number_input(
            "Quantity",
            min_value=0,
            step=1,
            value=1,
        )
        unit_price = st.number_input(
            "Unit price",
            min_value=0.0,
            step=100.0,
        )
        discount = st.number_input(
            "Discount (%)",
            min_value=0.0,
            max_value=100.0,
        )
        tax = st.number_input(
            "Tax (%)",
            min_value=0.0,
            max_value=100.0,
        )

        invoice_submit = st.form_submit_button("Calculate invoice")

    if invoice_submit:
        total = calculate_invoice_total(
            int(quantity),
            unit_price,
            tax_rate=tax,
            discount=discount,
        )
        st.metric("Invoice total", f"{total:,.2f}")


# ---------- Saved drafts ----------

def render_saved_drafts() -> None:
    st.subheader("Saved drafts")
    conn = connect_database()

    try:
        drafts = conn.execute("""
            SELECT id, kind, title, content, created_at
            FROM drafts
            ORDER BY id DESC
        """).fetchall()
    finally:
        conn.close()

    if not drafts:
        st.caption("No approved drafts saved yet.")
        return

    for draft in drafts:
        with st.expander(
            f"{draft['title']} ({draft['kind']})"
        ):
            st.caption(draft["created_at"])
            st.write(draft["content"])


# ---------- Overview page ----------

def render_overview_stats() -> None:
    """Count-up numbers read from the local database."""
    stats = get_overview_stats()

    items = [
        (stats["drafts"], "Drafts saved", "Approved and stored locally"),
        (stats["products"], "Products tracked", "Unique SKUs in inventory"),
        (stats["units"], "Units in stock", "Across all products"),
        (stats["reorder"], "Reorder alerts", "At or below reorder level"),
    ]

    cells = "".join(
        f'<div class="bp-stat" style="animation-delay:{index * 0.1:.1f}s">'
        f'<div class="bp-num"><span class="bp-count" style="--to:{value}">'
        f"</span></div>"
        f'<div class="bp-stat-label">{label}</div>'
        f'<div class="bp-stat-note">{note}</div>'
        f"</div>"
        for index, (value, label, note) in enumerate(items)
    )

    render_html(f"""
        <div class="bp-stats">{cells}</div>
        <div class="bp-live-note">Live from your local database.</div>
    """)


def render_workspace_cards() -> None:
    columns = st.columns(len(WORKSPACES), gap="medium")

    for index, (column, space) in enumerate(zip(columns, WORKSPACES)):
        tags = "".join(f"<span>{tag}</span>" for tag in space["tags"])

        with column:
            render_html(f"""
                <div class="bp-card" style="animation-delay:{index * 0.12:.2f}s">
                  <div class="bp-card-top">
                    <span class="bp-card-num">{space['num']}</span>
                    <span class="bp-arrow">↗</span>
                  </div>
                  <div class="bp-card-title">{space['title']}</div>
                  <div class="bp-card-text">{space['text']}</div>
                  <div class="bp-tags">{tags}</div>
                </div>
            """)

            st.button(
                space["button"],
                key=space["key"],
                use_container_width=True,
                on_click=go_to_page,
                args=(space["page"],),
            )


def render_approach_band() -> None:
    steps = [
        ("Prepare", "Enter the facts or upload a CSV. Nothing is saved yet."),
        ("Review", "Read the AI draft or check the import preview."),
        ("Approve", "You explicitly approve or reject every save."),
        ("Save securely", "Records are written to local SQLite on your machine."),
    ]

    process = "".join(
        f'<div class="bp-pstep" style="--i:{index}">'
        f'<div class="bp-pstep-title">{title}</div>'
        f'<div class="bp-pstep-text">{text}</div>'
        f"</div>"
        for index, (title, text) in enumerate(steps)
    )

    render_html(f"""
        <div class="bp-band">
          <div class="bp-label">Our approach</div>
          <div class="bp-band-title">AI that drafts. <span class="acc">You decide.</span></div>
          <div class="bp-process">{process}</div>
          <div class="bp-foot">
            <span>© {datetime.now().year} BizPilot AI</span>
            <span>Local-first · Human-approved · Your data stays with you</span>
          </div>
        </div>
    """)


def render_overview() -> None:
    render_bizpilot_hero()

    render_html("""
        <div class="bp-label">What BizPilot does</div>
        <div class="bp-statement">
          One workspace for the work behind a growing business,
          <span class="dim">with drafts, stock and numbers all reviewed
          by you before anything is saved.</span>
        </div>
    """)

    render_html('<div class="bp-label">Your workspace in numbers</div>')
    render_overview_stats()

    render_html('<div class="bp-label">Workspaces</div>')
    render_workspace_cards()

    render_approach_band()


# ---------- Main application ----------

def main() -> None:
    st.set_page_config(
        page_title="BizPilot AI",
        page_icon="BP",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    render_html(BIZPILOT_THEME_CSS)

    with st.sidebar:
        render_html("""
            <div class="bp-brand">
              <div class="bp-logo">BP</div>
              <div>
                <div class="bp-brand-name">BizPilot AI</div>
                <div class="bp-brand-sub">BUSINESS INTELLIGENCE</div>
              </div>
            </div>
        """)
        st.caption("Local-first AI · Human-approved actions")
        st.divider()
        render_html('<div class="bp-nav-heading">Local AI settings</div>')
        model = st.text_input("Ollama model", value="llama3.1")
        base_url = st.text_input("Ollama URL", value="http://localhost:11434")
        st.divider()
        selected_page = st.radio(
            "EXPLORE YOUR WORKSPACE",
            PAGES,
            index=0,
            key="bizpilot_navigation",
            label_visibility="visible",
        )
        st.divider()
        st.caption(
            "Your data stays in your local application. "
            "Review drafts before saving."
        )

    if selected_page == "Overview":
        render_overview()

    elif selected_page == "Freelance":
        render_page_header(
            "Create / 01",
            "Freelance studio",
            "Generate drafts with your local Ollama model, review them, "
            "and save only what you approve.",
        )
        render_freelance_tools(model, base_url)

    elif selected_page == "Retail":
        render_page_header(
            "Operate / 02",
            "Retail operations",
            "Upload a CSV, preview every change and approve it before "
            "anything touches the database.",
        )
        render_retail_tools()

    elif selected_page == "Business calculations":
        render_page_header(
            "Decide / 03",
            "Business calculations",
            "Quick, transparent profit, margin and invoice calculations.",
        )
        render_business_calculations()

    elif selected_page == "Saved drafts":
        render_page_header(
            "Library / 04",
            "Saved drafts",
            "Every draft you approved, stored locally on your machine.",
        )
        render_saved_drafts()


if __name__ == "__main__":
    main()