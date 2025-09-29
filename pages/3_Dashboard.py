import streamlit as st
import pandas as pd
import altair as alt

from utils.state import ensure_state
from utils.costing_core import compute_totals, project_financials, ACCURACY_BANDS, compute_ramp_monthly

st.set_page_config(page_title="Dashboard — Finance & Custom Charts", layout="wide")
data = ensure_state(st)

st.header(f"Dashboard — {data['project']['name']}")

with st.sidebar:
    st.subheader("Finance Settings (read-only inputs live in Details)")
    fin = data.setdefault("finance", data.get("finance", {}))
    st.caption("Edit CAPEX, price, horizon, depreciation in Details → Finance — CAPEX & Pricing")
    st.write(f"Price/t: {fin.get('selling_price_per_t', 0.0)} | Horizon: {fin.get('horizon_years', 10)} | Depreciation: {bool(fin.get('include_depreciation', True))}")

st.subheader("Financial Projection")
totals_now = compute_totals(data)
proj = project_financials(data)
cur = data["project"]["currency"]
band = ACCURACY_BANDS.get(data["project"]["stage"], None)
acc_label = f"Accuracy: {band[0]}% / +{band[1]}%" if band else ""

# KPI cards
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

irr_txt = "n/a" if proj["irr"] is None else f"{proj['irr']*100:,.2f}%"
def _scale_fmt(cur, x):
    x = float(x)
    if abs(x) >= 1e9: return f"{cur} {x/1e9:,.2f} B"
    if abs(x) >= 1e6: return f"{cur} {x/1e6:,.2f} M"
    if abs(x) >= 1e3: return f"{cur} {x/1e3:,.2f} K"
    return f"{cur} {x:,.2f}"

st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
def kpi(label, value):
    st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: kpi("NPV (FCF)", _scale_fmt(cur, proj["npv"]))
with k2: kpi("IRR", irr_txt)
with k3: kpi("Payback (year)", proj["payback_year"] if proj["payback_year"] is not None else "n/a")
with k4: kpi("Year-0 CAPEX", _scale_fmt(cur, proj["year0_capex"]))
with k5: kpi("Peak OPEX (annual)", _scale_fmt(cur, proj["peak_opex"]))
with k6: kpi("Peak Revenue (annual)", _scale_fmt(cur, proj["peak_revenue"]))
st.markdown('</div>', unsafe_allow_html=True)

st.caption(f"{acc_label} — Currency: {cur} — Discount rate: {data['project']['discountRatePct']:.2f}% — Tax: {data['settings']['taxPct']:.2f}% — Escalation: {data['settings']['escalationPctPerYear']:.2f}%/y")

df = proj["years_df"].copy()
df["Cum_FCF"] = df["FCF"].cumsum()

left, right = st.columns([2,1])
with left:
    area = alt.Chart(df.melt(id_vars=["Year"], value_vars=["Revenue","OPEX","CAPEX","Tax","Depreciation"], var_name="Bucket", value_name="Amount")).mark_area(opacity=0.7).encode(
        x="Year:O",
        y=alt.Y("Amount:Q", title=f"Amount ({cur})"),
        color="Bucket:N",
        tooltip=["Year","Bucket", alt.Tooltip("Amount:Q", format=",.2f")]
    ).properties(height=320, title="Annual Buckets")
    st.altair_chart(area, use_container_width=True)

    line = alt.Chart(df).mark_line(point=True).encode(
        x="Year:O",
        y=alt.Y("FCF:Q", title=f"Free Cash Flow ({cur})"),
        tooltip=["Year", alt.Tooltip("FCF:Q", format=",.2f")]
    ).properties(height=280, title="Free Cash Flow")
    st.altair_chart(line, use_container_width=True)

with right:
    cum = alt.Chart(df).mark_line(point=True).encode(
        x="Year:O",
        y=alt.Y("Cum_FCF:Q", title=f" Cumulative FCF ({cur})"),
        tooltip=["Year", alt.Tooltip("Cum_FCF:Q", format=",.2f")]
    ).properties(height=320, title="Cumulative FCF")
    st.altair_chart(cum, use_container_width=True)

st.subheader("Table — Projection")
show = df.copy()
st.dataframe(show.style.format({"CAPEX":"{:,.2f}","Revenue":"{:,.2f}","OPEX":"{:,.2f}","Depreciation":"{:,.2f}","Tax":"{:,.2f}","OCF":"{:,.2f}","FCF":"{:,.2f}","PV_FCF":"{:,.2f}","Cum_FCF":"{:,.2f}"}), use_container_width=True)

st.subheader("Custom Chart Builder")
st.caption("Build your own charts from available datasets.")
totals_now = compute_totals(data)
datasets = {
    "By Category (current year)": pd.DataFrame([{"Category":k, "Cost":v} for k,v in totals_now["byCategory"].items()]),
    "Scenarios (summary)": None,
    "Ramp-up (monthly cost)": None,
    "Finance (projection)": df.copy(),
}
rows = []
original_active = data.get("activeScenarioId")
for srow in data.get("scenarios", []):
    data["activeScenarioId"] = srow["id"]
    tt = compute_totals(data)
    unit = (tt["total"]/tt["tpy"]) if tt["tpy"] else 0.0
    rows.append({"Scenario": srow.get("name", srow["id"]), "Total": tt["total"], "Unit": unit,
                 "Subtotal": tt["subtotal"], "Overhead": tt["overhead"], "Contingency": tt["contingency"], "Tax": tt["tax"], "RiskEMV": tt["riskEMV"]})
data["activeScenarioId"] = original_active
datasets["Scenarios (summary)"] = pd.DataFrame(rows)
ramp_df = compute_ramp_monthly(data)
if not ramp_df.empty:
    datasets["Ramp-up (monthly cost)"] = ramp_df.melt(id_vars=["Month"], var_name="Bucket", value_name="Cost")
ds_name = st.selectbox("Dataset", list(datasets.keys()))
ds = datasets[ds_name]
if ds is None or ds.empty:
    st.info("Selected dataset is empty. Please add inputs first.")
else:
    cols = list(ds.columns)
    x = st.selectbox("X", cols, key="cust_x")
    y = st.selectbox("Y", cols, key="cust_y")
    series = st.multiselect("Series (optional)", [c for c in cols if c not in [x, y]], key="cust_series")
    chart_type = st.selectbox("Chart type", ["bar","line","area","point"])
    base = alt.Chart(ds)
    if chart_type == "bar":
        enc = base.mark_bar()
    elif chart_type == "line":
        enc = base.mark_line(point=True)
    elif chart_type == "area":
        enc = base.mark_area(opacity=0.7)
    else:
        enc = base.mark_point()
    if series:
        chart = enc.encode(
            x=f"{x}:O" if ds[x].dtype.kind in "biu" else f"{x}:N",
            y=f"{y}:Q",
            color=series[0]+":N",
            tooltip=[x, y] + series[:1]
        ).properties(height=320, title=f"{ds_name}")
    else:
        chart = enc.encode(
            x=f"{x}:O" if ds[x].dtype.kind in "biu" else f"{x}:N",
            y=f"{y}:Q",
            tooltip=[x, y]
        ).properties(height=320, title=f"{ds_name}")
    st.altair_chart(chart, use_container_width=True)
