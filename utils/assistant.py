# utils/assistant.py
# Precise, no-API assistant: intents (recipes) + Glossary + BM25 retrieval + guided mode.
import re
import textwrap
from typing import Dict, Any, List

# ---------- Glossary (definitions) ----------
GLOSSARY: Dict[str, Dict[str, Any]] = {
    "NPV": {
        "aliases": ["net present value"],
        "definition": "The sum of all future Free Cash Flows discounted to today using a discount rate.",
        "formula": "NPV = Σ_t (FCF_t / (1 + r)^t) − Initial CAPEX",
        "example": "If FCF = [−1000, 400, 400, 400] and r = 10%, then NPV ≈ −1000 + 364 + 331 + 301 = −4 (about breakeven).",
        "in_app": "See **Dashboard** KPI cards; discount rate is in **Details → Project (sidebar)**."
    },
    "IRR": {
        "aliases": ["internal rate of return"],
        "definition": "The discount rate r that makes NPV equal to 0.",
        "formula": "Find r such that 0 = Σ_t (FCF_t / (1 + r)^t) − Initial CAPEX",
        "example": "If NPV crosses 0 near 13%, that ~13% is the IRR.",
        "in_app": "See **Dashboard** KPI cards (IRR)."
    },
    "Payback": {
        "aliases": ["payback period", "payback time"],
        "definition": "Years needed until cumulative Free Cash Flow turns positive.",
        "formula": "Smallest t with Σ_i≤t FCF_i ≥ 0",
        "example": "If cumulative FCF becomes positive in Year 3.4, payback ≈ 3.4 years.",
        "in_app": "See **Dashboard** KPI cards (Payback)."
    },
    "CAPEX": {
        "aliases": ["capital expenditure", "capex items"],
        "definition": "Up-front investment to build or expand capacity; depreciated over useful life.",
        "example": "Equipment: 2M; Civil works: 0.5M; Commissioning: 0.1M.",
        "in_app": "Enter in **Details → Finance — CAPEX & Pricing** (amount, year, depr_years, category)."
    },
    "OPEX": {
        "aliases": ["operating cost", "operational expenditure"],
        "definition": "Recurring costs to operate the plant (materials, consumables, utilities, labor, logistics, waste, etc.).",
        "in_app": "All cost rubrics on **Details** roll up to OPEX in **Summary/Dashboard**."
    },
    "Discount rate": {
        "aliases": ["r", "cost of capital", "WACC"],
        "definition": "Rate used to discount future cash flows to present value; reflects risk and money time value.",
        "in_app": "Set in **Details → Project (sidebar)**; used for NPV."
    },
    "Depreciation": {
        "aliases": ["straight-line depreciation"],
        "definition": "Allocation of CAPEX cost over its useful life; non-cash expense that affects tax.",
        "formula": "Annual Depreciation = CAPEX / Depreciation years (straight-line)",
        "in_app": "Toggle **Include depreciation** in **Finance — CAPEX & Pricing**."
    },
    "Working capital": {
        "aliases": ["net working capital", "NWC"],
        "definition": "Capital tied in operations (inventory, receivables minus payables).",
        "in_app": "Not modeled explicitly by default; can be added via **Custom** rubric or CAPEX item if needed."
    },
    "EMV": {
        "aliases": ["expected monetary value", "risk emv"],
        "definition": "Probability-weighted expected cost/benefit of risk events.",
        "formula": "EMV = Σ (Probability × Impact)",
        "in_app": "Add as **Custom** or **Additional production cost** with note 'Risk EMV'."
    },
    "Accuracy band": {
        "aliases": ["estimate class", "feasibility range"],
        "definition": "Indicative error range of the estimate depending on project stage.",
        "example": "Feasibility: −30%/+50%; Design: −20%/+30%; Execution: −10%/+15%; Commissioning: −10%/+10%.",
        "in_app": "Shown on **Summary/Dashboard** as context."
    },
    "Throughput": {
        "aliases": ["tpy", "tons per year", "annual production"],
        "definition": "Annual steady-state production of final product (t/y).",
        "in_app": "Set at the top of **Details**."
    },
    "BOM": {
        "aliases": ["formulation", "process model", "mass & energy"],
        "definition": "Material and energy balance per 1 t of final product (t/t and intensity units).",
        "in_app": "Use **Process model — Mass & Energy** and related rubrics."
    },
    "Unit cost vs cost unit": {
        "aliases": ["unit cost", "cost unit", "currency unit"],
        "definition": "Unit cost is the numeric price; cost unit is the unit label (e.g., MAD/kg, EUR/kWh). Use dropdowns to avoid mistakes.",
        "in_app": "All tables have select lists for **cost_unit**."
    },
    "Price source": {
        "aliases": ["quote type", "benchmark vs firm"],
        "definition": "Origin/quality of the price: Benchmark, Budgetary, Firm, Contract, Estimate.",
        "in_app": "Choose from dropdown in every price table."
    },
    "Ramp-up": {
        "aliases": ["ramp up", "startup curve"],
        "definition": "Month-by-month fraction of steady-state for Y1 costs and price.",
        "in_app": "Edit in **Ramp-up profiles**; see charts & tables in **Summary**."
    }
}

# ---------- Knowledge sections (for “how do I … ?”) ----------
GUIDE_SECTIONS: List[Dict[str, str]] = [
    {"title": "Quick Start",
     "content": "Open Details. Fill Project info, choose Currency, set Throughput (t/y). Toggle 'Rubrics to display'. Fill tables: Process model (t/t), Consumables, Utilities, Byproducts, Logistics (Packaging + Transport), Waste, Custom, Additional. Add Scenarios and choose Active scenario. Check Summary & Dashboard. Export snapshot."},
    {"title": "Process model — Mass & Energy (BOM)",
     "content": "Use t_per_t (t per t product). Columns: name, t_per_t, unit (t/t), unit_cost, cost_unit ({CUR}/t), price_source, taxable, note. Aggregates to 'Formulation' cost."},
    {"title": "Consumables",
     "content": "spec_per_t with unit (e.g., kg/t). Provide unit_cost + cost_unit (e.g., {CUR}/kg). Choose price_source."},
    {"title": "Utilities (incl. Steam)",
     "content": "intensity_per_t (kWh/t, t/t, m3/t...). tariff_per_unit + tariff_unit (e.g., {CUR}/kWh, {CUR}/t). Steam is included here."},
    {"title": "Byproducts / Credits",
     "content": "credit_per_t with unit ({CUR}/t). Credits reduce total cost."},
    {"title": "Logistics → Packaging",
     "content": "units_per_t, unit_cost, cost_unit ({CUR}/unit), price_source."},
    {"title": "Logistics → Transport",
     "content": "wet_t_per_t, distance_km, tariff_per_tkm, cost_unit ({CUR}/(t*km)), price_source."},
    {"title": "Waste",
     "content": "kg_per_t and disposal_cost_per_kg, cost_unit ({CUR}/kg), price_source."},
    {"title": "Custom & Additional production costs",
     "content": "Custom: basis (per_t / per_year / fixed_project), quantity, map_to_category. Additional: free table for extra OPEX."},
    {"title": "Ramp-up profiles (Year 1)",
     "content": "12-month % profiles for Utilities, Logistics (Packaging & Transport), Other, and Price. Summary shows stacked area + tables."},
    {"title": "Finance — CAPEX & Pricing",
     "content": "Selling price per t; Horizon (years); Include depreciation (straight-line). CAPEX items (amount, year, depr_years, category). CAPEX spend curve (% at offsets -1,0,1). Dashboard → NPV/IRR/Payback. If price=0 → Net Present Cost."},
    {"title": "Import / Export",
     "content": "Quick Import (sidebar) CSV/XLSX to a section. Full Import (expander) with sheets: recipe, materials, utilities, byproducts, packaging, logistics, waste, rubrics, scenarios, capex, rampup. Download XLSX template. Export snapshot saves all."},
    {"title": "Scenarios",
     "content": "Each scenario sets costMultiplier, quantityMultiplier, contingencyPctDelta. Pick Active scenario in sidebar. Summary compares Unit/Total cost across scenarios."},
]

# ---------- Intents (precise playbooks) ----------
def _steps_add_utility(cur):
    return [
        "Open **Details — Inputs & Calculations**.",
        "In **Rubrics to display**, switch ON **Utilities (incl. Steam)**.",
        "Go to the **Utilities (incl. Steam)** table → **Add row**.",
        "Fill **name**, **intensity_per_t** (e.g., kWh/t), **tariff_per_unit** and **tariff_unit** (e.g., " + cur + "/kWh).",
        "Pick **price_source**; set **taxable** if applicable.",
        "Totals refresh in **Summary**."
    ]

def _steps_set_price(cur):
    return [
        "Open **Details — Inputs & Calculations**.",
        "Switch ON **Finance — CAPEX & Pricing**.",
        "Set **Selling price per t** (" + cur + "/t).",
        "If Year-1 differs, adjust **Price ramp %** in **Ramp-up profiles**.",
        "Check **Dashboard** for revenue and NPV/IRR."
    ]

def _steps_add_capex(cur):
    return [
        "Open **Details — Inputs & Calculations**.",
        "Switch ON **Finance — CAPEX & Pricing**.",
        "Under **CAPEX items**: set **name**, **amount** (" + cur + "), **year**, **depr_years**, **category**.",
        "Optionally define the **CAPEX spend curve (% at −1, 0, +1)**.",
        "See **Dashboard** for **NPV/IRR/Payback**."
    ]

def _steps_import_quick():
    return [
        "Open **Details — Inputs & Calculations**.",
        "In **sidebar → Quick Import**, choose **Target section**.",
        "Upload CSV/XLSX with matching columns → **Import**.",
        "Validate the table and **Summary** totals."
    ]

def _steps_import_full():
    return [
        "Open **Details — Inputs & Calculations**.",
        "Expand **Full Import (workbook)**.",
        "Click **Download XLSX template**; complete sheets.",
        "Upload workbook → **Import**.",
        "Check each section and **Summary**."
    ]

def _steps_export_snapshot():
    return [
        "Go to **Summary** (or **Dashboard**).",
        "Click **Export snapshot (xlsx)**.",
        "Share the file."
    ]

def _steps_add_scenario():
    return [
        "Open **Details — sidebar → Scenarios**.",
        "Add a row: **id**, **name**, **costMultiplier**, **quantityMultiplier**, **contingencyPctDelta**.",
        "Choose **Active scenario**.",
        "Compare in **Summary → Scenario compare**."
    ]

def _steps_change_currency():
    return [
        "Open **Details — sidebar → Project**.",
        "Set **Currency** (MAD / USD / EUR / GBP).",
        "All **cost_unit** dropdowns & totals align automatically."
    ]

def _steps_toggle_rubric():
    return [
        "Open **Details — Inputs & Calculations**.",
        "Use **Rubrics to display** to show/hide sections.",
        "Hidden sections don’t affect totals."
    ]

def _steps_adjust_rampup():
    return [
        "Open **Details → Ramp-up profiles (Year 1)**.",
        "Edit monthly % for **Utilities**, **Logistics — Packaging**, **Logistics — Transport**, **Other**.",
        "Edit **Price ramp %** if needed.",
        "See charts & tables in **Summary → Ramp-up**."
    ]

def _steps_add_packaging(cur):
    return [
        "Open **Details — Inputs & Calculations**.",
        "Ensure **Logistics** is ON.",
        "In **Logistics → Packaging**: set **name**, **units_per_t**, **unit_cost**, **cost_unit** (" + cur + "/unit), **price_source**.",
        "Totals update in **Summary**."
    ]

def _steps_add_transport(cur):
    return [
        "Open **Details — Inputs & Calculations**.",
        "Ensure **Logistics** is ON.",
        "In **Logistics → Transport**: set **wet_t_per_t**, **distance_km**, **tariff_per_tkm**, **cost_unit** (" + cur + "/(t*km)), **price_source**.",
        "Totals update in **Summary**."
    ]

def _steps_add_waste(cur):
    return [
        "Open **Details — Inputs & Calculations**.",
        "Switch ON **Waste**.",
        "Set **kg_per_t**, **disposal_cost_per_kg**, **cost_unit** (" + cur + "/kg), **price_source**.",
        "Totals reflect in **Summary**."
    ]

def _steps_add_byproduct(cur):
    return [
        "Open **Details — Inputs & Calculations**.",
        "Switch ON **Byproducts / Credits**.",
        "Add **credit_per_t** and **unit** (" + cur + "/t).",
        "Credit reduces **Total** in **Summary**."
    ]

INTENT_RECIPES = {
    "add_utility": _steps_add_utility,
    "set_price": _steps_set_price,
    "add_capex": _steps_add_capex,
    "import_quick": lambda cur: _steps_import_quick(),
    "import_full": lambda cur: _steps_import_full(),
    "export_snapshot": lambda cur: _steps_export_snapshot(),
    "add_scenario": lambda cur: _steps_add_scenario(),
    "change_currency": lambda cur: _steps_change_currency(),
    "toggle_rubric": lambda cur: _steps_toggle_rubric(),
    "adjust_rampup": lambda cur: _steps_adjust_rampup(),
    "add_packaging": _steps_add_packaging,
    "add_transport": _steps_add_transport,
    "add_waste": _steps_add_waste,
    "add_byproduct": _steps_add_byproduct,
}

INTENT_PATTERNS = [
    ("add_utility", r"\b(add|create|new)\b.*\b(utility|utilities|steam|electricity|water|fuel)\b"),
    ("set_price", r"\b(set|enter|change)\b.*\b(price|selling price|sell price)\b"),
    ("add_capex", r"\b(add|enter|record)\b.*\b(capex|capital)\b"),
    ("import_quick", r"\b(import|upload)\b.*\b(csv|xlsx|file)\b"),
    ("import_full", r"\b(full|template)\b.*\b(import)\b"),
    ("export_snapshot", r"\b(export|download)\b.*\b(snapshot|xlsx|file)\b"),
    ("add_scenario", r"\b(add|create)\b.*\b(scenario)\b"),
    ("change_currency", r"\b(change|set)\b.*\b(currency)\b"),
    ("toggle_rubric", r"\b(show|hide|toggle|display)\b.*\b(rubric|section)\b"),
    ("adjust_rampup", r"\b(ramp|ramp-up|ramp up|month)\b"),
    ("add_packaging", r"\b(add|create)\b.*\b(packaging|bag|big bag|sack|pallet)\b"),
    ("add_transport", r"\b(add|create)\b.*\b(transport|logistics|shipping|truck|km)\b"),
    ("add_waste", r"\b(add|create)\b.*\b(waste|disposal)\b"),
    ("add_byproduct", r"\b(add|create)\b.*\b(byproduct|credit)\b"),
]

# ---------- Retrieval (BM25) ----------
try:
    from rank_bm25 import BM25Okapi
    _HAS_BM25 = True
except Exception:
    _HAS_BM25 = False

def _bm25_answer(query: str, currency: str) -> str:
    docs = [(sec["title"] + ". " + sec["content"].replace("{CUR}", currency)) for sec in GUIDE_SECTIONS]
    if not _HAS_BM25:
        return _keyword_answer(query, currency)
    tokenized = [re.findall(r"[a-z0-9]+", d.lower()) for d in docs]
    bm25 = BM25Okapi(tokenized)
    qtok = re.findall(r"[a-z0-9]+", query.lower())
    scores = bm25.get_scores(qtok)
    idxs = sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)[:3]
    bullets = []
    for i in idxs:
        title = GUIDE_SECTIONS[i]["title"]
        body = GUIDE_SECTIONS[i]["content"].replace("{CUR}", currency)
        bullets.append("**" + title + "**\n- " + "\n- ".join(textwrap.wrap(body, width=110)))
    return "\n\n".join(bullets)

def _keyword_answer(query: str, currency: str) -> str:
    scored = []
    for sec in GUIDE_SECTIONS:
        body = sec["content"].replace("{CUR}", currency)
        q = query.lower()
        score = sum(1 for w in re.findall(r"[a-z0-9]+", q) if w in (sec["title"] + " " + body).lower())
        scored.append((score, sec["title"], body))
    scored.sort(key=lambda x: x[0], reverse=True)
    chunks = []
    for _, title, body in scored[:3]:
        chunks.append("**" + title + "**\n- " + "\n- ".join(textwrap.wrap(body, width=110)))
    return "\n\n".join(chunks) if chunks else "Try: enable **Rubrics to display**, fill the relevant table(s), then check **Summary** and **Dashboard**."

# ---------- Glossary match ----------
def _find_glossary_entry(query: str):
    t = query.lower()
    for term, entry in GLOSSARY.items():
        names = [term] + entry.get("aliases", [])
        for n in names:
            pattern = r"\b" + re.escape(n.lower()) + r"\b"
            if re.search(pattern, t):
                return term, entry
    # also if user writes "what is X" without match, try single word last token
    m = re.search(r"(?:what\s+is|define|meaning\s+of)\s+([a-z0-9 \-]+)\??", t)
    if m:
        guess = m.group(1).strip()
        for term, entry in GLOSSARY.items():
            names = [term] + entry.get("aliases", [])
            if any(guess == n.lower() for n in names):
                return term, entry
    return "", None

def _format_glossary_answer(term: str, entry: Dict[str, Any]) -> str:
    parts = [f"**{term}** — {entry.get('definition','')}"]
    if entry.get("formula"):
        parts.append("**Formula:** " + entry["formula"])
    if entry.get("example"):
        parts.append("**Example:** " + entry["example"])
    if entry.get("in_app"):
        parts.append("**In this app:** " + entry["in_app"])
    if entry.get("aliases"):
        parts.append("**Also called:** " + ", ".join(entry["aliases"]))
    return "\n\n".join(parts)

# ---------- Public API ----------
def answer(query: str, data: Dict[str, Any]) -> str:
    currency = (data.get("project", {}) or {}).get("currency", "MAD")

    # 1) Intent recipes (exact steps)
    for name, pattern in INTENT_PATTERNS:
        if re.search(pattern, query.lower()):
            steps = INTENT_RECIPES[name](currency)
            body = _as_numbered(steps)
            details = _bm25_answer(query, currency)
            return body + "\n\n<details><summary>More details</summary>\n\n" + details + "\n\n</details>"

    # 2) Glossary (definitions)
    term, entry = _find_glossary_entry(query)
    if entry:
        return _format_glossary_answer(term, entry)

    # 3) Retrieval-based short help
    details = _bm25_answer(query, currency)
    tips = [
        "Open **Details**; enable needed sections in **Rubrics to display**.",
        "Fill table fields with correct units (t/t, kg/t, kWh/t).",
        "Pick **cost_unit** via dropdown to avoid mistakes.",
        "Use **Scenarios** (sidebar) and select **Active scenario**.",
        "Check **Summary** for totals and **Dashboard** for NPV/IRR."
    ]
    short = _as_numbered(tips[:5])
    return short + "\n\n<details><summary>More details</summary>\n\n" + details + "\n\n</details>"

# ---------- Formatting helpers ----------
def _as_numbered(steps: List[str]) -> str:
    lines = []
    for i, s in enumerate(steps, 1):
        wrapped = textwrap.wrap(s, width=100) or [s]
        lines.append(f"{i}. {wrapped[0]}")
        for cont in wrapped[1:]:
            lines.append("   " + cont)
    return "\n".join(lines)

# ---------- Sidebar widget ----------
def render_quick_help_sidebar(st, data: Dict[str, Any]) -> None:
    with st.sidebar.expander("🤖 Quick Help", expanded=False):
        mode = st.radio("Mode", ["Guided", "Glossary", "Ask a question"], horizontal=True, key="qh_mode")
        if mode == "Guided":
            area = st.selectbox("Area", [
                "Process model — Mass & Energy","Consumables","Utilities (incl. Steam)","Byproducts / Credits",
                "Logistics → Packaging","Logistics → Transport","Waste","Custom","Additional production costs",
                "Finance — CAPEX & Pricing","Scenarios","Import / Export","Ramp-up profiles"
            ], key="qh_area")
            task_map = {
                "Utilities (incl. Steam)": [("Add a utility", "add_utility"), ("Adjust ramp-up for utilities", "adjust_rampup")],
                "Finance — CAPEX & Pricing": [("Set selling price", "set_price"), ("Enter CAPEX items", "add_capex")],
                "Import / Export": [("Quick import a section", "import_quick"), ("Full import with template", "import_full"), ("Export snapshot", "export_snapshot")],
                "Scenarios": [("Add a scenario", "add_scenario"), ("Change currency", "change_currency")],
                "Logistics → Packaging": [("Add packaging", "add_packaging")],
                "Logistics → Transport": [("Add transport tariff", "add_transport")],
                "Waste": [("Add waste item", "add_waste")],
                "Byproducts / Credits": [("Add a byproduct credit", "add_byproduct")],
                "Process model — Mass & Energy": [("Show section (toggle rubric)", "toggle_rubric")],
            }
            tasks = task_map.get(area, [("Show section (toggle rubric)", "toggle_rubric")])
            label = st.selectbox("Task", [t[0] for t in tasks], key="qh_task")
            code = dict(tasks)[label]
            if st.button("Show steps", key="qh_go"):
                st.markdown(answer(label, data))
        elif mode == "Glossary":
            term = st.selectbox("Term", sorted(GLOSSARY.keys()), key="qh_term")
            if st.button("Define", key="qh_define"):
                st.markdown(_format_glossary_answer(term, GLOSSARY[term]))
        else:
            q = st.text_input("Ask anything about the app", value="", key="qh_q")
            if st.button("Ask", key="qh_btn"):
                st.markdown(answer(q, data))
