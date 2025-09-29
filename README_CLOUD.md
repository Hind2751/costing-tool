# Streamlit Community Cloud — Quick Deploy

1) Create a new GitHub repo and upload all files from this folder.
2) On https://share.streamlit.io, click "New app" and select the repo.
3) Main file path: `standard_costing_tool_streamlit.py`
4) Deploy.

Troubleshooting:
- If the app can't find pages, ensure the `pages/` and `utils/` folders are at the repo root.
- If a Python package is missing, add it to `requirements.txt` and redeploy.
- Large XLSX imports may hit upload size limits on free tiers — split sheets if needed.
