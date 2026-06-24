"""金融指标计算器 — 收益率、风险、夏普比率等."""

import numpy as np                                                     # 数值计算
import pandas as pd                                                    # 数据处理


def annualized_return(returns: pd.Series, periods: int = 252) -> float:
    """计算年化收益率."""
    total = (1 + returns).prod()                                       # 累计收益
    n = len(returns)                                                   # 数据天数
    return float(total ** (periods / n) - 1)                           # 年化公式


def max_drawdown(nav: pd.Series) -> float:
    """计算最大回撤（负值表示亏损幅度）."""
    peak = nav.expanding(min_periods=1).max()                          # 历史最高点
    dd = (nav - peak) / peak                                           # 每日回撤幅度
    return float(dd.min())                                             # 取最大回撤


def sharpe_ratio(returns: pd.Series, rf: float = 0.03, periods: int = 252) -> float:
    """计算夏普比率（每单位风险的超额收益）."""
    excess = returns - rf / periods                                    # 超额收益
    return float(excess.mean() / excess.std() * np.sqrt(periods))      # 年化夏普


def volatility(returns: pd.Series, periods: int = 252) -> float:
    """计算年化波动率."""
    return float(returns.std() * np.sqrt(periods))                     # 标准差 × 根号252


def calmar_ratio(returns: pd.Series, nav: pd.Series) -> float:
    """计算 Calmar 比率（年化收益 / 最大回撤）."""
    ann = annualized_return(returns)                                   # 年化收益
    mdd = abs(max_drawdown(nav))                                       # 最大回撤绝对值
    return float(ann / mdd) if mdd > 0 else 0.0                       # 避免除零


def downside_risk(returns: pd.Series, threshold: float = 0.0, periods: int = 252) -> float:
    """计算下行风险（只统计负收益的波动）."""
    diff = returns - threshold                                         # 与阈值的差
    down = diff[diff < 0]                                              # 筛选负收益
    return float(np.sqrt((down ** 2).mean()) * np.sqrt(periods))       # 下行标准差


# ---- 风格漂移检测 ----

def detect_style_drift(old_holdings: list[dict], new_holdings: list[dict]) -> dict:
    """对比两期持仓，检测风格漂移.

    算法：
    1. 持仓重合度 = 两期共同股票数 / 总股票数
    2. 占比变化 = 共同持仓的占比差值绝对值之和
    3. 集中度变化 = 前5大持仓占比之和的差值
    4. 漂移分数 = (1-重合度)×40 + 占比变化×30 + 集中度变化×30，0-100
    """
    if not old_holdings or not new_holdings:                           # 数据不足
        return {"drift_score": 0, "is_drifting": False, "overlap": 0, "description": "数据不足，无法检测"}  # 返回默认

    old_codes = {h["stock_code"] for h in old_holdings}                # 旧持仓股票代码集合
    new_codes = {h["stock_code"] for h in new_holdings}                # 新持仓股票代码集合
    overlap = old_codes & new_codes                                    # 共同持仓
    total = old_codes | new_codes                                      # 总持仓
    overlap_ratio = len(overlap) / len(total) if total else 0          # 重合度

    old_pct = {h["stock_code"]: h["percentage"] for h in old_holdings}  # 旧持仓占比映射
    new_pct = {h["stock_code"]: h["percentage"] for h in new_holdings}  # 新持仓占比映射
    pct_change = sum(                                                  # 共同持仓占比变化
        abs(old_pct.get(c, 0) - new_pct.get(c, 0))                    # 占比差值绝对值
        for c in overlap                                               # 遍历共同持仓
    ) / max(len(overlap), 1)                                           # 取平均

    old_top5 = sum(sorted(old_pct.values(), reverse=True)[:5])         # 旧持仓前5集中度
    new_top5 = sum(sorted(new_pct.values(), reverse=True)[:5])         # 新持仓前5集中度
    concentration_change = abs(old_top5 - new_top5) / 100              # 集中度变化（归一化）

    drift_score = (1 - overlap_ratio) * 40 + pct_change * 3 + concentration_change * 30  # 漂移分数
    drift_score = min(max(drift_score, 0), 100)                        # 钳制到 0-100

    if drift_score > 60:                                               # 高漂移
        desc = "持仓风格发生显著变化，基金经理可能调整了投资策略"           # 描述
    elif drift_score > 30:                                             # 中等漂移
        desc = "持仓有一定调整，但整体风格基本保持"                       # 描述
    else:                                                              # 低漂移
        desc = "持仓风格稳定，基金经理投资策略一致"                       # 描述

    return {                                                           # 返回漂移检测结果
        "drift_score": round(drift_score, 1),                          # 漂移分数
        "is_drifting": drift_score > 60,                               # 是否漂移
        "overlap": round(overlap_ratio * 100, 1),                      # 重合度 %
        "pct_change": round(pct_change, 2),                            # 平均占比变化
        "concentration_change": round(concentration_change * 100, 1),  # 集中度变化 %
        "old_count": len(old_holdings),                                # 旧持仓数量
        "new_count": len(new_holdings),                                # 新持仓数量
        "overlap_count": len(overlap),                                 # 共同持仓数量
        "new_stocks": list(new_codes - old_codes)[:5],                 # 新增股票（最多5只）
        "removed_stocks": list(old_codes - new_codes)[:5],             # 移除股票（最多5只）
        "description": desc,                                           # 漂移描述
    }
