from datetime import datetime

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from database import get_engine


INVENTORY_COLS = ["批次号", "机型", "流水号", "状态", "预计入库时间", "更新时间", "占用订单号", "客户", "代理商", "订单备注", "机台备注/配置", "Location_Code"]
IMPORT_COLS = ["流水号", "批次号", "机型", "状态", "预计入库时间", "机台备注/配置"]


def get_data():
    try:
        with get_engine().connect() as conn:
            df = pd.read_sql("SELECT * FROM finished_goods_data", conn)
        if df.empty:
            return pd.DataFrame(columns=INVENTORY_COLS)
        df = df.fillna("")
        for col in INVENTORY_COLS:
            if col not in df.columns:
                df[col] = ""
        if '备注' in df.columns and '订单备注' not in df.columns:
            df.rename(columns={'备注': '订单备注'}, inplace=True)
        try:
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        except Exception:
            pass
        return df
    except (OperationalError, Exception) as e:
        raise RuntimeError(f"数据读取失败: {e}") from e


def save_data(df):
    try:
        df = df.drop_duplicates(subset=['流水号'], keep='last')
        df = df.copy()
        for col in INVENTORY_COLS:
            if col not in df.columns:
                df[col] = ""
        for dt_col in ["预计入库时间", "更新时间"]:
            df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
        df["占用订单号"] = df["占用订单号"].apply(lambda v: None if str(v).strip() == "" else str(v).strip())
        fill_cols = [c for c in INVENTORY_COLS if c not in ["预计入库时间", "更新时间", "占用订单号"]]
        for col in fill_cols:
            df[col] = df[col].fillna("")
        with get_engine().begin() as conn:
            result = conn.execute(text("SHOW COLUMNS FROM finished_goods_data LIKE 'Location_Code'"))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE finished_goods_data ADD COLUMN `Location_Code` VARCHAR(100) DEFAULT ''"))
            conn.execute(text("DELETE FROM finished_goods_data"))
            if not df.empty:
                df[INVENTORY_COLS].to_sql('finished_goods_data', conn, if_exists='append', index=False, method='multi', chunksize=500)
    except (OperationalError, Exception) as e:
        raise RuntimeError(f"保存失败: {e}") from e


def archive_shipped_data(df_shipped):
    try:
        current_month = datetime.now().strftime("%Y_%m")
        df_shipped = df_shipped.copy()
        df_shipped['archive_month'] = current_month
        for dt_col in ["预计入库时间", "更新时间"]:
            if dt_col in df_shipped.columns:
                df_shipped[dt_col] = pd.to_datetime(df_shipped[dt_col], errors="coerce")
        df_shipped.fillna("").to_sql('shipping_history', get_engine(), if_exists='append', index=False, method='multi', chunksize=500)
    except (OperationalError, Exception) as e:
        print(f"archive_shipped_data error: {e}")


def get_import_staging():
    try:
        with get_engine().connect() as conn:
            df = pd.read_sql("SELECT * FROM plan_import", conn)
        return df.fillna("")
    except (OperationalError, Exception) as e:
        raise RuntimeError(f"读取待入库数据失败: {e}") from e


def save_import_staging(df):
    try:
        df = df.copy()
        if "预计入库时间" in df.columns:
            df["预计入库时间"] = pd.to_datetime(df["预计入库时间"], errors="coerce")
        with get_engine().begin() as conn:
            conn.execute(text("DELETE FROM plan_import"))
            if not df.empty:
                df.to_sql('plan_import', conn, if_exists='append', index=False, method='multi')
    except (OperationalError, Exception) as e:
        raise RuntimeError(f"保存待入库数据失败: {e}") from e


def append_import_staging(df):
    if df is None or df.empty:
        return 0
    try:
        df = df.copy()
        df["流水号"] = df["流水号"].astype(str).str.strip()
        if "预计入库时间" in df.columns:
            df["预计入库时间"] = pd.to_datetime(df["预计入库时间"], errors="coerce")
        df = df[df["流水号"] != ""]
        if df.empty:
            return 0
        df = df.drop_duplicates(subset=["流水号"], keep="last")
        with get_engine().begin() as conn:
            existing_df = pd.read_sql("SELECT 流水号 FROM plan_import", conn)
            existing_sns = set(existing_df["流水号"].astype(str).str.strip().tolist()) if not existing_df.empty else set()
            df_to_append = df[~df["流水号"].isin(existing_sns)].copy()
            if df_to_append.empty:
                return 0
            df_to_append.to_sql('plan_import', conn, if_exists='append', index=False, method='multi')
            return len(df_to_append)
    except (OperationalError, Exception) as e:
        raise RuntimeError(f"追加待入库数据失败: {e}") from e


def clear_import_staging():
    try:
        with get_engine().begin() as conn:
            conn.execute(text("DELETE FROM plan_import"))
    except (OperationalError, Exception) as e:
        raise RuntimeError(f"清空待入库数据失败: {e}") from e
