import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, OperationalError

from config import (
    MYSQL_DB,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
    DEFAULT_ROLE_PERMISSIONS,
    DEFAULT_USERS,
)


@st.cache_resource
def get_engine():
    """返回 SQLAlchemy Engine（全局缓存，整个 Streamlit session 复用）"""
    url = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        f"?charset=utf8mb4"
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


def init_mysql_tables():
    """首次运行时建表，并写入默认用户（幂等操作，可安全重复调用）"""
    engine = get_engine()
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS finished_goods_data (
            `流水号`        VARCHAR(100) NOT NULL,
            `批次号`        VARCHAR(100) DEFAULT '',
            `机型`          VARCHAR(100) DEFAULT '',
            `状态`          VARCHAR(50)  DEFAULT '',
            `预计入库时间`  VARCHAR(50)  DEFAULT '',
            `更新时间`      VARCHAR(50)  DEFAULT '',
            `占用订单号`    VARCHAR(100) DEFAULT '',
            `客户`          VARCHAR(200) DEFAULT '',
            `代理商`        VARCHAR(200) DEFAULT '',
            `订单备注`      TEXT,
            `机台备注/配置` TEXT,
            `Location_Code` VARCHAR(100) DEFAULT '',
            PRIMARY KEY (`流水号`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS sales_orders (
            `订单号`        VARCHAR(100) NOT NULL,
            `客户名`        VARCHAR(200) DEFAULT '',
            `代理商`        VARCHAR(200) DEFAULT '',
            `需求机型`      TEXT,
            `需求数量`      VARCHAR(20)  DEFAULT '',
            `下单时间`      VARCHAR(50)  DEFAULT '',
            `备注`          TEXT,
            `包装选项`      VARCHAR(100) DEFAULT '',
            `发货时间`      VARCHAR(50)  DEFAULT '',
            `指定批次/来源` VARCHAR(200) DEFAULT '',
            `status`        VARCHAR(50)  DEFAULT 'active',
            `delete_reason` TEXT,
            PRIMARY KEY (`订单号`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS factory_plan (
            `id`            INT NOT NULL AUTO_INCREMENT,
            `合同号`        VARCHAR(100) DEFAULT '',
            `机型`          VARCHAR(100) DEFAULT '',
            `排产数量`      VARCHAR(20)  DEFAULT '',
            `要求交期`      VARCHAR(50)  DEFAULT '',
            `状态`          VARCHAR(50)  DEFAULT '',
            `备注`          TEXT,
            `客户名`        VARCHAR(200) DEFAULT '',
            `代理商`        VARCHAR(200) DEFAULT '',
            `指定批次/来源` VARCHAR(200) DEFAULT '',
            `订单号`        VARCHAR(100) DEFAULT '',
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS transaction_log (
            `id`        INT NOT NULL AUTO_INCREMENT,
            `时间`      VARCHAR(50)  DEFAULT '',
            `操作类型`  VARCHAR(200) DEFAULT '',
            `流水号`    VARCHAR(100) DEFAULT '',
            `操作员`    VARCHAR(100) DEFAULT '',
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS planning_records (
            `id`         INT NOT NULL AUTO_INCREMENT,
            `order_id`   VARCHAR(100) DEFAULT '',
            `model`      VARCHAR(100) DEFAULT '',
            `plan_info`  TEXT,
            `updated_at` VARCHAR(50)  DEFAULT '',
            PRIMARY KEY (`id`),
            UNIQUE KEY `uq_order_model` (`order_id`, `model`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS contract_records (
            `id`          INT NOT NULL AUTO_INCREMENT,
            `contract_id` VARCHAR(100) DEFAULT '',
            `customer`    VARCHAR(200) DEFAULT '',
            `file_name`   VARCHAR(500) DEFAULT '',
            `file_path`   VARCHAR(1000) DEFAULT '',
            `file_hash`   VARCHAR(64)  DEFAULT '',
            `uploader`    VARCHAR(100) DEFAULT '',
            `upload_time` VARCHAR(50)  DEFAULT '',
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            `id`        INT NOT NULL AUTO_INCREMENT,
            `timestamp` VARCHAR(50)  DEFAULT '',
            `user`      VARCHAR(100) DEFAULT '',
            `ip`        VARCHAR(100) DEFAULT '',
            `action`    VARCHAR(200) DEFAULT '',
            `details`   TEXT,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            `username`      VARCHAR(100) NOT NULL,
            `password`      VARCHAR(200) DEFAULT '',
            `role`          VARCHAR(50)  DEFAULT '',
            `name`          VARCHAR(100) DEFAULT '',
            `status`        VARCHAR(50)  DEFAULT 'pending',
            `register_time` VARCHAR(50)  DEFAULT '',
            `audit_time`    VARCHAR(50)  DEFAULT '',
            `auditor`       VARCHAR(100) DEFAULT '',
            PRIMARY KEY (`username`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS role_permissions (
            `id`        INT NOT NULL AUTO_INCREMENT,
            `role_id`   VARCHAR(50)  DEFAULT '',
            `func_code` VARCHAR(100) DEFAULT '',
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS shipping_history (
            `id`            INT NOT NULL AUTO_INCREMENT,
            `批次号`        VARCHAR(100) DEFAULT '',
            `机型`          VARCHAR(100) DEFAULT '',
            `流水号`        VARCHAR(100) DEFAULT '',
            `状态`          VARCHAR(50)  DEFAULT '',
            `预计入库时间`  VARCHAR(50)  DEFAULT '',
            `更新时间`      VARCHAR(50)  DEFAULT '',
            `占用订单号`    VARCHAR(100) DEFAULT '',
            `客户`          VARCHAR(200) DEFAULT '',
            `代理商`        VARCHAR(200) DEFAULT '',
            `订单备注`      TEXT,
            `机台备注/配置` TEXT,
            `archive_month` VARCHAR(20)  DEFAULT '',
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS plan_import (
            `流水号`        VARCHAR(100) NOT NULL,
            `批次号`        VARCHAR(100) DEFAULT '',
            `机型`          VARCHAR(100) DEFAULT '',
            `状态`          VARCHAR(50)  DEFAULT '待入库',
            `预计入库时间`  VARCHAR(50)  DEFAULT '',
            `机台备注/配置` TEXT,
            PRIMARY KEY (`流水号`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    ]
    with engine.begin() as conn:
        for ddl in ddl_statements:
            conn.execute(text(ddl))
        result = conn.execute(text("SHOW COLUMNS FROM finished_goods_data LIKE 'Location_Code'"))
        if result.fetchone() is None:
            conn.execute(text("ALTER TABLE finished_goods_data ADD COLUMN `Location_Code` VARCHAR(100) DEFAULT ''"))

        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        if result.fetchone()[0] == 0:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for uid, info in DEFAULT_USERS.items():
                conn.execute(text(
                    "INSERT IGNORE INTO users "
                    "(username, password, role, name, status, register_time, audit_time, auditor) "
                    "VALUES (:u, :p, :r, :n, 'active', :t, :t, 'System')"
                ), {"u": uid, "p": info["password"], "r": info["role"], "n": info["name"], "t": current_time})

        result = conn.execute(text("SELECT COUNT(*) FROM role_permissions"))
        if result.fetchone()[0] == 0:
            for role_id, func_codes in DEFAULT_ROLE_PERMISSIONS.items():
                for func_code in func_codes:
                    conn.execute(
                        text("INSERT IGNORE INTO role_permissions (role_id, func_code) VALUES (:r, :f)"),
                        {"r": role_id, "f": func_code},
                    )
        sales_perms = DEFAULT_ROLE_PERMISSIONS.get("Sales", [])
        conn.execute(text("DELETE FROM role_permissions WHERE role_id='Sales'"))
        for func_code in sales_perms:
            conn.execute(
                text("INSERT IGNORE INTO role_permissions (role_id, func_code) VALUES (:r, :f)"),
                {"r": "Sales", "f": func_code},
            )
