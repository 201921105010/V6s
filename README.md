# inventory_system_refactor

这是基于原始 `V6.py` 拆出来的一版过渡性重构骨架：

- `config.py`：环境变量、常量、目录、权限、机型排序、全局 CSS
- `database.py`：`get_engine()` / `init_mysql_tables()`
- `crud/`：数据库读写
- `core/`：认证、权限、文件管理、OCR、导航
- `utils/`：解析器与格式化器
- `views/`：侧边栏、登录页、各页面渲染函数
- `app.py`：唯一入口

## 说明

这版重构优先保证“拆分落地”和“低风险迁移”，所以 `views/common.py` 暂时保留了聚合导入，便于先把巨型单文件拆开，再继续做第二轮精修。

## 启动

```bash
streamlit run app.py
```
