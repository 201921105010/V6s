from views.common import *
from views.components import render_archive_preview, render_file_manager, render_module_logs


def render_log_viewer():
    c_back, c_title = st.columns([1.5, 8.5])
    with c_back: st.button("⬅️ 返回", on_click=go_home, use_container_width=True)
    with c_title: st.header("📜 日志")
    try:
        with get_engine().connect() as conn:
            df = pd.read_sql("SELECT * FROM transaction_log ", conn)
        st.dataframe(df, use_container_width=True)
    except: st.info("暂无日志")
