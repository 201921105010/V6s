from datetime import datetime
import uuid

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from crud.inventory import get_data, save_data
from crud.logs import append_log
from database import get_engine


ORDER_COLS = ["订单号", "客户名", "代理商", "需求机型", "需求数量", "下单时间", "备注", "包装选项", "发货时间", "指定批次/来源", "status", "delete_reason"]


def get_orders():
    try:
        with get_engine().connect() as conn:
            df = pd.read_sql("SELECT * FROM sales_orders", conn)
        for col in ORDER_COLS:
            if col not in df.columns:
                df[col] = ""
        df = df.fillna("")
        mask = (df['status'] == "") | (df['status'].isna())
        if mask.any():
            df.loc[mask, 'status'] = "active"
        return df
    except (OperationalError, Exception):
        return pd.DataFrame(columns=ORDER_COLS)


def save_orders(df):
    try:
        df = df.fillna("")
        for col in ORDER_COLS:
            if col not in df.columns:
                df[col] = ""
        with get_engine().begin() as conn:
            conn.execute(text("DELETE FROM sales_orders"))
            if not df.empty:
                df[ORDER_COLS].to_sql('sales_orders', conn, if_exists='append', index=False, method='multi', chunksize=500)
    except (OperationalError, Exception) as e:
        raise RuntimeError(f"订单保存失败: {e}") from e


def create_sales_order(customer, agent, model_data, note, pack_option="", delivery_time="", source_batch=""):
    odf = get_orders()
    order_id = f"SO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
    final_model_str = ""
    total_qty = 0

    if isinstance(model_data, dict):
        parts = []
        for m, q in model_data.items():
            parts.append(f"{m}:{q}")
            total_qty += int(q)
        final_model_str = ";".join(parts)
    else:
        final_model_str = str(model_data)

    new_row = {
        "订单号": order_id,
        "客户名": customer,
        "代理商": agent,
        "需求机型": final_model_str,
        "需求数量": str(total_qty) if isinstance(model_data, dict) else "0",
        "下单时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "备注": note,
        "包装选项": pack_option,
        "发货时间": delivery_time,
        "指定批次/来源": source_batch,
    }
    odf = pd.concat([odf, pd.DataFrame([new_row])], ignore_index=True)
    save_orders(odf)
    return order_id


def allocate_inventory(order_id, customer, agent, selected_sns):
    df = get_data()
    orders = get_orders()
    order_note = ""
    target_order = orders[orders['订单号'] == order_id]
    if not target_order.empty:
        order_note = str(target_order.iloc[0]['备注'])

    current_status_df = df[df['流水号'].isin(selected_sns)]
    pending_inbound_sns = current_status_df[current_status_df['状态'] == '待入库']['流水号'].tolist()
    if pending_inbound_sns:
        append_log("直接配货-自动入库", pending_inbound_sns)

    mask = df['流水号'].isin(selected_sns)
    df.loc[mask, '状态'] = '待发货'
    df.loc[mask, '占用订单号'] = order_id
    df.loc[mask, '客户'] = customer
    df.loc[mask, '代理商'] = agent
    df.loc[mask, '订单备注'] = order_note
    df.loc[mask, '更新时间'] = datetime.now().strftime("%Y-%m-%d %H:%M")

    save_data(df)
    append_log(f"配货锁定-{order_id}", selected_sns)


def revert_to_inbound(selected_sns, reason="撤回操作"):
    df = get_data()
    mask = df['流水号'].isin(selected_sns)
    df.loc[mask, '状态'] = '待入库'
    df.loc[mask, '占用订单号'] = ""
    df.loc[mask, '客户'] = ""
    df.loc[mask, '代理商'] = ""
    df.loc[mask, '订单备注'] = ""
    df.loc[mask, '更新时间'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_data(df)
    append_log(f"{reason}-退回待入库", selected_sns)


def update_sales_order(order_id, new_data, force_unbind=False):
    df = get_data()
    mask_alloc = (df['占用订单号'] == order_id) & (df['状态'] != '已出库')
    sns_to_unbind = df.loc[mask_alloc, '流水号'].tolist()
    has_allocation = len(sns_to_unbind) > 0

    if has_allocation:
        if force_unbind:
            revert_to_inbound(sns_to_unbind, reason=f"订单修改-自动解绑-{order_id}")
        else:
            return False, f"⚠️ 警告：该订单已锁定 {len(sns_to_unbind)} 台库存。修改将导致配货失效，是否继续？"

    orders = get_orders()
    idx = orders[orders['订单号'] == order_id].index
    if not idx.empty:
        for col, val in new_data.items():
            if col in orders.columns:
                orders.loc[idx, col] = str(val)
        save_orders(orders)
        msg_extra = f"已解绑 {len(sns_to_unbind)} 台关联机器。" if (has_allocation and force_unbind) else ""
        return True, f"订单更新成功！{msg_extra}"
    return False, "订单未找到"
