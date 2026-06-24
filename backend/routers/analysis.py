"""深度分析 API 路由 — 风险指标、评分、经理分析、风格漂移."""

import pandas as pd                                                    # 数据处理
from fastapi import APIRouter, Query                                    # 路由和查询参数
from services.fund_fetcher import (                                     # 数据服务
    get_fund_nav, get_fund_manager, get_fund_holdings,
    get_holdings_by_quarter,                                           # 多期持仓
)
from services.calculator import (                                      # 指标计算器
    annualized_return, max_drawdown, sharpe_ratio,
    volatility, calmar_ratio, downside_risk,
    detect_style_drift,                                                # 风格漂移检测
)

router = APIRouter()                                                   # 创建路由实例


@router.get("/{code}/manager")                                         # 基金经理信息
async def get_manager(code: str):                                      # 基金代码
    return get_fund_manager(code)                                      # 返回经理数据


@router.get("/{code}/risk")                                            # 风险指标
async def get_risk(code: str, period: str = Query("1y")):              # 基金代码 + 时间区间
    nav_data = get_fund_nav(code, period)                              # 获取净值数据
    if not nav_data or len(nav_data) < 10:                             # 数据不足
        return {"code": code, "error": "数据不足"}                     # 返回错误

    df = pd.DataFrame(nav_data)                                        # 转为 DataFrame
    df = df.sort_values("date")                                        # 按日期排序
    returns = df["nav"].pct_change().dropna()                          # 计算日收益率
    nav_series = df["nav"]                                             # 净值序列

    return {                                                           # 返回风险指标
        "code": code,                                                  # 基金代码
        "metrics": {                                                   # 指标详情
            "annualized_return": round(annualized_return(returns) * 100, 2),  # 年化收益 %
            "max_drawdown": round(max_drawdown(nav_series) * 100, 2), # 最大回撤 %
            "sharpe_ratio": round(sharpe_ratio(returns), 4),           # 夏普比率
            "volatility": round(volatility(returns) * 100, 2),        # 波动率 %
            "calmar_ratio": round(calmar_ratio(returns, nav_series), 4),  # Calmar
            "downside_risk": round(downside_risk(returns) * 100, 2),  # 下行风险 %
            "data_points": len(nav_data),                              # 数据点数
            "period": period,                                          # 时间区间
        },
    }


@router.get("/{code}/score")                                           # 综合评分
async def get_score(code: str):                                        # 基金代码
    nav_data = get_fund_nav(code, "1y")                                # 取近1年数据
    if not nav_data or len(nav_data) < 10:                             # 数据不足
        return {"code": code, "error": "数据不足"}                     # 返回错误

    df = pd.DataFrame(nav_data)                                        # 转 DataFrame
    df = df.sort_values("date")                                        # 排序
    returns = df["nav"].pct_change().dropna()                          # 日收益率
    nav_series = df["nav"]                                             # 净值序列

    ann_ret = annualized_return(returns) * 100                         # 年化收益率
    mdd = abs(max_drawdown(nav_series)) * 100                          # 最大回撤绝对值
    sr = sharpe_ratio(returns)                                         # 夏普比率

    # 简化评分模型：收益40% + 风控30% + 夏普30%
    ret_score = min(max(ann_ret / 50 * 100, 0), 100)                   # 收益分（50%年化=满分）
    risk_score = max(100 - mdd * 2, 0)                                 # 风控分（回撤越小越高）
    sharp_score = min(max(sr / 3 * 100, 0), 100)                       # 夏普分（3=满分）
    total = ret_score * 0.4 + risk_score * 0.3 + sharp_score * 0.3     # 加权总分

    # 根据总分给出建议
    if total >= 80:                                                    # 80分以上
        rec = "强烈推荐"                                               # 强烈推荐
    elif total >= 60:                                                  # 60-79分
        rec = "推荐"                                                   # 推荐
    elif total >= 40:                                                  # 40-59分
        rec = "观望"                                                   # 观望
    else:                                                              # 40分以下
        rec = "不推荐"                                                 # 不推荐

    return {                                                           # 返回评分结果
        "code": code,                                                  # 基金代码
        "score": round(total, 1),                                      # 综合分
        "recommendation": rec,                                         # 投资建议
        "breakdown": {                                                 # 评分明细
            "return_score": round(ret_score, 1),                       # 收益分
            "risk_score": round(risk_score, 1),                        # 风控分
            "sharpe_score": round(sharp_score, 1),                     # 夏普分
        },
        "metrics": {                                                   # 原始指标
            "annualized_return": round(ann_ret, 2),                    # 年化收益
            "max_drawdown": round(mdd, 2),                             # 最大回撤
            "sharpe_ratio": round(sr, 4),                              # 夏普比率
        },
    }


@router.get("/{code}/style-drift")                                     # 风格漂移
async def get_style_drift(code: str):                                  # 基金代码
    quarters = get_holdings_by_quarter(code, n_quarters=2)             # 获取最近2期持仓
    if len(quarters) < 2:                                              # 不足2期数据
        return {"code": code, "error": "持仓数据不足，需要至少2个报告期"}  # 返回错误
    old_holdings = quarters[1]["holdings"]                             # 较早一期持仓
    new_holdings = quarters[0]["holdings"]                             # 较新一期持仓
    result = detect_style_drift(old_holdings, new_holdings)            # 执行漂移检测
    return {                                                           # 返回结果
        "code": code,                                                  # 基金代码
        "old_quarter": quarters[1]["quarter"],                         # 旧季度
        "new_quarter": quarters[0]["quarter"],                         # 新季度
        **result,                                                      # 漂移检测结果
    }


@router.get("/{code}/ai-review")                                       # AI 分析评论
async def get_ai_review(code: str):                                    # 基金代码
    """聚合所有指标，生成 AI 视角的基金分析报告."""                       # 接口说明

    # 1. 获取基础数据
    nav_all = get_fund_nav(code, "all")                                # 全历史净值
    nav_1y = get_fund_nav(code, "1y")                                  # 近1年净值
    manager = get_fund_manager(code)                                   # 基金经理
    holdings = get_fund_holdings(code)                                 # 持仓数据
    quarters = get_holdings_by_quarter(code, 2)                        # 多期持仓

    if not nav_all or len(nav_all) < 30:                               # 数据不足
        return {"code": code, "error": "数据不足，无法生成分析"}         # 返回错误

    # 2. 计算核心指标
    df_all = pd.DataFrame(nav_all).sort_values("date")                 # 全历史 DataFrame
    df_1y = pd.DataFrame(nav_1y).sort_values("date") if len(nav_1y) > 10 else df_all  # 近1年
    ret_all = df_all["nav"].pct_change().dropna()                      # 全历史日收益率
    ret_1y = df_1y["nav"].pct_change().dropna()                        # 近1年日收益率
    nav_s = df_all["nav"]                                              # 净值序列

    total_return = (nav_s.iloc[-1] / nav_s.iloc[0] - 1) * 100         # 成立以来总收益 %
    ann_ret = annualized_return(ret_all) * 100                         # 年化收益率 %
    mdd = abs(max_drawdown(nav_s)) * 100                               # 最大回撤 %
    sr = sharpe_ratio(ret_all)                                         # 夏普比率
    vol = volatility(ret_all) * 100                                    # 波动率 %
    cal = calmar_ratio(ret_all, nav_s)                                 # Calmar
    days = len(nav_all)                                                # 交易日总数
    years = round(days / 252, 1)                                       # 运行年数

    # 3. 风格漂移
    drift_info = None                                                  # 默认无漂移数据
    if len(quarters) >= 2:                                             # 有2期数据
        drift_info = detect_style_drift(                               # 计算漂移
            quarters[1]["holdings"], quarters[0]["holdings"]            # 两期持仓
        )

    # 4. 生成 AI 分析
    strengths = []                                                     # 优势列表
    risks = []                                                         # 风险列表
    tags = []                                                          # 标签

    # 收益分析
    if ann_ret > 20:                                                   # 年化>20%
        strengths.append(f"年化收益 {ann_ret:.1f}%，长期盈利能力突出")    # 优势
        tags.append("高收益")                                           # 标签
    elif ann_ret > 10:                                                 # 年化>10%
        strengths.append(f"年化收益 {ann_ret:.1f}%，收益能力良好")       # 优势
    elif ann_ret > 0:                                                  # 正收益
        risks.append(f"年化收益仅 {ann_ret:.1f}%，盈利能力偏弱")        # 风险
    else:                                                              # 负收益
        risks.append(f"年化收益 {ann_ret:.1f}%，长期亏损")              # 风险
        tags.append("负收益")                                           # 标签

    # 回撤分析
    if mdd < 15:                                                       # 回撤<15%
        strengths.append(f"最大回撤仅 {mdd:.1f}%，风控能力优秀")        # 优势
        tags.append("低回撤")                                           # 标签
    elif mdd < 30:                                                     # 回撤<30%
        strengths.append(f"最大回撤 {mdd:.1f}%，风控在合理范围")         # 优势
    elif mdd < 50:                                                     # 回撤<50%
        risks.append(f"最大回撤 {mdd:.1f}%，波动较大，需承受较大亏损")   # 风险
    else:                                                              # 回撤>=50%
        risks.append(f"最大回撤 {mdd:.1f}%，曾腰斩，高风险")            # 风险
        tags.append("高风险")                                           # 标签

    # 夏普分析
    if sr > 2:                                                         # 夏普>2
        strengths.append(f"夏普比率 {sr:.2f}，风险调整后收益极佳")       # 优势
        tags.append("高夏普")                                           # 标签
    elif sr > 1:                                                       # 夏普>1
        strengths.append(f"夏普比率 {sr:.2f}，性价比不错")              # 优势
    elif sr > 0:                                                       # 夏普>0
        risks.append(f"夏普比率 {sr:.2f}，承担的风险偏高")              # 风险
    else:                                                              # 夏普<=0
        risks.append(f"夏普比率 {sr:.2f}，风险收益比很差")              # 风险

    # 风格漂移分析
    if drift_info:                                                     # 有漂移数据
        if drift_info["is_drifting"]:                                  # 发生漂移
            risks.append(f"风格漂移分数 {drift_info['drift_score']}，基金经理可能调整了策略")  # 风险
            tags.append("风格漂移")                                     # 标签
        else:                                                          # 风格稳定
            strengths.append(f"风格稳定（漂移分数 {drift_info['drift_score']}），投资策略一致")  # 优势

    # 持仓集中度
    if holdings:                                                       # 有持仓数据
        top3_pct = sum(h["percentage"] for h in holdings[:3])          # 前3占比
        if top3_pct > 30:                                              # 集中度>30%
            risks.append(f"前3大持仓占比 {top3_pct:.1f}%，集中度较高")   # 风险
        elif top3_pct < 15:                                            # 集中度<15%
            strengths.append(f"前3大持仓仅 {top3_pct:.1f}%，分散投资")  # 优势

    # 经理信息
    mgr_name = manager.get("manager_name", "") if manager else ""      # 经理姓名
    mgr_tenure = manager.get("tenure", "") if manager else ""          # 任职时间

    # 5. 综合判断
    score = len(strengths) * 20 - len(risks) * 15                      # 简单打分
    score = min(max(score + 50, 0), 100)                               # 钳制到 0-100

    if score >= 75:                                                    # 75分以上
        verdict = "优质基金"                                           # 结论
        action = "值得长期持有，适合作为核心仓位"                       # 建议
        emoji = "🟢"                                                   # 绿灯
    elif score >= 55:                                                  # 55-74分
        verdict = "中等偏上"                                           # 结论
        action = "可以配置，但建议控制仓位不超过总资产的 20%"            # 建议
        emoji = "🟡"                                                   # 黄灯
    elif score >= 35:                                                  # 35-54分
        verdict = "中等偏下"                                           # 结论
        action = "谨慎考虑，建议少量配置或等回调后介入"                  # 建议
        emoji = "🟠"                                                   # 橙灯
    else:                                                              # 35分以下
        verdict = "不推荐"                                             # 结论
        action = "风险收益比不佳，建议回避"                             # 建议
        emoji = "🔴"                                                   # 红灯

    # 6. 适合人群
    if mdd < 20 and sr > 1:                                            # 低回撤高夏普
        investor = "保守型/稳健型投资者，追求稳定增值"                   # 适合人群
    elif mdd < 30 and ann_ret > 15:                                    # 中回撤高收益
        investor = "稳健型/积极型投资者，能承受一定波动"                 # 适合人群
    elif mdd >= 40:                                                    # 高回撤
        investor = "激进型投资者，能承受大幅波动，追求高收益"            # 适合人群
    else:                                                              # 其他
        investor = "平衡型投资者，追求收益与风险的平衡"                  # 适合人群

    return {                                                           # 返回 AI 分析报告
        "code": code,                                                  # 基金代码
        "emoji": emoji,                                                # 状态灯
        "verdict": verdict,                                            # 综合判断
        "action": action,                                              # 操作建议
        "investor_type": investor,                                     # 适合人群
        "score": score,                                                # AI 综合分
        "summary": {                                                   # 核心数据摘要
            "total_return": round(total_return, 2),                    # 成立以来总收益 %
            "annualized_return": round(ann_ret, 2),                    # 年化收益 %
            "max_drawdown": round(mdd, 2),                             # 最大回撤 %
            "sharpe_ratio": round(sr, 4),                              # 夏普比率
            "volatility": round(vol, 2),                               # 波动率 %
            "calmar_ratio": round(cal, 4),                             # Calmar
            "years": years,                                            # 运行年数
            "data_points": days,                                       # 交易日数
        },
        "strengths": strengths,                                        # 优势列表
        "risks": risks,                                                # 风险列表
        "tags": tags,                                                  # 标签
        "manager": mgr_name,                                           # 基金经理
        "manager_tenure": mgr_tenure,                                  # 任职时间
    }
