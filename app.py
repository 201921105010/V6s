import streamlit as st

<<<<<<< HEAD
from core.bootstrap import initialize_app
from views.auth import login_form
from views.router import render_current_page
from views.sidebar import render_sidebar

initialize_app()
=======
from config import ensure_storage_dirs
from core.auth import init_session_state
from core.file_manager import clean_expired_contracts
from database import init_mysql_tables
from views.auth import login_form
from views.boss_planning import render_boss_planning
from views.home import render_home
from views.inbound import render_inbound
from views.log_viewer import render_log_viewer
from views.machine_archive import render_machine_archive
from views.machine_edit import render_machine_edit
from views.production import render_production
from views.query import render_query
from views.sales_alloc import render_sales_alloc
from views.sales_create import render_sales_create
from views.ship_confirm import render_ship_confirm
from views.sidebar import render_sidebar
from views.styles import apply_global_styles, configure_page
from views.user_management import render_user_management


configure_page()
apply_global_styles()
ensure_storage_dirs()
init_session_state()

if 'db_initialized' not in st.session_state:
    try:
        init_mysql_tables()
        st.session_state.db_initialized = True
    except Exception as init_err:
        st.error(f"❌ 数据库初始化失败，请检查 MySQL 连接配置：{init_err}")
        st.stop()

if 'last_cleanup' not in st.session_state:
    clean_expired_contracts()
    from datetime import datetime
    st.session_state.last_cleanup = datetime.now().strftime("%Y-%m-%d")
>>>>>>> 88b8b5966418ed53f8a893e327b91727f9c01707

if st.session_state.current_user is None:
    login_form()
    st.stop()

render_sidebar()
<<<<<<< HEAD
render_current_page(st.session_state.page)
=======

ROUTES = {
    'home': render_home,
    'user_management': render_user_management,
    'boss_planning': render_boss_planning,
    'production': render_production,
    'machine_edit': render_machine_edit,
    'machine_archive': render_machine_archive,
    'sales_create': render_sales_create,
    'sales_alloc': render_sales_alloc,
    'ship_confirm': render_ship_confirm,
    'inbound': render_inbound,
    'query': render_query,
    'log_viewer': render_log_viewer,
}

render = ROUTES.get(st.session_state.page, render_home)
render()
>>>>>>> 88b8b5966418ed53f8a893e327b91727f9c01707
