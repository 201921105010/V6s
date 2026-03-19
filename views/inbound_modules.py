import time
from datetime import datetime

import pandas as pd
import streamlit as st

from config import MACHINE_ARCHIVE_ABS_DIR
from crud.inventory import append_import_staging, get_data, get_import_staging, save_data, save_import_staging
from crud.logs import append_log
from utils.formatters import get_model_rank
from utils.parsers import build_import_payload, diff_tracking_vs_inventory, execute_import_transaction_payload, parse_tracking_xls, should_reset_page_selection

def check_prod_admin_permission():
    if st.session_state.role not in ['Admin', 'Prod']:
        st.error("🚫 权限不足！仅限管理员 (Admin) 或 生产/仓管 (Prod) 角色访问。")
        st.stop()

def render_tracking_import_module():
    """
    模块二：跟踪单流水号导入
    - 权限控制：仅 Prod/Admin
    - 功能：上传 -> PLAN_IMPORT -> 编辑 -> 确认 -> 写入库存
    """
    check_prod_admin_permission()
    
    st.markdown("### 📋 跟踪单流水号导入模块")
    
    # --- 1. 上传与解析 ---
    with st.expander("📤 上传新跟踪单 (Upload)", expanded=False):
        uploaded = st.file_uploader("选择跟踪单文件 (.xls / .xlsx)", type=["xls", "xlsx"], key="tracking_mod_uploader")
        if uploaded:
            if st.button("🔍 解析并追加到待入库清单", type="primary"):
                with st.spinner("正在解析..."):
                    code, msg, parsed_df = parse_tracking_xls(uploaded)
                    if code == 1:
                        # Diff check logic
                        diff_df = diff_tracking_vs_inventory(parsed_df)
                        
                        if not diff_df.empty:
                            # Append to DB Staging
                            try:
                                append_import_staging(diff_df)
                                st.success(f"✅ 解析成功！已追加 {len(diff_df)} 条记录到待入库清单。")
                                time.sleep(1); st.rerun()
                            except Exception as e:
                                st.error(f"写入待入库清单失败: {e}")
                        else:
                            st.warning("所有解析到的流水号均已在库存中，无需导入。")
                    else:
                        st.error(msg)

    # --- 2. 待入库数据表格展示与编辑 ---
    st.markdown("#### 📝 待入库数据审核 (DB Staging)")
    
    plan_df = get_import_staging().copy()
    
    if plan_df.empty:
        st.info("待入库清单为空，请先上传跟踪单或手动添加。")
    else:
        st.markdown(
            """
            <style>
            div[data-testid="stDataEditor"] table thead tr th:first-child,
            div[data-testid="stDataEditor"] table tbody tr td:first-child {
                width: 40px !important;
                min-width: 40px !important;
                max-width: 40px !important;
                text-align: center !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        plan_df["流水号"] = plan_df["流水号"].astype(str).str.strip()
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 1, 1, 2])
        with filter_col1:
            filter_keyword = st.text_input("筛选关键字", value="", key="plan_import_filter_keyword")
        with filter_col2:
            sort_col = st.selectbox("排序字段", ["流水号", "批次号", "机型", "预计入库时间"], index=0, key="plan_import_sort_col")
        with filter_col3:
            sort_asc = st.checkbox("升序", value=True, key="plan_import_sort_asc")
        with filter_col4:
            page_size = st.selectbox("每页条数", [10, 20, 50, 100], index=1, key="plan_import_page_size")

        work_df = plan_df.copy()
        if filter_keyword:
            mask = (
                work_df["流水号"].astype(str).str.contains(filter_keyword, case=False, na=False) |
                work_df["批次号"].astype(str).str.contains(filter_keyword, case=False, na=False) |
                work_df["机型"].astype(str).str.contains(filter_keyword, case=False, na=False)
            )
            work_df = work_df[mask].copy()

        if not work_df.empty:
            work_df = work_df.sort_values(by=sort_col, ascending=sort_asc, kind="stable")

        total_rows = len(work_df)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        page_col1, page_col2, page_col3 = st.columns([1, 1, 4])
        with page_col1:
            page_no = st.number_input("页码", min_value=1, max_value=total_pages, value=1, step=1, key="plan_import_page_no")
        with page_col2:
            st.markdown(f"共 {total_pages} 页")
        page_idx = int(page_no) - 1
        start = page_idx * page_size
        end = start + page_size
        page_df = work_df.iloc[start:end].copy()

        if should_reset_page_selection(st.session_state.get("plan_import_prev_page"), page_idx):
            st.session_state["plan_import_selected_map"] = {}
            st.session_state["plan_import_prev_page"] = page_idx

        selected_map = st.session_state.get("plan_import_selected_map", {})
        page_sns = page_df["流水号"].astype(str).tolist()
        for sn in page_sns:
            selected_map.setdefault(sn, False)
        selected_map = {sn: selected_map.get(sn, False) for sn in page_sns}
        st.session_state["plan_import_selected_map"] = selected_map

        selected_count = sum(1 for v in selected_map.values() if v)
        top_left, top_mid, top_right = st.columns([5, 2, 2])
        with top_mid:
            st.markdown(f"**已选 {selected_count} 条**")
        with top_right:
            all_selected = (len(page_sns) > 0 and selected_count == len(page_sns))
            select_all_key = f"plan_import_select_all_{page_idx}"
            select_all = st.checkbox("全选/取消全选", value=all_selected, key=select_all_key)
            if select_all != all_selected:
                selected_map = {sn: select_all for sn in page_sns}
                st.session_state["plan_import_selected_map"] = selected_map

        editor_df = page_df.copy()
        editor_df.insert(0, "选择", [selected_map.get(sn, False) for sn in page_sns])
        edited_plan = st.data_editor(
            editor_df,
            num_rows="fixed",
            hide_index=True,
            use_container_width=True,
            key=f"plan_import_editor_{page_idx}",
            column_config={
                "选择": st.column_config.CheckboxColumn("选择", width="small"),
                "批次号": st.column_config.TextColumn("批次号"),
                "机型": st.column_config.TextColumn("机型"),
                "流水号": st.column_config.TextColumn("流水号"),
                "预计入库时间": st.column_config.TextColumn("预计入库时间"),
                "机台备注/配置": st.column_config.TextColumn("机台备注/配置", width="large"),
            }
        )

        if "选择" in edited_plan.columns:
            current_map = {}
            for _, row in edited_plan.iterrows():
                current_map[str(row["流水号"]).strip()] = bool(row["选择"])
            st.session_state["plan_import_selected_map"] = current_map
            selected_map = current_map
        
        selected_rows = edited_plan[edited_plan["选择"] == True].copy() if "选择" in edited_plan.columns else pd.DataFrame()
        payload_date_col, confirm_btn_col, save_btn_col, msg_col = st.columns([2, 1.5, 1.5, 3])
        with payload_date_col:
            selected_date = st.date_input(
                "预计入库日期",
                value=None,
                min_value=datetime.now().date(),
                format="YYYY-MM-DD",
                key=f"plan_import_date_{page_idx}",
            )
        can_import = (not selected_rows.empty) and (selected_date is not None)
        with msg_col:
            if selected_rows.empty:
                st.warning("请先勾选至少 1 条数据")
            elif selected_date is None:
                st.warning("请选择预计入库日期")
            else:
                st.success(f"已选 {len(selected_rows)} 条，可执行导入")

        with confirm_btn_col:
            if st.button("🚀 确认导入 (Confirm)", type="primary", disabled=not can_import):
                payload, err = build_import_payload(selected_rows, selected_date)
                if err:
                    st.error(err)
                else:
                    import_result = execute_import_transaction_payload(payload, retry_times=1)
                    success_n = len(import_result["success"])
                    failed_n = len(import_result["failed"])
                    if hasattr(st, "toast"):
                        st.toast(f"成功 {success_n} 条，失败 {failed_n} 条")
                    else:
                        st.success(f"成功 {success_n} 条，失败 {failed_n} 条")
                    if failed_n > 0:
                        st.dataframe(pd.DataFrame(import_result["failed"]), use_container_width=True, hide_index=True)
                    time.sleep(0.5)
                    st.rerun()

        col_btns = [save_btn_col]
        with col_btns[0]:
             if st.button("💾 保存修改 (仅保存)", help="将上述修改保存到待入库清单"):
                 try:
                     save_import_staging(edited_plan.drop(columns=["选择"], errors="ignore"))
                     st.success("已保存修改")
                 except Exception as e:
                     st.error(f"保存失败: {e}")

def render_machine_inbound_module():
    """
    模块一：机台入库 (保留原有逻辑)
    - 权限控制：仅 Prod/Admin
    """
    check_prod_admin_permission()
    
    st.markdown("### 🏭 机台入库模块 (扫描入库)")
    
    # Original logic from line 4290
    c_s1, c_s2 = st.columns([3, 1])
    with c_s1: batch = st.text_input("扫描批次号", value=st.session_state.current_batch, key="machine_scan_batch")
    with c_s2: show_all = st.checkbox("显示全部待入库", value=True, key="machine_show_all")
    
    if batch: st.session_state.current_batch = batch
    
    df = get_data()
    # Filter '待入库'
    data = df[df['状态'] == '待入库'].copy()
    
    if not show_all:
        if batch: data = data[data['批次号'] == batch]
        else: data = pd.DataFrame(columns=data.columns)
        
    if not data.empty:
        st.info(f"待入库清单 ({len(data)} 台)")
        # 按机型排序
        data['__rank'] = data['机型'].apply(get_model_rank)
        data = data.sort_values(by=['__rank', '批次号'], ascending=[True, False])
        
        data.insert(0, "✅", False)
        # Use a key to avoid conflict
        res = st.data_editor(
            data[['✅', '批次号', '机型', '流水号', '机台备注/配置']], 
            hide_index=True, 
            use_container_width=True,
            key="machine_inbound_editor"
        )
        
        sel = res[res['✅'] == True]
        
        if not sel.empty:
            if st.button(f"🚀 确认入库 {len(sel)} 台", type="primary", key="btn_confirm_machine_inbound"):
                # Update status
                sns = sel['流水号'].tolist()
                df.loc[df['流水号'].isin(sns), '状态'] = '库存中'
                df.loc[df['流水号'].isin(sns), '更新时间'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(df)
                append_log("扫描入库", sns)
                st.success("入库成功！"); time.sleep(1); st.rerun()
    else:
        st.info("当前无待入库数据 (或未扫描到对应批次)")
