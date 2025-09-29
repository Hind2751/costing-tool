import streamlit as st
import pandas as pd
import altair as alt
from utils.state import ensure_state
from utils.costing_core import compute_totals, ACCURACY_BANDS, compute_ramp_monthly

st.set_page_config(page_title="Summary — Totals & Graphs", layout="wide")
data = ensure_state(st)

stage = data["project"]["stage"]
cur = data["project"]["currency"]
st.header(f"Summary — {data['project']['name']}")
band = ACCURACY_BANDS.get(stage, None)
acc_label = f"Expected accuracy range: {band[0]}% / +{band[1]}%" if band else "Accuracy range: n/a"
st.caption(f"Stage: {stage} • {acc_label} • Currency: {cur}")

totals = compute_totals(data)

def get_scale(total):
    if total >= 1e9: return 1e9, " (billions)"
    if total >= 1e6: return 1e6, " (millions)"
    if total >= 1e3: return 1e3, " (thousands)"
    return 1, ""

scale, scale_lbl = get_scale(totals["total"])
def fmt_money(x): return f"{cur} {x/scale:,.2f}"

ru = data.get("rampup", {})
def avg(arr):
    try:
        arr = arr or [100]*12
        return sum(float(x) for x in arr)/max(1, len(arr))
    except Exception:
        return 0.0
avg_u  = avg(ru.get("utilities_pct"))
avg_lp = avg(ru.get("logistics_packaging_pct"))
avg_lt = avg(ru.get("logistics_transport_pct"))
avg_o  = avg(ru.get("other_pct"))
st.markdown(
    f"""
    <div style="margin:6px 0 0 0; padding:10px 12px; border:1px solid rgba(0,0,0,0.08); background:#f7f7f7; border-radius:10px; display:flex; gap:10px; flex-wrap:wrap;">
      <div style="font-weight:600; color:#333;">Ramp-up (avg year-1):</div>
      <div style="background:#fff; border:1px solid #e3e3e3; padding:4px 8px; border-radius:999px;">Utilities: {avg_u:.0f}%</div>
      <div style="background:#fff; border:1px solid #e3e3e3; padding:4px 8px; border-radius:999px;">Logistics - Packaging: {avg_lp:.0f}%</div>
      <div style="background:#fff; border:1px solid #e3e3e3; padding:4px 8px; border-radius:999px;">Logistics - Transport: {avg_lt:.0f}%</div>
      <div style="background:#fff; border:1px solid #e3e3e3; padding:4px 8px; border-radius:999px;">Other: {avg_o:.0f}%</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    .kpi-grid {display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; margin-top: 8px; margin-bottom: 8px;}
    .kpi {background: #f2f2f2; border: 1px solid rgba(0,0,0,0.08); padding: 14px 12px; border-radius: 12px;}
    .kpi .label {font-size: 0.9rem; color: #333; margin-bottom: 6px;}
    .kpi .value {font-size: 1.7rem; font-weight: 700; line-height: 1.2; color: #111; word-break: break-word; white-space: normal;}
    @media (max-width: 1100px){ .kpi-grid {grid-template-columns: repeat(3, minmax(0, 1fr));} }
    @media (max-width: 700px){ .kpi-grid {grid-template-columns: repeat(2, minmax(0, 1fr));} }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
def kpi(label, value):
    st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: kpi("Subtotal"+scale_lbl, fmt_money(totals['subtotal']))
with k2: kpi("Overhead"+scale_lbl, fmt_money(totals['overhead']))
with k3: kpi(f"Contingency ({totals['contingencyPct']:.1f}%)"+scale_lbl, fmt_money(totals['contingency']))
with k4: kpi("Tax"+scale_lbl, fmt_money(totals['tax']))
with k5: kpi("Risk (EMV)"+scale_lbl, fmt_money(totals['riskEMV']))
with k6: kpi(f"Total (Active scenario)"+scale_lbl, fmt_money(totals['total']))
st.markdown('</div>', unsafe_allow_html=True)

tpy = totals["tpy"]
unit_total_cost = (totals["total"]/tpy) if tpy else 0.0
st.metric("Unit total cost (steady state)", f"{cur} {unit_total_cost:,.2f} per t")

with st.expander("Process details"):
    proc_df = pd.DataFrame(totals["process"]["rows"])
    if len(proc_df):
        st.dataframe(proc_df.style.format({"annual_qty":"{:,.3f}","unit_cost":"{:,.4f}","annual_cost":"{:,.2f}"}), use_container_width=True)
    else:
        st.info("No process rows yet.")

with st.expander("Logistics / Waste / Custom / Additional costs"):
    extra_df = pd.DataFrame(totals["extra"]["rows"])
    rub_df = pd.DataFrame(totals.get("rubrics", {}).get("rows", []))
    if len(extra_df):
        st.dataframe(extra_df.style.format({"annual_qty":"{:,.3f}","unit_cost":"{:,.4f}","annual_cost":"{:,.2f}"}), use_container_width=True)
    if len(rub_df):
        st.dataframe(rub_df.style.format({"annual_qty":"{:,.3f}","unit_cost":"{:,.4f}","annual_cost":"{:,.2f}"}), use_container_width=True)
    if not len(extra_df) and not len(rub_df):
        st.info("No rows yet.")

st.subheader("Cost by Category")
bycat = pd.DataFrame([{"Category":k, "Cost":v} for k,v in totals["byCategory"].items()])
if not bycat.empty:
    bar = alt.Chart(bycat).mark_bar().encode(
        x=alt.X("Cost:Q", title=f"Cost ({cur})"),
        y=alt.Y("Category:N", sort="-x"),
        tooltip=[alt.Tooltip("Category:N"), alt.Tooltip("Cost:Q", format=",.2f")]
    ).properties(height=350)
    st.altair_chart(bar, use_container_width=True)

st.subheader("Scenario Compare — Total & Unit Costs")
rows = []
original_active = data.get("activeScenarioId")
for srow in data.get("scenarios", []):
    data["activeScenarioId"] = srow["id"]
    tt = compute_totals(data)
    unit = (tt["total"]/tt["tpy"]) if tt["tpy"] else 0.0
    rows.append({"Scenario": srow.get("name", srow["id"]), "Total": tt["total"], "Unit": unit,
                 "Subtotal": tt["subtotal"], "Overhead": tt["overhead"], "Contingency": tt["contingency"], "Tax": tt["tax"], "RiskEMV": tt["riskEMV"]})
data["activeScenarioId"] = original_active
scen_df = pd.DataFrame(rows)
if not scen_df.empty:
    show = scen_df.copy()
    def get_scale(total):
        if total >= 1e9: return 1e9
        if total >= 1e6: return 1e6
        if total >= 1e3: return 1e3
        return 1
    sc = get_scale(show["Total"].max())
    for col in ["Total","Subtotal","Overhead","Contingency","Tax","RiskEMV"]:
        show[col] = show[col].apply(lambda x: x/sc)
    st.dataframe(show.style.format({"Total":"{:,.2f}","Unit":"{:,.2f}","Subtotal":"{:,.2f}","Overhead":"{:,.2f}","Contingency":"{:,.2f}","Tax":"{:,.2f}","RiskEMV":"{:,.2f}"}), use_container_width=True)

    unit_chart = alt.Chart(scen_df).mark_bar().encode(
        x=alt.X("Scenario:N", sort=None),
        y=alt.Y("Unit:Q", title=f"Unit Cost ({cur}/t)"),
        tooltip=["Scenario", alt.Tooltip("Unit:Q", format=",.2f")]
    ).properties(height=280, title="Unit Cost by Scenario")
    total_chart = alt.Chart(show).mark_bar().encode(
        x=alt.X("Scenario:N", sort=None),
        y=alt.Y("Total:Q", title=f"Total Cost ({cur})"),
        tooltip=["Scenario", alt.Tooltip("Total:Q", format=",.2f")]
    ).properties(height=280, title="Total Cost by Scenario")
    st.altair_chart(unit_chart, use_container_width=True)
    st.altair_chart(total_chart, use_container_width=True)

st.subheader("Ramp-up — Utilities & Logistics subrubrics")
ramp_df = compute_ramp_monthly(data)
if not ramp_df.empty:
    melted = ramp_df.melt(id_vars=["Month"], value_vars=["Utilities","Logistics - Packaging","Logistics - Transport","Other"], var_name="Bucket", value_name="Cost")
    area = alt.Chart(melted).mark_area(opacity=0.7).encode(
        x=alt.X("Month:O"),
        y=alt.Y("Cost:Q", title=f"Monthly Cost ({cur})"),
        color="Bucket:N",
        tooltip=["Month","Bucket", alt.Tooltip("Cost:Q", format=",.2f")]
    ).properties(height=300)
    st.altair_chart(area, use_container_width=True)

    st.subheader("Ramp-up — tables (Year 1)")
    def _pad12(arr, fill=100):
        arr = list(arr or [fill]*12)
        if len(arr) < 12: arr = arr + [arr[-1]]*(12-len(arr))
        return arr[:12]
    ru = data.get("rampup", {}) or {}
    tbl = pd.DataFrame({
        "Month": list(range(1,13)),
        "Utilities %": _pad12(ru.get("utilities_pct", [100]*12)),
        "Log. Packaging %": _pad12(ru.get("logistics_packaging_pct", [100]*12)),
        "Log. Transport %": _pad12(ru.get("logistics_transport_pct", [100]*12)),
        "Other %": _pad12(ru.get("other_pct", [100]*12)),
        "Price %": _pad12(ru.get("price_pct", [100]*12)),
    })
    st.dataframe(tbl, use_container_width=True)
else:
    st.info("Ramp-up data not available.")
