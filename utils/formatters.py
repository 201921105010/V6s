from config import CUSTOM_MODEL_ORDER


def get_model_rank(model_name):
    # 1. 基础清洗
    clean_name = str(model_name).strip()
    
    # 2. 尝试直接匹配
    if clean_name in CUSTOM_MODEL_ORDER:
        return CUSTOM_MODEL_ORDER.index(clean_name)
    
    # 3. 尝试忽略大小写匹配
    upper_list = [x.upper() for x in CUSTOM_MODEL_ORDER]
    if clean_name.upper() in upper_list:
        return upper_list.index(clean_name.upper())
        
    # 4. 尝试移除空格后匹配 (兼容 "FR-400 XS(PRO)" 这种写法)
    nospace_list = [x.replace(" ", "").upper() for x in CUSTOM_MODEL_ORDER]
    clean_nospace = clean_name.replace(" ", "").upper()
    if clean_nospace in nospace_list:
        return nospace_list.index(clean_nospace)
        
    # 5. 兼容旧版写法 (移除连字符)
    # 比如 CUSTOM_MODEL_ORDER 存的是 "FR-400G"，如果来了 "FR400G"，也让它匹配上
    # 或者反之
    # 既然列表里是带连字符的，我们把 clean_name 加连字符比较难，不如把列表去连字符
    nohyphen_list = [x.replace("-", "").upper() for x in CUSTOM_MODEL_ORDER]
    clean_nohyphen = clean_name.replace("-", "").upper()
    if clean_nohyphen in nohyphen_list:
        return nohyphen_list.index(clean_nohyphen)

    return 9999
