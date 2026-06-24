"""多基金对比服务 — 批量获取指标 + 横向对比."""

import pandas as pd
from services.fund_fetcher import get_fund_nav, get_fund_info, get_fund_manager, get_fund_holdings
from services.calculator import annualized_return, max_drawdown, sharpe_ratio, volatility, calmar_ratio, downside_risk


def compare_funds(codes: list[str], period: str = "1y") -> dict:
    """批量对比多只基金的核心指标."""
    results = []
    for code in codes:
        results.append(_analyze_single(code, period))
    return {"funds": results, "summary": _generate_summary(results), "period": period, "count": len(results)}


def _analyze_single(code: str, period: str) -> dict:
    """分析单只基金."""
    info = get_fund_info(code)
    nav_data = get_fund_nav(code, period)
    manager = get_fund_manager(code)
    holdings = get_fund_holdings(code)
    metrics = {"annualized_return": 0, "max_drawdown": 0, "sharpe_ratio": 0, "volatility": 0, "calmar_ratio": 0, "downside_risk": 0}

    if nav_data and len(nav_data) >= 10:
        df = pd.DataFrame(nav_data).sort_values("date")
        returns = df["nav"].pct_change().dropna()
        nav_s = df["nav"]
        metrics = {
            "annualized_return": round(annualized_return(returns) * 100, 2),
            "max_drawdown": round(max_drawdown(nav_s) * 100, 2),
            "sharpe_ratio": round(sharpe_ratio(returns), 4),
            "volatility": round(volatility(returns) * 100, 2),
            "calmar_ratio": round(calmar_ratio(returns, nav_s), 4),
            "downside_risk": round(downside_risk(returns) * 100, 2),
        }

    score = _calc_score(metrics)
    return {
        "code": code, "name": info.get("name", code), "nav": info.get("nav"),
        "one_year_return": info.get("one_year_return"),
        "manager": manager.get("manager_name", ""), "company": manager.get("company", ""),
        "metrics": metrics, "score": score,
        "holdings_count": len(holdings), "top3_holdings": holdings[:3],
    }


def _calc_score(metrics: dict) -> dict:
    """计算综合评分."""
    ann_ret = metrics["annualized_return"]
    mdd = abs(metrics["max_drawdown"])
    sr = metrics["sharpe_ratio"]
    ret_s = min(max(ann_ret / 50 * 100, 0), 100)
    risk_s = max(100 - mdd * 2, 0)
    sharp_s = min(max(sr / 3 * 100, 0), 100)
    total = ret_s * 0.4 + risk_s * 0.3 + sharp_s * 0.3
    rec = "强烈推荐" if total >= 80 else "推荐" if total >= 60 else "观望" if total >= 40 else "不推荐"
    return {"total": round(total, 1), "return_score": round(ret_s, 1), "risk_score": round(risk_s, 1), "sharpe_score": round(sharp_s, 1), "recommendation": rec}


def _generate_summary(funds: list[dict]) -> dict:
    """生成对比摘要 + AI 总结."""
    if not funds:
        return {}
    best_ret = max(funds, key=lambda f: f["metrics"]["annualized_return"])
    best_sh = max(funds, key=lambda f: f["metrics"]["sharpe_ratio"])
    low_risk = min(funds, key=lambda f: abs(f["metrics"]["max_drawdown"]))
    best_sc = max(funds, key=lambda f: f["score"]["total"])

    # ---- AI 总结 ----
    names = "、".join(f["name"][:4] for f in funds)                    # 基金简称列表
    winner = best_sc                                                   # 评分最高者
    runner = sorted(funds, key=lambda f: -f["score"]["total"])[1] if len(funds) > 1 else None  # 第二名

    # 构建总结原因
    reasons = []                                                       # 原因列表
    reasons.append(f"综合评分：{winner['name'][:4]}以{winner['score']['total']}分领先")  # 评分对比

    if best_ret["code"] != winner["code"]:                             # 最高收益不是冠军
        reasons.append(f"但{best_ret['name'][:4]}年化收益更高（{best_ret['metrics']['annualized_return']}%）")  # 补充
    else:                                                              # 收益也是冠军
        reasons.append(f"年化收益{winner['metrics']['annualized_return']}%也位居第一")  # 补充

    if abs(low_risk["metrics"]["max_drawdown"]) < abs(winner["metrics"]["max_drawdown"]) * 0.8:  # 风控差异明显
        reasons.append(f"{low_risk['name'][:4]}回撤控制更好（{low_risk['metrics']['max_drawdown']}%），风险更低")  # 补充

    # 最终建议
    if winner["score"]["total"] >= 80:                                 # 高分
        conclusion = f"推荐优先配置{winner['name'][:4]}，综合能力突出"
        if runner and runner["score"]["total"] >= 70:                  # 第二名也不错
            conclusion += f"，可搭配{runner['name'][:4]}分散风险"       # 补充
    elif winner["score"]["total"] >= 60:                               # 中等分
        conclusion = f"建议以{winner['name'][:4]}为主，但需关注回撤风险"
    else:                                                              # 低分
        conclusion = f"整体表现一般，建议观望或寻找更优标的"

    # 适合人群
    mdd = abs(winner["metrics"]["max_drawdown"])                       # 冠军回撤
    if mdd < 20:                                                       # 低回撤
        investor_type = "稳健型投资者，追求稳定增值"
    elif mdd < 35:                                                     # 中回撤
        investor_type = "平衡型投资者，能承受一定波动"
    else:                                                              # 高回撤
        investor_type = "激进型投资者，追求高收益、能承受较大波动"

    ai_conclusion = {                                                  # AI 总结
        "winner": {"code": winner["code"], "name": winner["name"], "score": winner["score"]["total"]},  # 冠军
        "reasons": reasons,                                            # 原因列表
        "conclusion": conclusion,                                      # 最终结论
        "investor_type": investor_type,                                # 适合人群
        "summary_text": f"在{names}的对比中，{winner['name'][:4]}综合表现最优。{'；'.join(reasons)}。{conclusion}。适合{investor_type}。",  # 完整总结
    }

    return {                                                           # 返回摘要
        "best_return": {"code": best_ret["code"], "name": best_ret["name"], "value": best_ret["metrics"]["annualized_return"]},
        "best_sharpe": {"code": best_sh["code"], "name": best_sh["name"], "value": best_sh["metrics"]["sharpe_ratio"]},
        "lowest_risk": {"code": low_risk["code"], "name": low_risk["name"], "value": low_risk["metrics"]["max_drawdown"]},
        "best_score": {"code": best_sc["code"], "name": best_sc["name"], "value": best_sc["score"]["total"]},
        "ai_conclusion": ai_conclusion,                                # AI 总结
    }
