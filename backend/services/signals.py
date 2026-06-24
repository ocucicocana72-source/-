"""买卖信号引擎 — 5维度评分 + 详细AI分析."""

import pandas as pd
import numpy as np
from services.fund_fetcher import get_fund_nav, get_fund_rank
from services.calculator import sharpe_ratio

SIGNAL_MAP = [
    (0.6, "强烈建议加仓", "🟢", "基金处于高性价比区间，建议分批加仓"),
    (0.2, "建议持有", "🟡", "基金表现中等偏上，维持现有仓位"),
    (-0.2, "中性观望", "⚪", "无明显方向，建议观望"),
    (-0.6, "建议减仓", "🟠", "表现偏弱，建议减仓控制风险"),
    (-999, "建议清仓", "🔴", "持续恶化，建议止损清仓"),
]


def _calculate_risk_metrics(navs: np.ndarray, returns: pd.Series) -> dict:
    """计算详细的风险指标."""
    if len(navs) < 30:
        return {"volatility": 0, "max_dd": 0, "calmar": 0, "downside_risk": 0, "win_rate": 0}

    # 年化波动率
    volatility = returns.std() * np.sqrt(252) * 100

    # 最大回撤
    peak = pd.Series(navs).expanding().max().values
    drawdowns = (navs - peak) / peak
    max_dd = drawdowns.min() * 100

    # 卡玛比率（年化收益/最大回撤）
    annual_return = (navs[-1] / navs[0]) ** (252 / len(navs)) - 1
    calmar = abs(annual_return / (max_dd / 100)) if max_dd != 0 else 0

    # 下行风险
    negative_returns = returns[returns < 0]
    downside_risk = negative_returns.std() * np.sqrt(252) * 100 if len(negative_returns) > 0 else 0

    # 胜率（正收益天数占比）
    win_rate = (returns > 0).sum() / len(returns) * 100 if len(returns) > 0 else 0

    return {
        "volatility": round(volatility, 2),
        "max_dd": round(max_dd, 2),
        "calmar": round(calmar, 2),
        "downside_risk": round(downside_risk, 2),
        "win_rate": round(win_rate, 2),
    }


def _calculate_trend_metrics(navs: np.ndarray) -> dict:
    """计算趋势相关指标."""
    if len(navs) < 5:
        return {"ret_1w": 0, "ret_1m": 0, "ret_3m": 0, "ret_6m": 0, "ret_1y": 0, "ma5": 0, "ma20": 0, "ma60": 0, "trend_direction": "横盘"}

    # 各周期收益率
    ret_1w = (navs[-1] / navs[-5] - 1) * 100 if len(navs) >= 5 else 0
    ret_1m = (navs[-1] / navs[-21] - 1) * 100 if len(navs) >= 21 else 0
    ret_3m = (navs[-1] / navs[-63] - 1) * 100 if len(navs) >= 63 else 0
    ret_6m = (navs[-1] / navs[-126] - 1) * 100 if len(navs) >= 126 else 0
    ret_1y = (navs[-1] / navs[-252] - 1) * 100 if len(navs) >= 252 else 0

    # 均线
    ma5 = pd.Series(navs).rolling(5).mean().iloc[-1] if len(navs) >= 5 else navs[-1]
    ma20 = pd.Series(navs).rolling(20).mean().iloc[-1] if len(navs) >= 20 else navs[-1]
    ma60 = pd.Series(navs).rolling(60).mean().iloc[-1] if len(navs) >= 60 else navs[-1]

    # 趋势判断
    current = navs[-1]
    if current > ma5 > ma20 > ma60:
        trend = "强势上涨"
    elif current > ma20 > ma60:
        trend = "温和上涨"
    elif current < ma5 < ma20 < ma60:
        trend = "持续下跌"
    elif current < ma20 < ma60:
        trend = "弱势下跌"
    else:
        trend = "震荡整理"

    return {
        "ret_1w": round(ret_1w, 2),
        "ret_1m": round(ret_1m, 2),
        "ret_3m": round(ret_3m, 2),
        "ret_6m": round(ret_6m, 2),
        "ret_1y": round(ret_1y, 2),
        "ma5": round(float(ma5), 4),
        "ma20": round(float(ma20), 4),
        "ma60": round(float(ma60), 4),
        "trend_direction": trend,
    }


def _generate_ai_analysis(code: str, name: str, risk: dict, trend: dict, signal: str, total_score: float, profit_pct: float) -> str:
    """生成详细的AI分析报告."""
    # 解析信号含义
    signal_explain = {
        "🟢": "这是一个积极的买入信号，表明基金当前处于较好的投资时机。",
        "🟡": "这是一个中性偏积极的信号，建议维持现有仓位，可适当观望。",
        "⚪": "这是一个中性信号，建议暂时观望，等待更明确的方向。",
        "🟠": "这是一个谨慎信号，表明基金可能存在一定风险，建议适当减仓。",
        "🔴": "这是一个风险警示信号，建议考虑止损或大幅减仓。",
    }

    # 趋势分析
    trend_analysis = f"**趋势分析**：{trend['trend_direction']}。\n"
    if trend["ret_1m"] > 5:
        trend_analysis += f"- 近1个月上涨{trend['ret_1m']:.1f}%，短期动能强劲\n"
    elif trend["ret_1m"] > 0:
        trend_analysis += f"- 近1个月上涨{trend['ret_1m']:.1f}%，保持正向趋势\n"
    else:
        trend_analysis += f"- 近1个月下跌{abs(trend['ret_1m']):.1f}%，短期承压\n"

    if trend["ret_3m"] > 10:
        trend_analysis += f"- 近3个月上涨{trend['ret_3m']:.1f}%，中期趋势良好\n"
    elif trend["ret_3m"] > 0:
        trend_analysis += f"- 近3个月上涨{trend['ret_3m']:.1f}%，中期表现尚可\n"
    else:
        trend_analysis += f"- 近3个月下跌{abs(trend['ret_3m']):.1f}%，中期表现较弱\n"

    # 风险分析
    risk_analysis = f"**风险分析**：\n"
    if risk["max_dd"] > -10:
        risk_analysis += f"- 最大回撤{risk['max_dd']:.1f}%，风险控制优秀\n"
    elif risk["max_dd"] > -20:
        risk_analysis += f"- 最大回撤{risk['max_dd']:.1f}%，风险可控\n"
    elif risk["max_dd"] > -30:
        risk_analysis += f"- 最大回撤{risk['max_dd']:.1f}%，风险中等\n"
    else:
        risk_analysis += f"- 最大回撤{risk['max_dd']:.1f}%，风险较高，需谨慎\n"

    risk_analysis += f"- 年化波动率{risk['volatility']:.1f}%，"
    if risk["volatility"] < 15:
        risk_analysis += "波动较小，适合稳健型投资者\n"
    elif risk["volatility"] < 25:
        risk_analysis += "波动适中\n"
    else:
        risk_analysis += "波动较大，适合风险承受能力强的投资者\n"

    risk_analysis += f"- 胜率{risk['win_rate']:.1f}%，"
    if risk["win_rate"] > 60:
        risk_analysis += "胜率较高，投资体验较好\n"
    elif risk["win_rate"] > 50:
        risk_analysis += "胜率一般\n"
    else:
        risk_analysis += "胜率偏低，持有体验可能较差\n"

    # 收益分析
    profit_analysis = f"**收益分析**：\n"
    if profit_pct > 30:
        profit_analysis += f"- 持有收益率{profit_pct:.2f}%，收益丰厚，可考虑部分止盈\n"
    elif profit_pct > 10:
        profit_analysis += f"- 持有收益率{profit_pct:.2f}%，收益良好\n"
    elif profit_pct > 0:
        profit_analysis += f"- 持有收益率{profit_pct:.2f}%，小幅盈利\n"
    elif profit_pct > -10:
        profit_analysis += f"- 持有收益率{profit_pct:.2f}%，小幅亏损，可考虑补仓摊低成本\n"
    else:
        profit_analysis += f"- 持有收益率{profit_pct:.2f}%，亏损较大，需评估是否继续持有\n"

    # 综合建议
    advice_map = {
        "🟢": "基于当前分析，该基金各项指标表现良好，**建议分批加仓**。建议采用定期定额的方式分批买入，降低择时风险。",
        "🟡": "该基金整体表现中等偏上，**建议继续持有**。可关注后续走势，等待更好的加仓时机。",
        "⚪": "当前没有明确的方向信号，**建议观望等待**。可设置价格提醒，在出现明确信号后再做决策。",
        "🟠": "该基金近期表现偏弱，**建议适当减仓**。可先减持部分仓位，降低风险敞口。",
        "🔴": "该基金多项指标恶化，**建议考虑清仓**。建议及时止损，避免进一步亏损。",
    }

    # 组装完整报告
    report = f"## 📊 {name}({code}) 详细分析报告\n\n"
    report += f"**综合评分**: {total_score:.3f} | **信号**: {signal} | **持有收益**: {profit_pct:.2f}%\n\n"
    report += f"---\n\n"
    report += f"{signal_explain.get(signal, '')}\n\n"
    report += f"{trend_analysis}\n"
    report += f"{risk_analysis}\n"
    report += f"{profit_analysis}\n"
    report += f"---\n\n"
    report += f"**💡 操作建议**：{advice_map.get(signal, '')}\n\n"
    report += f"**⚠️ 风险提示**：以上分析基于历史数据，不构成投资建议。基金投资有风险，入市需谨慎。请根据自身风险承受能力做出投资决策。"

    return report


def analyze_fund(code: str, buy_price: float = 0, name: str = "") -> dict:
    """分析单只基金，返回详细信号和AI报告."""
    nav_data = get_fund_nav(code, "all")
    if not nav_data or len(nav_data) < 30:
        return {"code": code, "error": "数据不足", "signal": "⚪", "signal_text": "无法分析", "score": 0, "dimensions": {}, "ai_report": "数据不足，无法生成分析报告。"}

    df = pd.DataFrame(nav_data).sort_values("date")
    navs = df["nav"].values
    returns = df["nav"].pct_change().dropna()
    current_nav = navs[-1]

    # 趋势
    nav_1m = navs[-21:] if len(navs) >= 21 else navs
    nav_3m = navs[-63:] if len(navs) >= 63 else navs
    ret_1m = (nav_1m[-1] / nav_1m[0] - 1) if len(nav_1m) > 1 else 0
    ret_3m = (nav_3m[-1] / nav_3m[0] - 1) if len(nav_3m) > 1 else 0
    trend_score = max(min((ret_1m - ret_3m / 3) * 10, 1), -1)

    # 回撤
    peak = pd.Series(navs).expanding().max().values
    current_dd = (current_nav - peak[-1]) / peak[-1]
    dd_score = 0.2 if current_dd > -0.05 else 0.5 if current_dd > -0.15 else 0.8 if current_dd > -0.30 else -0.5

    # 夏普
    sr = sharpe_ratio(returns) if len(returns) >= 60 else 0
    sr_score = max(min(sr / 3, 1), -1)

    # 动量
    nav_1w = navs[-5:] if len(navs) >= 5 else navs
    week_return = (nav_1w[-1] / nav_1w[0] - 1) if len(nav_1w) > 1 else 0
    momentum_score = max(min(week_return * 20, 1), -1)

    # 估值
    valuation_score = 0
    try:
        all_funds = get_fund_rank("股票型", 200) + get_fund_rank("混合型", 200)
        returns_list = sorted([f.get("one_year_return", 0) or 0 for f in all_funds])
        fund_info = next((f for f in all_funds if f["code"] == code), None)
        if fund_info and fund_info.get("one_year_return"):
            rank_pct = sum(1 for r in returns_list if r <= fund_info["one_year_return"]) / len(returns_list)
            valuation_score = (0.5 - rank_pct) * 2
    except Exception:
        pass

    # 综合
    total = trend_score * 0.25 + dd_score * 0.20 + sr_score * 0.25 + momentum_score * 0.15 + valuation_score * 0.15
    total = max(min(total, 1), -1)

    signal_text, signal_emoji, advice = "中性观望", "⚪", "无明显方向"
    for threshold, text, emoji, adv in SIGNAL_MAP:
        if total >= threshold:
            signal_text, signal_emoji, advice = text, emoji, adv
            break

    profit_pct = ((current_nav - buy_price) / buy_price * 100) if buy_price > 0 else 0

    # 计算详细指标
    risk_metrics = _calculate_risk_metrics(navs, returns)
    trend_metrics = _calculate_trend_metrics(navs)

    # 生成AI分析报告
    ai_report = _generate_ai_analysis(
        code=code,
        name=name or code,
        risk=risk_metrics,
        trend=trend_metrics,
        signal=signal_emoji,
        total_score=total,
        profit_pct=profit_pct,
    )

    return {
        "code": code, "current_nav": round(current_nav, 4), "buy_price": buy_price,
        "profit_pct": round(profit_pct, 2), "total_score": round(total, 3),
        "signal": signal_emoji, "signal_text": signal_text, "advice": advice,
        "current_dd": round(current_dd * 100, 2), "week_return": round(week_return * 100, 2),
        "dimensions": {
            "trend": {"score": round(trend_score, 2), "label": "趋势", "desc": f"近1月{ret_1m*100:.1f}%"},
            "drawdown": {"score": round(dd_score, 2), "label": "回撤", "desc": f"回撤{current_dd*100:.1f}%"},
            "sharpe": {"score": round(sr_score, 2), "label": "夏普", "desc": f"夏普{sr:.2f}"},
            "momentum": {"score": round(momentum_score, 2), "label": "动量", "desc": f"近1周{week_return*100:.2f}%"},
            "valuation": {"score": round(valuation_score, 2), "label": "估值", "desc": "同类排名"},
        },
        "risk_metrics": risk_metrics,
        "trend_metrics": trend_metrics,
        "ai_report": ai_report,
    }


def analyze_portfolio(holdings: list[dict]) -> dict:
    """分析整个持仓组合."""
    signals = []
    total_value = 0
    total_cost = 0
    for h in holdings:
        name = h.get("name", h["code"])
        sig = analyze_fund(h["code"], h.get("buy_price", 0), name)
        sig["name"] = name
        sig["shares"] = h.get("shares", 0)
        total_cost += h.get("buy_price", 0) * h.get("shares", 0)
        total_value += sig.get("current_nav", 0) * h.get("shares", 0)
        signals.append(sig)
    total_return = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
    return {
        "holdings": signals,
        "summary": {"total_value": round(total_value, 2), "total_cost": round(total_cost, 2), "total_return": round(total_return, 2), "count": len(signals)},
    }
