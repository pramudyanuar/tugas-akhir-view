# ==============================================================================
# 3DBPP SEMI-ONLINE WITH HIERARCHICAL DRL — FULL STREAMLIT APP
# ==============================================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import random
import time

# ==============================================================================
# PAGE CONFIG — FULL WIDTH, NO PADDING
# ==============================================================================

st.set_page_config(
    page_title="3DBPP Semi-Online | HDRL",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# GLOBAL CSS — DARK THEME, COMPACT, POLISHED
# ==============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

/* ── RESET & BASE ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0d0f1a !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── REMOVE TOP PADDING ── */
.main .block-container {
    padding: 0.5rem 0.8rem 0.5rem 0.8rem !important;
    max-width: 100% !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #111827 !important;
    border-right: 1px solid #1e293b !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0.8rem !important; }

/* ── SIDEBAR LABELS ── */
[data-testid="stSidebar"] label {
    color: #94a3b8 !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}

/* ── SIDEBAR SECTION HEADERS ── */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #f1f5f9 !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    margin: 0 !important;
}

/* ── NUMBER INPUT ── */
[data-testid="stNumberInput"] input {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    padding: 4px 8px !important;
}
[data-testid="stNumberInput"] button {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #94a3b8 !important;
}

/* ── TEXT INPUT ── */
[data-testid="stTextInput"] input {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
    border-radius: 6px !important;
    font-size: 13px !important;
}

/* ── SELECTBOX ── */
[data-testid="stSelectbox"] > div > div {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
    border-radius: 6px !important;
    font-size: 13px !important;
}

/* ── CHECKBOX ── */
[data-testid="stCheckbox"] label { color: #94a3b8 !important; font-size: 12px !important; }

/* ── BUTTONS — ADD ITEM ── */
[data-testid="stButton"] button {
    background: #7c3aed !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
    width: 100% !important;
    transition: background 0.2s !important;
}
[data-testid="stButton"] button:hover { background: #6d28d9 !important; }

/* ── RUN BUTTON OVERRIDE ── */
.run-btn button {
    background: linear-gradient(135deg, #16a34a, #15803d) !important;
    font-size: 15px !important;
    padding: 10px !important;
    letter-spacing: 0.04em !important;
}
.run-btn button:hover { background: #15803d !important; }

/* ── DIVIDER ── */
hr { border-color: #1e293b !important; margin: 0.5rem 0 !important; }

/* ── PLOTLY CHART BACKGROUND ── */
.js-plotly-plot .plotly .bg { fill: transparent !important; }

/* ── METRIC CARDS ── */
.metric-card {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 14px 20px;
    text-align: center;
}
.metric-label {
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 500;
    margin-bottom: 4px;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px;
    font-weight: 700;
}

/* ── PANEL CARD ── */
.panel-card {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 12px 14px;
}
.panel-title {
    font-size: 11px;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    margin-bottom: 8px;
}

/* ── TABLE ── */
.styled-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
}
.styled-table th {
    color: #64748b;
    font-weight: 600;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 6px 8px;
    border-bottom: 1px solid #1e293b;
    text-align: center;
}
.styled-table td {
    padding: 5px 8px;
    border-bottom: 1px solid #1a2234;
    text-align: center;
    color: #cbd5e1;
}
.styled-table tr:last-child td { border-bottom: none; }
.styled-table tr:hover td { background: #1e293b44; }

/* ── PROGRESS / SLIDER ── */
[data-testid="stSlider"] > div { padding: 0 !important; }

/* ── ANIMATION STEP LABEL ── */
.step-label {
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 6px;
    font-family: 'JetBrains Mono', monospace;
}

/* ── COLUMN GAP ── */
[data-testid="column"] { padding: 0 4px !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0d0f1a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }

/* ── TOAST ── */
[data-testid="stToast"] { background: #1e293b !important; border: 1px solid #334155 !important; }

/* ── SELECT SLIDER ── */
[data-testid="stSelectSlider"] div { font-size: 12px !important; }

/* ── DOWNLOAD BUTTON ── */
[data-testid="stDownloadButton"] button {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #94a3b8 !important;
    font-size: 12px !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: #334155 !important;
    color: #f1f5f9 !important;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SESSION STATE INIT
# ==============================================================================

if "items_data" not in st.session_state:
    st.session_state["items_data"] = []

if "placed_items" not in st.session_state:
    st.session_state["placed_items"] = []

if "anim_step" not in st.session_state:
    st.session_state["anim_step"] = 0

if "anim_playing" not in st.session_state:
    st.session_state["anim_playing"] = False

# ==============================================================================
# COLOR PALETTE FOR BOXES
# ==============================================================================

BOX_COLORS = [
    "#4ade80", "#f472b6", "#a78bfa", "#60a5fa", "#34d399",
    "#fb923c", "#facc15", "#38bdf8", "#f87171", "#c084fc",
    "#86efac", "#fda4af", "#93c5fd", "#6ee7b7", "#fbbf24",
]

# ==============================================================================
# HELPER — 3D FIGURE
# ==============================================================================

def make_box_traces(item, color, opacity=0.82):
    x0, y0, z0 = item["pos_x"], item["pos_y"], item["pos_z"]
    dx, dy, dz = item["w"], item["l"], item["h"]

    x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz

    # 6 faces as filled mesh
    vertices_x = [x0,x1,x1,x0, x0,x1,x1,x0]
    vertices_y = [y0,y0,y1,y1, y0,y0,y1,y1]
    vertices_z = [z0,z0,z0,z0, z1,z1,z1,z1]

    faces_i = [0,0,0,4,4,4,0,0,1,5,2,6]
    faces_j = [1,2,4,5,6,7,1,2,2,6,3,7]
    faces_k = [2,3,5,6,7,3,5,4,6,2,7,3]

    mesh = go.Mesh3d(
        x=vertices_x, y=vertices_y, z=vertices_z,
        i=faces_i, j=faces_j, k=faces_k,
        color=color,
        opacity=opacity,
        flatshading=True,
        showlegend=False,
        hovertemplate=(
            f"<b>{item['name']}</b><br>"
            f"Size: {item['w']}×{item['l']}×{item['h']}<br>"
            f"Pos: ({x0},{y0},{z0})<br>"
            f"Weight: {item['weight']} kg<extra></extra>"
        ),
    )

    # Wireframe edges
    edge_x, edge_y, edge_z = [], [], []
    edges = [
        (0,1),(1,2),(2,3),(3,0),
        (4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7),
    ]
    vx = [x0,x1,x1,x0,x0,x1,x1,x0]
    vy = [y0,y0,y1,y1,y0,y0,y1,y1]
    vz = [z0,z0,z0,z0,z1,z1,z1,z1]
    for a, b in edges:
        edge_x += [vx[a], vx[b], None]
        edge_y += [vy[a], vy[b], None]
        edge_z += [vz[a], vz[b], None]

    wire = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode="lines",
        line=dict(color="#ffffff", width=1.2),
        showlegend=False,
        hoverinfo="skip",
    )
    return mesh, wire


def create_3d_figure(placed, container, step=None, mini=False):
    cw, cl, ch = container

    fig = go.Figure()

    # Container wireframe
    cx = [0,cw,cw, 0, 0,cw,cw, 0]
    cy = [0, 0,cl,cl, 0, 0,cl,cl]
    cz = [0, 0, 0, 0,ch,ch,ch,ch]
    cedges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    ex, ey, ez = [], [], []
    for a, b in cedges:
        ex += [cx[a],cx[b],None]; ey += [cy[a],cy[b],None]; ez += [cz[a],cz[b],None]

    fig.add_trace(go.Scatter3d(
        x=ex, y=ey, z=ez,
        mode="lines",
        line=dict(color="#334155", width=1.5),
        showlegend=False, hoverinfo="skip",
    ))

    items_to_show = placed[:step] if step is not None else placed

    for idx, item in enumerate(items_to_show):
        color = BOX_COLORS[item.get("color_idx", idx) % len(BOX_COLORS)]

        # Dashed ghost for last item in mini view
        is_last = (step is not None and idx == len(items_to_show) - 1 and mini)
        opacity = 0.35 if is_last else 0.82

        mesh, wire = make_box_traces(item, color, opacity=opacity)
        fig.add_trace(mesh)
        fig.add_trace(wire)

    camera = dict(eye=dict(x=1.5, y=-1.5, z=1.2)) if not mini else dict(eye=dict(x=1.6, y=-1.6, z=1.3))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            bgcolor="rgba(13,15,26,0)",
            xaxis=dict(
                title=dict(text="X (Width)", font=dict(size=10, color="#94a3b8")),
                range=[0, cw],
                showbackground=True,
                backgroundcolor="rgba(30,41,59,0.3)",
                gridcolor="#1e293b", tickcolor="#475569", tickfont=dict(size=9, color="#64748b"),
                nticks=6,
            ),
            yaxis=dict(
                title=dict(text="Y (Length)", font=dict(size=10, color="#94a3b8")),
                range=[0, cl],
                showbackground=True,
                backgroundcolor="rgba(30,41,59,0.2)",
                gridcolor="#1e293b", tickcolor="#475569", tickfont=dict(size=9, color="#64748b"),
                nticks=6,
            ),
            zaxis=dict(
                title=dict(text="Z (Height)", font=dict(size=10, color="#94a3b8")),
                range=[0, ch],
                showbackground=True,
                backgroundcolor="rgba(30,41,59,0.15)",
                gridcolor="#1e293b", tickcolor="#475569", tickfont=dict(size=9, color="#64748b"),
                nticks=6,
            ),
            aspectmode="cube",
            camera=camera,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=220 if mini else 380,
    )

    return fig

# ==============================================================================
# PACKING ALGORITHM (Heuristic — Bottom-Left-Fill)
# ==============================================================================

def run_packing(items, container):
    cw, cl, ch = container
    placed = []
    cur_x, cur_y, cur_z = 0, 0, 0
    row_h = 0
    layer_h = 0

    for idx, item in enumerate(items):
        w, l, h = item["w"], item["l"], item["h"]

        # Simple row-based placement
        if cur_x + w > cw:
            cur_x = 0
            cur_y += row_h
            row_h = 0

        if cur_y + l > cl:
            cur_y = 0
            cur_x = 0
            cur_z += layer_h
            layer_h = 0
            row_h = 0

        if cur_z + h > ch:
            # Cannot place
            continue

        placed.append({
            **item,
            "pos_x": cur_x,
            "pos_y": cur_y,
            "pos_z": cur_z,
            "color_idx": idx,
        })

        cur_x += w
        row_h = max(row_h, l)
        layer_h = max(layer_h, h)

    return placed

# ==============================================================================
# SIDEBAR
# ==============================================================================

with st.sidebar:

    # ── TITLE ──
    st.markdown("""
    <div style="padding:4px 0 8px;">
        <div style="font-size:10px;color:#64748b;letter-spacing:0.1em;text-transform:uppercase;font-weight:600;">⚙️ CONFIGURATION</div>
    </div>
    """, unsafe_allow_html=True)

    # ── CONTAINER SIZE ──
    st.markdown("<div style='font-size:11px;color:#94a3b8;font-weight:500;margin-bottom:4px;'>Container Size (cm)</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div style='font-size:10px;color:#64748b;text-align:center;'>Width (X)</div>", unsafe_allow_html=True)
        cont_w = st.number_input("W", min_value=50, max_value=2000, value=300, step=10, label_visibility="collapsed", key="cont_w")
    with c2:
        st.markdown("<div style='font-size:10px;color:#64748b;text-align:center;'>Length (Y)</div>", unsafe_allow_html=True)
        cont_l = st.number_input("L", min_value=50, max_value=2000, value=300, step=10, label_visibility="collapsed", key="cont_l")
    with c3:
        st.markdown("<div style='font-size:10px;color:#64748b;text-align:center;'>Height (Z)</div>", unsafe_allow_html=True)
        cont_h = st.number_input("H", min_value=50, max_value=2000, value=300, step=10, label_visibility="collapsed", key="cont_h")

    container_size = (cont_w, cont_l, cont_h)
    container_volume = cont_w * cont_l * cont_h

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── ADD ITEM ──
    st.markdown("<div style='font-size:10px;color:#64748b;letter-spacing:0.1em;text-transform:uppercase;font-weight:600;margin-bottom:6px;'>➕ ADD ITEM</div>", unsafe_allow_html=True)

    item_name = st.text_input("Item Name", value="Box", label_visibility="visible")

    col_w, col_l, col_h = st.columns(3)
    with col_w:
        item_w = st.number_input("Width (X)", min_value=1, max_value=500, value=30, key="iw")
    with col_l:
        item_l = st.number_input("Length (Y)", min_value=1, max_value=500, value=30, key="il")
    with col_h:
        item_h = st.number_input("Height (Z)", min_value=1, max_value=500, value=30, key="ih")

    col_wt, col_qty = st.columns(2)
    with col_wt:
        item_weight = st.number_input("Weight (kg)", min_value=0.0, max_value=9999.0, value=10.0, key="iwt")
    with col_qty:
        item_qty = st.number_input("Quantity", min_value=1, max_value=100, value=1, key="iqty")

    col_stack, col_fragile = st.columns(2)
    with col_stack:
        stackable = st.checkbox("Stackable", value=True)
    with col_fragile:
        fragile = st.checkbox("Fragile", value=False)

    max_stack_w = st.number_input("Max Stack Weight (kg)", min_value=0.0, value=100.0, key="msw")

    if st.button("Add Item"):
        for _ in range(int(item_qty)):
            st.session_state["items_data"].append({
                "name": item_name,
                "w": item_w,
                "l": item_l,
                "h": item_h,
                "weight": item_weight,
                "stackable": stackable,
                "fragile": fragile,
                "max_stack_weight": max_stack_w,
                "volume": item_w * item_l * item_h,
            })
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── SAMPLE ITEMS ──
    st.markdown("<div style='font-size:10px;color:#64748b;letter-spacing:0.1em;text-transform:uppercase;font-weight:600;margin-bottom:6px;'>⚡ SAMPLE ITEMS</div>", unsafe_allow_html=True)

    if st.button("Generate Sample"):
        sizes = [(30,30,30,10),(50,40,30,15),(60,50,40,20),(80,70,50,30),(40,40,40,12),(50,30,30,8),(70,30,20,6),(60,40,20,7),(40,20,20,4),(30,20,20,3)]
        st.session_state["items_data"] = []
        for w2, l2, h2, wt in sizes:
            st.session_state["items_data"].append({
                "name": "Box",
                "w": w2, "l": l2, "h": h2,
                "weight": wt,
                "stackable": True,
                "fragile": False,
                "max_stack_weight": wt * 10,
                "volume": w2 * l2 * h2,
            })
        st.session_state["placed_items"] = []
        st.session_state["anim_step"] = 0
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── MODEL SELECT ──
    st.markdown("<div style='font-size:10px;color:#64748b;letter-spacing:0.1em;text-transform:uppercase;font-weight:600;margin-bottom:6px;'>🧠 MODEL</div>", unsafe_allow_html=True)

    model_choice = st.selectbox(
        "Select Model",
        ["Semi-Online HDRL (Heuristic)", "Online Greedy BLF", "Offline Optimal (ILP)"],
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── RUN BUTTON ──
    st.markdown('<div class="run-btn">', unsafe_allow_html=True)
    run_clicked = st.button("🚀 RUN PACKING")
    st.markdown('</div>', unsafe_allow_html=True)

    if run_clicked and len(st.session_state["items_data"]) > 0:
        placed = run_packing(st.session_state["items_data"], container_size)
        st.session_state["placed_items"] = placed
        st.session_state["anim_step"] = len(placed)
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── VISUAL SETTINGS ──
    st.markdown("<div style='font-size:10px;color:#64748b;letter-spacing:0.1em;text-transform:uppercase;font-weight:600;margin-bottom:6px;'>🎛️ VISUAL SETTINGS</div>", unsafe_allow_html=True)

    animation_speed = st.select_slider(
        "Animation Speed",
        options=["Slow", "Normal", "Fast"],
        value="Normal",
    )
    speed_map = {"Slow": 0.35, "Normal": 0.15, "Fast": 0.05}
    animation_delay = speed_map[animation_speed]

    show_grid = st.checkbox("Show Grid", value=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── REPLAY ──
    if len(st.session_state["placed_items"]) > 0:
        if st.button("🔄 Replay Animation"):
            st.session_state["anim_step"] = 0
            st.session_state["anim_playing"] = True

        # ── EXPORT ──
        export_df = pd.DataFrame(st.session_state["placed_items"])
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Export Packing Result",
            data=csv,
            file_name="packing_result.csv",
            mime="text/csv",
        )

    # ── CLEAR ──
    if st.button("🗑️ Clear All"):
        st.session_state["items_data"] = []
        st.session_state["placed_items"] = []
        st.session_state["anim_step"] = 0
        st.rerun()

# ==============================================================================
# MAIN CONTENT
# ==============================================================================

placed_items = st.session_state["placed_items"]
items_data = st.session_state["items_data"]
anim_step = st.session_state.get("anim_step", 0)

# ── HEADER ──
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;padding:4px 0;">
    <span style="font-size:28px;">📦</span>
    <div>
        <h1 style="font-family:'Inter',sans-serif;font-size:22px;font-weight:800;color:#f1f5f9;margin:0;letter-spacing:-0.02em;">
            3DBPP Semi-Online with Hierarchical DRL
        </h1>
        <p style="font-size:11px;color:#64748b;margin:0;letter-spacing:0.04em;">
            3D Bin Packing Problem &bull; Semi-Online Strategy &bull; Hierarchical Deep Reinforcement Learning
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── TOP ROW: 3D VIZ (left) + PACKING ANIMATION (right) ──
col_main, col_anim = st.columns([3, 2], gap="small")

with col_main:
    st.markdown("""
    <div class="panel-card">
        <div class="panel-title">📊 3D PACKING VISUALIZATION</div>
    """, unsafe_allow_html=True)

    if len(placed_items) > 0:
        fig_main = create_3d_figure(placed_items, container_size, step=anim_step)
    else:
        fig_main = create_3d_figure([], container_size)

    st.plotly_chart(fig_main, use_container_width=True, key="main_viz")

    st.markdown("</div>", unsafe_allow_html=True)

with col_anim:
    st.markdown("""
    <div class="panel-card" style="height:100%;">
        <div class="panel-title">🎬 PACKING ANIMATION</div>
    """, unsafe_allow_html=True)

    total_steps = len(placed_items)

    if total_steps > 0:
        step_label = f"Step {anim_step} / {total_steps}"
        if anim_step > 0:
            cur_item = placed_items[anim_step - 1]["name"]
            step_label += f" — Placing Item: {cur_item}"
        st.markdown(f'<div class="step-label">{step_label}</div>', unsafe_allow_html=True)

        anim_placeholder = st.empty()
        fig_mini = create_3d_figure(placed_items, container_size, step=anim_step, mini=True)
        anim_placeholder.plotly_chart(fig_mini, use_container_width=True, key=f"mini_viz_{anim_step}")

        # Progress bar
        progress_pct = anim_step / total_steps if total_steps > 0 else 0
        st.markdown(f"""
        <div style="background:#1e293b;border-radius:4px;height:5px;margin:6px 0;">
            <div style="background:linear-gradient(90deg,#7c3aed,#a855f7);height:5px;border-radius:4px;width:{progress_pct*100:.1f}%;transition:width 0.3s;"></div>
        </div>
        """, unsafe_allow_html=True)

        # Controls
        btn_c = st.columns(5)
        with btn_c[0]:
            if st.button("⏮ First", use_container_width=True, key="btn_first"):
                st.session_state["anim_step"] = 1
                st.rerun()
        with btn_c[1]:
            if st.button("◀ Prev", use_container_width=True, key="btn_prev"):
                st.session_state["anim_step"] = max(1, anim_step - 1)
                st.rerun()
        with btn_c[2]:
            playing = st.session_state.get("anim_playing", False)
            lbl = "⏸ Pause" if playing else "▶ Play"
            if st.button(lbl, use_container_width=True, key="btn_play"):
                st.session_state["anim_playing"] = not playing
                if not playing:
                    st.session_state["anim_step"] = max(1, anim_step)
                st.rerun()
        with btn_c[3]:
            if st.button("Next ▶", use_container_width=True, key="btn_next"):
                st.session_state["anim_step"] = min(total_steps, anim_step + 1)
                st.rerun()
        with btn_c[4]:
            if st.button("Last ⏭", use_container_width=True, key="btn_last"):
                st.session_state["anim_step"] = total_steps
                st.rerun()

        # Speed selector for animation panel
        speed_label = st.selectbox("Speed", ["Slow", "Normal", "Fast"], index=1, key="anim_speed_select", label_visibility="collapsed")

    else:
        st.markdown("""
        <div style="text-align:center;padding:40px 0;color:#475569;">
            <div style="font-size:32px;margin-bottom:8px;">📦</div>
            <div style="font-size:13px;">Run packing to see animation</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# AUTO-PLAY ANIMATION
# ==============================================================================

if st.session_state.get("anim_playing", False) and total_steps > 0:
    if anim_step < total_steps:
        time.sleep(animation_delay)
        st.session_state["anim_step"] = anim_step + 1
        st.rerun()
    else:
        st.session_state["anim_playing"] = False

# ── MIDDLE ROW: ITEM LIST ──
st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

import streamlit.components.v1 as components

with st.container():

    if len(items_data) > 0:
        rows_html = ""
        total_vol = 0
        for idx, item in enumerate(items_data):
            color = BOX_COLORS[idx % len(BOX_COLORS)]
            s_style = "color:#4ade80;font-weight:600;" if item["stackable"] else "color:#f87171;font-weight:600;"
            f_style = "color:#f87171;font-weight:600;" if item["fragile"] else "color:#64748b;"
            s_text  = "Yes" if item["stackable"] else "No"
            f_text  = "Yes" if item["fragile"]   else "No"
            vol = item["volume"]
            total_vol += vol
            row_bg = "#1a2337" if idx % 2 == 0 else "transparent"
            rows_html += f"""<tr style="background:{row_bg};">
                <td style="padding:5px 10px;border-bottom:1px solid #1a2234;text-align:center;">
                    <span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:{color};margin-right:5px;vertical-align:middle;"></span>{idx+1}
                </td>
                <td style="padding:5px 10px;border-bottom:1px solid #1a2234;text-align:center;">{item['name']}</td>
                <td style="padding:5px 10px;border-bottom:1px solid #1a2234;text-align:center;">{item['w']}</td>
                <td style="padding:5px 10px;border-bottom:1px solid #1a2234;text-align:center;">{item['l']}</td>
                <td style="padding:5px 10px;border-bottom:1px solid #1a2234;text-align:center;">{item['h']}</td>
                <td style="padding:5px 10px;border-bottom:1px solid #1a2234;text-align:center;">{item['weight']}</td>
                <td style="padding:5px 10px;border-bottom:1px solid #1a2234;text-align:center;{s_style}">{s_text}</td>
                <td style="padding:5px 10px;border-bottom:1px solid #1a2234;text-align:center;{f_style}">{f_text}</td>
                <td style="padding:5px 10px;border-bottom:1px solid #1a2234;text-align:center;">{item['max_stack_weight']}</td>
                <td style="padding:5px 10px;border-bottom:1px solid #1a2234;text-align:center;">{vol:,}</td>
            </tr>"""

        rows_html += f"""<tr>
            <td colspan="9" style="padding:7px 10px;text-align:right;color:#94a3b8;font-weight:600;font-size:11px;border-top:1px solid #334155;">Total</td>
            <td style="padding:7px 10px;text-align:center;color:#f1f5f9;font-weight:700;border-top:1px solid #334155;">{total_vol:,}</td>
        </tr>"""

        table_html = f"""<!DOCTYPE html><html><head><style>
            *{{box-sizing:border-box;margin:0;padding:0;}}
            body{{background:#111827;font-family:'Segoe UI',sans-serif;color:#cbd5e1;
                 padding:12px 14px;border:1px solid #1e293b;border-radius:10px;}}
            .ptitle{{font-size:11px;color:#94a3b8;text-transform:uppercase;
                     letter-spacing:.08em;font-weight:700;margin-bottom:10px;}}
            .wrap{{overflow-x:auto;overflow-y:auto;max-height:260px;}}
            table{{width:100%;border-collapse:collapse;font-size:12px;}}
            thead th{{position:sticky;top:0;background:#0f172a;color:#64748b;
                      font-weight:600;font-size:10px;text-transform:uppercase;
                      letter-spacing:.06em;padding:7px 10px;
                      border-bottom:1px solid #1e293b;text-align:center;white-space:nowrap;}}
            ::-webkit-scrollbar{{width:4px;height:4px;}}
            ::-webkit-scrollbar-track{{background:#0d0f1a;}}
            ::-webkit-scrollbar-thumb{{background:#334155;border-radius:4px;}}
        </style></head><body>
        <div class="ptitle">📋 ITEM LIST</div>
        <div class="wrap"><table>
            <thead><tr>
                <th>ID</th><th>Name</th>
                <th>X</th><th>Y</th><th>Z</th>
                <th>Weight (kg)</th><th>Stackable</th><th>Fragile</th>
                <th>Max Stack (kg)</th><th>Volume (cm³)</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table></div>
        </body></html>"""

        tbl_height = min(340, 90 + len(items_data) * 30)
        components.html(table_html, height=tbl_height, scrolling=False)

    else:
        st.markdown("""
        <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;padding:12px 14px;">
            <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;font-weight:700;margin-bottom:8px;">📋 ITEM LIST</div>
            <div style="text-align:center;padding:20px;color:#475569;font-size:13px;">
                No items added yet. Use the sidebar to add items or generate a sample.
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── BOTTOM STATS BAR ──
st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

items_packed = len(placed_items)
total_items = len(items_data)
used_volume = sum(p["volume"] for p in placed_items)
utilization = (used_volume / container_volume * 100) if container_volume > 0 and used_volume > 0 else 0.0
total_weight = sum(p["weight"] for p in placed_items)

metrics = [
    ("Items Packed", f"{items_packed} / {total_items}", "#4ade80"),
    ("Utilization", f"{utilization:.2f} %", "#a78bfa"),
    ("Total Weight", f"{total_weight} kg", "#fb923c"),
    ("Container Volume", f"{container_volume:,} cm³", "#60a5fa"),
    ("Used Volume", f"{used_volume:,} cm³", "#34d399"),
]

cols_stat = st.columns(5, gap="small")
for col, (label, value, color) in zip(cols_stat, metrics):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};">{value}</div>
        </div>
        """, unsafe_allow_html=True)

# ── SUCCESS TOAST ──
if len(placed_items) > 0 and run_clicked:
    st.toast("Packing Optimization Completed 🚀")

# ── FOOTER ──
st.markdown("""
<div style="text-align:center;color:#334155;font-size:11px;margin-top:12px;letter-spacing:0.06em;">
    3DBPP Framework &bull; Semi-Online Packing &bull; HDRL &bull; Reinforcement Learning
</div>
""", unsafe_allow_html=True)