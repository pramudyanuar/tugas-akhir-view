# ==============================================================================
# 3DBPP SEMI-ONLINE WITH HIERARCHICAL DRL — DASH APP (SeaRates Style)
# Run: python app_3dbpp_dash.py
# ==============================================================================

import json
import time
import uuid
import threading

import dash
from dash import dcc, html, Input, Output, State, ALL, MATCH, ctx, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from model_utils import pack_hierarchical_drl

# Global dictionary to track background DRL packing progress
PACKING_PROGRESS = {
    "active": False,
    "current": 0,
    "total": 0,
    "placed_count": 0,
    "result": None,
    "error": None
}

def bg_packing_worker(items, cL, cW, cH, model_name):
    global PACKING_PROGRESS
    try:
        def progress_cb(current, placed):
            PACKING_PROGRESS["current"] = current
            PACKING_PROGRESS["placed_count"] = placed
            
        placed = pack_hierarchical_drl(items, cL, cW, cH, model_name=model_name, progress_callback=progress_cb)
        PACKING_PROGRESS["result"] = placed
    except Exception as e:
        import traceback
        PACKING_PROGRESS["error"] = str(e)
        print("[BG Packing Error]", traceback.format_exc())
    finally:
        PACKING_PROGRESS["active"] = False


# ==============================================================================
# APP INIT
# ==============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap",
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
    "#4f46e5", "#ec4899", "#8b5cf6", "#10b981",
    "#f59e0b", "#eab308", "#14b8a6", "#ef4444",
    "#a855f7", "#06b6d4", "#22c55e", "#fda4af",
]
GROUP_PALETTE = ["#1e293b", "#3b82f6", "#6366f1", "#d97706", "#dc2626", "#16a34a"]

CONTAINERS = {
    "20gp": {"name": "20' Standard GP",  "dims": (5900, 2350, 2390), "maxw": 28000, "vol": 33.1},
    "40gp": {"name": "40' Standard GP",  "dims": (12032, 2350, 2390), "maxw": 27000, "vol": 67.6},
    "40hc": {"name": "40' High Cube HC", "dims": (12032, 2350, 2695), "maxw": 26500, "vol": 76.3},
    "lkw":  {"name": "Truck / LKW",      "dims": (13600, 2480, 2700), "maxw": 24000, "vol": 90.7},
}

ITEM_TYPES = ["Box"]

SAMPLE_ITEMS = [
    {"name": "Cargo Box Type A", "type": "Box", "length": 983, "width": 587, "height": 552, "weight": 20.0, "qty": 20, "color_idx": 0, "stackable": True},
    {"name": "Cargo Box Type B", "type": "Box", "length": 983, "width": 587, "height": 552, "weight": 20.0, "qty": 20, "color_idx": 2, "stackable": True},
    {"name": "Cargo Box Type C", "type": "Box", "length": 983, "width": 587, "height": 552, "weight": 20.0, "qty": 20, "color_idx": 5, "stackable": True},
    {"name": "Cargo Box Type D", "type": "Box", "length": 983, "width": 587, "height": 552, "weight": 20.0, "qty": 20, "color_idx": 8, "stackable": True},
]

# ==============================================================================
# CSS
# ==============================================================================

STYLES = """
.spinner-custom {
    width: 40px;
    height: 40px;
    border: 4px solid #e2e8f0;
    border-top: 4px solid #4f46e5;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    display: inline-block;
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

* { box-sizing: border-box; }
body, html {
    font-family: 'Inter', sans-serif !important;
    background: #f8fafc !important;
    color: #0f172a !important;
    margin: 0; padding: 0;
    -webkit-font-smoothing: antialiased;
}
h1, h2, h3, h4, .page-title, .topnav-brand {
    font-family: 'Outfit', sans-serif !important;
}
/* NAV */
.topnav {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(226, 232, 240, 0.8);
    padding: 0 3rem;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky; top: 0; z-index: 100;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.02);
}
.topnav-brand { 
    font-size: 20px; 
    font-weight: 700; 
    background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex; 
    align-items: center; 
    gap: 10px; 
    letter-spacing: -0.03em; 
}
.topnav-sub { 
    font-size: 13px; 
    color: #64748b; 
    font-weight: 400; 
    -webkit-text-fill-color: initial;
    font-family: 'Inter', sans-serif !important;
    margin-left: 8px;
    padding-left: 8px;
    border-left: 1px solid #e2e8f0;
}
/* STEP TABS */
.step-nav {
    background: #fff;
    border-bottom: 1px solid #e2e8f0;
    padding: 0 3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    position: sticky; top: 64px; z-index: 99;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01);
}
.step-tab {
    display: flex; align-items: center; gap: 10px;
    padding: 18px 24px; cursor: pointer;
    border-bottom: 3px solid transparent;
    color: #94a3b8; font-size: 14px; font-weight: 600;
    text-decoration: none; transition: all 0.25s ease; user-select: none;
}
.step-tab.active { 
    color: #4f46e5; 
    border-bottom-color: #4f46e5; 
}
.step-tab.done { 
    color: #10b981; 
}
.step-num {
    width: 26px; height: 26px; border-radius: 50%;
    background: #f1f5f9; color: #94a3b8;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700;
    transition: all 0.25s ease;
}
.step-tab.active .step-num { 
    background: #4f46e5; 
    color: #fff; 
    box-shadow: 0 0 12px rgba(79, 70, 229, 0.4);
}
.step-tab.done .step-num { 
    background: #10b981; 
    color: #fff; 
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
}
.step-arrow { color: #cbd5e1; font-size: 24px; padding: 0 12px; }
/* PAGE */
.page-wrap { max-width: 1080px; margin: 0 auto; padding: 2.5rem 1.5rem 5rem; }
.page-title { font-size: 26px; font-weight: 700; color: #0f172a; margin-bottom: 6px; letter-spacing: -0.03em; }
.page-sub   { font-size: 14px; color: #64748b; margin-bottom: 2rem; }
/* CARDS */
.panel-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 16px; padding: 1.5rem 1.75rem; margin-bottom: 1.25rem;
    box-shadow: 0 4px 20px -2px rgba(0,0,0,0.03);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.panel-title { 
    font-size: 12px; 
    font-weight: 700; 
    color: #64748b; 
    text-transform: uppercase; 
    letter-spacing: .08em; 
    margin-bottom: 1.25rem; 
    display: flex;
    align-items: center;
    gap: 8px;
}
.group-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 16px; padding: 1.5rem 1.75rem; margin-bottom: 1.25rem;
    box-shadow: 0 4px 20px -2px rgba(0,0,0,0.03);
}
.group-hdr {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1.25rem; padding-bottom: 1rem; border-bottom: 1px solid #f1f5f9;
}
/* CONTAINER CARDS */
.cont-card {
    background: #fff; border: 1.5px solid #e2e8f0;
    border-radius: 14px; padding: 18px 22px; cursor: pointer;
    transition: all .2s ease; margin-bottom: 10px;
    position: relative;
    overflow: hidden;
}
.cont-card:hover { 
    border-color: #a5b4fc; 
    background: #f8fafc;
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04);
}
.cont-card.selected { 
    border-color: #4f46e5 !important; 
    background: #f5f3ff !important; 
    box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.1);
}
.cont-name { font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
.cont-dims { font-size: 13px; color: #64748b; font-family: 'JetBrains Mono', monospace; }
.cont-vol  { font-size: 13px; color: #4f46e5; font-weight: 600; margin-top: 6px; }
/* ALGO CARDS */
.algo-card {
    background: #fff; border: 1.5px solid #e2e8f0;
    border-radius: 14px; padding: 18px 22px; cursor: pointer;
    transition: all .2s ease;
}
.algo-card:hover {
    border-color: #a5b4fc;
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04);
}
.algo-card.selected { 
    border-color: #4f46e5; 
    background: #f5f3ff; 
    box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.1);
}
/* METRICS */
.metric-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 16px; padding: 18px 22px; text-align: center; flex: 1;
    box-shadow: 0 4px 20px -2px rgba(0,0,0,0.02);
    border-top: 4px solid #4f46e5;
    transition: transform 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
}
.metric-label { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: .06em; font-weight: 600; margin-bottom: 8px; }
.metric-value { font-family: 'Outfit', sans-serif; font-size: 26px; font-weight: 700; }
/* BANNER */
.result-banner {
    background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 12px;
    padding: 16px 24px; display: flex; align-items: center; gap: 14px;
    margin-bottom: 1.5rem; font-size: 14px; color: #065f46; font-weight: 600;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.05);
}
.result-banner.warn { 
    background: #fffbeb; border-color: #fde68a; color: #92400e; 
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.05);
}
/* TABLE */
.placement-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.placement-table th {
    background: #f8fafc; color: #475569; font-weight: 700;
    font-size: 11px; text-transform: uppercase; letter-spacing: .06em;
    padding: 12px 14px; border-bottom: 2px solid #e2e8f0; text-align: center;
}
.placement-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; text-align: center; color: #334155; }
.placement-table tr:hover td { background: #f5f3ff; }
/* BUTTONS */
.btn-primary-custom {
    background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
    color: #fff; border: none;
    border-radius: 10px; padding: 10px 24px; font-size: 14px;
    font-weight: 600; cursor: pointer; transition: all .2s ease;
    font-family: 'Inter', sans-serif;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
    display: inline-flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-primary-custom:hover { 
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);
    filter: brightness(1.05);
}
.btn-primary-custom:active {
    transform: translateY(1px);
}
.btn-outline-custom {
    background: #fff; color: #334155; border: 1px solid #cbd5e1;
    border-radius: 10px; padding: 10px 20px; font-size: 14px;
    font-weight: 600; cursor: pointer; font-family: 'Inter', sans-serif;
    transition: all .2s ease;
    display: inline-flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-outline-custom:hover { 
    background: #f8fafc; 
    border-color: #94a3b8;
    transform: translateY(-1px);
}
.btn-danger-custom {
    background: #fff; color: #ef4444; border: 1px solid #fee2e2;
    border-radius: 8px; padding: 8px 14px; font-size: 13px;
    font-weight: 600; cursor: pointer; font-family: 'Inter', sans-serif;
    transition: all .2s ease;
}
.btn-danger-custom:hover { 
    background: #fef2f2; 
    border-color: #fca5a5;
}
/* PROGRESS BAR */
.prog-wrap { background: #f1f5f9; border-radius: 999px; height: 8px; margin: 12px 0; overflow: hidden; }
.prog-bar  { height: 8px; border-radius: 999px; background: linear-gradient(90deg, #4f46e5, #3b82f6); transition: width .3s ease; }
/* INPUTS */
.dash-input, .dash-dropdown .Select-control {
    border: 1px solid #cbd5e1 !important; border-radius: 10px !important;
    font-size: 14px !important; font-family: 'Inter', sans-serif !important;
    color: #0f172a !important;
    transition: all 0.2s ease;
}
input[type=number], input[type=text] {
    border: 1px solid #cbd5e1; border-radius: 8px; padding: 6px 10px;
    font-size: 14px; font-family: 'Inter', sans-serif; color: #0f172a;
    width: 100%; outline: none;
    transition: all 0.2s ease;
}
input[type=number]:focus, input[type=text]:focus { 
    border-color: #6366f1; 
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15); 
}
select {
    border: 1px solid #cbd5e1; border-radius: 8px; padding: 6px 10px;
    font-size: 14px; font-family: 'Inter', sans-serif; color: #0f172a;
    background: #fff; outline: none; width: 100%;
    transition: all 0.2s ease;
}
select:focus {
    border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}
.step-label { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #64748b; margin-bottom: 8px; }
.section-div { border: none; border-top: 1px solid #e2e8f0; margin: 1.75rem 0; }
.chip { display: inline-flex; align-items: center; gap: 6px; background: #f1f5f9; border-radius: 999px; padding: 6px 14px; font-size: 13px; color: #475569; font-weight: 600; margin-right: 8px; }
.chip-blue { background: #e0e7ff; color: #4338ca; }
.empty-state { text-align: center; padding: 4rem 2rem; background: #fff; border: 2px dashed #cbd5e1; border-radius: 16px; margin-bottom: 1.25rem; }
/* scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f8fafc; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
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
    "selected_model": "no-buffer",
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
    
    # 1. Real Container Visuals: Solid Floor (Slate Wood)
    fig.add_trace(go.Mesh3d(
        x=[0, cW, cW, 0],
        y=[0, 0, cL, cL],
        z=[0, 0, 0, 0],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color="#334155", opacity=0.18, flatshading=True, showlegend=False, hoverinfo="skip"
    ))
    
    # Real Container Visuals: Semi-transparent Metallic Walls
    # Back Wall (Y = cL)
    fig.add_trace(go.Mesh3d(
        x=[0, cW, cW, 0],
        y=[cL, cL, cL, cL],
        z=[0, 0, cH, cH],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color="#475569", opacity=0.08, flatshading=True, showlegend=False, hoverinfo="skip"
    ))
    # Left Wall (X = 0)
    fig.add_trace(go.Mesh3d(
        x=[0, 0, 0, 0],
        y=[0, cL, cL, 0],
        z=[0, 0, cH, cH],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color="#475569", opacity=0.05, flatshading=True, showlegend=False, hoverinfo="skip"
    ))
    # Right Wall (X = cW)
    fig.add_trace(go.Mesh3d(
        x=[cW, cW, cW, cW],
        y=[0, cL, cL, 0],
        z=[0, 0, cH, cH],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color="#475569", opacity=0.05, flatshading=True, showlegend=False, hoverinfo="skip"
    ))

    # Real Container Visuals: Open Door Panels at the Front (Y = 0)
    door_w = cW / 2
    dx = - door_w * 0.707
    dy = - door_w * 0.707
    # Left Door Panel Outline & Surface
    fig.add_trace(go.Scatter3d(x=[0, dx, dx, 0, 0], y=[0, dy, dy, 0, 0], z=[0, 0, cH, cH, 0], mode="lines",
        line=dict(color="#1e293b", width=2.5), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Mesh3d(x=[0, dx, dx, 0], y=[0, dy, dy, 0], z=[0, 0, cH, cH], i=[0, 0], j=[1, 2], k=[2, 3],
        color="#475569", opacity=0.15, flatshading=True, showlegend=False, hoverinfo="skip"))
    # Right Door Panel Outline & Surface
    fig.add_trace(go.Scatter3d(x=[cW, cW - dx, cW - dx, cW, cW], y=[0, dy, dy, 0, 0], z=[0, 0, cH, cH, 0], mode="lines",
        line=dict(color="#1e293b", width=2.5), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Mesh3d(x=[cW, cW - dx, cW - dx, cW], y=[0, dy, dy, 0], z=[0, 0, cH, cH], i=[0, 0], j=[1, 2], k=[2, 3],
        color="#475569", opacity=0.15, flatshading=True, showlegend=False, hoverinfo="skip"))
    # Text label for Front Door
    fig.add_trace(go.Scatter3d(x=[cW / 2], y=[dy * 0.7], z=[cH / 2], mode="text",
        text=["🚪 PINTU DEPAN (DOOR)"], textposition="middle center",
        textfont=dict(family="Outfit, sans-serif", size=10, color="#475569"), showlegend=False, hoverinfo="skip"))

    # Real Container Visuals: Corrugated Steel Ribs (Vertical lines every 300mm)
    rib_x, rib_y, rib_z = [], [], []
    # Left wall ribs
    for y in range(0, int(cL), 300):
        rib_x += [0, 0, None]
        rib_y += [y, y, None]
        rib_z += [0, cH, None]
    # Right wall ribs
    for y in range(0, int(cL), 300):
        rib_x += [cW, cW, None]
        rib_y += [y, y, None]
        rib_z += [0, cH, None]
    # Back wall ribs
    for x in range(0, int(cW), 300):
        rib_x += [x, x, None]
        rib_y += [cL, cL, None]
        rib_z += [0, cH, None]
        
    fig.add_trace(go.Scatter3d(
        x=rib_x, y=rib_y, z=rib_z, mode="lines",
        line=dict(color="rgba(148, 163, 184, 0.22)", width=1.2), showlegend=False, hoverinfo="skip"
    ))

    # Container Wireframe Outline (Main edges)
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
        line=dict(color="#475569", width=1.8), showlegend=False, hoverinfo="skip"))

    items_to_show = placed[:step_n] if step_n is not None else placed
    
    # Group boxes by color to minimize the number of WebGL draw calls
    from collections import defaultdict
    color_groups = defaultdict(list)
    
    # Combine all box wireframe outlines into a single Scatter3d trace
    ox, oy, oz = [], [], []
    
    for idx, item in enumerate(items_to_show):
        ci = item.get("color_idx", idx)
        color_idx = ci % len(BOX_COLORS)
        color_groups[color_idx].append(item)
        
        x0, y0, z0 = item["pos_x"], item["pos_y"], item["pos_z"]
        w, l, h = item.get("width", 300), item.get("length", 500), item.get("height", 300)
        x1, y1, z1 = x0+w, y0+l, z0+h
        vx = [x0,x1,x1,x0,x0,x1,x1,x0]
        vy = [y0,y0,y1,y1,y0,y0,y1,y1]
        vz = [z0,z0,z0,z0,z1,z1,z1,z1]
        
        for a, b in [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]:
            ox += [vx[a], vx[b], None]
            oy += [vy[a], vy[b], None]
            oz += [vz[a], vz[b], None]
            
    if ox:
        fig.add_trace(go.Scatter3d(x=ox, y=oy, z=oz, mode="lines",
            line=dict(color="rgba(255,255,255,0.4)", width=1.0), showlegend=False, hoverinfo="skip"))

    # Create a single Mesh3d trace for each color group
    for color_idx, group_items in color_groups.items():
        color = BOX_COLORS[color_idx]
        all_vx, all_vy, all_vz = [], [], []
        all_fi, all_fj, all_fk = [], [], []
        
        for box_idx, item in enumerate(group_items):
            x0, y0, z0 = item["pos_x"], item["pos_y"], item["pos_z"]
            w, l, h = item.get("width", 300), item.get("length", 500), item.get("height", 300)
            x1, y1, z1 = x0+w, y0+l, z0+h
            
            # Vertices
            all_vx += [x0,x1,x1,x0,x0,x1,x1,x0]
            all_vy += [y0,y0,y1,y1,y0,y0,y1,y1]
            all_vz += [z0,z0,z0,z0,z1,z1,z1,z1]
            
            # Triangles (offset by 8 vertices per box)
            offset = box_idx * 8
            fi = [0,0,0,4,4,4,0,0,1,5,2,6]
            fj = [1,2,4,5,6,7,1,2,2,6,3,7]
            fk = [2,3,5,6,7,3,5,4,6,2,7,3]
            all_fi += [f + offset for f in fi]
            all_fj += [f + offset for f in fj]
            all_fk += [f + offset for f in fk]
            
        fig.add_trace(go.Mesh3d(
            x=all_vx, y=all_vy, z=all_vz,
            i=all_fi, j=all_fj, k=all_fk,
            color=color, opacity=0.85, flatshading=True, showlegend=False,
            hoverinfo="skip"
        ))

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
            ], style={"flex":"0 0 85px"}),
            # Width
            html.Div([
                dcc.Input(value=item.get("width",400), type="number", min=1, max=10000,
                    id={"type":"item-width","gi":gi,"ii":ii}, style={"width":"100%"})
            ], style={"flex":"0 0 85px"}),
            # Height
            html.Div([
                dcc.Input(value=item.get("height",300), type="number", min=1, max=10000,
                    id={"type":"item-height","gi":gi,"ii":ii}, style={"width":"100%"})
            ], style={"flex":"0 0 85px"}),
            # Weight
            html.Div([
                dcc.Input(value=item.get("weight",10), type="number", min=0, step=0.5,
                    id={"type":"item-weight","gi":gi,"ii":ii}, style={"width":"100%"})
            ], style={"flex":"0 0 85px"}),
            # Qty
            html.Div([
                dcc.Input(value=item.get("qty",1), type="number", min=1, max=500,
                    id={"type":"item-qty","gi":gi,"ii":ii}, style={"width":"100%"})
            ], style={"flex":"0 0 70px"}),
            # Color dot + index
            html.Div([
                html.Div(style={
                    "width":"16px","height":"16px","borderRadius":"4px",
                    "background":color,"display":"inline-block","verticalAlign":"middle","marginRight":"8px",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                }),
                dcc.Input(value=ci, type="number", min=0, max=11,
                    id={"type":"item-color","gi":gi,"ii":ii},
                    style={"width":"45px","display":"inline-block"})
            ], style={"flex":"0 0 80px","display":"flex","alignItems":"center"}),
            # Stackable checkbox
            html.Div([
                dcc.Checklist(options=[{"label":" Stack","value":"s"}],
                    value=["s"] if item.get("stackable",True) else [],
                    id={"type":"item-stack","gi":gi,"ii":ii},
                    style={"fontSize":"13px", "fontWeight": "500"})
            ], style={"flex":"0 0 80px"}),
            # Delete
            html.Div([
                html.Button(html.I(className="ti ti-trash-x"), id={"type":"del-item","gi":gi,"ii":ii},
                    className="btn-danger-custom", style={"padding": "6px 10px"})
            ], style={"flex":"0 0 40px"}),
        ], style={
            "display":"flex","gap":"10px","alignItems":"center",
            "padding":"10px 0","borderBottom":"1px solid #f1f5f9"
        }),
    ])


def build_group_section(gi, group):
    dot_color = group.get("color", GROUP_PALETTE[gi % len(GROUP_PALETTE)])
    items_html = [
        # Table header
        html.Div([
            html.Div("Type",      style={"flex":"0 0 100px","fontSize":"11px","color":"#64748b","fontWeight":"700","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("Name",      style={"flex":"1 1 130px","fontSize":"11px","color":"#64748b","fontWeight":"700","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("L (mm)",    style={"flex":"0 0 85px","fontSize":"11px","color":"#64748b","fontWeight":"700","textTransform":"uppercase","letterSpacing":".05em","textAlign":"center"}),
            html.Div("W (mm)",    style={"flex":"0 0 85px","fontSize":"11px","color":"#64748b","fontWeight":"700","textTransform":"uppercase","letterSpacing":".05em","textAlign":"center"}),
            html.Div("H (mm)",    style={"flex":"0 0 85px","fontSize":"11px","color":"#64748b","fontWeight":"700","textTransform":"uppercase","letterSpacing":".05em","textAlign":"center"}),
            html.Div("Wt (kg)",   style={"flex":"0 0 85px","fontSize":"11px","color":"#64748b","fontWeight":"700","textTransform":"uppercase","letterSpacing":".05em","textAlign":"center"}),
            html.Div("Qty",       style={"flex":"0 0 70px","fontSize":"11px","color":"#64748b","fontWeight":"700","textTransform":"uppercase","letterSpacing":".05em","textAlign":"center"}),
            html.Div("Color",     style={"flex":"0 0 80px","fontSize":"11px","color":"#64748b","fontWeight":"700","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("Stack",     style={"flex":"0 0 80px","fontSize":"11px","color":"#64748b","fontWeight":"700","textTransform":"uppercase","letterSpacing":".05em"}),
            html.Div("",          style={"flex":"0 0 40px"}),
        ], style={
            "display":"flex","gap":"10px","alignItems":"center",
            "padding":"6px 0 12px","borderBottom":"2px solid #e2e8f0","marginBottom":"6px"
        })
    ] + [build_item_row(gi, ii, item) for ii, item in enumerate(group["items"])]

    return html.Div([
        html.Div([
            html.Div([
                html.Div(style={"width":"14px","height":"14px","borderRadius":"50%","background":dot_color,"marginRight":"10px","display":"inline-block", "boxShadow": "0 0 8px " + dot_color}),
                html.Strong(group["name"], style={"fontSize":"16px","color":"#0f172a", "fontFamily": "'Outfit', sans-serif"}),
                html.Span(f"({len(group['items'])} product types)", style={"fontSize":"13px","color":"#64748b","fontWeight":"500","marginLeft":"8px"}),
            ], style={"display":"flex","alignItems":"center"}),
            html.Button([html.I(className="ti ti-folder-x", style={"marginRight": "6px"}), "Remove group"], id={"type":"del-group","gi":gi},
                className="btn-danger-custom"),
        ], className="group-hdr"),
        html.Div(items_html, style={"overflowX":"auto"}),
        html.Div([
            html.Button([html.I(className="ti ti-plus", style={"marginRight":"4px"}), "Add product"], id={"type":"add-item","gi":gi},
                className="btn-outline-custom",
                style={"fontSize":"13px","padding":"8px 16px","marginTop":"14px"}),
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
    dcc.Interval(id="progress-interval", interval=500, disabled=False, n_intervals=0),

    # Premium Glassmorphic Progress Overlay (always in DOM, hidden by default)
    html.Div([
        html.Div([
            html.Div("Reinforcement Learning Agent is Packing...", className="page-title"),
            html.Div("The neural network is making real-time decisions to optimize container space.", className="page-sub"),
            
            html.Div([
                html.Div(id="progress-bar-fill", style={"width": "0%", "height": "100%", "background": "linear-gradient(90deg, #4f46e5, #3b82f6)", "borderRadius": "4px"})
            ], style={"width": "100%", "height": "16px", "background": "#e2e8f0", "borderRadius": "4px", "overflow": "hidden", "marginBottom": "1.5rem", "marginTop": "2rem"}),
            
            html.Div([
                html.Span(id="progress-text-label", children="Progress: 0 / 0 items (0%)", style={"fontSize": "16px", "fontWeight": "700", "color": "#1e293b", "fontFamily": "'Outfit', sans-serif"}),
                html.Span(id="progress-placed-label", children="Successfully Placed: 0 items", style={"fontSize": "14px", "color": "#64748b", "fontWeight": "500"})
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "2rem"}),
            
            html.Div([
                html.Div(className="spinner-custom"),
                html.Div([
                    html.Div("Selecting optimal coordinates...", style={"fontWeight": "600", "color": "#334155", "fontSize": "15px"}),
                    html.Div("Evaluating cargo stability and load balance", style={"color": "#64748b", "fontSize": "13px"})
                ], style={"textAlign": "left"})
            ], style={"display": "flex", "alignItems": "center", "gap": "1.5rem", "padding": "2rem", "background": "#f8fafc", "borderRadius": "12px", "border": "1px solid #e2e8f0"})
        ], className="card-custom", style={"maxWidth": "600px", "padding": "2.5rem", "background": "white", "boxShadow": "0 20px 25px -5px rgba(0,0,0,0.1)"})
    ], id="progress-overlay-container", style={"display": "none"}),

    # Top nav
    html.Div([
        html.Div([
            html.I(className="ti ti-box-padding", style={"fontSize": "24px", "background": "linear-gradient(135deg, #4f46e5, #3b82f6)", "WebkitBackgroundClip": "text", "WebkitTextFillColor": "transparent"}),
            html.Span("3DBPP Optima", style={"fontWeight": "800", "fontSize": "20px", "letterSpacing": "-0.03em"}),
            html.Span("Hierarchical DRL Engine", className="topnav-sub"),
        ], className="topnav-brand"),
        html.Div([
            html.Span([
                html.Span(style={"width": "8px", "height": "8px", "borderRadius": "50%", "background": "#10b981", "display": "inline-block", "marginRight": "6px"}),
                "System Active"
            ], style={"fontSize": "12px", "fontWeight": "600", "color": "#475569", "background": "#f1f5f9", "padding": "6px 12px", "borderRadius": "999px", "display": "flex", "alignItems": "center"})
        ]),
    ], className="topnav"),

    # Step tabs
    html.Div(id="step-nav"),

    # Page content
    dcc.Loading(
        id="loading-calc",
        type="circle",
        children=html.Div(id="page-content", className="page-wrap"),
        color="#4f46e5"
    ),
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
    def icon(i):
        if i < step:
            return html.Span("✓", className="step-num")
        icons = {1: "ti-list-details", 2: "ti-truck-loading", 3: "ti-presentation-analytics"}
        return html.Span(html.I(className=f"ti {icons[i]}", style={"fontSize": "14px"}), className="step-num")
    
    return html.Div([
        html.Div([icon(1), " 1. Products"],   className=cls(1)),
        html.Span("›", className="step-arrow"),
        html.Div([icon(2), " 2. Container & Algorithm"], className=cls(2)),
        html.Span("›", className="step-arrow"),
        html.Div([icon(3), " 3. Stuffing Result"],  className=cls(3)),
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
    sel_model = state.get("selected_model", "no-buffer")
    cdims = state.get("custom_dims",{})

    sel_cont = state.get("selected_container","20gp")
    use_custom = state.get("custom_container", False)
    sel_algo = state.get("selected_algo","hdrl")
    sel_model = state.get("selected_model", "no-buffer")
    cdims = state.get("custom_dims",{})

    cont_cards = []
    for k, c in CONTAINERS.items():
        is_sel = (sel_cont == k) and not use_custom
        icon_type = "ti-truck" if k == "lkw" else "ti-container"
        cont_cards.append(
            html.Div([
                html.Div([
                    html.I(className=f"ti {icon_type}", style={"fontSize": "24px", "color": "#4f46e5" if is_sel else "#94a3b8"}),
                    html.Div(c["name"], className="cont-name"),
                ], style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "10px"}),
                html.Div(f"{c['dims'][0]} × {c['dims'][1]} × {c['dims'][2]} mm", className="cont-dims"),
                html.Div(f"{c['vol']} m³  •  Max {c['maxw']//1000} Tons", className="cont-vol"),
                html.Button([
                    html.I(className="ti ti-circle-check" if is_sel else "ti ti-circle", style={"marginRight": "4px"}),
                    "Selected" if is_sel else "Select"
                ],
                    id={"type":"sel-cont","key":k},
                    className="btn-primary-custom" if is_sel else "btn-outline-custom",
                    style={"marginTop":"14px","fontSize":"13px","padding":"6px 14px", "width": "100%"}),
            ], className=f"cont-card {'selected' if is_sel else ''}"),
        )

    custom_section = html.Div([
        html.Div([
            html.Div([
                html.Div([html.I(className="ti ti-arrows-horizontal", style={"marginRight":"6px"}), "Length (mm)"], style={"fontSize":"13px","fontWeight":"600","color":"#475569","marginBottom":"6px"}),
                dcc.Input(id="c-length", type="number", value=cdims.get("length",5900), min=500, max=25000),
            ]),
            html.Div([
                html.Div([html.I(className="ti ti-arrows-vertical", style={"marginRight":"6px"}), "Width (mm)"], style={"fontSize":"13px","fontWeight":"600","color":"#475569","marginBottom":"6px"}),
                dcc.Input(id="c-width", type="number", value=cdims.get("width",2350), min=500, max=5000),
            ]),
            html.Div([
                html.Div([html.I(className="ti ti-arrow-up-tail", style={"marginRight":"6px"}), "Height (mm)"], style={"fontSize":"13px","fontWeight":"600","color":"#475569","marginBottom":"6px"}),
                dcc.Input(id="c-height", type="number", value=cdims.get("height",2390), min=500, max=5000),
            ]),
            html.Div([
                html.Div([html.I(className="ti ti-weight", style={"marginRight":"6px"}), "Max weight (kg)"], style={"fontSize":"13px","fontWeight":"600","color":"#475569","marginBottom":"6px"}),
                dcc.Input(id="c-maxw", type="number", value=cdims.get("maxw",28000), min=100),
            ]),
        ], style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)","gap":"16px"}),
        html.Button([
            html.I(className="ti ti-settings", style={"marginRight":"6px"}),
            "Use custom dimensions"
        ], id="btn-use-custom",
            className="btn-primary-custom" if use_custom else "btn-outline-custom",
            style={"marginTop":"16px","fontSize":"13px","padding":"8px 16px"}),
    ], className="panel-card", style={"marginBottom":"1.5rem"})

    algo_cards = []
    algos = {
        "hdrl": ("Semi-Online HDRL", "Hierarchical Deep Reinforcement Learning — best utilization for complex packing", "ti-brain"),
        "blf":  ("Online Greedy BLF", "Bottom-Left-Fill — fast heuristic, good for real-time applications", "ti-layout-grid-add"),
    }
    for k, (nm, desc, icon) in algos.items():
        is_sel = sel_algo == k
        algo_cards.append(html.Div([
            html.Div([
                html.I(className=f"ti {icon}", style={"fontSize": "26px", "color": "#4f46e5" if is_sel else "#94a3b8"}),
                html.Div([
                    html.Div(nm, className="cont-name"),
                    html.Div(desc, className="cont-dims", style={"fontSize": "12px", "marginTop": "2px"}),
                ])
            ], style={"display": "flex", "gap": "12px", "alignItems": "flex-start"}),
            html.Button([
                html.I(className="ti ti-circle-check" if is_sel else "ti ti-circle", style={"marginRight": "4px"}),
                "Selected" if is_sel else "Select"
            ],
                id={"type":"sel-algo","key":k},
                className="btn-primary-custom" if is_sel else "btn-outline-custom",
                style={"marginTop":"14px","fontSize":"12px","padding":"6px 14px", "alignSelf": "flex-start"}),
        ], className=f"algo-card {'selected' if is_sel else ''}",
           style={"flex":"1", "display": "flex", "flexDirection": "column", "justifyContent": "space-between"}))

    model_section = html.Div()
    if sel_algo == "hdrl":
        models = {
            "no-buffer": "No Buffer (Standard)",
            "buffer-1": "Buffer Size 1",
            "buffer-2": "Buffer Size 2",
            "buffer-3": "Buffer Size 3",
        }
        model_cards = []
        for mk, name in models.items():
            is_m_sel = (sel_model == mk)
            model_cards.append(html.Div([
                html.Div(name, className="cont-name", style={"fontSize":"14px"}),
                html.Button([
                    html.I(className="ti ti-circle-check" if is_m_sel else "ti ti-circle", style={"marginRight": "4px"}),
                    "Selected" if is_m_sel else "Select"
                ],
                    id={"type":"sel-model","key":mk},
                    className="btn-primary-custom" if is_m_sel else "btn-outline-custom",
                    style={"marginTop":"10px","fontSize":"12px","padding":"5px 12px", "width": "100%"}),
            ], className=f"algo-card {'selected' if is_m_sel else ''}",
               style={"borderColor":"#4f46e5" if is_m_sel else "","flex":"1","textAlign":"center", "padding": "14px"}))
        
        model_section = html.Div([
            html.Div([html.I(className="ti ti-adjustments-horizontal", style={"marginRight":"6px"}), "Model Configuration"], className="panel-title", style={"marginTop":"1.5rem"}),
            html.Div(model_cards, style={"display":"flex","gap":"12px","marginBottom":"1.5rem"}),
        ])

    return html.Div([
        html.Div("Container & Algorithm", className="page-title"),
        html.Div("Choose a standard shipping container or enter your own dimensions, then select the packing algorithm.", className="page-sub"),

        html.Div([html.I(className="ti ti-container", style={"marginRight":"6px"}), "Standard Containers"], className="panel-title"),
        html.Div(cont_cards, style={"display":"grid","gridTemplateColumns":"repeat(2,1fr)","gap":"12px","marginBottom":"1.5rem"}),

        html.Div([html.I(className="ti ti-manual-gearbox", style={"marginRight":"6px"}), "Custom Dimensions"], className="panel-title"),
        custom_section,

        html.Hr(className="section-div"),

        html.Div([html.I(className="ti ti-cpu", style={"marginRight":"6px"}), "Packing Algorithm"], className="panel-title"),
        html.Div(algo_cards, style={"display":"flex","gap":"16px","marginBottom":"1.5rem"}),

        model_section,

        html.Hr(className="section-div"),

        html.Div([
            html.Button([
                html.I(className="ti ti-arrow-narrow-left", style={"marginRight":"6px"}),
                "Back"
            ], id="btn-back-2", className="btn-outline-custom"),
            html.Button([
                "Calculate Stuffing", 
                html.I(className="ti ti-rocket", style={"marginLeft":"6px"})
            ], id="btn-run", className="btn-primary-custom"),
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
    banner_icon = html.I(className="ti ti-circle-check", style={"fontSize": "20px"}) if packed_count >= all_count else html.I(className="ti ti-alert-triangle", style={"fontSize": "20px"})
    banner_msg  = (f"All {packed_count} items placed — {util:.1f}% utilization achieved."
                   if packed_count >= all_count
                   else f"{packed_count}/{all_count} items placed — {all_count-packed_count} items did not fit. Volume utilization: {util:.1f}%")

    # Placement table rows
    table_rows = []
    for idx, it in enumerate(placed[:anim_step]):
        ci = it.get("color_idx", idx)
        col = BOX_COLORS[ci % len(BOX_COLORS)]
        table_rows.append(html.Tr([
            html.Td(idx+1, style={"fontWeight": "600", "color": "#64748b"}),
            html.Td([
                html.Span(style={"display":"inline-block","width":"12px","height":"12px","borderRadius":"3px","background":col,"marginRight":"8px","verticalAlign":"middle","boxShadow":"0 1px 3px rgba(0,0,0,0.1)"}),
                it.get("name","") or "Item"
            ], style={"textAlign": "left", "fontWeight": "500"}),
            html.Td(it.get("type","Box")),
            html.Td(it.get("length",0), style={"fontFamily": "JetBrains Mono, monospace"}), 
            html.Td(it.get("width",0), style={"fontFamily": "JetBrains Mono, monospace"}), 
            html.Td(it.get("height",0), style={"fontFamily": "JetBrains Mono, monospace"}),
            html.Td(f"{it.get('weight',0)} kg"),
            html.Td(it.get("pos_x",0), style={"fontFamily": "JetBrains Mono, monospace"}), 
            html.Td(it.get("pos_y",0), style={"fontFamily": "JetBrains Mono, monospace"}), 
            html.Td(it.get("pos_z",0), style={"fontFamily": "JetBrains Mono, monospace"}),
        ], style={"background":"#f8fafc" if idx%2==0 else "#fff"}))

    is_playing = state.get("anim_playing", False)

    # Conveyor belt display
    queue_cards = []
    if placed:
        start_q = max(0, anim_step - 1)
        end_q = min(len(placed), anim_step + 5)
        
        for i in range(start_q, end_q):
            item_data = placed[i]
            is_current = (i == anim_step)
            is_packed = (i < anim_step)
            
            ci = item_data.get("color_idx", i)
            col = BOX_COLORS[ci % len(BOX_COLORS)]
            
            card_style = {
                "border": "2px solid #4f46e5" if is_current else ("1px solid #e2e8f0" if not is_packed else "1px solid #e2e8f0"),
                "background": "#f5f3ff" if is_current else ("#fff" if not is_packed else "#f8fafc"),
                "opacity": "1.0" if not is_packed else "0.55",
                "borderRadius": "12px",
                "padding": "12px 14px",
                "minWidth": "140px",
                "flex": "1",
                "textAlign": "center",
                "position": "relative",
                "boxShadow": "0 10px 15px -3px rgba(79,70,229,0.1)" if is_current else "none",
                "transition": "all 0.25s ease"
            }
            
            badge_text = "CURRENT" if is_current else ("✓ PACKED" if is_packed else f"NEXT {i - anim_step}")
            badge_bg = "#4f46e5" if is_current else ("#10b981" if is_packed else "#64748b")
            
            badge = html.Span(badge_text, style={
                "position": "absolute", "top": "-9px", "left": "50%", "transform": "translateX(-50%)",
                "background": badge_bg, "color": "#fff", "fontSize": "9px", "fontWeight": "700",
                "padding": "2px 8px", "borderRadius": "999px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
            })
                
            queue_cards.append(html.Div([
                badge,
                html.Div(item_data.get("name") or "Item", style={"fontSize": "13px", "fontWeight": "700", "marginTop": "6px", "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}),
                html.Div(f"{item_data.get('length')}×{item_data.get('width')}×{item_data.get('height')}", style={"fontSize": "11px", "fontFamily": "JetBrains Mono, monospace", "color": "#64748b", "marginTop": "4px"}),
                html.Div(style={"width": "16px", "height": "16px", "backgroundColor": col, "borderRadius": "4px", "margin": "10px auto 0", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"})
            ], style=card_style))
            
            if i < end_q - 1:
                queue_cards.append(html.Div(html.I(className="ti ti-arrow-narrow-right", style={"color": "#cbd5e1", "fontSize": "20px"}), style={"alignSelf": "center", "display": "flex", "alignItems": "center"}))
    else:
        queue_cards.append(html.Div("No items in queue", style={"fontSize": "14px", "color": "#64748b", "padding": "12px"}))

    conveyor_belt = html.Div([
        html.Div([html.I(className="ti ti-caravan", style={"marginRight":"6px"}), "Arrival Sequence Conveyor Belt"], className="panel-title", style={"marginBottom": "12px"}),
        html.Div(queue_cards, style={"display": "flex", "gap": "10px", "overflowX": "auto", "padding": "16px 8px 8px", "background": "#f8fafc", "borderRadius": "12px", "border": "1px solid #e2e8f0"})
    ], className="panel-card", style={"marginBottom": "1.5rem"})

    # DRL Holding Buffer Display
    current_buffer = []
    if placed and anim_step > 0 and anim_step <= len(placed):
        current_buffer = placed[anim_step - 1].get("buffer", [])
        
    buffer_cards = []
    for idx, bit in enumerate(current_buffer):
        col = BOX_COLORS[bit.get("color_idx", idx) % len(BOX_COLORS)]
        buffer_cards.append(html.Div([
            html.Div(style={"width":"12px","height":"12px","borderRadius":"3px","background":col,"marginRight":"8px"}),
            html.Div([
                html.Div(bit.get("name", "Box"), style={"fontWeight":"600","fontSize":"12px","color":"#1e293b", "whiteSpace":"nowrap"}),
                html.Div(f"{bit.get('length')}×{bit.get('width')}×{bit.get('height')} mm", style={"fontSize":"10px","color":"#64748b", "fontFamily": "JetBrains Mono, monospace"})
            ], style={"textAlign":"left"})
        ], style={
            "display":"flex","alignItems":"center","padding":"8px 12px","minWidth":"150px","background":"#fff",
            "border":"1px solid #e2e8f0","borderRadius":"8px","boxShadow":"0 1px 3px rgba(0,0,0,0.05)"
        }))
        
    if not buffer_cards:
        buffer_display = html.Div("Buffer is currently empty", style={"color":"#94a3b8","fontSize":"13px","fontStyle":"italic","padding":"8px 12px"})
    else:
        buffer_display = html.Div(buffer_cards, style={"display":"flex","gap":"10px","padding":"4px 0", "overflowX": "auto"})

    buffer_panel = html.Div([
        html.Div([
            html.I(className="ti ti-layers-intersect", style={"marginRight":"6px", "color": "#4f46e5"}), 
            "DRL Holding Buffer Status",
            html.Span(" (Max Capacity: 3)", style={"fontSize": "11px", "color": "#64748b", "fontWeight": "normal"})
        ], className="panel-title", style={"marginBottom": "12px"}),
        html.Div(buffer_display, style={"display": "flex", "gap": "10px", "overflowX": "auto", "padding": "12px", "background": "#f8fafc", "borderRadius": "12px", "border": "1px solid #e2e8f0"})
    ], className="panel-card", style={"marginBottom": "1.5rem"})

    return html.Div([
        html.Div("Stuffing Result", className="page-title"),
        html.Div([
            html.Span(f"Algorithm: {state.get('selected_algo','hdrl').upper()}"),
            html.Span(" • ", style={"color": "#cbd5e1", "margin": "0 6px"}),
            html.Span(f"Container: {cont_name}"),
            html.Span(" • ", style={"color": "#cbd5e1", "margin": "0 6px"}),
            html.Span(f"{cL} × {cW} × {cH} mm", style={"fontFamily": "JetBrains Mono, monospace"})
        ], className="page-sub"),

        # Banner
        html.Div([
            banner_icon,
            html.Span(banner_msg),
        ], className=f"result-banner {banner_cls}"),

        # Metrics
        html.Div([
            html.Div([html.Div("Volume Utilization", className="metric-label"), html.Div(f"{util:.1f}%", className="metric-value", style={"color":"#4f46e5"})], className="metric-card", style={"borderTopColor": "#4f46e5"}),
            html.Div([html.Div("Items Packed", className="metric-label"), html.Div(f"{packed_count} / {all_count}", className="metric-value", style={"color":"#10b981"})], className="metric-card", style={"borderTopColor": "#10b981"}),
            html.Div([html.Div("Total Weight", className="metric-label"), html.Div(f"{total_weight:.1f} kg", className="metric-value", style={"color":"#f59e0b"})], className="metric-card", style={"borderTopColor": "#f59e0b"}),
            html.Div([html.Div("Used Volume", className="metric-label"), html.Div(f"{used_vol/1e9:.2f} m³", className="metric-value", style={"color":"#8b5cf6"})], className="metric-card", style={"borderTopColor": "#8b5cf6"}),
        ], style={"display":"flex","gap":"16px","marginBottom":"1.5rem"}),

        # Conveyor Belt
        conveyor_belt,

        # DRL Buffer Status
        buffer_panel,

        # 3D visualization + controls
        html.Div([
            html.Div([html.I(className="ti ti-cube-send", style={"marginRight":"6px"}), "3D Packing Visualization"], className="panel-title"),
            dcc.Graph(id="main-3d", figure=fig_main, config={"displayModeBar":False}),
            html.Div([html.Div(style={"width":f"{pct:.1f}%"}, className="prog-bar")], className="prog-wrap"),
            html.Div([
                dcc.Slider(id="anim-slider", min=0, max=len(placed), value=anim_step, step=1,
                    marks=None, tooltip={"placement":"bottom","always_visible":False}),
            ], style={"margin":"8px 0 14px"}),
            html.Div([
                html.Button(html.I(className="ti ti-player-skip-back"), id="btn-first", className="btn-outline-custom", style={"padding":"10px 14px"}),
                html.Button(html.I(className="ti ti-player-track-prev"), id="btn-prev", className="btn-outline-custom", style={"padding":"10px 14px"}),
                html.Button([
                    html.I(className="ti ti-player-pause" if is_playing else "ti ti-player-play"),
                    " Pause" if is_playing else " Play"
                ],
                    id="btn-play", className="btn-primary-custom", style={"padding":"10px 20px"}),
                html.Button(html.I(className="ti ti-player-track-next"), id="btn-next", className="btn-outline-custom", style={"padding":"10px 14px"}),
                html.Button(html.I(className="ti ti-player-skip-forward"), id="btn-last", className="btn-outline-custom", style={"padding":"10px 14px"}),
                
                html.Div(style={"flexGrow": "1"}),
                
                html.Div([
                    html.I(className="ti ti-device-heartbeat", style={"color": "#64748b", "marginRight": "6px"}),
                    dcc.Dropdown(id="anim-speed", options=[
                        {"label":"Slow","value":400},{"label":"Normal","value":180},{"label":"Fast","value":60}
                    ], value=180, clearable=False,
                    style={"width":"100px","fontSize":"13px"}),
                ], style={"display": "flex", "alignItems": "center"})
            ], style={"display":"flex","gap":"8px","alignItems":"center","flexWrap":"wrap"}),
        ], className="panel-card"),

        # Placement table
        html.Div([
            html.Div([html.I(className="ti ti-list-numbered", style={"marginRight":"6px"}), "Placement Detail Table"], className="panel-title"),
            html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th("#"), html.Th("Name"), html.Th("Type"),
                        html.Th("L (mm)"), html.Th("W (mm)"), html.Th("H (mm)"), html.Th("Weight"),
                        html.Th("Pos X"), html.Th("Pos Y"), html.Th("Pos Z"),
                    ])),
                    html.Tbody(table_rows),
                ], className="placement-table"),
            ], style={"maxHeight":"260px","overflowY":"auto","overflowX":"auto"}),
        ], className="panel-card"),

        html.Hr(className="section-div"),

        # Footer nav
        html.Div([
            html.Div([
                html.Button([html.I(className="ti ti-arrow-narrow-left"), "Back"], id="btn-back-3", className="btn-outline-custom", style={"marginRight":"10px"}),
                html.Button([html.I(className="ti ti-refresh"), "Replay"], id="btn-replay", className="btn-outline-custom"),
            ]),
            html.Div([
                dcc.Download(id="download-csv"),
                html.Button([html.I(className="ti ti-download"), "Export CSV"], id="btn-export", className="btn-outline-custom", style={"marginRight":"10px"}),
                html.Button([html.I(className="ti ti-plus"), "New Calculation"], id="btn-new", className="btn-primary-custom"),
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
    Input({"type":"sel-model","key":ALL},"n_clicks", allow_optional=True),
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
    Input("progress-interval","n_intervals", allow_optional=True),
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
    speed_val = args[-1]  # state is the last, speed_val is before it
    # Find speed_val index (second to last)
    speed_val = args[-2]
    if speed_val:
        try:
            speed = int(speed_val)
        except:
            pass

    # ── Progress interval tick (Real-time Progress Bar) ──
    if trigger == "progress-interval":
        if state.get("packing_in_progress", False):
            if not PACKING_PROGRESS["active"]:
                # Background packing finished!
                state["packing_in_progress"] = False
                if PACKING_PROGRESS["error"]:
                    state["placed_items"] = []
                else:
                    state["placed_items"] = PACKING_PROGRESS["result"] or []
                state["anim_step"] = len(state["placed_items"])
                state["anim_playing"] = False
                state["step"] = 3
                return json.dumps(state), True, speed
            else:
                # Update progress info from global dict to state
                state["packing_current"] = PACKING_PROGRESS["current"]
                state["packing_total"] = PACKING_PROGRESS["total"]
                state["packing_placed"] = PACKING_PROGRESS["placed_count"]
                return json.dumps(state), True, speed
        else:
            return no_update, no_update, no_update

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
        
        if t == "sel-model" and key:
            state["selected_model"] = key
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
            if state.get("selected_algo") == "hdrl":
                # Start background thread for DRL packing
                PACKING_PROGRESS["active"] = True
                PACKING_PROGRESS["current"] = 0
                PACKING_PROGRESS["total"] = len(all_items)
                PACKING_PROGRESS["placed_count"] = 0
                PACKING_PROGRESS["result"] = None
                PACKING_PROGRESS["error"] = None
                
                t = threading.Thread(target=bg_packing_worker, args=(all_items, cL, cW, cH, state.get("selected_model", "no-buffer")))
                t.daemon = True
                t.start()
                
                state["packing_in_progress"] = True
                state["packing_current"] = 0
                state["packing_total"] = len(all_items)
                state["packing_placed"] = 0
                # Stay on step 2 but show the progress UI
                state["step"] = 2
            else:
                # BLF is extremely fast, run it synchronously
                placed = pack_blf(all_items, cL, cW, cH)
                state["placed_items"] = placed
                state["anim_step"] = len(placed)
                state["anim_playing"] = False
                state["step"] = 3
        else:
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


# ── Progress Polling Callback ──────────────────────────────────────────────────

@app.callback(
    Output("progress-bar-fill", "style"),
    Output("progress-text-label", "children"),
    Output("progress-placed-label", "children"),
    Output("progress-overlay-container", "style"),
    Output("app-state", "data", allow_duplicate=True),
    Input("progress-interval", "n_intervals"),
    State("app-state", "data"),
    prevent_initial_call=True
)
def update_progress_ui(n, state_json):
    state = json.loads(state_json)
    if not state.get("packing_in_progress", False):
        return no_update, no_update, no_update, no_update, no_update
        
    if not PACKING_PROGRESS["active"]:
        # Finished!
        state["packing_in_progress"] = False
        if PACKING_PROGRESS["error"]:
            state["placed_items"] = []
        else:
            state["placed_items"] = PACKING_PROGRESS["result"] or []
        state["anim_step"] = len(state["placed_items"])
        state["anim_playing"] = False
        state["step"] = 3
        
        # Hide overlay and update state to trigger Step 3
        return {"width": "100%"}, "Finished!", f"Total Placed: {len(state['placed_items'])}", {"display": "none"}, json.dumps(state)
        
    # Still packing, update UI only (do NOT update app-state to prevent re-render!)
    current = PACKING_PROGRESS["current"]
    total = PACKING_PROGRESS["total"]
    placed = PACKING_PROGRESS["placed_count"]
    pct = int((current / max(1, total)) * 100)
    
    bar_style = {"width": f"{pct}%", "height": "100%", "background": "linear-gradient(90deg, #4f46e5, #3b82f6)", "borderRadius": "4px", "transition": "width 0.2s ease"}
    text_label = f"Progress: {current} / {total} items ({pct}%)"
    placed_label = f"Successfully Placed: {placed} items"
    overlay_style = {
        "display": "flex", "position": "fixed", "top": 0, "left": 0, "width": "100%", "height": "100%",
        "background": "rgba(255, 255, 255, 0.82)", "backdropFilter": "blur(8px)", "WebkitBackdropFilter": "blur(8px)",
        "zIndex": 1000, "justifyContent": "center", "alignItems": "center"
    }
    
    return bar_style, text_label, placed_label, overlay_style, no_update


# ==============================================================================
# RUN
# ==============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=8050)