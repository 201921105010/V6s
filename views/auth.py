import time

import streamlit as st

from core.auth import register_user, verify_login
from core.permissions import get_role_permissions

def login_form():
    """显示登录表单 (支持注册)"""
    # 使用空容器居中显示
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔐 成品管理系统</h2>", unsafe_allow_html=True)
        st.write("")
        
        tab_login, tab_register = st.tabs(["🔑 登录", "📝 注册新账号"])
        
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("账号")
                password = st.text_input("密码", type="password")
                submitted = st.form_submit_button("登录", use_container_width=True)
                
                if submitted:
                    ok, msg, user_row = verify_login(username, password)
                    if ok:
                        st.session_state.current_user = username
                        st.session_state.role = user_row["role"]
                        st.session_state.operator_name = user_row["name"]
                        st.session_state.is_admin = (user_row["role"] == "Admin")
                        
                        # --- Load Permissions ---
                        perms = get_role_permissions(user_row["role"])
                        st.session_state.permissions = perms
                        
                        st.success(f"{msg}！欢迎 {user_row['name']}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(msg)

        with tab_register:
            with st.form("register_form"):
                r_user = st.text_input("设置账号 (用户名)", help="登录用的唯一ID")
                r_pass = st.text_input("设置密码", type="password")
                r_name = st.text_input("您的姓名 (真实姓名)")
                
                # Role mapping for display
                role_display_map = {"销售员": "Sales", "生产/仓管": "Prod", "老板/管理": "Boss"}
                r_role_display = st.selectbox("申请角色", list(role_display_map.keys()))
                r_role = role_display_map[r_role_display]
                
                reg_submitted = st.form_submit_button("提交注册申请", use_container_width=True)
                
                if reg_submitted:
                    if not r_user or not r_pass or not r_name:
                        st.error("请填写完整信息")
                    else:
                        ok, msg = register_user(r_user, r_pass, r_role, r_name)
                        if ok: st.success(msg)
                        else: st.error(msg)
