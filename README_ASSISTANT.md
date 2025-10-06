
# Assistant Add-on (No API Key)
This adds a local help chatbot and a Quick Help sidebar to your app. No OpenAI API key required.

## Files to copy into your repo
- `utils/assistant.py`
- `pages/4_Help_Chat.py`

## 1) Add a link to the new page (home file)
In `standard_costing_tool_streamlit.py`, add:
```python
st.page_link("pages/4_Help_Chat.py", label="Help & Chat")
```

## 2) Show Quick Help on every page
At the top of each page file (after `data = ensure_state(st)`), add:
```python
from utils.assistant import render_quick_help_sidebar
render_quick_help_sidebar(st, data)
```

Pages to update:
- `standard_costing_tool_streamlit.py` (if it has `data`, otherwise keep only the page link)
- `pages/1_Details.py`
- `pages/2_Summary.py`
- `pages/3_Dashboard.py`

## 3) Deploy
Commit the two new files and the small edits, then redeploy (or Reboot on Streamlit Cloud).
