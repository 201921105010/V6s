from datetime import datetime

import pandas as pd
from sqlalchemy.exc import OperationalError

from database import get_engine


def append_log(action, sn_list, operator=None):
    current_time = datetime.now()
    operator = operator or "Unknown"
    new_logs = [{"时间": current_time, "操作类型": action, "流水号": sn, "操作员": operator} for sn in sn_list]
    if new_logs:
        try:
            pd.DataFrame(new_logs).to_sql('transaction_log', get_engine(), if_exists='append', index=False, method='multi')
        except (OperationalError, Exception) as e:
            print(f"append_log error: {e}")


def get_transaction_logs(limit=500):
    try:
        with get_engine().connect() as conn:
            return pd.read_sql(f"SELECT 时间, 操作类型, 流水号, 操作员 FROM transaction_log ORDER BY 时间 DESC LIMIT {int(limit)}", conn)
    except (OperationalError, Exception):
        return pd.DataFrame(columns=["时间", "操作类型", "流水号", "操作员"])
