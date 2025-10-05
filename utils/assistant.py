
# utils/assistant.py
# Local, no-API help assistant for the Streamlit costing tool.
import re
import textwrap
from typing import Dict, Any, List

# ---- Lightweight knowledge base ----
GUIDE_SECTIONS: List[Dict[str, str]] = [
    {"title": "Quick Start",
     "content": "Open Details page. Fill Project info, choose Currency, set Throughput (t/y). Toggle 'Rubrics to display'. Fill tables: Process model (t/t), Consumables, Utilities, Byproducts, Logistics (Packaging + Transport), Waste, Custom, Additional. Set Scenarios in sidebar and choose Active scenario. Review Summary and Dashboard. Export snapshot if needed."},
    {"title": "Process model — Mass & Energy (BOM)",
     "content": "Use t_per_t (t per t of final product). Columns: name, t_per_t, unit (t/t), unit_cost, cost_unit ({CUR}/t), price_source, taxable, note. Aggregates to 'Formulation' cost."},
    {"title": "Consumables",
     "content": "spec_per_t with units (e.g., kg/t). Provide unit_cost and cost_unit (e.g., {CUR}/kg). Choose price_source from list."},
    {"title": "Utilities (incl. Steam)",
     "content": "intensity_per_t (kWh/t, t/t, m3/t...). tariff_per_unit with tariff_unit (e.g., {CUR}/kWh, {CUR}/t). Steam is included here."},
    {"title": "Byproducts",
     "content": "Enter credit_per_t with unit ({CUR}/t). Credits reduce total cost."},
    {"title": "Logistics",
     "content": "Packaging: units_per_t with unit_cost ({CUR}/unit). Transport: wet_t_per_t, distance_km, tariff_per_tkm ({CUR}/(t*km))."},
    {"title": "Waste, Custom, Additional",
     "content": "Waste: kg_per_t and disposal cost ({CUR}/kg). Custom: basis (per_t / per_year / fixed_project) + map_to_category. Additional: free table for any extra OPEX."},
    {"title": "Ramp-up profiles",
     "content": "12-month % profiles for Utilities, Logistics (Packaging & Transport), Other, and Price. Summary shows stacked area + tables."},
    {"title": "Finance — CAPEX & Pricing",
     "content": "Selling price per t, Horizon (years), Include depreciation (straight-line). CAPEX items (amount, year, depr_years, category). CAPEX spend curve (% at offsets -1, 0, 1). Dashboard computes NPV/IRR/Payback. If price=0, it’s Net Present Cost."},
    {"title": "Scenarios",
     "content": "Each scenario changes costMultiplier, quantityMultiplier, contingencyPctDelta. Pick Active scenario in sidebar. Summary compares Unit/Total cost across scenarios."},
    {"title": "Import/Export",
     "content": "Quick Import in sidebar (CSV/XLSX to a target section). Full Import expander (XLSX with sheets: recipe, materials, utilities, byproducts, packaging, logistics, waste, rubrics, scenarios, capex, rampup). Download XLSX template. Export snapshot creates a workbook with current data."},
]

def _simple_keyword_score(q: str, txt: str) -> int:
    q = q.lower()
    txt = txt.lower()
    score = 0
    for w in re.findall(r"[a-z0-9]+", q):
        if w in txt:
            score += 1
    return score

def _local_search_answer(query: str, currency: str) -> str:
    scored = []
    for sec in GUIDE_SECTIONS:
        body = sec["content"].replace("{CUR}", currency)
        scored.append((_simple_keyword_score(query, sec["title"] + " " + body), sec["title"], body))
    scored.sort(key=lambda x: x[0], reverse=True)
    chunks = []
    for _, title, body in scored[:3]:
        bullets = "\\n- ".join(textwrap.wrap(body, width=110))
        chunks.append(f"**{title}**\\n- {bullets}")
    if not chunks:
        chunks = ["Here’s how to move forward:\\n- Open **Details** → enable needed **Rubrics to display**;\\n- Fill the relevant table(s);\\n- Check **Summary** for totals and **Dashboard** for NPV/IRR;\\n- Use **Import** (sidebar) to load data; **Export snapshot** to share."]
    return "\\n\\n".join(chunks)

def answer(query: str, data: Dict[str, Any]) -> str:
    currency = (data.get("project", {}) or {}).get("currency", "MAD")
    return _local_search_answer(query, currency)

def render_quick_help_sidebar(st, data: Dict[str, Any]) -> None:
    with st.sidebar.expander("🤖 Quick Help", expanded=False):
        st.caption("Ask how to do something in the app. Example: “How do I add a new utility?”")
        q = st.text_input("Question", value="", key="quick_help_q")
        if st.button("Ask", key="quick_help_btn"):
            if q.strip():
                st.markdown(answer(q, data))
            else:
                st.info("Type a question first.")
