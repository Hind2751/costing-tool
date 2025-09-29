import streamlit as st
import pandas as pd
from io import BytesIO

from utils.state import ensure_state, stage_sections
from utils.costing_core import ACCURACY_BANDS

st.set_page_config(page_title="Details — Inputs & Calculations", layout="wide")

PRICE_SOURCES = ["Benchmark", "Budgetary", "Firm", "Contract", "Estimate"]

def unit_options(cur: str):
    return {
        "recipe": [f"{cur}/t"],
        "materials": [f"{cur}/kg", f"{cur}/t", f"{cur}/L", f"{cur}/m3", f"{cur}/unit"],
        "utilities": [f"{cur}/kWh", f"{cur}/MWh", f"{cur}/Nm3", f"{cur}/m3", f"{cur}/GJ", f"{cur}/t", f"{cur}/unit"],
        "packaging": [f"{cur}/unit", f"{cur}/bag", f"{cur}/pallet", f"{cur}/drum"],
        "logistics": [f"{cur}/(t*km)", f"{cur}/t"],
        "waste": [f"{cur}/kg", f"{cur}/t"],
        "byproducts": [f"{cur}/t"],
        "rubrics": [f"{cur}/unit", f"{cur}/t", f"{cur}/y"],
    }

data = ensure_state(st)

with st.sidebar:
    st.title("Costing — Details")
    st.subheader("Project")
    data["project"]["name"] = st.text_input("Name", value=data["project"]["name"])
    stage_options = ["Feasibility", "Design", "Execution", "Commissioning"]
    if data["project"].get("stage") not in stage_options:
        data["project"]["stage"] = "Feasibility"
    data["project"]["stage"] = st.selectbox("Stage", stage_options, index=stage_options.index(data["project"]["stage"]))
    cur_list = ["MAD", "USD", "EUR", "GBP"]
    if data["project"].get("currency") not in cur_list:
        data["project"]["currency"] = "MAD"
    data["project"]["currency"] = st.selectbox("Currency", cur_list, index=cur_list.index(data["project"]["currency"]))
    data["project"]["discountRatePct"] = st.number_input("Discount rate (%)", value=float(data["project"].get("discountRatePct", 10.0)), step=0.1)
    data["project"]["durationMonths"] = int(st.number_input("Duration (months)", value=int(data["project"].get("durationMonths", 12)), step=1, min_value=1))

    st.subheader("Scenarios")
    scen_df = pd.DataFrame(data.get("scenarios", []))
    if scen_df.empty:
        scen_df = pd.DataFrame([{"id":"base","name":"Base","costMultiplier":1.0,"quantityMultiplier":1.0,"contingencyPctDelta":0.0}])
    scen_df = st.data_editor(scen_df, num_rows="dynamic", use_container_width=True, hide_index=True, key="scen_editor")
    data["scenarios"] = scen_df.to_dict(orient="records")
    scen_ids = [s["id"] for s in data["scenarios"]] if len(data["scenarios"]) else ["base"]
    if data.get("activeScenarioId") not in scen_ids:
        data["activeScenarioId"] = scen_ids[0]
    data["activeScenarioId"] = st.selectbox("Active scenario", options=scen_ids, index=scen_ids.index(data["activeScenarioId"]), key="active_scenario_details")

    # Quick Import in sidebar
    st.subheader("Import (quick)")
    up_sb = st.file_uploader("CSV/XLSX", type=["csv","xlsx"], key="sb_upl")
    tgt_sb = st.selectbox("Section", ["recipe","materials","utilities","byproducts","packaging","logistics","waste","rubrics","scenarios","capex","rampup"], key="sb_tgt")
    if st.button("Import (sidebar)") and up_sb is not None:
        try:
            if up_sb.name.lower().endswith(".csv"):
                df = pd.read_csv(up_sb)
                if tgt_sb == "recipe": data["recipe"] = df.to_dict("records")
                elif tgt_sb == "materials": data["process"]["materials"] = df.to_dict("records")
                elif tgt_sb == "utilities": data["process"]["utilities"] = df.to_dict("records")
                elif tgt_sb == "byproducts": data["process"]["byproducts"] = df.to_dict("records")
                elif tgt_sb == "packaging": data["packaging"] = df.to_dict("records")
                elif tgt_sb == "logistics": data["logistics"] = df.to_dict("records")
                elif tgt_sb == "waste": data["waste"] = df.to_dict("records")
                elif tgt_sb == "rubrics": data["rubrics"] = df.to_dict("records")
                elif tgt_sb == "scenarios": data["scenarios"] = df.to_dict("records")
                elif tgt_sb == "capex": data["finance"]["capex_items"] = df.to_dict("records")
                elif tgt_sb == "rampup": data["rampup"] = df.to_dict("list")
                st.success(f"Imported CSV into {tgt_sb}.")
            else:
                xls = pd.ExcelFile(up_sb)
                if "recipe" in xls.sheet_names: data["recipe"] = pd.read_excel(up_sb, sheet_name="recipe").to_dict("records")
                if "materials" in xls.sheet_names: data["process"]["materials"] = pd.read_excel(up_sb, sheet_name="materials").to_dict("records")
                if "utilities" in xls.sheet_names: data["process"]["utilities"] = pd.read_excel(up_sb, sheet_name="utilities").to_dict("records")
                if "byproducts" in xls.sheet_names: data["process"]["byproducts"] = pd.read_excel(up_sb, sheet_name="byproducts").to_dict("records")
                if "packaging" in xls.sheet_names: data["packaging"] = pd.read_excel(up_sb, sheet_name="packaging").to_dict("records")
                if "logistics" in xls.sheet_names: data["logistics"] = pd.read_excel(up_sb, sheet_name="logistics").to_dict("records")
                if "waste" in xls.sheet_names: data["waste"] = pd.read_excel(up_sb, sheet_name="waste").to_dict("records")
                if "rubrics" in xls.sheet_names: data["rubrics"] = pd.read_excel(up_sb, sheet_name="rubrics").to_dict("records")
                if "scenarios" in xls.sheet_names: data["scenarios"] = pd.read_excel(up_sb, sheet_name="scenarios").to_dict("records")
                if "capex" in xls.sheet_names: data["finance"]["capex_items"] = pd.read_excel(up_sb, sheet_name="capex").to_dict("records")
                if "rampup" in xls.sheet_names: data["rampup"] = pd.read_excel(up_sb, sheet_name="rampup").to_dict("list")
                st.success("Imported XLSX in sidebar.")
        except Exception as e:
            st.error(f"Import error: {e}")

cur = data["project"]["currency"]
stage = data["project"]["stage"]

st.header(f"Details — {data['project']['name']}")
# Project info directly under the title (as requested)
data["project"]["info"] = st.text_area("Project info (goal, scope, notes)", value=data["project"].get("info", ""), height=120, key="project_info_main")

acc = ACCURACY_BANDS.get(stage, None)
st.caption(f"Stage: {stage} • Currency: {cur}" + (f" • Accuracy: {acc[0]}% / +{acc[1]}%" if acc else ""))

# Throughput BEFORE Rubrics to display
p = data.get("process", {})
c_th0, c_th1 = st.columns([2, 1])
p["productName"] = c_th0.text_input("Final product name", value=p.get("productName", "Final Product"))
p["throughput_tpy"] = c_th1.number_input("Throughput (t/y) — steady state", value=float(p.get("throughput_tpy", 0.0)), step=100.0, min_value=0.0)
data["process"] = p

base_sec = stage_sections(stage)
RUBRICS_UI = [
    ("process_model","Process model — Mass & Energy"),
    ("consumables","Consumables"),
    ("utilities","Utilities"),
    ("byproducts","Byproducts"),
    ("logistics","Logistics"),
    ("waste","Waste"),
    ("custom","Custom"),
    ("additional","Additional production costs"),
    ("finance","Finance — CAPEX & Pricing"),
]
def _default_on(key: str) -> bool:
    if key == "process_model":  return bool(base_sec.get("recipe", True))
    if key == "consumables":    return bool(base_sec.get("materials", True))
    if key == "utilities":      return bool(base_sec.get("utilities", False))
    if key == "byproducts":     return bool(base_sec.get("byproducts", False))
    if key == "logistics":      return bool(base_sec.get("log_packaging", False) or base_sec.get("log_transport", False))
    if key == "waste":          return bool(base_sec.get("waste", False))
    if key == "custom":         return bool(base_sec.get("rubrics", False))
    if key == "additional":     return bool(base_sec.get("lineItems", True))
    if key == "finance":        return True
    return False

_ui_key = f"rubric_9pack_selection_{stage}"
if _ui_key not in st.session_state:
    st.session_state[_ui_key] = {k: _default_on(k) for k, _ in RUBRICS_UI}

st.markdown("### Rubrics to display")
cols = st.columns(3)
for i, (k, label) in enumerate(RUBRICS_UI):
    with cols[i % 3]:
        st.session_state[_ui_key][k] = st.toggle(label, value=st.session_state[_ui_key][k], key=f"{_ui_key}_{k}")
ui_sel = st.session_state[_ui_key]
sec = {
    "recipe":ui_sel["process_model"],
    "materials":ui_sel["consumables"],
    "utilities":ui_sel["utilities"],
    "byproducts":ui_sel["byproducts"],
    "log_packaging":ui_sel["logistics"],
    "log_transport":ui_sel["logistics"],
    "waste":ui_sel["waste"],
    "rubrics":ui_sel["custom"],
    "lineItems":ui_sel["additional"],
    "finance":ui_sel["finance"],
}

st.info(f"Basis: all intensities are per t of final product. Formulation is in t/t. Costs use selected currency units (e.g., {cur}/t, {cur}/kWh).")

uopt = unit_options(cur)

if sec.get("recipe", True):
    st.write("**Process model — Mass & Energy (t per t of product)**")
    rec_df = pd.DataFrame(data.get("recipe", []))
    if rec_df.empty:
        rec_df = pd.DataFrame([{"name":"","t_per_t":0.0,"unit":"t/t","unit_cost":0.0,"cost_unit":f"{cur}/t","price_source":"Benchmark","taxable":True,"note":""}])
    if "kg_per_t" in rec_df.columns and "t_per_t" not in rec_df.columns:
        rec_df["t_per_t"] = pd.to_numeric(rec_df["kg_per_t"], errors="coerce").fillna(0.0) / 1000.0
    rec_df = rec_df[["name","t_per_t","unit","unit_cost","cost_unit","price_source","taxable","note"]]
    rec_df = st.data_editor(rec_df, num_rows="dynamic", use_container_width=True, hide_index=True,
                            column_config={"cost_unit": st.column_config.SelectboxColumn(options=uopt["recipe"]),
                                           "price_source": st.column_config.SelectboxColumn(options=PRICE_SOURCES)})
    data["recipe"] = rec_df.to_dict(orient="records")

if sec.get("materials", True):
    st.write("**Process Consumables**")
    mat_df = pd.DataFrame(data["process"].get("materials", []))
    if mat_df.empty:
        mat_df = pd.DataFrame([{"name":"","spec_per_t":0.0,"unit_spec":"kg/t","unit_cost":0.0,"cost_unit":f"{cur}/kg","price_source":"Benchmark","category":"Materials","taxable":False,"note":""}])
    mat_df = st.data_editor(mat_df, num_rows="dynamic", use_container_width=True, hide_index=True,
                            column_config={"cost_unit": st.column_config.SelectboxColumn(options=uopt["materials"]),
                                           "price_source": st.column_config.SelectboxColumn(options=PRICE_SOURCES)})
    data["process"]["materials"] = mat_df.to_dict(orient="records")

if sec.get("utilities", False):
    st.write("**Utilities (incl. Steam)**")
    ut_df = pd.DataFrame(data["process"].get("utilities", []))
    if ut_df.empty:
        ut_df = pd.DataFrame([
            {"name":"Electricity","intensity_per_t":0.0,"unit_intensity":"kWh/t","tariff_per_unit":0.0,"tariff_unit":f"{cur}/kWh","price_source":"Benchmark","taxable":False,"note":""},
            {"name":"Steam","intensity_per_t":0.0,"unit_intensity":"t/t","tariff_per_unit":0.0,"tariff_unit":f"{cur}/t","price_source":"Benchmark","taxable":False,"note":""}
        ])
    ut_df = st.data_editor(ut_df, num_rows="dynamic", use_container_width=True, hide_index=True,
                           column_config={"tariff_unit": st.column_config.SelectboxColumn(options=uopt["utilities"]),
                                          "price_source": st.column_config.SelectboxColumn(options=PRICE_SOURCES)})
    data["process"]["utilities"] = ut_df.to_dict(orient="records")

if sec.get("byproducts", False):
    st.write("**Byproducts / Credits (optional)**")
    bp_df = pd.DataFrame(data["process"].get("byproducts", []))
    if bp_df.empty:
        bp_df = pd.DataFrame([{"name":"","credit_per_t":0.0,"unit":f"{cur}/t","note":""}])
    bp_df = st.data_editor(bp_df, num_rows="dynamic", use_container_width=True, hide_index=True,
                           column_config={"unit": st.column_config.SelectboxColumn(options=uopt["byproducts"])})
    data["process"]["byproducts"] = bp_df.to_dict(orient="records")

if sec.get("log_packaging", False) or sec.get("log_transport", False):
    st.subheader("Logistics")
    st.caption("Aggregates Packaging and Transport; both roll up to Logistics.")
    if sec.get("log_packaging", False):
        st.write("**Packaging**")
        pk_df = pd.DataFrame(data.get("packaging", []))
        if pk_df.empty:
            pk_df = pd.DataFrame([{"name":"","units_per_t":0.0,"unit_cost":0.0,"cost_unit":f"{cur}/unit","price_source":"Benchmark","taxable":True,"note":""}])
        pk_df = st.data_editor(pk_df, num_rows="dynamic", use_container_width=True, hide_index=True,
                               column_config={"cost_unit": st.column_config.SelectboxColumn(options=unit_options(cur)["packaging"]),
                                              "price_source": st.column_config.SelectboxColumn(options=PRICE_SOURCES)})
        data["packaging"] = pk_df.to_dict(orient="records")
    if sec.get("log_transport", False):
        st.write("**Transport**")
        lg_df = pd.DataFrame(data.get("logistics", []))
        if lg_df.empty:
            lg_df = pd.DataFrame([{"name":"","wet_t_per_t":1.0,"distance_km":0.0,"tariff_per_tkm":0.0,"cost_unit":f"{cur}/(t*km)","price_source":"Benchmark","taxable":True,"note":""}])
        lg_df = st.data_editor(lg_df, num_rows="dynamic", use_container_width=True, hide_index=True,
                               column_config={"cost_unit": st.column_config.SelectboxColumn(options=unit_options(cur)["logistics"]),
                                              "price_source": st.column_config.SelectboxColumn(options=PRICE_SOURCES)})
        data["logistics"] = lg_df.to_dict(orient="records")

if sec.get("waste", False):
    st.subheader("Waste")
    ws_df = pd.DataFrame(data.get("waste", []))
    if ws_df.empty:
        ws_df = pd.DataFrame([{"name":"","kg_per_t":0.0,"disposal_cost_per_kg":0.0,"cost_unit":f"{cur}/kg","price_source":"Benchmark","taxable":False,"note":""}])
    ws_df = st.data_editor(ws_df, num_rows="dynamic", use_container_width=True, hide_index=True,
                           column_config={"cost_unit": st.column_config.SelectboxColumn(options=unit_options(cur)["waste"]),
                                          "price_source": st.column_config.SelectboxColumn(options=PRICE_SOURCES)})
    data["waste"] = ws_df.to_dict(orient="records")

if sec.get("rubrics", False):
    st.subheader("Custom")
    rb = pd.DataFrame(data.get("rubrics", []))
    if rb.empty:
        rb = pd.DataFrame([{"name":"","basis":"per_t","quantity":0.0,"unit_cost":0.0,"cost_unit":f"{cur}/unit","map_to_category":"Other","price_source":"Benchmark","taxable":False,"note":""}])
    rb = st.data_editor(rb, num_rows="dynamic", use_container_width=True, hide_index=True,
                        column_config={
                            "basis": st.column_config.SelectboxColumn(options=["per_t","per_year","fixed_project"]),
                            "cost_unit": st.column_config.SelectboxColumn(options=[f"{cur}/unit", f"{cur}/t", f"{cur}/y"]),
                            "map_to_category": st.column_config.SelectboxColumn(options=["Labor","Formulation","Materials","Utilities","Logistics","Equipment","Subcontract","Travel","Capex","Opex","Other"]),
                            "price_source": st.column_config.SelectboxColumn(options=PRICE_SOURCES),
                        })
    data["rubrics"] = rb.to_dict(orient="records")

if sec.get("lineItems", False):
    st.subheader("Additional production costs")
    li_df = pd.DataFrame(data.get("lineItems", []))
    li_df = st.data_editor(li_df, num_rows="dynamic", use_container_width=True, hide_index=True)
    data["lineItems"] = li_df.to_dict(orient="records")

# -------- Ramp-up profiles (incl. Price ramp) --------
st.subheader("Ramp-up profiles")
ru = data.get("rampup", {}) or {}
def _pad12(arr, fill=100):
    arr = list(arr or [fill]*12)
    if len(arr) < 12: arr = arr + [arr[-1]]*(12-len(arr))
    return arr[:12]
c_ru1, c_ru2 = st.columns(2)
ru['utilities_pct'] = _pad12(ru.get('utilities_pct', [60,70,80,85,90,95,95,97,98,99,100,100]))
ru['logistics_packaging_pct'] = _pad12(ru.get('logistics_packaging_pct', [40,55,70,80,85,90,95,97,98,99,100,100]))
ru['logistics_transport_pct'] = _pad12(ru.get('logistics_transport_pct', [30,45,65,75,85,90,95,97,98,99,100,100]))
ru['other_pct'] = _pad12(ru.get('other_pct', [40,50,60,70,80,90,95,97,98,99,100,100]))
ru['price_pct'] = _pad12(ru.get('price_pct', [100]*12))
ru['startup_extra_cost_per_t'] = float(ru.get('startup_extra_cost_per_t', 0.0))
with c_ru1:
    st.write('Utilities (%) by month, Y1')
    ru['utilities_pct'] = st.data_editor(pd.DataFrame({'%':ru['utilities_pct']}), hide_index=True, use_container_width=True)['%'].tolist()
    st.write('Logistics — Packaging (%) by month, Y1')
    ru['logistics_packaging_pct'] = st.data_editor(pd.DataFrame({'%':ru['logistics_packaging_pct']}), hide_index=True, use_container_width=True)['%'].tolist()
with c_ru2:
    st.write('Logistics — Transport (%) by month, Y1')
    ru['logistics_transport_pct'] = st.data_editor(pd.DataFrame({'%':ru['logistics_transport_pct']}), hide_index=True, use_container_width=True)['%'].tolist()
    st.write('Other (%) by month, Y1')
    ru['other_pct'] = st.data_editor(pd.DataFrame({'%':ru['other_pct']}), hide_index=True, use_container_width=True)['%'].tolist()
st.write('Price ramp (%) by month, Y1 — multiplier of steady price')
ru['price_pct'] = st.data_editor(pd.DataFrame({'%':ru['price_pct']}), hide_index=True, use_container_width=True)['%'].tolist()
ru['startup_extra_cost_per_t'] = st.number_input('Startup extra cost per t (optional)', value=float(ru['startup_extra_cost_per_t']), step=1.0)
data['rampup'] = ru

# -------- Finance — CAPEX & Pricing (toggleable) --------
if sec.get("finance", True):
    st.subheader("Finance — CAPEX & Pricing")
    fin = data.setdefault("finance", data.get("finance", {}))

    c_f0, c_f1, c_f2 = st.columns(3)
    fin["selling_price_per_t"] = c_f0.number_input("Selling price (per t)", value=float(fin.get("selling_price_per_t", 0.0)), step=1.0, help="If 0, NPV becomes Net Present Cost (no revenue).")
    fin["horizon_years"] = int(c_f1.number_input("Horizon (years)", value=int(fin.get("horizon_years", 10)), min_value=1, max_value=40, step=1))
    fin["include_depreciation"] = bool(c_f2.checkbox("Include depreciation", value=bool(fin.get("include_depreciation", True))))

    st.markdown("**CAPEX items**")
    capex_df = pd.DataFrame(fin.get("capex_items", []))
    if capex_df.empty:
        capex_df = pd.DataFrame([{"name":"Equipment","amount":0.0,"year":0,"depr_years":10,"category":"Equipment"}])
    capex_df = st.data_editor(
        capex_df, use_container_width=True, num_rows="dynamic", hide_index=True,
        column_config={
            "name": st.column_config.TextColumn(),
            "amount": st.column_config.NumberColumn(format="%.2f"),
            "year": st.column_config.NumberColumn(help="In-service year; depreciation begins at year 0."),
            "depr_years": st.column_config.NumberColumn(format="%d"),
            "category": st.column_config.TextColumn(),
        }
    )
    fin["capex_items"] = capex_df.to_dict(orient="records")

    st.markdown("**CAPEX spend curve (%)**")
    curve_df = pd.DataFrame({"OffsetYear":[-1,0,1], "Percent": fin.get("capex_curve_pct", [60,35,5])[:3]})
    curve_df = st.data_editor(curve_df, hide_index=True)
    fin["capex_curve_pct"] = [float(x) for x in curve_df["Percent"].tolist()]

    data["finance"] = fin

# -------- Import data (full) --------
with st.expander("Import data (CSV/XLSX)"):
    up = st.file_uploader("Upload a workbook (.xlsx) with named sheets, or a CSV for a single section", type=["xlsx","csv"], key="full_import")
    section = st.selectbox("Target section (for CSV only)", ["recipe","materials","utilities","byproducts","packaging","logistics","waste","rubrics","scenarios","capex","rampup"], key="full_import_section")
    st.caption("XLSX supported sheets: recipe, materials, utilities, byproducts, packaging, logistics, waste, rubrics, scenarios, capex, rampup")
    do = st.button("Import", key="do_full_import")
    if st.button("Download XLSX template", key="dl_template"):
        bio_t = BytesIO()
        with pd.ExcelWriter(bio_t, engine="openpyxl") as xw:
            pd.DataFrame([{"name":"", "t_per_t":0.0, "unit":"t/t", "unit_cost":0.0, "cost_unit":f"{cur}/t", "price_source":"Benchmark", "taxable":True, "note":""}]).to_excel(xw, "recipe", index=False)
            pd.DataFrame([{"name":"", "spec_per_t":0.0, "unit_spec":"kg/t", "unit_cost":0.0, "cost_unit":f"{cur}/kg", "price_source":"Benchmark", "taxable":False, "note":""}]).to_excel(xw, "materials", index=False)
            pd.DataFrame([{"name":"Electricity","intensity_per_t":0.0,"unit_intensity":"kWh/t","tariff_per_unit":0.0,"tariff_unit":f"{cur}/kWh","price_source":"Benchmark","taxable":False,"note":""}]).to_excel(xw, "utilities", index=False)
            pd.DataFrame([{"name":"", "credit_per_t":0.0, "unit":f"{cur}/t", "note":""}]).to_excel(xw, "byproducts", index=False)
            pd.DataFrame([{"name":"", "units_per_t":0.0, "unit_cost":0.0, "cost_unit":f"{cur}/unit", "price_source":"Benchmark","taxable":True, "note":""}]).to_excel(xw, "packaging", index=False)
            pd.DataFrame([{"name":"", "wet_t_per_t":1.0, "distance_km":0.0, "tariff_per_tkm":0.0, "cost_unit":f"{cur}/(t*km)","price_source":"Benchmark","taxable":True,"note":""}]).to_excel(xw, "logistics", index=False)
            pd.DataFrame([{"name":"", "kg_per_t":0.0, "disposal_cost_per_kg":0.0, "cost_unit":f"{cur}/kg","price_source":"Benchmark","taxable":False,"note":""}]).to_excel(xw, "waste", index=False)
            pd.DataFrame([{"name":"", "basis":"per_t", "quantity":0.0, "unit_cost":0.0, "cost_unit":f"{cur}/unit", "map_to_category":"Other","price_source":"Benchmark","taxable":False,"note":""}]).to_excel(xw, "rubrics", index=False)
            pd.DataFrame([{"id":"base","name":"Base","costMultiplier":1.0,"quantityMultiplier":1.0,"contingencyPctDelta":0.0}]).to_excel(xw, "scenarios", index=False)
            pd.DataFrame([{"name":"Equipment","amount":0.0,"year":0,"depr_years":10,"category":"Equipment"}]).to_excel(xw, "capex", index=False)
            pd.DataFrame({"utilities_pct":[60,70,80,85,90,95,95,97,98,99,100,100],"logistics_packaging_pct":[40,55,70,80,85,90,95,97,98,99,100,100],"logistics_transport_pct":[30,45,65,75,85,90,95,97,98,99,100,100],"other_pct":[40,50,60,70,80,90,95,97,98,99,100,100],"price_pct":[100]*12}).to_excel(xw, "rampup", index=False)
        st.download_button("Download template (xlsx)", data=bio_t.getvalue(), file_name="costing_import_template.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if do and up is not None:
        try:
            if up.name.lower().endswith(".csv"):
                df = pd.read_csv(up)
                tgt = section
                if tgt == "recipe": data["recipe"] = df.to_dict("records")
                elif tgt == "materials": data["process"]["materials"] = df.to_dict("records")
                elif tgt == "utilities": data["process"]["utilities"] = df.to_dict("records")
                elif tgt == "byproducts": data["process"]["byproducts"] = df.to_dict("records")
                elif tgt == "packaging": data["packaging"] = df.to_dict("records")
                elif tgt == "logistics": data["logistics"] = df.to_dict("records")
                elif tgt == "waste": data["waste"] = df.to_dict("records")
                elif tgt == "rubrics": data["rubrics"] = df.to_dict("records")
                elif tgt == "scenarios": data["scenarios"] = df.to_dict("records")
                elif tgt == "capex": data["finance"]["capex_items"] = df.to_dict("records")
                elif tgt == "rampup": data["rampup"] = df.to_dict("list")
                st.success(f"Imported CSV into {tgt}.")
            else:
                xls = pd.ExcelFile(up)
                if "recipe" in xls.sheet_names: data["recipe"] = pd.read_excel(up, sheet_name="recipe").to_dict("records")
                if "materials" in xls.sheet_names: data["process"]["materials"] = pd.read_excel(up, sheet_name="materials").to_dict("records")
                if "utilities" in xls.sheet_names: data["process"]["utilities"] = pd.read_excel(up, sheet_name="utilities").to_dict("records")
                if "byproducts" in xls.sheet_names: data["process"]["byproducts"] = pd.read_excel(up, sheet_name="byproducts").to_dict("records")
                if "packaging" in xls.sheet_names: data["packaging"] = pd.read_excel(up, sheet_name="packaging").to_dict("records")
                if "logistics" in xls.sheet_names: data["logistics"] = pd.read_excel(up, sheet_name="logistics").to_dict("records")
                if "waste" in xls.sheet_names: data["waste"] = pd.read_excel(up, sheet_name="waste").to_dict("records")
                if "rubrics" in xls.sheet_names: data["rubrics"] = pd.read_excel(up, sheet_name="rubrics").to_dict("records")
                if "scenarios" in xls.sheet_names: data["scenarios"] = pd.read_excel(up, sheet_name="scenarios").to_dict("records")
                if "capex" in xls.sheet_names: data["finance"]["capex_items"] = pd.read_excel(up, sheet_name="capex").to_dict("records")
                if "rampup" in xls.sheet_names: data["rampup"] = pd.read_excel(up, sheet_name="rampup").to_dict("list")
                st.success("Imported XLSX. Sheets found: " + ", ".join(xls.sheet_names))
        except Exception as e:
            st.error(f"Import error: {e}")

# Export snapshot
st.subheader("Export data snapshot")
bio = BytesIO()
with pd.ExcelWriter(bio, engine="openpyxl") as xw:
    pd.DataFrame(data.get("recipe", [])).to_excel(xw, sheet_name="recipe", index=False)
    pd.DataFrame(data.get("process", {}).get("materials", [])).to_excel(xw, sheet_name="materials", index=False)
    pd.DataFrame(data.get("process", {}).get("utilities", [])).to_excel(xw, sheet_name="utilities", index=False)
    pd.DataFrame(data.get("process", {}).get("byproducts", [])).to_excel(xw, sheet_name="byproducts", index=False)
    pd.DataFrame(data.get("packaging", [])).to_excel(xw, sheet_name="packaging", index=False)
    pd.DataFrame(data.get("logistics", [])).to_excel(xw, sheet_name="logistics", index=False)
    pd.DataFrame(data.get("waste", [])).to_excel(xw, sheet_name="waste", index=False)
    pd.DataFrame(data.get("rubrics", [])).to_excel(xw, sheet_name="rubrics", index=False)
    pd.DataFrame(data.get("finance", {}).get("capex_items", [])).to_excel(xw, sheet_name="capex", index=False)
st.download_button("Download snapshot (xlsx)", data=bio.getvalue(), file_name="costing_snapshot.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
