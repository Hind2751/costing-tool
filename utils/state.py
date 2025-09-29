import copy
from .costing_core import DEFAULT_STATE, STAGE_PROFILE

def ensure_state(st):
    if "data" not in st.session_state:
        st.session_state["data"] = copy.deepcopy(DEFAULT_STATE)
    return st.session_state["data"]

def stage_sections(stage: str):
    prof = STAGE_PROFILE.get(stage, STAGE_PROFILE["Feasibility"])
    return prof.get("sections", {})
