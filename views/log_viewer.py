<<<<<<< HEAD
import streamlit as st

from core.navigation import go_home
from crud.logs import get_transaction_logs
=======
from views.common import *
>>>>>>> 88b8b5966418ed53f8a893e327b91727f9c01707
from views.components import render_archive_preview, render_file_manager, render_module_logs


def render_log_viewer():
    c_back, c_title = st.columns([1.5, 8.5])
    with c_back: st.button("⬅️ 返回", on_click=go_home, use_container_width=True)
    with c_title: st.header("📜 日志")
<<<<<<< HEAD
    df = get_transaction_logs()
    if df.empty:
        st.info("暂无日志")
    else:
        st.dataframe(df, use_container_width=True)
=======
    try:
        with get_engine().connect() as conn:
            df = pd.read_sql("SELECT * FROM transaction_log ", conn)
        st.dataframe(df, use_container_width=True)
    except: st.info("暂无日志")
>>>>>>> 88b8b5966418ed53f8a893e327b91727f9c01707
