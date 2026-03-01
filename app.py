import streamlit as st

from engine.tarification import tarify
from ui.upload_page import render_sidebar, render_upload_tab
from ui.results_page import render_summary_tab, render_detail_tab

st.set_page_config(page_title="CDR Тарификация", layout="wide")
st.title("CDR Тарификация")

render_sidebar()

# Run tarification if requested
if st.session_state.get("run_tarification"):
    st.session_state["run_tarification"] = False

    cdr_records = st.session_state["parsed_cdr"]
    tariffs = st.session_state["parsed_tariffs"]
    subscribers = st.session_state["subscribers"]

    progress_bar = st.progress(0)
    status_text = st.empty()

    def on_progress(current: int, total: int):
        if total > 0:
            progress_bar.progress(current / total)
            status_text.text(f"Обработка записи {current} / {total}")

    results = tarify(cdr_records, tariffs, subscribers, progress_callback=on_progress)
    st.session_state["results"] = results

    progress_bar.empty()
    status_text.empty()
    st.success(f"Тарификация завершена: {len(results)} записей обработано")

# Tabs
tab_upload, tab_summary, tab_detail = st.tabs(["Загрузка", "Итоги по абонентам", "Детализация звонков"])

with tab_upload:
    render_upload_tab()

with tab_summary:
    render_summary_tab()

with tab_detail:
    render_detail_tab()
