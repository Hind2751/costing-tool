from typing import Dict, Any, List
import json
import pandas as pd

ACCURACY_BANDS: Dict[str, tuple] = {
    "Feasibility": (-30, +50),
    "Design": (-20, +30),
    "Execution": (-10, +15),
    "Commissioning": (-10, +10),
}

STAGE_PROFILE: Dict[str, Dict[str, Any]] = {
    "Feasibility": {"contingency": 28, "sections": {"recipe": True,"materials": True,"utilities": False,"byproducts": True,"log_packaging": False,"log_transport": False,"waste": True,"rubrics": True,"lineItems": True}},
    "Design": {"contingency": 20, "sections": {"recipe": True,"materials": True,"utilities": True,"byproducts": True,"log_packaging": True,"log_transport": True,"waste": True,"rubrics": True,"lineItems": True}},
    "Execution": {"contingency": 12, "sections": {"recipe": True,"materials": True,"utilities": True,"byproducts": True,"log_packaging": True,"log_transport": True,"waste": True,"rubrics": True,"lineItems": True}},
    "Commissioning": {"contingency": 7, "sections": {"recipe": True,"materials": True,"utilities": True,"byproducts": True,"log_packaging": True,"log_transport": True,"waste": True,"rubrics": True,"lineItems": True}},
}

def deep(d: Any) -> Any:
    return json.loads(json.dumps(d))

def fnum(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0

def current_scenario(data: Dict[str, Any]) -> Dict[str, Any]:
    sid = data.get("activeScenarioId")
    for s in data.get("scenarios", []):
        if s.get("id") == sid:
            return s
    return {"costMultiplier": 1.0, "quantityMultiplier": 1.0, "contingencyPctDelta": 0.0}

DEFAULT_PRESETS: Dict[str, Any] = {
    "Generic Process": {
        "process": {
            "productName": "Final Product",
            "throughput_tpy": 10000.0,
            "materials": [{
                "name": "Generic reagent",
                "spec_per_t": 10.0,
                "unit_spec": "kg/t",
                "unit_cost": 5.0,
                "cost_unit": "MAD/kg",
                "price_source": "Benchmark",
                "category": "Materials",
                "taxable": True,
                "note": "",
            }],
            "utilities": [
                {"name": "Electricity","intensity_per_t": 50.0,"unit_intensity": "kWh/t","tariff_per_unit": 1.0,"tariff_unit": "MAD/kWh","price_source": "Benchmark","taxable": False,"note": ""},
                {"name": "Steam","intensity_per_t": 0.0,"unit_intensity":"t/t","tariff_per_unit": 320.0,"tariff_unit":"MAD/t","price_source":"Benchmark","taxable":False,"note":""},
            ],
            "byproducts": [],
        },
        "logistics": [{
            "name": "Plant -> Depot (transport)",
            "wet_t_per_t": 1.0,
            "distance_km": 50.0,
            "tariff_per_tkm": 0.6,
            "cost_unit": "MAD/(t*km)",
            "price_source": "Benchmark",
            "taxable": True,
            "note": "",
        }],
        "packaging": [{
            "name": "Bulk bags (1 t)",
            "units_per_t": 1.0,
            "unit_cost": 30.0,
            "cost_unit": "MAD/unit",
            "price_source": "Benchmark",
            "taxable": True,
            "note": "",
        }],
        "waste": [{
            "name": "Filter cake disposal",
            "kg_per_t": 5.0,
            "disposal_cost_per_kg": 0.5,
            "cost_unit": "MAD/kg",
            "price_source": "Benchmark",
            "taxable": False,
            "note": "",
        }],
        "rampup": {"utilities_pct":[60,70,80,85,90,95,95,97,98,99,100,100],"logistics_packaging_pct":[40,55,70,80,85,90,95,97,98,99,100,100],"logistics_transport_pct":[30,45,65,75,85,90,95,97,98,99,100,100],"other_pct":[40,50,60,70,80,90,95,97,98,99,100,100],"price_pct":[100]*12,"startup_extra_cost_per_t":0.0},
        "rubrics": [],
        "capex_items": [
            {"name":"Process equipment","amount": 5_000_000.0,"year":0,"depr_years":10,"category":"Equipment"},
            {"name":"Installation","amount": 1_200_000.0,"year":0,"depr_years":10,"category":"Installation"},
            {"name":"EPCM","amount": 800_000.0,"year":0,"depr_years":10,"category":"Services"},
        ],
        "capex_curve_pct": [60, 35, 5],
    }
}

DEFAULT_STATE: Dict[str, Any] = {
    "project": {"name": "New Project","type": "Process","stage": "Feasibility","currency": "MAD","discountRatePct": 10.0,"durationMonths": 12,"info": ""},
    "lineItems": [{"id": "li1","category": "Labor","description": "Process engineer (200 h)","unit": "h","quantity": 200.0,"unitCost": 350.0,"taxable": False,"accountCode": "","driver": ""}],
    "rates": [{"name": "Process Engineer", "hourly": 350.0},{"name": "Lab Technician", "hourly": 150.0},{"name": "Project Manager", "hourly": 400.0}],
    "risks": [{"id": "r1","name": "Delay in reagent delivery","probability": 0.3,"impactCost": 120000.0}],
    "scenarios": [
        {"id":"base","name":"Base","costMultiplier":1.0,"quantityMultiplier":1.0,"contingencyPctDelta":0.0},
        {"id":"optimistic","name":"Optimistic","costMultiplier":0.95,"quantityMultiplier":0.95,"contingencyPctDelta":-2.0},
        {"id":"pessimistic","name":"Pessimistic","costMultiplier":1.10,"quantityMultiplier":1.05,"contingencyPctDelta":3.0},
    ],
    "settings": {"taxPct": 20.0,"contingencyPct": 25.0,"overheadPct": 25.0,"overheadBase": ["Labor","Logistics"],"escalationPctPerYear": 3.0,"discountNominal": True},
    "activeScenarioId": "base",
    "presetName": "Generic Process",
    "process": deep(DEFAULT_PRESETS["Generic Process"]["process"]),
    "logistics": deep(DEFAULT_PRESETS["Generic Process"]["logistics"]),
    "packaging": deep(DEFAULT_PRESETS["Generic Process"]["packaging"]),
    "waste": deep(DEFAULT_PRESETS["Generic Process"]["waste"]),
    "rampup": deep(DEFAULT_PRESETS["Generic Process"]["rampup"]),
    "rubrics": deep(DEFAULT_PRESETS["Generic Process"]["rubrics"]),
    "recipe": [],
    "finance": {
        "horizon_years": 10,
        "start_year": 0,
        "selling_price_per_t": 0.0,
        "capex_items": deep(DEFAULT_PRESETS["Generic Process"]["capex_items"]),
        "capex_curve_pct": deep(DEFAULT_PRESETS["Generic Process"]["capex_curve_pct"]),
        "include_depreciation": True,
        "working_capital_pct_of_opex": 0.0,
        "wc_recovery_end": True,
    }
}

def compute_process_costs(data: Dict[str, Any]) -> Dict[str, Any]:
    scen = current_scenario(data)
    qm = fnum(scen.get("quantityMultiplier", 1.0))
    cm = fnum(scen.get("costMultiplier", 1.0))
    p = data.get("process", {}) or {}
    tpy = fnum(p.get("throughput_tpy", 0.0)) * qm
    rows: List[Dict[str, Any]] = []
    totals = {"Materials": 0.0, "Utilities": 0.0, "ByproductCredits": 0.0, "Formulation": 0.0, "TaxableBase": 0.0}
    cur = data.get("project", {}).get("currency", "MAD")

    for r in data.get("recipe", []) or []:
        t_per_t_val = r.get("t_per_t")
        if t_per_t_val is None:
            t_per_t = fnum(r.get("kg_per_t", 0.0)) / 1000.0
        else:
            t_per_t = fnum(t_per_t_val)
        annual_qty = t_per_t * tpy
        unit_cost = fnum(r.get("unit_cost", 0.0)) * cm
        cost = annual_qty * unit_cost
        rows.append({"module":"Formulation (t/t)","name":r.get("name",""),"annual_qty":annual_qty,"qty_unit":"t/y","unit_cost":unit_cost,"cost_unit":r.get("cost_unit", f"{cur}/t"),"price_source":r.get("price_source","Benchmark"),"annual_cost":cost,"category":"Formulation","taxable":bool(r.get("taxable",True)),"note":r.get("note","")})
        totals["Formulation"] += cost
        if r.get("taxable", True):
            totals["TaxableBase"] += cost

    for m in p.get("materials", []) or []:
        spec = fnum(m.get("spec_per_t", 0.0))
        unit_cost = fnum(m.get("unit_cost", 0.0)) * cm
        annual_qty = spec * tpy
        cost = annual_qty * unit_cost
        unit_spec = (m.get("unit_spec", "kg/t") or "kg/t").split("/")[0] + "/y"
        rows.append({"module":"Process Consumable","name":m.get("name",""),"annual_qty":annual_qty,"qty_unit":unit_spec,"unit_cost":unit_cost,"cost_unit":m.get("cost_unit", f"{cur}/unit"),"price_source":m.get("price_source","Benchmark"),"annual_cost":cost,"category":"Materials","taxable":bool(m.get("taxable",False)),"note":m.get("note","")})
        totals["Materials"] += cost
        if m.get("taxable", False):
            totals["TaxableBase"] += cost

    for u in p.get("utilities", []) or []:
        intensity = fnum(u.get("intensity_per_t", 0.0))
        tariff = fnum(u.get("tariff_per_unit", 0.0)) * cm
        annual_qty = intensity * tpy
        cost = annual_qty * tariff
        qty_unit = (u.get("unit_intensity", "unit/t") or "unit/t").split("/")[0] + "/y"
        rows.append({"module":"Utility","name":u.get("name",""),"annual_qty":annual_qty,"qty_unit":qty_unit,"unit_cost":tariff,"cost_unit":u.get("tariff_unit", f"{cur}/unit"),"price_source":u.get("price_source","Benchmark"),"annual_cost":cost,"category":"Utilities","taxable":bool(u.get("taxable",False)),"note":u.get("note","")})
        totals["Utilities"] += cost
        if u.get("taxable", False):
            totals["TaxableBase"] += cost

    for b in p.get("byproducts", []) or []:
        credit_per_t = fnum(b.get("credit_per_t", 0.0)) * cm
        credit = credit_per_t * tpy
        rows.append({"module":"Byproduct","name":b.get("name",""),"annual_qty":tpy,"qty_unit":"t/y","unit_cost":credit_per_t,"cost_unit":b.get("unit", f"{cur}/t"),"price_source":"N/A","annual_cost":credit,"category":"Other","taxable":False,"note":b.get("note","")})
        totals["ByproductCredits"] += credit

    return {"rows": rows, "totals": totals, "tpy": tpy}

def compute_extra_modules_costs(data: Dict[str, Any]) -> Dict[str, Any]:
    scen = current_scenario(data)
    qm = fnum(scen.get("quantityMultiplier", 1.0))
    cm = fnum(scen.get("costMultiplier", 1.0))
    tpy = fnum(data.get("process", {}).get("throughput_tpy", 0.0)) * qm
    rows: List[Dict[str, Any]] = []
    totals = {"Packaging": 0.0, "Transport": 0.0, "Waste": 0.0, "TaxableBase": 0.0}
    cur = data.get("project", {}).get("currency", "MAD")

    for p in data.get("packaging", []) or []:
        units = fnum(p.get("units_per_t", 0.0)) * tpy
        unit_cost = fnum(p.get("unit_cost", 0.0)) * cm
        cost = units * unit_cost
        rows.append({"module":"Packaging","name":p.get("name",""),"annual_qty":units,"qty_unit":"units/y","unit_cost":unit_cost,"cost_unit":p.get("cost_unit", f"{cur}/unit"),"price_source":p.get("price_source","Benchmark"),"annual_cost":cost,"category":"Logistics","taxable":bool(p.get("taxable",True)),"note":p.get("note","")})
        totals["Packaging"] += cost
        if p.get("taxable", True):
            totals["TaxableBase"] += cost

    for l in data.get("logistics", []) or []:
        ton_km = fnum(l.get("wet_t_per_t", 1.0)) * fnum(l.get("distance_km", 0.0)) * tpy
        tariff = fnum(l.get("tariff_per_tkm", 0.0)) * cm
        cost = ton_km * tariff
        rows.append({"module":"Transport","name":l.get("name",""),"annual_qty":ton_km,"qty_unit":"t*km/y","unit_cost":tariff,"cost_unit":l.get("cost_unit", f"{cur}/(t*km)"),"price_source":l.get("price_source","Benchmark"),"annual_cost":cost,"category":"Logistics","taxable":bool(l.get("taxable",True)),"note":l.get("note","")})
        totals["Transport"] += cost
        if l.get("taxable", True):
            totals["TaxableBase"] += cost

    for w in data.get("waste", []) or []:
        qty = fnum(w.get("kg_per_t", 0.0)) * tpy
        unit_cost = fnum(w.get("disposal_cost_per_kg", 0.0)) * cm
        cost = qty * unit_cost
        rows.append({"module":"Waste","name":w.get("name",""),"annual_qty":qty,"qty_unit":"kg/y","unit_cost":unit_cost,"cost_unit":w.get("cost_unit", f"{cur}/kg"),"price_source":w.get("price_source","Benchmark"),"annual_cost":cost,"category":"Other","taxable":bool(w.get("taxable",False)),"note":w.get("note","")})
        totals["Waste"] += cost
        if w.get("taxable", False):
            totals["TaxableBase"] += cost

    return {"rows": rows, "totals": totals, "tpy": tpy}

def compute_rubrics_costs(data: Dict[str, Any]) -> Dict[str, Any]:
    scen = current_scenario(data)
    qm = fnum(scen.get("quantityMultiplier", 1.0))
    cm = fnum(scen.get("costMultiplier", 1.0))
    tpy = fnum(data.get("process", {}).get("throughput_tpy", 0.0)) * qm
    rows: List[Dict[str, Any]] = []
    totals = {"Rubrics": 0.0, "TaxableBase": 0.0}
    cur = data.get("project", {}).get("currency", "MAD")

    for r in data.get("rubrics", []) or []:
        basis = (r.get("basis") or "per_t").strip().lower()
        qty = fnum(r.get("quantity", 0.0))
        unit_cost = fnum(r.get("unit_cost", 0.0)) * cm
        map_cat = r.get("map_to_category", "Other") or "Other"
        if basis == "per_t":
            annual_qty = qty * tpy
        elif basis == "per_year":
            annual_qty = qty * 1.0
        elif basis == "fixed_project":
            annual_qty = 1.0
            unit_cost = fnum(r.get("quantity", 0.0)) * cm
        else:
            annual_qty = qty * 1.0
        cost = annual_qty * unit_cost
        rows.append({"module":"Rubric","name":r.get("name",""),"basis":basis,"annual_qty":annual_qty,"qty_unit":"basis-dependent","unit_cost":unit_cost,"cost_unit":r.get("cost_unit", f"{cur}/unit"),"price_source":r.get("price_source","Benchmark"),"annual_cost":cost,"category":map_cat,"taxable":bool(r.get("taxable",False)),"note":r.get("note","")})
        totals["Rubrics"] += cost
        if r.get("taxable", False):
            totals["TaxableBase"] += cost
    return {"rows": rows, "totals": totals, "tpy": tpy}

def compute_totals(data: Dict[str, Any]) -> Dict[str, Any]:
    scen = current_scenario(data)
    contingency_pct = fnum(data.get("settings", {}).get("contingencyPct", 0.0)) + fnum(scen.get("contingencyPctDelta", 0.0))

    by_cat: Dict[str, float] = {}
    taxable_manual = 0.0
    subtotal_manual = 0.0
    qm = fnum(scen.get("quantityMultiplier", 1.0))
    cm = fnum(scen.get("costMultiplier", 1.0))

    for li in (data.get("lineItems", []) or []):
        cost = fnum(li.get("quantity", 0.0)) * qm * fnum(li.get("unitCost", 0.0)) * cm
        subtotal_manual += cost
        cat = li.get("category", "Other")
        by_cat[cat] = by_cat.get(cat, 0.0) + cost
        if li.get("taxable", False):
            taxable_manual += cost

    proc = compute_process_costs(data)
    by_cat["Formulation"] = by_cat.get("Formulation", 0.0) + proc["totals"]["Formulation"]
    by_cat["Materials"] = by_cat.get("Materials", 0.0) + proc["totals"]["Materials"]
    by_cat["Utilities"] = by_cat.get("Utilities", 0.0) + proc["totals"]["Utilities"]
    by_cat["Other"] = by_cat.get("Other", 0.0) + proc["totals"]["ByproductCredits"]
    taxable_base = taxable_manual + proc["totals"]["TaxableBase"]

    extra = compute_extra_modules_costs(data)
    by_cat["Logistics"] = by_cat.get("Logistics", 0.0) + extra["totals"]["Packaging"] + extra["totals"]["Transport"]
    by_cat["Other"] = by_cat.get("Other", 0.0) + extra["totals"]["Waste"]
    taxable_base += extra["totals"]["TaxableBase"]

    rub = compute_rubrics_costs(data) if data.get("rubrics") else {"rows": [], "totals": {"Rubrics": 0.0, "TaxableBase": 0.0}}
    for r in rub["rows"]:
        cat = r.get("category", "Other")
        by_cat[cat] = by_cat.get(cat, 0.0) + r["annual_cost"]
    taxable_base += rub["totals"]["TaxableBase"]

    subtotal = subtotal_manual + sum(proc["totals"].values()) - proc["totals"]["TaxableBase"] + sum(extra["totals"].values()) - extra["totals"]["TaxableBase"] + sum(rub["totals"].values()) - rub["totals"]["TaxableBase"]
    settings = data.get("settings", {})
    overhead_base_cats = set(settings.get("overheadBase", ["Labor", "Logistics"]))
    base_for_overhead = sum(v for k, v in by_cat.items() if k in overhead_base_cats)
    overhead = base_for_overhead * fnum(settings.get("overheadPct", 0.0)) / 100.0

    pre_tax = subtotal + overhead
    contingency = pre_tax * contingency_pct / 100.0
    tax = taxable_base * fnum(settings.get("taxPct", 0.0)) / 100.0
    risk_emv = sum(fnum(r.get("probability", 0.0)) * fnum(r.get("impactCost", 0.0)) for r in (data.get("risks", []) or []))
    total = pre_tax + contingency + tax + risk_emv

    breakdown = {"utilities_total": proc["totals"]["Utilities"], "log_packaging_total": extra["totals"]["Packaging"], "log_transport_total": extra["totals"]["Transport"]}

    return {"byCategory": by_cat,"subtotal": subtotal,"overhead": overhead,"contingency": contingency,"tax": tax,"riskEMV": risk_emv,"total": total,"contingencyPct": contingency_pct,"process": proc,"extra": extra,"rubrics": rub,"breakdown": breakdown,"tpy": proc["tpy"]}

def compute_ramp_monthly(data: Dict[str, Any]) -> pd.DataFrame:
    totals = compute_totals(data)
    b = totals["breakdown"]
    util_annual = b.get("utilities_total", 0.0)
    log_pack_annual = b.get("log_packaging_total", 0.0)
    log_trans_annual = b.get("log_transport_total", 0.0)
    other_annual = sum(v for k, v in totals["byCategory"].items() if k not in ("Utilities", "Logistics"))
    ru = data.get("rampup", {}) or {}
    def pad12(arr):
        arr = list(arr or [100] * 12)
        if len(arr) < 12: arr = arr + [arr[-1]] * (12 - len(arr))
        return arr[:12]
    up = pad12(ru.get("utilities_pct"))
    lp = pad12(ru.get("logistics_packaging_pct"))
    lt = pad12(ru.get("logistics_transport_pct"))
    op = pad12(ru.get("other_pct"))
    rows = []
    for i in range(12):
        rows.append({"Month": i + 1, "Utilities": util_annual / 12.0 * (up[i] / 100.0), "Logistics - Packaging": log_pack_annual / 12.0 * (lp[i] / 100.0), "Logistics - Transport": log_trans_annual / 12.0 * (lt[i] / 100.0), "Other": other_annual / 12.0 * (op[i] / 100.0)})
    return pd.DataFrame(rows)

def capex_spend_by_year(fin: Dict[str, Any]) -> Dict[int, float]:
    items = fin.get("capex_items", []) or []
    curve = fin.get("capex_curve_pct", [100])
    s = sum([fnum(x) for x in curve]) or 100.0
    curve = [fnum(x) * 100.0 / s for x in curve]
    total = sum(fnum(i.get("amount", 0.0)) for i in items)
    spend = {}
    offsets = list(range(-1, -1 + len(curve)))
    for off, pct in zip(offsets, curve):
        spend[off] = total * pct / 100.0
    return spend

def project_financials(data: Dict[str, Any]) -> Dict[str, Any]:
    cur = data.get("project", {}).get("currency", "MAD")
    fin = data.get("finance", {})
    horizon = int(fnum(fin.get("horizon_years", 10)))
    price = fnum(fin.get("selling_price_per_t", 0.0))
    esc = fnum(data.get("settings", {}).get("escalationPctPerYear", 0.0)) / 100.0
    tax_rate = fnum(data.get("settings", {}).get("taxPct", 0.0)) / 100.0
    disc = fnum(data.get("project", {}).get("discountRatePct", 10.0)) / 100.0
    totals_now = compute_totals(data)
    base_opex = totals_now["subtotal"] + totals_now["overhead"] + totals_now["tax"]
    tpy = totals_now["tpy"]
    years = list(range(0, horizon+1))
    capex_curve = capex_spend_by_year(fin)

    ru = data.get("rampup", {}) or {}
    price_pct = ru.get("price_pct", [100]*12) or [100]*12
    if len(price_pct) < 12:
        price_pct = list(price_pct) + [price_pct[-1]]*(12-len(price_pct))
    price_year1_mult = (sum(float(x) for x in price_pct[:12]) / 12.0) / 100.0

    def _depreciation_schedule(fin: Dict[str, Any], horizon: int) -> Dict[int, float]:
        dep = {y: 0.0 for y in range(0, horizon+1)}
        for it in fin.get("capex_items", []) or []:
            amt = fnum(it.get("amount", 0.0))
            years_it = max(1, int(fnum(it.get("depr_years", 10))))
            annual = amt / years_it
            for y in range(0, min(horizon, years_it)):
                dep[y] += annual
        return dep
    depreciation = _depreciation_schedule(fin, horizon)

    annuals = []
    for y in years:
        capex_spend = 0.0
        for off, val in capex_curve.items():
            if y == max(0, off):
                capex_spend += val
        opex_y = base_opex * ((1.0 + esc) ** y)

        if price > 0 and tpy > 0:
            if y == 0:
                revenue_y = price * tpy * price_year1_mult
            else:
                revenue_y = price * tpy * ((1.0 + esc) ** y)
        else:
            revenue_y = 0.0

        dep_y = depreciation.get(y, 0.0) if fin.get("include_depreciation", True) else 0.0
        ebit_y = revenue_y - opex_y - dep_y
        tax_y = max(0.0, ebit_y * tax_rate)
        ocf_y = (revenue_y - opex_y) - tax_y + dep_y
        fcf_y = ocf_y - capex_spend
        pv = fcf_y / ((1.0 + disc) ** y)
        annuals.append({"Year": y,"CAPEX": -capex_spend,"Revenue": revenue_y,"OPEX": -opex_y,"Depreciation": -dep_y,"Tax": -tax_y,"OCF": ocf_y,"FCF": fcf_y,"PV_FCF": pv})

    df = pd.DataFrame(annuals)
    npv = df["PV_FCF"].sum()

    irr = None
    if price > 0 and df["FCF"].abs().sum() > 0:
        def npv_rate(r):
            return sum(df.loc[i, "FCF"] / ((1+r)**int(df.loc[i,"Year"])) for i in df.index)
        try:
            low, high = -0.9, 1.0
            for _ in range(80):
                mid = (low + high)/2
                val = npv_rate(mid)
                if abs(val) < 1e-7: break
                if val > 0: low = mid
                else: high = mid
            irr = (low + high)/2
        except Exception:
            irr = None

    df["Cum_FCF"] = df["FCF"].cumsum()
    payback_year = None
    for _, row in df.iterrows():
        if row["Cum_FCF"] >= 0:
            payback_year = int(row["Year"])
            break

    y0_capex = 0.0
    curve = capex_spend_by_year(fin)
    for off, val in curve.items():
        if max(0, off) == 0:
            y0_capex += val

    peak_opex = float((-df["OPEX"]).max()) if not df.empty else 0.0
    peak_revenue = float((df["Revenue"]).max()) if not df.empty else 0.0

    return {"currency": cur, "years_df": df, "npv": npv, "irr": irr, "tpy": tpy, "price": price,
            "payback_year": payback_year, "year0_capex": y0_capex, "peak_opex": peak_opex, "peak_revenue": peak_revenue}
