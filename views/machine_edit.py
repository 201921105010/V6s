import time
from datetime import datetime

import streamlit as st

from config import CUSTOM_MODEL_ORDER
from core.navigation import go_home
from core.permissions import check_access
from crud.inventory import get_data, save_data
from utils.formatters import get_model_rank


def render_machine_edit():
    check_access('MACHINE_EDIT')
    user_perms = st.session_state.get('permissions', [])
    can_edit_model = (st.session_state.role == "Admin") or ("MACHINE_EDIT_MODEL" in user_perms)
    c_back, c_title = st.columns([2, 8])
    with c_back: st.button("⬅️ 返回", on_click=go_home, use_container_width=True)
    with c_title: st.header("🛠️ 机台信息编辑")

    with st.expander("🔎 筛选条件", expanded=True):
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1: f_sn = st.text_input("流水号 (包含)")
        with c_f2: f_order = st.text_input("订单号 (包含)")
        with c_f3: f_date_range = st.date_input("更新时间范围", value=[])

    df = get_data()
    edit_df = df[df['状态'] != '已出库'].copy()
    all_models = sorted(list(set(CUSTOM_MODEL_ORDER).union(set(df['机型'].dropna().astype(str).tolist()))), key=get_model_rank)

    if f_sn: edit_df = edit_df[edit_df['流水号'].str.contains(f_sn, case=False, na=False)]
    if f_order: edit_df = edit_df[edit_df['占用订单号'].str.contains(f_order, case=False, na=False)]

    if not edit_df.empty:
        # 按机型排序
        edit_df['__rank'] = edit_df['机型'].apply(get_model_rank)
        edit_df = edit_df.sort_values(by=['__rank', '批次号'], ascending=[True, False])
        
        edit_df.insert(0, "✅ 选择", False)
        
        from crud.inventory import get_warehouse_layout
        layout_resp = get_warehouse_layout("default")
        slots_list = layout_resp.get("layout_json", {}).get("slots", [])
        slot_options = [s.get("code") for s in slots_list if s.get("code")]
        status_options = ["待入库", "已入库", "库存中", "已出库", "已退回"]
        
        edited_res = st.data_editor(
            edit_df[['✅ 选择', '流水号', '机型', '状态', 'Location_Code', '占用订单号', '机台备注/配置', '更新时间']],
            hide_index=True,
            use_container_width=True,
            key="machine_edit_editor",
            column_config={
                "机型": st.column_config.SelectboxColumn("机型", options=all_models, required=True),
                "状态": st.column_config.SelectboxColumn("状态", options=status_options),
                "Location_Code": st.column_config.SelectboxColumn("库位", options=[""] + slot_options),
            },
            disabled=[] if can_edit_model else ["机型"],
        )
        selected_rows = edited_res[edited_res['✅ 选择'] == True]
        
        if not selected_rows.empty:
            st.divider()
            with st.form("batch_edit_form"):
                if can_edit_model:
                    new_model = st.selectbox("新的机型 (可选)", ["(不修改)"] + all_models)
                
                c_s1, c_s2 = st.columns(2)
                with c_s1:
                    new_status = st.selectbox("新的状态 (可选)", ["(不修改)"] + status_options)
                with c_s2:
                    new_slot = st.selectbox("新的库位 (可选)", ["(不修改)", "(清空)"] + slot_options)
                    
                new_note = st.text_area("新的机台备注/配置 (Max 500字)", max_chars=500)
                c_q1, c_q2 = st.columns(2)
                with c_q1:
                    opt_xs_auto = st.checkbox("XS改X手自一体")
                with c_q2:
                    opt_back_cond = st.checkbox("后导电")
                if st.form_submit_button("💾 批量保存修改", type="primary"):
                    sns_val = selected_rows['流水号'].tolist()
                    if can_edit_model and new_model != "(不修改)":
                        df.loc[df['流水号'].isin(sns_val), '机型'] = new_model
                        
                    if new_status != "(不修改)":
                        if new_slot != "(不修改)" and new_slot != "(清空)" and new_status in ["已入库", "库存中"]:
                            df.loc[df['流水号'].isin(sns_val), '状态'] = f"{new_status}（{new_slot}）"
                        else:
                            df.loc[df['流水号'].isin(sns_val), '状态'] = new_status
                            
                    if new_slot != "(不修改)":
                        if new_slot == "(清空)":
                            df.loc[df['流水号'].isin(sns_val), 'Location_Code'] = ""
                        else:
                            df.loc[df['流水号'].isin(sns_val), 'Location_Code'] = new_slot
                            # 如果只改了库位没改状态，且状态是库存中，需要同步更新状态文本
                            if new_status == "(不修改)":
                                mask = df['流水号'].isin(sns_val) & df['状态'].str.contains("库存中", na=False)
                                df.loc[mask, '状态'] = f"库存中（{new_slot}）"
                                
                    note_parts = [new_note.strip()] if str(new_note).strip() else []
                    if opt_xs_auto:
                        note_parts.append("XS改X手自一体")
                    if opt_back_cond:
                        note_parts.append("后导电")
                    df.loc[df['流水号'].isin(sns_val), '机台备注/配置'] = "；".join(note_parts)
                    df.loc[df['流水号'].isin(sns_val), '更新时间'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    save_data(df)
                    st.success(f"已更新 {len(sns_val)} 台机器！"); time.sleep(1); st.rerun()
    else: st.info("无数据")

    # --- 📂 机台档案 (Machine Archive) ---
