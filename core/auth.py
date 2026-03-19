import time

import streamlit as st
from sqlalchemy.exc import IntegrityError, OperationalError

from crud.users import create_pending_user, get_all_users, user_exists


def init_session_state():
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
        st.session_state.role = None
        st.session_state.operator_name = ''
        st.session_state.is_admin = False
        st.session_state.page = 'home'
        st.session_state.current_batch = ''
        st.session_state.permissions = []


def register_user(username, password, role, name):
    try:
        if user_exists(username):
            return False, "用户名已存在"
    except (OperationalError, Exception) as e:
        return False, f"系统错误: {e}"

    try:
        create_pending_user(username, password, role, name)
        return True, "注册成功，请等待管理员审核"
    except (IntegrityError, OperationalError, Exception) as e:
        return False, f"系统错误，保存失败: {e}"


def verify_login(username, password):
    df = get_all_users()
    user = df[df['username'] == username]

    if user.empty:
        return False, "用户不存在", None

    user_row = user.iloc[0]
    if str(user_row['password']) != str(password):
        return False, "密码错误", None

    status = str(user_row['status'])
    if status == 'active':
        return True, "登录成功", user_row
    if status == 'pending':
        return False, "账户待审核，请联系管理员", None
    if status == 'rejected':
        return False, "账户审核未通过", None
    return False, f"账户状态异常: {status}", None
