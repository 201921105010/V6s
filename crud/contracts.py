from datetime import datetime
import os
import re

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from config import BASE_DIR
from database import get_engine


def get_contract_files(contract_id=None):
    try:
        with get_engine().connect() as conn:
            if contract_id:
                df = pd.read_sql(text("SELECT * FROM contract_records WHERE contract_id=:cid"), conn, params={"cid": str(contract_id)})
            else:
                df = pd.read_sql(text("SELECT * FROM contract_records"), conn)
        df = df.fillna("")

        if contract_id:
            safe_cid = re.sub(r'[\/*?:"<>|]', "", str(contract_id)).strip()
            folder_paths = [
                os.path.join(BASE_DIR, "data", safe_cid),
                os.path.join(BASE_DIR, "data", "contracts", safe_cid),
            ]
            folder_paths = [p for p in folder_paths if os.path.exists(p) and os.path.isdir(p)]

            if folder_paths:
                disk_files = []
                existing_files = set(df['file_name'].tolist()) if not df.empty else set()
                existing_paths = set(df['file_path'].tolist()) if not df.empty else set()
                seen_disk_paths = set()

                for folder_path in folder_paths:
                    rel_prefix = os.path.relpath(folder_path, BASE_DIR)
                    for f in os.listdir(folder_path):
                        abs_file = os.path.join(folder_path, f)
                        if os.path.isfile(abs_file):
                            rel_file = os.path.join(rel_prefix, f)
                            if rel_file in seen_disk_paths:
                                continue
                            seen_disk_paths.add(rel_file)
                            if (f not in existing_files) and (rel_file not in existing_paths):
                                disk_files.append({
                                    "contract_id": str(contract_id),
                                    "customer": "Unknown",
                                    "file_name": f,
                                    "file_path": rel_file,
                                    "file_hash": "",
                                    "uploader": "Disk/System",
                                    "upload_time": datetime.fromtimestamp(os.path.getmtime(abs_file)).strftime("%Y-%m-%d %H:%M:%S"),
                                })

                if disk_files:
                    df_disk = pd.DataFrame(disk_files)
                    df = pd.concat([df, df_disk], ignore_index=True)

        return df
    except (OperationalError, Exception) as e:
        print(f"Error getting contract files: {e}")
        return pd.DataFrame(columns=["contract_id", "customer", "file_name", "file_path", "file_hash", "uploader", "upload_time"])


def get_unlinked_contract_folders(known_contract_ids=None):
    rows = []
    known_ids = set(str(x).strip() for x in (known_contract_ids or []) if str(x).strip())
    try:
        data_root = os.path.join(BASE_DIR, "data")
        if not os.path.exists(data_root) or not os.path.isdir(data_root):
            return pd.DataFrame(columns=["合同号", "客户名", "文件数", "最近更新时间"])

        scan_roots = [data_root, os.path.join(data_root, "contracts")]
        seen_ids = set()
        for root in scan_roots:
            if not os.path.exists(root) or not os.path.isdir(root):
                continue
            for folder in os.listdir(root):
                folder_path = os.path.join(root, folder)
                if not os.path.isdir(folder_path):
                    continue
                cid = str(folder).strip()
                if not cid or cid in seen_ids:
                    continue
                seen_ids.add(cid)
                if cid in known_ids:
                    continue

                files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
                if not files:
                    continue

                latest_ts = max(os.path.getmtime(os.path.join(folder_path, f)) for f in files)
                customer = cid.split("_")[0] if "_" in cid else cid
                rows.append({
                    "合同号": cid,
                    "客户名": customer,
                    "文件数": len(files),
                    "最近更新时间": datetime.fromtimestamp(latest_ts).strftime("%Y-%m-%d %H:%M:%S"),
                })

        if not rows:
            return pd.DataFrame(columns=["合同号", "客户名", "文件数", "最近更新时间"])
        df = pd.DataFrame(rows)
        return df.sort_values("最近更新时间", ascending=False).reset_index(drop=True)
    except Exception as e:
        print(f"Error scanning unlinked contract folders: {e}")
        return pd.DataFrame(columns=["合同号", "客户名", "文件数", "最近更新时间"])
