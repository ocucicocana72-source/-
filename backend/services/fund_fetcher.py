"""基金数据采集服务 — 基于 AKShare 获取天天基金/东方财富数据."""

import akshare as ak                                                   # 金融数据接口
import pandas as pd                                                    # 数据处理
from functools import lru_cache                                        # 缓存装饰器


# ---- 基金排行 ----

def get_fund_rank(fund_type: str = "股票型", limit: int = 50) -> list[dict]:
    """获取基金排行列表."""
    df = ak.fund_open_fund_rank_em(symbol=fund_type)                   # 调用排行接口
    df = df.head(limit)                                                # 截取前N条
    return [_parse_rank_row(row) for _, row in df.iterrows()]          # 逐行解析


def _parse_rank_row(row) -> dict:
    """解析排行单行数据."""
    def safe_float(val):                                               # 安全转浮点
        return float(val) if pd.notna(val) else None                   # NaN 返回 None

    return {
        "code": row["基金代码"],                                        # 基金代码
        "name": row["基金简称"],                                        # 基金名称
        "nav": safe_float(row["单位净值"]),                              # 单位净值
        "acc_nav": safe_float(row["累计净值"]),                          # 累计净值
        "date": str(row["日期"]),                                       # 净值日期
        "daily_return": safe_float(row["日增长率"]),                     # 日涨跌
        "week_return": safe_float(row["近1周"]),                         # 近1周
        "month_return": safe_float(row["近1月"]),                        # 近1月
        "three_month_return": safe_float(row["近3月"]),                  # 近3月
        "six_month_return": safe_float(row["近6月"]),                    # 近6月
        "one_year_return": safe_float(row["近1年"]),                     # 近1年
        "three_year_return": safe_float(row["近3年"]),                   # 近3年
    }


# ---- 基金搜索 ----

# 搜索缓存（全局只加载一次）
_search_cache = {"df": None, "ts": 0}                                 # 缓存 DataFrame + 时间戳
SEARCH_CACHE_TTL = 3600                                               # 缓存1小时

def _get_fund_list():                                                  # 获取基金列表（带缓存）
    import time                                                        # 时间模块
    now = time.time()                                                  # 当前时间
    if _search_cache["df"] is not None and now - _search_cache["ts"] < SEARCH_CACHE_TTL:  # 缓存有效
        return _search_cache["df"]                                     # 返回缓存
    df = ak.fund_name_em()                                             # 从 AKShare 获取
    _search_cache["df"] = df                                           # 存入缓存
    _search_cache["ts"] = now                                          # 记录时间
    return df                                                          # 返回数据

def search_funds(keyword: str, limit: int = 20) -> list[dict]:
    """按代码或名称模糊搜索基金，覆盖全部基金（带缓存）."""
    df = _get_fund_list()                                              # 获取基金列表（缓存）
    code_mask = df["基金代码"].str.contains(keyword, case=False, na=False)  # 代码匹配
    name_mask = df["基金简称"].str.contains(keyword, case=False, na=False)  # 名称匹配
    pinyin_mask = df["拼音缩写"].str.contains(keyword.upper(), na=False)  # 拼音匹配
    mask = code_mask | name_mask | pinyin_mask                         # 任一匹配
    results = df[mask].head(limit)                                     # 截取前N条
    return [                                                           # 返回结果
        {"code": r["基金代码"], "name": r["基金简称"], "type": r.get("基金类型", "")}  # 代码+名称+类型
        for _, r in results.iterrows()                                 # 遍历匹配结果
    ]


# ---- 净值走势 ----

def get_fund_nav(code: str, period: str = "all") -> list[dict]:
    """获取基金净值历史（单位净值）."""
    df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")  # 调用接口
    df["净值日期"] = pd.to_datetime(df["净值日期"])                     # 转日期类型
    df = _filter_period(df, "净值日期", period)                         # 按区间过滤
    return [                                                           # 返回数据列表
        {
            "date": r["净值日期"].strftime("%Y-%m-%d"),                 # 日期字符串
            "nav": float(r["单位净值"]),                                # 单位净值
            "daily_return": float(r["日增长率"]) if pd.notna(r["日增长率"]) else 0,  # 日涨跌
        }
        for _, r in df.iterrows()                                      # 遍历每行
    ]


def get_fund_acc_nav(code: str, period: str = "all") -> list[dict]:
    """获取基金累计净值历史."""
    df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")  # 调用接口
    df["净值日期"] = pd.to_datetime(df["净值日期"])                     # 转日期类型
    df = _filter_period(df, "净值日期", period)                         # 按区间过滤
    return [                                                           # 返回数据列表
        {"date": r["净值日期"].strftime("%Y-%m-%d"), "acc_nav": float(r["累计净值"])}
        for _, r in df.iterrows()
    ]


def _filter_period(df: pd.DataFrame, col: str, period: str) -> pd.DataFrame:
    """按时间区间过滤 DataFrame."""
    if period == "all":                                                # 全部数据
        return df                                                      # 不过滤
    days_map = {"1m": 30, "3m": 90, "6m": 180, "1y": 365, "3y": 1095}  # 区间映射
    days = days_map.get(period, 365)                                   # 默认1年
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)              # 计算截止日期
    return df[df[col] >= cutoff]                                       # 过滤


# ---- 基金详情 ----

def get_fund_info(code: str) -> dict:
    """获取基金基本信息（自动搜索股票型和混合型）."""
    for ftype in ["股票型", "混合型"]:                                  # 依次尝试两种类型
        df = ak.fund_open_fund_rank_em(symbol=ftype)                   # 获取排行
        match = df[df["基金代码"] == code]                              # 按代码匹配
        if not match.empty:                                            # 找到了
            row = match.iloc[0]                                        # 取第一行
            return {                                                   # 返回详情
                "code": code,                                          # 基金代码
                "name": row["基金简称"],                                # 基金名称
                "nav": float(row["单位净值"]) if pd.notna(row["单位净值"]) else None,  # 净值
                "one_year_return": float(row["近1年"]) if pd.notna(row["近1年"]) else None,  # 年收益
                "three_year_return": float(row["近3年"]) if pd.notna(row["近3年"]) else None,  # 三年收益
            }
    return {"code": code, "error": "未找到基金"}                        # 未找到返回错误


# ---- 基金经理 ----

def get_fund_manager(code: str) -> dict:
    """获取基金经理信息."""
    try:
        df = ak.fund_manager_em()                                       # 获取经理数据
        match = df[df["现任基金代码"] == code]                           # 按代码匹配
        if match.empty:                                                # 未找到
            return {"code": code, "manager": None}                     # 返回空
        row = match.iloc[0]                                            # 取第一行
        days = int(row.get("累计从业时间", 0))                          # 从业天数
        years = round(days / 365, 1)                                   # 转换为年
        return {                                                       # 返回经理信息
            "code": code,                                              # 基金代码
            "manager_name": row.get("姓名", ""),                        # 经理姓名
            "tenure": f"{years}年",                                     # 任职时间
            "return_since": f"{row.get('现任基金最佳回报', '')}%",       # 任职回报
            "company": row.get("所属公司", ""),                         # 所属公司
        }
    except Exception as e:                                             # 捕获异常
        return {"code": code, "error": str(e)}                         # 返回错误信息


# ---- 基金持仓 ----

def get_fund_holdings(code: str) -> list[dict]:
    """获取基金最新一期前十大持仓."""
    try:
        df = ak.fund_portfolio_hold_em(symbol=code, date="2024")       # 获取持仓数据
        if df is None or df.empty:                                     # 无数据
            return []                                                  # 返回空列表
        latest_q = df["季度"].iloc[0]                                  # 取最新季度
        df = df[df["季度"] == latest_q].head(10)                       # 只取最新季度前10
        return [                                                       # 返回持仓列表
            {
                "stock_code": r.get("股票代码", ""),                     # 股票代码
                "stock_name": r.get("股票名称", ""),                     # 股票名称
                "percentage": float(r.get("占净值比例", 0)) if pd.notna(r.get("占净值比例")) else 0,  # 占比
            }
            for _, r in df.iterrows()                                  # 遍历持仓
        ]
    except Exception:                                                  # 接口可能无数据
        return []                                                      # 返回空列表


def get_holdings_by_quarter(code: str, n_quarters: int = 2) -> list[dict]:
    """获取基金最近 N 个季度的持仓数据，用于风格漂移检测."""
    try:
        df = ak.fund_portfolio_hold_em(symbol=code, date="2024")       # 获取持仓数据
        if df is None or df.empty:                                     # 无数据
            return []                                                  # 返回空列表
        quarters = df["季度"].unique()[:n_quarters]                     # 取最近N个季度
        result = []                                                    # 结果列表
        for q in quarters:                                             # 遍历每个季度
            sub = df[df["季度"] == q].head(10)                         # 取前10大持仓
            holdings = [                                               # 解析持仓
                {
                    "stock_code": r.get("股票代码", ""),                 # 股票代码
                    "stock_name": r.get("股票名称", ""),                 # 股票名称
                    "percentage": float(r.get("占净值比例", 0)) if pd.notna(r.get("占净值比例")) else 0,  # 占比
                }
                for _, r in sub.iterrows()                             # 遍历持仓
            ]
            result.append({"quarter": str(q), "holdings": holdings})   # 添加到结果
        return result                                                  # 返回季度持仓列表
    except Exception:                                                  # 接口可能无数据
        return []                                                      # 返回空列表
