<<<<<<< HEAD
"""已弃用的兼容模块。

第一轮拆分时，这个文件用于临时聚合 imports，帮助把单文件快速切开。
第二轮精修后，所有视图都已经改成显式依赖，不再应当 import 本模块。

后续建议：
1. 新增页面时直接按需从 config/core/crud/utils 导入。
2. 若第三轮继续重构，可直接删除本文件。
"""
=======
import ast
import base64
import json
import os
import random
import re
import shutil
import tempfile
import time
import uuid
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from config import (
    ARCHIVE_DIR,
    BASE_DIR,
    CONTRACT_ABS_DIR,
    CONTRACT_DIR,
    FUNC_MAP,
    MACHINE_ARCHIVE_ABS_DIR,
    MACHINE_ARCHIVE_DIR,
    MAMMOTH_AVAILABLE,
    OPENPYXL_AVAILABLE,
    OCR_AVAILABLE,
    PLOTLY_AVAILABLE,
    PRESET_RATIOS,
    go,
    mammoth,
    px,
)
from core.auth import register_user, verify_login
from core.file_manager import delete_contract_file, save_contract_file
from core.metrics import get_urgent_production_count
from core.navigation import go_home, go_page
from core.permissions import check_access, get_role_permissions
from crud.contracts import get_contract_files, get_unlinked_contract_folders
from crud.inventory import append_import_staging, clear_import_staging, get_data, get_import_staging, save_data, save_import_staging
from crud.logs import get_transaction_logs
from crud.orders import allocate_inventory, create_sales_order, get_orders, revert_to_inbound, save_orders, update_sales_order
from crud.planning import get_factory_plan, get_planning_records, save_factory_plan, save_planning_record
from crud.users import get_all_users, save_all_users
from utils.formatters import get_model_rank
from utils.parsers import (
    build_import_payload,
    diff_tracking_vs_inventory,
    execute_import_transaction_payload,
    generate_auto_inbound,
    parse_requirements,
    parse_tracking_xls,
    process_paste_data,
    should_reset_page_selection,
)
>>>>>>> 88b8b5966418ed53f8a893e327b91727f9c01707
