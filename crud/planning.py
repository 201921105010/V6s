from datetime import datetime

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from database import get_engine


def get_planning_records():
    try:
        with get_engine().connect() as conn:
            df = pd.read_sql("SELECT order_id, model, plan_info, updated_at FROM planning_records", conn)
        return df.fillna("")
    except (OperationalError, Exception):
        return pd.DataFrame(columns=["order_id", "model", "plan_info", "updated_at"])


def save_planning_record(order_id, model, plan_info):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with get_engine().begin() as conn:
            result = conn.execute(
                text("SELECT 1 FROM planning_records WHERE order_id=:oid AND model=:m"),
                {"oid": str(order_id), "m": str(model)}
            )
            if result.fetchone():
                conn.execute(
                    text("UPDATE planning_records SET plan_info=:pi, updated_at=:ua WHERE order_id=:oid AND model=:m"),
                    {"pi": str(plan_info), "ua": current_time, "oid": str(order_id), "m": str(model)}
                )
            else:
                conn.execute(
                    text("INSERT INTO planning_records (order_id, model, plan_info, updated_at) VALUES (:oid, :m, :pi, :ua)"),
                    {"oid": str(order_id), "m": str(model), "pi": str(plan_info), "ua": current_time}
                )
    except (IntegrityError, OperationalError, Exception) as e:
        print(f"Error saving planning record: {e}")
        raise


def get_factory_plan():
    cols = ["合同号", "机型", "排产数量", "要求交期", "状态", "备注", "客户名", "代理商", "指定批次/来源", "订单号"]
    try:
        with get_engine().connect() as conn:
            df = pd.read_sql("SELECT * FROM factory_plan", conn)
        for col in cols:
            if col not in df.columns:
                df[col] = ""
        return df.fillna("").drop(columns=['id'], errors='ignore')
    except (OperationalError, Exception):
        return pd.DataFrame(columns=cols)


def save_factory_plan(df):
    cols = ["合同号", "机型", "排产数量", "要求交期", "状态", "备注", "客户名", "代理商", "指定批次/来源", "订单号"]
    try:
        df = df.fillna("")
        for col in cols:
            if col not in df.columns:
                df[col] = ""
        with get_engine().begin() as conn:
            conn.execute(text("DELETE FROM factory_plan"))
            if not df.empty:
                df[cols].to_sql('factory_plan', conn, if_exists='append', index=False, method='multi', chunksize=500)
    except (OperationalError, Exception) as e:
        raise RuntimeError(f"排产计划保存失败: {e}") from e
