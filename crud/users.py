from datetime import datetime

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from database import get_engine


def init_users_csv():
    """兼容入口：MySQL 版本中由 init_mysql_tables() 统一处理，此函数保留以避免调用报错"""
    pass


def get_all_users():
    try:
        with get_engine().connect() as conn:
            df = pd.read_sql("SELECT username, password, role, name, status, register_time, audit_time, auditor FROM users", conn)
        return df.fillna("")
    except (OperationalError, Exception) as e:
        print(f"get_all_users error: {e}")
        return pd.DataFrame(columns=["username", "password", "role", "name", "status", "register_time", "audit_time", "auditor"])


def save_all_users(df):
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM users"))
            if not df.empty:
                df.fillna("").to_sql('users', conn, if_exists='append', index=False, method='multi')
        return True
    except (OperationalError, Exception) as e:
        print(f"save_all_users error: {e}")
        return False


def create_pending_user(username, password, role, name):
    new_row = {
        "username": username,
        "password": password,
        "role": role,
        "name": name,
        "status": "pending",
        "register_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "audit_time": "",
        "auditor": "",
    }
    pd.DataFrame([new_row]).to_sql('users', get_engine(), if_exists='append', index=False, method='multi')
    return new_row


def user_exists(username):
    with get_engine().connect() as conn:
        result = conn.execute(text("SELECT username FROM users WHERE username=:u"), {"u": username})
        return result.fetchone() is not None
