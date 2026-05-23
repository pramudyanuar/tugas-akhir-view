# ==============================================================================
# 3DBPP SEMI-ONLINE WITH HIERARCHICAL DRL — DASH APP (SeaRates Style)
# Run: python app_3dbpp_dash.py
# ==============================================================================

import json
import time
import uuid

import dash
from dash import dcc, html, Input, Output, State, ALL, MATCH, ctx, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ==============================================================================
# APP INIT
# ==============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap",
        "https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css",
    ],
    suppress_callback_exceptions=True,
    title="3DBPP | Load & Stuffing",
)
server = app.server

# ==============================================================================
# CONSTANTS
# ==============================================================================

BOX_COLORS = [
    "#3b82f6", "#f472b6", "#a78bfa", "#4ade80",
    "#fb923c", "#facc15", "#34d399", "#f87171",
    "#c084fc", "#38bdf8", "#86efac", "#fda4af",
]
GROUP_PALETTE = ["#374151", "#1e40af", "#7c3aed", "#b45309", "#dc2626", "#16a34a"]

CONTAINERS = {
    "20gp": {"name": "20' Standard GP",  "dims": (5900, 2350, 2390), "maxw": 28000, "vol": 33.1},
    "40gp": {"name": "40' Standard GP",  "dims": (12032, 2350, 2390), "maxw": 27000, "vol": 67.6},
    "40hc": {"name": "40' High Cube HC", "dims": (12032, 2350, 2695), "maxw": 26500, "vol": 76.3},
    "lkw":  {"name": "Truck / LKW",      "dims": (13600, 2480, 2700), "maxw": 24000, "vol": 90.7},
}

ITEM_TYPES = ["Box", "Bag/Sack", "Cylinder"]

SAMPLE_ITEMS = [
    {"name": "Boxes 1",  "type": "Box",      "length": 500,  "width": 400,  "height": 300,  "weight": 10.0,  "qty": 80,  "color_idx": 0, "stackable": True},
    {"name": "Sacks",    "type": "Bag/Sack", "length": 1000, "width": 450,  "height": 300,  "weight": 45.0,  "qty": 100, "color_idx": 1, "stackable": True},
    {"name": "Big bags", "type": "Box",      "length": 1000, "width": 1000, "height": 1000, "weight": 900.0, "qty": 10,  "color_idx": 3, "stackable": False},
]

# ==============================================================================
# CSS
# ==============================================================================

STYLES = """
* { box-sizing: border-box; }
body, html {
    font-family: 'Inter', sans-serif !important;
    background: #f8fafc !important;
    color: #1e293b !important;
    margin: 0; padding: 0;
}
/* NAV */
.topnav {
    background: #fff;
    border-bottom: 1px solid #e2e8f0;
    padding: 0 2rem;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky; top: 0; z-index: 100;
}
.topnav-brand { font-size: 18px; font-weight: 700; color: #1e40af; display: flex; align-items: center; gap: 8px; letter-spacing: -0.02em; }
.topnav-sub { font-size: 12px; color: #94a3b8; font-weight: 400; }
/* STEP TABS */
.step-nav {
    background: #fff;
    border-bottom: 1px solid #e2e8f0;
    padding: 0 2rem;
    display: flex;
    align-items: center;
    position: sticky; top: 56px; z-index: 99;
}
.step-tab {
    display: flex; align-items: center; gap: 10px;
    padding: 16px 20px; cursor: pointer;
    border-bottom: 3px solid transparent;
    color: #94a3b8; font-size: 13px; font-weight: 500;
    text-decoration: none; transition: all 0.2s; user-select: none;
}
.step-tab.active { color: #1e40af; border-bottom-color: #1e40af; }
.step-tab.done   { color: #16a34a; }
.step-num {
    width: 24px; height: 24px; border-radius: 50%;
    background: #f1f5f9; color: #94a3b8;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 600;
}
.step-tab.active .step-num { background: #1e40af; color: #fff; }
.step-tab.done   .step-num { background: #16a34a; color: #fff; }
.step-arrow { color: #cbd5e1; font-size: 20px; padding: 0 4px; }
/* PAGE */
.page-wrap { max-width: 980px; margin: 0 auto; padding: 2rem 1rem 4rem; }
.page-title { font-size: 22px; font-weight: 700; color: #1e293b; margin-bottom: 4px; letter-spacing: -0.02em; }
.page-sub   { font-size: 13px; color: #64748b; margin-bottom: 1.5rem; }
/* CARDS */
.panel-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1rem;
}
.panel-title { font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 1rem; }
.group-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1rem;
}
.group-hdr {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1rem; padding-bottom: .75rem; border-bottom: 1px solid #f1f5f9;
}
/* CONTAINER CARDS */
.cont-card {
    background: #fff; border: 1.5px solid #e2e8f0;
    border-radius: 10px; padding: 14px 18px; cursor: pointer;
    transition: all .15s; margin-bottom: 10px;
}
.cont-card:hover { border-color: #93c5fd; background: #f0f9ff; }
.cont-card.selected { border-color: #1e40af !important; background: #eff6ff !important; }
.cont-name { font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 3px; }
.cont-dims { font-size: 12px; color: #64748b; }
.cont-vol  { font-size: 12px; color: #94a3b8; margin-top: 4px; }
/* ALGO CARDS */
.algo-card {
    background: #fff; border: 1.5px solid #e2e8f0;
    border-radius: 10px; padding: 14px 18px; cursor: pointer;
    transition: all .15s;
}
.algo-card.selected { border-color: #1e40af; background: #eff6ff; }
/* METRICS */
.metric-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 16px 20px; text-align: center; flex: 1;
}
.metric-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: .05em; font-weight: 500; margin-bottom: 6px; }
.metric-value { font-family: 'JetBrains Mono', monospace; font-size: 24px; font-weight: 700; }
/* BANNER */
.result-banner {
    background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px;
    padding: 14px 20px; display: flex; align-items: center; gap: 12px;
    margin-bottom: 1.25rem; font-size: 13px; color: #15803d; font-weight: 500;
}
.result-banner.warn { background: #fffbeb; border-color: #fde68a; color: #b45309; }
/* TABLE */
.placement-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.placement-table th {
    background: #f8fafc; color: #94a3b8; font-weight: 600;
    font-size: 10px; text-transform: uppercase; letter-spacing: .06em;
    padding: 8px 10px; border-bottom: 1px solid #f1f5f9; text-align: center;
}
.placement-table td { padding: 6px 10px; border-bottom: 1px solid #f8fafc; text-align: center; color: #374151; }
.placement-table tr:hover td { background: #f0f9ff; }
/* BUTTONS */
.btn-primary-custom {
    background: #1e40af; color: #fff; border: none;
    border-radius: 8px; padding: 8px 20px; font-size: 13px;
    font-weight: 500; cursor: pointer; transition: background .15s;
    font-family: 'Inter', sans-serif;
}
.btn-primary-custom:hover { background: #1d4ed8; }
.btn-outline-custom {
    background: #fff; color: #374151; border: 1px solid #e2e8f0;
    border-radius: 8px; padding: 8px 16px; font-size: 13px;
    font-weight: 500; cursor: pointer; font-family: 'Inter', sans-serif;
}
.btn-outline-custom:hover { background: #f8fafc; }
.btn-danger-custom {
    background: #fff; color: #ef4444; border: 1px solid #fecaca;
    border-radius: 8px; padding: 6px 12px; font-size: 12px;
    cursor: pointer; font-family: 'Inter', sans-serif;
}
.btn-danger-custom:hover { background: #fef2f2; }
/* PROGRESS BAR */
.prog-wrap { background: #f1f5f9; border-radius: 4px; height: 6px; margin: 8px 0; }
.prog-bar  { height: 6px; border-radius: 4px; background: linear-gradient(90deg,#1e40af,#3b82f6); transition: width .3s; }
/* INPUTS */
.dash-input, .dash-dropdown .Select-control {
    border: 1px solid #e2e8f0 !important; border-radius: 8px !important;
    font-size: 13px !important; font-family: 'Inter', sans-serif !important;
    color: #1e293b !important;
}
input[type=number], input[type=text] {
    border: 1px solid #e2e8f0; border-radius: 6px; padding: 5px 8px;
    font-size: 13px; font-family: 'Inter', sans-serif; color: #1e293b;
    width: 100%; outline: none;
}
input[type=number]:focus, input[type=text]:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,.12); }
select {
    border: 1px solid #e2e8f0; border-radius: 6px; padding: 5px 8px;
    font-size: 13px; font-family: 'Inter', sans-serif; color: #1e293b;
    background: #fff; outline: none; width: 100%;
}
.step-label { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #64748b; margin-bottom: 6px; }
.section-div { border: none; border-top: 1px solid #f1f5f9; margin: 1.25rem 0; }
.chip { display: inline-flex; align-items: center; gap: 5px; background: #f1f5f9; border-radius: 999px; padding: 4px 12px; font-size: 12px; color: #475569; font-weight: 500; margin-right: 6px; }
.chip-blue { background: #eff6ff; color: #1d4ed8; }
.empty-state { text-align: center; padding: 3rem 2rem; background: #fff; border: 1.5px dashed #e2e8f0; border-radius: 12px; margin-bottom: 1rem; }
/* scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #f1f5f9; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
"""

# ==============================================================================
# INITIAL STATE
# ==============================================================================

INITIAL_STATE = {
    "step": 1,
    "groups": [
        {
            "id": "g1",
            "name": "Group #1",
            "color": GROUP_PALETTE[0],
            "items": [],
        }
    ],
    "selected_container": "20gp",
    "custom_container": False,
    "custom_dims": {"length": 5900, "width": 2350, "height": 2390, "maxw": 28000},
    "selected_algo": "hdrl",
    "placed_items": [],
    "anim_step": 0,
    "anim_playing": False,
}

# ==============================================================================
# HELPERS
# ==============================================================================

def make_uid():
    return str(uuid.uuid4())[:8]


def pack_blf(items, cL, cW, cH):
    placed = []
    cx, cy, cz = 0, 0, 0
    row_d, layer_h = 0, 0
    for idx, item in enumerate(items):
        w = item.get("width", 300)
        l = item.get("length", 500)
        h = item.get("height", 300)
        if cx + w > cW:
            cx = 0; cy += row_d; row_d = 0
        if cy + l > cL:
            cy = 0; cx = 0; cz += layer_h; layer_h = 0; row_d = 0
        if cz + h > cH:
            continue
        placed.append({**item, "pos_x": cx, "pos_y": cy, "pos_z": cz, "_flat_idx": idx})
        cx += w
        row_d = max(row_d, l)
        layer_h = max(layer_h, h)
    return placed


def get_container_dims(state):
    if state.get("custom_container"):
        d = state.get("custom_dims", {})
        return d.get("length", 5900), d.get("width", 2350), d.get("height", 2390)
    k = state.get("selected_container", "20gp")
    return CONTAINERS[k]["dims"]  # (L, W, H)


def make_3d_figure(placed, cL, cW, cH, step_n=None, height=380):
    fig = go.Figure()
    # Container wireframe
    cx_ = [0, cW, cW, 0, 0, cW, cW, 0]
    cy_ = [0, 0, cL, cL, 0, 0, cL, cL]
    cz_ = [0, 0, 0, 0, cH, cH, cH, cH]
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    ex, ey, ez = [], [], []
    for a, b in edges:
        ex += [cx_[a], cx_[b], None]
        ey += [cy_[a], cy_[b], None]
        ez += [cz_[a], cz_[b], None]
    fig.add_trace(go.Scatter3d(x=ex, y=ey, z=ez, mode="lines",
        line=dict(color="#cbd5e1", width=1.5), showlegend=False, hoverinfo="skip"))

    items_to_show = placed[:step_n] if step_n is not None else placed
    for idx, item in enumerate(items_to_show):
        ci = item.get("color_idx", idx)
        color = BOX_COLORS[ci % len(BOX_COLORS)]
        x0, y0, z0 = item["pos_x"], item["pos_y"], item["pos_z"]
        w, l, h = item.get("width", 300), item.get("length", 500), item.get("height", 300)
        x1, y1, z1 = x0+w, y0+l, z0+h
        vx = [x0,x1,x1,x0,x0,x1,x1,x0]
        vy = [y0,y0,y1,y1,y0,y0,y1,y1]
        vz = [z0,z0,z0,z0,z1,z1,z1,z1]
        fi = [0,0,0,4,4,4,0,0,1,5,2,6]
        fj = [1,2,4,5,6,7,1,2,2,6,3,7]
        fk = [2,3,5,6,7,3,5,4,6,2,7,3]
        nm = item.get("name", "") or "Item"
        fig.add_trace(go.Mesh3d(
            x=vx, y=vy, z=vz, i=fi, j=fj, k=fk,
            color=color, opacity=0.85, flatshading=True, showlegend=False,
            hovertemplate=f"<b>{nm}</b><br>Size: {w}×{l}×{h} mm<br>Pos: ({x0},{y0},{z0})<br>Weight: {item.get('weight',0)} kg<extra></extra>",
        ))
        ex2, ey2, ez2 = [], [], []
        for a, b in [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]:
            ex2 += [vx[a],vx[b],None]; ey2 += [vy[a],vy[b],None]; ez2 += [vz[a],vz[b],None]
        fig.add_trace(go.Scatter3d(x=ex2, y=ey2, z=ez2, mode="lines",
            line=dict(color="rgba(255,255,255,0.35)", width=0.8), showlegend=False, hoverinfo="skip"))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            bgcolor="rgba(248,250,252,0)",
            xaxis=dict(title=dict(text="Width (X)", font=dict(size=10, color="#94a3b8")), range=[0, cW],
                showbackground=True, backgroundcolor="rgba(241,245,249,0.5)",
                gridcolor="#e2e8f0", tickfont=dict(size=9, color="#94a3b8"), nticks=6, tickcolor="#e2e8f0"),
            yaxis=dict(title=dict(text="Length (Y)", font=dict(size=10, color="#94a3b8")), range=[0, cL],
                showbackground=True, backgroundcolor="rgba(241,245,249,0.35)",
                gridcolor="#e2e8f0", tickfont=dict(size=9, color="#94a3b8"), nticks=6, tickcolor="#e2e8f0"),
            zaxis=dict(title=dict(text="Height (Z)", font=dict(size=10, color="#94a3b8")), range=[0, cH],
                showbackground=True, backgroundcolor="rgba(241,245,249,0.2)",
                gridcolor="#e2e8f0", tickfont=dict(size=9, color="#94a3b8"), nticks=6, tickcolor="#e2e8f0"),
            aspectmode="data",
            camera=dict(eye=dict(x=1.4, y=-1.4, z=1.1)),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
    )
    return fig


def build_item_row(gi, ii, item):
    ci = item.get("color_idx", ii)
    color = BOX_COLORS[ci % len(BOX_COLORS)]
    return html.Div([
        html.Div([
            # Type
            html.Div([
                html.Select(
                    [html.Option(t, value=t, selected=(item.get("type","Box")==t)) for t in ITEM_TYPES],
                    id={"type":"item-type","gi":gi,"ii":ii},
                    style={"width":"100%"}
                )
            ], style={"flex":"0 0 100px"}),
            # Name
            html.Div([
                dcc.Input(value=item.get("name",""), placeholder="Product name",
                    id={"type":"item-name","gi":gi,"ii":ii}, type="text",
                    style={"width":"100%"})
            ], style={"flex":"1 1 130px"}),
            # Length
            html.Div([
                dcc.Input(value=item.get("length",500), type="number", min=1, max=20000,
                    id={"type":"item-length","gi":gi,"ii":ii}, style={"width":"100%"})
            ], style={"flex":"0 0 80px"}),
            # Width
            html.Div([
                dcc.Input(value=item.get("width",400), type="number", min=1, max=10000,
                    id={"type":"item-width","gi":gi,"ii":ii}, style={"width":"100%"})
            ], style={"flex":"0 0 80px"}),
            # Height
            html.Div([
                dcc.Input(value=item.get("height",300), type="number", min=1, max=10000,
                    id={"type":"item-height","gi":gi,"ii":ii}, style={"width":"100%"})
            ], style={"flex":"0 0 80px"}),
            # Weight
            html.Div([
                dcc.Input(value=item.get("weight",10), type="number", min=0, step=0.5,
                    id={"type":"item-weight","gi":gi,"ii":ii}, style={"width":"100%"})
            ], style={"flex":"0 0 80px"}),
            # Qty
            html.Div([
                dcc.Input(value=item.get("qty",1), type="number", min=1, max=500,
                    id={"type":"item-qty","gi":gi,"ii":ii}, style={"width":"100%"})
            ], style={"flex":"0 0 60px"}),
            # Color dot + index
            html.Div([
                html.Div(style={
                    "width":"14px","height":"14px","borderRadius":"3px",
                    "background":color,"display":"inline-block","verticalAlign":"middle","marginRight":"6px"
                }),
                dcc.Input(value=ci, type="number", min=0, max=11,
                    id={"type":"item-color","gi":gi,"ii":ii},
                    style={"width":"40px","display":"inline-block"})
            ], style={"flex":"0 0 70px","display":"flex","alignItems":"center"}),
            # Stackable checkbox
            html.Div([
                dcc.Checklist(options=[{"label":" Stack","value":"s"}],
                    value=["s"] if item.get("stackable",True) else [],
                    id={"type":"item-stack","gi":gi,"ii":ii},
                    style={"fontSize":"12px"})
            ], style={"flex":"0 0 70px"}),
            # Delete
            html.Div([
                html.Button("✕", id={"type":"del-item","gi":gi,"ii":ii},
                    className="btn-danger-custom")
            ], style={"flex":"0 0 40px"}),
        ], style={
            "display":"flex","gap":"8px","alignItems":"center",
            "padding":"8px 0","borderBottom":"1px solid #f8fafc"
        }),
    ])


def build_group_section(gi, group):
    dot_color = group.get("color", GROUP_PALETTE[gi % len(GROUP_PALETTE)])
    items_html = [
        # Table header
        html.Div([
            html.Div("Type",      style={"flex":"0 0 100px","fontSize":"10px","color":"#94a3b8","fontWeight":"600","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("Name",      style={"flex":"1 1 130px","fontSize":"10px","color":"#94a3b8","fontWeight":"600","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("L (mm)",    style={"flex":"0 0 80px","fontSize":"10px","color":"#94a3b8","fontWeight":"600","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("W (mm)",    style={"flex":"0 0 80px","fontSize":"10px","color":"#94a3b8","fontWeight":"600","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("H (mm)",    style={"flex":"0 0 80px","fontSize":"10px","color":"#94a3b8","fontWeight":"600","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("Wt (kg)",   style={"flex":"0 0 80px","fontSize":"10px","color":"#94a3b8","fontWeight":"600","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("Qty",       style={"flex":"0 0 60px","fontSize":"10px","color":"#94a3b8","fontWeight":"600","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("Color",     style={"flex":"0 0 70px","fontSize":"10px","color":"#94a3b8","fontWeight":"600","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("Stack",     style={"flex":"0 0 70px","fontSize":"10px","color":"#94a3b8","fontWeight":"600","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("",          style={"flex":"0 0 40px"}),
        ], style={
            "display":"flex","gap":"8px","alignItems":"center",
            "padding":"6px 0 10px","borderBottom":"1px solid #f1f5f9","marginBottom":"4px"
        })
    ] + [build_item_row(gi, ii, item) for ii, item in enumerate(group["items"])]

    return html.Div([
        html.Div([
            html.Div([
                html.Div(style={"width":"12px","height":"12px","borderRadius":"50%","background":dot_color,"marginRight":"8px","display":"inline-block"}),
                html.Strong(group["name"], style={"fontSize":"14px","color":"#1e293b"}),
                html.Span(f" ({len(group['items'])} product types)", style={"fontSize":"12px","color":"#94a3b8","fontWeight":"400","marginLeft":"6px"}),
            ], style={"display":"flex","alignItems":"center"}),
            html.Button(f"🗑 Remove group", id={"type":"del-group","gi":gi},
                className="btn-danger-custom"),
        ], className="group-hdr"),
        html.Div(items_html, style={"overflowX":"auto"}),
        html.Div([
            html.Button("➕ Add product", id={"type":"add-item","gi":gi},
                className="btn-outline-custom",
                style={"fontSize":"12px","padding":"6px 12px","marginTop":"10px"}),
        ]),
    ], className="group-card")


# ==============================================================================
# LAYOUT
# ==============================================================================

app.layout = html.Div([
    # App state store
    dcc.Store(id="app-state", data=json.dumps(INITIAL_STATE)),
    dcc.Store(id="anim-trigger", data=0),
    dcc.Interval(id="anim-interval", interval=180, disabled=True, n_intervals=0),

    # Top nav
    html.Div([
        html.Div([
            html.Span("📦", style={"fontSize":"20px"}),
            html.Span("3DBPP"),
            html.Span(" Semi-Online with Hierarchical DRL", className="topnav-sub"),
        ], className="topnav-brand"),
        html.Div("Load & Stuffing Calculation", style={"fontSize":"12px","color":"#94a3b8"}),
    ], className="topnav"),

    # Step tabs
    html.Div(id="step-nav"),

    # Page content
    html.Div(id="page-content", className="page-wrap"),
])


# ==============================================================================
# STEP NAV RENDER
# ==============================================================================

@app.callback(Output("step-nav","children"), Input("app-state","data"))
def render_step_nav(state_json):
    state = json.loads(state_json)
    step = state.get("step", 1)
    def cls(i):
        if i == step: return "step-tab active"
        if i < step:  return "step-tab done"
        return "step-tab"
    def num(i):
        return "✓" if i < step else str(i)
    return html.Div([
        html.Div([html.Span(num(1), className="step-num"), " Products"],   className=cls(1)),
        html.Span("›", className="step-arrow"),
        html.Div([html.Span(num(2), className="step-num"), " Container & Truck"], className=cls(2)),
        html.Span("›", className="step-arrow"),
        html.Div([html.Span(num(3), className="step-num"), " Stuffing Result"],  className=cls(3)),
    ], className="step-nav")


# ==============================================================================
# PAGE CONTENT RENDER
# ==============================================================================

@app.callback(Output("page-content","children"), Input("app-state","data"))
def render_page(state_json):
    state = json.loads(state_json)
    step = state.get("step", 1)

    if step == 1:
        return render_step1(state)
    elif step == 2:
        return render_step2(state)
    elif step == 3:
        return render_step3(state)
    return html.Div("Unknown step")


# ── STEP 1 ──────────────────────────────────────────────────────────────────

def render_step1(state):
    groups = state.get("groups", [])
    total_items = sum(it.get("qty",1) for g in groups for it in g["items"])

    empty = html.Div([
        html.Div("📦", style={"fontSize":"32px","marginBottom":"10px"}),
        html.Div("No items yet", style={"fontSize":"14px","fontWeight":"600","marginBottom":"4px"}),
        html.Div("Click 'Add group' below or use 'Sample items' to load an example.",
            style={"fontSize":"13px","color":"#64748b"}),
    ], className="empty-state") if not groups else html.Div([
        build_group_section(gi, g) for gi, g in enumerate(groups)
    ])

    return html.Div([
        html.Div("Products", className="page-title"),
        html.Div("Add the items you want to pack. Group them by type, fragility, or destination.", className="page-sub"),
        # Toolbar
        html.Div([
            html.Div([
                html.Button("⚡ Sample items", id="btn-sample", className="btn-outline-custom",
                    style={"marginRight":"8px"}),
                html.Button("🗑 Clear all", id="btn-clear", className="btn-outline-custom"),
            ]),
            html.Div([
                html.Span(f"📦 {total_items} items", className="chip chip-blue"),
                html.Span(f"{len(groups)} groups", className="chip"),
            ]),
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"1rem"}),

        # Groups
        html.Div(id="groups-container", children=empty),

        # Add group + pallet
        html.Div([
            html.Button("➕ Add group", id="btn-add-group", className="btn-outline-custom"),
            html.Div([
                dcc.Checklist(options=[{"label":" Use pallets","value":"p"}], value=[],
                    id="use-pallets", style={"fontSize":"13px","marginLeft":"16px"}),
            ], style={"display":"inline-flex","alignItems":"center"}),
        ], style={"display":"flex","alignItems":"center","marginTop":"8px"}),

        html.Hr(className="section-div"),

        # Footer nav
        html.Div([
            html.Div(),
            html.Button("Next →", id="btn-next-1", className="btn-primary-custom"),
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center"}),
    ])


# ── STEP 2 ──────────────────────────────────────────────────────────────────

def render_step2(state):
    sel_cont = state.get("selected_container","20gp")
    use_custom = state.get("custom_container", False)
    sel_algo = state.get("selected_algo","hdrl")
    cdims = state.get("custom_dims",{})

    cont_cards = []
    for k, c in CONTAINERS.items():
        is_sel = (sel_cont == k) and not use_custom
        cont_cards.append(
            html.Div([
                html.Div(c["name"], className="cont-name"),
                html.Div(f"{c['dims'][0]} × {c['dims'][1]} × {c['dims'][2]} mm", className="cont-dims"),
                html.Div(f"{c['vol']} m³  •  max {c['maxw']//1000}t", className="cont-vol"),
                html.Button("✓ Selected" if is_sel else "Select",
                    id={"type":"sel-cont","key":k},
                    className="btn-primary-custom" if is_sel else "btn-outline-custom",
                    style={"marginTop":"10px","fontSize":"12px","padding":"5px 14px"}),
            ], className=f"cont-card {'selected' if is_sel else ''}",
               style={"borderColor":"#1e40af" if is_sel else ""}),
        )

    custom_section = html.Div([
        html.Div([
            html.Div([
                html.Div("Length (mm)", style={"fontSize":"12px","color":"#64748b","marginBottom":"4px"}),
                dcc.Input(id="c-length", type="number", value=cdims.get("length",5900), min=500, max=25000,
                    style={"width":"100%"}),
            ]),
            html.Div([
                html.Div("Width (mm)", style={"fontSize":"12px","color":"#64748b","marginBottom":"4px"}),
                dcc.Input(id="c-width", type="number", value=cdims.get("width",2350), min=500, max=5000,
                    style={"width":"100%"}),
            ]),
            html.Div([
                html.Div("Height (mm)", style={"fontSize":"12px","color":"#64748b","marginBottom":"4px"}),
                dcc.Input(id="c-height", type="number", value=cdims.get("height",2390), min=500, max=5000,
                    style={"width":"100%"}),
            ]),
            html.Div([
                html.Div("Max weight (kg)", style={"fontSize":"12px","color":"#64748b","marginBottom":"4px"}),
                dcc.Input(id="c-maxw", type="number", value=cdims.get("maxw",28000), min=100,
                    style={"width":"100%"}),
            ]),
        ], style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)","gap":"12px"}),
        html.Button("✓ Use custom dimensions", id="btn-use-custom",
            className="btn-primary-custom" if use_custom else "btn-outline-custom",
            style={"marginTop":"12px","fontSize":"12px","padding":"6px 14px"}),
    ], className="panel-card", style={"marginBottom":"1rem"}) if True else html.Div()

    algo_cards = []
    algos = {
        "hdrl": ("Semi-Online HDRL", "Hierarchical Deep Reinforcement Learning — best utilization"),
        "blf":  ("Online Greedy BLF", "Bottom-Left-Fill — fast, good for real-time"),
    }
    for k, (nm, desc) in algos.items():
        is_sel = sel_algo == k
        algo_cards.append(html.Div([
            html.Div(nm, className="cont-name"),
            html.Div(desc, className="cont-dims"),
            html.Button("✓ Selected" if is_sel else "Select",
                id={"type":"sel-algo","key":k},
                className="btn-primary-custom" if is_sel else "btn-outline-custom",
                style={"marginTop":"10px","fontSize":"12px","padding":"5px 14px"}),
        ], className=f"algo-card {'selected' if is_sel else ''}",
           style={"borderColor":"#1e40af" if is_sel else "","flex":"1"}))

    return html.Div([
        html.Div("Container & Truck", className="page-title"),
        html.Div("Choose a standard shipping container or enter your own dimensions.", className="page-sub"),

        html.Div("Standard Containers", className="panel-title"),
        html.Div(cont_cards, style={"display":"grid","gridTemplateColumns":"repeat(2,1fr)","gap":"10px","marginBottom":"1rem"}),

        html.Div("Custom Dimensions", className="panel-title"),
        custom_section,

        html.Hr(className="section-div"),

        html.Div("Packing Algorithm", className="panel-title"),
        html.Div(algo_cards, style={"display":"flex","gap":"12px","marginBottom":"1.25rem"}),

        html.Hr(className="section-div"),

        html.Div([
            html.Button("← Back", id="btn-back-2", className="btn-outline-custom"),
            html.Button("🚀 Calculate stuffing", id="btn-run", className="btn-primary-custom"),
        ], style={"display":"flex","justifyContent":"space-between"}),
    ])


# ── STEP 3 ──────────────────────────────────────────────────────────────────

def render_step3(state):
    placed = state.get("placed_items", [])
    groups = state.get("groups", [])
    anim_step = state.get("anim_step", len(placed))
    cL, cW, cH = get_container_dims(state)
    cont_key = state.get("selected_container","20gp")
    cont_name = "Custom" if state.get("custom_container") else CONTAINERS.get(cont_key,{}).get("name","")

    all_count = sum(it.get("qty",1) for g in groups for it in g["items"])
    packed_count = len(placed)
    used_vol = sum(it.get("width",0)*it.get("length",0)*it.get("height",0) for it in placed)
    cont_vol = cL * cW * cH
    util = (used_vol / cont_vol * 100) if cont_vol > 0 else 0
    total_weight = sum(it.get("weight",0) for it in placed)

    # Figures
    fig_main = make_3d_figure(placed, cL, cW, cH, step_n=anim_step, height=380)

    # Progress
    pct = (anim_step / len(placed) * 100) if len(placed) > 0 else 0

    banner_cls = "" if packed_count >= all_count else "warn"
    banner_icon = "✅" if packed_count >= all_count else "⚠️"
    banner_msg  = (f"All {packed_count} items placed — {util:.1f}% utilization"
                   if packed_count >= all_count
                   else f"{packed_count}/{all_count} items placed — {all_count-packed_count} did not fit. Utilization: {util:.1f}%")

    # Placement table rows
    table_rows = []
    for idx, it in enumerate(placed[:anim_step]):
        ci = it.get("color_idx", idx)
        col = BOX_COLORS[ci % len(BOX_COLORS)]
        table_rows.append(html.Tr([
            html.Td(idx+1),
            html.Td([
                html.Span(style={"display":"inline-block","width":"10px","height":"10px","borderRadius":"2px","background":col,"marginRight":"5px","verticalAlign":"middle"}),
                it.get("name","") or "Item"
            ]),
            html.Td(it.get("type","Box")),
            html.Td(it.get("length",0)), html.Td(it.get("width",0)), html.Td(it.get("height",0)),
            html.Td(it.get("weight",0)),
            html.Td(it.get("pos_x",0)), html.Td(it.get("pos_y",0)), html.Td(it.get("pos_z",0)),
        ], style={"background":"#f8fafc" if idx%2==0 else "#fff"}))

    # CSV for download
    df_exp = pd.DataFrame(placed) if placed else pd.DataFrame()
    csv_str = df_exp.to_csv(index=False) if not df_exp.empty else ""

    is_playing = state.get("anim_playing", False)

    return html.Div([
        html.Div("Stuffing Result", className="page-title"),
        html.Div(f"Algorithm: {state.get('selected_algo','hdrl').upper()}  •  Container: {cont_name}  •  {cL}×{cW}×{cH} mm", className="page-sub"),

        # Banner
        html.Div([
            html.Span(banner_icon, style={"fontSize":"20px"}),
            html.Span(banner_msg),
        ], className=f"result-banner {banner_cls}"),

        # Metrics
        html.Div([
            html.Div([html.Div("Utilization",    className="metric-label"), html.Div(f"{util:.1f}%",             className="metric-value", style={"color":"#1e40af"})], className="metric-card"),
            html.Div([html.Div("Items packed",   className="metric-label"), html.Div(f"{packed_count}/{all_count}", className="metric-value", style={"color":"#16a34a"})], className="metric-card"),
            html.Div([html.Div("Total weight",   className="metric-label"), html.Div(f"{total_weight:.0f} kg",   className="metric-value", style={"color":"#b45309"})], className="metric-card"),
            html.Div([html.Div("Used volume",    className="metric-label"), html.Div(f"{used_vol/1e9:.2f} m³",   className="metric-value", style={"color":"#7c3aed"})], className="metric-card"),
        ], style={"display":"flex","gap":"12px","marginBottom":"1.25rem"}),

        # 3D visualization + controls
        html.Div([
            html.Div("📊 3D Packing Visualization", className="panel-title"),
            dcc.Graph(id="main-3d", figure=fig_main, config={"displayModeBar":False}),
            html.Div([html.Div(style={"width":f"{pct:.1f}%"}, className="prog-bar")], className="prog-wrap"),
            html.Div([
                dcc.Slider(id="anim-slider", min=0, max=len(placed), value=anim_step, step=1,
                    marks=None, tooltip={"placement":"bottom","always_visible":False}),
            ], style={"margin":"4px 0 10px"}),
            html.Div([
                html.Button("⏮", id="btn-first", className="btn-outline-custom", style={"padding":"6px 10px"}),
                html.Button("◀",  id="btn-prev",  className="btn-outline-custom", style={"padding":"6px 10px"}),
                html.Button("⏸ Pause" if is_playing else "▶ Play",
                    id="btn-play", className="btn-primary-custom", style={"padding":"6px 14px"}),
                html.Button("▶",  id="btn-next",  className="btn-outline-custom", style={"padding":"6px 10px"}),
                html.Button("⏭", id="btn-last",  className="btn-outline-custom", style={"padding":"6px 10px"}),
                dcc.Dropdown(id="anim-speed", options=[
                    {"label":"Slow","value":400},{"label":"Normal","value":180},{"label":"Fast","value":60}
                ], value=180, clearable=False,
                style={"width":"90px","fontSize":"12px"}),
            ], style={"display":"flex","gap":"6px","alignItems":"center","flexWrap":"wrap"}),
        ], className="panel-card"),

        # Placement table
        html.Div([
            html.Div("📋 Placement Detail", className="panel-title"),
            html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th("#"), html.Th("Name"), html.Th("Type"),
                        html.Th("L"), html.Th("W"), html.Th("H"), html.Th("Wt"),
                        html.Th("Pos X"), html.Th("Pos Y"), html.Th("Pos Z"),
                    ])),
                    html.Tbody(table_rows),
                ], className="placement-table"),
            ], style={"maxHeight":"200px","overflowY":"auto","overflowX":"auto"}),
        ], className="panel-card"),

        html.Hr(className="section-div"),

        # Footer nav
        html.Div([
            html.Div([
                html.Button("← Back", id="btn-back-3", className="btn-outline-custom", style={"marginRight":"8px"}),
                html.Button("🔄 Replay", id="btn-replay", className="btn-outline-custom"),
            ]),
            html.Div([
                dcc.Download(id="download-csv"),
                html.Button("📥 Export CSV", id="btn-export", className="btn-outline-custom", style={"marginRight":"8px"}),
                html.Button("🚀 New calculation", id="btn-new", className="btn-primary-custom"),
            ]),
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center"}),
    ])


app.validation_layout = html.Div([
    app.layout,
    render_step1(INITIAL_STATE),
    render_step2(INITIAL_STATE),
    render_step3(INITIAL_STATE),
])


# ==============================================================================
# MASTER STATE CALLBACK
# ==============================================================================

@app.callback(
    Output("app-state","data"),
    Output("anim-interval","disabled"),
    Output("anim-interval","interval"),
    # ── Step 1 inputs
    Input("btn-sample","n_clicks", allow_optional=True),
    Input("btn-clear","n_clicks", allow_optional=True),
    Input("btn-add-group","n_clicks", allow_optional=True),
    Input("btn-next-1","n_clicks", allow_optional=True),
    Input({"type":"add-item","gi":ALL},"n_clicks", allow_optional=True),
    Input({"type":"del-item","gi":ALL,"ii":ALL},"n_clicks", allow_optional=True),
    Input({"type":"del-group","gi":ALL},"n_clicks", allow_optional=True),
    # Input field changes (pattern match)
    Input({"type":"item-name","gi":ALL,"ii":ALL},"value", allow_optional=True),
    Input({"type":"item-type","gi":ALL,"ii":ALL},"value", allow_optional=True),
    Input({"type":"item-length","gi":ALL,"ii":ALL},"value", allow_optional=True),
    Input({"type":"item-width","gi":ALL,"ii":ALL},"value", allow_optional=True),
    Input({"type":"item-height","gi":ALL,"ii":ALL},"value", allow_optional=True),
    Input({"type":"item-weight","gi":ALL,"ii":ALL},"value", allow_optional=True),
    Input({"type":"item-qty","gi":ALL,"ii":ALL},"value", allow_optional=True),
    Input({"type":"item-color","gi":ALL,"ii":ALL},"value", allow_optional=True),
    Input({"type":"item-stack","gi":ALL,"ii":ALL},"value", allow_optional=True),
    # ── Step 2 inputs
    Input({"type":"sel-cont","key":ALL},"n_clicks", allow_optional=True),
    Input({"type":"sel-algo","key":ALL},"n_clicks", allow_optional=True),
    Input("btn-use-custom","n_clicks", allow_optional=True),
    Input("btn-back-2","n_clicks", allow_optional=True),
    Input("btn-run","n_clicks", allow_optional=True),
    Input("c-length","value", allow_optional=True), Input("c-width","value", allow_optional=True),
    Input("c-height","value", allow_optional=True), Input("c-maxw","value", allow_optional=True),
    # ── Step 3 inputs
    Input("btn-back-3","n_clicks", allow_optional=True),
    Input("btn-new","n_clicks", allow_optional=True),
    Input("btn-replay","n_clicks", allow_optional=True),
    Input("btn-first","n_clicks", allow_optional=True),
    Input("btn-prev","n_clicks", allow_optional=True),
    Input("btn-play","n_clicks", allow_optional=True),
    Input("btn-next","n_clicks", allow_optional=True),
    Input("btn-last","n_clicks", allow_optional=True),
    Input("anim-slider","value", allow_optional=True),
    Input("anim-interval","n_intervals", allow_optional=True),
    Input("anim-speed","value", allow_optional=True),
    State("app-state","data"),
    prevent_initial_call=True,
)
def master_callback(*args):
    state = json.loads(args[-1])
    trigger = ctx.triggered_id

    placed = state.get("placed_items",[])
    is_playing = state.get("anim_playing", False)
    speed = 180

    # ── Speed dropdown ──────────────────────────────
    speed_val = args[-2]
    if speed_val:
        speed = int(speed_val)

    # ── Animation interval tick ──────────────────────
    if trigger == "anim-interval":
        if is_playing:
            cur = state.get("anim_step", 0)
            if cur < len(placed):
                state["anim_step"] = cur + 1
            else:
                state["anim_playing"] = False
        return json.dumps(state), not state.get("anim_playing",False), speed

    # ── Step 1 actions ───────────────────────────────
    if trigger == "btn-sample":
        state["groups"] = [{"id":"g1","name":"Group #1","color":GROUP_PALETTE[0],"items":SAMPLE_ITEMS[:]}]
        state["placed_items"] = []
        return json.dumps(state), True, speed

    if trigger == "btn-clear":
        state["groups"] = []
        state["placed_items"] = []
        return json.dumps(state), True, speed

    if trigger == "btn-add-group":
        idx = len(state["groups"])
        state["groups"].append({"id":make_uid(),"name":f"Group #{idx+1}","color":GROUP_PALETTE[idx%len(GROUP_PALETTE)],"items":[]})
        return json.dumps(state), True, speed

    if trigger == "btn-next-1":
        if state.get("groups"):
            state["step"] = 2
        return json.dumps(state), True, speed

    if isinstance(trigger, dict):
        t = trigger.get("type","")
        gi = trigger.get("gi", None)
        ii = trigger.get("ii", None)
        key = trigger.get("key", None)

        if t == "add-item" and gi is not None:
            g = state["groups"][gi]
            idx = len(g["items"])
            g["items"].append({"name":"","type":"Box","length":500,"width":400,"height":300,
                                "weight":10.0,"qty":1,"color_idx":idx,"stackable":True})
            return json.dumps(state), True, speed

        if t == "del-item" and gi is not None and ii is not None:
            state["groups"][gi]["items"].pop(ii)
            if not state["groups"][gi]["items"]:
                state["groups"].pop(gi)
            return json.dumps(state), True, speed

        if t == "del-group" and gi is not None:
            state["groups"].pop(gi)
            return json.dumps(state), True, speed

        # Item field updates — sync all pattern-matched values back to state
        item_field_map = {
            "item-name":"name","item-type":"type","item-length":"length",
            "item-width":"width","item-height":"height","item-weight":"weight",
            "item-qty":"qty","item-color":"color_idx","item-stack":"stackable",
        }
        if t in item_field_map and gi is not None and ii is not None:
            # Find the value from ctx.triggered
            field = item_field_map[t]
            for trig in ctx.triggered:
                if trig["prop_id"] != ".":
                    try:
                        tid = json.loads(trig["prop_id"].split(".")[0])
                        if tid.get("type")==t and tid.get("gi")==gi and tid.get("ii")==ii:
                            val = trig["value"]
                            if field == "stackable":
                                val = bool(val)
                            elif field == "color_idx":
                                val = int(val or 0)
                            elif field not in ("name","type"):
                                val = float(val or 0) if field=="weight" else int(val or 1)
                            if gi < len(state["groups"]) and ii < len(state["groups"][gi]["items"]):
                                state["groups"][gi]["items"][ii][field] = val
                    except Exception:
                        pass
            return json.dumps(state), True, speed

        # Step 2 container/algo selection
        if t == "sel-cont" and key:
            state["selected_container"] = key
            state["custom_container"] = False
            return json.dumps(state), True, speed

        if t == "sel-algo" and key:
            state["selected_algo"] = key
            return json.dumps(state), True, speed

    # ── Step 2 actions ───────────────────────────────
    if trigger == "btn-use-custom":
        state["custom_container"] = True
        for k, arg_k in [("c-length","length"),("c-width","width"),("c-height","height"),("c-maxw","maxw")]:
            for trig in ctx.triggered:
                pass  # handled separately
        return json.dumps(state), True, speed

    if trigger in ("c-length","c-width","c-height","c-maxw"):
        key_map = {"c-length":"length","c-width":"width","c-height":"height","c-maxw":"maxw"}
        for trig in ctx.triggered:
            pid = trig["prop_id"].split(".")[0]
            if pid in key_map:
                if "custom_dims" not in state:
                    state["custom_dims"] = {}
                state["custom_dims"][key_map[pid]] = trig["value"] or 0
        return json.dumps(state), True, speed

    if trigger == "btn-back-2":
        state["step"] = 1
        return json.dumps(state), True, speed

    if trigger == "btn-run":
        # Run packing
        all_items = []
        for gi, g in enumerate(state.get("groups",[])):
            for ii, it in enumerate(g["items"]):
                for _ in range(max(1, it.get("qty",1))):
                    all_items.append({**it,"_gi":gi,"_ii":ii})
        if all_items:
            cL, cW, cH = get_container_dims(state)
            placed = pack_blf(all_items, cL, cW, cH)
            state["placed_items"] = placed
            state["anim_step"] = len(placed)
            state["anim_playing"] = False
        state["step"] = 3
        return json.dumps(state), True, speed

    # ── Step 3 actions ───────────────────────────────
    if trigger == "btn-back-3":
        state["step"] = 2
        state["anim_playing"] = False
        return json.dumps(state), True, speed

    if trigger == "btn-new":
        state["step"] = 1
        state["groups"] = []
        state["placed_items"] = []
        state["anim_playing"] = False
        return json.dumps(state), True, speed

    if trigger == "btn-replay":
        state["anim_step"] = 0
        state["anim_playing"] = True
        return json.dumps(state), False, speed

    if trigger == "btn-first":
        state["anim_step"] = 1
        state["anim_playing"] = False
        return json.dumps(state), True, speed

    if trigger == "btn-last":
        state["anim_step"] = len(placed)
        state["anim_playing"] = False
        return json.dumps(state), True, speed

    if trigger == "btn-prev":
        state["anim_step"] = max(0, state.get("anim_step",0) - 1)
        state["anim_playing"] = False
        return json.dumps(state), True, speed

    if trigger == "btn-next":
        state["anim_step"] = min(len(placed), state.get("anim_step",0) + 1)
        state["anim_playing"] = False
        return json.dumps(state), True, speed

    if trigger == "btn-play":
        playing = not state.get("anim_playing", False)
        state["anim_playing"] = playing
        if playing and state.get("anim_step",0) >= len(placed):
            state["anim_step"] = 0
        return json.dumps(state), not playing, speed

    if trigger == "anim-slider":
        for trig in ctx.triggered:
            if "anim-slider" in trig["prop_id"]:
                state["anim_step"] = int(trig["value"] or 0)
        state["anim_playing"] = False
        return json.dumps(state), True, speed

    return json.dumps(state), not is_playing, speed


# ── CSV Download ──────────────────────────────────────────────────────────────

@app.callback(
    Output("download-csv","data"),
    Input("btn-export","n_clicks"),
    State("app-state","data"),
    prevent_initial_call=True,
)
def export_csv(n, state_json):
    if not n:
        return no_update
    state = json.loads(state_json)
    placed = state.get("placed_items",[])
    if not placed:
        return no_update
    df = pd.DataFrame(placed)
    return dcc.send_data_frame(df.to_csv, "packing_result.csv", index=False)


# ==============================================================================
# RUN
# ==============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=8050)