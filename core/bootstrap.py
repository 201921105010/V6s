from datetime import datetime

import streamlit as st

from config import ensure_storage_dirs
from core.auth import init_session_state
from core.file_manager import clean_expired_contracts
from database import init_mysql_tables
from views.styles import apply_global_styles, configure_page


def initialize_app() -> None:
    """运行所有应用级初始化逻辑。"""
    configure_page()
    apply_global_styles()
    ensure_storage_dirs()
    init_session_state()
    _initialize_database_once()
    _cleanup_contracts_once_per_session()



def _initialize_database_once() -> None:
    if st.session_state.get('db_initialized'):
        return

    try:
        init_mysql_tables()
        st.session_state.db_initialized = True
    except Exception as init_err:
        st.error(f"❌ 数据库初始化失败，请检查 MySQL 连接配置：{init_err}")
        st.stop()



def _cleanup_contracts_once_per_session() -> None:
    if st.session_state.get('last_cleanup'):
        return

    clean_expired_contracts()
    st.session_state.last_cleanup = datetime.now().strftime("%Y-%m-%d")
